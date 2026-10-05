using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;

namespace SurvivorUnchained.Content;

/* The credits a player reads, made from public/assets/CREDITS.md: the
 * ledger the provenance audit and the fetch tools keep. Where each file
 * lives, which tool fetched it and what is still under legal review are the
 * team's business. They must not reach the build, where anyone can unpack
 * them, so they are cut here and every other word is kept as written.
 *
 * The game shows data/credits.json. licences/CREDITS.txt ships beside the
 * executable. A test keeps both in step with the ledger, and fails if any
 * link in it goes uncredited. */

/// <summary>The credits as the player reads them.</summary>
public sealed class CreditsBook
{
    public List<string> Intro = new();
    public List<CreditSection> Sections = new();
}

public sealed class CreditSection
{
    public string Title = "";
    /// <summary>Its name in an index: the title without its bracket.</summary>
    public string Short = "";
    /// <summary>The licence everything in it is used under, when it is one ('CC BY 4.0').</summary>
    public string? Licence;
    public string? LicenceLink;
    public List<string> Notes = new();
    public List<CreditGroup> Groups = new();
}

public sealed class CreditGroup
{
    public string? Title;
    /// <summary>A list's own heading inside a group (the Verge's ground under Poly Haven).</summary>
    public bool Sub;
    public List<string> Links = new();
    public List<string> Notes = new();
    public List<CreditEntry> Entries = new();
}

public sealed class CreditEntry
{
    /// <summary>The work's title or the maker's name, set in bold.</summary>
    public string? Name;
    /// <summary>The name is a work's title, quoted in a line of text.</summary>
    public bool Work;
    public string Text = "";
    public List<string> Links = new();
    public List<string> Lines = new();
}

public static class Credits
{
    public const string CcByLink = "https://creativecommons.org/licenses/by/4.0/";

    /// <summary>The licence texts shipped beside the game, each with what it covers.</summary>
    public static readonly (string File, string What)[] Texts =
    {
        ("GODOT_LICENSE.txt", "Godot Engine, under the MIT licence"),
        ("GODOT_COPYRIGHT.txt", "the parts of Godot made by others, and their licences"),
        ("DOTNET_LICENSE.TXT", "the .NET runtime, under the MIT licence"),
        ("DOTNET_THIRD-PARTY-NOTICES.TXT", "the parts of the .NET runtime made by others, and their notices"),
        ("OFL-Cinzel.txt", "the Cinzel typeface, under the SIL Open Font License 1.1"),
        ("OFL-Alegreya.txt", "the Alegreya typeface, under the SIL Open Font License 1.1"),
        ("OFL-AlegreyaSans.txt", "the Alegreya Sans typeface, under the SIL Open Font License 1.1"),
    };

    /* ------------------------------------------------------- the ledger -- */

    abstract record Block;
    sealed record Heading(int Level, string Text) : Block;
    sealed record Para(string Text) : Block;
    sealed record ListBlock(List<Item> Items) : Block;

    sealed class Item
    {
        public string Text = "";
        public readonly List<Item> Children = new();
        public readonly List<string> More = new();
    }

    static readonly Regex Bullet = new(@"^(\s*)[-*] (.*)$");

    /// <summary>The ledger's Markdown as headings, paragraphs and lists (nested by two spaces).</summary>
    static List<Block> Blocks(string md)
    {
        var lines = md.Replace("\r\n", "\n").Split('\n');
        var blocks = new List<Block>();
        static bool Blank(string l) => l.Trim().Length == 0;
        static int Indent(string l) => l.Length - l.TrimStart(' ').Length;
        int i = 0;
        while (i < lines.Length)
        {
            var l = lines[i];
            if (Blank(l)) { i++; continue; }
            if (l.StartsWith('#'))
            {
                int level = l.TakeWhile(c => c == '#').Count();
                blocks.Add(new Heading(level, l[level..].Trim()));
                i++;
                continue;
            }
            if (Bullet.Match(l) is { Success: true } top && top.Groups[1].Length == 0)
            {
                var list = new ListBlock(new List<Item>());
                var stack = new List<Item>();
                bool afterBlank = false, lastWasBullet = false;
                while (i < lines.Length)
                {
                    l = lines[i];
                    if (Blank(l))
                    {
                        // The list goes on only if what comes next is indented under an item.
                        int j = i;
                        while (j < lines.Length && Blank(lines[j])) j++;
                        if (j < lines.Length && Indent(lines[j]) > 0) { afterBlank = true; i = j; continue; }
                        break;
                    }
                    if (Bullet.Match(l) is { Success: true } m)
                    {
                        int depth = m.Groups[1].Length / 2;
                        var it = new Item { Text = m.Groups[2].Value.Trim() };
                        if (depth == 0 || stack.Count == 0) { list.Items.Add(it); stack.Clear(); }
                        else
                        {
                            depth = Math.Min(depth, stack.Count);
                            stack[depth - 1].Children.Add(it);
                            stack.RemoveRange(depth, stack.Count - depth);
                        }
                        stack.Add(it);
                        lastWasBullet = true;
                    }
                    else if (Indent(l) > 0 && stack.Count > 0)
                    {
                        // A paragraph of the item it is indented under, or a wrapped line of one.
                        var owner = stack[Math.Clamp(Indent(l) / 2 - 1, 0, stack.Count - 1)];
                        if (afterBlank || (!lastWasBullet && owner.More.Count == 0)) owner.More.Add(l.Trim());
                        else if (lastWasBullet) stack[^1].Text += " " + l.Trim();
                        else owner.More[^1] += " " + l.Trim();
                        lastWasBullet = false;
                    }
                    else break;
                    afterBlank = false;
                    i++;
                }
                blocks.Add(list);
                continue;
            }
            var sb = new StringBuilder();
            while (i < lines.Length && !Blank(lines[i]) && !lines[i].StartsWith('#') && !(Bullet.Match(lines[i]) is { Success: true } b && b.Groups[1].Length == 0))
            {
                if (sb.Length > 0) sb.Append(' ');
                sb.Append(lines[i].Trim());
                i++;
            }
            blocks.Add(new Para(sb.ToString()));
        }
        return blocks;
    }

    /* --------------------------------------------------------- cleaning -- */

    static readonly Regex Tick = new("`([^`]*)`");
    static readonly Regex Url = new(@"https?://[^\s,;()]+");
    static readonly Regex Review = new(@"under review|\b(?:PE|CR)-\d", RegexOptions.IgnoreCase);
    static readonly string[] DevFiles = { ".glb", ".gltf", ".py", ".mjs", ".js", ".json", ".cs", ".gd", ".png", ".jpg", ".res", ".tres", ".tscn", ".wav", ".ogg", ".bin", ".md" };

    /// <summary>A backticked name that is the workshop's: a path, or a file of code or art.</summary>
    static bool IsRef(string tick) =>
        tick.IndexOfAny(new[] { '/', '\\', '*', '{', '<' }) >= 0 || DevFiles.Any(e => tick.EndsWith(e, StringComparison.OrdinalIgnoreCase));

    static bool HasRef(string s) => Tick.Matches(s).Any(m => IsRef(m.Groups[1].Value));

    /// <summary>Where the sentence that holds this place ends: at a full stop before a capital, or at the end.</summary>
    static int SentenceEnd(string s, int from)
    {
        for (int k = from; k < s.Length - 1; k++)
            if (s[k] == '.' && s[k + 1] == ' ' && k + 2 < s.Length && (char.IsUpper(s[k + 2]) || s[k + 2] is '*' or '"' or '`' or '('))
                return k;
        return s.Length;
    }

    static string Url_(string u) => u.TrimEnd('.', ':');

    static readonly Regex Tacked = new(@"^(?:`|(?:and|in|also|made|as|each|beside|with|by|gathered|stacked|fetched)\b)");

    /// <summary>
    /// A line of the ledger made fit to ship, or null if nothing is left of it.
    /// Where a thing lands ('-> file'), brackets that name the workshop's files
    /// or a review, and sentences that do, are cut; a clause naming a file is
    /// cut back to its comma. With <paramref name="links"/>, the links come
    /// out of the words and are kept there; without, they stay in the prose.
    /// </summary>
    static string? Clean(string s, List<string>? links = null)
    {
        s = s.Trim();
        // Where it landed in the repository.
        for (int a = s.IndexOf(" -> ", StringComparison.Ordinal); a >= 0; a = s.IndexOf(" -> ", StringComparison.Ordinal))
            s = s[..a] + s[SentenceEnd(s, a + 4)..];
        // Brackets: the workshop's go, a review goes, links come out.
        var outp = new StringBuilder();
        for (int k = 0; k < s.Length; k++)
        {
            if (s[k] != '(') { outp.Append(s[k]); continue; }
            int depth = 0, e = k;
            for (; e < s.Length; e++)
            {
                if (s[e] == '(') depth++;
                else if (s[e] == ')' && --depth == 0) break;
            }
            if (e >= s.Length) { outp.Append(s[k]); continue; }
            var inner = s[(k + 1)..e];
            k = e;
            if (HasRef(inner) || Review.IsMatch(inner)) { TrimEnd(outp); continue; }
            if (links != null && Url.IsMatch(inner))
            {
                string? last = null;
                var kept = new List<string>();
                foreach (var part in inner.Split(new[] { ',', ';' }))
                {
                    var p = part.Trim();
                    if (Url.Match(p) is { Success: true } um && um.Index == 0) { links.Add(last = Url_(um.Value)); var rest = p[um.Length..].Trim(); if (rest.Length > 0) kept.Add(rest); }
                    else if (p.StartsWith('/') && last != null && !p.Contains(' ')) links.Add(last = last[..last.LastIndexOf('/')] + p);
                    else if (p.Length > 0) kept.Add(p);
                }
                if (kept.Count == 0) { TrimEnd(outp); continue; }
                outp.Append('(').Append(string.Join("; ", kept)).Append(')');
                continue;
            }
            outp.Append('(').Append(inner).Append(')');
        }
        s = outp.ToString();
        // Sentences: a review goes; one naming the workshop's files is cut back to its last comma, or goes.
        var kept2 = new List<string>();
        foreach (var raw in Regex.Split(s, @"(?<=[.!?])\s+(?=[A-Z*""`(])"))
        {
            var t = raw;
            if (Review.IsMatch(t)) continue;
            while (t.Length > 0 && Tick.Matches(t).FirstOrDefault(m => IsRef(m.Groups[1].Value)) is { } r)
            {
                int cut = Math.Max(t.LastIndexOf(", ", r.Index, StringComparison.Ordinal), t.LastIndexOf("; ", r.Index, StringComparison.Ordinal));
                // Only a clause tacked on the end can go ('..., and their copies in `x`'); one that holds the verb takes the sentence with it.
                if (cut >= 0 && !Tacked.IsMatch(t[(cut + 2)..])) cut = -1;
                char end = t.TrimEnd()[^1];
                t = cut < 0 ? "" : t[..cut] + (end is '.' or ':' or '!' or '?' ? end.ToString() : "");
            }
            if (t.Trim().Length > 0) kept2.Add(t.Trim());
        }
        s = string.Join(" ", kept2);
        s = Tick.Replace(s, "$1");
        if (links != null)
        {
            // Bare links, with the comma, colon or '; see' that led to them.
            s = Regex.Replace(s, @"(?:[,;]\s*see|\s*[,:])?\s*(https?://[^\s,;()]+)", m => { links.Add(Url_(m.Groups[1].Value)); return m.Groups[1].Value.EndsWith('.') ? "." : ""; });
        }
        // (a stop or comma left alone by a cut, never the dot of '.NET')
        s = Regex.Replace(s, @"\s+([.,;:)])(?=\s|$)", "$1");
        s = Regex.Replace(s, @"\(\s+", "(");
        s = Regex.Replace(s, @"[,;]([.:])(?=\s|$)", "$1");
        s = Regex.Replace(s, @"\.{2,}(?=\s|$)", ".");
        s = Regex.Replace(s, @"\s{2,}", " ").Trim();
        if (s.StartsWith('.') || s.StartsWith(',')) s = s[1..].Trim();
        return s.Length == 0 || s == ":" ? null : s;
    }

    static void TrimEnd(StringBuilder sb)
    {
        while (sb.Length > 0 && sb[^1] == ' ') sb.Length--;
    }

    /// <summary>Bold is for a line's lead; inside prose it is only emphasis.</summary>
    static string Prose(string s) => s.Replace("**", "");

    /// <summary>A short label and its list as one line ('Changes: rigged; arms raised; hands refitted.').</summary>
    static string? Fold(string label, IEnumerable<Item> items, List<string>? links = null)
    {
        var parts = items.Select(it => it.Children.Count > 0 ? Fold(Clean(it.Text, links) ?? "", it.Children, links) : Clean(it.Text, links))
            .Where(p => !string.IsNullOrEmpty(p)).Select(p => Prose(p!).TrimEnd(';', '.', ',')).ToList();
        if (parts.Count == 0) return label.Length > 0 ? label : null;
        return $"{Prose(label)} {string.Join("; ", parts)}.".Trim();
    }

    /// <summary>A list short and plain enough to read as one line under its label.</summary>
    static bool Plain(ListBlock l) =>
        l.Items.All(it => it.Children.Count == 0 && it.More.Count == 0 && !Url.IsMatch(it.Text) && !it.Text.StartsWith('"') && !it.Text.Contains(':') && it.Text.Length <= 120);

    static CreditEntry? Entry(Item it)
    {
        var e = new CreditEntry();
        var text = Clean(it.Text, e.Links);
        if (text == null) return null;
        if (text.StartsWith('"') && text.IndexOf('"', 1) is int q and > 0)
        {
            e.Name = text[1..q];
            e.Work = true;
            text = text[(q + 1)..].TrimStart(':', ',', ' ');
        }
        else if (text.StartsWith("**") && text.IndexOf("**", 2, StringComparison.Ordinal) is int b and > 0)
        {
            e.Name = text[2..b].Trim();
            text = text[(b + 2)..].Trim();
            // 'Cinzel: Copyright ...': the colon goes with the name it follows.
            if (text.StartsWith(':')) { e.Name += ":"; text = text[1..].Trim(); }
        }
        text = Prose(text);
        // A change named on the work's own line goes with its other lines.
        string? own = null;
        int c = text.IndexOf(". Changes: ", StringComparison.Ordinal);
        if (c >= 0) { own = text[(c + 2)..]; text = text[..(c + 1)]; }
        if (!text.Contains(". ")) text = text.TrimEnd('.');
        e.Text = text;
        foreach (var ch in it.Children)
        {
            var line = ch.Children.Count > 0 ? Fold(Clean(ch.Text, e.Links) ?? "", ch.Children, e.Links) : Clean(ch.Text, e.Links);
            if (line != null) e.Lines.Add(Prose(line));
        }
        foreach (var m in it.More)
            if (Clean(m, e.Links) is { } line) e.Lines.Add(Prose(line));
        if (own != null) e.Lines.Add(own);
        return e;
    }

    /// <summary>A heading's words, its links taken out.</summary>
    static (string Title, List<string> Links) Title(string h)
    {
        var links = new List<string>();
        return (Prose(Clean(h, links) ?? h), links);
    }

    /* ------------------------------------------------------- the credits -- */

    /// <summary>The ledger (public/assets/CREDITS.md) as the player reads it.</summary>
    public static CreditsBook Parse(string md)
    {
        var book = new CreditsBook();
        var blocks = Blocks(md);
        CreditSection? sec = null;
        CreditGroup? grp = null;
        bool before = true, introDone = false, skip = false;
        var rescued = new List<Item>();

        CreditGroup Group(CreditSection s, string? title, bool sub = false)
        {
            var g = new CreditGroup { Title = title, Sub = sub };
            s.Groups.Add(g);
            return g;
        }

        for (int k = 0; k < blocks.Count; k++)
        {
            switch (blocks[k])
            {
                case Heading { Level: 1 }:
                    break;
                case Heading { Level: 2 } h:
                {
                    before = false;
                    var (title, links) = Title(h.Text);
                    // The web game is not this game; anything a fetch tool appended after it is.
                    skip = title.Contains("web game", StringComparison.OrdinalIgnoreCase);
                    if (skip) break;
                    // A source of public-domain work is a group of the public-domain section.
                    if (title.EndsWith("(CC0)") && sec != null && sec.Title.Contains("CC0"))
                    {
                        grp = Group(sec, title[..^"(CC0)".Length].Trim());
                        grp.Links.AddRange(links);
                        break;
                    }
                    sec = new CreditSection { Title = title, Short = Regex.Replace(title, @"\s*\(.*\)\s*$", "") };
                    if (title.Contains("Creative Commons Attribution 4.0")) { sec.Licence = "CC BY 4.0"; sec.LicenceLink = CcByLink; }
                    book.Sections.Add(sec);
                    grp = null;
                    break;
                }
                case Heading h when sec != null && !skip:
                {
                    var (title, links) = Title(h.Text);
                    grp = Group(sec, title);
                    grp.Links.AddRange(links);
                    break;
                }
                case Para p when before:
                    // The opening words, up to the note for the fetch tools and its list.
                    if (p.Text.TrimEnd().EndsWith(':')) introDone = true;
                    if (!introDone && Clean(p.Text) is { } intro) book.Intro.Add(Prose(intro));
                    break;
                case Para p when sec != null && !skip:
                {
                    if (Clean(p.Text) is not { } text) break;
                    text = Prose(text);
                    if (text.EndsWith(':') && k + 1 < blocks.Count && blocks[k + 1] is ListBlock next)
                    {
                        if (Plain(next))
                        {
                            if (Fold(text, next.Items) is { } note) (grp?.Notes ?? sec.Notes).Add(note);
                            k++;
                            break;
                        }
                        // The heading of the list under it: its first sentence names it, the rest is a note.
                        // A long one that is all one sentence says how the list was made, not what it is.
                        var name = text.TrimEnd(':');
                        int dot = name.IndexOf(". ", StringComparison.Ordinal);
                        if (dot < 0 && name.Length > 60) { (grp?.Notes ?? sec.Notes).Add(text); break; }
                        grp = Group(sec, dot > 0 ? name[..dot] : name, true);
                        if (dot > 0) grp.Notes.Add(name[(dot + 2)..] + ":");
                        break;
                    }
                    (grp?.Notes ?? sec.Notes).Add(text);
                    break;
                }
                case ListBlock l when before:
                    introDone = true;
                    break;
                case ListBlock l when skip:
                    rescued.AddRange(l.Items.Where(it => Url.IsMatch(it.Text)));
                    break;
                case ListBlock l when sec != null:
                {
                    // A second list under the same heading is a group of its own.
                    if (grp == null) grp = Group(sec, null);
                    else if (grp.Entries.Count > 0) grp = Group(sec, null, true);
                    foreach (var it in l.Items)
                        if (Entry(it) is { } e) grp.Entries.Add(e);
                    break;
                }
            }
        }

        // What a fetch tool appended at the end, put where it belongs.
        foreach (var it in rescued)
        {
            CreditSection? home = null;
            string title;
            if (it.Text.Contains("sketchfab.com"))
            {
                bool cc0 = it.Text.Contains("CC0");
                home = book.Sections.FirstOrDefault(s => cc0 ? s.Title.Contains("CC0") : s.Licence == "CC BY 4.0");
                title = "More from Sketchfab";
            }
            else if (it.Text.Contains("polyhaven.com")) { home = book.Sections.FirstOrDefault(s => s.Title.Contains("CC0")); title = "Poly Haven models"; }
            else if (it.Text.Contains("ambientcg.com")) { home = book.Sections.FirstOrDefault(s => s.Title.Contains("CC0")); title = "ambientCG"; }
            else continue;
            if (home == null || Entry(it) is not { } e) continue;
            var g = home.Groups.LastOrDefault(x => x.Title == title) ?? Group(home, title);
            g.Entries.Add(e);
        }
        return book;
    }

    /// <summary>The credits as the game reads them (data/credits.json), its apostrophes left as they are.</summary>
    public static string Json(CreditsBook book) =>
        System.Text.Json.JsonSerializer.Serialize(book, new System.Text.Json.JsonSerializerOptions(Core.Json.Options)
        {
            WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        }) + "\n";

    /* ---------------------------------------------- CREDITS.txt, to ship -- */

    /// <summary>What a group says it changed in every work under it ('Changes for every weapon: ...').</summary>
    static IEnumerable<string> Changes(IEnumerable<string> lines) =>
        lines.Where(l => l.StartsWith("Changes", StringComparison.Ordinal) && l.Contains(':')).Select(l => l[(l.IndexOf(':') + 1)..].Trim());

    /// <summary>The credits as a text file for the licences folder beside the game.</summary>
    public static string Text(CreditsBook book)
    {
        var sb = new StringBuilder();
        void L(string s = "") => sb.Append(s).Append("\r\n");
        string rule = new('=', 72), thin = new('-', 72);
        L("SURVIVOR UNCHAINED");
        L("Credits and licences");
        L();
        foreach (var p in book.Intro) { L(p); L(); }
        L("The licence texts are in this folder:");
        int w = Texts.Max(t => t.File.Length);
        foreach (var (file, what) in Texts) L($"    {file.PadRight(w)}  {what}");
        L();
        foreach (var s in book.Sections)
        {
            L(rule);
            L(s.Title.ToUpperInvariant());
            L(rule);
            L();
            foreach (var n in s.Notes) { L(n); L(); }
            foreach (var g in s.Groups)
            {
                if (g.Title != null && g.Sub) L(g.Title);
                else if (g.Title != null) { L(g.Title); L(thin); }
                foreach (var l in g.Links) L(l);
                if (g.Title != null && !g.Sub) L();
                foreach (var n in g.Notes) { L(n); L(); }
                foreach (var e in g.Entries)
                {
                    var head = e.Name == null ? e.Text : e.Work ? $"\"{e.Name}\" {e.Text}" : $"{e.Name} {e.Text}";
                    L("* " + head.Trim());
                    if (s.Licence != null)
                    {
                        // The form the legal brief asks for: source, creator, licence, and what we changed.
                        var source = e.Links.LastOrDefault();
                        if (source != null) L("    Source: " + source);
                        foreach (var c in e.Links.Take(Math.Max(0, e.Links.Count - 1))) L("    Creator: " + c);
                        L($"    Licence: {s.Licence}, {s.LicenceLink}");
                        var changed = Changes(g.Notes).Concat(Changes(e.Lines)).ToList();
                        if (changed.Count > 0) L("    Modified: " + string.Join(" ", changed.Select((c, i) => i == 0 || c.Length == 0 ? c : char.ToUpperInvariant(c[0]) + c[1..])));
                        foreach (var x in e.Lines.Where(x => !x.StartsWith("Changes", StringComparison.Ordinal))) L("    " + x);
                    }
                    else
                    {
                        foreach (var x in e.Lines) L("    " + x);
                        foreach (var x in e.Links) L("    " + x);
                    }
                }
                L();
            }
        }
        return sb.ToString().TrimEnd() + "\r\n";
    }
}
