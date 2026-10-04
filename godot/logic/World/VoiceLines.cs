using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.World;

/* The recorded voices: which take belongs to which line.
 *
 * Every line the game can say aloud has an id (tools/vo/lines.py builds the
 * list): a conversation's line is its npc, node and variant; a bark is its
 * person, day or night, and place in the list; a line written in the zone
 * code is the hash of its text. The index (data/vo/index.json, written by
 * tools/vo/produce.py) holds, per id, the take's file and the hash of the
 * text it was made from. A take is played only while that hash still
 * matches the text on screen: a line the writer has changed since goes
 * quiet (its subtitle still shows) until it is recorded again. */

/// <summary>One recorded line: where it is, what it was made from, how long it runs.</summary>
public sealed class VoTake
{
    /// <summary>Under art/vo/, e.g. 'rook/dlg.rook.first.0.ogg'.</summary>
    public string File = "";
    /// <summary>VoiceLines.Hash of the text the take was made from.</summary>
    public string Hash = "";
    public string Voice = "";
    public double Sec;
    /// <summary>Where each voice in the line starts and ends, in seconds, and
    /// how far through the text it has got by then (0..1): the words on
    /// screen follow the voice, the narrator's part and then the speaker's.</summary>
    public List<double[]>? Segs;
    /// <summary>'f' or 'm' where the line is one of several takes of the same
    /// words by different passers-by.</summary>
    public string? Sex;
    /// <summary>A stand-in made locally until the final take (recorded by
    /// hand in ElevenLabs, tools/vo/import_takes.py) replaces it.</summary>
    public bool Placeholder;
}

public sealed class VoIndex
{
    public Dictionary<string, VoTake> Lines = new();
}

public static class VoiceLines
{
    /// <summary>The first 12 hex digits of the text's SHA-1 (tools/vo/lines.py text_hash).</summary>
    public static string Hash(string text)
    {
        var h = SHA1.HashData(Encoding.UTF8.GetBytes(text));
        return Convert.ToHexString(h, 0, 6).ToLowerInvariant();
    }

    public static string Dialogue(string npc, string node, int variant) => $"dlg.{npc}.{node}.{variant}";
    public static string Bark(string npc, bool night, int i) => $"bark.{npc}.{(night ? "night" : "day")}.{i}";
    public static string Folk(int i) => $"folk.{i}";
    public static string Guard(int i) => $"guard.{i}";
    /// <summary>A line written in the zone code: its text's hash.</summary>
    public static string Said(string text) => $"say.{Hash(text)}";
    public static string FightBark(string text) => $"cbark.{Hash(text)}";

    static VoIndex? index;
    static Dictionary<string, List<string>>? byText;

    /// <summary>The index, read once (empty when there are no recordings yet).</summary>
    public static VoIndex Index
    {
        get
        {
            if (index != null) return index;
            try { index = Json.Parse<VoIndex>(DataFiles.Text("vo/index.json")); }
            catch (Exception) { index = new VoIndex(); }
            return index;
        }
    }

    /// <summary>For tests and tools: a given index in place of the file.</summary>
    public static void Use(VoIndex i) { index = i; byText = null; }

    /// <summary>The take for this id, if it was made from exactly this text.</summary>
    public static VoTake? Take(string id, string text) =>
        Index.Lines.TryGetValue(id, out var t) && t.Hash == Hash(text) ? t : null;

    /// <summary>Every take of these words (a bark knows only what it says):
    /// the person's own first, then anyone's.</summary>
    public static List<(string Id, VoTake Take)> ByText(string text)
    {
        if (byText == null)
        {
            byText = new();
            foreach (var (id, t) in Index.Lines)
            {
                if (!byText.TryGetValue(t.Hash, out var l)) byText[t.Hash] = l = new();
                l.Add(id);
            }
        }
        return byText.TryGetValue(Hash(text), out var ids) ? ids.Select(i => (i, Index.Lines[i])).ToList() : new();
    }
}
