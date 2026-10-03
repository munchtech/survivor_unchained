using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.World;

/* Spoken lines, as the voice pass sees them.
 *
 * Every line has an ID from where it lives (a conversation's node and the
 * variant's place in it, a bark's place in its list) and a hash of its words.
 * tools/voice/extract.py writes the manifest (data/voice/lines.json) the
 * same way; tools/voice/tts_batch.py records the takes and writes what it
 * recorded, and for which words, to data/voice/takes.json. A take plays only
 * while the words on screen are still the words it was recorded for, so a
 * rewrite silences its old audio instead of contradicting the subtitle. With
 * no takes at all, nothing here finds anything, and the game is as it was. */

/// <summary>A recorded take: the line it says, whose voice, the hash of the
/// words it was recorded for, and the audio file.</summary>
public sealed class Take
{
    public string Id = "";
    public string Voice = "";
    public string Hash = "";
    public string File = "";
}

/// <summary>One line of the manifest (data/voice/lines.json).</summary>
public sealed class ManifestLine
{
    public string Id = "";
    public string Speaker = "";
    public string Voice = "";
    public string Kind = "";
    public string Text = "";
    public string Hash = "";
    public string File = "";
    public string? Skip;
    public bool Optional;
}

public sealed class Manifest { public List<ManifestLine> Lines = new(); }
public sealed class TakeFile { public Dictionary<string, Take> Takes = new(); }

public static class VoiceLines
{
    /// <summary>The first twelve hex digits of the SHA-1 of the words as
    /// written, tokens and all (text_hash in tools/voice/extract.py).</summary>
    public static string Hash(string text)
    {
        var h = SHA1.HashData(Encoding.UTF8.GetBytes(text));
        return Convert.ToHexString(h, 0, 6).ToLowerInvariant();
    }

    /// <summary>A conversation line's ID: conversation.node, and the variant's
    /// place (from 1) when the node has more than one.</summary>
    public static string DialogueId(string convo, string node, int variant, int count) =>
        count > 1 ? $"{convo}.{node}.{variant + 1}" : $"{convo}.{node}";

    /// <summary>Which variants Dialogue.PickText says, in order: the first that
    /// holds (the last if none does), or every Add variant that holds.</summary>
    public static List<int> Spoken(List<Variant> t, Ctx ctx)
    {
        var said = new List<int>();
        if (t.Exists(v => v.Add))
        {
            for (int i = 0; i < t.Count; i++) if (t[i].Add && Rules.Test(t[i].When, ctx)) said.Add(i);
            return said;
        }
        for (int i = 0; i < t.Count; i++) if (Rules.Test(t[i].When, ctx)) { said.Add(i); return said; }
        if (t.Count > 0) said.Add(t.Count - 1);
        return said;
    }

    static Dictionary<string, Take>? byId;
    static Dictionary<string, List<Take>>? byHash;

    /// <summary>What has been recorded (data/voice/takes.json); empty when
    /// nothing has, or the file cannot be read.</summary>
    public static IReadOnlyDictionary<string, Take> Takes
    {
        get
        {
            if (byId == null)
            {
                string? json = null;
                try { json = DataFiles.Text("voice/takes.json"); }
                catch (Exception) { }
                Load(json);
            }
            return byId!;
        }
    }

    /// <summary>Use these takes (null or unreadable: none).</summary>
    public static void Load(string? json)
    {
        byId = new();
        byHash = new();
        if (string.IsNullOrWhiteSpace(json)) return;
        TakeFile? f;
        try { f = Json.Parse<TakeFile>(json); }
        catch (Exception) { return; }
        foreach (var (id, t) in f.Takes)
        {
            if (string.IsNullOrEmpty(t.File) || string.IsNullOrEmpty(t.Hash)) continue;
            t.Id = id;
            byId[id] = t;
            if (!byHash.TryGetValue(t.Hash, out var list)) byHash[t.Hash] = list = new();
            list.Add(t);
        }
    }

    public static bool Any => Takes.Count > 0;

    /// <summary>The take for this line, if it was recorded for these words.</summary>
    public static Take? For(string id, string text) =>
        Takes.TryGetValue(id, out var t) && t.Hash == Hash(text) ? t : null;

    /// <summary>Whether a take exists but was recorded for other words.</summary>
    public static bool Stale(string id, string text) =>
        Takes.TryGetValue(id, out var t) && t.Hash != Hash(text);

    /// <summary>The takes a conversation line plays, in order (a notice board
    /// reads every notice that is up).</summary>
    public static List<Take> ForNode(string convo, DNode node, Ctx ctx)
    {
        var takes = new List<Take>();
        if (!Any) return takes;
        foreach (var i in Spoken(node.Text, ctx))
            if (For(DialogueId(convo, node.Id, i, node.Text.Count), node.Text[i].Text) is { } t) takes.Add(t);
        return takes;
    }

    /// <summary>A take for words said in the world (a bark, a line under the
    /// picture), found by the words themselves. The hint picks between takes
    /// of the same words: a voice ('rook', 'narrator'), or 'm' or 'f' for a
    /// line any passer-by might say, by who is saying it.</summary>
    public static Take? ForText(string text, string? hint = null)
    {
        _ = Takes;
        if (!byHash!.TryGetValue(Hash(text), out var list) || list.Count == 0) return null;
        if (hint != null)
            foreach (var t in list)
                if (t.Voice == hint || t.Id.EndsWith("." + hint, StringComparison.Ordinal)) return t;
        return list[0];
    }

    /// <summary>The manifest, if there is one.</summary>
    public static Manifest? ReadManifest()
    {
        try { return Json.Parse<Manifest>(DataFiles.Text("voice/lines.json")); }
        catch (Exception) { return null; }
    }

    /// <summary>Every line the content itself holds (conversations, barks, the
    /// town's passing lines), as ID and hash: what the manifest should say,
    /// worked out the way tools/voice/extract.py works it out. The zone
    /// scripts' lines live in code and are left to the tool.</summary>
    public static Dictionary<string, string> FromContent()
    {
        var all = new Dictionary<string, string>();
        foreach (var (cid, convo) in Dialogue.All)
            foreach (var (nid, n) in convo.Nodes)
            {
                if (n.Speaker == "player") continue;
                for (int i = 0; i < n.Text.Count; i++) all[DialogueId(cid, nid, i, n.Text.Count)] = Hash(n.Text[i].Text);
            }
        void Barks(string id, List<string>? list, string prefix)
        {
            for (int i = 0; i < (list?.Count ?? 0); i++) all[$"{prefix}{i + 1}"] = Hash(list![i]);
        }
        foreach (var d in Lore.Npcs.Values.Concat(Lore.Outsiders.Values))
        {
            Barks(d.Id, d.Barks, $"bark.{d.Id}.");
            Barks(d.Id, d.NightBarks, $"bark.{d.Id}.night.");
        }
        for (int i = 0; i < Lore.Guards.Count; i++)
            foreach (var s in new[] { "m", "f" }) all[$"bark.guard.{i + 1}.{s}"] = Hash(Lore.Guards[i].Line);
        var lines = Lore.FolkLines;
        for (int i = 0; i < lines.Count; i++)
        {
            var l = lines[i];
            if (l.Child == true) all[$"folk.{i + 1}"] = Hash(l.Text);
            else foreach (var s in new[] { "m", "f" }) all[$"folk.{i + 1}.{s}"] = Hash(l.Text);
        }
        return all;
    }
}
