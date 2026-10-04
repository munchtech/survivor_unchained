using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The recorded voices (data/vo/index.json, art/vo): every take is
/// on disk, belongs to a line that exists, and was made from exactly that
/// line's words as they stand now. A line the writer has changed since must
/// be recorded again (tools/vo/produce.py) or it is caught here.</summary>
public class VoiceTests
{
    static string ArtDir => Path.GetFullPath(Path.Combine(DataFiles.Dir, "..", "art", "vo"));
    static string LogicDir => Path.GetFullPath(Path.Combine(DataFiles.Dir, "..", "logic"));

    static VoIndex Index()
    {
        var p = Path.Combine(DataFiles.Dir, "vo", "index.json");
        return File.Exists(p) ? Json.Parse<VoIndex>(File.ReadAllText(p)) : new VoIndex();
    }

    /// <summary>Every string written in the zone code, as the game holds it.</summary>
    static HashSet<string> CodeStrings()
    {
        var all = new HashSet<string>();
        var lit = new Regex(@"""((?:[^""\\]|\\.)*)""");
        foreach (var f in Directory.EnumerateFiles(LogicDir, "*.cs", SearchOption.AllDirectories))
            foreach (Match m in lit.Matches(File.ReadAllText(f)))
                all.Add(Regex.Unescape(m.Groups[1].Value));
        return all;
    }

    /// <summary>The words a line id stands for, read from the content; null if no such line.</summary>
    static string? TextOf(string id, Lazy<HashSet<string>> code)
    {
        var p = id.Split('.');
        // Takes of the same words by a woman and a man: folk.12.f, guard.0.m.
        if (p[0] is "folk" or "guard" && p.Length == 3 && p[2] is "f" or "m") p = p[..2];
        switch (p[0])
        {
            case "dlg":
                if (p.Length != 4 || Dialogue.Find(p[1]) is not { } c || !c.Nodes.TryGetValue(p[2], out var n)) return null;
                int v = int.Parse(p[3]);
                return v < n.Text.Count ? n.Text[v].Text : null;
            case "bark":
                var npc = Lore.Person(p[1]);
                var list = p[2] == "night" ? npc?.NightBarks : npc?.Barks;
                int b = int.Parse(p[3]);
                return list != null && b < list.Count ? list[b] : null;
            case "guard":
                int g = int.Parse(p[1]);
                return g < Lore.Guards.Count ? Lore.Guards[g].Line : null;
            case "folk":
                int f = int.Parse(p[1]);
                return f < Lore.FolkLines.Count ? Lore.FolkLines[f].Text : null;
            case "say":
            case "cbark":
                return code.Value.FirstOrDefault(s => VoiceLines.Hash(s) == p[1]);
        }
        return null;
    }

    [Fact]
    public void HashMatchesTheTools()
    {
        // tools/vo/lines.py text_hash: the first 12 hex digits of SHA-1 over UTF-8.
        Assert.Equal("15dacab66734", VoiceLines.Hash("Payment, always."));
        Assert.Equal("f641911d6fdc", VoiceLines.Hash("Oho! A Warden’s heart"));
    }

    [Fact]
    public void EveryTakeIsOnDiskAndMadeFromTheWordsOnScreen()
    {
        var idx = Index();
        var code = new Lazy<HashSet<string>>(CodeStrings);
        var problems = new List<string>();
        foreach (var (id, t) in idx.Lines)
        {
            if (!File.Exists(Path.Combine(ArtDir, t.File))) problems.Add($"{id}: {t.File} is missing");
            if (!t.File.EndsWith(".ogg")) problems.Add($"{id}: {t.File} is not Ogg Vorbis");
            if (!t.File.EndsWith($"/{id}.ogg")) problems.Add($"{id}: the file {t.File} is not named for the line");
            var text = TextOf(id, code);
            if (text == null) problems.Add($"{id}: no such line any more");
            else if (VoiceLines.Hash(text) != t.Hash) problems.Add($"{id}: recorded from other words than \"{text}\" (record it again)");
            if (t.Sec <= 0.2 || t.Sec > 90) problems.Add($"{id}: {t.Sec} s long");
            double last = 0;
            foreach (var s in t.Segs ?? new())
            {
                if (s.Length != 4 || s[0] < last - 1e-6 || s[1] < s[0] || s[1] > t.Sec + 0.05 || s[2] < 0 || s[3] > 1.0001 || s[3] < s[2])
                    problems.Add($"{id}: a part's marks are out of order ({string.Join(", ", s)})");
                last = s.Length > 1 ? s[1] : last;
            }
            if (t.Sex is not (null or "f" or "m")) problems.Add($"{id}: sex '{t.Sex}'");
        }
        Assert.True(problems.Count == 0, string.Join("\n", problems));
    }

    [Fact]
    public void AConversationsLineCarriesItsIdAndWords()
    {
        var ctx = Lore.Context(WorldState.Fresh(1), H.Survivor());
        var p = new DialogueRunner(Dialogue.Find("rook")!, ctx).Start()!;
        Assert.Matches(@"^dlg\.rook\.first\.\d+$", p.Line!);
        int v = int.Parse(p.Line!.Split('.')[3]);
        Assert.Equal(p.Node.Text[v].Text, p.Raw);
        Assert.Equal(VoiceLines.Dialogue("rook", "first", v), p.Line);
    }

    [Fact]
    public void ATakeIsOnlyPlayedForTheWordsItWasMadeFrom()
    {
        var keep = VoiceLines.Index;
        try
        {
            VoiceLines.Use(new VoIndex { Lines = { ["dlg.rook.hub.2"] = new VoTake { File = "rook/dlg.rook.hub.2.ogg", Hash = VoiceLines.Hash("Back again, {name}. What'll it be?"), Sec = 2 } } });
            Assert.NotNull(VoiceLines.Take("dlg.rook.hub.2", "Back again, {name}. What'll it be?"));
            Assert.Null(VoiceLines.Take("dlg.rook.hub.2", "Back again. What'll it be?"));
            Assert.Single(VoiceLines.ByText("Back again, {name}. What'll it be?"));
        }
        finally { VoiceLines.Use(keep); }
    }
}
