using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* The Waystation, lived in (the web game's game/zones/waystation.ts).
 *
 * Everyone stands near their door. Doors lead to whoever keeps them. The
 * notice board reads out the town's troubles; the gates lead back down to
 * the Low Ford, out along the Old Road (for five gold), or nowhere at all
 * (north, past Keegan). At night Pell's warehouse can be got into, by
 * someone with a key or a light touch. Behind the shrine, a gap in the
 * hedge. */
public sealed class Waystation : ZoneRuntime
{
    public override string Id => "waystation";
    public override string Name => "The Waystation";
    public override string? Region => "Where three roads meet";
    public override bool Combat => false;

    /// <summary>What the stall-keepers shout.</summary>
    static readonly Dictionary<string, string[]> StallCalls = new()
    {
        ["produce"] = ["Apples! Morrow pippins, crisp as frost!", "Turnips, onions, the last of the beans!", "Two for a copper, and I'm robbing myself!"],
        ["cloth"] = ["Wool from the south, warm as a bed!", "Mend your cloak, traveller? It needs it.", "Dyed in the Morrow, never fades!"],
        ["herbs"] = ["Feverfew, woundwort, sleep-easy!", "Wenna's not the only one who knows a leaf.", "Something for the cough? Everyone's got the cough."],
        ["pots"] = ["Pots! Pans! Things to put things in!", "Fired in Low Kiln, sound as a bell. Hear that?", "You look like someone who needs a pot."],
    };

    /// <summary>Who is out and about, given what has happened.</summary>
    static readonly Dictionary<string, string> Present = new()
    {
        ["pell"] = """{ "all": [{ "not": { "fact": "caravan.pell", "eq": "exposed" } }, { "not": { "fact": "caravan.pell", "eq": "fled" } }] }""",
        ["jory"] = """{ "fact": "caravan.survivors", "eq": "rescued" }""",
        // A farm boy goes home at night.
        ["tam"] = """{ "not": { "time": "night" } }""",
        // Maeca hunts the Verge by day once you know her; she drinks here at night.
        ["maeca"] = """{ "any": [{ "not": { "met": "maeca" } }, { "time": "night" }, { "time": "dusk" }, { "fact": "beasts.outcome", "eq": "slaughtered" }] }""",
    };

    /// <summary>Where people are, by the hour and by what has happened to
    /// them. The first entry whose condition holds wins; none means their
    /// usual spot.</summary>
    static readonly Dictionary<string, (string When, Spot? Spot, string? Idle)[]> Routine = new()
    {
        ["harlan"] =
        [
            // Nobody has found the caravan: by day he watches the road; once
            // he gives up, he sits outside the tavern.
            ("""{ "all": [{ "fact": "caravan.days", "gte": 3 }, { "not": { "fact": "caravan.survivors", "exists": true } }] }""", new Spot { X = -12.3, Z = -14.2, Facing = Math.PI / 2 }, "Sit_Floor_Idle"),
            ("""{ "all": [{ "fact": "caravan.days", "gte": 1 }, { "not": { "fact": "caravan.survivors", "exists": true } }, { "not": { "time": "night" } }] }""", new Spot { X = 35.4, Z = 1.4, Facing = Math.PI / 2 }, null),
        ],
        // The smith stops at night.
        ["brannoc"] = [("""{ "time": "night" }""", null, "Idle")],
        ["maeca"] = [("""{ "time": "night" }""", new Spot { X = -11.6, Z = -4.4, Facing = Math.PI / 2 }, "Idle_B")],
    };

    /// <summary>Doors lead to whoever keeps them.</summary>
    static readonly (string Door, string Owner, string Label)[] DoorOwners =
    [
        ("inn", "rook", "The Last Lamp"), ("tavern", "rav", "The Crooked Flagon"), ("smithy", "brannoc", "Brannoc's Smithy"),
        ("trading", "harlan", "Coyle Trading Post"), ("shrine", "chid", "Shrine of the Morning Light"), ("wenna", "wenna", "Wenna's House"),
        ("barracks", "holloway", "Watch House"), ("toll", "vonnra", "The Toll Tower"),
    ];

    readonly List<NpcActor> guards = new(), keepers = new();
    readonly Dictionary<string, XZ> doors = new();
    readonly int[] braziers;
    readonly HashSet<string> placed = new();
    Folk folk = null!;
    bool nightNow;
    double trackT;

    XZ Way(string place) => P("WAY", place);

    /// <summary>Where the Wayfinder keeps her stall: the south side of the Old
    /// Road, between the square and the east gate, facing the road.</summary>
    static readonly XZ Stall = new(19.0, 5.3);
    /// <summary>Before the Wayfinder's table, facing it (where an arena from it gives the survivor back).</summary>
    public static readonly Arrival AtTable = new(Stall.X, Stall.Z - 2.6, 0);

    /// <summary>The stall itself: a counter under an awning, maps and a lamp on
    /// it, a table of charts beside, a lectern with the great atlas open.</summary>
    void DressStall()
    {
        var look = G.Look;
        double x = Stall.X, z = Stall.Z;
        // The awning hangs low over the side that serves (the piece's -z): toward the road.
        look.AddProp("props/Stall_Empty", x, z, 0, 1.15);
        const double counter = 1.02;
        look.AddProp("props/Scroll_1", x - 0.5, z - 0.1, 0.35, 1.7, counter);
        look.AddProp("props/Scroll_2", x + 0.35, z - 0.05, -0.4, 1.7, counter);
        look.AddProp("props/Book_Stack_1", x + 0.8, z + 0.1, 0.2, 1.1, counter);
        look.AddProp("props/CandleStick_Triple", x - 0.85, z + 0.1, 0, 1, counter);
        look.AddProp("props/Table_Large", x - 3.8, z - 0.7, 0, 0.75);
        const double table = 0.61;
        look.AddProp("props/Scroll_1", x - 4.2, z - 0.8, 1.2, 1.6, table);
        look.AddProp("props/Scroll_2", x - 3.3, z - 0.6, -0.2, 1.6, table);
        look.AddProp("props/Book_Stack_2", x - 4.6, z - 0.5, 0.5, 1, table);
        look.AddProp("props/Stool", x - 3.8, z + 0.3, 0, 1);
        look.AddProp("props/BookStand", x + 2.6, z - 1.0, Math.PI + 0.3, 1);
        look.AddProp("props/Chest_Wood", x + 2.5, z + 0.3, Math.PI, 0.75);
        // A lamp that can be seen from the square, and the candles' glow.
        double y = look.HeightAt(x, z);
        look.AddLight(x, y + 2.3, z - 0.3, "#ffc27a", 9, 12, 0.1, 0.1, "#ffd08a");
        look.AddLight(x - 0.85, y + counter + 0.5, z + 0.1, "#ffb060", 3, 5, 0.25, 0.05, "#ffd890");
        if (B != null)
        {
            B.Collision.AddBox(x, z, 1.1, 0.55);
            B.Collision.AddBox(x - 3.8, z - 0.7, 1.1, 0.45);
            B.Collision.AddCircle(x + 2.6, z - 1.0, 0.3);
            B.Collision.AddCircle(x + 2.5, z + 0.3, 0.45);
        }
    }
    bool Dark => W.Time is TimeOfDay.Night or TimeOfDay.Dusk;

    public Waystation(IZoneHost host, ZoneMeta meta) : base(host, meta)
    {
        foreach (var d in meta.Refs.GetProperty("doors").EnumerateObject())
            doors[d.Name] = new XZ(d.Value.GetProperty("x").GetDouble(), d.Value.GetProperty("z").GetDouble());
        braziers = meta.Refs.GetProperty("braziers").EnumerateArray().Select(b => b.GetInt32()).ToArray();
        MakeInteractables();
    }

    void People()
    {
        var look = G.Look;
        foreach (var def in Lore.Npcs.Values.Append(Lore.Outsiders["jory"]).Append(Lore.Outsiders["wayfinder"]))
            Wire(Actors[def.Id] = new NpcActor(def, look, G.Rng), () => Dark);
        for (int i = 0; i < Lore.Guards.Count; i++)
        {
            var g = Lore.Guards[i];
            // The Watch's leathers and hood, a sword and shield.
            guards.Add(new NpcActor(new NpcDef
            {
                Id = $"guard{i}", Name = "Watchman", Title = "The Waystation Watch", Role = "Watch", Model = "knight",
                Show = ["Knight_Helmet", "1H_Sword", "Rectangle_Shield"], Tint = "#8a98b0", Idle = "Idle_Shield_Loop",
                Spot = new Spot { X = g.X, Z = g.Z, Facing = g.Facing }, Barks = [g.Line],
                Person = Folk.Person(FolkRole.Watch, Lore.WatchLook, G.Rng), Arms = new Held { Right = "viking_sword", Forearm = "shield_round" },
            }, look, G.Rng));
        }
        // Behind every stall, someone selling; they pack up at dusk.
        var stalls = Meta.Refs.GetProperty("stalls").EnumerateArray().ToList();
        for (int i = 0; i < stalls.Count; i++)
        {
            var st = stalls[i];
            double x = st.GetProperty("x").GetDouble(), z = st.GetProperty("z").GetDouble(), rot = st.GetProperty("rot").GetDouble();
            var kind = st.GetProperty("kind").GetString()!;
            var l = Lore.FolkLooks[(i * 3 + 1) % Lore.FolkLooks.Count];
            keepers.Add(new NpcActor(new NpcDef
            {
                Id = $"keeper{i}", Name = "Stall-keeper", Model = l.Model, Show = l.Show, Tint = l.Tint, Scale = l.Scale,
                Idle = i % 2 == 1 ? "Idle_Talking_Loop" : "Idle_FoldArms_Loop", Person = Folk.Person(FolkRole.Adult, l, G.Rng),
                Spot = new Spot { X = x - Math.Sin(rot) * 0.35, Z = z - Math.Cos(rot) * 0.35, Facing = rot },
                Barks = StallCalls.TryGetValue(kind, out var calls) ? [.. calls] : ["Come and look!"],
            }, look, G.Rng));
        }
        foreach (var (id, a) in Actors)
            Interactables.Add(new() { Id = $"talk:{id}", X = a.X, Z = a.Z, R = 2.8, Verb = "Talk", Name = a.Def.Name, When = () => !a.Hidden, Act = () => G.Talk(id) });
        MakeFolk(stalls);
    }

    void MakeFolk(List<System.Text.Json.JsonElement> stalls)
    {
        // Where the town walks: the lanes, and what is at the end of them.
        FolkNode Node(string id, double x, double z, FolkKind kind = FolkKind.Path, bool square = false, XZ? face = null, bool tavern = false) =>
            new() { Id = id, X = x, Z = z, Kind = kind, Square = square, Face = face, Tavern = tavern };
        FolkNode Door(string id, string key, double out_ = 0.5, bool tavern = false)
        {
            var d = doors[key];
            // Stand on the step, not in the wall: half a pace out from the door.
            XZ? b = key.StartsWith("home") ? null : Way(key);
            double x = d.X, z = d.Z;
            if (b is XZ bb)
            {
                double l = Math.Sqrt((d.X - bb.X) * (d.X - bb.X) + (d.Z - bb.Z) * (d.Z - bb.Z));
                if (l == 0) l = 1;
                x += (d.X - bb.X) / l * out_; z += (d.Z - bb.Z) / l * out_;
            }
            return Node(id, x, z, FolkKind.Door, face: b, tavern: tavern);
        }
        var board = Way("board");
        var nodes = new List<FolkNode>
        {
            Node("gS", 0, 33, FolkKind.Gate), Node("s3", 0, 27.5), Node("s1", 0, 20), Node("s2", 0, 12),
            Node("sL", -5, 25.3), Node("sR", 5, 25.3), Node("swL", -14.5, 25), Node("seL", 14.5, 25),
            Node("sqSW", -3.6, 3.2, square: true), Node("sqSE", 4.4, 4.2, square: true),
            Node("sqNW", -4.4, -4.6, square: true), Node("board", 4.2, -3.2, FolkKind.Board, true, board),
            Node("well", -1.75, 0.9, FolkKind.Well, true, new XZ(0, 0)),
            Node("n1", 0, -12.5), Node("n2", 0, -23.5), Node("e1", 12, 0.6), Node("e2", 24, 0.6), Node("gE", 33, 0, FolkKind.Gate),
            Node("innL", -6, 9.5), Node("innN", -11.5, 15.5), Node("tavL", -6, -9.5), Node("wN", -9, -3), Node("trS", 8.5, -15), Node("smL", 6, 10.5), Node("trL", 5, -10.2),
            Node("w1", -18, 17.5), Node("wW", -19, -5.5), Node("sh0", -6, -16), Node("sh1", -14, -19.5), Node("shF", -20.5, -23.5), Node("ne0", 10, -19), Node("ne1", 17, -23.5), Node("eS", 25, 5),
            Door("inn", "inn"), Door("tavern", "tavern", tavern: true), Door("smithy", "smithy"), Door("trading", "trading"), Door("shrine", "shrine", 0),
        };
        for (int i = 0; i < 12; i++) nodes.Add(Door($"home{i}", $"home{i}"));
        for (int i = 0; i < stalls.Count; i++)
        {
            var st = stalls[i];
            double x = st.GetProperty("x").GetDouble(), z = st.GetProperty("z").GetDouble(), rot = st.GetProperty("rot").GetDouble();
            nodes.Add(Node($"stall{i}", x + Math.Sin(rot) * 2.1, z + Math.Cos(rot) * 2.1, FolkKind.Stall, true, new XZ(x, z)));
        }
        (string, string)[] edges =
        [
            ("gS", "s3"), ("s3", "s1"), ("s3", "sL"), ("s3", "sR"), ("sL", "home5"), ("sR", "home4"), ("sL", "swL"), ("swL", "home7"), ("sR", "seL"), ("seL", "home8"), ("s1", "s2"),
            ("s2", "sqSW"), ("s2", "sqSE"), ("sqSW", "well"), ("sqSW", "sqNW"), ("well", "sqNW"), ("sqSE", "board"), ("sqSE", "e1"), ("board", "e1"), ("board", "n1"), ("sqNW", "n1"),
            ("n1", "n2"), ("n2", "home11"), ("e1", "e2"), ("e2", "gE"), ("e2", "eS"), ("eS", "home6"),
            ("s2", "innL"), ("innL", "inn"), ("inn", "innN"), ("innN", "w1"), ("w1", "home9"), ("w1", "home7"),
            ("sqNW", "tavL"), ("tavL", "tavern"), ("sqNW", "wN"), ("wN", "wW"), ("wW", "home2"), ("wW", "home3"),
            ("sqSE", "smL"), ("s2", "smL"), ("smL", "smithy"), ("n1", "trL"), ("trL", "trading"), ("trading", "trS"), ("trL", "trS"), ("trS", "ne0"), ("ne0", "ne1"), ("ne1", "home0"), ("ne1", "home1"),
            ("n1", "sh0"), ("sh0", "sh1"), ("sh1", "shF"), ("shF", "shrine"), ("e2", "home10"),
            ("innL", "stall0"), ("smL", "stall1"), ("tavL", "stall2"), ("sqNW", "stall2"), ("trL", "stall3"),
        ];
        folk = new Folk(new Folk.Options
        {
            Nodes = nodes, Edges = edges.ToList(), Col = B!.Collision, Look = G.Look,
            Plan = () => W.Time switch
            {
                TimeOfDay.Night => new FolkPlan(2, 0, true), TimeOfDay.Dusk => new FolkPlan(5, 0, true),
                TimeOfDay.Dawn => new FolkPlan(3, 0, false), _ => new FolkPlan(8, 1, false),
            },
            Dark = () => Dark,
            Lines = role =>
            {
                bool died = G.Journey.Ch.Stats.Deaths > 0;
                return Lore.FolkLines.Where(l => (role == FolkRole.Child ? l.Child == true : role == FolkRole.Watch ? l.Watch == true : l.Child != true && l.Watch != true)
                    && (l.Night == null || l.Night == Dark) && (l.Died != true || died) && Rules.Test(l.When, C)).ToList();
            },
            Round = ["gS", "s2", "sqSW", "sqNW", "n1", "n2", "n1", "board", "e1", "e2", "gE", "e2", "e1", "sqSE", "s2", "s1"],
        }, G.Rng);
    }

    void MakeInteractables()
    {
        var I = Interactables;
        foreach (var (door, owner, label) in DoorOwners)
        {
            if (!doors.TryGetValue(door, out var d)) continue;
            I.Add(new() { Id = $"door:{door}", X = d.X, Z = d.Z, R = 2.2, Verb = "Visit", Name = label, Act = () => G.Talk(owner) });
        }
        var board = Way("board"); var south = Way("south"); var east = Way("east"); var north = Way("north"); var garden = Way("garden");
        var warehouse = doors["warehouse"];
        I.Add(new() { Id = "board", X = board.X, Z = board.Z, R = 2.6, Verb = "Read", Name = "Notice Board", Act = () => G.Talk("board") });
        I.Add(new() { Id = "well", X = 0, Z = 0, R = 2.8, Verb = "Look into", Name = "The Well", Act = () => G.Say("The water is a long way down, and clean. Somebody has scratched \"M. + J.\" into the stone.", null, 4) });
        I.Add(new() { Id = "gate:south", X = south.X, Z = south.Z - 1.5, R = 3.4, Verb = "Travel", Name = "The Low Ford Road", Act = () => G.Travel("lowford", "The Low Ford Road", "South, toward the crossing") });
        I.Add(new()
        {
            Id = "gate:east", X = east.X - 1.5, Z = east.Z, R = 3.4, Verb = "Travel", Name = "The Old Road",
            Hint = () => F("toll.paid").Truthy ? "Thornhollow Verge" : "Vonnra's toll: 5 gold",
            Locked = () => !F("toll.paid").Truthy && G.Journey.Ch.Gold < 5 ? "The toll is five gold" : null,
            Act = () =>
            {
                if (!F("toll.paid").Truthy)
                {
                    G.Apply("""[{ "gold": -5 }, { "set": { "toll.paid": true } }]""");
                    G.Toast(new Toast(ToastKind.Gold, "Five gold to Vonnra's toll"));
                }
                G.Travel("verge", "Thornhollow Verge", "East along the Old Road");
            },
        });
        // The Wayfinder's stall on the Old Road: maps to places the road forgets, each an arena.
        I.Add(new()
        {
            Id = "maps", X = Stall.X, Z = Stall.Z - 1.6, R = 2.2, Verb = "Choose a map", Name = "The Wayfinder's Table",
            Hint = () => W.Rematches.Count > 0 ? $"{W.Rematches.Count} fight{(W.Rematches.Count == 1 ? "" : "s")} to take again" : F("arena.best").Number > 0 ? $"Tier {(int)F("arena.best").Number} won" : null,
            Act = () => G.Open("maps"),
        });
        I.Add(new() { Id = "gate:north", X = north.X, Z = north.Z + 3, R = 3.2, Verb = "Pass", Name = "The North Gate", Locked = () => "Dame Keegan bars the way" });
        I.Add(new()
        {
            Id = "warehouse", X = warehouse.X, Z = warehouse.Z, R = 2.4, Verb = "Enter", Name = "Pell's Warehouse",
            When = () => !F("warehouse.searched").Truthy,
            Hint = () => W.Time == TimeOfDay.Night ? null : "Locked. Pell is watching.",
            Locked = () =>
            {
                if (HasItem("clerks_key")) return null;
                if (W.Time != TimeOfDay.Night) return "Locked, and Pell is watching the door";
                return HasItem("lockpicks") ? null : "Locked. You would need lockpicks, or a key";
            },
            Act = () =>
            {
                bool night = W.Time == TimeOfDay.Night;
                bool withKey = HasItem("clerks_key");
                G.Apply($$"""
                    [{ "set": { "warehouse.searched": true } }, { "give": "pell_ledger" }, { "quest": { "id": "caravan", "entry": "pell_ledger" } },
                     {{Hist("burgled_pell", "broke into Pell Varrow's warehouse", ["theft", "caravan"], night ? 0 : 1, null, """{ "pell": { "trust": -30, "fear": 10 } }""")}}]
                    """);
                G.Say(withKey ? "The clerk's key turns sweetly. Inside: crates, dust, and a ledger Pell should have burned."
                    : "The lock gives under your picks. Inside: crates, dust, and a ledger Pell should have burned.", null, 5);
            },
        });
        // C08 (cin_iron_marker): the morning they bury Nell, the town is in the Quiet
        // Garden, and the hymn plays as a conversation until the cinematic does.
        I.Add(new()
        {
            Id = "burial", X = garden.X, Z = garden.Z, R = 5, Verb = "Stand with them", Name = "The Quiet Garden",
            When = () => F("nell.burying").Truthy && W.Time != TimeOfDay.Night
                && !(W.Zones.TryGetValue("waystation", out var zs) && zs.TryGetValue("burial", out var g) && g.Truthy),
            Act = () =>
            {
                G.Apply("""[{ "zone": { "id": "waystation", "key": "burial", "value": true } }]""");
                G.Say("The whole town is in the Quiet Garden, round a fresh grave beside the old captain's stone. Brannoc kneels at its head with an iron marker and his hammer: three strokes, iron into earth. Rook sets the inn's lamp at its foot, lit, in broad daylight, and steps back, and back.", null, 7);
                G.After(7.2, () => G.Talk("cin_iron_marker"));
            },
        });
        I.Add(new()
        {
            Id = "garden", X = garden.X + 2.5, Z = garden.Z + 4.5, R = 2.2, Verb = "Open", Name = "An old trunk",
            When = () => !(W.Zones.TryGetValue("waystation", out var zs) && zs.TryGetValue("garden", out var g) && g.Truthy),
            Act = () =>
            {
                G.Apply("""
                    [{ "zone": { "id": "waystation", "key": "garden", "value": true } }, { "give": "ember_shard", "qty": 2 }, { "gold": 25 },
                     { "learn": "lore.firstlamp", "text": "The Quiet Garden: where the first Watch-captain is buried, with his lamp." }]
                    """);
                G.Say("Beside the old captain's stone, sunk in the nettles, a trunk the Watch forgot: ember shards, a purse, and a note: \"Keep the lights lit. — C.\"", null, 6);
            },
        });
    }

    void Presence()
    {
        var p = B?.Player;
        foreach (var (id, a) in Actors)
        {
            bool hide = Present.TryGetValue(id, out var cond) && !Test(cond);
            a.Night = Dark;
            // Nobody vanishes in front of you: someone leaving waits until you look away.
            bool watched = p != null && !a.Hidden && Dist(p.X, p.Z, a.X, a.Z) < 16;
            if (hide != a.Hidden && !(hide && (watched || a.Talking) && placed.Contains(id))) a.Hidden = hide;
            Spot spot = a.Def.Spot;
            string idle = a.Def.Idle;
            if (Routine.TryGetValue(id, out var r) && r.FirstOrDefault(e => Test(e.When)) is { When: not null } hit)
            {
                spot = hit.Spot ?? spot;
                idle = hit.Idle ?? idle;
            }
            if (spot.X != a.X || spot.Z != a.Z || idle != a.Pose)
            {
                // Only while nobody is looking: never pop someone across the
                // square mid-conversation.
                bool near = p != null && (Dist(p.X, p.Z, a.X, a.Z) < 16 || Dist(p.X, p.Z, spot.X, spot.Z) < 16);
                if (a.Talking || (near && placed.Contains(id))) continue;
                a.Place(spot, idle);
                if (Interactables.FirstOrDefault(i => i.Id == $"talk:{id}") is { } it) { it.X = spot.X; it.Z = spot.Z; }
            }
            placed.Add(id);
        }
    }

    void SetNight(bool on)
    {
        G.Look.SetNight(on);
        foreach (var b in braziers) G.Look.SetLit(b, on);
    }

    public override Arrival ArrivalFrom(string? from)
    {
        var east = Way("east"); var shrine = Way("shrine"); var south = Way("south");
        if (from == "verge") return new(east.X - 5, east.Z, -Math.PI / 2);
        if (from == "arena") return AtTable;
        if (from == "death") return new(shrine.X + 6, shrine.Z + 6, Math.PI * 0.25);
        // Far enough through the south gate that the wall is behind the
        // camera, not a brown slab across the bottom of the picture.
        return new(south.X, south.Z - 15, Math.PI);
    }

    public override AtmospherePreset AtmosphereFor(TimeOfDay t) => t == TimeOfDay.Night ? Atmospheres.NightTown : base.AtmosphereFor(t);

    // The town is seen whole from its gate; the corner behind the shrine is not.
    public override List<(double X, double Z, double R)> MapKnown => [(0, 2, 35), (22, 20, 20), (-22, 20, 20), (22, -20, 20), (-20, -18, 17)];
    public override (double X, double Z, double Zoom)? MapFocus => (0, 3, 1.5);

    public override List<MapMark> MapMarks()
    {
        XZ at(string k) => Way(k);
        var marks = new List<MapMark>
        {
            new(at("inn").X, at("inn").Z, "The Last Lamp", MarkKind.Place), new(at("tavern").X, at("tavern").Z, "The Tavern", MarkKind.Place),
            new(at("smithy").X, at("smithy").Z, "Smithy", MarkKind.Place), new(at("trading").X, at("trading").Z, "Coyle Trading", MarkKind.Place),
            new(at("warehouse").X, at("warehouse").Z, "Warehouse", MarkKind.Place), new(at("shrine").X, at("shrine").Z, "Shrine", MarkKind.Place),
            new(at("wenna").X, at("wenna").Z, "Wenna's", MarkKind.Place), new(at("barracks").X, at("barracks").Z, "The Watch", MarkKind.Place),
            new(0, 0, "The Square", MarkKind.Place), new(at("south").X, at("south").Z + 4, "To the Low Ford", MarkKind.Exit),
            new(Stall.X, Stall.Z, "The Wayfinder's Maps", MarkKind.Place),
            new(at("east").X + 4, at("east").Z, "The Old Road, east", MarkKind.Exit), new(at("north").X, at("north").Z - 4, "North (barred)", MarkKind.Exit),
        };
        if (W.Zones.TryGetValue("waystation", out var zs) && zs.TryGetValue("garden", out var g) && g.Truthy) marks.Add(new(at("garden").X, at("garden").Z, "Quiet Garden", MarkKind.Place));
        foreach (var (id, a) in Actors)
        {
            if (a.Hidden) continue;
            var m = Dialogue.All.TryGetValue(id, out var convo) ? Dialogue.MarkerOf(convo, C) : null;
            // On the map, a '?' (news to bring, something to turn in) is gold;
            // someone you have simply not met yet is just a name.
            if (m == "?") marks.Add(new(a.X, a.Z, a.Def.Name, MarkKind.Quest));
            else if (m != null) marks.Add(new(a.X, a.Z, a.Def.Name, MarkKind.Person));
        }
        return marks;
    }

    public override AmbienceMix Ambience(double x, double z)
    {
        var t = W.Time;
        bool dark = t == TimeOfDay.Night, day = t is TimeOfDay.Day or TimeOfDay.Dawn;
        var sm = Way("smithy");
        double forge = Math.Max(0, 1 - Dist(x, z, sm.X, sm.Z) / 26);
        return new AmbienceMix
        {
            Wind = 0.3, Leaves = 0.2, Fire = Warmth(x, z), Town = (dark ? 0.25 : 0.85) * (1 - Math.Min(1, Math.Sqrt(x * x + z * z) / 60) * 0.6),
            Smithy = day ? forge : 0, Birds = day ? 0.45 : 0, Crickets = dark ? 0.55 : t == TimeOfDay.Dusk ? 0.25 : 0, Owl = dark ? 0.3 : 0,
        };
    }

    public override void Begin(Battle b)
    {
        base.Begin(b);
        People();
        DressStall();
        G.SetAtmosphere(AtmosphereFor(W.Time));
        nightNow = Dark;
        SetNight(nightNow);
        Presence();
        G.SetObjectives(Objectives.Of(C));
        G.AnnounceZone();
        if (!F("waystation.visited").Truthy)
        {
            W.Facts["waystation.visited"] = true;
            G.After(2.5, () => G.Say("The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.", null, 5));
        }
        else if (!F("maps.told").Truthy && F("prologue.done").Truthy)
        {
            // Once the town knows you: someone new on the Old Road, selling maps.
            W.Facts["maps.told"] = true;
            G.After(2.5, () => G.Say("A cartographer has set up a stall on the Old Road, by the east gate: maps to places the road forgets.", null, 5));
        }
    }

    public override void Frame(double dt)
    {
        if (B == null) return;
        double px = B.Player.X, pz = B.Player.Z;
        foreach (var a in Actors.Values) a.Update(dt, px, pz);
        foreach (var a in guards) a.Update(dt, px, pz);
        foreach (var a in keepers) { a.Hidden = Dark; a.Update(dt, px, pz); }
        folk.Update(dt, px, pz);
        trackT -= dt;
        if (trackT <= 0)
        {
            trackT = 1;
            Presence();
            G.SetObjectives(Objectives.Of(C));
            // The hour turned (a rest, waiting for night): light the braziers or put them out.
            if (Dark != nightNow) { nightNow = Dark; SetNight(nightNow); }
        }
        var plates = new List<Plate>();
        foreach (var (id, a) in Actors)
        {
            if (a.Hidden) continue;
            bool metThem = W.Npcs.TryGetValue(id, out var s) && s.Flags.TryGetValue("met", out var met) && met.Truthy;
            var mark = Dialogue.All.TryGetValue(id, out var convo) ? Dialogue.MarkerOf(convo, C) : null;
            plates.Add(new Plate(id, a.X, G.Look.HeightAt(a.X, a.Z) + 2.25 * (a.Def.Scale ?? 1) - (a.Seated ? 0.5 : 0), a.Z, a.Def.Name,
                metThem ? a.Def.Role : null, mark is { Length: > 0 } ? mark[0] : null));
        }
        G.Look.Plates(plates);
    }

    public override Dictionary<string, object?> Debug() => new()
    {
        ["folk"] = folk.Count, ["lanes"] = folk.Validate(), ["night"] = nightNow,
    };

    public override void Dispose()
    {
        base.Dispose();
        foreach (var a in guards) a.Dispose();
        foreach (var a in keepers) a.Dispose();
        folk?.Dispose();
        G.Look.Plates(new());
        G.SetObjectives(new());
    }
}
