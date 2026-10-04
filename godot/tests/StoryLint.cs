using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The story read as a whole, the way a script editor would: every
/// conversation can be walked into and out of, every journal line can be
/// earned, every fact something asks about is something that can happen,
/// every item a choice wants can be found, and nobody changes sex between
/// one page and the next. The content will triple; this keeps it honest.
///
/// The world's language is written in two places, the content JSON and the
/// zone scripts that embed the same JSON in C#, so both are read: the JSON
/// as data, the C# as text.</summary>
public class StoryLint
{
    static readonly string[] ContentFiles = ["dialogue.json", "quests.json", "rules.json", "concerns.json", "folk.json", "shops.json", "npcs.json", "archetypes.json"];

    static string ContentDir => Path.Combine(DataFiles.Dir, "content");
    static string GodotDir => Path.GetFullPath(Path.Combine(DataFiles.Dir, ".."));
    static JsonElement Content(string f) => JsonDocument.Parse(File.ReadAllText(Path.Combine(ContentDir, f))).RootElement;

    /// <summary>The C# that speaks the world's language: the game's logic and its view.</summary>
    static readonly Lazy<List<(string File, string Text)>> Code = new(() =>
        new[] { "logic", "src" }.Select(d => Path.Combine(GodotDir, d)).Where(Directory.Exists)
            .SelectMany(d => Directory.EnumerateFiles(d, "*.cs", SearchOption.AllDirectories))
            .Select(f => (Path.GetRelativePath(GodotDir, f).Replace('\\', '/'), File.ReadAllText(f))).ToList());

    /// <summary>Facts the game writes from outside the story (the settings screen).</summary>
    static bool Outside(string fact) => fact.StartsWith("settings.");

    /* ------------------------------------------------------------ the JSON -- */

    sealed class Uses
    {
        public readonly HashSet<string> FactsRead = new(), FactsWritten = new(), EntriesWritten = new(), ItemsWanted = new(), ItemsGiven = new(), TagsWanted = new();
    }

    static readonly string[] CondKeys = ["when", "show", "if"];
    static readonly Regex FactRef = new(@"\{fact:([\w.]+)\}", RegexOptions.Compiled);

    /// <summary>Walk content: under when/show/if is a question; anything else
    /// that changes the world is a change.</summary>
    static void Walk(JsonElement e, Uses u, bool cond)
    {
        switch (e.ValueKind)
        {
            case JsonValueKind.Object:
                foreach (var p in e.EnumerateObject())
                {
                    var v = p.Value;
                    // (A node may be called "show"; a node has words, a question has none.)
                    bool asCond = cond || (CondKeys.Contains(p.Name) && v.ValueKind == JsonValueKind.Object && !v.TryGetProperty("text", out _));
                    if (asCond)
                    {
                        if (p.Name == "fact" && v.ValueKind == JsonValueKind.String) u.FactsRead.Add(v.GetString()!);
                        if (p.Name == "hasItem" && v.ValueKind == JsonValueKind.String) u.ItemsWanted.Add(v.GetString()!);
                        if (p.Name == "hasTag" && v.ValueKind == JsonValueKind.String) u.TagsWanted.Add(v.GetString()!);
                    }
                    else
                    {
                        if (p.Name is "set" or "add" && v.ValueKind == JsonValueKind.Object) foreach (var k in v.EnumerateObject()) u.FactsWritten.Add(k.Name);
                        if (p.Name == "give" && v.ValueKind == JsonValueKind.String) u.ItemsGiven.Add(v.GetString()!);
                        if (p.Name == "take" && v.ValueKind == JsonValueKind.String) u.ItemsWanted.Add(v.GetString()!);
                        if (p.Name == "quest" && v.ValueKind == JsonValueKind.Object && v.TryGetProperty("entry", out var en) && v.TryGetProperty("id", out var qid))
                            u.EntriesWritten.Add($"{qid.GetString()}/{en.GetString()}");
                    }
                    Walk(v, u, asCond);
                }
                break;
            case JsonValueKind.Array:
                foreach (var x in e.EnumerateArray()) Walk(x, u, cond);
                break;
            case JsonValueKind.String:
                foreach (Match m in FactRef.Matches(e.GetString()!)) u.FactsRead.Add(m.Groups[1].Value);
                break;
        }
    }

    /* -------------------------------------------------------------- the C# -- */

    static IEnumerable<string> All(string text, string pattern, int group = 1) => Regex.Matches(text, pattern).Select(m => m.Groups[group].Value);

    /// <summary>An object's body in embedded JSON, which may hold {{interpolations}}.</summary>
    const string Body = @"((?:[^{}]|\{\{[^{}]*\}\})*)";

    static void ReadCode(Uses u)
    {
        foreach (var (file, t) in Code.Value)
        {
            // Facts: the JSON embedded in scripts, and the scripts' own reads and
            // writes (reads only in the logic: the view's F(...) are other things).
            foreach (Match m in Regex.Matches(t, @"""(?:set|add)""\s*:\s*\{" + Body + @"\}"))
                foreach (var k in All(m.Groups[1].Value, @"""([\w.]+)""\s*:")) u.FactsWritten.Add(k);
            foreach (var k in All(t, @"Facts\[""([\w.]+)""\]\s*=")) u.FactsWritten.Add(k);
            foreach (var k in All(t, @"\bf\[""([\w.]+)""\]\s*=")) u.FactsWritten.Add(k);
            foreach (var k in All(t, @"TurnHostile\(""([\w.]+)""")) u.FactsWritten.Add(k);
            if (file.StartsWith("logic/"))
            {
                foreach (var k in All(t, @"""fact""\s*:\s*""([\w.]+)""")) u.FactsRead.Add(k);
                foreach (var k in All(t, @"\b(?:F|Fact|Num|Is)\((?:c,\s*)?""([\w.]+)""")) u.FactsRead.Add(k);
                foreach (var k in All(t, @"FactKey\s*=\s*""([\w.]+)""")) u.FactsRead.Add(k);
            }
            // Journal lines, including one of two chosen as the script runs:
            // "entry": "{{(blown ? "a" : "b")}}".
            foreach (Match m in Regex.Matches(t, @"""quest""\s*:\s*\{" + Body + @"\}"))
            {
                var id = Regex.Match(m.Groups[1].Value, @"""id""\s*:\s*""(\w+)""");
                if (!id.Success) continue;
                var en = Regex.Match(m.Groups[1].Value, @"""entry""\s*:\s*""([\w.]+)""");
                if (en.Success) u.EntriesWritten.Add($"{id.Groups[1].Value}/{en.Groups[1].Value}");
                var either = Regex.Match(m.Groups[1].Value, @"""entry""\s*:\s*""\{\{\(\w+\s*\?\s*""(\w+)""\s*:\s*""(\w+)""\)\}\}""");
                if (either.Success)
                {
                    u.EntriesWritten.Add($"{id.Groups[1].Value}/{either.Groups[1].Value}");
                    u.EntriesWritten.Add($"{id.Groups[1].Value}/{either.Groups[2].Value}");
                }
            }
            // Items: what scripts check and take, and where things come from.
            foreach (var k in All(t, @"\bHasItem\(""(\w+)""\)")) u.ItemsWanted.Add(k);
            foreach (var k in All(t, @"(?:HasItem\s*=|""hasItem""\s*:|""take""\s*:)\s*""(\w+)""")) u.ItemsWanted.Add(k);
            foreach (var k in All(t, @"""give""\s*:\s*""(\w+)""")) u.ItemsGiven.Add(k);
            foreach (var k in All(t, @"Loot\(PickupKind\.\w+,\s*""(\w+)""")) u.ItemsGiven.Add(k);
            foreach (var k in All(t, @"GiveItem\(""(\w+)""")) u.ItemsGiven.Add(k);
            // Things dropped where a fight ends (the Warden's lamp-iron at the ford).
            foreach (var k in All(t, @"SpawnPickup\(PickupKind\.\w+,[^;""]*""(\w+)""")) u.ItemsGiven.Add(k);
            foreach (var k in All(t, @"(?:HasTag\s*=|""hasTag""\s*:)\s*""(\w+)""")) u.TagsWanted.Add(k);
        }
    }

    static readonly Lazy<Uses> World = new(() =>
    {
        var u = new Uses();
        foreach (var f in ContentFiles) Walk(Content(f), u, false);
        ReadCode(u);
        // Shops, backgrounds and callings hand things over too.
        foreach (var s in Lore.Shops.Values) foreach (var l in s.Lines) u.ItemsGiven.Add(l.Id);
        foreach (var b in Callings.Backgrounds.Values) foreach (var i in b.Items) u.ItemsGiven.Add(i);
        foreach (var a in Callings.Archetypes.Values) foreach (var w in a.Weapons) u.ItemsGiven.Add(w);
        return u;
    });

    /* ------------------------------------------------------------- the tests -- */

    [Fact]
    public void Every_conversation_can_be_walked_into_and_out_of()
    {
        var problems = new List<string>();
        foreach (var (id, c) in Dialogue.All)
        {
            if (c.Entry.Count == 0) { problems.Add($"{id}: no way in"); continue; }
            if (c.Entry[^1].When != null) problems.Add($"{id}: the last entry has a condition, so some visits find nobody home");
            var reach = new HashSet<string>();
            var stack = new Stack<string>(c.Entry.Select(e => e.Node));
            while (stack.Count > 0)
            {
                var n = stack.Pop();
                if (!c.Nodes.TryGetValue(n, out var node)) { problems.Add($"{id}: something points at missing node {n}"); continue; }
                if (!reach.Add(n)) continue;
                if (node.Next != null) stack.Push(node.Next);
                foreach (var ch in node.Choices ?? new())
                {
                    if (ch.Goto != null) stack.Push(ch.Goto);
                    // A topic that answers by asking itself again is a menu, not a conversation.
                    // (Once-only questions are gone by the time their answer is showing.)
                    if (ch.Goto == n && ch.Effects == null && ch.Action == null && ch.Once == null) problems.Add($"{id}.{n}: \"{Dialogue.PickText(ch.Text, Ctx())}\" returns to the node it is on");
                }
            }
            foreach (var n in c.Nodes.Keys.Where(k => !reach.Contains(k))) problems.Add($"{id}.{n}: nothing leads here");
        }
        Assert.Empty(problems);
    }

    [Fact]
    public void Every_journal_line_can_be_earned()
    {
        var u = World.Value;
        var defined = Lore.Quests.SelectMany(q => q.Value.Entries.Keys.Select(e => $"{q.Key}/{e}")).ToHashSet();
        Assert.Empty(defined.Except(u.EntriesWritten).Select(e => $"never added: {e}"));
        Assert.Empty(u.EntriesWritten.Except(defined).Select(e => $"added but not in quests.json: {e}"));
    }

    [Fact]
    public void Every_fact_asked_about_can_happen()
    {
        var u = World.Value;
        // The readers found the story at all (a regex that matches nothing passes everything).
        Assert.True(u.FactsRead.Count > 60 && u.FactsWritten.Count > 60, $"{u.FactsRead.Count} read, {u.FactsWritten.Count} written");
        Assert.Contains("beasts.pelts_sold", u.FactsWritten);
        Assert.Contains("settings.intimacy", u.FactsRead);
        Assert.Empty(u.FactsRead.Where(f => !u.FactsWritten.Contains(f) && !Outside(f)).OrderBy(f => f).Select(f => $"read, never written: {f}"));
    }

    /// <summary>Facts Act 1 records for the acts to come (docs/WRITING_PASS.md
    /// section 9, the bible's ledger in section 10), and the game's own bookkeeping.</summary>
    static readonly string[] Seeds =
    [
        "brannoc.waits_buyer", "chid.note_asked", "harlan.told_dig", "holloway.letter_seen", "jory.told_knew",
        "redcowl.birds", "redcowl.gave_charge", "sella.sleeptalk", "vonnra.asked_jessop", "wayfinder.name",
        // The romances' Act 1 seeds (docs/romance/ARCS.md section 7): what each lover
        // learned of the survivor, read in Act 2 ("what you are") and Act 3.
        "maeca.heard_heart", "maeca.heard_past", "rav.came_back", "sella.cold_sold", "sella.heard_past",
        "player.zone", "map.drawn",
        // The last night, for the town to talk about (docs/EXPERIENCE_AUDIT.md, finding 5): the
        // story's lines read them next; take each off this list as it is read.
        "arena.last.tier", "arena.last.minutes", "arena.last.day", "arena.last.killer",
    ];

    [Fact]
    public void Every_fact_written_is_read_or_is_a_seed_for_a_later_act()
    {
        var u = World.Value;
        Assert.Empty(u.FactsWritten.Where(f => !u.FactsRead.Contains(f) && !Seeds.Contains(f)).OrderBy(f => f).Select(f => $"written, never read: {f}"));
        // A seed that is read now is no longer only a seed: take it off the list.
        Assert.Empty(Seeds.Where(u.FactsRead.Contains).Select(f => $"read now, still listed as a seed: {f}"));
    }

    [Fact]
    public void Every_item_a_choice_wants_can_be_found()
    {
        var u = World.Value;
        Assert.Empty(u.ItemsWanted.Where(i => Items.Find(i) == null).Select(i => $"unknown item: {i}"));
        Assert.Empty(u.ItemsWanted.Where(i => !u.ItemsGiven.Contains(i)).OrderBy(i => i).Select(i => $"wanted, never obtainable: {i}"));
        var tags = Items.All.Values.SelectMany(i => i.Tags ?? new()).Concat(Callings.Traits.Values.SelectMany(t => t.Tags ?? new())).ToHashSet();
        Assert.Empty(u.TagsWanted.Where(t => !tags.Contains(t)).Select(t => $"nothing carries the tag {t}"));
    }

    static readonly Regex His = new(@"\b(he|him|his|himself)\b", RegexOptions.IgnoreCase), Hers = new(@"\b(she|her|hers|herself)\b", RegexOptions.IgnoreCase);

    [Fact]
    public void Nobody_changes_sex_between_pages()
    {
        // What is on someone's mind is written about them: its pronouns are theirs.
        var problems = new List<string>();
        foreach (var (id, list) in Lore.Concerns)
        {
            var sex = Lore.Person(id)?.Person?.Sex;
            if (sex == null) continue;
            var wrong = sex == Sex.Female ? His : Hers;
            foreach (var c in list)
                if (wrong.Match(c.Text) is { Success: true } m) problems.Add($"{id} ({sex}): \"{m.Value}\" in \"{c.Text}\"");
        }
        Assert.Empty(problems);
    }

    [Fact]
    public void Every_explicit_slot_waits_behind_the_setting_with_a_cut_away_beside_it()
    {
        // Explicit scenes are the owner's writer's: the content holds a marked
        // slot, shown only when the player asked for intimate scenes in full,
        // and a cut-away for everyone else.
        var problems = new List<string>();
        int slots = 0;
        foreach (var (id, c) in Dialogue.All)
            foreach (var (nid, n) in c.Nodes)
            {
                var marked = n.Text.Where(v => v.Text.StartsWith("[explicit scene:")).ToList();
                slots += marked.Count;
                foreach (var v in marked)
                    if (v.When?.FactKey != "settings.intimacy" || v.When.Eq?.Str != "full") problems.Add($"{id}.{nid}: a slot not behind settings.intimacy = full");
                if (marked.Count > 0 && !n.Text.Any(v => v.When == null && !v.Text.StartsWith("[explicit scene:"))) problems.Add($"{id}.{nid}: no cut-away");
            }
        Assert.Empty(problems);
        Assert.True(slots >= 3, $"{slots} slots");
    }

    [Fact]
    public void No_genre_word_gets_into_the_valleys_mouth()
    {
        // The bible ("The nights", rule 5): Greymuzzle is the old dog-wolf, never an alpha; no warlords,
        // no gangers. Only words are read: a string with a space in it, so ids like "alpha_dead" pass.
        var genre = new Regex(@"\b(alpha|warlord|ganger)s?\b", RegexOptions.IgnoreCase);
        var found = new List<string>();
        void Read(JsonElement e, string where)
        {
            if (e.ValueKind == JsonValueKind.Object) foreach (var p in e.EnumerateObject()) Read(p.Value, $"{where}.{p.Name}");
            else if (e.ValueKind == JsonValueKind.Array) { int i = 0; foreach (var x in e.EnumerateArray()) Read(x, $"{where}[{i++}]"); }
            else if (e.ValueKind == JsonValueKind.String && e.GetString()!.Contains(' ') && genre.Match(e.GetString()!) is { Success: true } m)
                found.Add($"{where}: \"{m.Value}\"");
        }
        foreach (var f in ContentFiles.Append("items.json").Append("crafting.json")) Read(Content(f), f);
        // The zone scripts say things too (the deeds a fight writes down).
        // Read where the scripts put words: a deed's text, a line said, an announcement.
        var said = new Regex(@"(?:Hist\(\s*""[^""]*"",\s*|Say\(\s*\$?|Announcement\(\s*\$?)""([^""]*)""");
        foreach (var (file, text) in Code.Value)
            foreach (Match lit in said.Matches(text))
                if (genre.Match(lit.Groups[1].Value) is { Success: true } m) found.Add($"{file}: \"{m.Value}\"");
        Assert.Empty(found);
    }

    [Fact]
    public void The_table_names_its_maps_in_the_valleys_words_for_their_people()
    {
        // The bible's place words ("The nights"): a map's name says whose ground it is, and no
        // genre word gets on to the Wayfinder's sheets.
        var words = new Dictionary<string, string[]>
        {
            ["dead"] = ["Howes", "Lows", "Barrows", "Lych-Way", "Chesters", "Burying-Ground"],
            ["pack"] = ["Dene", "Clough", "Holt", "Shaw", "Brake", "Den"],
            ["kerchiefs"] = ["Ruts", "Drove", "Cutting", "Ravine", "Waggon-Way", "Gap"],
            ["lamplings"] = ["Sump", "Delph", "Sough", "Spoil", "Workings"],
        };
        var seen = new HashSet<string>();
        for (int day = 1; day <= 40; day++)
            foreach (var o in SurvivorUnchained.Maps.MapOffers.Today(day, 1 + day % 5, day % 3))
            {
                Assert.Matches(@"^The [A-Z][\w']+ [A-Z][\w-]+$", o.Spec.Name);
                Assert.Contains(o.Spec.Name.Split(' ')[^1], words[o.People]);
                Assert.DoesNotMatch(@"Weeping|Whispering|Bleeding|Moonless|Ashen|Alpha|Warlord", o.Spec.Name);
                seen.Add(o.Spec.Name);
            }
        Assert.True(seen.Count > 40, $"{seen.Count} names in forty days");
    }

    static Ctx Ctx() => Lore.Context(WorldState.Fresh(1), H.Survivor());
}
