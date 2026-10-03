using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The voice pass: line IDs, the hash of the words, which take a
/// line plays and when it stays silent; and a report of how far the
/// manifest has fallen behind the writing, which never fails a build.</summary>
[Collection("voice")]
public class VoiceTests(ITestOutputHelper log) : IDisposable
{
    public void Dispose() => VoiceLines.Load(null);

    static string TakesJson(params (string Id, string Voice, string Text)[] takes) =>
        "{ \"takes\": {" + string.Join(",", takes.Select(t =>
            $"\"{t.Id}\": {{ \"voice\": \"{t.Voice}\", \"hash\": \"{VoiceLines.Hash(t.Text)}\", \"file\": \"res://audio/vo/{t.Voice}/{t.Id}.ogg\" }}")) + "} }";

    [Fact]
    public void The_hash_is_the_tools_hash()
    {
        // Worked out by tools/voice/extract.py's text_hash.
        Assert.Equal("ffe9468e5f83", VoiceLines.Hash("Wipe your boots."));
        Assert.Equal("c70369651abe", VoiceLines.Hash("Late, {name}. Stew's cold. Beds aren't."));
        Assert.Equal("ede250bcd98b", VoiceLines.Hash("— é"));
    }

    [Fact]
    public void A_line_is_named_by_its_node_and_its_variant()
    {
        Assert.Equal("rook.first", VoiceLines.DialogueId("rook", "first", 0, 1));
        Assert.Equal("rook.hub.3", VoiceLines.DialogueId("rook", "hub", 2, 4));
    }

    [Fact]
    public void The_variant_spoken_is_the_one_on_screen()
    {
        var s = H.Make();
        var never = new Cond { Day = new Cmp { Gte = 999 } };
        var first = new List<Variant> { new() { When = never, Text = "a" }, new() { Text = "b" }, new() { Text = "c" } };
        Assert.Equal([1], VoiceLines.Spoken(first, s.C));
        var none = new List<Variant> { new() { When = never, Text = "a" }, new() { When = never, Text = "b" } };
        Assert.Equal([1], VoiceLines.Spoken(none, s.C));
        Assert.Equal("b", Dialogue.PickText(none, s.C));
        var notices = new List<Variant> { new() { Add = true, Text = "a" }, new() { Add = true, When = never, Text = "b" }, new() { Add = true, Text = "c" } };
        Assert.Equal([0, 2], VoiceLines.Spoken(notices, s.C));
    }

    [Fact]
    public void Without_takes_nothing_plays()
    {
        VoiceLines.Load(null);
        var s = H.Make();
        var rook = Dialogue.Find("rook")!;
        var p = new DialogueRunner(rook, s.C).Start()!;
        Assert.False(VoiceLines.Any);
        Assert.Empty(VoiceLines.ForNode("rook", p.Node, s.C));
        Assert.Null(VoiceLines.ForText("Wipe your boots."));
        VoiceLines.Load("not json at all");
        Assert.False(VoiceLines.Any);
    }

    [Fact]
    public void A_take_plays_only_for_the_words_it_was_recorded_for()
    {
        var s = H.Make();
        var rook = Dialogue.Find("rook")!;
        var p = new DialogueRunner(rook, s.C).Start()!;
        var n = p.Node;
        int i = VoiceLines.Spoken(n.Text, s.C).Single();
        string id = VoiceLines.DialogueId("rook", n.Id, i, n.Text.Count);
        VoiceLines.Load(TakesJson((id, "rook", n.Text[i].Text)));
        var takes = VoiceLines.ForNode("rook", n, s.C);
        Assert.Equal(id, Assert.Single(takes).Id);
        Assert.Equal($"res://audio/vo/rook/{id}.ogg", takes[0].File);
        Assert.False(VoiceLines.Stale(id, n.Text[i].Text));
        // The writing moved on: the old take is stale, and silent.
        VoiceLines.Load(TakesJson((id, "rook", "Something she used to say.")));
        Assert.Empty(VoiceLines.ForNode("rook", n, s.C));
        Assert.True(VoiceLines.Stale(id, n.Text[i].Text));
    }

    [Fact]
    public void A_passing_line_is_said_in_the_voice_of_whoever_passes()
    {
        const string line = "Mind the cart.";
        VoiceLines.Load(TakesJson(("folk.2.m", "townsman", line), ("folk.2.f", "townswoman", line), ("bark.rook.2", "rook", "Wipe your boots.")));
        Assert.Equal("folk.2.f", VoiceLines.ForText(line, "f")!.Id);
        Assert.Equal("folk.2.m", VoiceLines.ForText(line, "m")!.Id);
        Assert.NotNull(VoiceLines.ForText(line));
        Assert.Equal("bark.rook.2", VoiceLines.ForText("Wipe your boots.", "f")!.Id);
        Assert.Null(VoiceLines.ForText("Executed"));
        // Only a wife says "my husband": a man walking past says it unvoiced.
        const string wife = "My husband says the wolves are the Watch's problem.";
        VoiceLines.Load(TakesJson(("folk.102.f", "townswoman", wife)));
        Assert.Equal(["f"], VoiceLines.Sexes(wife));
        Assert.Null(VoiceLines.ForText(wife, "m"));
        Assert.NotNull(VoiceLines.ForText(wife, "f"));
    }

    [Fact]
    public void The_manifest_keeps_its_own_promises()
    {
        var m = VoiceLines.ReadManifest();
        if (m == null) { log.WriteLine("No manifest yet: python3 tools/voice/extract.py writes godot/data/voice/lines.json."); return; }
        Assert.Equal(m.Lines.Count, m.Lines.Select(l => l.Id).Distinct().Count());
        foreach (var l in m.Lines)
        {
            Assert.Equal($"res://audio/vo/{l.Voice}/{l.Id}.ogg", l.File);
            Assert.Equal(VoiceLines.Hash(l.Text), l.Hash);
        }
    }

    /// <summary>Lines written since the manifest was, or rewritten: said, not
    /// failed, so the writing is never held up by the voice pass. Run
    /// `dotnet test --logger "console;verbosity=detailed"` to read it.</summary>
    [Fact]
    public void Report_lines_the_manifest_has_not_caught_up_with()
    {
        var m = VoiceLines.ReadManifest();
        if (m == null) { log.WriteLine("No manifest yet: python3 tools/voice/extract.py writes godot/data/voice/lines.json."); return; }
        var listed = m.Lines.ToDictionary(l => l.Id, l => l.Hash);
        var hashes = m.Lines.Select(l => l.Hash).ToHashSet();
        var content = VoiceLines.FromContent();
        var missing = content.Keys.Where(id => !listed.ContainsKey(id)).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var changed = content.Where(kv => listed.TryGetValue(kv.Key, out var h) && h != kv.Value).Select(kv => kv.Key).OrderBy(x => x, StringComparer.Ordinal).ToList();
        // The zone scripts' captions, read as text: the first words of each G.Say.
        var zones = Path.GetFullPath(Path.Combine(DataFiles.Dir, "..", "logic", "Play", "Zones"));
        var unlisted = new List<string>();
        if (Directory.Exists(zones))
            foreach (var f in Directory.EnumerateFiles(zones, "*.cs"))
                foreach (Match x in Regex.Matches(File.ReadAllText(f), @"\bG\.Say\(\s*""((?:[^""\\]|\\.)*)"""))
                {
                    var words = Regex.Unescape(x.Groups[1].Value);
                    if (!hashes.Contains(VoiceLines.Hash(words))) unlisted.Add($"{Path.GetFileName(f)}: \"{(words.Length > 60 ? words[..60] + "…" : words)}\"");
                }
        var stale = VoiceLines.Takes.Values.Where(t => listed.TryGetValue(t.Id, out var h) && h != t.Hash).Select(t => t.Id).ToList();
        if (missing.Count + changed.Count + unlisted.Count + stale.Count == 0)
        {
            log.WriteLine($"The voice manifest is up to date: {m.Lines.Count} lines, {VoiceLines.Takes.Count} recorded.");
            return;
        }
        var report = new List<string> { "The voice manifest is behind the writing (this is a note, not a failure):" };
        void Say(string what, List<string> ids)
        {
            if (ids.Count == 0) return;
            report.Add($"  {ids.Count} {what}: {string.Join(", ", ids.Take(12))}{(ids.Count > 12 ? ", …" : "")}");
        }
        Say("lines not in the manifest", missing);
        Say("lines whose words changed since the manifest", changed);
        Say("zone captions not in the manifest", unlisted);
        Say("takes recorded for words the manifest no longer has", stale);
        report.Add("  Run python3 tools/voice/extract.py to catch up, then tools/voice/tts_batch.py to voice what is new.");
        foreach (var r in report) log.WriteLine(r);
        Console.WriteLine(string.Join(Environment.NewLine, report));
    }
}
