using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>What a callout says, as the drawing needs it: its title and line, its kind, the key
/// that answers it (drawn as the key itself, pad-aware), and the footer's words.</summary>
public sealed record CalloutLook(string Title, string Line, CalloutKind Kind, Act? Key, Act? GoOn, string GoOnWord)
{
    /// <summary>The thing has its own heading (a draft panel, a banner shown again): the title is not said twice.</summary>
    public bool Headed { get; init; }
    /// <summary>The word marked in ember (none: the title's, Subject).</summary>
    public string? Mark { get; init; }
    /// <summary>The marked word's colour as hex (none: ember amber).</summary>
    public string? MarkInk { get; init; }
}

/// <summary>Where a callout points this frame, on the HUD's 1920 by 1080: points (a HUD part, a thing
/// in the world, projected), areas (the cards, a banner), and where its words should stand, if the
/// game says (a draft's tip). Behind this the look can change without the game knowing.</summary>
public sealed record CalloutAim(IReadOnlyList<Vector2> Points, IReadOnlyList<Rect2> Areas, Rect2? Words = null)
{
    /// <summary>Her figure on the canvas (none: not known): the words never stand on her.</summary>
    public Rect2? Her { get; init; }
    /// <summary>Each point's size on the canvas (a HUD part's radius, a thing's in the world); none: a default.</summary>
    public IReadOnlyList<float>? Radii { get; init; }
    /// <summary>How many of the points, from the first, are HUD parts (the rest are in the world: only
    /// those stand in a pool of light; a HUD part is kept undimmed by the HUD itself).</summary>
    public int HudPoints { get; init; }
    /// <summary>What an arrow must not cross: the figures on the screen, the HUD's words.</summary>
    public IReadOnlyList<Rect2>? Avoid { get; init; }
    /// <summary>Things of the callout off the screen: where the screen's edge is nearest them, and which way.</summary>
    public IReadOnlyList<(Vector2 At, Vector2 Dir)>? Edges { get; init; }
    /// <summary>How far an area's brackets stand off it (a slot's +6, a banner's +12).</summary>
    public float AreaGrow { get; init; } = 12;
    /// <summary>The arrow stops at this height, short of the thing (the chain, under the six places).</summary>
    public float? StopY { get; init; }
    /// <summary>The marks in cold blue, not ember: things that glow cold themselves (the Warden's lamps).</summary>
    public bool Cold { get; init; }
    /// <summary>Where the words would rather stand (the canvas's px; none: toward the middle).</summary>
    public Vector2? WordsNear { get; init; }
    /// <summary>Figures the words must not cover (a boss), besides her.</summary>
    public IReadOnlyList<Rect2>? Shun { get; init; }
    /// <summary>Extra pools (x, y, radius px) for the things the lesson names but does not ring: the
    /// caster of a telegraph (the Knight of the red line), so it is not dimmed to a ghost.</summary>
    public IReadOnlyList<Vector3>? Pools { get; init; }
    /// <summary>Discs (x, y, radius) kept wholly undimmed and unblurred, as she is (a caster's body).</summary>
    public IReadOnlyList<Vector3>? Crisp { get; init; }
    /// <summary>Points (by index) that are ringed but never get an arrow (the Knight, beside his lane).</summary>
    public IReadOnlyList<int>? NoArrow { get; init; }
    /// <summary>A point (by index) with no ring: the arrow lands on it bare (the lane under her).</summary>
    public int Bare { get; init; } = -1;
}

/// <summary>The drawing of a callout, as the game drives it (the UI design pass restyles behind it).</summary>
public interface ICalloutView
{
    void Show(CalloutLook look);
    void Aim(CalloutAim aim);
    /// <summary>Taken down: it fades and frees itself.</summary>
    void TakeDown();
    /// <summary>Real seconds since it came up.</summary>
    double Age { get; }
    /// <summary>When its words are whole on the screen (seconds after it comes up).</summary>
    public const double Legible = 0.3;
}

/// <summary>
/// The tutorial's callouts (docs/story/TUTORIAL_COPY.md), in the game's own tip voice (TipLine,
/// WorldType.cs): words set on the world with no box, the title in display type, the line under
/// it, the subject's word in ember, keys drawn as the keys themselves.
///
/// A freeze is the night holding its breath: the world drains to ash and darkens, and the thing
/// being taught stands in a pool of lamplight, its own colour, with a faint warmth at the pool's
/// edge. The words stand on the dark beside it (never on her, never on the thing) and an arrow
/// reaches from them: a forged iron barb with the ember's heat in it, hottest at the point, the
/// heat pulsing down it to the thing, which it rings (a point) or brackets (an area) in the same
/// hot iron. The title burns in hot and cools to bone; the way on shows when it may be taken.
/// An arrow-only callout is the same, lighter and smaller, over the running fight, with no dark.
/// On a panel or a banner (which have their own heading) only the line shows.
/// Everything a callout looks like is in this file.
/// </summary>
public partial class Callout : Control, ICalloutView
{
    const float Canvas = 1920, CanvasH = 1080;
    static readonly Color PaleGlow = new("#dfe6ee");
    static readonly Color Bone = new("#f2e8d4"), LineInk = new("#e8dfcd"), FootInk = new("#cbbd9f"),
        Iron = new(0.055f, 0.04f, 0.035f, 0.94f), Deep = new("#a8380f"), Hot = new("#ff9a40"), White = new("#ffe6a8"),
        Mark = new("#ffa04a"), Warm = new(1f, 0.74f, 0.46f);

    CalloutLook look = null!;
    CalloutAim aim = new([], []);
    double age, gone = -1;
    readonly ColorRect dim;
    readonly ShaderMaterial dimMat;
    /// <summary>The dim's own layer, under the HUD's: the world darkens, the HUD dims itself but for the
    /// part being taught (GameHud.Spotlight).</summary>
    readonly CanvasLayer dimLayer;
    readonly ColorRect smoke;
    readonly ShaderMaterial smokeMat;
    /// <summary>Each arrow's way, chosen each aim (none: no arrow to that mark).</summary>
    readonly List<(Way W, (Vector2 C, float R, Rect2 Box, bool Round) M)> ways = new();
    readonly Dictionary<int, (int Start, int Land, int Bow)> wayWas = new();
    VBoxContainer column = null!;
    Control? title, foot;
    TextureRect burn = null!;
    readonly Ink glow, ink;
    Vector2 wordsAt, placedFor;
    bool placed;

    public double Age => age;

    bool Freeze => look.Kind == CalloutKind.Freeze;
    bool Panel => look.Kind == CalloutKind.Panel;
    bool Headed => look.Headed || Panel;
    /// <summary>How big it all is: a freeze full, an arrow over the running fight lighter.</summary>
    float Scale1 => Freeze ? 1f : Panel ? 0.86f : 0.8f;

    public Callout()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Style.Fill(this);
        dimMat = new ShaderMaterial { Shader = DimShader() };
        dim = new ColorRect { MouseFilter = MouseFilterEnum.Ignore, Material = dimMat, Visible = false, Size = new Vector2(Canvas, CanvasH) };
        dimLayer = new CanvasLayer { Layer = 9 };
        dimLayer.AddChild(dim);
        AddChild(dimLayer);
        smokeMat = new ShaderMaterial { Shader = SmokeShader() };
        smoke = new ColorRect { MouseFilter = MouseFilterEnum.Ignore, Material = smokeMat, Color = Colors.White };
        AddChild(smoke);
        glow = new Ink(this, true) { Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
        ink = new Ink(this, false);
        Style.Fill(glow);
        Style.Fill(ink);
        AddChild(glow);
        AddChild(ink);
        Modulate = Colors.Transparent;
    }

    /// <summary>--dim-diag with --shot: the freeze's dim held off for a frame of the same moment undimmed
    /// (set by GameTeach; the two frames differ by the dim alone).</summary>
    public static bool DimHeld;
    /// <summary>--dim-diag: the flat dim before UI 16 for a frame of the same moment (before/after).</summary>
    public static bool DimOld;
    /// <summary>After dark (set by the game when it shows a freeze): the dim keeps the night's dark readable.</summary>
    public bool Night;

    public void Show(CalloutLook l)
    {
        look = l;
        dim.Visible = Freeze;
        burn = WorldType.Light(new Vector2(620, 190), Style.Ember with { A = 0 });
        AddChild(burn);
        Build();
    }

    void Build()
    {
        float k = Scale1;
        column = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        column.AddThemeConstantOverride("separation", 2);
        if (!Headed)
        {
            var display = new FontVariation { BaseFont = Style.Display };
            display.SetSpacing(TextServer.SpacingType.Glyph, 2);
            var t = WorldType.Lettering(look.Title.ToUpperInvariant(), display, (int)Math.Round(38 * k), Bone);
            t.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            title = t;
            column.AddChild(t);
            column.AddChild(new Wire(t, k) { SizeFlagsHorizontal = SizeFlags.ShrinkCenter });
            column.AddChild(Style.Gap(2 * k));
        }
        foreach (var row in Rows(Spoken(), (int)Math.Round((Panel ? 30 : 25) * k), Panel ? 940 : Freeze ? 560 : 520))
        {
            row.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            column.AddChild(row);
        }
        // A freeze says how to go on, quietly, under the words, once it may be taken.
        if (Freeze && look.GoOn is Act go)
        {
            column.AddChild(Style.Gap(12));
            var f = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center, SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
            f.AddThemeConstantOverride("separation", 10);
            f.AddChild(Controls.Instance is { UsingPad: false } kc ? KeyCap(kc.KeyLabel(go), 1.05f) : Chip(Style.Prompt(go), 1.2f));
            var word = WorldType.Lettering(look.GoOnWord, Style.TextItalic, 20, FootInk);
            word.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            f.AddChild(word);
            f.Modulate = Colors.Transparent;
            foot = f;
            column.AddChild(f);
        }
        column.Modulate = Colors.Transparent;
        AddChild(column);
    }

    public void Aim(CalloutAim a)
    {
        aim = a;
        if (column == null) return;
        // A panel's place for the words is the panel's: they stand on it, wherever it is.
        if (aim.Words is Rect2 w) { wordsAt = w.GetCenter(); placed = true; Route(); return; }
        var p = Primary();
        if (!placed) { wordsAt = Place(); placedFor = p; placed = true; }
        else if (p.DistanceTo(placedFor) > 80) { wordsAt = wordsAt.Lerp(Place(), 0.2f); placedFor = placedFor.Lerp(p, 0.2f); }
        Route();
    }

    public void TakeDown() { if (gone < 0) gone = 0; }

    /* ----------------------------------------------------------- words -- */

    /// <summary>The line as it is said here. On a freeze whose key is drawn in its footer ("Space to
    /// dash"), the line does not say the key again ("Space: a roll" is "A roll").</summary>
    string Spoken()
    {
        string s = look.Line.Trim();
        if (!Freeze || look.GoOn is not Act go || look.Key == null) return s;
        foreach (var lab in Labels(go))
        {
            var e = Regex.Escape(lab);
            var lead = Regex.Match(s, $@"^{e}\s*:\s*");
            if (lead.Success && lead.Length < s.Length) { s = s[lead.Length..]; s = char.ToUpperInvariant(s[0]) + s[1..]; break; }
            var tail = Regex.Match(s, $@"\s*:\s*{e}\s*([.!?])\s*$");
            if (tail.Success) { s = s[..tail.Index] + tail.Groups[1].Value; break; }
        }
        return s;
    }

    /// <summary>What the player is shown for an action: its key, and its pad button.</summary>
    static IEnumerable<string> Labels(Act a)
    {
        var c = Controls.Instance;
        if (c == null) yield break;
        var seen = new HashSet<string>();
        foreach (var l in c.KeyLabels(a).Append(c.PromptLabel(a)))
            if (!string.IsNullOrWhiteSpace(l) && seen.Add(l)) yield return l;
    }

    /// <summary>The keys a line may name (drawn as keys where it does): the actions a tip speaks of.
    /// A lone "A" or "I" is a word, not a key.</summary>
    static List<string> KeyWords()
    {
        var all = new HashSet<string>();
        foreach (var a in new[] { Act.Dash, Act.Flare, Act.Draught, Act.Interact, Act.Inventory, Act.Character, Act.Journal, Act.Map })
            foreach (var l in Labels(a))
                if (l is not ("A" or "I") && (l.Length > 1 || char.IsUpper(l[0]))) all.Add(l);
        return all.OrderByDescending(l => l.Length).ToList();
    }

    /// <summary>The line in rows: a short line on one; a longer one a sentence to a row (a sentence
    /// of two words stays with its neighbour), as the storybook sets it. Keys it names are drawn as
    /// keys; the subject (the title's word) is marked in ember, once.</summary>
    List<Control> Rows(string text, int size, float maxW)
    {
        var font = Style.Text;
        float W(string s) => font.GetStringSize(s, HorizontalAlignment.Left, -1, size).X;
        var keys = KeyWords();
        var rows = new List<string>();
        // (a line set by hand, row by row: kept as written)
        if (text.Contains('\n')) rows.AddRange(text.Split('\n', StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries));
        else if (Panel || W(text) <= 380) rows.Add(text);
        else
        {
            var parts = Regex.Split(text, @"(?<=[.!?])\s+(?=[A-Z])").Where(p => p.Length > 0).ToList();
            foreach (var p in parts)
            {
                bool small = p.Split(' ').Length <= 2;
                if (rows.Count > 0 && (small || rows[^1].Split(' ').Length <= 2) && W(rows[^1] + " " + p) <= maxW) rows[^1] += " " + p;
                else rows.Add(p);
            }
        }
        // A row too wide for the measure breaks into rows of about equal width (never one word left alone).
        rows = rows.SelectMany(r => W(r) <= maxW ? [r] : Balance(r, W, maxW)).ToList();
        string? subject = look.Mark ?? Subject(text, look.Title);
        bool marked = false;
        var list = new List<Control>();
        foreach (var r in rows)
        {
            var box = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
            box.AddThemeConstantOverride("separation", 0);
            foreach (var (seg, isKey) in Split(r, keys))
            {
                if (isKey) { box.AddChild(Pad(Controls.Instance?.UsingPad == true ? Chip(Style.PadButton(seg), 1.15f) : KeyCap(seg, 1.1f), 5)); continue; }
                string bb = seg.Replace("[", "[lb]");
                if (!marked && subject != null && Regex.Match(bb, $@"\b{Regex.Escape(subject)}\b", RegexOptions.IgnoreCase) is { Success: true } m)
                {
                    bb = bb[..m.Index] + $"[color={(look.MarkInk != null ? new Color(look.MarkInk) : Mark).ToHtml(false)}]" + m.Value + "[/color]" + bb[(m.Index + m.Length)..];
                    marked = true;
                }
                box.AddChild(Text(bb, W(seg), size, maxW));
            }
            list.Add(box);
        }
        return list;
    }

    /// <summary>A row cut where it names a key: (words, false) and (key, true) in turn.</summary>
    static IEnumerable<(string, bool)> Split(string row, List<string> keys)
    {
        if (keys.Count == 0) { yield return (row, false); yield break; }
        var rx = new Regex(@"(?<![\w'’-])(" + string.Join("|", keys.Select(Regex.Escape)) + @")(?![\w'’-])");
        int at = 0;
        foreach (Match m in rx.Matches(row))
        {
            // (the space before a key is the chip's margin)
            if (m.Index > at) yield return (row[at..m.Index].TrimEnd(), false);
            yield return (m.Value, true);
            at = m.Index + m.Length;
            while (at < row.Length && row[at] == ' ') at++;
        }
        if (at < row.Length) yield return (row[at..], false);
    }

    /// <summary>The subject's word as the line says it (the title's last word, else its first), or none.</summary>
    static string? Subject(string text, string title)
    {
        var word = title.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        foreach (var w in word.Length > 0 ? new[] { word[^1].TrimEnd('s'), word[0] } : Array.Empty<string>())
        {
            if (w.Length < 3 || w.Equals("the", StringComparison.OrdinalIgnoreCase)) continue;
            var m = Regex.Match(text, $@"\b{Regex.Escape(w)}\w*", RegexOptions.IgnoreCase);
            if (m.Success) return m.Value;
        }
        return null;
    }

    /// <summary>A row in the fewest rows that fit `maxW`, its breaks where the widest row is narrowest.</summary>
    static List<string> Balance(string row, Func<string, float> W, float maxW)
    {
        var words = row.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        int n = words.Length;
        string Join(int a, int b) => string.Join(' ', words[a..b]);
        for (int k = 2; k <= n; k++)
        {
            // (best[i, j]: the narrowest widest row setting the first i words in j rows)
            var best = new float[n + 1, k + 1];
            var cut = new int[n + 1, k + 1];
            for (int i = 0; i <= n; i++) for (int j = 0; j <= k; j++) best[i, j] = float.MaxValue;
            best[0, 0] = 0;
            for (int j = 1; j <= k; j++)
                for (int i = j; i <= n; i++)
                    for (int a = j - 1; a < i; a++)
                    {
                        if (best[a, j - 1] == float.MaxValue) continue;
                        float w = Math.Max(best[a, j - 1], W(Join(a, i)));
                        if (w < best[i, j]) { best[i, j] = w; cut[i, j] = a; }
                    }
            if (best[n, k] > maxW && k < n) continue;
            var list = new List<string>();
            for (int i = n, j = k; j > 0; j--) { int a = cut[i, j]; list.Insert(0, Join(a, i)); i = a; }
            return list;
        }
        return [row];
    }

    /// <summary>A run of the line, outlined on the world like all its type.</summary>
    static RichTextLabel Text(string bbcode, float width, int size, float maxW)
    {
        bool wrap = width > maxW;
        var t = new RichTextLabel
        {
            BbcodeEnabled = true, FitContent = true, ScrollActive = false, MouseFilter = MouseFilterEnum.Ignore,
            AutowrapMode = wrap ? TextServer.AutowrapMode.WordSmart : TextServer.AutowrapMode.Off,
            SizeFlagsVertical = SizeFlags.ShrinkCenter, ClipContents = false,
        };
        t.AddThemeFontOverride("normal_font", Style.Text);
        t.AddThemeFontSizeOverride("normal_font_size", size);
        t.AddThemeColorOverride("default_color", LineInk);
        t.AddThemeColorOverride("font_outline_color", new Color(0.03f, 0.02f, 0.02f, 0.88f));
        t.AddThemeConstantOverride("outline_size", Math.Max(6, size / 4));
        t.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.62f));
        t.AddThemeConstantOverride("shadow_offset_y", 2);
        t.AddThemeConstantOverride("shadow_outline_size", Math.Max(8, size / 3));
        t.Text = wrap ? $"[center]{bbcode}[/center]" : bbcode;
        t.CustomMinimumSize = new Vector2(Mathf.Ceil(Math.Min(width, maxW)) + 4, 0);
        return t;
    }

    /// <summary>A key or button, larger than a footer's (the game stopped for it).</summary>
    static Control Chip(Control c, float k)
    {
        c.CustomMinimumSize *= k;
        foreach (var l in c.FindChildren("*", "Label", true, false).OfType<Label>())
            l.AddThemeFontSizeOverride("font_size", (int)Math.Round(l.GetThemeFontSize("font_size") * k));
        c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        return c;
    }

    /// <summary>A key as a callout draws it, the same for every key it names (Space, R, E): the shared keycap
    /// the tips use too (Style.KeyCap).</summary>
    static Control KeyCap(string text, float k) => Style.KeyCap(text, k);

    static Control Pad(Control c, int side)
    {
        var m = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkCenter };
        m.AddThemeConstantOverride("margin_left", side);
        m.AddThemeConstantOverride("margin_right", side);
        m.AddChild(c);
        return m;
    }

    /// <summary>A wire of hot iron under the title, a coal at its middle: the chain's heat, once.</summary>
    partial class Wire : Control
    {
        readonly Control over;
        readonly float k;
        public Wire(Control over, float k)
        {
            this.over = over;
            this.k = k;
            MouseFilter = MouseFilterEnum.Ignore;
            CustomMinimumSize = new Vector2(over.GetCombinedMinimumSize().X + 56 * k, 10 * k);
        }

        public override void _Draw()
        {
            float w = Size.X, y = Size.Y / 2;
            const int n = 24;
            for (int i = 0; i < n; i++)
            {
                float u0 = i / (float)n, u1 = (i + 1) / (float)n, um = (u0 + u1) / 2;
                float a = Mathf.Pow(Mathf.Sin(um * Mathf.Pi), 0.8f);
                DrawLine(new Vector2(w * u0, y), new Vector2(w * u1, y), Iron with { A = 0.8f * a }, 3.2f * k);
                DrawLine(new Vector2(w * u0, y), new Vector2(w * u1, y), Deep.Lerp(Hot, a) with { A = 0.95f * a }, 1.3f * k);
            }
            var c = new Vector2(w / 2, y);
            float r = 5.2f * k;
            DrawColoredPolygon([c + new Vector2(0, -r - 1.6f), c + new Vector2(r + 1.6f, 0), c + new Vector2(0, r + 1.6f), c + new Vector2(-r - 1.6f, 0)], Iron);
            DrawColoredPolygon([c + new Vector2(0, -r), c + new Vector2(r, 0), c + new Vector2(0, r), c + new Vector2(-r, 0)], Hot);
            DrawColoredPolygon([c + new Vector2(0, -r * 0.45f), c + new Vector2(r * 0.45f, 0), c + new Vector2(0, r * 0.45f), c + new Vector2(-r * 0.45f, 0)], White);
        }
    }

    /* ---------------------------------------------------------- layout -- */

    Vector2 Size2 => column.GetCombinedMinimumSize();

    /// <summary>What the callout marks: each point as a ring of its size, each area as a box.</summary>
    List<(Vector2 C, float R, Rect2 Box, bool Round)> Marks()
    {
        var list = new List<(Vector2, float, Rect2, bool)>();
        for (int i = 0; i < aim.Points.Count && i < 3; i++)
        {
            float r = aim.Radii is { } rr && i < rr.Count ? rr[i] : 30;
            float ring = i == aim.Bare ? 4 : r + 9;
            list.Add((aim.Points[i], ring, new Rect2(aim.Points[i] - Vector2.One * ring, Vector2.One * ring * 2), true));
        }
        if (aim.Points.Count == 0)
            foreach (var a in aim.Areas.Take(1))
            {
                // A whole row of cards is the panel itself: nothing to point at but the words' own place.
                if (Panel && a.Size.X > 760) continue;
                var g = a.Grow(Panel ? 6 : aim.AreaGrow);
                list.Add((g.GetCenter(), 0, g, false));
            }
        return list;
    }

    /// <summary>Whether the mark at i is a thing in the world (it stands in a pool of light).</summary>
    bool InWorld(int i) => i >= aim.HudPoints && i < Math.Min(3, aim.Points.Count);
    /// <summary>Whether a mark rings a part of the HUD: it is drawn pale, not in ember, so it never reads as the
    /// HUD's own "ready" glow (the dash's form, round 2 judge).</summary>
    bool OnHud(Vector2 at)
    {
        for (int i = 0; i < aim.HudPoints && i < aim.Points.Count; i++) if (aim.Points[i] == at) return true;
        return false;
    }

    /// <summary>Whether the mark at this place is the bare one (no ring: the arrow lands on it).</summary>
    bool IsBare(Vector2 at) => aim.Bare >= 0 && aim.Bare < aim.Points.Count && aim.Points[aim.Bare] == at;

    Vector2 Primary() => aim.Points.Count > 0 ? aim.Points[0] : aim.Areas.Count > 0 ? aim.Areas[0].GetCenter() : new Vector2(960, 540);

    /// <summary>Where the words' middle stands: where the game said (a draft's tip), else the best
    /// place on the screen near the things: clear of her, of the things and their marks, of the map,
    /// of the HUD; a good stride from each so the arrows have length to read; toward the middle.</summary>
    Vector2 Place()
    {
        var s = Size2;
        if (aim.Words is Rect2 w) return w.GetCenter();
        var marks = Marks();
        if (marks.Count == 0) return new Vector2(960, 400);
        var keep = new List<Rect2> { new(1520, 0, 400, 480) };
        foreach (var m in marks) keep.Add(m.Box.Grow(26));
        // (and the edge markers, ring and tip, with the same room)
        if (aim.Edges is { } edges)
            foreach (var (eAt, _) in edges) keep.Add(new Rect2(eAt - Vector2.One * EdgeTip, Vector2.One * 2 * EdgeTip).Grow(26));
        // Her figure and her health bar, and a good margin: never words, never an arrow.
        Rect2? her = aim.Her?.Grow(HerMargin);
        if (her is Rect2 h0) keep.Add(h0);
        if (aim.Shun is { } shun) foreach (var r in shun) keep.Add(r.Grow(24));
        var near = aim.WordsNear ?? new Vector2(960, 470);
        var aimed = Aimed(marks);
        float best = float.MaxValue;
        var at = new Vector2(960, 400);
        float hw = s.X / 2 + 14, hh = s.Y / 2 + 10;
        for (float y = 112 + hh; y <= 846 - hh; y += 10)
            for (float x = 56 + hw; x <= Canvas - 56 - hw; x += 12)
            {
                var box = new Rect2(x - hw, y - hh, hw * 2, hh * 2);
                bool clear = true;
                foreach (var k in keep) if (k.Intersects(box)) { clear = false; break; }
                if (!clear) continue;
                float cost = aim.WordsNear != null ? 0.12f * Math.Abs(x - near.X) + 0.12f * Math.Abs(y - near.Y) : 0.1f * Math.Abs(x - 960) + 0.05f * Math.Abs(y - 470);
                for (int i = 0; i < marks.Count; i++)
                {
                    float d = Apart(box, marks[i].Box);
                    cost += (i == 0 ? 1.4f : 0.7f) * Math.Abs(d - 120) + (d < 56 ? 400 : 0);
                }
                // (the test below only adds: a place already no better than the best is passed by)
                if (cost >= best) continue;
                if (her is Rect2 hr)
                    foreach (var i in aimed)
                        if (!ClearWay(new Rect2(x - hw + 14, y - hh + 10, s.X, s.Y), marks[i], hr)) cost += 900;
                if (cost < best) { best = cost; at = new Vector2(x, y); }
            }
        if (OS.GetCmdlineUserArgs().Contains("--teach-diag"))
            GD.Print($"calloutdiag place size={s} her={aim.Her} at={at} best={best} marks={string.Join(";", marks.Select(m => m.Box))}");
        return at;
    }

    /// <summary>How far apart two boxes are (0: they touch).</summary>
    static float Apart(Rect2 a, Rect2 b)
    {
        float dx = Math.Max(0, Math.Max(a.Position.X - b.End.X, b.Position.X - a.End.X));
        float dy = Math.Max(0, Math.Max(a.Position.Y - b.End.Y, b.Position.Y - a.End.Y));
        return Mathf.Sqrt(dx * dx + dy * dy);
    }

    /// <summary>An edge marker's ring (its radius), how far its outer edge reaches with the iron rim, and
    /// how far its tip stands from its middle (px at 1080p): GameTeach pins it to the safe frame by these.</summary>
    public const float EdgeRing = 20, EdgeRim = 23, EdgeTip = 33;

    /// <summary>Her figure's margin: words and arrows keep this far off it.</summary>
    const float HerMargin = 48;
    /// <summary>How far outside the words an arrow starts.</summary>
    const float Out = 16;

    /// <summary>Which marks get an arrow: each HUD part and area, and of the things in the world only the
    /// one nearest the words (three lamps: three rings, one arrow).</summary>
    List<int> Aimed(List<(Vector2 C, float R, Rect2 Box, bool Round)> marks)
    {
        var list = new List<int>();
        int nearest = -1;
        float nd = float.MaxValue;
        for (int i = 0; i < marks.Count; i++)
        {
            if (!InWorld(i)) { list.Add(i); continue; }
            if (aim.NoArrow?.Contains(i) == true) continue;
            float d = marks[i].C.DistanceTo(wordsAt);
            if (d < nd) { nd = d; nearest = i; }
        }
        if (nearest >= 0) list.Add(nearest);
        return list;
    }

    /// <summary>An arrow's way: where it leaves the words and which way, where it lands and which way,
    /// and how it bows (added to both its handles).</summary>
    public readonly record struct Way(Vector2 A, Vector2 DA, Vector2 B, Vector2 DB, Vector2 Bow)
    {
        public List<Vector2> Path(float t, int steps)
        {
            float bend = Bend(A, B);
            return Ink.Bezier(A, A + DA * bend + Bow, B - DB * bend + Bow, B, t, steps);
        }

        /// <summary>Path's points into buf (steps + 1 long), none allocated; how many (0: too short).</summary>
        public int PathInto(Span<Vector2> buf, float t, int steps)
        {
            float bend = Bend(A, B);
            return Ink.BezierInto(buf, A, A + DA * bend + Bow, B - DB * bend + Bow, B, t, steps);
        }
    }

    /// <summary>Where an arrow may leave the words: 16 px out of their foot or head (under or over the
    /// thing), out of a corner, or, last, out of a side (inline with the words: it reads as a bullet).</summary>
    static List<(Vector2 P, Vector2 D, float Cost)> Starts(Rect2 box, Vector2 toward, List<(Vector2 P, Vector2 D, float Cost)> list)
    {
        list.Clear();
        var c = box.GetCenter();
        float inset = Math.Min(28, box.Size.X * 0.2f);
        float x = Mathf.Clamp(toward.X, box.Position.X + inset, box.End.X - inset);
        var o = box.Grow(Out);
        list.Add((new Vector2(x, o.End.Y), Vector2.Down, 0)); list.Add((new Vector2(x, o.Position.Y), Vector2.Up, 0));
        list.Add((new Vector2(o.Position.X, c.Y), Vector2.Left, 220)); list.Add((new Vector2(o.End.X, c.Y), Vector2.Right, 220));
        foreach (var (cx, cy) in Corners)
        {
            var d = new Vector2(cx * 0.6f, cy * 0.8f);
            var corner = new Vector2(cx < 0 ? box.Position.X : box.End.X, cy < 0 ? box.Position.Y : box.End.Y);
            list.Add((corner + d * Out, d, 40));
        }
        return list;
    }

    /// <summary>Where an arrow may land on a mark, from a, and which way: on a ring's near edge (or short of
    /// it, StopY); on an area's near edges, at their middle or toward a corner (a bracket).</summary>
    static readonly (int, int)[] Corners = { (-1, -1), (1, -1), (1, 1), (-1, 1) };
    static readonly (float, float)[] Along = { (0.5f, 0f), (0.15f, 50f), (0.85f, 50f) };
    // (BestWay's lists, kept: it runs thousands of times as a callout is placed, never inside itself)
    readonly List<(Vector2 P, Vector2 D, float Cost)> startsBuf = new(8);
    readonly List<(Vector2 B, Vector2 DB, float Cost)> landsBuf = new(8);

    List<(Vector2 B, Vector2 DB, float Cost)> Lands((Vector2 C, float R, Rect2 Box, bool Round) m, Vector2 a, List<(Vector2 B, Vector2 DB, float Cost)> list)
    {
        list.Clear();
        if (m.Round)
        {
            if (aim.StopY is float sy && a.Y < sy) { list.Add((new Vector2(m.C.X, sy), Vector2.Down, 0)); return list; }
            var db = (m.C - a).Normalized();
            list.Add((m.C - db * (m.R + 5), db, 0));
            return list;
        }
        var r = m.Box.Grow(4);
        // (a card's leaves stand over its frame: the point stops clear of them)
        float lift = Panel ? 13 : 0;
        foreach (var (f, cost) in Along)
        {
            float x = Mathf.Lerp(r.Position.X, r.End.X, f);
            if (a.Y < r.Position.Y) list.Add((new Vector2(x, r.Position.Y - lift), Vector2.Down, cost));
            if (a.Y > r.End.Y) list.Add((new Vector2(x, r.End.Y), Vector2.Up, cost));
        }
        float y = Mathf.Clamp(a.Y, r.Position.Y + 12, r.End.Y - 12);
        if (a.X < r.Position.X) list.Add((new Vector2(r.Position.X, y), Vector2.Right, 120));
        if (a.X > r.End.X) list.Add((new Vector2(r.End.X, y), Vector2.Left, 120));
        return list;
    }

    /// <summary>What a way costs: its length, a start turned from its thing, a bow, and above all what it
    /// crosses (her, the figures, the HUD's words, the words themselves, the screen's edge). Near the
    /// thing it lands on, nothing counts (an ember at her feet is still pointed at).</summary>
    float Cost(Way w, (Vector2 C, float R, Rect2 Box, bool Round) m, Rect2 words, Rect2? her, IReadOnlyList<Rect2>? avoid, int samples)
    {
        Span<Vector2> pts = stackalloc Vector2[samples + 1];
        int n = w.PathInto(pts, 1, samples);
        if (n < 2) return float.MaxValue;
        float len = 0;
        for (int i = 1; i < n; i++) len += pts[i].DistanceTo(pts[i - 1]);
        float cost = len + w.Bow.Length() * 0.6f;
        var to = (w.B - w.A).Normalized();
        if (w.DA.Dot(to) < -0.1f) cost += 500;
        // (a hook: it leaves one way and comes back the other to land; it reads as lost, not pointing)
        if (w.DA.Normalized().Dot(w.DB.Normalized()) < -0.3f) cost += 900;
        var near = m.Round ? new Rect2(m.C - Vector2.One * (m.R + 26), Vector2.One * (m.R + 26) * 2) : m.Box.Grow(26);
        var wordsIn = words.Grow(6);
        // Her figure itself is never crossed; her margin is kept where a way can, but a short, straight
        // way into a mark she stands at may graze it rather than hook round.
        Rect2? core = her?.Grow(12 - HerMargin);
        bool herHit = false, marginHit = false, wordsHit = false, edgeHit = false;
        Span<bool> hits = avoid != null ? stackalloc bool[avoid.Count] : default;
        for (int i = 1; i < n; i++)
        {
            var q = pts[i];
            if (near.HasPoint(q)) continue;
            if (her is Rect2 h && h.HasPoint(q)) { if (core is Rect2 hc && hc.HasPoint(q)) herHit = true; else marginHit = true; }
            if (i > 1 && wordsIn.HasPoint(q)) wordsHit = true;
            if (q.X < 16 || q.X > Canvas - 16 || q.Y < 16 || q.Y > CanvasH - 16) edgeHit = true;
            if (avoid != null) for (int k = 0; k < avoid.Count; k++) if (!hits[k] && avoid[k].HasPoint(q)) hits[k] = true;
        }
        if (herHit) cost += 4000;
        else if (marginHit) cost += 700;
        if (wordsHit) cost += 2500;
        if (edgeHit) cost += 2000;
        foreach (var hb in hits) if (hb) cost += 700;
        return cost;
    }

    /// <summary>The best way from the words to a mark: every start, every landing, five bows.</summary>
    (Way W, int Start, int Land, int Bow, float Cost) BestWay(Rect2 words, (Vector2 C, float R, Rect2 Box, bool Round) m, Rect2? her,
        IReadOnlyList<Rect2>? avoid, (int, int, int)? was, bool bowed = true, int samples = 24)
    {
        (Way, int, int, int, float) best = (default, -1, -1, -1, float.MaxValue);
        var starts = Starts(words, m.C, startsBuf);
        float[] bows = bowed ? [0, 0.22f, -0.22f, 0.42f, -0.42f] : [0];
        for (int si = 0; si < starts.Count; si++)
        {
            var (a, da, sc) = starts[si];
            var lands = Lands(m, a, landsBuf);
            for (int li = 0; li < lands.Count; li++)
            {
                var (b, db, lc) = lands[li];
                if (a.DistanceTo(b) < 24) continue;
                var nrm = (b - a).Normalized().Orthogonal();
                float len = a.DistanceTo(b);
                for (int bi = 0; bi < bows.Length; bi++)
                {
                    var w = new Way(a, da, b, db, nrm * bows[bi] * len);
                    float c = Cost(w, m, words, her, avoid, samples) + sc + lc;
                    // (what was chosen holds unless another is clearly better: no flicker as things move)
                    if (was is (int ws, int wl, int wb) && ws == si && wl == li && wb == bi) c -= 90;
                    if (c < best.Item5) best = (w, si, li, bi, c);
                }
            }
        }
        return best;
    }

    /// <summary>Whether the words at box have a way to a mark that keeps off her (the placing's test: no bows, few samples).</summary>
    /// (BestWay's loop, no bows, stopped at the first way under the bar: the same answer as its best's)
    bool ClearWay(Rect2 box, (Vector2 C, float R, Rect2 Box, bool Round) m, Rect2 her)
    {
        var starts = Starts(box, m.C, startsBuf);
        for (int si = 0; si < starts.Count; si++)
        {
            var (a, da, sc) = starts[si];
            var lands = Lands(m, a, landsBuf);
            for (int li = 0; li < lands.Count; li++)
            {
                var (b, db, lc) = lands[li];
                if (a.DistanceTo(b) < 24) continue;
                var nrm = (b - a).Normalized().Orthogonal();
                float len = a.DistanceTo(b);
                var w = new Way(a, da, b, db, nrm * 0f * len);
                if (Cost(w, m, box, her, null, 12) + sc + lc < 2500) return true;
            }
        }
        return false;
    }

    /// <summary>How far an arrow's ends hold their way before it bends.</summary>
    static float Bend(Vector2 a, Vector2 b) => Math.Min(0.5f * a.DistanceTo(b), 160);

    Rect2 Words => new(wordsAt - Size2 / 2, Size2);

    /// <summary>Each arrow: its way, and the mark it lands on (chosen in Aim).</summary>
    IEnumerable<(Way W, (Vector2 C, float R, Rect2 Box, bool Round) M)> Arrows() => ways;

    /// <summary>The arrows' ways for where the words and the things are now.</summary>
    void Route()
    {
        ways.Clear();
        if (column == null) return;
        var marks = Marks();
        var words = Words;
        Rect2? her = aim.Her?.Grow(HerMargin);
        foreach (var i in Aimed(marks))
        {
            var m = marks[i];
            var best = BestWay(words, m, her, aim.Avoid, wayWas.TryGetValue(i, out var w) ? w : null);
            if (best.Start < 0) continue;
            wayWas[i] = (best.Start, best.Land, best.Bow);
            ways.Add((best.W, m));
        }
    }

    /* ----------------------------------------------------------- frame -- */

    static float Smooth(double x) { float k = (float)Math.Clamp(x, 0, 1); return k * k * (3 - 2 * k); }

    public override void _Process(double delta)
    {
        if (look == null || column == null) return;
        age += delta;
        // (a freeze's card goes in 0.12 s: the world is moving again under it, and a slower fade left its
        // words ghosting over the walls while the strike it warned of played out)
        double outT = Freeze ? 0.12 : 0.3;
        if (gone >= 0) { gone += delta; if (gone > outT) { QueueFree(); return; } }
        var s = Size2;
        column.Size = s;
        column.Position = wordsAt - s / 2;
        // It burns in: the glow first, the words up through it by Legible, the title hot and cooling to bone.
        float out_ = gone >= 0 ? 1 - Smooth((float)(gone / outT)) : 1;
        Modulate = Colors.White with { A = out_ };
        column.Modulate = Colors.White with { A = Smooth(age / ICalloutView.Legible) };
        if (title != null) title.Modulate = Warm.Lerp(Colors.White, Smooth((age - 0.1) / 0.6));
        // The way on shows once it may be taken (Teacher.MinHold), and breathes while it waits.
        if (foot != null) foot.Modulate = Colors.White with { A = Smooth((age - Teacher.MinHold) / 0.18) * (0.86f + 0.14f * Mathf.Cos((float)(age - Teacher.MinHold) * 2.6f)) };
        burn.Size = new Vector2(s.X + 260, s.Y + 120);
        burn.Position = wordsAt - burn.Size / 2;
        burn.Modulate = Style.Ember with { A = 0.3f * (float)Math.Max(0, 1 - Math.Abs(age - 0.16) / 0.55) + (Headed ? 0 : 0.035f) };
        // A soft dark under the words, so they read over a lit ground (none on a panel: it has its own
        // dark): over the running fight 45% at its heart, fading out over 140 px; lighter on a freeze.
        if (!Panel)
        {
            float fade = Freeze ? 110 : 140;
            smoke.Size = s + Vector2.One * fade * 2;
            smoke.Position = wordsAt - smoke.Size / 2;
            smokeMat.SetShaderParameter("size", smoke.Size);
            smokeMat.SetShaderParameter("fade", fade);
            smokeMat.SetShaderParameter("alpha", (Freeze ? 0.32f : 0.55f) * Smooth(age / 0.25));
        }
        else smoke.Visible = false;
        // The world drains, darkens and softens, but for a soft round pool on each thing in the world
        // (its own colour, no more light than it had); a HUD part has no pool (the HUD keeps it undimmed).
        if (Freeze) dim.Visible = !DimHeld;
        if (Freeze) { dimMat.SetShaderParameter("old_dim", DimOld ? 1 : 0); dimMat.SetShaderParameter("night", Night ? 1f : 0f); }
        if (dim.Visible)
        {
            var lights = new Vector4[6];
            int n = 0;
            // (she keeps her own light: a soft pool about one and a half times her height)
            // (1.4 times that, its fall over the whole radius: no edge, never a disc of the night's own colour)
            if (aim.Her is Rect2 hr) lights[n++] = new Vector4(hr.GetCenter().X, hr.GetCenter().Y, hr.Size.Y * 0.8f * 1.4f * 1.25f, 0);
            dimMat.SetShaderParameter("soft_first", aim.Her is Rect2 ? 1 : 0);
            var marks = Marks();
            for (int i = 0; i < marks.Count && n < 6; i++)
            {
                if (!InWorld(i)) continue;
                var m = marks[i];
                lights[n++] = new Vector4(m.C.X, m.C.Y, i == aim.Bare ? 90 : m.R * 1.5f + 46, 0.7f);
            }
            if (aim.Pools != null)
                foreach (var pl in aim.Pools)
                    if (n < 6) lights[n++] = new Vector4(pl.X, pl.Y, pl.Z, 0.7f);
            var crisp = new Vector4[4];
            int cn = 0;
            if (aim.Crisp != null)
                foreach (var cr in aim.Crisp)
                    if (cn < 4) crisp[cn++] = new Vector4(cr.X, cr.Y, cr.Z, 0);
            dimMat.SetShaderParameter("crisp", crisp);
            dimMat.SetShaderParameter("crisp_n", cn);
            dimMat.SetShaderParameter("lights", lights);
            dimMat.SetShaderParameter("count", n);
            dimMat.SetShaderParameter("canvas", new Vector2(Canvas, CanvasH));
            dimMat.SetShaderParameter("amount", Smooth(age / 0.26) * out_);
            if (OS.GetCmdlineUserArgs().Contains("--dim-diag") && age > 0.6 && age < 1.3)
                GD.Print($"dimdiag age={age:0.00} words={new Rect2(wordsAt - Size2 / 2, Size2)} lights={string.Join(";", lights.Take(n).Select(l => $"{l.X:0},{l.Y:0},{l.Z:0}"))}");
        }
        glow.QueueRedraw();
        ink.QueueRedraw();
    }

    /// <summary>How much of each arrow is drawn: it shoots out from the words between 0.1 s and 0.4 s.</summary>
    float Reach => (float)Math.Clamp((age - 0.1) / 0.3, 0, 1);
    /// <summary>The moment the arrows land: their marks strike, flaring and settling.</summary>
    const double Land = 0.4;

    /// <summary>The arrows' layer: the glow (added light) or the iron and its heat.</summary>
    partial class Ink : Control
    {
        readonly Callout c;
        // (a cold callout's ink: the lamps glow ice blue, so their marks do too, round 2 judge)
        static readonly Color ColdDeep = new("#1f4f86"), ColdHot = new("#7cc4ff"), ColdWhite = new("#e4f4ff");
        Color Deep => c.aim.Cold ? ColdDeep : Callout.Deep;
        Color Hot => c.aim.Cold ? ColdHot : Callout.Hot;
        Color White => c.aim.Cold ? ColdWhite : Callout.White;
        Color Ember => c.aim.Cold ? ColdHot : Style.Ember;
        readonly bool glow;
        public Ink(Callout c, bool glow) { this.c = c; this.glow = glow; MouseFilter = MouseFilterEnum.Ignore; }

        public override void _Draw()
        {
            if (c.look == null || c.column == null) return;
            float reach = c.Reach;
            if (reach <= 0) return;
            float r = 1 - (1 - reach) * (1 - reach) * (1 - reach);
            float k = c.Scale1;
            double since = c.age - Land;
            float strike = since < 0 ? 0 : (float)Math.Max(0, 1 - since / 0.28);
            float breathe = 0.5f + 0.5f * Mathf.Sin((float)c.age * 3.4f);
            // Every thing is marked; the arrows go to those Aimed (of things in the world, the nearest).
            if (reach >= 1)
            {
                var marks = c.Marks();
                for (int i = 0; i < marks.Count; i++)
                    if (i != c.aim.Bare && !c.ways.Any(x => x.M.C == marks[i].C)) Mark(marks[i], k, strike, breathe, glow, c.OnHud(marks[i].C));
            }
            if (c.aim.Edges is { } edges) foreach (var (at, d) in edges) Chevron(at, d, k, breathe, reach, glow);
            foreach (var (way, m) in c.Arrows())
            {
                var (a, da, b, _, _) = way;
                float len = a.DistanceTo(b);
                var pts = way.Path(r, Math.Max(10, (int)(len / 9)));
                if (pts.Count < 2) continue;
                var tip = pts[^1];
                var dir = (pts[^1] - pts[^2]).Normalized();
                // The heat that runs down it to the thing, every second and a half once it has landed.
                float bead = since < 0 ? -1 : (float)(since % 1.5 / 1.1);
                if (glow)
                {
                    // A soft light along it, warmest at the point, and a bloom where the point is.
                    Soft(pts, 30 * k, 40 * k, u =>
                    {
                        float hb = bead is >= 0 and <= 1 ? Mathf.Exp(-Mathf.Pow((u - bead) / 0.08f, 2)) : 0;
                        return Ember with { A = 0.12f + 0.2f * u + 0.22f * hb };
                    }, r);
                    float bloom = (64 + 14 * strike) * k;
                    DrawTextureRect(Bloom(), new Rect2(tip - Vector2.One * bloom / 2, Vector2.One * bloom), false, Ember with { A = 0.42f + 0.3f * strike });
                    if (reach >= 1 && !c.IsBare(m.C)) Mark(m, k, strike, breathe, true, c.OnHud(m.C));
                    continue;
                }
                // The iron, then the heat inside it, cooler at the words, hottest at the point.
                Stroke(pts, 12.5f * k, 8f * k, _ => Iron, r);
                Stroke(pts, 5.4f * k, 3.4f * k, u =>
                {
                    var col = u < 0.7f ? Deep.Lerp(Hot, u / 0.7f) : Hot.Lerp(White, (u - 0.7f) / 0.3f);
                    float hb = bead is >= 0 and <= 1 ? Mathf.Exp(-Mathf.Pow((u - bead) / 0.07f, 2)) : 0;
                    return col.Lerp(White, 0.75f * hb);
                }, r);
                // Where it leaves the words: a link of the chain.
                Link(pts[0], da, k);
                float drawn = (tip - pts[0]).Length();
                if (drawn > 14) Head(tip, dir, k * Mathf.Clamp(drawn / 80f, 0.45f, 1f));
                if (reach >= 1 && !c.IsBare(m.C)) Mark(m, k, strike, breathe, false, c.OnHud(m.C));
            }
        }

        /// <summary>A cubic from a to b, drawn as far as t.</summary>
        public static List<Vector2> Bezier(Vector2 p0, Vector2 p1, Vector2 p2, Vector2 p3, float t, int steps)
        {
            var list = new List<Vector2>(steps + 1);
            if (p0.DistanceTo(p3) < 8 || t <= 0) return list;
            for (int i = 0; i <= steps; i++)
            {
                float s = t * i / steps, v = 1 - s;
                list.Add(v * v * v * p0 + 3 * v * v * s * p1 + 3 * v * s * s * p2 + s * s * s * p3);
            }
            return list;
        }

        /// <summary>Bezier's points into buf (steps + 1 long), the same sums, nothing allocated (the
        /// placing tries thousands of ways a callout: s6, 350 ms of lists); how many were written.</summary>
        public static int BezierInto(Span<Vector2> buf, Vector2 p0, Vector2 p1, Vector2 p2, Vector2 p3, float t, int steps)
        {
            if (p0.DistanceTo(p3) < 8 || t <= 0) return 0;
            for (int i = 0; i <= steps; i++)
            {
                float s = t * i / steps, v = 1 - s;
                buf[i] = v * v * v * p0 + 3 * v * v * s * p1 + 3 * v * s * s * p2 + s * s * s * p3;
            }
            return steps + 1;
        }

        /// <summary>A stroke along the points, w0 wide at the start, w1 at the end (u runs 0 to r
        /// along it): a strip of triangles, each drawn as it is (a polygon is triangulated, and one
        /// squeezed thin by the arrow's first frames fails to; a triangle never does).</summary>
        void Stroke(List<Vector2> raw, float w0, float w1, Func<float, Color> col, float r)
        {
            var pts = new List<Vector2>(raw.Count);
            foreach (var q in raw) if (pts.Count == 0 || pts[^1].DistanceSquaredTo(q) > 0.1f) pts.Add(q);
            int n = pts.Count;
            if (n < 2) return;
            var left = new Vector2[n];
            var right = new Vector2[n];
            var cols = new Color[n];
            for (int i = 0; i < n; i++)
            {
                var dir = (pts[Math.Min(n - 1, i + 1)] - pts[Math.Max(0, i - 1)]).Normalized();
                var nrm = new Vector2(-dir.Y, dir.X);
                float u = i / (float)(n - 1) * r;
                float w = Mathf.Lerp(w0, w1, u) / 2;
                left[i] = pts[i] + nrm * w;
                right[i] = pts[i] - nrm * w;
                cols[i] = col(u);
            }
            for (int i = 1; i < n; i++)
            {
                DrawPrimitive([left[i - 1], left[i], right[i]], [cols[i - 1], cols[i], cols[i]], []);
                DrawPrimitive([left[i - 1], right[i], right[i - 1]], [cols[i - 1], cols[i], cols[i - 1]], []);
            }
        }

        /// <summary>A soft band of light along the points (added): w0 wide at the start, w1 at the end,
        /// fading to nothing at both its edges (a texture across it, so no edge shows).</summary>
        void Soft(List<Vector2> raw, float w0, float w1, Func<float, Color> col, float r)
        {
            var pts = new List<Vector2>(raw.Count);
            foreach (var q in raw) if (pts.Count == 0 || pts[^1].DistanceSquaredTo(q) > 0.1f) pts.Add(q);
            int n = pts.Count;
            if (n < 2) return;
            var tex = Across();
            Vector2 pl = default, pr = default;
            Color pc = default;
            for (int i = 0; i < n; i++)
            {
                var dir = (pts[Math.Min(n - 1, i + 1)] - pts[Math.Max(0, i - 1)]).Normalized();
                var nrm = new Vector2(-dir.Y, dir.X);
                float u = i / (float)(n - 1) * r;
                float w = Mathf.Lerp(w0, w1, u) / 2;
                Vector2 l = pts[i] + nrm * w, rt = pts[i] - nrm * w;
                var cl = col(u);
                if (i > 0)
                {
                    DrawPrimitive([pl, l, rt], [pc, cl, cl], [new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(1, 0.5f)], tex);
                    DrawPrimitive([pl, rt, pr], [pc, cl, pc], [new Vector2(0, 0.5f), new Vector2(1, 0.5f), new Vector2(1, 0.5f)], tex);
                }
                pl = l; pr = rt; pc = cl;
            }
        }

        static GradientTexture2D? across, bloom;

        /// <summary>Light across a band: nothing at its edges, whole at its middle.</summary>
        static GradientTexture2D Across() => across ??= new GradientTexture2D
        {
            Width = 64, Height = 1,
            Gradient = new Gradient { Colors = [Colors.White with { A = 0 }, Colors.White with { A = 0.35f }, Colors.White, Colors.White with { A = 0.35f }, Colors.White with { A = 0 }], Offsets = [0f, 0.25f, 0.5f, 0.75f, 1f] },
        };

        /// <summary>A soft round light (added).</summary>
        static GradientTexture2D Bloom() => bloom ??= new GradientTexture2D
        {
            Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
            Gradient = new Gradient { Colors = [Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 }], Offsets = [0f, 0.4f, 1f] },
        };

        /// <summary>The head: a forged broad barb, iron round the heat, white at the point.</summary>
        void Head(Vector2 tip, Vector2 dir, float k)
        {
            var n = new Vector2(-dir.Y, dir.X);
            float L = 34 * k, W = 15 * k;
            Vector2[] Shape(float grow) =>
            [
                tip + dir * grow * 1.6f,
                tip - dir * (L + grow * 0.6f) + n * (W + grow),
                tip - dir * (L * 0.64f - grow * 0.2f),
                tip - dir * (L + grow * 0.6f) - n * (W + grow),
            ];
            // (two triangles each: the barbed shape is concave, and triangles never fail)
            void Barb(Vector2[] s, Color[] c)
            {
                DrawPrimitive([s[0], s[1], s[2]], [c[0], c[1], c[2]], []);
                DrawPrimitive([s[0], s[2], s[3]], [c[0], c[2], c[3]], []);
            }
            Barb(Shape(3.2f * k), [Iron, Iron, Iron, Iron]);
            Barb(Shape(0), [White, Deep, Hot, Deep]);
            // A bright ridge down its middle, the way a hot blade shows its edge.
            DrawLine(tip - dir * 2 * k, tip - dir * L * 0.6f, White with { A = 0.85f }, 1.6f * k, true);
        }

        /// <summary>A thing off the screen: a ring at the screen's edge holding a small lamp flame, its
        /// plain triangular tip pointing at the thing (in the marks' iron and ember).</summary>
        void Chevron(Vector2 at, Vector2 dir, float k, float breathe, float reach, bool light)
        {
            if (reach <= 0) return;
            float R = EdgeRing * k;
            if (light)
            {
                DrawTextureRect(Bloom(), new Rect2(at - Vector2.One * 34 * k, Vector2.One * 68 * k), false, Ember with { A = (0.18f + 0.1f * breathe) * reach });
                return;
            }
            var n = new Vector2(-dir.Y, dir.X);
            // The tip: a plain triangle standing off the ring toward the thing.
            var apex = at + dir * EdgeTip * k;
            var b1 = at + (dir * Mathf.Cos(0.42f) + n * Mathf.Sin(0.42f)) * (R - 1 * k);
            var b2 = at + (dir * Mathf.Cos(0.42f) - n * Mathf.Sin(0.42f)) * (R - 1 * k);
            Vector2[] tip = [apex, b1, b2];
            DrawPolyline([apex, b1, b2, apex], Iron with { A = Iron.A * reach }, 5f * k, true);
            DrawArc(at, R, 0, Mathf.Tau, 48, Iron with { A = Iron.A * reach }, 6f * k, true);
            // (the ring's dark heart, so the flame reads on snow or lamplight)
            DrawCircle(at, R - 2 * k, Deep with { A = 0.55f * reach });
            DrawColoredPolygon(tip, Hot.Lerp(White, 0.2f * breathe) with { A = reach });
            DrawArc(at, R, 0, Mathf.Tau, 48, Hot.Lerp(White, 0.25f) with { A = (0.85f + 0.15f * breathe) * reach }, 2.4f * k, true);
            // The lamp: a small flame over its cup.
            var f0 = at + new Vector2(0, 5.5f * k);
            var flame = new List<Vector2>(20);
            for (int i = 0; i <= 16; i++)
            {
                float a = Mathf.Pi * i / 16;
                // (a drop: round below, drawn up to a point)
                float rr = 4.6f * k;
                float x = Mathf.Cos(a) * rr, y = Mathf.Sin(a) * rr;
                flame.Add(f0 + new Vector2(x, y - 3 * k));
            }
            flame.Add(f0 + new Vector2(0, -14.5f * k));
            Vector2[] fl = [.. flame];
            DrawColoredPolygon(fl, Hot.Lerp(White, 0.15f + 0.2f * breathe) with { A = reach });
            var core = fl.Select(q => f0 + (q - f0) * 0.5f + new Vector2(0, 0.5f * k)).ToArray();
            DrawColoredPolygon(core, White with { A = 0.9f * reach });
            DrawLine(at + new Vector2(-6.5f * k, 8.5f * k), at + new Vector2(6.5f * k, 8.5f * k), Hot with { A = reach }, 2.2f * k, true);
            DrawLine(at + new Vector2(-4f * k, 11.5f * k), at + new Vector2(4f * k, 11.5f * k), Hot with { A = 0.8f * reach }, 1.8f * k, true);
        }

        /// <summary>The arrow's tail where it leaves the words: one link of the chain, end on.</summary>
        void Link(Vector2 at, Vector2 dir, float k)
        {
            var c = at + dir * 2 * k;
            DrawArc(c, 6.2f * k, 0, Mathf.Tau, 20, Iron, 4.6f * k, true);
            DrawArc(c, 6.2f * k, 0, Mathf.Tau, 20, Deep.Lerp(Hot, 0.35f), 1.8f * k, true);
        }

        /// <summary>The mark where it lands: a ring round a point, brackets at an area's corners;
        /// it strikes bright and a size larger, and settles.</summary>
        void Mark((Vector2 C, float R, Rect2 Box, bool Round) m, float k, float strike, float breathe, bool light, bool pale = false)
        {
            float grow = 7 * strike * strike;
            if (m.Round)
            {
                float rr = m.R + grow + 1.5f * breathe;
                if (light)
                {
                    var ring = new List<Vector2>(65);
                    for (int i = 0; i <= 64; i++) ring.Add(m.C + Vector2.FromAngle(i * Mathf.Tau / 64) * rr);
                    Soft(ring, 26 * k, 26 * k, _ => (pale ? PaleGlow : Ember) with { A = (pale ? 0.22f : 0.3f) + 0.35f * strike }, 1);
                    return;
                }
                DrawArc(m.C, rr, 0, Mathf.Tau, 64, Iron, 7f * k, true);
                DrawArc(m.C, rr, 0, Mathf.Tau, 64, (pale ? Bone : Hot.Lerp(White, 0.25f + 0.6f * strike)) with { A = 0.85f + 0.15f * breathe }, 2.6f * k, true);
                return;
            }
            var b = m.Box.Grow(grow);
            float arm = Math.Min(30 * k, Math.Min(b.Size.X, b.Size.Y) * 0.3f);
            foreach (var (corner, sx, sy) in new[] { (b.Position, 1, 1), (new Vector2(b.End.X, b.Position.Y), -1, 1), (b.End, -1, -1), (new Vector2(b.Position.X, b.End.Y), 1, -1) })
            {
                var p = new[] { corner + new Vector2(sx * arm, 0), corner, corner + new Vector2(0, sy * arm) };
                if (light) { Soft([.. p], 26 * k, 26 * k, _ => Ember with { A = 0.3f + 0.35f * strike }, 1); continue; }
                DrawPolyline(p, Iron, 7f * k, true);
                DrawPolyline(p, Hot.Lerp(White, 0.25f + 0.6f * strike) with { A = 0.85f + 0.15f * breathe }, 2.6f * k, true);
            }
        }
    }

    static Shader? smokeShader;

    /// <summary>A soft dark the words stand on: whole under the words, fading to nothing over `fade` px
    /// round them, no edge anywhere.</summary>
    static Shader SmokeShader() => smokeShader ??= new Shader
    {
        Code = """
            shader_type canvas_item;
            uniform vec2 size = vec2(400.0, 200.0);
            uniform float fade = 140.0;
            uniform float alpha = 0.45;
            void fragment() {
                vec2 p = (UV - 0.5) * size;
                vec2 h = size * 0.5 - vec2(fade) - vec2(14.0);
                vec2 d = abs(p) - h;
                float sd = length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0) - 14.0;
                float a = 1.0 - smoothstep(0.0, fade, sd);
                COLOR = vec4(0.02, 0.012, 0.008, alpha * a * a * (3.0 - 2.0 * a));
            }
            """,
    };

    static Shader? dimShader;

    /// <summary>The world drained to ash, darkened and softened (a light blur calms the ground's
    /// mottle), deeper at the screen's edges, but for soft round pools on the things being taught:
    /// their own colour, faded over the pool's outer half, never lit brighter than they were.</summary>
    static Shader DimShader() => dimShader ??= new Shader
    {
        Code = """
            shader_type canvas_item;
            uniform sampler2D screen : hint_screen_texture, filter_linear;
            uniform vec4 lights[6];
            uniform int count = 0;
            uniform int soft_first = 0;
            uniform vec4 crisp[4];
            uniform int crisp_n = 0;
            uniform float amount = 0.0;
            uniform int old_dim = 0;
            uniform float night = 0.0;
            uniform vec2 canvas = vec2(1920.0, 1080.0);
            void fragment() {
                vec2 p = UV * canvas;
                float lit = 0.0;
                float warm = 0.0;
                for (int i = 0; i < 6; i++) {
                    if (i >= count) { break; }
                    float r = lights[i].z;
                    float d = length(p - lights[i].xy);
                    // (her own: nearly a straight fall over the whole radius, eased at its ends, so it
                    // changes under 2% in 10 px and has no rim; a thing's: lit to half, falling outside)
                    float t = clamp(d / r, 0.0, 1.0);
                    float l = i < soft_first ? 1.0 - mix(t, smoothstep(0.0, 1.0, t), 0.35) : 1.0 - smoothstep(0.5 * r, r, d);
                    lit = max(lit, l);
                    warm = max(warm, l * lights[i].w);
                }
                // (a caster's body: wholly lit, edge eased over its outer fifth; no dim, no blur)
                float body = 0.0;
                for (int j = 0; j < 4; j++) {
                    if (j >= crisp_n) { break; }
                    float dj = length(p - crisp[j].xy);
                    body = max(body, 1.0 - smoothstep(0.8 * crisp[j].z, crisp[j].z, dj));
                }
                vec3 c = texture(screen, SCREEN_UV).rgb;
                float k = amount * (1.0 - max(lit, body));
                vec3 src = c;
                if (k > 0.001) {
                    // (about 3 px at 1080p: a 5 by 5 gaussian, 1.5 px apart)
                    vec2 px = SCREEN_PIXEL_SIZE * 1.5;
                    vec3 acc = vec3(0.0);
                    float wsum = 0.0;
                    for (int x = -2; x <= 2; x++) {
                        for (int y = -2; y <= 2; y++) {
                            float g = exp(-float(x * x + y * y) / 4.5);
                            acc += texture(screen, SCREEN_UV + vec2(float(x), float(y)) * px).rgb * g;
                            wsum += g;
                        }
                    }
                    src = mix(c, acc / wsum, k);
                }
                float y = dot(src, vec3(0.299, 0.587, 0.114));
                // Half drained, and darkened by the hour and the pixel's own light. By day the lit ground loses
                // about 30% (round 2 judge: 45% sank it to the shadows' level, a dusk), its shade less; by night (a flat 28% cut sank it to near black: the bolts' archers in
                // the dash lesson barely read) the dark keeps nearly all it has and the lit about 80%: the drain,
                // the softening and the warm pools set the taught apart instead.
                float day_keep = mix(0.92, 0.70, smoothstep(0.03, 0.25, y));
                float night_keep = mix(0.95, 0.8, smoothstep(0.05, 0.35, y));
                float keep = old_dim == 1 ? 0.72 : mix(day_keep, night_keep, night);
                vec3 ash = mix(vec3(y), src, 0.5) * keep;
                vec2 q = UV - 0.5;
                ash *= 1.0 - (old_dim == 1 ? 0.15 : mix(0.15, 0.06, night)) * smoothstep(0.3, 0.8, length(q * vec2(1.0, 0.72)));
                // (a thing's pool is lit warm, as by the ember: never a cold white patch)
                vec3 col = mix(c, ash, k) * mix(vec3(1.0), vec3(1.06, 0.95, 0.78), warm * amount);
                // (the pools a touch brighter than the ground was, by day: so they still stand off the lighter world)
                col *= 1.0 + 0.15 * lit * amount * (1.0 - night) * (old_dim == 1 ? 0.0 : 1.0);
                COLOR = vec4(col, 1.0);
            }
            """,
    };
}
