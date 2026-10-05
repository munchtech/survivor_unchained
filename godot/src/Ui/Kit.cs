using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The approved layouts' plain kit (docs/design/UI_RESEARCH.md, docs/ui_review/greybox/): one
/// frame per screen, and inside it only tone, spacing, type and thin rules. Every piece asks
/// <see cref="UiArt"/> first by the UI art lead's names (side, panel, well, slot and slot_0..5,
/// rule_h, tab and tab_on, chip, price, button, keycap; nodes/*.png for round pieces), so their
/// art drops in by name and the content margins drawn here hold, so nothing moves when it does.
/// The owner on the old frames: "those borders are just ugly, adding more of them dosn't make
/// them better". Colour here is only rarity, state, or the one primary action.
/// </summary>
public static class Kit
{
    /* Warm dark, in three planes: the ground, a raised panel, a recessed well and tile. */
    public static readonly Color Ground = new("#1b191c"), Panel = new("#252226"), PanelHi = new("#3a363b");
    public static readonly Color Well = new("#161417"), Tile = new("#111012"), TileEdge = new("#070608"), Rule = new("#3a363b");
    /// <summary>The window's edge until UI art's "side" lands: one quiet line, not a border.</summary>
    public static readonly Color Edge = new("#6c6458");
    /// <summary>Words, from loudest to quietest; HeadInk is a section's small capitals.</summary>
    public static readonly Color Ink = new("#ece6da"), Ink2 = new("#c6c0b4"), Dim = new("#8c867c"), Faint = new("#5e5a54"), HeadInk = new("#c9ba94");
    public static readonly Color Glyph = new("#4a474c");

    /// <summary>The window's ground is a little translucent over the world (the owner: "enough
    /// to slightly see through"); the words on it never are.</summary>
    public const float WindowAlpha = 0.94f;

    /* ------------------------------------------------------------ boxes -- */

    static StyleBoxFlat Flat(Color bg, int radius = 3, int padX = 0, int padY = 0)
    {
        var b = new StyleBoxFlat { BgColor = bg, CornerDetail = 4, AntiAliasing = true };
        b.SetCornerRadiusAll(radius);
        b.ContentMarginLeft = b.ContentMarginRight = padX;
        b.ContentMarginTop = b.ContentMarginBottom = padY;
        return b;
    }

    /// <summary>The screen's one frame: the window a side panel or a fitted counter panel is.</summary>
    public static StyleBox Window(int padX = 32, int padTop = 22, int padFoot = 24)
    {
        var b = Flat(Panel with { A = WindowAlpha }, 4);
        b.BorderColor = Edge;
        b.SetBorderWidthAll(1);
        b.BorderWidthTop = 2;
        b.ShadowColor = new Color(0, 0, 0, 0.45f);
        b.ShadowSize = 18;
        b.ContentMarginLeft = b.ContentMarginRight = padX;
        b.ContentMarginTop = padTop;
        b.ContentMarginBottom = padFoot;
        return UiArt.Frame("side", b);
    }

    /// <summary>A raised tonal panel inside a window: a shade lighter, its top edge catching light.</summary>
    public static StyleBox PanelBox(int padX = 14, int padY = 10, Color? tone = null)
    {
        var b = Flat(tone ?? new Color("#2d2a2e"), 3, padX, padY);
        b.BorderColor = PanelHi;
        b.BorderWidthTop = 1;
        return UiArt.Frame("panel", b);
    }

    /// <summary>A recessed area a grid or a list lies in.</summary>
    public static StyleBox WellBox(int pad = 6)
    {
        var b = Flat(Well, 3, pad, pad);
        b.BorderColor = new Color("#0a090b");
        b.BorderWidthTop = 1;
        return UiArt.Frame("well", b);
    }

    /// <summary>A tile: empty, a quiet recess; filled, its tier's colour as tint and edge.</summary>
    public static StyleBox TileBox(ItemInstance? it, bool lit = false)
    {
        if (it == null)
        {
            var e = Flat(Tile, 4);
            e.BorderColor = TileEdge;
            e.BorderWidthTop = 1;
            return UiArt.Frame("slot", e);
        }
        var c = TierColour(it);
        var b = Flat(Tile.Lerp(c, 0.16f) with { A = 1 }, 4);
        b.BorderColor = c.Darkened(lit ? 0 : 0.2f);
        b.SetBorderWidthAll(lit ? 2 : 2);
        return UiArt.Frame($"slot_{Math.Clamp(it.Rarity, 0, 5)}", b);
    }

    /* ------------------------------------------------------------ tiers -- */

    /// <summary>An item's colour on every surface: its band (docs/design/LOOT_DESIGN.md 3). The
    /// one place a tile, a card and a label ask, so the tiers' colours live in one table.</summary>
    public static Color TierColour(ItemInstance it) => Style.RarityOf(it.Rarity);

    /* ------------------------------------------------------------ rules -- */

    /// <summary>A thin rule running on: UI art's rule_h (a tooled line fading at its ends).</summary>
    public static Control RuleH(float minWidth = 0)
    {
        var line = new StyleBoxLine { Color = Rule, Thickness = 1 };
        var p = new Panel { MouseFilter = Control.MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(minWidth, 6), SizeFlagsHorizontal = Control.SizeFlags.ExpandFill, SizeFlagsVertical = Control.SizeFlags.ShrinkCenter };
        p.AddThemeStyleboxOverride("panel", UiArt.Frame("rule_h", line));
        return p;
    }

    /// <summary>A section's head: its name in small capitals, a note, a rule running on to what
    /// sits at its end (a count, Filter and Sort, the purse). No mark before it.</summary>
    public static HBoxContainer Head(string title, string? note = null, params Control[] end)
    {
        var h = Style.H(10);
        var t = Style.Label(title.ToUpperInvariant(), Style.UiHeavy, 14, HeadInk, false, HorizontalAlignment.Left, false);
        t.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
        h.AddChild(t);
        if (note != null)
        {
            var n = Style.Label(note, Style.TextItalic, 15, Dim, false, HorizontalAlignment.Left, false);
            n.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
            h.AddChild(n);
        }
        h.AddChild(RuleH(24));
        foreach (var e in end)
        {
            e.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
            h.AddChild(e);
        }
        return h;
    }

    /// <summary>A section's head over a centred register (a result's page): its name and note
    /// between two rules of a length, as the title sits between its chains, quieter.</summary>
    public static HBoxContainer HeadMid(string title, string? note = null)
    {
        var h = Style.H(14);
        h.AddChild(RuleH(24));
        var t = Style.Label(title.ToUpperInvariant(), Style.UiHeavy, 14, HeadInk, false, HorizontalAlignment.Center, false);
        t.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
        h.AddChild(t);
        if (note != null)
        {
            var n = Style.Label(note, Style.TextItalic, 15, Dim, false, HorizontalAlignment.Left, false);
            n.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
            h.AddChild(n);
        }
        h.AddChild(RuleH(24));
        return h;
    }

    /* ---------------------------------------------------------- widgets -- */

    /// <summary>A quiet action in words (Filter, Sort): no box, lit when the pointer is on it.</summary>
    public static Button Word(string text, Action press, Color? color = null, int size = 15)
    {
        var b = new Button { Text = text, FocusMode = Control.FocusModeEnum.None, MouseDefaultCursorShape = Control.CursorShape.PointingHand, Flat = true };
        Style.Font(b, Style.UiBold, size, color ?? Ink2, false);
        b.AddThemeColorOverride("font_hover_color", Ink);
        b.AddThemeColorOverride("font_pressed_color", Style.Focus);
        foreach (var s in new[] { "normal", "hover", "pressed", "focus", "disabled" })
        {
            var e = new StyleBoxEmpty { ContentMarginLeft = 4, ContentMarginRight = 4, ContentMarginTop = 2, ContentMarginBottom = 2 };
            b.AddThemeStyleboxOverride(s, e);
        }
        b.Pressed += press;
        return b;
    }

    /// <summary>Text tabs: the open one in full ink over an ember underline (tab_on), the rest dim.
    /// count, if given, follows each name ("Pouch · 3").</summary>
    public static HBoxContainer Tabs(string[] names, int on, Action<int> pick, int size = 15, int gap = 22, string[]? counts = null)
    {
        var h = Style.H(gap);
        for (int i = 0; i < names.Length; i++)
        {
            int k = i;
            string text = counts != null && counts[i] != "" ? $"{names[i]} · {counts[i]}" : names[i];
            var b = new Button { Text = text, FocusMode = Control.FocusModeEnum.None, MouseDefaultCursorShape = Control.CursorShape.PointingHand };
            Style.Font(b, Style.UiBold, size, i == on ? Ink : Dim, false);
            b.AddThemeColorOverride("font_hover_color", Ink);
            b.AddThemeColorOverride("font_pressed_color", Ink);
            StyleBox Pad(StyleBox s) { s.ContentMarginLeft = s.ContentMarginRight = 0; s.ContentMarginTop = 2; s.ContentMarginBottom = 8; return s; }
            if (i == on)
            {
                var u = new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = Style.Ember, BorderWidthBottom = 2 };
                foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, Pad(UiArt.Frame("tab_on", u)));
            }
            else
            {
                b.AddThemeStyleboxOverride("normal", Pad(UiArt.Frame("tab", new StyleBoxEmpty())));
                b.AddThemeStyleboxOverride("hover", Pad(UiArt.Frame("tab_hover", new StyleBoxEmpty())));
                b.AddThemeStyleboxOverride("pressed", Pad(UiArt.Frame("tab_pressed", new StyleBoxEmpty())));
                b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
            }
            b.Pressed += () => { if (k != on) { Sound.Sfx.Page(); pick(k); } };
            h.AddChild(b);
        }
        return h;
    }

    /// <summary>A small round control (spend a point, take it back): nodes/round.png and its
    /// states when painted, a drawn ring until then.</summary>
    public static Button Round(string sign, Action press, bool lit = true, int size = 26)
    {
        var b = new Button { Text = sign, FocusMode = Control.FocusModeEnum.None, MouseDefaultCursorShape = Control.CursorShape.PointingHand, CustomMinimumSize = new Vector2(size, size) };
        Style.Font(b, Style.UiHeavy, (int)(size * 0.7f), lit ? new Color("#ffe4be") : Ink2, false);
        StyleBox Disc(Color bg, Color edge, string art)
        {
            if (UiArt.Art($"nodes/{art}.png") is { } t) return new StyleBoxTexture { Texture = t };
            var d = Flat(bg, size / 2);
            d.BorderColor = edge;
            d.SetBorderWidthAll(lit ? 2 : 1);
            return d;
        }
        b.AddThemeStyleboxOverride("normal", Disc(lit ? new Color("#40291a") : new Color("#2e2b30"), lit ? Style.Ember : new Color("#58545a"), lit ? "round_spend" : "round"));
        b.AddThemeStyleboxOverride("hover", Disc(lit ? new Color("#5a3820") : new Color("#3a363c"), lit ? Style.EmberHi : Ink2, "round_hover"));
        b.AddThemeStyleboxOverride("pressed", Disc(lit ? new Color("#6a4224") : new Color("#444046"), Style.EmberHi, "round_hover"));
        b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
        b.Pressed += press;
        return b;
    }

    /// <summary>A pill with a word in it (a trait given for a deed): UI art's chip.</summary>
    public static Control Chip(string text, Color? color = null)
    {
        var p = Style.Panel(UiArt.Frame("chip", Flat(new Color("#34303a"), 13, 11, 4)), Style.Label(text, Style.UiBold, 14, color ?? Ink2, false, HorizontalAlignment.Center, false));
        p.MouseFilter = Control.MouseFilterEnum.Stop;
        return p;
    }

    /// <summary>One of the foot's prompts: the key as a cap, what it does beside it.</summary>
    public static Control Prompt(string cap, string text)
    {
        var h = Style.H(8, Style.Key(cap), Style.Label(text, Style.Ui, 15, Dim, false, HorizontalAlignment.Left, false));
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return h;
    }

    /// <summary>A prompt for an action, as the device in hand has it.</summary>
    public static Control Prompt(Act a, string text)
    {
        var h = Style.H(8, Style.Prompt(a), Style.Label(text, Style.Ui, 15, Dim, false, HorizontalAlignment.Left, false));
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return h;
    }

    /// <summary>The foot's prompts in a centred row.</summary>
    public static HBoxContainer Prompts(params Control[] items)
    {
        var h = Style.H(28, items);
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return h;
    }

    /// <summary>
    /// Words broken into lines of even length, never leaving a word or two alone on the last (a
    /// greedy wrap left Self's "You read the ground and the animals" over a lone "on it."). Of
    /// every way to break the words into the fewest lines that fit `width`, it keeps the one whose
    /// longest line is shortest.
    /// </summary>
    public static string Balance(string text, Font font, int size, float width)
    {
        var words = text.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        float W(int a, int b) => font.GetStringSize(string.Join(' ', words[a..b]), HorizontalAlignment.Left, -1, size).X;
        if (words.Length < 2 || W(0, words.Length) <= width) return text;
        // The fewest lines a greedy wrap needs.
        int lines = 1;
        for (int i = 0, start = 0; i < words.Length; i++)
            if (i > start && W(start, i + 1) > width) { lines++; start = i; }
        // The best breaks for that many lines (few words: a plain search).
        int n = words.Length;
        float best = float.MaxValue;
        int[]? keep = null;
        void Try(int from, int left, List<int> cuts, float worst)
        {
            if (worst >= best) return;
            if (left == 1)
            {
                float w = W(from, n);
                if (w > width) return;
                float m = Math.Max(worst, w);
                if (m < best) { best = m; keep = cuts.ToArray(); }
                return;
            }
            for (int to = from + 1; to <= n - left + 1; to++)
            {
                float w = W(from, to);
                if (w > width) break;
                cuts.Add(to);
                Try(to, left - 1, cuts, Math.Max(worst, w));
                cuts.RemoveAt(cuts.Count - 1);
            }
        }
        Try(0, lines, new List<int>(), 0);
        if (keep == null) return text;
        var o = new System.Text.StringBuilder();
        int at = 0;
        foreach (var cut in keep.Append(n))
        {
            if (o.Length > 0) o.Append('\n');
            o.Append(string.Join(' ', words[at..cut]));
            at = cut;
        }
        return o.ToString();
    }

    /// <summary>A number in a column: right-aligned in the face's tabular figures.</summary>
    public static Label Num(string text, int size = 17, Color? color = null)
    {
        var l = Style.Label(text, Style.UiBold, size, color ?? Ink, false, HorizontalAlignment.Right, false);
        l.AddThemeConstantOverride("outline_size", 0);
        return l;
    }
}

/// <summary>
/// A surface that hugs what it holds and then runs on a little, fading into the world behind it
/// (the owner: "if were taking up a lot of extra space have it fade or taper out"). Its own
/// drawing fades over its last <see cref="Fade"/> pixels (shaders/ui_taper.gdshader); what it
/// holds keeps clear of the fade, so words are never faded.
/// </summary>
public partial class TaperPanel : PanelContainer
{
    static Shader? shader;
    readonly ShaderMaterial mat;
    public readonly float Fade;

    public TaperPanel(StyleBox box, float fade = 110)
    {
        Fade = fade;
        // The run-on is room under what it holds, so the content never reaches the fade.
        box.ContentMarginBottom = box.GetContentMargin(Side.Bottom) + fade;
        AddThemeStyleboxOverride("panel", box);
        shader ??= GD.Load<Shader>("res://shaders/ui_taper.gdshader");
        mat = new ShaderMaterial { Shader = shader };
        mat.SetShaderParameter("fade", fade);
        Material = mat;
        MouseFilter = MouseFilterEnum.Stop;
        Resized += () => mat.SetShaderParameter("foot", Size.Y);
    }
}
