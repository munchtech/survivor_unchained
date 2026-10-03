using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Play.Zones;

/* An ember arena, run (Arena/Arena.cs): a horde that thickens by the minute.
 *
 *   the horde    kept at a number that climbs from a score to a few hundred;
 *                a people's kinds join as the minutes pass, and grow stronger
 *   events       every minute or so, in turn: a closing ring, a champion and
 *                its escort (a chest when it falls), a stampede, a swarm
 *   heralds      at ten and twenty minutes, a champion of champions
 *   the boss     at the half hour, what rules the people comes; kill it and
 *                the arena is won
 *   beyond       it goes on, and harder by the minute (a herald every five),
 *                until the survivor takes the way out that opened where the
 *                boss fell, or falls
 *
 * The ember starts at nothing here and goes nowhere afterward; the cards
 * come often. A great blessing is chosen as it begins and another at the
 * fifteenth minute, from all of them, whoever the survivor is. Win or die,
 * the arena is over and the story goes on. */
public sealed class ArenaRun : ZoneRuntime
{
    public readonly ArenaSpec Spec;
    readonly MapBuild map;
    readonly Denizens people;
    readonly List<OathDef> oaths;
    readonly double packSize, elites, ember, gear;
    readonly int levels, waves;
    readonly string[] lean;
    double spawnT = 1.2, eventT = 55;
    int eventIx;
    bool herald10, herald20, great15, bossUp, won, over;
    double nextHerald, pulseT;
    (double X, double Z)? way;
    Enemy? boss, herald;
    readonly HashSet<int> chests = new();

    public override string Id => "arena";
    public override string Name => Spec.Name;
    public override string? Region => Spec.Sub != "" ? Spec.Sub : $"Tier {Spec.Tier} · {people.Name}";
    public override bool Combat => true;
    public override IReadOnlyList<string> Creatures => people.Arena.Select(h => h.Def).Append(people.Champion).Append(BossDef).Distinct().ToList();
    /// <summary>Higher and further out: the whole of the fight in view.</summary>
    public override (double Pitch, double Distance)? Camera => (64, 31);
    public override bool Ember => true;
    public bool Over => over;
    /// <summary>What comes at the half hour: the story's named foe, or what rules the people.</summary>
    string BossDef => Spec.Boss ?? people.Boss;
    string BossName => Spec.BossName ?? people.BossName;
    string BossTitle => Spec.BossTitle ?? people.BossTitle;
    /// <summary>What rules the horde is dead: the fight is won, and the way out open.</summary>
    public bool Won => won;
    double Seconds => B?.Time ?? 0;
    double Minute => Seconds / 60;
    double End => Spec.Minutes * 60;

    public ArenaRun(IZoneHost host, MapBuild map, ArenaSpec spec) : base(host, map.Meta)
    {
        Spec = spec;
        this.map = map;
        people = MapOffers.People(spec.People);
        oaths = spec.Oaths.Select(MapOffers.Oath).ToList();
        packSize = oaths.Aggregate(1.0, (a, o) => a * o.PackSize);
        elites = oaths.Aggregate(1.0, (a, o) => a * o.Elites);
        ember = oaths.Aggregate(1.0, (a, o) => a * o.Ember);
        gear = oaths.Aggregate(1.0, (a, o) => a * o.Gear);
        levels = oaths.Sum(o => o.Levels);
        waves = oaths.Sum(o => o.Waves);
        lean = MapOffers.Lean(spec.Map, spec.People);
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot, OnPickup = OnPickup };
    }

    /// <summary>Always night: the ember burns only in the dark.</summary>
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Night;

    /// <summary>An arena's night is brighter than the wood's: the fight is seen
    /// from high up, and has to read out to the edges of the picture.</summary>
    static readonly AtmospherePreset Night = Atmospheres.Night with
    {
        KeyIntensity = 4.4, HemiIntensity = 1.6, EnvIntensity = 0.95, FogDensity = 0.004, Exposure = 1.7, RimStrength = 0.75,
    };
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) => t == TimeOfDay.Night ? Night : base.AtmosphereFor(t);
    public override Arrival ArrivalFrom(string? from) => new(0, 0, 0);

    public override void Begin(Battle b)
    {
        base.Begin(b);
        // The people's own cover: graves, walls, rubble, lanterns.
        foreach (var pc in map.Pieces) G.Look.AddProp(pc.Id, pc.X, pc.Z, pc.Rot, pc.Scale);
        b.Rules = MapOffers.Rules(Spec.Map);
        // The survivor's light reaches further here (the camera is further out); a moonless oath still halves it.
        b.Rules.Light *= 1.6;
        b.InBounds = map.CanStand;
        // The first great blessing, before anything moves.
        b.GreatOwed = 1;
        G.Announce(new Announcement(Spec.Name, Region, "zone", 3.4, "Ember arena"));
        Objectives();
    }

    /* ---------------------------------------------------------- the horde -- */

    double R() => G.Rng.NextDouble();

    /// <summary>Minutes past the half hour (0 before it).</summary>
    double Beyond => Math.Max(0, Seconds - End) / 60;
    int Level() => Math.Max(1, Spec.Tier * 2 - 1 + levels + (int)(Minute / 2.5) + (int)(Beyond / 2));
    /// <summary>What an ordinary creature's health is divided by at a minute.</summary>
    public static double FodderEase(double minute) => 1 + 0.12 * minute;

    /// <summary>How many the horde is kept at (a dark bargain struck asks for more of them).</summary>
    int Target() => (int)Math.Min(won ? 380 : 320, (22 + 7.5 * Minute) * packSize * (1 + 0.12 * (Spec.Tier - 1)) * Bargain);
    double Bargain => 1 + 0.15 * (B?.Boons.GetValueOrDefault("dark_bargain") ?? 0);

    /// <summary>Throwers and shooters at once: a few behind the crowd, never a
    /// battery (hundreds of them, each lobbing fire, is not a fight but weather).</summary>
    int RangedCap() => (int)Math.Min(won ? 24 : 16, 5 + Minute / 3);
    int rangedAlive;

    /// <summary>A kind from the people, weighted: those that joined long ago more often.</summary>
    string Pick()
    {
        var open = people.Arena.Where(h => h.From <= Minute).ToList();
        double W((string Def, double Weight, double From) h) => h.Weight * (1 + (Minute - h.From) / 8);
        double r = R() * open.Sum(W);
        foreach (var h in open) { r -= W(h); if (r <= 0) return h.Def; }
        return open[0].Def;
    }

    /// <summary>The strongest kind the people have put in the field so far.</summary>
    string Strongest() => people.Arena.Where(h => h.From <= Minute).OrderByDescending(h => Enemies.Get(h.Def).Health).First().Def;

    /// <summary>Somewhere standable a way off from the survivor, on this bearing if it can.</summary>
    (double X, double Z)? Around(double angle, double dist)
    {
        var p = B!.Player;
        for (int t = 0; t < 10; t++)
        {
            double a = angle + (t == 0 ? 0 : (R() - 0.5) * 2.4), d = dist * (t < 5 ? 1 : 0.7);
            double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
            if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.7)) return (x, z);
        }
        return null;
    }

    Enemy? Spawn(string def, double x, double z, bool elite = false, SpawnStyle? style = null)
    {
        if (B == null) return null;
        // One thrower too many is one of the crowd instead.
        if (Enemies.Get(def).Ranged != null && !elite && def != BossDef)
        {
            if (rangedAlive >= RangedCap())
            {
                var melee = people.Arena.Where(h => h.From <= Minute && Enemies.Get(h.Def).Ranged == null).Select(h => h.Def).FirstOrDefault();
                if (melee == null) return null;
                def = melee;
            }
            else rangedAlive++;
        }
        var st = style ?? (Enemies.Get(def).Family == Family.Undead ? SpawnStyle.Rise : Enemies.Get(def).Behavior == Behavior.Tunneler ? SpawnStyle.Burrow : SpawnStyle.Walk);
        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level() + (elite ? 1 : 0), Elite = elite, Style = st });
        // The crowd softens as the night goes on, so the survivor's growth shows
        // as a horde that melts (docs/SKILLS_DESIGN.md, "The power curve");
        // champions, heralds and the boss keep the steep curve and are the test.
        if (e != null && !elite && def != BossDef) e.MaxHp = e.Hp = e.MaxHp / FodderEase(Math.Min(Minute, End / 60));
        // Past the half hour they harden by the minute, until something gives.
        if (e != null && Beyond > 0)
        {
            double m = Beyond;
            e.MaxHp = e.Hp = e.MaxHp * (1 + 0.1 * m + 0.006 * m * m);
            e.Damage *= 1 + 0.035 * m;
        }
        return e;
    }

    List<Enemy> Group(string def, int n, double x, double z, double spread)
    {
        var o = new List<Enemy>();
        for (int i = 0; i < n; i++)
        {
            double a = R() * Math.PI * 2, d = R() * spread;
            double sx = x + Math.Cos(a) * d, sz = z + Math.Sin(a) * d;
            if (!map.CanStand(sx, sz) || B!.Collision.Blocked(sx, sz, 0.6)) continue;
            // Now and then one of them a champion (more under the oath of champions, and as the minutes go).
            if (Spawn(def, sx, sz, R() < 0.012 * elites * (1 + Minute / 12)) is { } e) o.Add(e);
        }
        return o;
    }

    public override void Step(double dt)
    {
        if (B == null || over) return;
        var p = B.Player;
        int alive = 0;
        rangedAlive = 0;
        foreach (var e in B.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            alive++;
            if (e.Def.Ranged != null) rangedAlive++;
        }
        // The horde kept up: groups from out of sight, all round.
        spawnT -= dt;
        if (spawnT <= 0 && alive < Target() && !bossUp)
        {
            // A field mown thin fills twice as fast, so a strong build mows rather than waits.
            bool thin = alive < Target() * 0.6;
            spawnT = thin ? 0.225 : 0.45;
            if (Around(R() * Math.PI * 2, 24 + R() * 5) is var (x, z)) Group(Pick(), (3 + (int)(R() * 4) + (int)(Minute / 5)) * (thin ? 2 : 1), x, z, thin ? 4.5 : 3.5);
        }
        else if (bossUp && spawnT <= 0 && alive < Target() / 2)
        {
            spawnT = 0.9;
            if (Around(R() * Math.PI * 2, 24) is var (x, z)) Group(Pick(), 4, x, z, 3);
        }
        eventT -= dt;
        if (eventT <= 0 && !bossUp)
        {
            eventT = (60 + R() * 25) / (1 + waves);
            Event(eventIx++ % 4);
        }
        // (Not on the boss's heels: a herald missed that late is let go.)
        if (!herald10 && Minute >= 10) { herald10 = true; if (Seconds < End - 60) Herald(); }
        if (!herald20 && Minute >= 20) { herald20 = true; if (Seconds < End - 60) Herald(); }
        if (won && Seconds >= nextHerald) { nextHerald += 300; Herald(); }
        if (!great15 && Minute >= 15 && !bossUp)
        {
            great15 = true;
            B.GreatOwed++;
            // And a banish with it: by now the build knows what it does not want.
            B.Banishes++;
            G.Announce(new Announcement("The fifteenth minute", "A great blessing", "reward", 2.6));
        }
        if (!bossUp && !won && Seconds >= End) Boss();
    }

    /// <summary>The minute's turn: a ring, a champion, a stampede, a swarm.</summary>
    void Event(int kind)
    {
        var p = B!.Player;
        double m = Minute;
        switch (kind)
        {
            case 0:
            {
                // A closing ring: every way out has something in it.
                int n = 18 + (int)(m * 1.2);
                string def = Pick();
                for (int i = 0; i < n; i++)
                {
                    double a = (double)i / n * Math.PI * 2, rr = 13 + R() * 2;
                    double x = p.X + Math.Cos(a) * rr, z = p.Z + Math.Sin(a) * rr;
                    if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.6)) Spawn(def, x, z);
                }
                Shout("They close in from every side.");
                break;
            }
            case 1:
            {
                // A champion and its escort (two, or more, under the oath of champions); each carries a chest.
                int n = (int)elites + (R() < elites % 1 ? 1 : 0);
                double a0 = R() * Math.PI * 2;
                for (int k = 0; k < n; k++)
                {
                    if (Around(a0 + k * 1.1, 22) is not var (x, z)) continue;
                    var champ = Spawn(Strongest(), x, z, true);
                    if (champ == null) continue;
                    champ.MaxHp = champ.Hp = champ.MaxHp * 2;
                    chests.Add(champ.Id);
                    Group(Pick(), 5 + (int)(m / 3), x, z, 3);
                }
                Shout(n > 1 ? $"Champions of {people.Name}: they carry something." : $"A champion of {people.Name}: it carries something.");
                break;
            }
            case 2:
            {
                // A stampede: a column of the fastest, straight across.
                string def = people.Arena.Where(h => h.From <= m).OrderByDescending(h => Enemies.Get(h.Def).Speed).First().Def;
                double a = R() * Math.PI * 2;
                double sx = -Math.Sin(a), sz = Math.Cos(a);
                int n = 12 + (int)(m / 2);
                for (int i = 0; i < n; i++)
                {
                    double off = (i - n / 2.0) * 1.3;
                    double x = p.X + Math.Cos(a) * 26 + sx * off, z = p.Z + Math.Sin(a) * 26 + sz * off;
                    if (!map.CanStand(x, z)) continue;
                    if (Spawn(def, x, z) is { } e) e.Speed *= 1.35;
                }
                Shout("A stampede!");
                break;
            }
            default:
            {
                // A swarm from one quarter.
                if (Around(R() * Math.PI * 2, 22) is var (x, z)) Group(Pick(), 25 + (int)m, x, z, 5);
                Shout("A swarm, from the dark.");
                break;
            }
        }
    }

    void Shout(string text)
    {
        var p = B!.Player;
        B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = text });
        B.Events.Emit(new Ev.Shake { Amount = 0.2 });
    }

    /// <summary>A champion of champions, at ten and twenty minutes.</summary>
    void Herald()
    {
        if (Around(R() * Math.PI * 2, 20) is not var (x, z)) return;
        herald = Spawn(people.Champion, x, z, true);
        if (herald == null) return;
        herald.MaxHp = herald.Hp = herald.MaxHp * (4 + Spec.Tier) * (Minute >= 20 ? 1.6 : 1) * (1 + Beyond / 10);
        herald.Damage *= 1.2;
        chests.Add(herald.Id);
        herald.Named = new Named { Title = $"Herald of {people.Name}" };
        G.Announce(new Announcement($"Herald of {people.Name}", "It carries a chest", "danger", 2.4));
    }

    /// <summary>The half hour: what rules the people comes.</summary>
    void Boss()
    {
        bossUp = true;
        var p = B!.Player;
        var at = Around(R() * Math.PI * 2, 18) ?? (p.X + 8, p.Z);
        boss = Spawn(BossDef, at.X, at.Z, true, SpawnStyle.Walk);
        if (boss != null && Spec.BossName != null) boss.Named = new Named { Title = Spec.BossName };
        if (boss != null)
        {
            boss.MaxHp = boss.Hp = boss.MaxHp * (6 + Spec.Tier * 2);
            boss.Damage *= 1.3;
        }
        for (int k = 0; k < 14; k++)
        {
            double a = k * Math.PI * 2 / 14;
            double x = at.X + Math.Cos(a) * 5, z = at.Z + Math.Sin(a) * 5;
            if (map.CanStand(x, z)) Spawn(Pick(), x, z);
        }
        B.Events.Emit(new Ev.Shake { Amount = 0.45 });
        G.Announce(new Announcement(BossName, BossTitle, "danger", 3, "The half hour"));
        Objectives();
    }

    /* ------------------------------------------------------------ spoils -- */

    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    int Rarity(double luck)
    {
        double roll = R() / luck;
        return roll < 0.04 + Spec.Tier * 0.01 ? 3 : roll < 0.2 + Spec.Tier * 0.02 ? 2 : roll < 0.65 ? 1 : 0;
    }

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        if (chests.Remove(e.Id)) o.Add(new Loot(PickupKind.Chest, null, 1, true));
        if (e.Elite && e != boss && R() < 0.3 * gear)
            o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Rarity(gear), lean));
        if (e == boss)
        {
            for (int k = 0; k < 2 + Spec.Tier / 2; k++)
                o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Math.Max(1, Rarity(gear * 1.5)), lean));
            var pool = Abilities.All.Values.Where(a => a.Movement && ArtBook.CanLearn(G.Journey.Ch, a.Id)).Select(a => a.Id).ToList();
            if (pool.Count > 0) o.Add(new Loot(PickupKind.Item, ArtBook.Manual(pool[(int)(R() * pool.Count)]), 1, true, 2));
        }
        return o;
    }

    /// <summary>A chest: upgrades, an evolution first if one is earned.</summary>
    bool OnPickup(Pickup p)
    {
        if (p.Kind != PickupKind.Chest || B == null) return true;
        int n = 1 + (R() < 0.3 ? 1 : 0) + (R() < 0.1 ? 1 : 0);
        var got = LevelUp.OpenChest(B, n);
        G.Announce(new Announcement("A chest", string.Join(" · ", got), "reward", 2.8));
        return true;
    }

    void OnKill(Enemy e, bool byPlayer)
    {
        // (Let go of the fallen: the pool gives the same body to the next of the horde.)
        if (e == herald) herald = null;
        if (e == boss && !over) Victory(e.X, e.Z);
    }

    /* -------------------------------------------------------------- the end -- */

    /// <summary>What rules the horde is dead: won, and told so; the way out opens
    /// where it fell, and the arena goes on for whoever wants more of it.</summary>
    void Victory(double x, double z)
    {
        won = true;
        bossUp = false;
        boss = null;
        nextHerald = Seconds + 300;
        eventT = 20;
        Arenas.Won(G.Journey, Spec);
        way = map.CanStand(x, z) ? (x, z) : (B!.Player.X, B.Player.Z);
        var (wx, wz) = way.Value;
        G.Look.AddLight(wx, 2.2, wz, "#8ab4ff", 3.2, 14, 0.08, 0.14, "#b8d0ff");
        Interactables.Add(new Interactable
        {
            Id = "way_out", X = wx, Z = wz, R = 2.6, Verb = "Leave", Name = "The way out",
            Hint = () => $"Won. Or stay: {Clock(Seconds - End)} past the half hour",
            Act = Leave,
        });
        B!.Events.Emit(new Ev.Shake { Amount = 0.35 });
        G.Announce(new Announcement($"{Spec.Name} is won", "The way out is open. Or stay, and see how far the ember goes.", "reward", 4, "Victory"));
        Objectives();
    }

    /// <summary>Out by the way out (only once the fight is won).</summary>
    public void Leave()
    {
        if (won && !over) Finish();
    }

    public override bool OnDeath(string killer)
    {
        if (!over) Finish();
        return true;
    }

    void Finish()
    {
        if (B == null) return;
        over = true;
        G.SetBoss(null);
        var result = Arenas.Finish(G.Journey, B, Spec, won);
        G.After(B.Player.Alive ? 0.6 : 2.2, () => G.ArenaOver(result));
    }

    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    public override void Frame(double dt)
    {
        if (B == null || over) return;
        // The way out, pulsing on the ground where the boss fell.
        if (way is var (wx, wz) && (pulseT -= dt) <= 0)
        {
            pulseT = 1.3;
            B.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = wx, Z = wz, Radius = 2.4, Duration = 1.2, Hostile = false });
        }
        if (boss is { Alive: true } b && b.State != EnemyState.Dying) G.SetBoss(new BossBar(BossName, BossTitle, b.Hp, b.MaxHp));
        else if (herald is { Alive: true } h && h.State != EnemyState.Dying) G.SetBoss(new BossBar(h.Named?.Title ?? $"Herald of {people.Name}", people.Name, h.Hp, h.MaxHp));
        else G.SetBoss(null);
        // The clock on the objectives, each second.
        if ((int)Seconds != lastSecond) { lastSecond = (int)Seconds; Objectives(); }
    }

    int lastSecond = -1;

    void Objectives()
    {
        int left = (int)Math.Max(0, End - Seconds);
        var steps = new List<Step>
        {
            won ? new Step($"{BossName} is dead: the arena is won", Done: true)
            : bossUp ? new Step($"{BossName} has come: kill it")
            : new Step($"Survive: {left / 60}:{left % 60:00} until {BossName} comes"),
        };
        if (won) steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} past the half hour", Optional: true));
        foreach (var o in oaths) steps.Add(new Step($"{o.Name}: {o.Asks.ToLowerInvariant()}", Optional: true));
        G.SetObjectives([new Tracked("arena", Spec.Name, TrackTone.Main, steps)]);
    }

    public override AmbienceMix Ambience(double x, double z) => new() { Wind = 0.4, Leaves = Spec.Theme == "blight" ? 0.1 : 0.35, Crickets = 0.3, Owl = 0.2, Fire = Warmth(x, z) };

    public override Dictionary<string, object?> Debug() => new()
    {
        ["minute"] = Math.Round(Minute, 1), ["alive"] = B?.Enemies.Living().Count() ?? 0, ["target"] = Target(), ["level"] = Level(), ["ember"] = B?.EmberLevel,
    };
}
