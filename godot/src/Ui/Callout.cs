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
    static readonly Color Bone = new("#f2e8d4"), LineInk = new("#e8dfcd"), FootInk = new("#cbbd9f"),
        Iron = new(0.055f, 0.04f, 0.035f, 0.94f), Deep = new("#a8380f"), Hot = new("#ff9a40"), White = new("#ffe6a8"),
        Mark = new("#ffa04a"), Warm = new(1f, 0.74f, 0.46f);

    CalloutLook look = null!;
    CalloutAim aim = new([], []);
    double age, gone = -1;
    readonly ColorRect dim;
    readonly ShaderMaterial dimMat;
    readonly TextureRect smoke;
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
        dim = new ColorRect { MouseFilter = MouseFilterEnum.Ignore, Material = dimMat, Visible = false };
        Style.Fill(dim);
        AddChild(dim);
        smoke = new TextureRect
        {
            Texture = Smoke(), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
            MouseFilter = MouseFilterEnum.Ignore, Modulate = Colors.Transparent,
        };
        AddChild(smoke);
        glow = new Ink(this, true) { Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
        ink = new Ink(this, false);
        Style.Fill(glow);
        Style.Fill(ink);
        AddChild(glow);
        AddChild(ink);
        Modulate = Colors.Transparent;
    }

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
            f.AddChild(Chip(Style.Prompt(go), 1.2f));
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
        if (aim.Words is Rect2 w) { wordsAt = w.GetCenter(); placed = true; return; }
        var p = Primary();
        if (!placed) { wordsAt = Place(); placedFor = p; placed = true; }
        else if (p.DistanceTo(placedFor) > 80) { wordsAt = wordsAt.Lerp(Place(), 0.2f); placedFor = placedFor.Lerp(p, 0.2f); }
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
        if (Panel || W(text) <= 380) rows.Add(text);
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
        string? subject = Subject(text, look.Title);
        bool marked = false;
        var list = new List<Control>();
        foreach (var r in rows)
        {
            var box = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
            box.AddThemeConstantOverride("separation", 0);
            foreach (var (seg, isKey) in Split(r, keys))
            {
                if (isKey) { box.AddChild(Pad(Chip(Controls.Instance?.UsingPad == true ? Style.PadButton(seg) : Style.Key(seg), 1.15f), 5)); continue; }
                string bb = seg.Replace("[", "[lb]");
                if (!marked && subject != null && Regex.Match(bb, $@"\b{Regex.Escape(subject)}\b", RegexOptions.IgnoreCase) is { Success: true } m)
                {
                    bb = bb[..m.Index] + $"[color={Mark.ToHtml(false)}]" + m.Value + "[/color]" + bb[(m.Index + m.Length)..];
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
            float ring = r + 9;
            list.Add((aim.Points[i], ring, new Rect2(aim.Points[i] - Vector2.One * ring, Vector2.One * ring * 2), true));
        }
        if (aim.Points.Count == 0)
            foreach (var a in aim.Areas.Take(1))
            {
                // A whole row of cards is the panel itself: nothing to point at but the words' own place.
                if (Panel && a.Size.X > 760) continue;
                var g = a.Grow(Panel ? 6 : 12);
                list.Add((g.GetCenter(), 0, g, false));
            }
        return list;
    }

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
        Rect2? her = aim.Her?.Grow(22);
        if (her is Rect2 h0) keep.Add(h0);
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
                float cost = 0.1f * Math.Abs(x - 960) + 0.05f * Math.Abs(y - 470);
                for (int i = 0; i < marks.Count; i++)
                {
                    float d = Apart(box, marks[i].Box);
                    cost += (i == 0 ? 1.4f : 0.7f) * Math.Abs(d - 120) + (d < 56 ? 400 : 0);
                    if (her is Rect2 hr && Crosses(Route(box, marks[i]), hr)) cost += 900;
                }
                if (cost < best) { best = cost; at = new Vector2(x, y); }
            }
        return at;
    }

    /// <summary>How far apart two boxes are (0: they touch).</summary>
    static float Apart(Rect2 a, Rect2 b)
    {
        float dx = Math.Max(0, Math.Max(a.Position.X - b.End.X, b.Position.X - a.End.X));
        float dy = Math.Max(0, Math.Max(a.Position.Y - b.End.Y, b.Position.Y - a.End.Y));
        return Mathf.Sqrt(dx * dx + dy * dy);
    }

    /// <summary>Whether an arrow's way passes over r.</summary>
    static bool Crosses((Vector2 A, Vector2 DA, Vector2 B, Vector2 DB) w, Rect2 r)
    {
        var pts = Ink.Bezier(w.A, w.A + w.DA * Bend(w.A, w.B), w.B - w.DB * Bend(w.A, w.B), w.B, 1, 24);
        foreach (var q in pts) if (r.HasPoint(q)) return true;
        return false;
    }

    /// <summary>How far an arrow's ends hold their way before it bends.</summary>
    static float Bend(Vector2 a, Vector2 b) => Math.Min(0.5f * a.DistanceTo(b), 160);

    Rect2 Words => new(wordsAt - Size2 / 2, Size2);

    /// <summary>Where an arrow leaves the words, and which way: out of the foot or the head toward a
    /// thing below or above (the words are wide), else out of the side.</summary>
    static (Vector2 P, Vector2 Dir) Exit(Rect2 box, Vector2 toward)
    {
        var c = box.GetCenter();
        var d = toward - c;
        float ax = Math.Abs(d.X) / (box.Size.X / 2 + 90), ay = Math.Abs(d.Y) / (box.Size.Y / 2 + 20);
        if (ay >= ax)
        {
            float x = Mathf.Clamp(toward.X, box.Position.X + box.Size.X * 0.2f, box.End.X - box.Size.X * 0.2f);
            return (new Vector2(x, d.Y > 0 ? box.End.Y : box.Position.Y), new Vector2(0, Math.Sign(d.Y)));
        }
        return (new Vector2(d.X > 0 ? box.End.X : box.Position.X, c.Y), new Vector2(Math.Sign(d.X), 0));
    }

    /// <summary>An arrow's way: where it leaves the words and which way, where it lands and which
    /// way. A point: out of the words' nearer edge, onto its ring. An area below or above (a card, a
    /// banner): onto the middle of its near edge, straight down or up when that lies under the words,
    /// else hooked off the words' end; an area beside: onto the middle of its near side.</summary>
    static (Vector2 A, Vector2 DA, Vector2 B, Vector2 DB) Route(Rect2 box, (Vector2 C, float R, Rect2 Box, bool Round) m)
    {
        if (m.Round)
        {
            var (a, da) = Exit(box, m.C);
            var db = (m.C - a).Normalized();
            return (a, da, m.C - db * (m.R + 5), db);
        }
        var r = m.Box.Grow(4);
        var c = box.GetCenter();
        bool below = r.Position.Y >= box.End.Y - 4, above = r.End.Y <= box.Position.Y + 4;
        if (below || above)
        {
            var sy = new Vector2(0, below ? 1 : -1);
            var land = new Vector2(r.GetCenter().X, below ? r.Position.Y : r.End.Y);
            if (land.X >= box.Position.X + 24 && land.X <= box.End.X - 24)
                return (new Vector2(land.X, below ? box.End.Y : box.Position.Y), sy, land, sy);
            bool left = land.X < c.X;
            return (new Vector2(left ? box.Position.X : box.End.X, c.Y), new Vector2(left ? -1 : 1, 0), land, sy);
        }
        bool l2 = r.GetCenter().X < c.X;
        var side = new Vector2(l2 ? -1 : 1, 0);
        return (new Vector2(l2 ? box.Position.X : box.End.X, c.Y), side, new Vector2(l2 ? r.End.X : r.Position.X, Mathf.Clamp(c.Y, r.Position.Y + 12, r.End.Y - 12)), side);
    }

    /// <summary>Each arrow: its way, and the mark it lands on.</summary>
    IEnumerable<(Vector2 A, Vector2 DA, Vector2 B, Vector2 DB, (Vector2 C, float R, Rect2 Box, bool Round) M)> Arrows()
    {
        var box = Words.Grow(Headed ? 8 : 12);
        foreach (var m in Marks())
        {
            var (a, da, b, db) = Route(box, m);
            if (a.DistanceTo(b) < 24) continue;
            yield return (a, da, b, db, m);
        }
    }

    /* ----------------------------------------------------------- frame -- */

    static float Smooth(double x) { float k = (float)Math.Clamp(x, 0, 1); return k * k * (3 - 2 * k); }

    public override void _Process(double delta)
    {
        if (look == null || column == null) return;
        age += delta;
        if (gone >= 0) { gone += delta; if (gone > 0.3) { QueueFree(); return; } }
        var s = Size2;
        column.Size = s;
        column.Position = wordsAt - s / 2;
        // It burns in: the glow first, the words up through it by Legible, the title hot and cooling to bone.
        float out_ = gone >= 0 ? 1 - Smooth(gone / 0.3) : 1;
        Modulate = Colors.White with { A = out_ };
        column.Modulate = Colors.White with { A = Smooth(age / ICalloutView.Legible) };
        if (title != null) title.Modulate = Warm.Lerp(Colors.White, Smooth((age - 0.1) / 0.6));
        // The way on shows once it may be taken (Teacher.MinHold), and breathes while it waits.
        if (foot != null) foot.Modulate = Colors.White with { A = Smooth((age - Teacher.MinHold) / 0.18) * (0.86f + 0.14f * Mathf.Cos((float)(age - Teacher.MinHold) * 2.6f)) };
        burn.Size = new Vector2(s.X + 260, s.Y + 120);
        burn.Position = wordsAt - burn.Size / 2;
        burn.Modulate = Style.Ember with { A = 0.3f * (float)Math.Max(0, 1 - Math.Abs(age - 0.16) / 0.55) + (Headed ? 0 : 0.035f) };
        // A smoke under the words, so they read over a lit ground (none on a panel: it has its own dark).
        if (!Panel)
        {
            smoke.Size = new Vector2(s.X + 220, s.Y + 130);
            smoke.Position = wordsAt - smoke.Size / 2;
            smoke.Modulate = Colors.White with { A = (Freeze ? 0.34f : 0.46f) * Smooth(age / 0.25) };
        }
        // The world drains and darkens round its pools of light, easing in.
        if (dim.Visible)
        {
            var lights = new Vector4[6];
            var corner = new float[6];
            int n = 0;
            foreach (var m in Marks())
            {
                if (n >= 6) break;
                if (m.Round) { float r = m.R + 30; lights[n] = new Vector4(m.C.X, m.C.Y, r, r); corner[n] = r; }
                else { var h = m.Box.Size / 2 + new Vector2(14, 14); lights[n] = new Vector4(m.C.X, m.C.Y, h.X, h.Y); corner[n] = 22; }
                n++;
            }
            dimMat.SetShaderParameter("lights", lights);
            dimMat.SetShaderParameter("corner", corner);
            dimMat.SetShaderParameter("count", n);
            dimMat.SetShaderParameter("canvas", dim.Size);
            dimMat.SetShaderParameter("amount", Smooth(age / 0.26));
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
            foreach (var (a, da, b, db, m) in c.Arrows())
            {
                float len = a.DistanceTo(b);
                float bend = Bend(a, b);
                var pts = Bezier(a, a + da * bend, b - db * bend, b, r, Math.Max(10, (int)(len / 9)));
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
                        return Style.Ember with { A = 0.12f + 0.2f * u + 0.22f * hb };
                    }, r);
                    float bloom = (64 + 14 * strike) * k;
                    DrawTextureRect(Bloom(), new Rect2(tip - Vector2.One * bloom / 2, Vector2.One * bloom), false, Style.Ember with { A = 0.42f + 0.3f * strike });
                    if (reach >= 1) Mark(m, k, strike, breathe, true);
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
                if (reach >= 1) Mark(m, k, strike, breathe, false);
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

        /// <summary>The arrow's tail where it leaves the words: one link of the chain, end on.</summary>
        void Link(Vector2 at, Vector2 dir, float k)
        {
            var c = at + dir * 2 * k;
            DrawArc(c, 6.2f * k, 0, Mathf.Tau, 20, Iron, 4.6f * k, true);
            DrawArc(c, 6.2f * k, 0, Mathf.Tau, 20, Deep.Lerp(Hot, 0.35f), 1.8f * k, true);
        }

        /// <summary>The mark where it lands: a ring round a point, brackets at an area's corners;
        /// it strikes bright and a size larger, and settles.</summary>
        void Mark((Vector2 C, float R, Rect2 Box, bool Round) m, float k, float strike, float breathe, bool light)
        {
            float grow = 7 * strike * strike;
            if (m.Round)
            {
                float rr = m.R + grow + 1.5f * breathe;
                if (light)
                {
                    var ring = new List<Vector2>(65);
                    for (int i = 0; i <= 64; i++) ring.Add(m.C + Vector2.FromAngle(i * Mathf.Tau / 64) * rr);
                    Soft(ring, 26 * k, 26 * k, _ => Style.Ember with { A = 0.3f + 0.35f * strike }, 1);
                    return;
                }
                DrawArc(m.C, rr, 0, Mathf.Tau, 64, Iron, 7f * k, true);
                DrawArc(m.C, rr, 0, Mathf.Tau, 64, Hot.Lerp(White, 0.25f + 0.6f * strike) with { A = 0.85f + 0.15f * breathe }, 2.6f * k, true);
                return;
            }
            var b = m.Box.Grow(grow);
            float arm = Math.Min(30 * k, Math.Min(b.Size.X, b.Size.Y) * 0.3f);
            foreach (var (corner, sx, sy) in new[] { (b.Position, 1, 1), (new Vector2(b.End.X, b.Position.Y), -1, 1), (b.End, -1, -1), (new Vector2(b.Position.X, b.End.Y), 1, -1) })
            {
                var p = new[] { corner + new Vector2(sx * arm, 0), corner, corner + new Vector2(0, sy * arm) };
                if (light) { Soft([.. p], 26 * k, 26 * k, _ => Style.Ember with { A = 0.3f + 0.35f * strike }, 1); continue; }
                DrawPolyline(p, Iron, 7f * k, true);
                DrawPolyline(p, Hot.Lerp(White, 0.25f + 0.6f * strike) with { A = 0.85f + 0.15f * breathe }, 2.6f * k, true);
            }
        }
    }

    static GradientTexture2D? smokeTex;

    /// <summary>A soft dark the words stand on: no edge anywhere, darkest under them.</summary>
    static GradientTexture2D Smoke() => smokeTex ??= new GradientTexture2D
    {
        Width = 128, Height = 128, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
        Gradient = new Gradient
        {
            Colors = [new Color(0.02f, 0.012f, 0.008f, 1), new Color(0.02f, 0.012f, 0.008f, 0.75f), new Color(0.02f, 0.012f, 0.008f, 0)],
            Offsets = [0f, 0.5f, 1f],
        },
    };

    static Shader? dimShader;

    /// <summary>The world drained to ash and darkened, deeper at the screen's edges, but for pools of
    /// lamplight (each a rounded box: a ring's circle, an area), warm at their edge.</summary>
    static Shader DimShader() => dimShader ??= new Shader
    {
        Code = """
            shader_type canvas_item;
            uniform sampler2D screen : hint_screen_texture, filter_linear;
            uniform vec4 lights[6];
            uniform float corner[6];
            uniform int count = 0;
            uniform float amount = 0.0;
            uniform vec2 canvas = vec2(1920.0, 1080.0);
            float box(vec2 p, vec2 c, vec2 h, float r) {
                vec2 d = abs(p - c) - (h - vec2(r));
                return length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0) - r;
            }
            void fragment() {
                vec2 p = UV * canvas;
                float lit = 0.0;
                float rim = 0.0;
                for (int i = 0; i < 6; i++) {
                    if (i >= count) { break; }
                    float r = min(corner[i], min(lights[i].z, lights[i].w));
                    float sd = box(p, lights[i].xy, lights[i].zw, r);
                    lit = max(lit, 1.0 - smoothstep(-10.0, 72.0, sd));
                    rim = max(rim, exp(-pow((sd - 18.0) / 34.0, 2.0)));
                }
                vec3 c = texture(screen, SCREEN_UV).rgb;
                float y = dot(c, vec3(0.299, 0.587, 0.114));
                vec3 ash = mix(vec3(y), c, 0.22) * vec3(0.46, 0.445, 0.43);
                vec2 q = UV - 0.5;
                ash *= 1.0 - 0.4 * smoothstep(0.25, 0.8, length(q * vec2(1.0, 0.72)));
                vec3 o = mix(c, ash, amount * (1.0 - lit));
                o += vec3(1.0, 0.5, 0.18) * rim * 0.045 * amount * (1.0 - lit * 0.6);
                COLOR = vec4(o, 1.0);
            }
            """,
    };
}
