using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>What a callout says, as the drawing needs it: its title and line, its kind, the key
/// that answers it (drawn as the key itself, pad-aware), and the footer's words.</summary>
public sealed record CalloutLook(string Title, string Line, CalloutKind Kind, Act? Key, Act? GoOn, string GoOnWord);

/// <summary>Where a callout points this frame, on the HUD's 1920 by 1080: points (a HUD part, a thing
/// in the world, projected), areas (the cards, a banner), and where its words should stand, if the
/// game says (a draft's tip). Behind this the look can change without the game knowing.</summary>
public sealed record CalloutAim(IReadOnlyList<Vector2> Points, IReadOnlyList<Rect2> Areas, Rect2? Words = null);

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
/// The tutorial's callouts (docs/story/TUTORIAL_COPY.md): the game's own tip voice set beside the
/// thing it is about, and an arrow to it. In TipLine's vocabulary (WorldType.cs): the title in
/// display type, the line under it outlined on the world, the subject's word marked in ember, keys
/// drawn as the keys themselves, burning in out of an ember glow; no panel behind. The arrow is drawn
/// in code: a tapered stroke of hot ember inside an iron edge, a soft glow round it, a barbed head and
/// a ring of light where it lands. A freeze dims the world but for a soft window round each target.
/// Everything a callout looks like is in this file.
/// </summary>
public partial class Callout : Control, ICalloutView
{
    const float Canvas = 1920, CanvasH = 1080;
    static readonly Color Bone = new("#f2e8d4"), Line = new("#e6dccb"), Iron = new(0.07f, 0.05f, 0.04f, 0.9f),
        Hot = new("#ffb35a"), Deep = new("#c4501a"), Mark = new("#ffa04a");

    CalloutLook look = null!;
    CalloutAim aim = new([], []);
    double age, gone = -1;
    readonly ColorRect dim;
    readonly ShaderMaterial dimMat;
    VBoxContainer column = null!;
    TextureRect burn = null!;
    readonly Ink glow, ink;
    Vector2 wordsAt;
    bool placed;

    public double Age => age;

    public Callout()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Style.Fill(this);
        dimMat = new ShaderMaterial { Shader = DimShader() };
        dim = new ColorRect { MouseFilter = MouseFilterEnum.Ignore, Material = dimMat, Visible = false };
        Style.Fill(dim);
        AddChild(dim);
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
        dim.Visible = l.Kind == CalloutKind.Freeze;
        column = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        column.AddThemeConstantOverride("separation", 6);
        var head = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        head.AddThemeConstantOverride("separation", 12);
        if (l.Key is Act k) { var key = Style.Prompt(k); key.SizeFlagsVertical = SizeFlags.ShrinkCenter; head.AddChild(key); }
        head.AddChild(WorldType.Lettering(l.Title.ToUpperInvariant(), Style.Display, 30, Bone));
        column.AddChild(head);
        var line = new RichTextLabel { BbcodeEnabled = true, FitContent = true, ScrollActive = false, MouseFilter = MouseFilterEnum.Ignore, AutowrapMode = TextServer.AutowrapMode.WordSmart };
        line.AddThemeFontOverride("normal_font", Style.Text);
        line.AddThemeFontSizeOverride("normal_font_size", 21);
        line.AddThemeColorOverride("default_color", Line);
        line.AddThemeColorOverride("font_outline_color", new Color(0.03f, 0.02f, 0.02f, 0.85f));
        line.AddThemeConstantOverride("outline_size", 6);
        line.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.6f));
        line.AddThemeConstantOverride("shadow_offset_y", 2);
        line.AddThemeConstantOverride("shadow_outline_size", 8);
        line.Text = $"[center]{Marked(l.Line, l.Title)}[/center]";
        line.CustomMinimumSize = new Vector2(Math.Min(560, Style.Text.GetStringSize(l.Line, HorizontalAlignment.Left, -1, 21).X + 12), 0);
        column.AddChild(line);
        // A freeze says how to go on, quietly, under the words.
        if (l.Kind == CalloutKind.Freeze && l.GoOn is Act go)
        {
            var foot = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
            foot.AddThemeConstantOverride("separation", 8);
            var key = Style.Prompt(go);
            key.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            key.Scale = new Vector2(0.8f, 0.8f);
            foot.AddChild(key);
            foot.AddChild(WorldType.Lettering(l.GoOnWord, Style.TextItalic, 17, new Color("#b8ab94")));
            column.AddChild(Style.Gap(4));
            column.AddChild(foot);
        }
        burn = WorldType.Light(new Vector2(640, 170), Style.Ember with { A = 0 });
        AddChild(burn);
        AddChild(column);
    }

    public void Aim(CalloutAim a)
    {
        aim = a;
        if (!placed && column != null) { wordsAt = Place(); placed = true; }
        else if (column != null) wordsAt = wordsAt.Lerp(Place(), 0.25f);
    }

    public void TakeDown() { if (gone < 0) gone = 0; }

    /// <summary>The text with its subject (the title's word, where the line says it) marked in ember, once.</summary>
    static string Marked(string text, string title)
    {
        string safe = text.Replace("[", "[lb]");
        var word = title.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        foreach (var w in word.Length > 0 ? new[] { word[^1].TrimEnd('s'), word[0] } : Array.Empty<string>())
        {
            if (w.Length < 3 || w.Equals("the", StringComparison.OrdinalIgnoreCase)) continue;
            var m = Regex.Match(safe, $@"\b{Regex.Escape(w)}\w*", RegexOptions.IgnoreCase);
            if (m.Success) return safe[..m.Index] + $"[color={Mark.ToHtml(false)}]" + m.Value + "[/color]" + safe[(m.Index + m.Length)..];
        }
        return safe;
    }

    /* ---------------------------------------------------------- layout -- */

    Vector2 Size2 => column.GetCombinedMinimumSize();

    /// <summary>Where the words' middle stands: where the game said (a draft's tip), else beside the
    /// first target, on the side with room, a good stride from it so the arrow has length to read.</summary>
    Vector2 Place()
    {
        var s = Size2;
        if (aim.Words is Rect2 w) return w.GetCenter();
        Vector2 t = Primary();
        Vector2 at;
        if (aim.Areas.Count > 0 && aim.Points.Count == 0)
        {
            // An area (a banner): the words under it, the arrow up to it.
            var r = aim.Areas[0];
            at = new Vector2(r.GetCenter().X, r.End.Y + 150 + s.Y / 2);
        }
        else if (t.Y > CanvasH - 260)
        {
            // A part of the instrument along the foot: the words above it, leaning to the middle.
            float x = Mathf.Lerp(t.X, 960, 0.35f);
            at = new Vector2(x, t.Y - 230 - s.Y / 2);
        }
        else
        {
            // A thing in the world: to its side with the more room, a little above.
            float side = t.X < 960 ? 1 : -1;
            at = new Vector2(t.X + side * (190 + s.X / 2), t.Y - 110);
        }
        float hw = s.X / 2 + 24, hh = s.Y / 2 + 24;
        return new Vector2(Mathf.Clamp(at.X, hw + 40, Canvas - hw - 40), Mathf.Clamp(at.Y, hh + 120, CanvasH - 230 - hh));
    }

    Vector2 Primary() => aim.Points.Count > 0 ? aim.Points[0] : aim.Areas.Count > 0 ? aim.Areas[0].GetCenter() : new Vector2(960, 540);

    Rect2 Words => new(wordsAt - Size2 / 2, Size2);

    /// <summary>Each arrow: from the words' edge toward the target, to just short of it (an area: its edge).</summary>
    IEnumerable<(Vector2 From, Vector2 To, Vector2 At, float Ring)> Arrows()
    {
        var box = Words.Grow(14);
        foreach (var p in aim.Points) yield return (Edge(box, p), Short(p, box.GetCenter(), 40), p, 30);
        if (aim.Points.Count == 0)
            foreach (var r in aim.Areas.Take(1))
            {
                var c = r.GetCenter();
                var near = new Vector2(Mathf.Clamp(box.GetCenter().X, r.Position.X + 30, r.End.X - 30), box.GetCenter().Y < r.Position.Y ? r.Position.Y - 10 : box.GetCenter().Y > r.End.Y ? r.End.Y + 10 : c.Y);
                yield return (Edge(box, near), near, near, 0);
            }
    }

    /// <summary>Where a line from the box's middle toward p leaves the box.</summary>
    static Vector2 Edge(Rect2 box, Vector2 p)
    {
        var c = box.GetCenter();
        var d = p - c;
        if (d.LengthSquared() < 1) return c;
        float tx = Mathf.Abs(d.X) > 0.001f ? (box.Size.X / 2) / Mathf.Abs(d.X) : float.MaxValue;
        float ty = Mathf.Abs(d.Y) > 0.001f ? (box.Size.Y / 2) / Mathf.Abs(d.Y) : float.MaxValue;
        return c + d * Mathf.Min(1, Mathf.Min(tx, ty));
    }

    static Vector2 Short(Vector2 p, Vector2 from, float by)
    {
        var d = p - from;
        float len = d.Length();
        return len <= by * 2 ? p : p - d / len * by;
    }

    /* ----------------------------------------------------------- frame -- */

    public override void _Process(double delta)
    {
        if (look == null) return;
        age += delta;
        if (gone >= 0) { gone += delta; if (gone > 0.35) { QueueFree(); return; } }
        var s = Size2;
        column.Size = s;
        column.Position = wordsAt - s / 2;
        burn.Position = wordsAt - burn.Size / 2;
        // It burns in: the glow first, the words up through it by Legible, the glow cooling after.
        float k = (float)Math.Clamp(age / ICalloutView.Legible, 0, 1);
        float out_ = gone >= 0 ? 1 - (float)Math.Clamp(gone / 0.35, 0, 1) : 1;
        Modulate = Colors.White with { A = out_ };
        column.Modulate = Colors.White with { A = k * k * (3 - 2 * k) };
        burn.Modulate = Style.Ember with { A = 0.34f * (float)Math.Max(0, 1 - Math.Abs(age - 0.2) / 0.6) };
        // The world dims round its windows, easing in.
        if (dim.Visible)
        {
            var holes = new List<Vector4>();
            foreach (var p in aim.Points.Take(3)) holes.Add(new Vector4(p.X, p.Y, 56, 56));
            foreach (var r in aim.Areas.Take(4 - holes.Count)) holes.Add(new Vector4(r.GetCenter().X, r.GetCenter().Y, r.Size.X / 2 + 6, r.Size.Y / 2 + 6));
            // (the words keep their own ground clear, so the dim never sits under them)
            if (holes.Count < 4) holes.Add(new Vector4(wordsAt.X, wordsAt.Y, s.X / 2 + 10, s.Y / 2 + 6));
            var arr = new Vector4[4];
            for (int i = 0; i < holes.Count && i < 4; i++) arr[i] = holes[i];
            dimMat.SetShaderParameter("holes", arr);
            dimMat.SetShaderParameter("count", Math.Min(4, holes.Count));
            dimMat.SetShaderParameter("canvas", dim.Size);
            float e = (float)Math.Clamp(age / 0.22, 0, 1);
            dimMat.SetShaderParameter("amount", 0.58f * e * (2 - e));
        }
        glow.QueueRedraw();
        ink.QueueRedraw();
    }

    /// <summary>How much of each arrow is drawn: it shoots out from the words between 0.08 s and 0.36 s.</summary>
    float Reach => (float)Math.Clamp((age - 0.08) / 0.28, 0, 1);

    /// <summary>The arrows' layer: the glow (added light) or the ink.</summary>
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
            float r = reach * reach * (3 - 2 * reach);
            float pulse = 0.5f + 0.5f * Mathf.Sin((float)c.age * 4.2f);
            foreach (var (from, to, at, ring) in c.Arrows())
            {
                var pts = Curve(from, to, r);
                if (pts.Count < 2) continue;
                if (glow)
                {
                    // A soft light along it, warmest at the head.
                    for (int i = 1; i < pts.Count; i++)
                    {
                        float u = i / (float)(pts.Count - 1);
                        DrawLine(pts[i - 1], pts[i], Style.Ember with { A = 0.05f + 0.1f * u }, 22 + 8 * u, true);
                    }
                    if (reach >= 1 && ring > 0) DrawCircle(at, 26 + 6 * pulse, Style.Ember with { A = 0.08f + 0.05f * pulse });
                    continue;
                }
                // The iron edge, then the hot core inside it, tapering from the words to the head.
                Stroke(pts, 9.5f, 4.5f, _ => Iron);
                Stroke(pts, 5.5f, 2.2f, u => Deep.Lerp(Hot, u));
                if (reach >= 0.98f && (pts[^1] - pts[^2]).LengthSquared() > 0.01f) Head(pts[^1], (pts[^1] - pts[^2]).Normalized());
                // Where it lands: a ring of light round the thing (none for an area: its edge is the mark).
                if (ring > 0 && reach >= 1)
                {
                    float rr = ring + 3 * pulse;
                    DrawArc(at, rr, 0, Mathf.Tau, 48, Iron, 4.5f, true);
                    DrawArc(at, rr, 0, Mathf.Tau, 48, Hot with { A = 0.7f + 0.3f * pulse }, 2, true);
                }
            }
        }

        /// <summary>A gentle arc from a to b (bowed a fifth of its length), drawn as far as k.</summary>
        static List<Vector2> Curve(Vector2 a, Vector2 b, float k)
        {
            var d = b - a;
            float len = d.Length();
            var list = new List<Vector2>();
            if (len < 8) return list;
            var n = new Vector2(-d.Y, d.X) / len;
            // Bowed away from the screen's middle, so neighbouring arrows fan rather than cross.
            if (n.Dot(a - new Vector2(960, 540)) < 0) n = -n;
            var ctl = (a + b) / 2 + n * len * 0.18f;
            int steps = Math.Max(6, (int)(len / 14));
            for (int i = 0; i <= steps; i++)
            {
                float t = k * i / steps;
                list.Add((1 - t) * (1 - t) * a + 2 * (1 - t) * t * ctl + t * t * b);
            }
            return list;
        }

        /// <summary>A stroke along the points, w0 wide at the start, w1 at the end: a strip of
        /// triangles, each drawn as it is (a polygon is triangulated, and one squeezed thin by the
        /// arrow's first frames fails to; a triangle never does).</summary>
        void Stroke(List<Vector2> raw, float w0, float w1, Func<float, Color> col)
        {
            // Points closer than a third of a pixel give no direction: kept apart or dropped.
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
                float u = i / (float)(n - 1);
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

        /// <summary>The head: a barbed point, iron round ember.</summary>
        void Head(Vector2 tip, Vector2 dir)
        {
            var n = new Vector2(-dir.Y, dir.X);
            Vector2[] Shape(float s) => [tip + dir * 4 * s, tip - dir * 24 * s + n * 12 * s, tip - dir * 17 * s, tip - dir * 24 * s - n * 12 * s];
            // (two triangles each: the barbed shape is concave, and triangles never fail)
            void Barb(Vector2[] s, Color[] c)
            {
                DrawPrimitive([s[0], s[1], s[2]], [c[0], c[1], c[2]], []);
                DrawPrimitive([s[0], s[2], s[3]], [c[0], c[2], c[3]], []);
            }
            Barb(Shape(1.25f), [Iron, Iron, Iron, Iron]);
            Barb(Shape(1), [Hot.Lightened(0.3f), Hot, Deep, Hot]);
        }
    }

    static Shader? dimShader;

    /// <summary>The world held dark round soft windows (each a rounded box: a point, an area, the words).</summary>
    static Shader DimShader() => dimShader ??= new Shader
    {
        Code = """
            shader_type canvas_item;
            uniform vec4 holes[4];
            uniform int count = 0;
            uniform float amount = 0.0;
            uniform vec2 canvas = vec2(1920.0, 1080.0);
            void fragment() {
                vec2 p = UV * canvas;
                float keep = 0.0;
                for (int i = 0; i < 4; i++) {
                    if (i >= count) { break; }
                    vec2 d = abs(p - holes[i].xy) - holes[i].zw;
                    float sd = length(max(d, vec2(0.0))) + min(max(d.x, d.y), 0.0);
                    keep = max(keep, 1.0 - smoothstep(-6.0, 64.0, sd));
                }
                vec2 c = UV - 0.5;
                float vig = smoothstep(0.15, 0.75, length(c * vec2(1.0, 0.8)));
                COLOR = vec4(0.025, 0.015, 0.01, amount * (0.8 + 0.2 * vig) * (1.0 - keep));
            }
            """,
    };
}
