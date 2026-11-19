using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Core;

/// <summary>
/// The demo flavor (the owner, 18 Nov 2026: "a very straightforward demo getting to town and then the dungeon"): the tutorial in
/// Lowford, the town, the den, nothing else. On in a build exported with the custom feature `demo` (preset "Windows Demo") or a dev
/// run given `--demo`; the engine sets <see cref="On"/> once at start. What it hides is data (data/content/demo.json): every cut is
/// a guard at one choke point reading a list here, never deleted code; empty a list (or set a switch false) to bring it back.
/// </summary>
public static class Demo
{
    /// <summary>Whether this run is the demo (set by the engine at start: OS.HasFeature("demo") or --demo).</summary>
    public static bool On;

    public sealed class Cuts
    {
        /// <summary>Interactables not offered (exact ids; a trailing '*' matches a prefix: "talk:*").</summary>
        public List<string> Interactables = new();
        /// <summary>Cinematics not played (the zone does without, as under --nocine); "*" is every one.</summary>
        public List<string> Cinematics = new();
        /// <summary>Storybooks not shown (what follows them still runs, as under --nocine); "*" is every one.</summary>
        public List<string> Storybooks = new();
        /// <summary>Conversations not opened (Game.Talk); "*" is every one.</summary>
        public List<string> Talks = new();
        /// <summary>goals.json entries dropped, by id.</summary>
        public List<string> HideGoals = new();
        /// <summary>Goals of the demo's own (the same shape as goals.json's).</summary>
        public JsonElement? Goals;
        /// <summary>The day clock stands still (it is always day: the night only offers arenas, and shuts the den's mouth).</summary>
        public bool FreezeClock;
        /// <summary>No arena of any kind (the Wayfinder's maps, ember scars, story nights, answering the night).</summary>
        public bool NoArenas;
        /// <summary>No Wayfinder's table (maps and the atlas).</summary>
        public bool NoMapTable;
        /// <summary>The new journey opens straight on the tutorial, not on the story's storybook.</summary>
        public bool NoOpeningStory;
        /// <summary>The creator shows only "A woman" (the male hero is untested).</summary>
        public bool HideMale;
        /// <summary>Dev keys a tester could hit by accident do nothing (F7, the facing mode).</summary>
        public bool NoDevKeys;
        /// <summary>Dungeons offered, by id (an empty list: all).</summary>
        public List<string> Dungeons = new();
        /// <summary>Callings the creator offers, by id (an empty list: as the full game; the owner 17 Nov: "hide all 3 besides warden for demo").</summary>
        public List<string> Callings = new();
    }

    static Cuts? cuts;
    /// <summary>The cut lists (data/content/demo.json), read once; a missing file cuts nothing.</summary>
    public static Cuts Data => cuts ??= Load();

    /// <summary>(tests) Reads the cut lists from this JSON instead of the file.</summary>
    public static void Use(string? json) => cuts = json == null ? null : Parse(json);

    static Cuts Load()
    {
        try { return Parse(Json.ReadContent("demo.json")); }
        catch (System.IO.IOException) { return new Cuts(); }
    }

    static Cuts Parse(string json)
    {
        using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true });
        var r = doc.RootElement;
        var c = new Cuts();
        List<string> L(string k) => r.TryGetProperty(k, out var a) && a.ValueKind == JsonValueKind.Array ? a.EnumerateArray().Select(e => e.GetString() ?? "").Where(s => s != "").ToList() : new();
        bool B(string k) => r.TryGetProperty(k, out var b) && b.ValueKind == JsonValueKind.True;
        c.Interactables = L("hide_interactables"); c.Cinematics = L("hide_cinematics"); c.Storybooks = L("hide_storybooks");
        c.Talks = L("hide_talks"); c.HideGoals = L("hide_goals"); c.Dungeons = L("dungeons"); c.Callings = L("callings");
        if (r.TryGetProperty("goals", out var g) && g.ValueKind == JsonValueKind.Array) c.Goals = g.Clone();
        c.FreezeClock = B("freeze_clock"); c.NoArenas = B("no_arenas"); c.NoMapTable = B("no_map_table");
        c.NoOpeningStory = B("no_opening_story"); c.HideMale = B("hide_male"); c.NoDevKeys = B("no_dev_keys");
        return c;
    }

    /// <summary>Whether a list cuts this id: an exact entry, "*", or a "prefix*" entry.</summary>
    public static bool Listed(IEnumerable<string> list, string id) =>
        list.Any(e => e == "*" || e == id || (e.EndsWith('*') && id.StartsWith(e[..^1], StringComparison.Ordinal)));

    /// <summary>In the demo, whether this interactable is not offered.</summary>
    public static bool HidesInteractable(string id) => On && Listed(Data.Interactables, id);
    public static bool HidesCinematic(string id) => On && Listed(Data.Cinematics, id);
    public static bool HidesStorybook(string id) => On && Listed(Data.Storybooks, id);
    public static bool HidesTalk(string id) => On && Listed(Data.Talks, id);
    public static bool HidesGoal(string id) => On && Data.HideGoals.Contains(id);
    public static bool HidesDungeon(string id) => On && Data.Dungeons.Count > 0 && !Data.Dungeons.Contains(id);
    /// <summary>In the demo, whether the creator leaves this calling out entirely (whatever --body or her_body.json say).</summary>
    public static bool HidesCalling(string id) => On && Data.Callings.Count > 0 && !Data.Callings.Contains(id);
    public static bool FreezeClock => On && Data.FreezeClock;
    public static bool NoArenas => On && Data.NoArenas;
    public static bool NoMapTable => On && Data.NoMapTable;
    public static bool NoOpeningStory => On && Data.NoOpeningStory;
    public static bool HideMale => On && Data.HideMale;
    public static bool NoDevKeys => On && Data.NoDevKeys;
}
