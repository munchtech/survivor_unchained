using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>Where a goal is on the screen's plane, whether it can be seen there, how far, and (on screen) how opaque.</summary>
public readonly record struct GoalMark(Vector2 At, bool OnScreen, string Glyph, Color Color, string Label, float Metres, float Alpha = 1);

/// <summary>
/// The goals on the ground: a pin over the spot (disc, tail, stem and a tick on the ground, with its
/// name under, bobbing a little) while it is on screen, and a larger pulsing arrow at the screen's
/// edge, with its name and distance, when it is not.
/// </summary>
public partial class GoalMarks : Control
{
    readonly record struct Edge(GoalMark Mark, Vector2 Point, Vector2 Dir, bool Bottom);
    readonly List<GoalMark> marks = new();
    readonly List<Edge> edges = new();
    readonly List<Vector2> arrowPoints = new();
    const float Inset = 64, FontSize = 18, DiscR = 20;
    static readonly Color Bronze = new("#8a6a3a"), InkPlate = new("#0b0906");
    /// <summary>A part of the screen the edge arrows keep out of (the corner's words), or none.</summary>
    public Rect2? Avoid;
    /// <summary>Where the off-screen arrows sit (the edge marks keep clear of them).</summary>
    public IReadOnlyList<Vector2> ArrowPoints => arrowPoints;

    public GoalMarks() { MouseFilter = MouseFilterEnum.Ignore; }

    public void Show(IEnumerable<GoalMark> list)
    {
        bool had = marks.Count > 0;
        marks.Clear();
        // A pin under the corner's words (the place, the tracker, the map) is drawn as an arrow pointing in under
        // them, from outside them: the words never cover it, nor it the words.
        foreach (var m in list) marks.Add(m.OnScreen && Avoid is Rect2 av && av.HasPoint(m.At) ? m with { OnScreen = false } : m);
        edges.Clear();
        arrowPoints.Clear();
        if (marks.Count > 0)
        {
            var size = GetViewportRect().Size;
            var mid = size / 2;
            var box = new Rect2(Inset, 160, size.X - Inset * 2, size.Y - 160 - 210);
            foreach (var m in marks)
            {
                if (m.OnScreen) continue;
                var d = m.At - mid;
                if (d.LengthSquared() < 1) continue;
                float tx = d.X != 0 ? ((d.X > 0 ? box.End.X : box.Position.X) - mid.X) / d.X : float.MaxValue;
                float ty = d.Y != 0 ? ((d.Y > 0 ? box.End.Y : box.Position.Y) - mid.Y) / d.Y : float.MaxValue;
                var p = mid + d * Mathf.Min(tx, ty);
                // Inside the corner's words: drawn in from them, along the same line from the middle.
                if (Avoid is Rect2 av && av.HasPoint(p) && d.X > 0)
                {
                    float ax = (av.Position.X - 130 - mid.X) / d.X;
                    if (ax > 0) p = mid + d * Mathf.Min(ax, Mathf.Min(tx, ty));
                }
                edges.Add(new Edge(m, p, d.Normalized(), p.Y >= box.End.Y - 1));
                arrowPoints.Add(p);
            }
        }
        if (had || marks.Count > 0) QueueRedraw();
    }

    public override void _Process(double delta)
    {
        // (the bob and the pulse move the marks, so they are redrawn while one is up)
        if (marks.Count > 0) QueueRedraw();
    }

    public override void _Draw()
    {
        if (marks.Count == 0) return;
        var size = GetViewportRect().Size;
        float t = Time.GetTicksMsec() / 1000f;
        float bob = 2 * Mathf.Sin(t * Mathf.Tau / 1.5f);
        foreach (var m in marks)
        {
            if (!m.OnScreen) continue;
            // From the spot up: the ground tick, a 2 px stem, the tail (12 x 11) pointing down, the disc.
            var c = m.Color with { A = 0.9f * m.Alpha };
            var at = m.At;
            var tail = at + new Vector2(0, bob - 6);
            DrawRect(new Rect2(at.X - 1, tail.Y, 2, at.Y - tail.Y), c);
            DrawSetTransform(at, 0, new Vector2(1, 0.4f));
            DrawCircle(Vector2.Zero, 5, c);
            DrawSetTransform(Vector2.Zero);
            DrawColoredPolygon(new[] { tail + new Vector2(-6, -11), tail + new Vector2(6, -11), tail }, c);
            var disc = tail + new Vector2(0, -11 - (DiscR + 3));
            Disc(disc, m.Alpha, m);
            Label(new Vector2(at.X, at.Y + 8), m.Label, c, size, false);
        }
        float pulse = 1 + 0.08f * (0.5f - 0.5f * Mathf.Cos(t * Mathf.Tau / 1.2f));
        foreach (var e in edges)
        {
            var c = e.Mark.Color with { A = 1 };
            var dir = e.Dir;
            var side = new Vector2(-dir.Y, dir.X) * 7;
            // The pointer faces the target: a 14 x 16 triangle, its base 3 px off the disc's rim (which is 3 px thick).
            DrawSetTransform(e.Point, 0, new Vector2(pulse, pulse));
            var bas = dir * (DiscR + 3 + 3);
            DrawColoredPolygon(new[] { bas + dir * 16, bas + side, bas - side }, c);
            Disc(Vector2.Zero, 1, e.Mark);
            DrawSetTransform(Vector2.Zero);
            Label(e.Point + new Vector2(0, e.Bottom ? -(DiscR + 3 + 6) : DiscR + 3 + 6), $"{e.Mark.Label} · {Mathf.RoundToInt(e.Mark.Metres)} m", c, size, e.Bottom);
        }
    }

    /// <summary>The disc: ink, the bronze rim outside (3 px), the goal's colour in a line just inside it (1.5 px), the glyph.</summary>
    void Disc(Vector2 p, float a, GoalMark m)
    {
        var c = m.Color with { A = a };
        DrawCircle(p, DiscR, new Color(0.04f, 0.03f, 0.05f, 0.9f * a));
        DrawArc(p, DiscR - 0.75f, 0, Mathf.Tau, 36, c, 1.5f, true);
        DrawArc(p, DiscR + 1.5f, 0, Mathf.Tau, 40, Bronze with { A = a }, 3, true);
        DrawTextureRect(Glyphs.Texture(m.Glyph, 56, m.Color), new Rect2(p - new Vector2(14, 14), new Vector2(28, 28)), false, Colors.White with { A = a });
    }

    /// <summary>Centered on a point, below it (above it when asked), on a soft ink plate, dark-outlined, kept inside the screen. The colour carries the alpha.</summary>
    void Label(Vector2 at, string text, Color c, Vector2 screen, bool above)
    {
        var font = Style.UiBold;
        var w = font.GetStringSize(text, HorizontalAlignment.Left, -1, (int)FontSize).X;
        float h = font.GetHeight((int)FontSize), asc = font.GetAscent((int)FontSize);
        float x = Mathf.Clamp(at.X - w / 2, 14, screen.X - w - 14);
        float top = Mathf.Clamp(above ? at.Y - h : at.Y, 8, screen.Y - h - 8);
        float a = c.A < 0.95f ? c.A / 0.9f : 1;
        var plate = new StyleBoxFlat { BgColor = InkPlate with { A = 0.6f * a }, CornerRadiusTopLeft = 3, CornerRadiusTopRight = 3, CornerRadiusBottomLeft = 3, CornerRadiusBottomRight = 3 };
        DrawStyleBox(plate, new Rect2(x - 6, top - 3, w + 12, h + 6));
        var y = top + asc;
        DrawStringOutline(font, new Vector2(x, y), text, HorizontalAlignment.Left, -1, (int)FontSize, 2, InkPlate with { A = 0.85f * a });
        DrawString(font, new Vector2(x, y), text, HorizontalAlignment.Left, -1, (int)FontSize, c);
    }
}
