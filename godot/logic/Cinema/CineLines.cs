using System;
using System.Collections.Generic;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Cinema;

/// <summary>A line a cinematic says: its recording's id, the words as written
/// (what the take was made from) and as shown, who says it (null: the narrator),
/// and whether it is sung (its subtitle is set in italics).</summary>
public sealed record CineLine(string Id, string VoId, string Raw, string Text, string? Speaker, string? SpeakerId, bool Sung = false);

/// <summary>
/// A cinematic's lines, read from the conversation that holds them
/// (dialogue.json; docs/cinematics/README.md section 5): "conversation.node",
/// the variant the survivor gets, and how long it runs: its take, or a
/// slow reading pace when there is no take yet.
/// </summary>
public static class CineLines
{
    public static CineLine Find(string id, Ctx ctx)
    {
        int dot = id.IndexOf('.');
        if (dot < 0) throw new FormatException($"a line id is conversation.node, not {id}");
        string conv = id[..dot], node = id[(dot + 1)..];
        var c = Dialogue.Find(conv) ?? throw new KeyNotFoundException($"no conversation {conv}");
        if (!c.Nodes.TryGetValue(node, out var n)) throw new KeyNotFoundException($"no node {node} in {conv}");
        int i = Math.Max(0, Dialogue.PickIndex(n.Text, ctx));
        string raw = n.Text.Count > 0 ? n.Text[i].Text : "";
        string who = n.Speaker ?? c.Npc;
        string? name = who == "narrator" ? null : Lore.NameOf(who);
        var (shown, sung) = Subtitle(Dialogue.Template(raw, ctx));
        return new CineLine(id, VoiceLines.Dialogue(conv, node, i), raw, shown, name, who, sung);
    }

    /// <summary>The words as the subtitle shows them. A lower-case (parenthesis)
    /// is how the line is said (docs/VOICES.md, as the VO pipeline reads it), so
    /// it is dropped here; a capitalised one, such as a translation, stays. The
    /// text keeps both, because the takes are matched to the words as written.
    /// A direction that says the line is sung sets it in italics.</summary>
    public static (string Text, bool Sung) Subtitle(string text)
    {
        bool sung = false;
        var shown = Direction.Replace(text, m =>
        {
            if (!char.IsLower(m.Groups[1].Value.TrimStart()[0])) return m.Value;
            if (m.Value.Contains("sung", StringComparison.OrdinalIgnoreCase)) sung = true;
            return " ";
        });
        shown = Spaces.Replace(shown, " ").Trim();
        // A direction just before a comma leaves a gap; an ellipsis keeps its own.
        shown = shown.Replace(" ,", ",").Replace(" ?", "?").Replace(" !", "!");
        return (shown, sung);
    }

    static readonly System.Text.RegularExpressions.Regex Direction = new(@"\s*\(\s*([^()\s][^()]*)\)\s*");
    static readonly System.Text.RegularExpressions.Regex Spaces = new(@"[ \t]{2,}");

    /// <summary>How long a line runs, for the cut: its take's voice when there is
    /// one made from these words (Read, without the room's tail, which plays on
    /// over what follows; the whole file for a take made before Read was
    /// measured), else a slow narrator's pace (about 2.6 words a second).</summary>
    public static double Seconds(CineLine l)
    {
        if (l.Raw == "") return 0;
        if (VoiceLines.Take(l.VoId, l.Raw) is { } take) return take.Read > 0 ? take.Read : take.Sec;
        return Reading(l.Text);
    }

    /// <summary>Where a subtitle too wide for one line breaks into two (the script's '/' says so outright
    /// and wins): at the end of a sentence (or a clause: ; :) when both lines fit and the shorter is at
    /// least half the longer, the most balanced such break; else at the word break that makes the longer
    /// line shortest. Never leaves one word alone. Returns the text with a line break, or as it was (it
    /// fits, or it needs more than two lines).</summary>
    public static string Break(string text, Func<string, double> width, double max)
    {
        if (text.Contains('/') || text.Contains('\n') || width(text) <= max) return text;
        string? best = null, bestSentence = null;
        double bestW = double.MaxValue, bestBal = double.MaxValue;
        for (int i = text.IndexOf(' '); i > 0; i = text.IndexOf(' ', i + 1))
        {
            string a = text[..i].TrimEnd(), b = text[(i + 1)..].TrimStart();
            if (a.Length == 0 || b.Length == 0 || !a.Contains(' ') || !b.Contains(' ')) continue;
            double wa = width(a), wb = width(b);
            if (wa > max || wb > max) continue;
            if (Math.Max(wa, wb) < bestW) { bestW = Math.Max(wa, wb); best = a + "\n" + b; }
            string bare = a.TrimEnd('"', '\'', '\u201d', '\u2019', ')');
            if (bare.Length > 0 && ".!?;:\u2026".IndexOf(bare[^1]) >= 0
                && Math.Min(wa, wb) >= 0.5 * Math.Max(wa, wb) && Math.Abs(wa - wb) < bestBal)
            {
                bestBal = Math.Abs(wa - wb);
                bestSentence = a + "\n" + b;
            }
        }
        return bestSentence ?? best ?? text;
    }

    /// <summary>A line too long for two lines under the picture, paged across its take (C13's narrator, 5 Nov: a
    /// 25.7 s line stood as one three-line block for the whole take). Whole sentences are packed into pages of at
    /// most two lines (Break); a sentence too long alone is split at its clauses (, ; : and dashes), then at words.
    /// Each page comes up as the voice reaches its first word: through the take's segments (where in the text the
    /// voice is, by time: VoTake.Segs) less the reveal's 0.25 s lead, else evenly by letters over `voiced` seconds;
    /// the last page runs to `seconds` (the linger). A line that fits two lines, or whose script breaks it ('/'),
    /// is one page as it was. The words never change: the pages joined by spaces are the line.</summary>
    public static List<(string Text, double At)> Pages(string text, Func<string, double> width, double max, double voiced,
        IReadOnlyList<double[]>? segs = null)
    {
        bool Fits(string s) => width(s) <= max || Break(s, width, max).Contains('\n');
        if (text.Contains('/') || text.Contains('\n') || Fits(text)) return [(text, 0)];
        var pieces = new List<string>();
        foreach (var sentence in Split(text, ".!?…"))
            if (Fits(sentence)) pieces.Add(sentence);
            else foreach (var clause in Split(sentence, ",;:—–"))
                if (Fits(clause)) pieces.Add(clause);
                else pieces.AddRange(clause.Split(' ', StringSplitOptions.RemoveEmptyEntries));
        var pages = new List<string>();
        foreach (var piece in pieces)
            if (pages.Count > 0 && Fits(pages[^1] + " " + piece)) pages[^1] += " " + piece;
            else pages.Add(piece);
        var shown = new List<(string, double)>();
        int from = 0;
        double total = Math.Max(1, string.Join(" ", pages).Length);
        foreach (var page in pages)
        {
            double f = from / total, at = voiced * f;
            if (segs is { Count: > 0 })
                foreach (var g in segs)
                    if (f >= g[2] && f <= g[3]) { at = g[0] + (g[1] - g[0]) * (f - g[2]) / Math.Max(1e-6, g[3] - g[2]); break; }
                    else if (f > g[3]) at = g[1];
            shown.Add((page, from == 0 ? 0 : Math.Max(shown[^1].Item2, at - 0.25)));
            from += page.Length + 1;
        }
        return shown;
    }

    /// <summary>The text cut after each of `ends` where a space follows (a closing quote or bracket kept with
    /// it), the pieces trimmed, none empty.</summary>
    static IEnumerable<string> Split(string text, string ends)
    {
        int start = 0;
        for (int i = 0; i < text.Length; i++)
        {
            if (ends.IndexOf(text[i]) < 0) continue;
            int j = i + 1;
            while (j < text.Length && "\"'”’)".IndexOf(text[j]) >= 0) j++;
            if (j < text.Length && text[j] != ' ') continue;
            var piece = text[start..j].Trim();
            if (piece.Length > 0) { yield return piece; start = j; }
        }
        if (text[start..].Trim() is { Length: > 0 } rest) yield return rest;
    }

    public static double Reading(string text)
    {
        int words = text.Split((char[])[' ', '/'], StringSplitOptions.RemoveEmptyEntries).Length;
        return Math.Max(1.2, 0.5 + words / 2.6);
    }

    /// <summary>The survivor a cinematic is played for, from the character.</summary>
    public static CineContext Context(CharacterData ch, IEnumerable<string>? facts = null)
    {
        var c = new CineContext
        {
            Calling = ch.Archetype,
            Background = ch.Background,
            Sex = ch.Sex == Sex.Male ? "male" : "female",
            Hair = ch.HairStyle ?? "braid",
        };
        foreach (var f in facts ?? []) c.Facts.Add(f);
        return c;
    }
}
