using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The Lamps (docs/design/CLASSES.md §2): one dark board of the valley's
 * roads, a quarter to each calling, and a survivor lights lamps along them.
 *
 * Each quarter has a hearth (where the calling starts: its dash form, its
 * reflexes, its Flare lamps), two roads (one per type: the entry lamp carries
 * the type's mechanic) and a bridge between them; crossings join neighbouring
 * quarters. A lamp hangs from others (At), and can be lit when one it touches
 * is lit. Depth gates count lamps lit on the lamp's own road.
 *
 * Every lamp says what it does as effects. An effect's Phase says when it
 * comes alive (§7): phase 1's work now; a later phase's are written, waiting
 * on the skill or the grip they change (LampsTests holds the accounting).
 * All of it is data (data/content/lamps.json). */

public enum LampKind { Start, Small, Attribute, Entry, Skill, Notable, Blue, Reflex, ReflexUp, Form, FlareLamp, Ultimate, UltimateMod }

public enum LampRegion { Hearth, Road, Bridge, Crossing }

/// <summary>What an effect is: a number, an attribute, a rule the fight reads, a facet of an art,
/// the dash form, a reflex, a Flare learned, or a Flare reshaped.</summary>
public enum LampDo { Mod, Attr, Rule, Facet, Form, Reflex, Flare, FlareMod }

public sealed class LampEffect
{
    public LampDo Do;
    /// <summary>Mod: a stat changed (a stat key, Stat.*), how, by how much, and when.</summary>
    public string? Stat;
    public ModKind Mod = ModKind.Inc;
    public double Value;
    public ModWhen? When;
    /// <summary>A blue lamp's price: kept in full by night, when sizes shrink (§2.10).</summary>
    public bool Price;
    /// <summary>Attr: an attribute (might, finesse, wits, resolve), by Value points.</summary>
    public string? Attr;
    /// <summary>Rule: the rule's id, read by the fight (Battle.Lamp); its numbers in Args.</summary>
    public string? Rule;
    public Dictionary<string, double>? Args;
    /// <summary>Facet, Form, Reflex: the art (Abilities' id) and the facet; a reflex's trigger and a form's or reflex's wait.</summary>
    public string? Art, Facet, Trigger;
    public double Wait;
    /// <summary>Flare, FlareMod: the Flare (FlareDef's id), and the modifier.</summary>
    public string? Flare;
    /// <summary>The combat skill it changes (a skill lamp's, or a mod on one skill).</summary>
    public string? Skill;
    /// <summary>The skills it changes by their tags (any of them): "heavy and nova skills".</summary>
    public Tag[]? Tags;
    /// <summary>A status it adds or reads (a skill that bleeds what it strikes).</summary>
    public StatusKind? Status;
    /// <summary>The phase that brings it to life (docs/design/CLASSES.md §7). Above 1 it is inert for now.</summary>
    public int Phase = 1;

    public double Arg(string key, double fallback = 0) => Args != null && Args.TryGetValue(key, out var v) ? v : fallback;
}

public sealed class LampDef
{
    public string Id = "", Name = "", Text = "";
    public LampKind Kind;
    public LampRegion Region;
    /// <summary>The quarter's calling (null on a crossing, which two share).</summary>
    public string? Calling;
    /// <summary>The road (a RoadDef's id), the bridge ("warden.bridge") or the crossing ("shambles").</summary>
    public string? Road;
    /// <summary>The lamps it hangs from: lit, any of them opens it. Joins are both ways (Lamps.Next).</summary>
    public string[] At = [];
    /// <summary>The combat skills it feeds (their glyphs on the lamp; dimmed when none is carried).</summary>
    public string[] Feeds = [];
    /// <summary>Lamps lit on its road before it can be lit (§2.2's depth gates).</summary>
    public int Gate;
    public LampEffect[] Effects = [];
    /// <summary>A Flare modifier Light my way may light before Act 1 is done (one per Flare, measured on Act 1; §7).</summary>
    public bool Early;

    /// <summary>Only the calling may light it: the hearth is home, and Flares are the one hard lock (§2.7).</summary>
    public bool Home => Region == LampRegion.Hearth || Kind is LampKind.Ultimate or LampKind.UltimateMod;
}

public enum FlareKind { Strike, Stand }

/// <summary>A Flare (§3): the calling's ultimate. Phase 1 plays each as its kind's plain form
/// (a Strike's blows, a Stand's pulses) with these numbers; phase 2 stages each one.</summary>
public sealed class FlareDef
{
    public string Id = "", Name = "", Calling = "", Road = "", Text = "";
    /// <summary>Its own line glyph (data/content/glyphs.json's key): what the HUD's Q vessel wears, never the calling's badge.</summary>
    public string Icon = "";
    public FlareKind Kind;
    /// <summary>A Strike: how long it holds the controls (1.2 s at most). A Stand: how long it holds.</summary>
    public double Length;
    /// <summary>Its reach, in metres.</summary>
    public double Radius;
    /// <summary>A Strike: its blows over its length. A Stand: its pulses a second.</summary>
    public int Blows = 1;
    /// <summary>Each blow's damage at level 1 (Lamps.FlarePower scales it by level).</summary>
    public double Power;
    public School School = School.Physical;
    /// <summary>It counts as these tags, so its road's lamps feed it (The Long Cut is heavy).</summary>
    public Tag[] Tags = [];
    /// <summary>What it does for the survivor while it holds (a Stand): "cut" blows by Value, "mend" a share a second.</summary>
    public string? Guard;
    public double GuardValue;
    /// <summary>A staged Flare's beat (phase 2, CLASSES.md §3.5-3.6): its timings from the press in seconds ("key": the
    /// key pose's end; "first"/"step" or "first"/"last": the blows'; Burns Twice's "frost") and its hitstop in frames
    /// ("hitstop", "hitstopLast", "hitstopExecute", "hitstopFrost"). The logic schedules its blows by it; the view reads the rest.</summary>
    public Dictionary<string, double> Beat = new();
    /// <summary>Staged (its own logic, FlareStaged.cs) once its data has a beat; without one it plays its kind's plain
    /// form (the harness measures a staged Flare against it so).</summary>
    public bool Staged => Beat.Count > 0;
    /// <summary>A staged Flare's own numbers (shares of its power, seconds, metres), by name.</summary>
    public Dictionary<string, double> Args = new();
    public double Arg(string key, double fallback) => Args.TryGetValue(key, out var v) ? v : fallback;
    public double BeatAt(string key, double fallback) => Beat.TryGetValue(key, out var v) ? v : fallback;
}

/// <summary>A road: one type of a calling (§1).</summary>
public sealed class RoadDef
{
    public string Id = "", Calling = "", Name = "", Line = "";
    /// <summary>What's in the hands: the grip the type starts with (an item id; a grip still to be made is null).</summary>
    public string? Grip;
    /// <summary>Its three signature skills: the cards its depth leans toward at night (§2.10).</summary>
    public string[] Skills = [];
    /// <summary>Its Flares: the Strike (given with the type) and the Stand.</summary>
    public string Strike = "", Stand = "";
}

public static class Lamps
{
    sealed class File
    {
        public List<RoadDef> Roads = new();
        public List<FlareDef> Flares = new();
        public List<LampDef> Lamps = new();
        /// <summary>The story's fights whose first win lights a lamp (their arena ids).</summary>
        public List<string> Story = new();
    }

    sealed class Board
    {
        public readonly Dictionary<string, LampDef> All;
        public readonly Dictionary<string, RoadDef> Roads;
        public readonly Dictionary<string, FlareDef> Flares;
        public readonly Dictionary<string, List<string>> Next = new();
        public readonly List<string> Story;

        public Board(File f)
        {
            All = f.Lamps.ToDictionary(l => l.Id);
            Roads = f.Roads.ToDictionary(r => r.Id);
            Flares = f.Flares.ToDictionary(x => x.Id);
            Story = f.Story;
            foreach (var l in f.Lamps) Next[l.Id] = new();
            foreach (var l in f.Lamps)
                foreach (var a in l.At)
                {
                    if (!Next.ContainsKey(a)) throw new InvalidOperationException($"lamp {l.Id} hangs from no lamp {a}");
                    if (!Next[l.Id].Contains(a)) Next[l.Id].Add(a);
                    if (!Next[a].Contains(l.Id)) Next[a].Add(l.Id);
                }
        }
    }

    static Board? board;
    static Board B => board ??= new Board(Json.Parse<File>(Json.ReadContent("lamps.json")));

    public static IReadOnlyDictionary<string, LampDef> All => B.All;
    public static IReadOnlyDictionary<string, RoadDef> Roads => B.Roads;
    public static IReadOnlyDictionary<string, FlareDef> Flares => B.Flares;
    public static IReadOnlyList<string> StoryFights => B.Story;

    public static LampDef Get(string id) => B.All.TryGetValue(id, out var l) ? l : throw new KeyNotFoundException($"no lamp {id}");
    public static LampDef? Find(string id) => B.All.GetValueOrDefault(id);
    public static RoadDef Road(string id) => B.Roads.TryGetValue(id, out var r) ? r : throw new KeyNotFoundException($"no road {id}");
    public static FlareDef? Flare(string id) => B.Flares.GetValueOrDefault(id);

    /// <summary>The lamps this one touches (it hangs from them, or they from it).</summary>
    public static IReadOnlyList<string> Next(string id) => B.Next.TryGetValue(id, out var n) ? n : [];

    /// <summary>A calling's two roads, its first the one a new survivor is offered first.</summary>
    public static IEnumerable<RoadDef> RoadsOf(string calling) => B.Roads.Values.Where(r => r.Calling == calling);

    /// <summary>Where a calling starts: its hearth's first lamp, always lit.</summary>
    public static string Start(string calling) => B.All.Values.First(l => l.Kind == LampKind.Start && l.Calling == calling).Id;

    /// <summary>A road's entry lamp (the type's mechanic).</summary>
    public static string Entry(string road) => B.All.Values.First(l => l.Kind == LampKind.Entry && l.Road == road).Id;

    /// <summary>The lamp that learns a Flare.</summary>
    public static string? FlareLamp(string flare) =>
        B.All.Values.FirstOrDefault(l => l.Kind == LampKind.Ultimate && l.Effects.Any(e => e.Do == LampDo.Flare && e.Flare == flare))?.Id;

    /* --------------------------------------------------- what lamps give -- */

    /// <summary>By night, sizes run at a quarter (§2.10): rules cross into the night, numbers barely do.</summary>
    public const double NightSize = 0.25;
    /// <summary>Lamp effects of a later phase stay dark until the build reaches it (phase 2: the four staged Flares' lamps).</summary>
    public const int LivePhase = 2;
    /// <summary>By night, the whole board adds at most this much to each count (projectiles, pierce, chains).</summary>
    public const int NightCount = 1;
    /// <summary>By night, small lamps give no numbers: their road leans the draft (×1.25, as the Edge does).</summary>
    public const double RoadLean = 1.25;
    /// <summary>The calling's path lean and the road's multiply, clamped here.</summary>
    public const double LeanCap = 2;

    /// <summary>Stats that are counts, not sizes: by night the board adds at most one of each.</summary>
    public static bool IsCount(string stat) => stat is Sim.Stat.Projectiles or Sim.Stat.Pierce or Sim.Stat.DashCharges;

    /// <summary>A Flare's damage scales with level (the character's by day and in maps, the ember's at night),
    /// by the rule every ember-scaled blow of hers follows (Battle.BaseOf's flat damage, Rise Fire, thorns): +8% a level.</summary>
    public static double FlarePower(FlareDef f, int level) => f.Power * (1 + 0.08 * Math.Max(0, level - 1));
}
