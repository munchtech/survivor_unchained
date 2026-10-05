using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/// <summary>How a map ended, and what came out of it.</summary>
public sealed record MapResult(Chart Chart, bool Cleared, double Seconds, int Kills, int Falls, int PacksCleared, int Packs,
    double? BossTtk, bool FirstClear, Dictionary<string, int> Spilled);

/// <summary>
/// A Wayfinder's map: the permanent ARPG arena (docs/SKILLS_DESIGN.md §17). The survivor's own
/// build, kept for good, against placed packs at the map's level and full strength, on MapGen's
/// winding way: clearings, altars kept by the people's minibosses, and its ruler's clearing at
/// the end, fought by the same script as at night (ArenaBosses) on shorter floors.
///
/// What differs from a night, and why:
///   - nothing refills and nothing is softened: each pack is a fight, and the map is a lock
///     that the build is the key to;
///   - kinds and Signs open by tier, not by a clock (the night's rule "a verb is shown before it
///     spreads" becomes the atlas's);
///   - packs rest until the survivor comes near (the day's Wake and Leash), and charge only
///     once roused, in waves of two, with no spikes but at the altar's event;
///   - a fall closes the map and spills half of what was picked up here; only a trait that gets
///     her up (Second Wind, Cold, Then Not) keeps her in it (the owner: getting up and fighting on
///     is rare, or it is a balancing nightmare).
/// </summary>
public sealed class MapRun : ZoneRuntime, IBossArena
{
    public readonly Chart Chart;
    readonly MapBuild map;
    readonly Denizens people;
    /// <summary>Contested: a second people holds a third of the packs.</summary>
    readonly Denizens? rival;
    readonly Core.Rng rng;

    /// <summary>A placed pack: where it rests, whether it has been put down yet, and who is in it.</summary>
    sealed class Pack
    {
        public required PackSpot Spot;
        public required Denizens People;
        public bool Placed, Cleared;
        public int Grade;
        public readonly List<(Enemy E, double Seed)> Members = new();
        public bool Alive => Members.Any(m => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying);
    }
    readonly List<Pack> packs = new();
    /// <summary>Each altar's keepers (placed as the survivor nears), and whether it is lit.</summary>
    sealed class Altar
    {
        public required Area Area;
        public bool Placed, Lit;
        public readonly List<(Enemy E, double Seed)> Keepers = new();
        public bool Kept => Keepers.Any(m => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying);
    }
    readonly List<Altar> altars = new();
    /// <summary>Who carries gear, and how much: a magic pack's leader one, a rare's two, a keeper two.</summary>
    readonly Dictionary<int, int> carriers = new();

    ArenaBoss? script;
    Enemy? boss;
    double bossAt = -1;
    bool bossUp, cleared, over, restlessDone, eventLit, firstClear;
    int falls, kills;
    double? bossTtk;
    (double X, double Z)? way;
    readonly Dictionary<string, int> picked = new();
    readonly Dictionary<string, int> spilled = new();

    /// <summary>Falls a map takes: one. A trait that gets her up catches her before it counts.</summary>
    public const int FallsAllowed = 1;
    /// <summary>The share of MapGen's pack spots set: in clearings, and along the ways (a pack about
    /// every 14 s: the experience lead's density, the ARPG's clear-speed fantasy).</summary>
    public static double ClearingKeep = 0.8, WayKeep = 0.62;
    /// <summary>How near the survivor comes before a pack is set down (out of sight, so it is
    /// already there when seen), and how near a pack must be to wake.</summary>
    const double PlaceAt = 46, Wake = 14, Leash = 24;
    /// <summary>The ruler's floors over the night's (10, 13 and 10 s against 15, 20 and 15):
    /// a map is ten minutes, not thirty.</summary>
    public const double BossFloors = 0.65;
    /// <summary>The ruler's health, over its body's at the map's level: 45-75 s at par (§17.7). The
    /// night's own multipliers (12 to 43 at the first tier) were set against the ember's builds and
    /// their Breaks; a day build meets the four more evenly (at a fifth of the night's, the Pack-Mother
    /// took 173 s and the Barrow Lord 67), so one number serves all four.</summary>
    public const double BossHealth = 3.5;

    public MapRun(IZoneHost host, MapBuild map, Chart chart) : base(host, map.Meta)
    {
        Chart = chart;
        this.map = map;
        people = MapOffers.People(chart.People);
        rng = new Core.Rng((uint)chart.Seed * 2654435761u + 7);
        if (chart.Has("contested"))
        {
            var others = MapOffers.Peoples.Where(p => p.Id != people.Id).ToList();
            rival = others[(int)(rng.Next() * others.Count)];
        }
        // MapGen sets a spot about every 14 m: a pack at each made the way one long fight (a pack every
        // 8 s, a map of 14 minutes). Three in four clearings' spots are kept and one in three of the
        // way's, so packs come with ground between them to walk and to pick up after.
        foreach (var s in map.Packs)
        {
            var a = map.Areas[Math.Clamp(s.Area, 0, map.Areas.Count - 1)];
            bool clearing = (s.X - a.X) * (s.X - a.X) + (s.Z - a.Z) * (s.Z - a.Z) < a.R * a.R;
            // A breath before the ruler: the last way to its clearing is left empty.
            if (!clearing && s.Area == map.Boss.Index - 1) continue;
            if (rng.Next() >= (clearing ? ClearingKeep : WayKeep)) continue;
            packs.Add(new Pack { Spot = s, People = rival != null && rng.Next() < 1 / 3.0 ? rival : people });
        }
        foreach (var a in map.Altars) altars.Add(new Altar { Area = a });
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot, OnPickup = OnPickup, OnPlayerDeath = OnFall };
    }

    public override string Id => "map";
    public override string Name => Chart.Name;
    public override string? Region => $"Tier {Chart.Tier} · {people.Name}";
    public override bool Combat => true;
    public override IReadOnlyList<string> Creatures =>
        Charts.Kinds(people, Chart.Tier).Select(k => k.Def)
            .Concat(rival != null ? Charts.Kinds(rival, Chart.Tier).Select(k => k.Def) : [])
            .Concat(Charts.Guardians(people, Chart.Tier)).Append(people.Champion).Append(people.Boss).Distinct().ToList();
    /// <summary>By day: the maps are the day's build in the day's world, and a pack must be read
    /// before it is woken (at dusk the way was black past the start's fire).</summary>
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Day;
    /// <summary>A pack and the ground round it in view: higher than the road's, nearer than a night's.</summary>
    public override (double Pitch, double Distance)? Camera => (62, 24);
    public override Arrival ArrivalFrom(string? from) => new(map.Start.X, map.Start.Z, 0);

    /// <summary>The map's clock and how it stands.</summary>
    public double Seconds => B?.Time ?? 0;
    public bool Cleared => cleared;
    public bool Over => over;
    public int Falls => falls;
    public int Kills => kills;
    public ArenaBoss? BossScript => script;
    public Enemy? Boss => boss;
    public int PacksPlaced => packs.Count(p => p.Placed);
    public int PacksCleared => packs.Count(p => p.Cleared);
    public int PackCount => packs.Count;
    /// <summary>For the bots: where the packs still standing are, and the altars and the ruler.</summary>
    public IEnumerable<(double X, double Z)> Standing => packs.Where(p => !p.Cleared).Select(p => (p.Spot.X, p.Spot.Z));
    public MapBuild Ground => map;
    public MapResult? Result { get; private set; }

    /// <summary>The ruler's tier, for the counts its script uses (wolves in a drive, shields in a
    /// line): a night's tier per four of the atlas's.</summary>
    int BossTier => Math.Min(4, 1 + (Chart.Tier - 1) / 4);
    int Level => Chart.Level;

    public override void Begin(Battle b)
    {
        base.Begin(b);
        b.Rules = Chart.Rules();
        b.InBounds = map.CanStand;
        // What the gear inscribes works here, and only here (the scars' kit carries coals).
        var kit = Character.Kit(G.Journey.Ch);
        b.Wear(kit.Marks, kit.SkillMods);
        // Packs charge in waves of two, and only once roused; no spikes but the altar's event.
        b.Charges.Spikes = false;
        b.Charges.Cap = 2;
        b.Charges.Tell = "";
        G.Announce(new Announcement(Chart.Name, Region ?? "", "zone", 3.4, "A Wayfinder's map"));
        Objectives();
    }

    /* ------------------------------------------------------------- packs -- */

    double R() => rng.Next();

    string PickKind(Denizens d)
    {
        var open = Charts.Kinds(d, Chart.Tier).ToList();
        double r = R() * open.Sum(k => k.Weight);
        foreach (var k in open) { r -= k.Weight; if (r <= 0) return k.Def; }
        return open[0].Def;
    }

    Enemy? Put(string def, double x, double z, (double X, double Z) home, bool elite = false, int levelUp = 0)
    {
        if (B == null) return null;
        for (int t = 0; t < 6; t++)
        {
            double a = R() * Math.Tau, d = t == 0 ? 0 : 0.8 + R() * 2.2;
            double px = x + Math.Cos(a) * d, pz = z + Math.Sin(a) * d;
            if (!map.CanStand(px, pz) || B.Collision.Blocked(px, pz, 0.6)) continue;
            var def0 = Enemies.Get(def);
            var style = def0.Family == Family.Undead ? SpawnStyle.Rise : SpawnStyle.Walk;
            return B.SpawnEnemy(def, px, pz, new Battle.SpawnOpts { Level = Level + levelUp, Elite = elite, Style = style, Home = (home.X, home.Z, Leash), Wake = Wake });
        }
        return null;
    }

    /// <summary>Signs on a champion: from those its people have opened at this tier, never two that
    /// may not go together.</summary>
    void Sign(Enemy e, Denizens d, int n, string? first = null)
    {
        var open = Charts.Signs(d, Chart.Tier);
        var worn = new List<string>();
        if (first != null && Signs.Fits(e.Def, first, worn)) worn.Add(first);
        while (worn.Count < n)
        {
            var fit = open.Where(s => Signs.Fits(e.Def, s, worn)).ToList();
            if (fit.Count == 0) break;
            worn.Add(fit[(int)(R() * fit.Count)]);
        }
        if (worn.Count == 0) return;
        double was = e.Def.Speed;
        e.Def = Signs.Wear(e.Def, worn);
        e.Speed *= e.Def.Speed / was;
    }

    /// <summary>A pack set down where it rests: 4-10 of the people's open kinds (more under the
    /// chart's mods), one kind or two. One in four is magic (a champion with a Sign leads it), one in
    /// ten rare (two or three Signs, and an escort).</summary>
    void Place(Pack k)
    {
        k.Placed = true;
        var s = k.Spot;
        string main = PickKind(k.People), mix = PickKind(k.People);
        int n = Math.Clamp((int)Math.Round((4 + R() * 4) * s.Size * Chart.PackSize), 3, 14);
        double roll = R();
        k.Grade = roll < 0.1 ? 2 : roll < 0.35 ? 1 : 0;
        if (k.Grade == 2) n += 3;
        for (int i = 0; i < n; i++)
            if (Put(i % 3 == 2 ? mix : main, s.X, s.Z, (s.X, s.Z)) is { } e) k.Members.Add((e, e.Seed));
        bool hardened = Chart.Has("hardened");
        if (k.Grade > 0 || hardened)
        {
            // The leader: the strongest of its kinds, a level up.
            string lead = Charts.Kinds(k.People, Chart.Tier).Select(h => h.Def).Where(d => Enemies.Get(d).Ranged == null)
                .OrderByDescending(d => Enemies.Get(d).Health).FirstOrDefault() ?? main;
            if (Put(lead, s.X, s.Z, (s.X, s.Z), elite: true, levelUp: 1) is { } c)
            {
                int signs = k.Grade switch { 2 => 2 + (R() < 0.5 ? 1 : 0), 1 => 1, _ => 0 } + (Chart.Has("signed") && k.Grade > 0 ? 1 : 0);
                Sign(c, k.People, Math.Max(signs, hardened ? 1 : 0), hardened ? k.People.Signs.FirstOrDefault() : null);
                if (k.Grade > 0) carriers[c.Id] = k.Grade;
                k.Members.Add((c, c.Seed));
            }
        }
    }

    /// <summary>An altar's keepers: one of the people's minibosses open at this tier (two under the
    /// twin guardians), wearing the map's Signs. Put down, it lights the altar.</summary>
    void Place(Altar a)
    {
        a.Placed = true;
        var pool = Charts.Guardians(people, Chart.Tier);
        int n = Chart.Has("twin") ? 2 : 1;
        for (int i = 0; i < n; i++)
        {
            string def = pool[(int)(R() * pool.Count)];
            double ang = R() * Math.Tau;
            if (Put(def, a.Area.X + Math.Cos(ang) * 3, a.Area.Z + Math.Sin(ang) * 3, (a.Area.X, a.Area.Z), elite: true, levelUp: 1) is not { } e) continue;
            // A night's miniboss is a champion's turn and more (1.6 + 0.6 a tier); here it keeps an altar.
            e.MaxHp = e.Hp = e.MaxHp * 2.2;
            Sign(e, people, Math.Min(2, Chart.Tier / 4) + (Chart.Has("signed") ? 1 : 0));
            e.Named = new Named { Title = e.Def.Name };
            carriers[e.Id] = 3;
            a.Keepers.Add((e, e.Seed));
        }
    }

    public override void Step(double dt)
    {
        if (B == null || over) return;
        var p = B.Player;
        // Packs and keepers are set down out of sight as the survivor nears them.
        foreach (var k in packs)
        {
            if (!k.Placed && Near(p, k.Spot.X, k.Spot.Z, PlaceAt)) Place(k);
            if (k.Placed && !k.Cleared && !k.Alive) k.Cleared = true;
        }
        foreach (var a in altars)
        {
            if (!a.Placed && Near(p, a.Area.X, a.Area.Z, PlaceAt)) Place(a);
            if (a.Placed && !a.Lit && !a.Kept) Light(a);
        }
        // The ruler's sign at its clearing's edge, as the last stretch of way begins.
        var bc = map.Boss;
        if (!signed && Near(p, bc.X, bc.Z, bc.R + 34)) Sign(p);
        if (eventAt >= 0) Event();
        // The ruler, in its clearing.
        if (!bossUp && !cleared && boss == null && Near(p, bc.X, bc.Z, bc.R + 2)) Ruler(false);
    }

    static bool Near(PlayerState p, double x, double z, double r) => (p.X - x) * (p.X - x) + (p.Z - z) * (p.Z - z) < r * r;

    /* -------------------------------------------------- the ruler's sign -- */

    bool signed;

    /// <summary>The night's run-up, small: a sound and a light at the edge of the ruler's clearing,
    /// on the side the way comes in, so the survivor walks the last stretch toward it.</summary>
    void Sign(PlayerState p)
    {
        signed = true;
        var bc = map.Boss;
        double a = Math.Atan2(p.Z - bc.Z, p.X - bc.X);
        double x = bc.X + Math.Cos(a) * (bc.R - 2), z = bc.Z + Math.Sin(a) * (bc.R - 2);
        G.Look.AddLight(x, 2.5, z, "#ff6a3a", 3.2, 16, 0.25, 0.12, "#ff8a5a");
        string sign = people.Id switch
        {
            "pack" => "A howl from the far side of the trees; the wolves lift their heads.",
            "dead" => "A drum, slow, under everything; the dead turn to face it.",
            "lamplings" => "A blasting thump, and the ground shivers; picks rattle somewhere.",
            "kerchiefs" => "A whistle, three notes, and an answering whistle.",
            _ => "Something is waiting.",
        };
        B!.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = sign });
        G.Announce(new Announcement($"{people.BossName} waits", "At the end of the way", "danger", 2.6));
    }

    /* -------------------------------------------------------- the altars -- */

    /// <summary>Its keepers down, the altar is lit. The first lit is the map's event: the people's
    /// own question, as at night (a ring of them, a captain with a chest), with its tell.</summary>
    void Light(Altar a)
    {
        a.Lit = true;
        G.Look.AddLight(a.Area.X, 2.4, a.Area.Z, "#ffb46a", 3.6, 16, 0.1, 0.12, "#ffd29a");
        G.Announce(new Announcement("The altar is lit", eventLit ? "" : "Something answers it", "reward", 2.6));
        // The first lit is the map's event; with the atlas's "twice lit", a later one may be too.
        if (eventLit && !(eventsLit < 2 && R() < Atlas.Rank(G.Journey.World, Atlas.TwiceLit) / 3.0)) return;
        eventLit = true;
        eventsLit++;
        eventAt = Seconds;
        eventWave = 0;
        eventAltar = a.Area;
        eventFoes.Clear();
        B!.Charges.Spikes = true;
        G.Announce(new Announcement(EventName, "Hold the altar", "danger", 3, people.Name));
    }

    /* The map's event (the experience lead's shape): the people's own question, asked three times
     * over about fifty seconds at the lit altar, its tell first; then, its last asker down (or a
     * minute gone), a strongbox at the altar: three to five things at the map's level, and a chart
     * now and then. */
    double eventAt = -1;
    int eventWave, eventsLit;
    Area? eventAltar;
    readonly List<(Enemy E, double Seed)> eventFoes = new();

    string EventName => people.Id switch
    {
        "pack" => "The Hunt", "dead" => "The Ford Rises", "lamplings" => "The Dig Opens", "kerchiefs" => "The Ambush", _ => "The Question",
    };

    void Event()
    {
        if (B == null || eventAltar == null) return;
        double t = Seconds - eventAt;
        if (eventWave < 3 && t >= eventWave * 17)
        {
            Wave(eventWave);
            eventWave++;
        }
        bool clear = eventFoes.All(f => !f.E.Alive || f.E.Seed != f.Seed || f.E.State == EnemyState.Dying);
        if ((eventWave >= 3 && t >= 45 && clear) || t >= 60)
        {
            var at = eventAltar;
            eventAt = -1;
            B.Charges.Spikes = false;
            B.SpawnPickup(PickupKind.Chest, at.X, at.Z, 1, "strongbox");
            B.Events.Emit(new Ev.Shake { Amount = 0.3 });
            G.Announce(new Announcement("A strongbox", "The altar gives up what it kept", "reward", 2.6));
        }
    }

    /// <summary>One asking of the people's question: a ring of them up round her, then a line from
    /// one side with a champion leading it, then the ring again with more.</summary>
    void Wave(int k)
    {
        var p = B!.Player;
        string def = PickKind(people);
        int n = (int)Math.Round((8 + Chart.Tier + 3 * k) * Chart.PackSize);
        B.Charges.Spike(B, quiet: false);
        var at = new List<(double X, double Z)>();
        double a0 = R() * Math.Tau;
        for (int i = 0; i < n; i++)
        {
            double x, z;
            if (k == 1)
            {
                // A line across one side.
                double sx = -Math.Sin(a0), sz = Math.Cos(a0), off = (i - (n - 1) / 2.0) * 1.6;
                x = p.X + Math.Cos(a0) * 14 + sx * off; z = p.Z + Math.Sin(a0) * 14 + sz * off;
            }
            else
            {
                double ang = (double)i / n * Math.Tau + R() * 0.2, rr = 10 + R() * 3;
                x = p.X + Math.Cos(ang) * rr; z = p.Z + Math.Sin(ang) * rr;
            }
            if (!map.CanStand(x, z) || B.Collision.Blocked(x, z, 0.6)) continue;
            at.Add((x, z));
            B.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.9, Duration = 1.3, Hostile = true, Kind = TelegraphKind.Ground });
        }
        G.After(1.3, () =>
        {
            if (B == null || over) return;
            foreach (var (x, z) in at)
                if (Put(def, x, z, (x, z)) is { } e) { B.Rouse(e); eventFoes.Add((e, e.Seed)); }
            if (k != 1) return;
            if (Put(people.Champion, p.X + Math.Cos(a0) * 15, p.Z + Math.Sin(a0) * 15, (p.X, p.Z), elite: true, levelUp: 1) is { } c)
            {
                c.MaxHp = c.Hp = c.MaxHp * 1.5;
                Sign(c, people, 1 + Chart.Tier / 6);
                carriers[c.Id] = 2;
                B.Rouse(c);
                eventFoes.Add((c, c.Seed));
            }
        });
    }

    /* ---------------------------------------------------------- the ruler -- */

    void Ruler(bool again)
    {
        if (B == null) return;
        var bc = map.Boss;
        bossUp = true;
        bossAt = Seconds;
        var e = B.SpawnEnemy(people.Boss, bc.X, bc.Z, new Battle.SpawnOpts { Level = Level + 1, Elite = true, Style = SpawnStyle.Walk });
        if (e == null) return;
        script = ArenaBosses.For(people.Boss, this);
        boss = e;
        e.Boss = true;
        e.Named = new Named { Title = people.BossName };
        double mul = BossHealth * (again ? 0.5 : 1);
        e.MaxHp = e.Hp = e.MaxHp * mul;
        // Its blows as its people's champion's, not the night's ruler's third more: a day build carries
        // none of the ember's mending, and her bites took a level-ten warden from full in eight seconds.
        if (script != null)
        {
            script.FloorScale = BossFloors;
            script.Begin(e);
            Hooks.BossTick = (x, dt) => x == boss && script.Tick(x, dt);
            Hooks.OnBossHit = (x, school, dmg) => { if (x == boss) script.OnHit(x, school, dmg); };
            Hooks.OnBossStagger = x => { if (x == boss) script.OnStagger(x); };
        }
        // A boss allows one crowd run at a time, so its own marks are the ones read.
        B.Charges.Cap = 1;
        B.Events.Emit(new Ev.Focus { X = bc.X, Z = bc.Z, Duration = 1.6 });
        B.Events.Emit(new Ev.Shake { Amount = 0.45 });
        G.Announce(new Announcement(people.BossName, script != null ? $"{people.BossTitle} · Weakness: {script.WeaknessText}" : people.BossTitle, "danger", 3.4,
            again ? "It comes again" : "The map's ruler"));
        Objectives();
    }

    Battle IBossArena.B => B!;
    int IBossArena.Tier => BossTier;
    string IBossArena.BossName => people.BossName;
    bool IBossArena.Spare => false;
    bool IBossArena.Sworn(string oath) => Chart.Has(oath);
    double IBossArena.R() => R();
    Enemy? IBossArena.Spawn(string def, double x, double z, bool elite, SpawnStyle? style)
    {
        if (B == null) return null;
        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level, Elite = elite, Style = style ?? SpawnStyle.Walk });
        // What the ruler calls is its crowd, as at night (softened as the half hour's horde is): at the
        // map's full strength her drive's wolves were each a pack's worth, and every build fell to her.
        if (e != null && !elite) e.MaxHp = e.Hp = e.MaxHp / ArenaRun.FodderEase(30);
        return e;
    }
    bool IBossArena.CanStand(double x, double z) => map.CanStand(x, z) && !B!.Collision.Blocked(x, z, 0.6);
    void IBossArena.Say(string title, string? sub, string tone) => G.Announce(new Announcement(title, sub ?? "", tone, 2.4));
    void IBossArena.Bark(double x, double z, string text, string? speaker) => B?.Events.Emit(new Ev.Bark { X = x, Z = z, Text = text, Speaker = speaker });
    double IBossArena.HordeShare { set { } }
    void IBossArena.Won(double x, double z)
    {
        if (over || !bossUp || boss == null) return;
        foreach (var l in OnLoot(boss)) B!.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);
        RulerDown(x, z);
    }

    void RulerDown(double x, double z)
    {
        bossUp = false;
        bossTtk ??= Seconds - bossAt;
        boss = null;
        B!.Charges.Cap = 2;
        // Restless: it comes again once, at half its strength.
        if (Chart.Has("restless") && !restlessDone)
        {
            restlessDone = true;
            G.After(4, () => { if (!over) Ruler(true); });
            return;
        }
        cleared = true;
        bool first = firstClear = Atlas.Complete(G.Journey.World, Chart);
        way = map.CanStand(x, z) ? (x, z) : (B.Player.X, B.Player.Z);
        var (wx, wz) = way.Value;
        G.Look.AddLight(wx, 2.2, wz, "#8ab4ff", 3.2, 14, 0.08, 0.14, "#b8d0ff");
        Interactables.Add(new Interactable { Id = "way_out", X = wx, Z = wz, R = 2.6, Verb = "Leave", Name = "The way out", Hint = () => "The map is cleared", Act = Leave });
        B.Events.Emit(new Ev.Victory { X = x, Z = z });
        G.Announce(new Announcement($"{Chart.Name} is cleared", first ? "A new mark on the Wayfinder's atlas" : "The way out is open", "reward", 4, "Cleared"));
        Objectives();
    }

    /* ------------------------------------------------------------- spoils -- */

    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    /// <summary>A rarity at the map's tier: rarer finds the higher it is, and under the chart's rarity.</summary>
    int RarityRoll(double bonus = 1)
    {
        double roll = R() / (Chart.RarityBonus * bonus);
        return roll < 0.03 + Chart.Tier * 0.01 ? 3 : roll < 0.18 + Chart.Tier * 0.02 ? 2 : roll < 0.62 ? 1 : 0;
    }

    Loot Gear(double bonus = 1, int floor = 0) =>
        new(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Math.Max(floor, RarityRoll(bonus)), MapOffers.Lean(Chart.Map, people.Id));

    /// <summary>The people's material, as a day's kill drops it; a champion or keeper more.</summary>
    static string? Material(Enemy e) => e.Def.Family switch
    {
        Family.Wolf => "wolf_pelt", Family.Boar => "boar_hide", Family.Kerchief => "kerchief_cloth",
        Family.Lampling => "ember_shard", Family.Undead => "bone_dust", _ => null,
    };

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        double q = Chart.Quantity;
        if (Material(e) is { } m)
        {
            int n = e == boss ? 5 : carriers.ContainsKey(e.Id) ? 2 : R() < 0.25 * q ? 1 : 0;
            if (n > 0) o.Add(new Loot(PickupKind.Material, m, n));
        }
        if (e == boss)
        {
            int n = 3 + (R() < 0.5 * q ? 1 : 0) + (R() < 0.25 * q ? 1 : 0) + Atlas.Rank(G.Journey.World, Atlas.RulersHoard);
            for (int k = 0; k < n; k++) o.Add(Gear(1.5, 1));
            // Charts: one of its tier or one up, more under quantity; the first clear of a people at a
            // tier always gives the next tier (the ladder).
            bool first = !Atlas.Done(G.Journey.World, Chart.People, Chart.Tier);
            int charts = 1 + (R() < 0.4 * q ? 1 : 0) + (R() < 0.15 * q ? 1 : 0);
            for (int k = 0; k < charts; k++)
            {
                int tier = Chart.Tier + (k == 0 && first ? 1 : R() < 0.3 ? 1 : 0);
                var next = MapOffers.Peoples[(int)(R() * MapOffers.Peoples.Length)].Id;
                // The people's road: the charts lean toward the people followed.
                if (Atlas.Road(G.Journey.World) is { } road && R() < 0.2 * Atlas.Rank(G.Journey.World, Atlas.PeoplesRoad)) next = road;
                o.Add(new Loot(PickupKind.Item, Charts.Ref(Charts.Roll(rng, tier, k == 0 ? Chart.People : next, Chart.RarityBonus)), 1, true, 2));
            }
            return o;
        }
        if (carriers.Remove(e.Id, out int grade))
        {
            var w = G.Journey.World;
            int n = grade switch { 3 => 2, 2 => 2, _ => 1 }
                + (grade == 3 ? Atlas.Rank(w, Atlas.KeepersDue) : 0)
                + (grade < 3 && R() < 0.5 * Atlas.Rank(w, Atlas.MarkedMen) / Atlas.MaxRank ? 1 : 0);
            for (int k = 0; k < n; k++) o.Add(Gear(grade >= 3 ? 1.4 : 1, grade >= 3 && R() < 0.35 ? 2 : 0));
            // A rare pack or a keeper, now and then a chart.
            if (grade >= 2 && R() < 0.12 * q) o.Add(new Loot(PickupKind.Item, Charts.Ref(Charts.Roll(rng, Chart.Tier, Chart.People, Chart.RarityBonus)), 1, true, 2));
        }
        return o;
    }

    int opened;

    bool OnPickup(Pickup p)
    {
        if (p.Kind == PickupKind.Material && p.Ref != null) picked[p.Ref] = picked.GetValueOrDefault(p.Ref) + (int)Math.Max(1, Math.Round(p.Value));
        if (p.Kind == PickupKind.Chest && p.Ref == "strongbox" && B != null) Strongbox(p.X, p.Z);
        return true;
    }

    /// <summary>The event's strongbox: three to five things at the map's level (the atlas's "the
    /// keeper's due" adds), now and then a chart; flung out round it, and its opening shown.</summary>
    void Strongbox(double x, double z)
    {
        var loot = new List<Loot>();
        int n = 3 + (R() < 0.5 * Chart.Quantity ? 1 : 0) + (R() < 0.25 * Chart.Quantity ? 1 : 0);
        for (int k = 0; k < n; k++) loot.Add(Gear(1.3, 1));
        if (R() < 0.25 * Chart.Quantity) loot.Add(new Loot(PickupKind.Item, Charts.Ref(Charts.Roll(rng, Chart.Tier, Chart.People, Chart.RarityBonus)), 1, true, 2));
        var shown = new List<ChestItem>();
        foreach (var l in loot)
        {
            double a = R() * Math.Tau, d = 1.2 + R() * 1.6;
            if (B!.SpawnPickup(l.Kind, x + Math.Cos(a) * d, z + Math.Sin(a) * d, l.Value, l.Ref) is { } pk)
            {
                pk.Persistent = true;
                if (l.Rarity is { } r) pk.Tier = r;
                pk.Lean = l.Lean;
            }
            if (l.Ref == null) continue;
            var chart = Charts.FromRef(l.Ref);
            var def = Items.Find(chart != null ? Charts.Item : l.Ref);
            shown.Add(new ChestItem(ChestItemKind.Gear, def?.Id ?? l.Ref, chart != null ? Charts.Title(chart) : def?.Name ?? l.Ref, def?.Icon ?? "chest", 0, 0,
                (Rarity)Math.Clamp(l.Rarity ?? 0, 0, 4), null, null));
        }
        opened++;
        G.Chest(new ChestOpened(x, z, opened, shown, "The strongbox", opened));
    }

    void OnKill(Enemy e, bool byPlayer)
    {
        if (byPlayer) kills++;
        if (e == boss && !over && bossUp) RulerDown(e.X, e.Z);
    }

    /* ------------------------------------------------------------- falls -- */

    /// <summary>A fall: half of what was picked up here is spilled. While falls remain (none, since the
    /// owner's rule) she is up again where she was last safe (the last altar she lit, or the map's
    /// start); the last closes the map.</summary>
    bool OnFall(Enemy? killer)
    {
        if (B == null || over) return false;
        falls++;
        Spill();
        if (falls >= FallsAllowed) return false;
        var p = B.Player;
        p.Hp = B.MaxHp;
        p.Iframes = 3;
        var safe = altars.Where(a => a.Lit).OrderByDescending(a => a.Area.Index).Select(a => a.Area).FirstOrDefault() ?? map.Start;
        p.X = safe.X; p.Z = safe.Z;
        p.PoisonT = p.BurnT = 0;
        // What was roused goes back to rest where it was.
        foreach (var e in B.Enemies.Living())
            if (e.Disposition == Disposition.Hostile && !e.Boss && e.Wake > 0) { e.Roused = false; e.X = e.HomeX; e.Z = e.HomeZ; }
        G.Revived(p.X, p.Z);
        G.Announce(new Announcement("You fall", $"Half of what you carried here is spilled. {FallsAllowed - falls} more and the map closes.", "danger", 3.2));
        Objectives();
        return true;
    }

    void Spill()
    {
        foreach (var (m, n) in picked.ToList())
        {
            int half = n / 2;
            if (half <= 0) continue;
            int took = Inventory.Take(G.Journey.Ch, m, half);
            picked[m] = n - took;
            spilled[m] = spilled.GetValueOrDefault(m) + took;
        }
    }

    public override bool OnDeath(string killer)
    {
        if (!over) Finish();
        return true;
    }

    public void Leave()
    {
        if (cleared && !over) Finish();
    }

    void Finish()
    {
        if (B == null) return;
        over = true;
        G.SetBoss(null);
        Result = new MapResult(Chart, cleared, Seconds, kills, falls, PacksCleared, PackCount, bossTtk, firstClear, new(spilled));
        G.Journey.BankGold(B);
        G.Journey.World.Map = null;
        // (the game tells it on its result page, then goes back to the Waystation)
        G.MapOver(Result, B.Player.Alive);
    }

    public override void Frame(double dt)
    {
        if (B == null || over) return;
        if (boss is { Alive: true } b && b.State != EnemyState.Dying)
            G.SetBoss(script != null ? script.Bar(people.BossName, people.BossTitle) : new BossBar(people.BossName, people.BossTitle, b.Hp, b.MaxHp));
        else G.SetBoss(null);
    }

    void Objectives()
    {
        var steps = new List<Step>
        {
            cleared ? new Step($"{people.BossName} is beaten: the map is cleared", Done: true)
            : bossUp ? new Step($"{people.BossName} has come: beat it")
            : new Step($"Find {people.BossName} at the end of the way"),
            new Step($"Altars lit: {altars.Count(a => a.Lit)} of {altars.Count}", Optional: true, Done: altars.All(a => a.Lit)),
            new Step(FallsAllowed > 1 ? $"Falls: {falls} of {FallsAllowed}" : "A fall ends the map", Optional: true),
        };
        foreach (var m in Chart.Rolled) steps.Add(new Step($"{m.Name}: {m.Says.ToLowerInvariant()}", Optional: true));
        G.SetObjectives([new Tracked("map", Chart.Name, TrackTone.Main, steps)]);
    }

    public override Dictionary<string, object?> Debug() => new()
    {
        ["tier"] = Chart.Tier, ["level"] = Level, ["packs"] = $"{PacksCleared}/{PackCount}", ["falls"] = falls, ["boss"] = bossUp,
    };
}
