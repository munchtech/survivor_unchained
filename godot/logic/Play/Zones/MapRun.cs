using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* A map, run (Maps/MapGen.cs made it): a level to beat, not a wood that
 * never ends. It is thick with packs that wait where they stand until you
 * come to them; its altars, woken, call the horde in waves until they are
 * spent; its last clearing holds what rules the place. Kill that and the
 * map is yours: its hoard, and the way home.
 *
 * Nothing spawns out of nowhere behind you. What is on the map is what you
 * fight, packs brought to life as you come within sight of them, so a map
 * can hold hundreds without the fight carrying them all at once. */
public sealed class MapRun : ZoneRuntime
{
    public readonly MapBuild Map;
    readonly Denizens people;
    readonly List<OathDef> oaths;
    readonly double packSize, elites, ember, gear;
    readonly int levels, extraWaves;

    enum AltarState { Asleep, Waves, Spent }
    sealed class Altar
    {
        public required Area Area;
        public required int Light;
        public AltarState State;
        public int Wave, Waves;
        public double WaveT;
        public readonly List<Enemy> Called = new();
    }

    readonly bool[] packUp;
    readonly List<Enemy> packFolk = new();
    readonly List<Altar> altars = new();
    Enemy? boss;
    bool bossUp, done;
    int slain, total;
    double clock;

    public override string Id => "map";
    public override string Name => Map.Spec.Name;
    public override string? Region => $"Tier {Map.Spec.Tier} · {people.Name}" + (oaths.Count > 0 ? " · " + string.Join(", ", oaths.Select(o => o.Name)) : "");
    public override bool Combat => true;
    public override IReadOnlyList<string> Creatures => people.Horde.Select(h => h.Def).Append(people.Boss).Distinct().ToList();

    public MapRun(IZoneHost host, MapBuild map, string peopleId) : base(host, map.Meta)
    {
        Map = map;
        people = MapOffers.People(peopleId);
        oaths = map.Spec.Oaths.Select(MapOffers.Oath).ToList();
        packSize = oaths.Aggregate(1.0, (a, o) => a * o.PackSize);
        elites = oaths.Aggregate(1.0, (a, o) => a * o.Elites);
        ember = oaths.Aggregate(1.0, (a, o) => a * o.Ember);
        gear = oaths.Aggregate(1.0, (a, o) => a * o.Gear);
        levels = oaths.Sum(o => o.Levels);
        extraWaves = oaths.Sum(o => o.Waves);
        packUp = new bool[map.Packs.Count];
        total = map.Packs.Sum(p => PackCount(p));
        int li = 0;
        foreach (var a in map.Altars)
        {
            // Each altar's hearth is the light the generator set down cold at its middle.
            int light = map.Meta.Lights.FindIndex(l => Dist(l.X, l.Z, a.X, a.Z) < 0.5);
            altars.Add(new Altar { Area = a, Light = light, Waves = 3 + extraWaves });
            li++;
        }
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot };
        MakeInteractables();
    }

    /* ------------------------------------------------------------ levels -- */

    int Tier => Map.Spec.Tier;
    // Harder with the tier and the oaths, and with the ember you carry in.
    int Level() => 1 + Tier * 2 + levels + (B?.EmberLevel ?? 1) / 5;
    int PackCount(PackSpot p) => Math.Max(3, (int)Math.Round((5 + Tier * 1.2) * p.Size * packSize));
    double R() => G.Rng.NextDouble();

    string Pick()
    {
        double sum = people.Horde.Sum(h => h.Weight), r = R() * sum;
        foreach (var (def, w) in people.Horde) { r -= w; if (r <= 0) return def; }
        return people.Horde[0].Def;
    }

    Enemy? Spawn(string def, double x, double z, bool elite = false, (double, double, double)? home = null, SpawnStyle style = SpawnStyle.Walk)
    {
        if (B == null) return null;
        for (int t = 0; t < 8; t++)
        {
            double a = R() * Math.PI * 2, d = t == 0 ? 0 : R() * 2.5;
            double sx = x + Math.Cos(a) * d, sz = z + Math.Sin(a) * d;
            if (!Map.CanStand(sx, sz) || B.Collision.Blocked(sx, sz, 0.6)) continue;
            return B.SpawnEnemy(def, sx, sz, new Battle.SpawnOpts { Level = Level() + (elite ? 1 : 0), Elite = elite, Home = home, Style = style });
        }
        return null;
    }

    /* ------------------------------------------------------------- flow -- */

    public override Arrival ArrivalFrom(string? from) => new(Map.Start.X, Map.Start.Z, Map.Meta.Start.Facing);

    public override void Begin(Battle b)
    {
        base.Begin(b);
        G.Announce(new Announcement(Map.Spec.Name, Region, "zone", 3.2, "Map"));
        Objectives();
    }

    public override void Step(double dt)
    {
        if (B == null) return;
        clock += dt;
        var p = B.Player;
        // Packs come to life as you come within sight of them.
        for (int i = 0; i < Map.Packs.Count; i++)
        {
            if (packUp[i]) continue;
            var s = Map.Packs[i];
            if (Dist(p.X, p.Z, s.X, s.Z) > 44) continue;
            packUp[i] = true;
            int n = PackCount(s);
            // A champion leads one pack in five (more under the Oath of Champions).
            bool champ = R() < 0.2 * elites;
            for (int k = 0; k < n; k++)
                if (Spawn(k == 0 && champ ? people.Horde[0].Def : Pick(), s.X, s.Z, k == 0 && champ, (s.X, s.Z, 26)) is Enemy e) packFolk.Add(e);
        }
        foreach (var a in altars) Waves(a, dt);
        // The last clearing: what rules the place is waiting.
        var bz = Map.Boss;
        if (!bossUp && Dist(p.X, p.Z, bz.X, bz.Z) < bz.R + 6)
        {
            bossUp = true;
            boss = Spawn(people.Boss, bz.X, bz.Z, true, (bz.X, bz.Z, bz.R + 10));
            if (boss != null)
            {
                boss.MaxHp *= 3 + Tier; boss.Hp = boss.MaxHp;
                boss.Damage *= 1.3;
            }
            for (int k = 0; k < 10 + Tier * 2; k++)
            {
                double ang = k * Math.PI * 2 / (10 + Tier * 2);
                Spawn(Pick(), bz.X + Math.Cos(ang) * (bz.R - 5), bz.Z + Math.Sin(ang) * (bz.R - 5), false, (bz.X, bz.Z, bz.R + 10));
            }
            B.Events.Emit(new Ev.Shake { Amount = 0.35 });
            G.Announce(new Announcement(people.BossName, people.BossTitle, "danger", 2.6));
        }
    }

    public override void Frame(double dt)
    {
        if (boss != null && bossUp && !done)
            G.SetBoss(boss.Alive && boss.State != EnemyState.Dying ? new BossBar(people.BossName, people.BossTitle, boss.Hp, boss.MaxHp) : null);
    }

    /* ----------------------------------------------------------- altars -- */

    void MakeInteractables()
    {
        foreach (var a in altars)
            Interactables.Add(new Interactable
            {
                Id = $"altar{a.Area.Index}", X = a.Area.X, Z = a.Area.Z, R = 3.2, Verb = "Wake", Name = "The Altar",
                When = () => a.State == AltarState.Asleep,
                Hint = () => $"{a.Waves} waves; a hoard when they are spent",
                Act = () => Wake(a),
            });
        Interactables.Add(new Interactable
        {
            Id = "exit", X = Map.Boss.X, Z = Map.Boss.Z, R = 3.4, Verb = "Go home", Name = "The Way Back",
            When = () => done,
            Act = () => G.Travel("waystation", "The Waystation", $"{Map.Spec.Name}, taken"),
        });
    }

    void Wake(Altar a)
    {
        a.State = AltarState.Waves;
        a.Wave = 0;
        a.WaveT = 1.5;
        if (a.Light >= 0) G.Look.SetLit(a.Light, true);
        B?.Events.Emit(new Ev.Shake { Amount = 0.25 });
        G.Announce(new Announcement("The altar wakes", "Hold the clearing", "danger", 2.2));
        Objectives();
    }

    void Waves(Altar a, double dt)
    {
        if (a.State != AltarState.Waves || B == null) return;
        a.Called.RemoveAll(e => !e.Alive || e.State == EnemyState.Dying);
        a.WaveT -= dt;
        // The next wave when this one is mostly down, or it has had its time.
        bool thin = a.Called.Count <= Math.Max(2, a.Wave * 3);
        if (a.Wave < a.Waves && (a.WaveT <= 0 || (thin && a.WaveT < 18)))
        {
            a.Wave++;
            a.WaveT = 24;
            int n = (int)Math.Round((14 + Tier * 4 + a.Wave * 6) * packSize);
            var ar = a.Area;
            for (int k = 0; k < n; k++)
            {
                // From every side of the clearing at once, out of the ground.
                double ang = R() * Math.PI * 2, rr = ar.R - 2 - R() * 3;
                if (Spawn(Pick(), ar.X + Math.Cos(ang) * rr, ar.Z + Math.Sin(ang) * rr, k == 0 && a.Wave == a.Waves, null, SpawnStyle.Rise) is Enemy e)
                    a.Called.Add(e);
            }
            G.Announce(new Announcement($"Wave {a.Wave} of {a.Waves}", null, "danger", 1.4));
            Objectives();
        }
        else if (a.Wave >= a.Waves && a.Called.Count == 0)
        {
            a.State = AltarState.Spent;
            if (a.Light >= 0) G.Look.SetLit(a.Light, false);
            Hoard(a.Area.X, a.Area.Z, 1.0 * gear);
            G.Announce(new Announcement("The altar is spent", "Its hoard is yours", "reward", 2.4));
            Objectives();
        }
    }

    /* ------------------------------------------------------------ spoils -- */

    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    int Rarity(double luck)
    {
        double roll = R() / luck;
        return roll < 0.04 + Tier * 0.01 ? 3 : roll < 0.2 + Tier * 0.02 ? 2 : roll < 0.65 ? 1 : 0;
    }

    /// <summary>A hoard thrown out on the ground: gear, gold and ember.</summary>
    void Hoard(double x, double z, double size)
    {
        if (B == null) return;
        int pieces = Math.Max(1, (int)Math.Round((1 + Tier * 0.5) * size));
        for (int k = 0; k < pieces; k++)
        {
            double a = k * 2.4, r = 1.5 + k * 0.4;
            B.SpawnPickup(PickupKind.Item, x + Math.Cos(a) * r, z + Math.Sin(a) * r, 1, PlainGear[(int)Math.Floor(R() * PlainGear.Length)]);
        }
        for (int k = 0; k < 8; k++)
        {
            double a = R() * Math.PI * 2, r = 1 + R() * 3;
            B.SpawnPickup(k % 2 == 0 ? PickupKind.Gold : PickupKind.Ember, x + Math.Cos(a) * r, z + Math.Sin(a) * r, (k % 2 == 0 ? 6 : 8) * Tier * (k % 2 == 0 ? 1 : ember));
        }
    }

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var out_ = new List<Loot>();
        var loot = e.Def.Loot;
        double r = R();
        if (loot == "wolf" && r < 0.4) out_.Add(new Loot(PickupKind.Material, "wolf_pelt", 1));
        if (loot == "boar" && r < 0.4) out_.Add(new Loot(PickupKind.Material, "boar_hide", 1));
        if (loot == "kerchief" && r < 0.25) out_.Add(new Loot(PickupKind.Material, "kerchief_cloth", 1));
        if (e.Def.Family == Family.Lampling && r < 0.15) out_.Add(new Loot(PickupKind.Material, "ember_shard", 1));
        if (e.Def.Family == Family.Undead && r < 0.2) out_.Add(new Loot(PickupKind.Material, "bone_dust", 1));
        // Champions carry gear, rolled where it falls.
        if (e.Elite && e != boss && R() < 0.55 * gear)
            out_.Add(new Loot(PickupKind.Item, PlainGear[(int)Math.Floor(R() * PlainGear.Length)], 1, true, Rarity(gear)));
        if (e == boss)
            for (int k = 0; k < 2 + Tier / 2; k++)
                out_.Add(new Loot(PickupKind.Item, PlainGear[(int)Math.Floor(R() * PlainGear.Length)], 1, true, Math.Max(1, Rarity(gear * 1.5))));
        return out_;
    }

    void OnKill(Enemy e, bool byPlayer)
    {
        if (e.Faction == Faction.Ally) return;
        slain++;
        if (e == boss && !done)
        {
            done = true;
            G.SetBoss(null);
            Hoard(e.X, e.Z, 2 * gear);
            G.Announce(new Announcement($"{Map.Spec.Name} is taken", "The way home is open at the heart of the clearing", "reward", 3.5, "Map complete"));
            int tier = (int)Math.Max(W.Fact("map.best").Number, Tier);
            W.Facts["map.best"] = tier;
            W.Facts["map.done"] = W.Fact("map.done").Number + 1;
            G.Save("map");
        }
        if (slain % 25 == 0 || e == boss) Objectives();
    }

    void Objectives()
    {
        var steps = new List<Step>
        {
            new($"Carve through: {Math.Min(slain, total)} of {total} slain", Done: slain >= total),
        };
        foreach (var a in altars)
            steps.Add(new Step(a.State switch
            {
                AltarState.Asleep => "Wake an altar",
                AltarState.Waves => $"Hold the altar: wave {a.Wave} of {a.Waves}",
                _ => "An altar, spent",
            }, Optional: true, Done: a.State == AltarState.Spent));
        steps.Add(new Step(done ? "Go home: the way is open" : $"Slay {people.BossName}", Done: false));
        G.SetObjectives(new List<Tracked> { new("map", Map.Spec.Name, TrackTone.Main, steps) });
    }

    /* ------------------------------------------------------------- look -- */

    public override TimeOfDay TimeOf(WorldState w) => Map.Spec.Night ? TimeOfDay.Night : TimeOfDay.Day;
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) => t == TimeOfDay.Night ? Atmospheres.Night : Atmospheres.Day;

    public override List<MapMark> MapMarks()
    {
        var marks = new List<MapMark> { new(Map.Start.X, Map.Start.Z, "Where you came in", MarkKind.Place) };
        foreach (var a in altars) marks.Add(new(a.Area.X, a.Area.Z, a.State == AltarState.Spent ? "A spent altar" : "An altar", a.State == AltarState.Spent ? MarkKind.Place : MarkKind.Quest));
        marks.Add(new(Map.Boss.X, Map.Boss.Z, done ? "The way home" : people.BossName, done ? MarkKind.Exit : MarkKind.Danger));
        return marks;
    }

    public override AmbienceMix Ambience(double x, double z) => new()
    {
        Wind = 0.5, Leaves = 0.6, Crickets = Map.Spec.Night ? 0.5 : 0, Owl = Map.Spec.Night ? 0.3 : 0, Birds = Map.Spec.Night ? 0 : 0.5,
        Fire = Warmth(x, z), Hum = altars.Any(a => a.State == AltarState.Waves) ? 0.6 : 0,
    };

    public override Dictionary<string, object?> Debug() => new()
    {
        ["seed"] = Map.Spec.Seed, ["tier"] = Tier, ["slain"] = slain, ["total"] = total, ["boss"] = bossUp, ["done"] = done,
        ["packsUp"] = packUp.Count(u => u), ["alive"] = B?.Enemies.Living().Count() ?? 0,
    };
}
