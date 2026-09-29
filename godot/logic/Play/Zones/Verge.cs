using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* Thornhollow Verge, alive (the web game's game/zones/verge.ts).
 *
 * The wood is dangerous in proportion to what has been left undone: while
 * the Pack is sick and nobody has made peace with it, wolves come in packs;
 * the road east belongs to whoever has scared the Kerchiefs least; the
 * diggers mind their pump and nothing else unless you give them a reason.
 * Every group here reads the world before it decides what you are - the
 * same wolf is an enemy, a stranger or a friend depending on what you did
 * last week.
 *
 * The places the quests need are here too, each with the handful of things
 * a clever player might try. */
public sealed class Verge : ZoneRuntime
{
    /// <summary>Where the Coyle wagons' ruts leave the road for the ravine.</summary>
    static readonly XZ RutsAt = new(-52, 40);

    /// <summary>The caravan quest settles once both halves of it have.</summary>
    const string CaravanSettle = """{ "if": { "all": [{ "fact": "caravan.survivors", "exists": true }, { "fact": "caravan.cargo", "exists": true }] }, "then": [{ "quest": { "id": "caravan", "status": "resolved" } }] }""";

    public override string Id => "verge";
    public override string Name => "Thornhollow Verge";
    public override string? Region => "East of the Waystation";
    public override bool Combat => true;
    public override IReadOnlyList<string> Creatures { get; } =
        ["wolf", "wolf_blighted", "wolf_alpha", "boar", "lampling", "lampling_sapper", "footpad", "pillager", "bruiser", "enforcer", "risen", "risen_warrior", "risen_archer"];

    readonly PathIndex road, stream;
    readonly int postFire, blindFire, pumpLight;
    readonly List<(double X, double Z, int Collider, string Node)> brambles = new();
    readonly string[] cageNodes;
    double spawnT = 4, surgeT = 70, dispT, stayT, chargeT = -1, trackT;
    readonly HashSet<string> seen = new();
    readonly bool[] cagesOpen = new bool[3];
    readonly double[] brambleHp;
    Enemy? greymuzzle, redcowl, snib, nemesis;
    readonly List<Enemy> roostCrew = new(), digCrew = new();
    bool hollowSpawned, roostSpawned, digSpawned, sinkSpawned, restUsed;

    XZ V(string place) => P("V", place);

    public Verge(IZoneHost host, ZoneMeta meta) : base(host, meta)
    {
        static List<(double, double)> Pts(double[][] p) => p.Select(q => (q[0], q[1])).ToList();
        road = new PathIndex(Pts(meta.Paths["VROAD"]), 14, 8, meta.Paths.TryGetValue("ROAD_KEYS", out var rk) ? Pts(rk) : null);
        stream = new PathIndex(Pts(meta.Paths["STREAM"]), 14, 8, meta.Paths.TryGetValue("STREAM_KEYS", out var sk) ? Pts(sk) : null);
        var refs = meta.Refs;
        postFire = refs.GetProperty("postFire").GetInt32();
        blindFire = refs.GetProperty("blindFire").GetInt32();
        foreach (var b in refs.GetProperty("brambles").EnumerateArray())
            brambles.Add((b.GetProperty("x").GetDouble(), b.GetProperty("z").GetDouble(), b.GetProperty("collider").GetInt32(), b.GetProperty("node").GetString()!));
        brambleHp = brambles.Select(_ => 260.0).ToArray();
        cageNodes = refs.GetProperty("cages").EnumerateArray().Select(c => c.GetString()!).ToArray();
        var pump = V("pump");
        pumpLight = meta.Lights.FindIndex(l => Dist(l.X, l.Z, pump.X, pump.Z) < 1);
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot, OnHitProp = OnHitProp };
        MakeInteractables();
    }

    public double StreamDist(double x, double z) => stream.Dist(x, z);
    public double RoadDist(double x, double z) => road.Dist(x, z);

    /* ------------------------------------------------------ dispositions -- */

    bool WolvesFriendly() => Standings.WolvesFriendly(C);
    bool KerchiefsFriendly() => Standings.KerchiefsFriendly(C);
    bool DiggersFriendly() => Standings.DiggersFriendly(C);
    // At their own den, the Pack holds off for someone who knows how to come
    // to it (a hunter's lore, Maeca's advice, a wolf's fang worn openly):
    // long enough for Greymuzzle to come out and look.
    bool HollowCalm() => Standings.HollowCalm(C);
    static bool Up(Enemy? e) => e is { Alive: true } && e.State != EnemyState.Dying;

    void SetDisposition(Enemy e)
    {
        if (e.Faction == Faction.Pack && e.Disposition != Disposition.Ally)
        {
            bool den = e.Tag is "hollow" or "greymuzzle";
            e.Disposition = (den ? HollowCalm() : WolvesFriendly()) ? Disposition.Neutral : Disposition.Hostile;
        }
        if (e.Faction == Faction.Kerchief) e.Disposition = KerchiefsFriendly() ? Disposition.Neutral : Disposition.Hostile;
        if (e.Faction == Faction.Lampling && e.Tag?.StartsWith("dig") == true) e.Disposition = DiggersFriendly() ? Disposition.Neutral : Disposition.Hostile;
    }

    void TurnHostile(string key, string? text = null)
    {
        if (F(key).Truthy) return;
        W.Facts[key] = true;
        if (B != null) foreach (var e in B.Enemies.Living()) SetDisposition(e);
        if (text != null) G.Announce(new Announcement(text, null, "danger", 2.4));
    }

    // What comes at you grows with the days, with your ember, and with how
    // long you have stayed out: the wood keeps up with you.
    int Level() => 2 + W.Day / 2 + (B?.EmberLevel ?? 1) / 4 + (int)Math.Floor(stayT / 120);

    /* ------------------------------------------------------------ spawns -- */

    bool OpenGround(double x, double z) => B != null && !B.Collision.Blocked(x, z, 0.7) && Math.Abs(x) < 136 && Math.Abs(z) < 136 && StreamDist(x, z) > 3;

    double R() => G.Rng.NextDouble();

    List<Enemy> SpawnGroup(string def, int n, double cx, double cz, double spread, string? tag = null, double? home = null, SpawnStyle style = SpawnStyle.Walk)
    {
        var out_ = new List<Enemy>();
        for (int i = 0; i < n; i++)
            for (int t = 0; t < 8; t++)
            {
                double a = R() * Math.PI * 2, d = R() * spread;
                double x = cx + Math.Cos(a) * d, z = cz + Math.Sin(a) * d;
                if (!OpenGround(x, z)) continue;
                var e = B!.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level(), Style = style, Tag = tag, Home = home is double h ? (cx, cz, h) : null });
                if (e != null) { SetDisposition(e); out_.Add(e); }
                break;
            }
        return out_;
    }

    bool KerchiefsOut() => !KerchiefsFriendly() && F("redcowl").Str is not ("tricked" or "dead") && !F("roost.cleared").Truthy;

    /// <summary>The wood's own pressure: what comes at you depends on where
    /// you are, what you have made peace with, the hour, how bright your
    /// ember burns and how long you have been out here.</summary>
    void Director(double dt)
    {
        if (B == null) return;
        var p = B.Player;
        spawnT -= dt; surgeT -= dt; stayT += dt;
        // Quiet near the gate and around a lit fire.
        var post = V("post");
        if (p.X < -112 || (Dist(p.X, p.Z, post.X, post.Z) < 16 && G.Look.IsLit(postFire))) return;
        int hostile = B.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile);
        bool night = W.Time == TimeOfDay.Night;
        int ember = B.EmberLevel;
        // The longer you stay, the more of the wood knows you are here.
        double tension = Math.Min(1, stayT / 300);
        double cap = (night ? 48 : 34) + Math.Min(42, ember * 2.6) + tension * 12;
        if (spawnT <= 0 && hostile < cap)
        {
            spawnT = (night ? 2.0 : 2.7) * Math.Max(0.5, 1 - ember * 0.03) * (1 - tension * 0.2);
            // Some come from where you are heading: running is not a way out of the wood.
            bool moving = Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz) > 1;
            double a = moving && R() < 0.45 ? Math.Atan2(p.Vz, p.Vx) + (R() - 0.5) * 1.6 : R() * Math.PI * 2;
            double d = 17 + R() * 5;
            double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
            double pop = F("beasts.population").IsNull ? 60 : F("beasts.population").Number;
            var roost = V("roost"); var dig = V("dig"); var vault = V("vault"); var sink = V("sinkhole");
            bool nearRoost = Dist(x, z, roost.X, roost.Z) < 60 || (x > 30 && Math.Abs(z) < 20);
            bool nearDig = Dist(x, z, dig.X, dig.Z) < 60;
            bool nearVault = Dist(x, z, vault.X, vault.Z) < 45;
            bool nearSink = Dist(x, z, sink.X, sink.Z) < 45;
            bool onRoad = RoadDist(x, z) < 14;
            int extra = ember / 3;
            double r = R();
            int Few() => 3 + (int)Math.Floor(R() * 3) + extra;
            // Place first, then the wood at large.
            if (night && nearVault) SpawnGroup(r < 0.3 ? "risen_warrior" : "risen", Few(), x, z, 4, style: SpawnStyle.Rise);
            else if (nearRoost && KerchiefsOut()) SpawnGroup(r < 0.25 ? "pillager" : r < 0.35 ? "bruiser" : "footpad", 2 + (int)Math.Floor(R() * 3) + extra / 2, x, z, 4);
            // The diggers mind their pump unless given a reason; then they come up out of the ground.
            else if (nearDig && !DiggersFriendly() && R() < 0.7) SpawnGroup("lampling", Few(), x, z, 4, "dig:crew", style: SpawnStyle.Burrow);
            // Near the pit, since the tremor: lamplings that went down and came back wrong.
            else if (nearSink && F("tremor.felt").Truthy && R() < 0.5) SpawnGroup("lampling", Few(), x, z, 4, "feral", style: SpawnStyle.Burrow);
            else
            {
                // The wood at large: a weighted pick of whatever is still out here.
                var pool = new List<(double W, Action Fn)>();
                if (!WolvesFriendly() && pop > 5)
                {
                    bool sick = F("beasts.outcome").Str != "cured" && StreamDist(x, z) < 30;
                    pool.Add((3 * (pop / 60), () => SpawnGroup(sick && r < 0.35 ? "wolf_blighted" : "wolf", 3 + (int)Math.Floor(R() * 3 * (pop / 60)) + extra, x, z, 4)));
                }
                // Every night the dark climbs out of the ground; the Verge is no different.
                if (night) pool.Add((2.2, () => SpawnGroup(r < 0.2 ? "risen_warrior" : r < 0.42 ? "risen_archer" : "risen", Few(), x, z, 4, style: SpawnStyle.Rise)));
                if (onRoad && KerchiefsOut() && W.Day >= 2) pool.Add((1, () => SpawnGroup("footpad", 2 + (int)Math.Floor(R() * 2) + extra / 2, x, z, 3)));
                pool.Add((1, () => SpawnGroup("boar", 1 + (int)Math.Floor(R() * 2) + extra / 3, x, z, 3)));
                double pick = R() * pool.Sum(q => q.W);
                foreach (var (wt, fn) in pool) { pick -= wt; if (pick <= 0) { fn(); break; } }
            }
        }
        // Now and then, a surge: the wood noticing you.
        if (surgeT <= 0)
        {
            surgeT = (night ? 40 : 52) + R() * 25 - tension * 10;
            double a = R() * Math.PI * 2;
            double sx = p.X + Math.Cos(a) * 18, sz = p.Z + Math.Sin(a) * 18;
            int size = 9 + Math.Min(16, (int)Math.Floor(ember * 1.3)) + (int)Math.Floor(tension * 6);
            // A closing ring: every way out has something in it.
            List<Enemy> Ring(string def, int n, SpawnStyle style = SpawnStyle.Walk)
            {
                var out_ = new List<Enemy>();
                for (int i = 0; i < n; i++)
                {
                    double t = (double)i / n * Math.PI * 2 + R() * 0.2, rr = 14 + R() * 3;
                    out_.AddRange(SpawnGroup(def, 1, p.X + Math.Cos(t) * rr, p.Z + Math.Sin(t) * rr, 1.5, style: style));
                }
                return out_;
            }
            var group = new List<Enemy>();
            string shout = "";
            bool big = ember >= 5 && R() < 0.5;
            double pop = F("beasts.population").IsNull ? 60 : F("beasts.population").Number;
            if (!WolvesFriendly() && pop > 20) { group = big ? Ring("wolf", size) : SpawnGroup("wolf", size, sx, sz, 5); shout = big ? "Wolves — all around!" : "Howling — close!"; }
            else if (night) { group = big ? Ring("risen", size + 4, SpawnStyle.Rise) : SpawnGroup("risen", size, sx, sz, 5, style: SpawnStyle.Rise); shout = "The ground is moving."; }
            else if (KerchiefsOut()) { group = SpawnGroup("footpad", (int)Math.Ceiling(size * 0.6), sx, sz, 4); shout = "Red kerchiefs in the trees!"; }
            // A brighter ember draws something bigger with the crowd.
            if (group.Count > 0 && ember >= 6)
            {
                var lead = B.SpawnEnemy(group[0].Def.Id, sx, sz, new Battle.SpawnOpts
                {
                    Level = Level() + 1, Elite = true, Style = night && group[0].Def.Id == "risen" ? SpawnStyle.Rise : SpawnStyle.Walk,
                });
                if (lead != null) SetDisposition(lead);
            }
            if (shout != "")
            {
                B.Events.Emit(new Ev.Bark { X = p.X + Math.Cos(a) * 14, Z = p.Z + Math.Sin(a) * 14, Text = shout });
                B.Events.Emit(new Ev.Shake { Amount = 0.2 });
            }
        }
    }

    /* ------------------------------------------------------------ places -- */

    void Approach()
    {
        if (B == null) return;
        var p = B.Player;
        bool Near(XZ pt, double r) => Dist(p.X, p.Z, pt.X, pt.Z) < r;
        var hollow = V("hollow"); var roost = V("roost"); var dig = V("dig"); var pump = V("pump"); var sink = V("sinkhole");
        // Wolf Hollow.
        if (!hollowSpawned && Near(hollow, 38) && F("greymuzzle").Str != "dead")
        {
            hollowSpawned = true;
            greymuzzle = B.SpawnEnemy("wolf_alpha", hollow.X, hollow.Z, new Battle.SpawnOpts { Level = Level(), Tag = "greymuzzle", Home = (hollow.X, hollow.Z, 14) });
            if (greymuzzle != null) SetDisposition(greymuzzle);
            SpawnGroup("wolf", 5, hollow.X, hollow.Z, 9, "hollow", 14);
            if (F("beasts.outcome").Str != "cured") SpawnGroup("wolf_blighted", 3, hollow.X, hollow.Z, 6, "hollow", 8);
            if (HollowCalm()) G.Say("The wolves watch you come. None of them move to stop you.", null, 4);
            else G.Say("Low growling from every side of the Hollow.", null, 3);
        }
        // Redcowl's Roost.
        if (!roostSpawned && Near(roost, 42) && F("redcowl").Str != "tricked" && !F("roost.cleared").Truthy)
        {
            roostSpawned = true;
            if (seen.Add("roost")) G.Apply("""[{ "quest": { "id": "caravan", "status": "active", "entry": "roost_found" } }, { "learn": "hint.roost" }]""");
            roostCrew.AddRange(SpawnGroup("footpad", 4, roost.X, roost.Z + 4, 10, "roost", 16));
            roostCrew.AddRange(SpawnGroup("pillager", 2, roost.X + 6, roost.Z - 2, 6, "roost", 14));
            roostCrew.AddRange(SpawnGroup("bruiser", 2, roost.X - 4, roost.Z + 8, 6, "roost", 12));
            if (!KerchiefsFriendly() && F("redcowl").Str != "dead") PromoteRedcowl();
            else if (F("redcowl").Str is not ("dead" or "furious")) PlaceRedcowl();
            if (KerchiefsFriendly()) G.Say("Red cloth at every tent. They see your colours and go back to their dice.", null, 4);
        }
        if (roostSpawned && !KerchiefsFriendly() && !F("roost.hostile").Truthy && Near(roost, 26) && roostCrew.Any(Up)) TurnHostile("roost.hostile", "The Roost has seen you");
        // The Dig.
        if (!digSpawned && Near(dig, 44) && F("dig.pump").Str != "blown")
        {
            digSpawned = true;
            if (!F("snib.dead").Truthy)
            {
                snib = B.SpawnEnemy("lampling", pump.X + 4, pump.Z + 3, new Battle.SpawnOpts { Level = Level(), Tag = "dig:snib", Home = (pump.X + 4, pump.Z + 3, 3) });
                if (snib != null) { snib.Named = new Named { Title = "Snib, Foreman" }; SetDisposition(snib); }
            }
            digCrew.AddRange(SpawnGroup("lampling", 6, dig.X - 4, dig.Z + 4, 12, "dig", 16));
            digCrew.AddRange(SpawnGroup("lampling_sapper", 2, dig.X, dig.Z, 8, "dig", 14));
        }
        if (digSpawned && DiggersFriendly() && Near(pump, 5) && !(W.Npcs.TryGetValue("snib", out var sn) && sn.Flags.TryGetValue("met", out var met) && met.Truthy) && Up(snib))
            B.Events.Emit(new Ev.Bark { X = pump.X + 4, Z = pump.Z + 3, Text = "OI! No surface-meat past the pump!", Speaker = "Snib" });
        // The Sinkhole: the ground shakes the first time you look in.
        if (!sinkSpawned && Near(sink, 24))
        {
            sinkSpawned = true;
            G.Apply("""[{ "quest": { "id": "below", "status": "active", "entry": "sinkhole" } }, { "quest": { "id": "below", "entry": "tremor" } }]""");
            B.Events.Emit(new Ev.Shake { Amount = 0.9 });
            G.Say("The ground shivers. At the bottom of the pit lies something pale and segmented, bigger than a house, and — probably — dead.", null, 6);
            if (Knows("faith"))
                G.After(6.5, () =>
                {
                    G.Say("Under the silence you hear it, for as long as a held breath: slow, patient, enormous. Not breathing. Praying.", null, 7);
                    G.Apply("""[{ "quest": { "id": "below", "entry": "prayer" } }]""");
                });
            var s = B.SpawnEnemy("lampling", sink.X + 15, sink.Z + 12, new Battle.SpawnOpts { Level = 1, Tag = "survivor", Disposition = Disposition.Neutral, Home = (sink.X + 15, sink.Z + 12, 1.5) });
            if (s != null) s.Named = new Named { Title = "A babbling lampling" };
        }
        // The Vault.
        if (Near(V("vault"), 16) && seen.Add("vault")) G.Apply("""[{ "quest": { "id": "vault", "status": "active", "entry": "seen" } }]""");
        // Clues that need only a look.
        if (Near(V("wreck"), 14) && seen.Add("wreck")) G.Say("Three wagons, dragged off the road into the trees. Wolves do not drive wagons.", null, 4);
    }

    void PlaceRedcowl()
    {
        if (Actors.ContainsKey("redcowl")) return;
        Actors["redcowl"] = new NpcActor(Lore.Outsiders["redcowl"], G.Look, G.Rng);
    }

    void PromoteRedcowl()
    {
        if (B == null || Up(redcowl) || F("redcowl").Str == "dead") return;
        var at = V("redcowl");
        double x = at.X, z = at.Z;
        if (Actors.Remove("redcowl", out var a)) { x = a.X; z = a.Z; a.Dispose(); }
        redcowl = B.SpawnEnemy("enforcer", x, z, new Battle.SpawnOpts { Level = Level() + 1, Tag = "redcowl", Home = (x, z, 18) });
        if (redcowl != null) { redcowl.Named = new Named { Title = "Redcowl" }; redcowl.Disposition = Disposition.Hostile; }
    }

    /* ------------------------------------------------------ interactables -- */

    void MakeInteractables()
    {
        var I = Interactables;
        var entry = V("entry"); var wreck = V("wreck"); var post = V("post"); var carcass = V("carcass"); var sample = V("sample");
        var pipe = V("pipe"); var hollow = V("hollow"); var redcowlAt = V("redcowl"); var cages = V("cages"); var cargo = V("cargo");
        var pump = V("pump"); var sink = V("sinkhole"); var vault = V("vault"); var shrine = V("groveShrine"); var grove = V("grove");
        I.Add(new() { Id = "exit", X = entry.X - 4, Z = entry.Z, R = 5, Verb = "Travel", Name = "The Waystation", Act = () => G.Travel("waystation", "The Waystation", "West along the Old Road") });
        I.Add(new()
        {
            Id = "wreck", X = wreck.X - 3, Z = wreck.Z - 1, R = 3.2, Verb = "Search", Name = "The Coyle Wagons",
            When = () => !Quest("caravan", "wreck"),
            Act = () =>
            {
                G.Apply("""[{ "quest": { "id": "caravan", "status": "active", "entry": "wreck" } }, { "give": "caravan_manifest" }, { "quest": { "id": "caravan", "entry": "manifest" } }]""");
                G.Say("Kerchief arrows in the sideboards, red-fletched. The strongbox bolts are sprung, the box gone. Under the seat: a torn manifest.", null, 6);
            },
        });
        I.Add(new()
        {
            Id = "ruts", X = RutsAt.X, Z = RutsAt.Z, R = 3.5, Verb = "Examine", Name = "Wheel Ruts",
            When = () => !Quest("caravan", "ruts"),
            Act = () =>
            {
                G.Apply("""[{ "quest": { "id": "caravan", "status": "active", "entry": "ruts" } }, { "learn": "hint.roost" }]""");
                G.Say("Deep ruts, heavy wagons, driven south-east into the trees. Toward the ravine.", null, 4);
            },
        });
        I.Add(new()
        {
            Id = "postfire", X = post.X, Z = post.Z + 0.5, R = 3, Verb = "Light", Name = "The Old Watch Fire",
            When = () => !G.Look.IsLit(postFire),
            Act = () => { G.Look.SetLit(postFire, true); G.Say("The old fire takes. For a little while, this is a safe place.", null, 3.5); },
        });
        I.Add(new()
        {
            Id = "postrest", X = post.X, Z = post.Z + 0.5, R = 3, Verb = "Rest", Name = "By the Fire",
            When = () => G.Look.IsLit(postFire),
            Hint = () => restUsed ? "Once per expedition" : "Heal, and write it down",
            Locked = () => restUsed ? "You have rested here already" : null,
            Act = () =>
            {
                restUsed = true;
                if (B != null) B.Player.Hp = B.MaxHp;
                G.Save("fire");
                G.Toast(new Toast(ToastKind.World, "You rest by the fire", "Your wounds close. Your journey is saved."));
            },
        });
        I.Add(new()
        {
            Id = "carcass", X = carcass.X, Z = carcass.Z, R = 3, Verb = "Examine", Name = "A Dead Wolf",
            When = () => !Knows("clue.sick_wolf") || !seen.Contains("carcass"),
            Act = () =>
            {
                seen.Add("carcass");
                bool lore = Knows("beastlore");
                G.Apply("""[{ "learn": "clue.sick_wolf", "text": "The wolves are sick." }, { "quest": { "id": "beasts", "status": "active", "entry": "clue.sick_wolf" } }]""");
                G.Say(lore ? "No wound. Black gums, milky eyes, ribs like a washboard, and the belly swollen hard. It drank something that rotted it from the inside."
                    : "A wolf, dead, with no wound on it. Its eyes have gone milky.", null, 6);
            },
        });
        I.Add(new()
        {
            Id = "sample", X = sample.X, Z = sample.Z, R = 3.2, Verb = "Fill a bottle", Name = "The Green Water",
            When = () => !HasItem("stream_sample") && !Knows("clue.analysis"),
            Act = () =>
            {
                G.Apply("""[{ "give": "stream_sample" }, { "learn": "clue.green_stream" }, { "quest": { "id": "beasts", "status": "active", "entry": "clue.green_stream" } }, { "quest": { "id": "beasts", "entry": "sample" } }]""");
                G.Say("The water is warm, and faintly green, and smells like a chapel lamp.", null, 4);
            },
        });
        I.Add(new()
        {
            Id = "pipe", X = pipe.X, Z = pipe.Z, R = 3.2, Verb = "Examine", Name = "An Iron Pipe",
            When = () => !seen.Contains("pipe"),
            Act = () =>
            {
                seen.Add("pipe");
                G.Apply("""
                    [
                      { "learn": ["clue.pipe", "clue.lampling_tracks"] }, { "quest": { "id": "beasts", "status": "active", "entry": "clue.pipe" } },
                      { "quest": { "id": "beasts", "entry": "clue.lampling_tracks" } },
                      { "if": { "not": { "hasItem": "slurry_sample" } }, "then": [{ "give": "slurry_sample" }] },
                      { "if": { "knows": "clue.analysis" }, "then": [{ "learn": "root_cause", "text": "The Dig is poisoning the stream." }, { "quest": { "id": "beasts", "entry": "root_cause" } }] }
                    ]
                    """);
                G.Say("Riveted iron, warm to the touch, spilling glowing slurry into the stream. Small clawed prints all round it, and the drag-marks of lamps.", null, 6);
            },
        });
        I.Add(new() { Id = "greymuzzle", X = hollow.X, Z = hollow.Z, R = 6, Verb = "Approach", Name = "Greymuzzle", When = () => Up(greymuzzle) && greymuzzle!.Disposition == Disposition.Neutral, Act = () => G.Talk("greymuzzle") });
        I.Add(new() { Id = "redcowl", X = redcowlAt.X, Z = redcowlAt.Z, R = 3.2, Verb = "Talk", Name = "Redcowl", When = () => Actors.ContainsKey("redcowl") && !F("roost.hostile").Truthy, Act = () => G.Talk("redcowl") });
        for (int i = 0; i < 3; i++)
        {
            int k = i;
            I.Add(new()
            {
                Id = $"cage{k}", X = cages.X + k * 3.2, Z = cages.Z - k * 0.8 - 1.6, R = 2.4, Verb = "Open", Name = "A Cage",
                When = () => !cagesOpen[k] && F("caravan.survivors").Str != "dead",
                Locked = () =>
                {
                    bool watching = roostCrew.Any(e => Up(e) && Dist(e.X, e.Z, cages.X, cages.Z) < 16);
                    if (!watching || F("redcowl").Str == "tricked" || F("redcowl.releases").Truthy) return null;
                    return KerchiefsFriendly() ? "Redcowl's men are watching the cages" : "Too many eyes. Deal with them first";
                },
                Act = () => OpenCage(k),
            });
        }
        I.Add(new()
        {
            Id = "strongbox", X = cargo.X + 2.2, Z = cargo.Z - 1.4, R = 2.4, Verb = "Take", Name = "The Coyle Strongbox",
            When = () => !F("caravan.box_taken").Truthy && !F("caravan.cargo").Truthy,
            Act = () =>
            {
                W.Facts["caravan.box_taken"] = true;
                G.Apply("""[{ "give": "coyle_strongbox" }]""");
                if (KerchiefsFriendly() && F("redcowl").Str != "bargained" && roostCrew.Any(Up)) TurnHostile("roost.hostile", "Thief!");
            },
        });
        I.Add(new() { Id = "snib", X = pump.X + 4, Z = pump.Z + 3, R = 3.2, Verb = "Talk", Name = "Snib", When = () => Up(snib) && snib!.Disposition == Disposition.Neutral, Act = () => G.Talk("snib") });
        bool Pumping() => F("dig.pump").IsNull || F("dig.pump").Str == "running";
        I.Add(new()
        {
            Id = "pump", X = pump.X, Z = pump.Z, R = 3.4, Verb = "Break", Name = "The Pump",
            When = Pumping,
            Locked = () => digCrew.Concat(snib != null ? [snib] : Array.Empty<Enemy>()).Any(e => Up(e) && Dist(e.X, e.Z, pump.X, pump.Z) < 14) ? "The crew would never let you" : null,
            Act = () => BreakPump("broken"),
        });
        I.Add(new()
        {
            Id = "charge", X = pump.X - 2, Z = pump.Z + 2, R = 3.4, Verb = "Set a charge", Name = "Blasting Ember",
            When = () => Pumping() && HasItem("blasting_ember") && chargeT < 0,
            Act = () =>
            {
                G.Apply("""[{ "take": "blasting_ember" }]""");
                chargeT = 3.2;
                G.Say("The fuse fizzes. You have a few seconds. Run.", null, 3);
                B?.Events.Emit(new Ev.Telegraph { Id = 9001, Shape = TelegraphShape.Circle, X = pump.X, Z = pump.Z, Radius = 9, Duration = 3.2, Hostile = true });
            },
        });
        I.Add(new() { Id = "survivor", X = sink.X + 15, Z = sink.Z + 12, R = 3, Verb = "Talk", Name = "A Lampling", When = () => sinkSpawned, Act = () => G.Talk("survivor") });
        I.Add(new()
        {
            Id = "vaultdoor", X = vault.X + 1.5, Z = vault.Z + 2.5, R = 3.4, Verb = "Examine", Name = "The Sealed Door",
            Act = () =>
            {
                bool reads = Test("""{ "any": [{ "knows": "arcana" }, { "hasTag": "scholar_lens" }] }""");
                G.Apply("""[{ "quest": { "id": "vault", "status": "active", "entry": "seen" } }, { "if": { "any": [{ "knows": "arcana" }, { "hasTag": "scholar_lens" }] }, "then": [{ "quest": { "id": "vault", "entry": "script" } }] }]""");
                if (HasItem("sigil_fragment")) G.Say("The fragment fits one notch of the sigil. The other six are empty. The door does not care how much you want it open.", null, 6);
                else G.Say(reads ? "Old-empire script over the door: \"Here the Seventh Legion buried what it could not burn.\" Below it, a sigil with seven notches, all empty."
                    : "A door of black stone, smooth as glass, and a violet sigil you cannot read. It hums against your teeth.", null, 6);
            },
        });
        I.Add(new()
        {
            Id = "vaultbody", X = vault.X + 3.8, Z = vault.Z + 3.2, R = 2.4, Verb = "Search", Name = "Bones",
            When = () => !Quest("vault", "fragment"),
            Act = () =>
            {
                G.Apply("""[{ "give": "sigil_fragment" }, { "quest": { "id": "vault", "status": "active", "entry": "fragment" } }]""");
                G.Say("In the bones of one hand, a wedge of black stone cut to fit something.", null, 4);
                if (Knows("faith"))
                    G.After(4.5, () =>
                    {
                        G.Say("The skull turns, very slightly, toward you. \"It was never locked from the outside.\"", "The bones", 6);
                        G.Apply("""[{ "quest": { "id": "vault", "entry": "whisper" } }]""");
                    });
            },
        });
        I.Add(new()
        {
            Id = "vaultprints", X = vault.X + 0.5, Z = vault.Z + 5, R = 2.6, Verb = "Look at", Name = "The Ground",
            When = () => !Quest("vault", "bootprints"),
            Act = () =>
            {
                G.Apply("""[{ "quest": { "id": "vault", "status": "active", "entry": "bootprints" } }]""");
                G.Say("Bootprints in the mud, fresh, going up to the door. None coming away.", null, 4);
            },
        });
        I.Add(new()
        {
            Id = "circlet", X = shrine.X, Z = shrine.Z, R = 2.6, Verb = "Take", Name = "Something Silver",
            When = () => !F("grove.circlet").Truthy,
            Act = () =>
            {
                G.Apply($$"""[{ "set": { "grove.circlet": true } }, { "give": "moonsilver_circlet" }, {{Hist("found_grove", "found the Moon Grove, and what was hidden in it", ["secret", "wolves"], 0)}}]""");
                G.Say("Under the brambles, where the wolves go when one of them is dying: a circlet of moonsilver, cold as snow.", null, 5);
            },
        });
        for (int i = 0; i < 3; i++)
        {
            int k = i;
            I.Add(new()
            {
                Id = $"petal{k}", X = grove.X - 4 + k * 4, Z = grove.Z + 4 - k, R = 2.2, Verb = "Gather", Name = "Moonpetal",
                When = () => !(W.Zones.TryGetValue("verge", out var zs) && zs.TryGetValue($"petal{k}", out var f) && f.Truthy),
                Locked = () => W.Time == TimeOfDay.Night ? null : "Closed. It opens only at night",
                Act = () => G.Apply($$"""[{ "zone": { "id": "verge", "key": "petal{{k}}", "value": true } }, { "give": "moonpetal" }]"""),
            });
        }
    }

    /* ------------------------------------------------------------ events -- */

    static readonly string[] CageLines =
    [
        "A teamster, thin and grey, stumbles out and grips your arm.",
        "A woman who will not stop saying thank you.",
        "A young man: \"Jory. Jory Coyle. Is my uncle —? Is he —?\"",
    ];

    void OpenCage(int i)
    {
        cagesOpen[i] = true;
        G.Look.Show(cageNodes[i], false);
        G.Say(CageLines[i], null, 4);
        if (cagesOpen.All(o => o))
            G.Apply($$"""
                [
                  { "set": { "caravan.survivors": "rescued" } }, { "quest": { "id": "caravan", "entry": "survivors_freed" } }, {{CaravanSettle}},
                  {{Hist("freed_teamsters", "freed the Coyle teamsters from the Kerchief cages", ["rescue", "caravan"], 2, """{ "affection": 10 }""", """{ "harlan": { "affection": 40, "trust": 30 }, "holloway": { "respect": 15 } }""")}}
                ]
                """);
    }

    void BreakPump(string how)
    {
        if (F("dig.pump").Str is "broken" or "blown" or "moved") return;
        G.Look.Stop("pump_wheel");
        if (pumpLight >= 0) G.Look.SetLit(pumpLight, false);
        bool blown = how == "blown";
        G.Apply($$"""
            [
              { "set": { "dig.pump": "{{how}}" } }, { "quest": { "id": "beasts", "entry": "{{(blown ? "pump_blown" : "pump_broken")}}" } },
              {{Hist(blown ? "blew_dig" : "broke_pump", blown ? "blew the Dig's powder and half the hillside with it" : "wrecked the Dig's pump", ["beasts", "lampling"], 2, """{ "respect": 10 }""", """{ "wenna": { "respect": 20 }, "maeca": { "respect": 20 } }""")}}
            ]
            """);
        if (!blown) G.Say("Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.", null, 4);
    }

    void Explode(double x, double z, double r)
    {
        if (B == null) return;
        B.Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = r, School = School.Fire, Power = 2.5 });
        B.Events.Emit(new Ev.Shake { Amount = 1 });
        B.Explode(x, z, r, 120, School.Fire, [Tag.Explosion, Tag.Area], null);
        if (Dist(B.Player.X, B.Player.Z, x, z) < r) B.HurtPlayer(40, School.Fire, "the blast", null);
    }

    void OnHitProp(string tag, int id, School school, double dmg, double x, double z)
    {
        if (tag == "powder" && school == School.Fire)
        {
            B?.Collision.Remove(id);
            Explode(x, z, 7);
            var dig = V("dig"); var roost = V("roost");
            if (Dist(x, z, dig.X, dig.Z) < 20) { BreakPump("blown"); TurnHostile("dig.hostile"); }
            if (Dist(x, z, roost.X, roost.Z) < 30)
            {
                TurnHostile("roost.hostile");
                if (!cagesOpen.All(o => o) && F("caravan.survivors").Str != "rescued")
                {
                    G.Apply($$"""
                        [{ "set": { "caravan.survivors": "dead" } }, { "quest": { "id": "caravan", "entry": "survivors_dead" } },
                         {{Hist("burned_roost", "set the Roost burning with the prisoners still in their cages", ["caravan"], 2, """{ "trust": -10 }""", """{ "harlan": { "trust": -60, "affection": -60 } }""")}}]
                        """);
                    G.Say("The fire takes the tents, and the cages with them. There is screaming, and then there is not.", null, 6);
                }
                // Whatever of the Coyle cargo was still in the camp goes up with it.
                if (!F("caravan.box_taken").Truthy && !F("caravan.cargo").Truthy)
                    G.Apply("""[{ "set": { "caravan.cargo": "lost" } }, { "quest": { "id": "caravan", "entry": "cargo_lost", "outcome": "lost" } }]""");
                G.Apply($"[{CaravanSettle}]");
            }
            return;
        }
        if (tag.StartsWith("bramble:") && int.TryParse(tag[8..], out int i) && i < brambles.Count)
        {
            brambleHp[i] -= school == School.Fire ? 1e9 : dmg;
            var br = brambles[i];
            if (brambleHp[i] <= 0 && G.Look.Shown(br.Node))
            {
                G.Look.Show(br.Node, false);
                B?.Collision.Remove(br.Collider);
                B?.Events.Emit(new Ev.Explosion { X = br.X, Z = br.Z, Radius = 2.4, School = school == School.Fire ? School.Fire : School.Nature, Power = 0.8 });
                if (seen.Add("grove"))
                    G.Say(school == School.Fire ? "The brambles go up like paper. Beyond them, a glade full of pale light." : "You hack a way through the brambles. Beyond them, a glade full of pale light.", null, 5);
            }
        }
    }

    /* ---------------------------------------------------------- the dead -- */

    void OnKill(Enemy e, bool byPlayer)
    {
        if (!byPlayer) return;
        var f = W.Facts;
        double Num(string k, double d = 0) => f.TryGetValue(k, out var v) && !v.IsNull ? v.Number : d;
        if (e.Def.Family == Family.Wolf)
        {
            f["beasts.population"] = Math.Max(0, Num("beasts.population", 60) - (e.Tag == "greymuzzle" ? 20 : 1));
            f["verge.wolf_kills"] = Num("verge.wolf_kills") + 1;
            if (Num("verge.wolf_kills") == 15)
                G.Apply($"[{Hist("wolf_slaughter", "killed a great many wolves in the Verge", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": -20 }, "brannoc": { "respect": 5 }, "holloway": { "respect": 10 } }""")}]");
            if (e.Disposition == Disposition.Neutral || e.Provoked) TurnHostile("hollow.hostile");
        }
        if (e.Def.Family == Family.Kerchief) f["verge.kerchief_kills"] = Num("verge.kerchief_kills") + 1;
        if (e.Tag == "greymuzzle")
        {
            greymuzzle = null;
            G.Apply($$"""[{ "set": { "greymuzzle": "dead" } }, { "quest": { "id": "beasts", "entry": "alpha_dead" } }, {{Hist("killed_greymuzzle", "killed Greymuzzle, the old alpha of the Pack", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": -50, "respect": -20 }, "holloway": { "respect": 20 } }""")}}]""");
            G.SetBoss(null);
        }
        if (e.Tag == "redcowl")
        {
            redcowl = null;
            G.Apply($$"""[{ "set": { "redcowl": "dead" } }, {{Hist("killed_redcowl", "killed Redcowl in his own camp", ["kerchief", "caravan"], 2, """{ "fear": 10 }""", """{ "holloway": { "respect": 25 }, "rav": { "affection": -20 } }""")}}]""");
            G.SetBoss(null);
            if (!roostCrew.Any(Up)) W.Facts["roost.cleared"] = true;
        }
        if (e.Tag == "dig:snib") { snib = null; W.Facts["snib.dead"] = true; TurnHostile("dig.hostile"); }
        if (e.Tag?.StartsWith("dig") == true) TurnHostile("dig.hostile");
        if (e.Tag == "roost" && e.Disposition != Disposition.Hostile) TurnHostile("roost.hostile");
        if (e == nemesis && W.Nemesis is { } n)
        {
            n.Killed = true;
            foreach (var it in n.Carries) G.ReturnItem(it);
            G.Apply($"[{Hist("nemesis_slain", $"put down {n.Title}, and took back what it took", ["revenge"], 2, """{ "respect": 10 }""")}]");
            nemesis = null;
            G.SetBoss(null);
            G.Announce(new Announcement("Taken back", n.Title, "boon", 3.5));
        }
    }

    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var out_ = new List<Loot>();
        double r = R();
        var loot = e.Def.Loot;
        if (loot == "wolf" && r < 0.55) out_.Add(new Loot(PickupKind.Material, "wolf_pelt", 1));
        if (loot == "alpha") { out_.Add(new Loot(PickupKind.Item, "greymuzzle_fang", 1, true)); out_.Add(new Loot(PickupKind.Material, "wolf_pelt", 3)); }
        if (loot == "boar" && r < 0.5) out_.Add(new Loot(PickupKind.Material, "boar_hide", 1));
        if (loot == "kerchief" && r < 0.3) out_.Add(new Loot(PickupKind.Material, "kerchief_cloth", 1));
        if (e.Def.Family == Family.Lampling && r < 0.18) out_.Add(new Loot(PickupKind.Material, "ember_shard", 1));
        if (e.Def.Family == Family.Undead && r < 0.25) out_.Add(new Loot(PickupKind.Material, "bone_dust", 1));
        if (e.Elite && loot == "elite")
        {
            // Gear, rolled where it falls: the deeper into the night's ember,
            // the better the odds. The column of light over it says how good.
            int ember = B?.EmberLevel ?? 1;
            double roll = R();
            int rarity = roll < 0.03 + ember * 0.006 ? 3 : roll < 0.16 + ember * 0.012 ? 2 : roll < 0.62 ? 1 : 0;
            out_.Add(new Loot(PickupKind.Item, PlainGear[(int)Math.Floor(R() * PlainGear.Length)], 1, true, rarity));
        }
        // Named things keep the light of what they are.
        return out_.Select(d => d.Kind == PickupKind.Item && d.Ref != null && d.Rarity == null ? d with { Rarity = Items.Find(d.Ref)?.Rarity ?? 0 } : d).ToList();
    }

    /* ------------------------------------------------------------ runtime -- */

    public override Arrival ArrivalFrom(string? from)
    {
        var e = V("entry");
        return from == "waystation" || from == null ? new Arrival(e.X + 4, e.Z, Math.PI / 2) : new Arrival(e.X + 4, e.Z);
    }

    public override void Begin(Battle battle)
    {
        base.Begin(battle);
        var wd = W;
        G.SetAtmosphere(AtmosphereFor(wd.Time));
        // Maeca hunts here by day, once you have met her in town.
        if (wd.Time != TimeOfDay.Night && F("beasts.outcome").Str != "slaughtered" && wd.Npcs.TryGetValue("maeca", out var m) && m.Flags.TryGetValue("met", out var met) && met.Truthy)
        {
            var blind = V("blind");
            var a = new NpcActor(Lore.Npcs["maeca"], G.Look, G.Rng, new Spot { X = blind.X + 2.6, Z = blind.Z + 4.2, Facing = 0.4 });
            Actors["maeca"] = a;
            Interactables.Add(new() { Id = "talk:maeca", X = a.X, Z = a.Z, R = 2.8, Verb = "Talk", Name = "Maeca Barefoot", Act = () => G.Talk("maeca") });
        }
        if (!F("dig.pump").IsNull && F("dig.pump").Str != "running") G.Look.Stop("pump_wheel");
        // Your wolves, if the Pack runs with you.
        if (F("pack.allied").Truthy)
        {
            var entry = V("entry");
            for (int i = 0; i < 4; i++)
            {
                var e = battle.SpawnEnemy("wolf", entry.X + 6 + i, entry.Z + 2, new Battle.SpawnOpts { Level = Level(), Disposition = Disposition.Ally, Faction = Faction.Ally, Tag = "packmate" });
                if (e != null) e.Named = new Named { Title = "Of the Pack" };
            }
            G.Say("Four grey shapes fall in beside you at the edge of the wood.", null, 4);
        }
        // What you left behind, and what took it.
        var c = wd.Corpse;
        if (c != null && c.Zone == "verge")
        {
            G.Look.AddProp("halloween/gravemarker_B", c.X, c.Z, 0.3, 0.7);
            int light = G.Look.AddLight(c.X, G.Look.HeightAt(c.X, c.Z) + 1.4, c.Z, "#ffc070", 6, 9, 0.1, 0.08, "#ffd890");
            Interactables.Add(new()
            {
                Id = "corpse", X = c.X, Z = c.Z, R = 2.6, Verb = "Recover", Name = $"{c.HeroName}'s belongings",
                When = () => W.Corpse != null,
                Act = () =>
                {
                    var cc = W.Corpse!;
                    G.Apply($$"""[{ "gold": {{cc.Gold}} }]""");
                    foreach (var it in cc.Items) G.GiveItem(it.Def, it.Qty);
                    W.Corpse = null;
                    G.Look.SetLit(light, false);
                    G.Say("Where you fell. The ground has kept your things for you, mostly.", null, 4);
                },
            });
        }
        var n = wd.Nemesis;
        if (n != null && n.Zone == "verge" && !n.Killed)
        {
            var post = V("post");
            var (ax, az) = c != null && c.Zone == "verge" ? (c.X, c.Z) : (post.X + 20, post.Z - 20);
            nemesis = battle.SpawnEnemy(n.Def, ax + 6, az + 6, new Battle.SpawnOpts { Level = n.Level, Elite = true, Tag = "nemesis", Home = (ax, az, 30) });
            if (nemesis != null) nemesis.Named = new Named { Title = n.Title, Carries = n.Carries.Select(i => i.Def).ToList(), SourceHero = n.HeroName };
        }
        G.AnnounceZone();
        // The first time out here: the wood is big, and there is a map.
        if (!wd.Fact("tip.verge_map").Truthy)
        {
            wd.Facts["tip.verge_map"] = true;
            G.After(5, () =>
            {
                G.SetHint(new Hint("verge_map", "The map", "The Verge is wide and the trees close in. The map fills in as you walk, and marks what you have found.", [G.KeyLabel("map")]));
                G.After(10, () => { if (G.CurrentHint?.Id == "verge_map") G.SetHint(null); });
            });
        }
        G.SetObjectives(Objectives.Of(C));
    }

    public override void Step(double dt)
    {
        Director(dt);
        Approach();
        // Peace made in a conversation reaches everyone already out there;
        // anyone you have struck stays angry.
        dispT -= dt;
        if (dispT <= 0 && B != null)
        {
            dispT = 0.5;
            foreach (var e in B.Enemies.Living()) if (!e.Provoked && e.Disposition != Disposition.Ally) SetDisposition(e);
        }
        if (chargeT > 0)
        {
            chargeT -= dt;
            if (chargeT <= 0)
            {
                var pump = V("pump");
                Explode(pump.X, pump.Z, 9);
                BreakPump("blown");
                TurnHostile("dig.hostile");
                chargeT = -1;
            }
        }
    }

    public override void Frame(double dt)
    {
        if (B == null) return;
        var p = B.Player;
        foreach (var a in Actors.Values) a.Update(dt, p.X, p.Z);
        // Named creatures carry their names over their heads; the one you are
        // fighting gets a bar.
        var plates = new List<Plate>();
        foreach (var (id, a) in Actors)
        {
            bool metThem = W.Npcs.TryGetValue(id, out var s) && s.Flags.TryGetValue("met", out var met) && met.Truthy;
            plates.Add(new Plate(id, a.X, G.Look.HeightAt(a.X, a.Z) + 2.3, a.Z, a.Def.Name, metThem ? a.Def.Role : null));
        }
        Enemy? fight = null;
        foreach (var e in B.Enemies.Living())
        {
            if (e.Named == null || e.State == EnemyState.Dying) continue;
            plates.Add(new Plate($"e{e.Id}", e.X, G.Look.HeightAt(e.X, e.Z) + 1.6 * (e.Def.Scale ?? 1) + 0.6, e.Z, e.Named.Title,
                e.Disposition == Disposition.Ally ? "Friend" : e.Disposition == Disposition.Neutral ? null : "Hostile"));
            if (e.Elite && e.Disposition == Disposition.Hostile && Dist(e.X, e.Z, p.X, p.Z) < 22) fight = e;
        }
        if (fight != null) G.SetBoss(new BossBar(fight.Named!.Title, fight == nemesis ? $"Who took {W.Nemesis?.HeroName}'s light" : fight.Def.Name, fight.Hp, fight.MaxHp));
        else G.SetBoss(null);
        G.Look.Plates(plates);
        trackT -= dt;
        if (trackT <= 0) { trackT = 1.5; G.SetObjectives(Objectives.Of(C)); }
    }

    public override List<MapMark> MapMarks()
    {
        bool Q(string id, string entry) => Quest(id, entry);
        // Where the tracker sends you is gold, and shows through the fog: you
        // were told of it, so you know roughly where.
        bool pumping = F("dig.pump").IsNull || F("dig.pump").Str == "running";
        bool toDig = Knows("root_cause") && pumping;
        bool toHollow = Knows("hint.greymuzzle") && !Q("beasts", "greymuzzle_met") && F("greymuzzle").Str != "dead";
        bool toWreck = Q("caravan", "harlan_plea") && !Q("caravan", "wreck");
        XZ at(string k) => V(k);
        var marks = new List<MapMark>
        {
            new(at("entry").X - 2, at("entry").Z, "The Waystation", MarkKind.Exit),
            new(at("exitEast").X - 8, at("exitEast").Z, "Road washed out", MarkKind.Place),
            new(at("post").X, at("post").Z, "Old Watch Fire", MarkKind.Place),
            new(at("wreck").X, at("wreck").Z, "Coyle Wagons", toWreck ? MarkKind.Quest : Q("caravan", "wreck") ? MarkKind.Place : MarkKind.Turn),
            new(at("blind").X, at("blind").Z, "Hunters' Blind", MarkKind.Place),
            new(at("hollow").X, at("hollow").Z, "Wolf Hollow", toHollow ? MarkKind.Quest : WolvesFriendly() ? MarkKind.Place : MarkKind.Danger),
            new(at("dig").X, at("dig").Z, "The Dig", toDig ? MarkKind.Quest : F("dig.hostile").Truthy ? MarkKind.Danger : MarkKind.Place),
            new(at("roost").X, at("roost").Z, "Redcowl's Roost", KerchiefsFriendly() || F("redcowl").Str == "tricked" ? MarkKind.Place : MarkKind.Danger),
            new(at("vault").X, at("vault").Z, "Sealed Door", MarkKind.Mystery),
            new(at("sinkhole").X, at("sinkhole").Z, "The Sinkhole", MarkKind.Mystery),
            new(at("grove").X, at("grove").Z, "Moon Grove", MarkKind.Place),
        };
        if (!Knows("clue.sick_wolf")) marks.Add(new(at("carcass").X, at("carcass").Z, "Something dead", MarkKind.Turn));
        bool toWater = !HasItem("stream_sample") && !Knows("clue.analysis") && (Knows("hint.stream") || Q("beasts", "wenna_request"));
        if (!Knows("clue.green_stream") || toWater) marks.Add(new(at("sample").X, at("sample").Z, "The green water", toWater ? MarkKind.Quest : MarkKind.Turn));
        if (!Knows("clue.pipe")) marks.Add(new(at("pipe").X, at("pipe").Z, "The pipe", Knows("clue.analysis") ? MarkKind.Quest : MarkKind.Turn));
        if (Q("caravan", "wreck") && !Q("caravan", "ruts") && !Q("caravan", "roost_found")) marks.Add(new(RutsAt.X, RutsAt.Z, "Wheel ruts", MarkKind.Quest));
        if (F("caravan.survivors").Str is not ("rescued" or "dead") && (Knows("hint.roost") || Q("caravan", "roost_found")))
            marks.Add(new(at("cages").X, at("cages").Z, "The cages", MarkKind.Quest));
        return marks;
    }

    public override string? MusicMood(double x, double z)
    {
        XZ v = V("vault"), s = V("sinkhole"), g = V("grove");
        return Dist(x, z, v.X, v.Z) < 22 || Dist(x, z, s.X, s.Z) < 26 || Dist(x, z, g.X, g.Z) < 16 ? "mystery" : null;
    }

    public override AmbienceMix Ambience(double x, double z)
    {
        var t = W.Time;
        bool dark = t == TimeOfDay.Night, day = t is TimeOfDay.Day or TimeOfDay.Dawn;
        bool pumping = F("dig.pump").IsNull || F("dig.pump").Str == "running";
        var pump = V("pump");
        return new AmbienceMix
        {
            Wind = 0.6, Leaves = 0.7, Fire = Warmth(x, z),
            Water = Math.Max(0, 1 - StreamDist(x, z) / 24),
            Hum = pumping ? Math.Max(0, 1 - Dist(x, z, pump.X, pump.Z) / 40) : 0,
            Birds = day && F("beasts.outcome").Str != "slaughtered" ? 0.8 : day ? 0.3 : 0,
            Crickets = dark ? 0.7 : t == TimeOfDay.Dusk ? 0.35 : 0, Owl = dark ? 0.55 : 0,
        };
    }

    public override Dictionary<string, object?> Debug() => new()
    {
        ["roostHostile"] = F("roost.hostile").Truthy, ["digHostile"] = F("dig.hostile").Truthy, ["pop"] = F("beasts.population").Number,
        ["wolvesFriendly"] = WolvesFriendly(), ["kerchiefsFriendly"] = KerchiefsFriendly(),
    };

    public override void Dispose()
    {
        base.Dispose();
        G.SetBoss(null);
        G.SetObjectives(new());
        G.Look.Plates(new());
    }
}
