using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The credits and licences (docs/legal/LEGAL_BRIEF.md, issue 4), from the
/// title and the pause menu: a page over the blurred world, its index down
/// the left and the reading on the right. The credits are data/credits.json,
/// made from the provenance ledger (Content/Credits.cs). The engine's, the
/// runtime's and the typefaces' licences are read from licences/, which also
/// ships beside the executable. Closing goes back to whatever opened it.
/// </summary>
public partial class CreditsScreen : Overlay
{
    public override string Kind => "credits";
    readonly Action back;

    static CreditsBook? book;
    static CreditsBook Ledger => book ??= Core.Json.Parse<CreditsBook>(DataFiles.Text("credits.json"));

    /// <summary>The index: each section of the credits, then each licence's text.</summary>
    readonly List<(string Name, string? Numeral, string View, int Section)> index = new();
    static readonly string[] Numerals = { "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII" };

    string view = "credits";
    int at;
    ScrollContainer? scroll;
    Control? inner;
    readonly List<Control> heads = new();
    readonly List<(Label Name, ColorRect Mark)> marks = new();

    public CreditsScreen(Game g, Action back) : base(g)
    {
        this.back = back;
        for (int i = 0; i < Ledger.Sections.Count; i++) index.Add((Ledger.Sections[i].Short, Numerals[Math.Min(i, Numerals.Length - 1)], "credits", i));
        index.Add(("Godot Engine", null, "godot", 0));
        index.Add((".NET runtime", null, "dotnet", 0));
        index.Add(("The typefaces", null, "fonts", 0));
    }

    protected override void Build()
    {
        heads.Clear();
        marks.Clear();
        var page = Page("Credits and Licences", "Everyone whose work is in the game, and the licences it is used under", back, "Esc");
        Index(Pane(page, new Rect2(0, 0, 420, 920), null, Style.Gap2));
        var right = Pane(page, new Rect2(450, 0, 1390, 920), Style.Column(0));
        scroll = new ScrollContainer { HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled, SizeFlagsVertical = SizeFlags.ExpandFill, SizeFlagsHorizontal = SizeFlags.ExpandFill };
        var margin = new MarginContainer { MouseFilter = MouseFilterEnum.Pass };
        foreach (var (side, px) in new[] { ("left", 52), ("right", 44), ("top", 34), ("bottom", 64) }) margin.AddThemeConstantOverride("margin_" + side, px);
        margin.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        margin.AddChild(view switch { "godot" => Godot_(), "dotnet" => DotNet(), "fonts" => Fonts(), _ => Reading() });
        scroll.AddChild(margin);
        inner = margin;
        right.AddChild(scroll);
        PageFooter(Footer((Act.SubNext, "Section"), (Act.Down, "Read on"), (Act.Alt, "Open the licences folder"), (Act.Cancel, "Back")));
        Mark();
    }

    /* ------------------------------------------------------- the index -- */

    void Index(VBoxContainer v)
    {
        // The house first: who made it, and what it grew from.
        if (Ledger.Intro.Count > 0) v.AddChild(Style.Label(Ledger.Intro[0], Style.TextItalic, Style.Lead, Style.Ink, true));
        v.AddChild(Style.Gap(Style.Gap3));
        v.AddChild(new Section("The credits"));
        for (int i = 0; i < index.Count; i++)
        {
            if (i > 0 && index[i].View != "credits" && index[i - 1].View == "credits")
            {
                v.AddChild(Style.Gap(Style.Gap3));
                v.AddChild(new Section("The licences"));
            }
            v.AddChild(IndexLine(i));
        }
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        // The texts the licences ask for also lie beside the game.
        var slab = Style.Panel(Style.Slab(16));
        var sv = Style.V(Style.Gap2, Style.Label("Every licence text, and these credits, also lie beside the game in its licences folder.", Style.TextItalic, Style.Small, Style.InkDim, true));
        var open = Style.Button("", OpenFolder, false, true);
        var row = Style.H(Style.Gap2, Style.Prompt(Act.Alt), Style.Label("Open the licences folder", Style.UiBold, Style.Small, Style.GoldHi));
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(10, 5);
        open.AddChild(row);
        open.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X + 22, 36);
        open.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
        sv.AddChild(Nav.Skip(open));
        slab.AddChild(sv);
        v.AddChild(slab);
    }

    Control IndexLine(int i)
    {
        var (name, numeral, _, _) = index[i];
        var b = new Button { Flat = true, FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(0, 34) };
        foreach (var st in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(st, new StyleBoxEmpty());
        var row = Style.H(10);
        row.Position = new Vector2(4, 5);
        var markBox = new Control { CustomMinimumSize = new Vector2(14, 22), MouseFilter = MouseFilterEnum.Ignore };
        var mark = new ColorRect { Color = Style.Ember, Size = new Vector2(8, 8), Position = new Vector2(3, 7), Rotation = Mathf.Pi / 4, PivotOffset = new Vector2(4, 4), MouseFilter = MouseFilterEnum.Ignore };
        markBox.AddChild(mark);
        row.AddChild(markBox);
        var num = Style.Label(numeral ?? "", Style.DisplayLight, 15, Style.GoldDim);
        num.CustomMinimumSize = new Vector2(34, 0);
        row.AddChild(num);
        var label = Style.Label(name, Style.Display, 17, Style.GoldHi);
        row.AddChild(label);
        b.AddChild(row);
        b.MouseEntered += () => { if (i != at) label.AddThemeColorOverride("font_color", Colors.White); };
        b.MouseExited += Mark;
        b.Pressed += () => Go(i);
        marks.Add((label, mark));
        return Nav.Skip(b);
    }

    /// <summary>The index lit where the reading is.</summary>
    void Mark()
    {
        for (int i = 0; i < marks.Count; i++)
        {
            var (label, mark) = marks[i];
            if (!IsInstanceValid(label)) continue;
            label.AddThemeColorOverride("font_color", i == at ? new Color("#fff2d8") : new Color("#cbbd9f"));
            mark.Visible = i == at;
        }
    }

    /// <summary>To an entry of the index: a section of the credits is scrolled to, a licence opened.</summary>
    void Go(int i)
    {
        i = (i + index.Count) % index.Count;
        if (i == at && index[i].View == view && view != "credits") return;
        Sound.Sfx.Page();
        at = i;
        var (_, _, v, section) = index[i];
        if (v != view)
        {
            view = v;
            Refresh();
            if (v == "credits") Callable.From(() => ScrollTo(section, false)).CallDeferred();
            return;
        }
        if (v == "credits") ScrollTo(section, true);
        Mark();
    }

    void ScrollTo(int section, bool glide)
    {
        if (scroll == null || !IsInstanceValid(scroll) || section >= heads.Count) return;
        int y = section == 0 ? 0 : (int)(heads[section].GlobalPosition.Y - inner!.GlobalPosition.Y) - 6;
        following = false;
        if (!glide) { scroll.ScrollVertical = y; following = true; return; }
        var t = CreateTween();
        t.TweenProperty(scroll, "scroll_vertical", y, 0.4).SetTrans(Tween.TransitionType.Cubic).SetEase(Tween.EaseType.Out);
        t.Finished += () => following = true;
    }

    bool following = true;

    public override void _Process(double delta)
    {
        base._Process(delta);
        // Reading on lights the section being read (not while gliding to one chosen).
        if (view != "credits" || !following || scroll == null || !IsInstanceValid(scroll) || inner == null || heads.Count == 0) return;
        float y = scroll.ScrollVertical + 140;
        int now = 0;
        for (int i = 0; i < heads.Count; i++)
            if (heads[i].GlobalPosition.Y - inner.GlobalPosition.Y <= y) now = i;
        // At the foot, the last section is the one being read, however short.
        if (scroll.ScrollVertical >= scroll.GetVScrollBar().MaxValue - scroll.Size.Y - 4) now = heads.Count - 1;
        if (now != at) { at = now; Mark(); }
    }

    public override bool Key(Act a)
    {
        switch (a)
        {
            case Act.Cancel or Act.Pause: back(); return true;
            case Act.SubNext or Act.Right: Go(at + 1); return true;
            case Act.SubPrev or Act.Left: Go(at - 1); return true;
            case Act.Alt: OpenFolder(); return true;
            case Act.Up or Act.Down when scroll != null && IsInstanceValid(scroll):
                Nav.KeyMode = true;
                scroll.ScrollVertical += a == Act.Down ? 120 : -120;
                return true;
        }
        return false;
    }

    /// <summary>The licences folder beside the game (in the project when run from the editor).</summary>
    void OpenFolder()
    {
        string dir = OS.HasFeature("editor") ? ProjectSettings.GlobalizePath("res://licences")
            : System.IO.Path.Combine(System.IO.Path.GetDirectoryName(OS.GetExecutablePath()) ?? "", "licences");
        if (System.IO.Directory.Exists(dir)) OS.ShellOpen(dir);
        else G.Toast(new Toast(ToastKind.Warning, "No licences folder beside the game; every text is on this page."));
    }

    /* ----------------------------------------------------- the credits -- */

    Control Reading()
    {
        var v = Style.V(Style.Gap5);
        foreach (var p in Ledger.Intro.Skip(1)) v.AddChild(Measure(Style.Label(p, Style.TextItalic, Style.Lead, Style.InkDim, true)));
        for (int i = 0; i < Ledger.Sections.Count; i++)
        {
            var s = Ledger.Sections[i];
            var head = Head(Numerals[Math.Min(i, Numerals.Length - 1)], s.Title, s.Licence, s.LicenceLink);
            heads.Add(head);
            v.AddChild(head);
            foreach (var n in s.Notes) v.AddChild(Measure(Prose(n, Style.Body)));
            foreach (var g in s.Groups) v.AddChild(Group(g));
        }
        v.AddChild(Style.Gap(Style.Gap6));
        v.AddChild(Style.Label("Thank you, every one.", Style.TextItalic, Style.Lead, Style.GoldHi, false, HorizontalAlignment.Center));
        return v;
    }

    /// <summary>A section's head: its numeral and name over a rule, its licence at the right.</summary>
    static Control Head(string? numeral, string title, string? licence = null, string? link = null)
    {
        var row = Style.H(Style.Gap4);
        if (numeral != null)
        {
            var n = Style.Label(numeral, Style.DisplayLight, 22, Style.GoldDim);
            n.SizeFlagsVertical = SizeFlags.ShrinkEnd;
            row.AddChild(n);
        }
        var t = Style.Label(title, Style.Display, 30, Style.GoldHi, true);
        t.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        row.AddChild(t);
        if (licence != null)
        {
            // The licence as a seal: its name, a link to its text.
            var seal = Rich();
            seal.FitContent = true;
            seal.AutowrapMode = TextServer.AutowrapMode.Off;
            Link(seal, licence, link ?? "", Style.UiHeavy, 15, Style.EmberHi);
            var frame = Style.Box(new Color(0.25f, 0.12f, 0.05f, 0.55f), Style.Ember with { A = 0.55f }, 1, 3, 0);
            frame.ContentMarginLeft = frame.ContentMarginRight = 12;
            frame.ContentMarginTop = 4;
            frame.ContentMarginBottom = 2;
            var box = Style.Panel(frame, seal);
            box.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(box);
        }
        var v = Style.V(0, Style.Gap(Style.Gap4), row, Style.Rule());
        return v;
    }

    /// <summary>A group: its name, notes and links down a rail at the left, its works beside them.</summary>
    static Control Group(CreditGroup g)
    {
        var row = Style.H(Style.Gap6);
        var rail = Style.V(Style.Gap2);
        rail.CustomMinimumSize = new Vector2(300, 0);
        if (g.Title != null)
            rail.AddChild(g.Sub ? Style.Label(g.Title.ToUpperInvariant(), Style.UiHeavy, 14, Style.Gold, true) : Style.Label(g.Title, Style.Display, 20, Style.GoldHi, true));
        foreach (var n in g.Notes) rail.AddChild(Prose(n, Style.Small, Style.TextItalic, Style.InkDim));
        if (g.Links.Count > 0) rail.AddChild(Links(g.Links));
        row.AddChild(rail);
        var works = Style.V(Style.Gap3);
        works.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (Compact(g, out var names, out var common))
        {
            if (common != null) works.AddChild(Style.Label(common, Style.TextItalic, Style.Small, Style.InkDim, true));
            var r = Rich();
            for (int i = 0; i < names.Count; i++)
            {
                if (i > 0) { r.PushColor(Style.GoldDim); r.AddText("   ·   "); r.Pop(); }
                var e = g.Entries[i];
                if (e.Links.Count > 0) Link(r, names[i], e.Links[^1], Style.Text, Style.Small, Style.Ink);
                else Run(r, names[i], Style.Text, Style.Small, Style.Ink);
            }
            works.AddChild(r);
        }
        else foreach (var e in g.Entries) works.AddChild(Work(e));
        row.AddChild(works);
        return row;
    }

    /// <summary>A long run of short names reads as one paragraph ('Metal038 · Metal048C · ...'),
    /// with what they share said once ('ambientCG, CC0').</summary>
    static bool Compact(CreditGroup g, out List<string> names, out string? common)
    {
        names = new();
        common = null;
        if (g.Entries.Count < 6 || g.Entries.Any(e => e.Lines.Count > 0 || e.Links.Count > 1 || e.Name != null || e.Text.Length > 48)) return false;
        var tails = g.Entries.Select(e => e.Text.Contains(": ") ? e.Text[(e.Text.IndexOf(": ", StringComparison.Ordinal) + 2)..] : null).Distinct().ToList();
        if (tails.Count == 1 && tails[0] != null)
        {
            common = tails[0];
            names = g.Entries.Select(e => e.Text[..e.Text.IndexOf(": ", StringComparison.Ordinal)]).ToList();
        }
        else names = g.Entries.Select(e => e.Text).ToList();
        return true;
    }

    /// <summary>A work: its name in bold and who made it, what was done to it, and where it is.</summary>
    static Control Work(CreditEntry e)
    {
        var v = Style.V(2);
        var head = Rich();
        if (e.Name != null) { Run(head, e.Name, Style.TextBold, Style.Body, Style.GoldHi); head.AddText(" "); }
        Run(head, e.Text, Style.Text, Style.Body, Style.Ink);
        v.AddChild(head);
        foreach (var l in e.Lines)
        {
            var m = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
            m.AddThemeConstantOverride("margin_left", 18);
            m.AddChild(Prose(l, Style.Small, Style.Text, Style.InkDim));
            v.AddChild(m);
        }
        if (e.Links.Count > 0)
        {
            var m = new MarginContainer { MouseFilter = MouseFilterEnum.Pass };
            m.AddThemeConstantOverride("margin_left", 18);
            m.AddChild(Links(e.Links));
            v.AddChild(m);
        }
        return v;
    }

    /* ------------------------------------------------------ the licences -- */

    static string Licence(string file)
    {
        using var f = FileAccess.Open("res://licences/" + file, FileAccess.ModeFlags.Read);
        return f?.GetAsText() ?? "";
    }

    Control Godot_()
    {
        var v = Style.V(Style.Gap4, Head(null, "Godot Engine", "MIT", "https://godotengine.org/license"));
        v.AddChild(Measure(Style.Label("The game is built with the Godot Engine, used under the MIT licence below. Godot is made of many parts by many people; each is listed after it, with its licence. Their licence texts are in GODOT_COPYRIGHT.txt in the licences folder.", Style.TextItalic, Style.Body, Style.InkDim, true)));
        v.AddChild(Measure(LicenceText(Licence("GODOT_LICENSE.txt"))));
        v.AddChild(Head(null, "Its parts, made by others"));
        // Read from the engine itself, so the list is always the build's own.
        var grid = new GridContainer { Columns = 3, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 36);
        grid.AddThemeConstantOverride("v_separation", 18);
        foreach (var c in Engine.GetCopyrightInfo())
        {
            var cell = Style.V(2, Style.Label(c["name"].AsString(), Style.TextBold, Style.Small, Style.GoldHi, true));
            cell.CustomMinimumSize = new Vector2(380, 0);
            foreach (var part in c["parts"].AsGodotArray())
            {
                var d = part.AsGodotDictionary();
                foreach (var line in d["copyright"].AsStringArray().Distinct().Take(4))
                    cell.AddChild(Style.Label("© " + line, Style.Text, Style.Caption, Style.InkDim, true));
                cell.AddChild(Style.Label(d["license"].AsString(), Style.Ui, Style.Badge, Style.InkFaint, true));
            }
            grid.AddChild(cell);
        }
        v.AddChild(grid);
        return v;
    }

    Control DotNet()
    {
        var v = Style.V(Style.Gap4, Head(null, ".NET runtime", "MIT", "https://github.com/dotnet/runtime/blob/main/LICENSE.TXT"));
        v.AddChild(Measure(Style.Label("The game's code runs on the .NET runtime, used under the MIT licence below. Its notices for the parts others made follow it, as .NET ships them.", Style.TextItalic, Style.Body, Style.InkDim, true)));
        v.AddChild(Measure(LicenceText(Licence("DOTNET_LICENSE.TXT"))));
        v.AddChild(Head(null, "Its parts, made by others"));
        v.AddChild(Measure(LicenceText(Licence("DOTNET_THIRD-PARTY-NOTICES.TXT"), Style.Small)));
        return v;
    }

    Control Fonts()
    {
        var v = Style.V(Style.Gap4, Head(null, "The typefaces", "SIL OFL 1.1", "https://openfontlicense.org"));
        v.AddChild(Measure(Style.Label("The game's words are set in Cinzel, Alegreya and Alegreya Sans, each used under the SIL Open Font License, Version 1.1, below.", Style.TextItalic, Style.Body, Style.InkDim, true)));
        foreach (var (file, face) in new[] { ("OFL-Cinzel.txt", "Cinzel"), ("OFL-Alegreya.txt", "Alegreya"), ("OFL-AlegreyaSans.txt", "Alegreya Sans") })
        {
            // The copyright is the file's first line (Alegreya Sans repeats it for every weight; once is enough).
            var first = Licence(file).Split('\n')[0].Trim();
            int close = first.IndexOf(')');
            var r = Rich();
            Run(r, face + "  ", Style.TextBold, Style.Body, Style.GoldHi);
            Run(r, close > 0 ? first[..(close + 1)] : first, Style.Text, Style.Body, Style.Ink);
            v.AddChild(r);
        }
        var text = Licence("OFL-Cinzel.txt");
        int body = text.IndexOf("SIL OPEN FONT LICENSE", StringComparison.Ordinal);
        v.AddChild(Style.Gap(Style.Gap2));
        v.AddChild(Measure(LicenceText(body > 0 ? text[body..] : text)));
        return v;
    }

    /// <summary>A licence's own words, its hard-wrapped lines run together into paragraphs; a line
    /// in capitals, or one underlined, is a heading; rules of dashes are dropped.</summary>
    static RichTextLabel LicenceText(string raw, int size = Style.Body)
    {
        var r = Rich();
        bool first = true;
        foreach (var para in Regex.Split(raw.Replace("\r\n", "\n").Trim(), @"\n\s*\n"))
        {
            var lines = para.Split('\n').Select(l => l.Trim()).ToList();
            bool underlined = lines.Count == 2 && Regex.IsMatch(lines[1], @"^[-=_*]{3,}$");
            lines = lines.Where(l => l.Length > 0 && !Regex.IsMatch(l, @"^[-=_*]{3,}$")).ToList();
            if (lines.Count == 0) continue;
            if (!first) r.Newline();
            first = false;
            var text = string.Join(" ", lines);
            if (underlined || lines.Count == 1 && text.Length < 70 && text == text.ToUpperInvariant() && text.Any(char.IsLetter))
            {
                r.Newline();
                Run(r, text.ToUpperInvariant(), Style.UiHeavy, size - 2, Style.Gold);
            }
            else Run(r, text, Style.Text, size, Style.Ink);
            r.Newline();
        }
        return r;
    }

    /* ---------------------------------------------------------- pieces -- */

    /// <summary>Words that flow: wrapped, fitted to their height, links that open in the browser.</summary>
    static RichTextLabel Rich()
    {
        var r = new RichTextLabel
        {
            FitContent = true, ScrollActive = false, AutowrapMode = TextServer.AutowrapMode.WordSmart, BbcodeEnabled = false,
            SelectionEnabled = false, MouseFilter = MouseFilterEnum.Pass, SizeFlagsHorizontal = SizeFlags.ExpandFill,
        };
        r.AddThemeColorOverride("default_color", Style.Ink);
        r.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.85f));
        r.AddThemeConstantOverride("shadow_offset_y", 1);
        r.AddThemeConstantOverride("shadow_offset_x", 0);
        r.AddThemeConstantOverride("line_separation", 3);
        r.MetaClicked += m => OS.ShellOpen(m.AsString());
        return r;
    }

    static void Run(RichTextLabel r, string text, Font font, int size, Color color)
    {
        r.PushFont(font, size);
        r.PushColor(color);
        r.AddText(text);
        r.Pop();
        r.Pop();
    }

    static void Link(RichTextLabel r, string text, string url, Font font, int size, Color color)
    {
        r.PushMeta(url, RichTextLabel.MetaUnderline.OnHover, url);
        Run(r, text, font, size, color);
        r.Pop();
    }

    /// <summary>Where a work lives, quietly: each link without its 'https://', each one opening.</summary>
    static RichTextLabel Links(IEnumerable<string> links)
    {
        var r = Rich();
        bool first = true;
        foreach (var u in links)
        {
            if (!first) r.AddText("    ");
            first = false;
            Link(r, Regex.Replace(u, @"^https?://(www\.)?", ""), u, Style.Ui, 14, new Color("#8f8470"));
        }
        return r;
    }

    static RichTextLabel Prose(string text, int size, Font? font = null, Color? color = null)
    {
        // The links in a note open too; the words round them read as words.
        var r = Rich();
        int k = 0;
        foreach (Match m in Regex.Matches(text, @"https?://[^\s,;()]+[^\s,;().:]"))
        {
            if (m.Index > k) Run(r, text[k..m.Index], font ?? Style.Text, size, color ?? Style.Ink);
            Link(r, m.Value, m.Value, Style.Ui, size - 2, new Color("#c9b07a"));
            k = m.Index + m.Length;
        }
        if (k < text.Length) Run(r, text[k..], font ?? Style.Text, size, color ?? Style.Ink);
        return r;
    }

    /// <summary>Prose kept to a reading measure, not run across the whole page.</summary>
    static Control Measure(Control c)
    {
        var m = new MarginContainer { MouseFilter = MouseFilterEnum.Pass };
        m.AddThemeConstantOverride("margin_right", 300);
        m.AddChild(c);
        return m;
    }
}
