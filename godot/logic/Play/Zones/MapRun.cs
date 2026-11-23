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
    double? BossTtk, bool FirstClear, Dictionary<string, int> Spilled)
{
    /// <summary>What was still lying at the end: gathered home, to Rook's storeroom, or broken down.</summary>
    public Journey.Gathered? Gathered { get; init; }
}

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
    /// <summary>(den r17 lead) true lays the kit's long bones (halloween/bone_*) in the den again; the game sets it from --den-kit-bone.</summary>
    public static bool DenKitBones;
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
        /// <summary>(P3) The den's recipe id this pack was built from ("" elsewhere).</summary>
        public string Recipe = "";
        /// <summary>(M3) When the first of it was roused (B.Time; -1: resting).</summary>
        public double Woke = -1;
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
    /// (Codex audit SU-086) Known by lifetime, never by slot: a carrier's entry goes with its death, credited or not, so a
    /// newcomer in its slot carries nothing.
    readonly Dictionary<Lifetime, int> carriers = new();

    ArenaBoss? script;
    Enemy? boss;
    double bossAt = -1;
    bool bossUp, cleared, over, restlessDone, returning, eventLit, firstClear;
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
    /// <summary>A dungeon's keeps (dungeon-gen, 15 Nov): its rooms' sockets all, its halls' four in five.</summary>
    public static double DungeonRoomKeep = 1.0, DungeonHallKeep = 0.8;
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
    /// <summary>The day curve was tuned for three day skills; six day slots by level 20 (CLASS_IDENTITY 3.7)
    /// and the Hands made day builds stronger. So each slot past three at the map's level adds PackPerSlot
    /// to every pack creature's health (champions' own multiples on top) and BossPerSlot to the ruler's.
    /// Measured (classes 14, tiers 1-6 x 8 seeds against integration 3ef34f61's three-slot curve): 0.9 and 0.4 put
    /// every tier's minutes, pack gap and ruler TTK within 5% (tiers 5-6 within 6%). The harness sets them with --maphp PACK,BOSS.</summary>
    public static double PackPerSlot = 0.9, BossPerSlot = 0.4;
    /// (bd-keys) The old keys-plus-autos ladder (SkillBook.OldBarSlotsAt, kept for this scaling and flagged for a re-tune)
    /// opens exactly as the six day slots did through the ninth level; the seventh (at the tenth) is unmeasured on maps, so
    /// the curve stays the measured one: slots past three, counted to six. Gear's auto skills (uncapped) are not counted
    /// either; a MapSim run decides both.
    static double DayMul(double per, int level) => 1 + per * Math.Max(0, Math.Min(6, SkillBook.OldBarSlotsAt(level)) - 3);

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
            // A dungeon's rooms were drawn to hold their packs: all of them stay, and most of its halls'.
            if (rng.Next() >= (map.Dungeon != null ? (clearing ? DungeonRoomKeep : DungeonHallKeep) : clearing ? ClearingKeep : WayKeep)) continue;
            packs.Add(new Pack { Spot = s, People = rival != null && rng.Next() < 1 / 3.0 ? rival : people });
        }
        foreach (var a in map.Altars) altars.Add(new Altar { Area = a });
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot, OnPickup = OnPickup, OnPlayerDeath = OnFall };
    }

    public override string Id => "map";

    /// <summary>Every map and dungeon shares the zone id "map", so its fog ("seen") outlived the run: the owner, 19 Nov
    /// ("entering den a second time minimap shows the explored previous map"). The fog is kept only for the same layout
    /// (the same dungeon or map and seed: a fall inside wakes her in the run as she left it and never comes back here; a
    /// reload of the same run keeps it); a new layout starts dark.</summary>
    public static void ForgetFogOfOtherLayout(WorldState world, Chart chart)
    {
        var zs = world.Zone("map");
        string layout = $"{chart.Dungeon}|{chart.Pinned}|{chart.Tier}|{chart.People}|{chart.Seed}";
        if (zs.TryGetValue("layout", out var f) && f.Str == layout) return;
        zs.Remove("seen");
        zs["layout"] = layout;
    }
    public override string SoundZone => map.DungeonTheme == "den" ? "den" : "map";
    public override (float[] Field, int Res, double Half, double Step)? SoundHoles =>
        map.DungeonTheme == "den" && map.HoleField is { } hf ? (hf, map.Meta.Res, map.Meta.Size / 2, map.Meta.Size / (map.Meta.Res - 1)) : null;
    public override string Name => Chart.Name;
    public override string? Region => map.Dungeon is { } dl ? $"{dl.Def.Region} · held by {people.Name}" : $"Tier {Chart.Tier} · {people.Name}";
    /// <summary>A dungeon (DungeonGen), not a Wayfinder's map: its caches, its way out past the ruler, no mark on the atlas.</summary>
    public bool IsDungeon => map.Dungeon != null;
    /// <summary>(P3) Whether a woken pack's foes cast the kit's shared charge (PackKit.Tells): a Wayfinder's map only,
    /// never a dungeon (DEN_ROSTER.md section 3, "the fix that matters, first").</summary>
    public bool KitCharges => !IsDungeon;
    public override bool Combat => true;
    public override IReadOnlyList<string> Creatures =>
        Charts.Kinds(people, Chart.Tier).Select(k => k.Def)
            .Concat(rival != null ? Charts.Kinds(rival, Chart.Tier).Select(k => k.Def) : [])
            .Concat(Charts.Guardians(people, Chart.Tier)).Append(people.Champion).Append(people.Boss)
            .Concat(DenRoster.For(Chart.Dungeon) ? DenRoster.Kinds : []).Distinct().ToList();
    /// <summary>By day: the maps are the day's build in the day's world, and a pack must be read
    /// before it is woken (at dusk the way was black past the start's fire).</summary>
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Day;
    /// <summary>A dungeon is lit as its theme is (the den: no sky; the ravine: an evening sun), not by the day's clock.</summary>
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) => map.Dungeon?.Def.Theme switch
    {
        "den" => Atmospheres.Den, "ravine" => Atmospheres.Ravine, _ => base.AtmosphereFor(t),
    };
    /// <summary>A pack and the ground round it in view: higher than the road's, nearer than a night's.</summary>
    /// <summary>The map's play camera: pitch (degrees) and distance (metres); the den's painted set casts along it
    /// (src/World/DungeonDress.Set.cs).</summary>
    public const double CamPitch = 62, CamDistance = 24;
    public override (double Pitch, double Distance)? Camera => (CamPitch, CamDistance);
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
    /// <summary>The placed packs' grades (0 plain, 1 magic, 2 rare), for probes of what a chart's oaths field.</summary>
    public IEnumerable<int> PackGrades => packs.Where(p => p.Placed).Select(p => p.Grade);
    /// <summary>(P3) The placed packs' recipe, grade and members' def ids (probes and tests of the den's roster).</summary>
    public IEnumerable<(string Recipe, int Grade, IReadOnlyList<string> Defs)> PackMakeup =>
        packs.Where(p => p.Placed).Select(p => (p.Recipe, p.Grade, (IReadOnlyList<string>)p.Members.Select(m => m.E.Def.Id).ToList()));
    /// <summary>(P3, measuring) Each placed pack's recipe, grade and members with their lifetimes (balance/Harness/DenFeel.cs:
    /// a pack's time to kill, how tight it stands under an area skill, how many fall together).</summary>
    public IEnumerable<(string Recipe, int Grade, IReadOnlyList<(Enemy E, double Seed)> Members)> PackLives =>
        packs.Where(p => p.Placed).Select(p => (p.Recipe, p.Grade, (IReadOnlyList<(Enemy E, double Seed)>)p.Members));
    /// <summary>Whether this very creature carries gear here (a pack's leader, a keeper; SU-086: by lifetime).</summary>
    public bool Carries(Enemy e) => carriers.ContainsKey(Lifetime.Of(e));
    /// <summary>Every pack and altar set down now, wherever she is (ClearNow; probes).</summary>
    public void PlaceAll()
    {
        if (B == null) return;
        foreach (var k in packs) if (!k.Placed) Place(k);
        foreach (var a in altars) if (!a.Placed) Place(a);
    }
    /// <summary>For the bots: where the packs still standing are, and the altars and the ruler.</summary>
    public IEnumerable<(double X, double Z)> Standing => packs.Where(p => !p.Cleared).Select(p => (p.Spot.X, p.Spot.Z));
    public MapBuild Ground => map;
    public MapResult? Result { get; private set; }

    /// <summary>The ruler's tier, for the counts its script uses (wolves in a drive, shields in a
    /// line): a night's tier per four of the atlas's.</summary>
    int BossTier => Math.Min(4, 1 + (Chart.Tier - 1) / 4);
    int Level => Chart.Level + Chart.FoeLevels;   // (SU-085) the Deep Dark's two levels

    public override void Begin(Battle b)
    {
        base.Begin(b);
        if (DenRoster.For(Chart.Dungeon)) b.Roster = DenRoster.Cuts();
        ForgetFogOfOtherLayout(G.Journey.World, Chart);
        b.Rules = Chart.Rules();
        b.InBounds = map.CanStand;
        // (P3, the den's ruler) A dungeon is rock: a pack's foe (its ruler too) held up by stone on its way to its slot round her
        // goes round by the flow field (Battle.PackRoundCover, as the arena's director has it). Without it the Pack-Mother stood
        // pressed into the rock 7 m from her for minutes (hollow seed 1), the flow field leading round it 8 m.
        if (IsDungeon) b.PackRoundCover = true;
        // What the gear inscribes works here, and only here (the scars' kit carries coals).
        var kit = Character.Kit(G.Journey.Ch);
        b.Wear(kit.Marks, kit.SkillMods);
        // Packs charge in waves of two, and only once roused; no spikes but the altar's event.
        b.Charges.Spikes = false;
        b.Charges.Cap = 2;
        b.Charges.Tell = "";
        // (M3 round 4) The world tier's press (world_tiers.json, the chart's tier's row: WorldTiers.ForMap): the kit's bite and
        // cadence, and the stand clock, read by PackKit as the story fights read them. Its health and damage stay the map's own.
        var wt = Content.WorldTiers.ForMap(Chart.Tier);
        b.KitDamageMul = wt.Kit; b.KitEveryMul = wt.KitEvery; b.StoryStand = wt.Stand;
        press = new PackKit(b);
        G.Announce(new Announcement(Chart.Name, Region ?? "", "zone", 3.4, IsDungeon ? "A dungeon" : "A Wayfinder's map"));
        // Her road, if it is due and was never raised (she reached its level where no card could say it): its card shows here, once.
        if (IsDungeon) G.Journey.RaiseRoad();
        // A dungeon's caches lie in its side rooms from the start: the deep branch's hoard is the richer.
        // Its rooms' dressing (MapGen.DressDungeon), made pieces and the kit's both, through the scene.
        // (the den's long bones at the size of its painted litter, DungeonDress.Decals: a metre-long femur read as a log)
        // (den r15 helper D) the kit's whole skull (an olive dome over a skull, r13 #14, r14 #6) and its rib cage (a repeat the per-screen
        // caps could not see: a made piece, not a card) are not laid in the den: the painted set's piles carry both, under DenCaps
        if (map.Dungeon != null) foreach (var p in map.Props)
            // (den r17 lead, R16 item 5: the yellow femurs at s11 room (1325,595) and s23 lair (1612,872) were these kit long bones,
            // laid here past Dressing's --den-kit-bone cut) the den's painted litter carries its bones: the kit's are not laid
            if (!(map.DungeonTheme == "den" && (p.Id is "halloween/skull" or "halloween/ribcage" or "halloween/skull_candle" || p.Id.StartsWith("halloween/bone_") && !DenKitBones)))
            G.Look.AddProp(p.Id, p.X, p.Z, p.Rot, p.Scale * (map.DungeonTheme == "den" && p.Id.StartsWith("halloween/bone_") ? 0.6 : 1));
        if (map.Dungeon is { } dl) foreach (var c in dl.Caches) b.SpawnPickup(PickupKind.Chest, c.X, c.Z, 1, c.Rich ? "hoard" : "strongbox");
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
            var e = B.SpawnEnemy(def, px, pz, new Battle.SpawnOpts { Level = Level + levelUp, Elite = elite, Style = style, Home = (home.X, home.Z, Leash), Wake = Wake });
            if (e != null && PackPerSlot != 0) e.MaxHp = e.Hp = e.MaxHp * DayMul(PackPerSlot, Level);
            return e;
        }
        return null;
    }

    /// <summary>Signs on a champion: from those its people have opened at this tier, never two that
    /// may not go together.</summary>
    void Sign(Enemy e, Denizens d, int n, string? first = null)
    {
        var open = Charts.Signs(d, Chart.Tier);
        // (the owner, 22 Nov, "Keep, no blocking": the champion stays as a plain tougher foe) The den's champions turn no blow:
        // a den champion's Ironbound roll is drawn as before and its slot spent, but the sign is not worn (no other sign in its
        // place, nothing added), so the den's other rolls do not move. The Sign stays for the arena and the Wayfinder's maps
        // (their Oath of Iron too).
        bool den = DenRoster.For(Chart.Dungeon);
        var worn = new List<string>();
        int slots = 0;
        if (first != null && Signs.Fits(e.Def, first, worn)) { slots++; if (!(den && first == "ironbound")) worn.Add(first); }
        while (slots < n)
        {
            var fit = open.Where(s => Signs.Fits(e.Def, s, worn) && !(den && s == "ironbound" && slots > worn.Count)).ToList();
            if (fit.Count == 0) break;
            string pick = fit[(int)(R() * fit.Count)];
            slots++;
            if (!(den && pick == "ironbound")) worn.Add(pick);
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
        if (DenRoster.For(Chart.Dungeon) && k.People == people) { PlaceRecipe(k); return; }
        k.Placed = true;
        var s = k.Spot;
        string main = PickKind(k.People), mix = PickKind(k.People);
        int n = Math.Clamp((int)Math.Round((4 + R() * 4) * s.Size * Chart.PackSize), 3, 14);
        double roll = R();
        // (SU-085) the Oath of Champions: twice the packs led by a champion (rare and magic alike)
        double el = Chart.Elites;
        k.Grade = roll < 0.1 * el ? 2 : roll < 0.35 * el ? 1 : 0;
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
                if (k.Grade > 0) carriers[Lifetime.Of(c)] = k.Grade;
                k.Members.Add((c, c.Seed));
            }
        }
    }

    /// <summary>(P3, DEN_ROSTER.md section 3) A den pack built from one of the recipes, not from the people's kinds.</summary>
    void PlaceRecipe(Pack k)
    {
        // Seam: a story beat may later replace one room's pack; the recipe pick below is the one place to swap.
        k.Placed = true;
        var s = k.Spot;
        double roll = R();
        double el = Chart.Elites;
        k.Grade = roll < 0.1 * el ? 2 : roll < 0.35 * el ? 1 : 0;
        var rec = k.Grade == 2 ? DenRoster.Recipes[R() < 0.5 ? 0 : 2] : DenRoster.Recipes[Math.Min(3, (int)(R() * 4))];
        k.Recipe = rec.Id;
        bool hardened = Chart.Has("hardened");
        bool tusker = rec.Id == "tusker";
        // The leader's kind: the recipe's own Ironback, or a champion added to it.
        string? added = null;
        if (k.Grade == 2) { string pick = R() < 0.5 ? "boar_ironback" : "wolf_alpha"; if (!(tusker && pick == "boar_ironback")) added = pick; }
        else if ((k.Grade == 1 || hardened) && !tusker) added = "wolf_alpha";
        bool leads = k.Grade > 0 || hardened;

        double f = s.Size * Chart.PackSize / Content.DungeonFights.Of(Chart.Dungeon).PackSize;
        var walk = new List<string>();
        int tele = 0;
        foreach (var p in rec.Parts)
        {
            if (p.Telegraphed) { tele += p.Count; continue; }
            int c = Math.Max(1, (int)Math.Round(p.Count * f));
            for (int i = 0; i < c; i++) walk.Add(p.Def);
        }
        if (added == "boar_ironback") tele++;
        string pad = rec.Id == "called" ? "wolf_runner" : "wolf";
        while (walk.Count < 2 * tele) walk.Add(pad);
        int room = Math.Max(0, 14 - tele - (added != null && added != "boar_ironback" ? 1 : 0));
        if (walk.Count > room) walk.RemoveRange(room, walk.Count - room);

        Enemy? lead = null;
        foreach (var p in rec.Parts)
        {
            if (!p.Telegraphed) continue;
            for (int i = 0; i < p.Count; i++)
            {
                bool ironLead = tusker && p.Def == "boar_ironback";
                if (Put(p.Def, s.X, s.Z, (s.X, s.Z), elite: ironLead) is not { } e) continue;
                k.Members.Add((e, e.Seed));
                if (ironLead) lead = e;
            }
        }
        foreach (var d in walk)
            if (Put(d, s.X, s.Z, (s.X, s.Z)) is { } e) k.Members.Add((e, e.Seed));
        if (added != null && Put(added, s.X, s.Z, (s.X, s.Z), elite: true, levelUp: 1) is { } c2)
        {
            k.Members.Add((c2, c2.Seed));
            lead = c2;
        }
        if (!leads || lead == null) return;
        int signs = k.Grade switch { 2 => 2 + (R() < 0.5 ? 1 : 0), 1 => 1, _ => 0 } + (Chart.Has("signed") && k.Grade > 0 ? 1 : 0);
        Sign(lead, k.People, Math.Max(signs, hardened ? 1 : 0), hardened ? k.People.Signs.FirstOrDefault() : null);
        if (k.Grade > 0) carriers[Lifetime.Of(lead)] = k.Grade;
    }

    /// <summary>An altar's keepers: one of the people's minibosses open at this tier (two under the
    /// twin guardians), wearing the map's Signs. Put down, it lights the altar.</summary>
    void Place(Altar a)
    {
        a.Placed = true;
        var pool = DenRoster.For(Chart.Dungeon) ? DenRoster.Guardians.ToList() : Charts.Guardians(people, Chart.Tier);
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
            carriers[Lifetime.Of(e)] = 3;
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
        if (lit != null) Event();
        Press(dt);
        // The ruler, in its clearing.
        if (!bossUp && !cleared && !returning && boss == null && Seconds >= RulerHold && Near(p, bc.X, bc.Z, bc.R + 2)) Ruler(false);
    }

    /* ------------------------------------------- the packs' kit (M3 round 4) -- */

    PackKit? press;
    /// <summary>(M3) Stand charges cast this run (the harness's tally).</summary>
    public int StandCharges => press?.StandCharges ?? 0;
    static bool Live((Enemy E, double Seed) m) => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying;

    /// <summary>A roused pack presses as a story fight's does (PackKit): its foes on foot (not its leader, nor an archer) charge
    /// with the kit's charge at the story pack's waits x the tier's kitEvery, and the stand clock sends a roused pack's foe at a
    /// stander. Campaign only (a map is a campaign fight: Journey.StartBattle).
    /// (P3, DEN_ROSTER.md, the owner 22 Nov "I approve den roster") Not in a dungeon: there no foe casts the kit's shared
    /// charge, and each foe keeps only its own move (the boar's charge is the den's one ordinary lane). Arena nights and
    /// story fights (Encounters) keep the kit; a Wayfinder's map keeps it too.</summary>
    void Press(double dt)
    {
        if (press == null || B == null || !B.Campaign) return;
        foreach (var k in packs)
        {
            if (!k.Placed || k.Cleared) continue;
            var up = k.Members.Where(Live).ToList();
            if (k.Woke < 0)
            {
                if (!up.Any(m => m.E.Roused)) continue;
                k.Woke = B.Time;
                // (P3) A den recipe pack wakes as one: Battle.Rouse wakes only its own faction, and a recipe mixes the Pack's wolves
                // with the wild boars (measured 22 Nov: its boars woke late and came in strung out behind the wolves).
                if (k.Recipe != "") foreach (var m in up) if (!m.E.Roused) B.Rouse(m.E);
            }
            if (!KitCharges) continue;
            press.Tells("charge", up, k.Woke, PackKit.FirstAfter, PackKit.Every, e => !e.Elite && e.Def.Ranged == null, null, null);
        }
        press.Stand(dt, null, () =>
        {
            var awake = new HashSet<Enemy>();
            foreach (var k in packs)
                if (k.Placed && !k.Cleared && k.Woke >= 0)
                    foreach (var m in k.Members) if (Live(m)) awake.Add(m.E);
            return awake;
        });
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
        // (SU-029) A second question waits its turn: it is asked once the first's strongbox is out.
        if (lit != null) queued.Enqueue(a.Area);
        else Ask(a.Area);
    }

    /// <summary>The people's question begins at its altar.</summary>
    void Ask(Area altar)
    {
        lit = new Lighting { Altar = altar, At = Seconds };
        B!.Charges.Spikes = true;
        G.Announce(new Announcement(EventName, "Hold the altar", "danger", 3, people.Name));
    }

    /* The map's event (the experience lead's shape): the people's own question, asked three times
     * over about fifty seconds at the lit altar, its tell first; then, its last asker down (or a
     * minute gone), a strongbox at the altar: three to five things at the map's level, and a chart
     * now and then. */
    sealed class Lighting
    {
        public required Area Altar;
        public double At;
        public int Wave;
        public readonly List<(Enemy E, double Seed)> Foes = new();
    }
    /// <summary>The question being asked, and any lit since that wait their turn (each its own altar).</summary>
    Lighting? lit;
    readonly Queue<Area> queued = new();
    int eventsLit;

    string EventName => people.Id switch
    {
        "pack" => "The Hunt", "dead" => "The Ford Rises", "lamplings" => "The Dig Opens", "kerchiefs" => "The Ambush", _ => "The Question",
    };

    void Event()
    {
        if (B == null || lit == null) return;
        var ev = lit;
        double t = Seconds - ev.At;
        if (ev.Wave < 3 && t >= ev.Wave * 17)
        {
            Wave(ev, ev.Wave);
            ev.Wave++;
        }
        bool clear = ev.Foes.All(f => !f.E.Alive || f.E.Seed != f.Seed || f.E.State == EnemyState.Dying);
        if ((ev.Wave >= 3 && t >= 45 && clear) || t >= 60)
        {
            var at = ev.Altar;
            lit = null;
            B.Charges.Spikes = false;
            B.SpawnPickup(PickupKind.Chest, at.X, at.Z, 1, "strongbox");
            B.Events.Emit(new Ev.Shake { Amount = 0.3 });
            G.Announce(new Announcement("A strongbox", "The altar gives up what it kept", "reward", 2.6));
            if (queued.Count > 0) Ask(queued.Dequeue());
        }
    }

    /// <summary>One asking of the people's question: a ring of them up round her, then a line from
    /// one side with a champion leading it, then the ring again with more.</summary>
    void Wave(Lighting ev, int k)
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
                if (Put(def, x, z, (x, z)) is { } e) { B.Rouse(e); ev.Foes.Add((e, e.Seed)); }
            if (k != 1) return;
            if (Put(people.Champion, p.X + Math.Cos(a0) * 15, p.Z + Math.Sin(a0) * 15, (p.X, p.Z), elite: true, levelUp: 1) is { } c)
            {
                c.MaxHp = c.Hp = c.MaxHp * 1.5;
                Sign(c, people, 1 + Chart.Tier / 6);
                carriers[Lifetime.Of(c)] = 2;
                B.Rouse(c);
                ev.Foes.Add((c, c.Seed));
            }
        });
    }

    /* ---------------------------------------------------------- the ruler -- */

    /// <summary>(den r18 lead, R17 item 8; pictures only) seconds into the run before the ruler may rise (--den-ruler-hold): the lair shot clear of the boss. 0: as before.</summary>
    public static double RulerHold;

    void Ruler(bool again)
    {
        // (SU-028) Never a second over a living one.
        if (B == null || boss is { Alive: true } up && up.State != EnemyState.Dying) return;
        var bc = map.Boss;
        bossUp = true;
        bossAt = Seconds;
        var e = B.SpawnEnemy(people.Boss, bc.X, bc.Z, new Battle.SpawnOpts { Level = Level + 1, Elite = true, Style = SpawnStyle.Walk });
        if (e == null) return;
        script = ArenaBosses.For(people.Boss, this);
        boss = e;
        e.Boss = true;
        e.Named = new Named { Title = people.BossName };
        double mul = BossHealth * Content.DungeonFights.Of(Chart.Dungeon).BossHealth * DayMul(BossPerSlot, Level) * (again ? 0.5 : 1);
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
            again ? "It comes again" : "The map's ruler") { YieldsToFight = true });
        Objectives();
    }

    Battle IBossArena.B => B!;
    int IBossArena.Tier => BossTier;
    string IBossArena.BossName => people.BossName;
    bool IBossArena.Spare => false;
    bool IBossArena.DenCut => DenRoster.For(Chart.Dungeon);
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
    bool IBossArena.HordeReturns => false;
    void IBossArena.Won(double x, double z)
    {
        if (over || !bossUp || boss == null) return;
        foreach (var l in OnLoot(boss)) B!.Spill(l, x, z);
        RulerDown(x, z);
    }

    void RulerDown(double x, double z)
    {
        bossUp = false;
        bossTtk ??= Seconds - bossAt;
        // (SU-030) Its script lets go of what it holds (Red Hand's cage, Snib's pits) on every path.
        if (boss is { } fallen) script?.Fell(fallen);
        boss = null;
        B!.Charges.Cap = 2;
        // Restless: it comes again once, at half its strength. (SU-028) The return is pending until
        // its callback takes it, never read as "no ruler yet" by the clearing's own spawn.
        if (Chart.Has("restless") && !restlessDone)
        {
            restlessDone = true;
            returning = true;
            G.After(4, () => { if (!returning) return; returning = false; if (!over) Ruler(true); });
            return;
        }
        cleared = true;
        bool first = firstClear = !IsDungeon && Atlas.Complete(G.Journey.World, Chart);
        // A dungeon's way out is cut past the ruler's room (DungeonGen); a map's opens where the ruler fell.
        way = map.Dungeon is { } dl ? dl.Exit : map.CanStand(x, z) ? (x, z) : (B.Player.X, B.Player.Z);
        var (wx, wz) = way.Value;
        G.Look.AddLight(wx, 2.2, wz, "#8ab4ff", 3.2, 14, 0.08, 0.14, "#b8d0ff");
        Interactables.Add(new Interactable { Id = "way_out", X = wx, Z = wz, R = 2.6, Verb = "Leave", Name = "The way out", Hint = () => "The map is cleared", Act = Leave });
        B.Events.Emit(new Ev.Victory { X = x, Z = z });
        B.Events.Emit(new Ev.WayOutOpen { X = wx, Z = wz });  // the way out and its banner are already one moment here
        G.Announce(new Announcement(IsDungeon ? $"{people.BossName} is dead" : $"{Chart.Name} is cleared", first ? "A new mark on the Wayfinder's atlas" : IsDungeon ? "The way out is open, past where it kept" : "The way out is open", "reward", 4, "Cleared"));
        Objectives();
    }

    /* ------------------------------------------------------------- spoils -- */

    /// <summary>What a carrier leaves (docs/design/LOOT_DESIGN.md §5): gear rolled whole at the map's
    /// level (its make climbs with the tier), under the chart's rarity and quantity, the people's
    /// material where a roll is not gear; extra: further rolls the atlas has earned.</summary>
    List<Loot> Gear(DropSource source, int extra = 0, int levelUp = 0) => G.Journey.Drops(new DropCtx
    {
        Source = source, Level = Chart.ItemLevel + levelUp, People = Chart.People, Lean = MapOffers.Lean(Chart.Map, people.Id),
        Luck = B!.Stats.Get(Stat.Luck), Rarity = Chart.RarityBonus, Quantity = Chart.Quantity, Extra = extra, Tier = Chart.Tier, R = R, Dungeon = Chart.Dungeon,
    });

    /// <summary>The people's material, as their carriers leave it. In the atlas the Dig's lamplings carry
    /// its picks and nails, old iron: their ember shards are the night's (docs/CRAFTING_DESIGN.md 20.1,
    /// fire is the scars' and iron the atlas's; a lamplings' map paid 73 shards, a long scar's worth).</summary>
    static string? Material(Enemy e) => e.Def.Family switch
    {
        Family.Wolf => "wolf_pelt", Family.Boar => "boar_hide", Family.Kerchief => "kerchief_cloth",
        Family.Lampling => Crafting.Iron, Family.Undead => "bone_dust", _ => null,
    };

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        double q = Chart.Quantity;
        // From what visibly carries it (crafting's measure, design 20.7): the ruler three, a keeper two, a
        // pack's leader one, the rank and file none, more under the chart's quantity. A quarter of every
        // kill paid 75-100 a map, where a night pays at most eight of a kind and a pin takes two.
        if (Material(e) is { } m)
        {
            int n = (int)Math.Floor((e == boss ? 3 : carriers.TryGetValue(Lifetime.Of(e), out int g) ? g >= 3 ? 2 : 1 : 0) * q + (e == boss || carriers.ContainsKey(Lifetime.Of(e)) ? R() : 0));
            if (n > 0) o.Add(new Loot(PickupKind.Material, m, n));
        }
        if (e == boss)
        {
            o.AddRange(Gear(DropSource.MapRuler, Atlas.Rank(G.Journey.World, Atlas.RulersHoard)));
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
            // Now and then a thing of its own, carrying how it fought: a Mark for Vonnra to inscribe
            // (crafting's, design 20.3), finer the harder the map.
            if (Crafting.RulerMark(Chart.People, Chart.Tier, rng) is { } mark) o.Add(new Loot(PickupKind.Item, mark.Item, 1, true, mark.Grade));
            return o;
        }
        if (carriers.Remove(Lifetime.Of(e), out int grade))
        {
            var w = G.Journey.World;
            int extra = (grade == 3 ? Atlas.Rank(w, Atlas.KeepersDue) : 0)
                + (grade < 3 && R() < 0.5 * Atlas.Rank(w, Atlas.MarkedMen) / Atlas.MaxRank ? 1 : 0);
            o.AddRange(Gear(grade switch { 3 => DropSource.MapKeeper, 2 => DropSource.MapPackFine, _ => DropSource.MapPack }, extra));
            // A rare pack or a keeper, now and then a chart.
            if (grade >= 2 && R() < 0.12 * q) o.Add(new Loot(PickupKind.Item, Charts.Ref(Charts.Roll(rng, Chart.Tier, Chart.People, Chart.RarityBonus)), 1, true, 2));
        }
        return o;
    }

    int opened;

    bool OnPickup(Pickup p)
    {
        if (p.Kind == PickupKind.Material && p.Ref != null) picked[p.Ref] = picked.GetValueOrDefault(p.Ref) + (int)Math.Max(1, Math.Round(p.Value));
        if (p.Kind == PickupKind.Chest && p.Ref is "strongbox" or "hoard" && B != null) Strongbox(p.X, p.Z, hoard: p.Ref == "hoard");
        return true;
    }

    /// <summary>The event's strongbox: three to five things at the map's level (the atlas's "the
    /// keeper's due" adds), now and then a chart; flung out round it, and its opening shown
    /// (told: false spills it unshown, for a whole map cleared at once).</summary>
    void Strongbox(double x, double z, bool told = true, bool hoard = false)
    {
        var loot = Gear(DropSource.Strongbox, extra: hoard ? 2 : 0, levelUp: 1);
        if (R() < 0.25 * Chart.Quantity) loot.Add(new Loot(PickupKind.Item, Charts.Ref(Charts.Roll(rng, Chart.Tier, Chart.People, Chart.RarityBonus)), 1, true, 2));
        var shown = new List<ChestItem>();
        foreach (var l in loot)
        {
            double a = R() * Math.Tau, d = 1.2 + R() * 1.6;
            double px = x + Math.Cos(a) * d, pz = z + Math.Sin(a) * d;
            if (B!.Spill(l with { Persistent = true }, px, pz) is { } pk) { px = pk.X; pz = pk.Z; }
            if (l.Ref == null || l.Kind == PickupKind.Material) continue;
            var chart = Charts.FromRef(l.Ref);
            var def = Items.Find(chart != null ? Charts.Item : l.Ref);
            // Where it lies: its opening ends with each thing going down to its place on the ground.
            shown.Add(new ChestItem(ChestItemKind.Gear, def?.Id ?? l.Ref, chart != null ? Charts.Title(chart) : def?.Name ?? l.Ref, def?.Icon ?? "chest", 0, 0,
                (Rarity)Math.Clamp(l.Rarity ?? 0, 0, 4), null, null, px, pz));
        }
        if (!told) return;
        opened++;
        G.Chest(new ChestOpened(x, z, opened, shown, hoard ? "The hoard" : IsDungeon ? "A cache" : "The strongbox", opened));
    }

    /// <summary>The whole map as a thorough survivor leaves it, at once: every pack and keeper set
    /// down and felled by her hand, the event's strongbox spilled at its altar, the ruler called and
    /// felled, and the gold drawn to her. What a map pays, seen without the walk (--clear T in the
    /// game; probes of the atlas's economy).</summary>
    public void ClearNow()
    {
        if (B == null || over || cleared) return;
        PlaceAll();
        foreach (var e in B.Enemies.Living().ToList())
            if (e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying) B.KillEnemy(e, true, null);
        foreach (var a in altars) a.Lit = true;
        if (altars.FirstOrDefault() is { } first) { eventLit = true; Strongbox(first.Area.X, first.Area.Z, told: false); }
        // (A restless ruler is called and felled twice; its pending return is taken here, not in 4 s.)
        for (int i = 0; i < 2 && !cleared && !over; i++)
        {
            if (!bossUp) { bool again = returning; returning = false; Ruler(again); }
            if (boss is { } b) B.KillEnemy(b, true, null);
        }
        foreach (var p in B.Pickups.Items) if (p.Alive && p.Kind == PickupKind.Gold) p.Pulled = true;
    }

    void OnKill(Enemy e, bool byPlayer)
    {
        if (byPlayer) kills++;
        carriers.Remove(Lifetime.Of(e));   // (SU-086) any death; a credited one was paid in OnLoot, just before
        if (e == boss && !over && bossUp) RulerDown(e.X, e.Z);
    }

    /* ------------------------------------------------------------- falls -- */

    /// <summary>A fall on a Wayfinder's map: half of what was picked up here is spilled. While falls remain (none,
    /// since the owner's rule) she is up again where she was last safe (the last altar she lit, or the map's
    /// start); the last closes the map. A dungeon's fall is handed on: she falls, and OnDeath wakes her.</summary>
    bool OnFall(Enemy? killer)
    {
        if (B == null || over || IsDungeon) return false;
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

    /// <summary>Her death: a Wayfinder's map closes. A dungeon closes nothing (the owner, 19 Nov: "dying dosn't put us at
    /// the front of the dungeon, it puts us outside, and makes the dungeon start all over - that seems bad"): she falls as
    /// she does out on the Verge, and gets up whole at its mouth, inside (LampRise.Stand, the Verge's own rise), the
    /// dungeon as she left it: its dead stay dead, its loot lies where it fell, its caches stay open, nothing is spilled.
    /// What she had roused goes back to rest, and its ruler and champions are whole again, as out on the Verge.</summary>
    public override bool OnDeath(string killer)
    {
        if (IsDungeon && B is { } battle && !over)
        {
            falls++;
            G.After(RiseAfter, () =>
            {
                if (over || B != battle) return;
                foreach (var e in battle.Enemies.Living())
                    if (e.Disposition == Disposition.Hostile && !e.Boss && e.Wake > 0) { e.Roused = false; e.X = e.HomeX; e.Z = e.HomeZ; }
                LampRise.Stand(G, battle, map.Start.X, map.Start.Z);
                G.Announce(new Announcement("You fall", "You wake at the mouth. What you cleared stays cleared.", "danger", 3.2));
                Objectives();
            });
            return true;
        }
        if (!over) Finish();
        return true;
    }

    /// <summary>A dungeon's fall: seconds on the ground before she gets up at its mouth (the Verge's 2.6).</summary>
    public const double RiseAfter = 2.6;

    public void Leave()
    {
        if (cleared && !over) Finish();
    }

    void Finish()
    {
        if (B == null) return;
        over = true;
        G.SetBoss(null);
        // What the filter shows and is still lying comes home; what it hid is broken down (LOOT_DESIGN §6.2).
        var gathered = G.Journey.Gather(B);
        Result = new MapResult(Chart, cleared, Seconds, kills, falls, PacksCleared, PackCount, bossTtk, firstClear, new(spilled)) { Gathered = gathered };
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
            IsDungeon ? new Step(falls > 0 ? $"Falls: {falls} (each wakes you at the mouth)" : "A fall wakes you at the mouth", Optional: true)
            : new Step(FallsAllowed > 1 ? $"Falls: {falls} of {FallsAllowed}" : "A fall ends the map", Optional: true),
        };
        foreach (var m in Chart.Rolled) steps.Add(new Step($"{m.Name}: {m.Says.ToLowerInvariant()}", Optional: true));
        G.SetObjectives([new Tracked("map", Chart.Name, TrackTone.Main, steps)]);
    }

    public override Dictionary<string, object?> Debug() => new()
    {
        ["tier"] = Chart.Tier, ["level"] = Level, ["packs"] = $"{PacksCleared}/{PackCount}", ["falls"] = falls, ["boss"] = bossUp,
    };
}
