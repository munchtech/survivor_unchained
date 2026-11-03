using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>Where a goal is on the screen's plane, whether it can be seen there, and how far.</summary>
public readonly record struct GoalMark(Vector2 At, bool OnScreen, string Glyph, Color Color, string Label, float Metres);

/// <summary>
/// The goals on the ground: a pin over the spot (with its name under, bobbing a little) while it is
/// on screen, and a larger arrow at the screen's edge, with its name and distance, when it is not.
/// </summary>
public partial class GoalMarks : Control
{
    readonly List<GoalMark> marks = new();
    const float Inset = 64, FontSize = 18;
    /// <summary>A part of the screen the edge arrows keep out of (the corner's words), or none.</summary>
    public Rect2? Avoid;

    public GoalMarks() { MouseFilter = MouseFilterEnum.Ignore; }

    public void Show(IEnumerable<GoalMark> list)
    {
        bool had = marks.Count > 0;
        marks.Clear();
        marks.AddRange(list);
        if (had || marks.Count > 0) QueueRedraw();
    }

    public override void _Process(double delta)
    {
        // (the bob moves the pin, so it is redrawn while one is up)
        if (marks.Count > 0) QueueRedraw();
    }

    public override void _Draw()
    {
        if (marks.Count == 0) return;
        var size = GetViewportRect().Size;
        var mid = size / 2;
        var box = new Rect2(Inset, 160, size.X - Inset * 2, size.Y - 160 - 210);
        float bob = 2 * Mathf.Sin(Time.GetTicksMsec() / 1000f * Mathf.Tau / 1.5f);
        foreach (var m in marks)
        {
            if (m.OnScreen)
            {
                var p = m.At + new Vector2(0, bob - 22);
                var c = m.Color with { A = 0.9f };
                // The tail under the disc, pointing down at the spot.
                DrawColoredPolygon(new[] { p + new Vector2(-9, 16), p + new Vector2(9, 16), p + new Vector2(0, 30) }, c);
                Disc(p, 0.9f, m);
                Label(p + new Vector2(0, 34), m.Label, c, size);
            }
            else
            {
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
                var dir = d.Normalized();
                var c = m.Color with { A = 1 };
                var tip = p + dir * 38;
                var side = new Vector2(-dir.Y, dir.X) * 11;
                DrawColoredPolygon(new[] { tip, p + dir * 18 + side, p + dir * 18 - side }, c);
                Disc(p, 1, m);
                Label(p + new Vector2(0, 30), $"{m.Label} · {Mathf.RoundToInt(m.Metres)} m", c, size);
            }
        }
    }

    void Disc(Vector2 p, float a, GoalMark m)
    {
        var c = m.Color with { A = a };
        DrawCircle(p, 20, new Color(0.04f, 0.03f, 0.05f, 0.9f * a));
        DrawArc(p, 20, 0, Mathf.Tau, 36, c, 3, true);
        DrawTextureRect(Glyphs.Texture(m.Glyph, 56, m.Color), new Rect2(p - new Vector2(14, 14), new Vector2(28, 28)), false, Colors.White with { A = a });
    }

    /// <summary>Centered under a point, dark-outlined, kept inside the screen.</summary>
    void Label(Vector2 at, string text, Color c, Vector2 screen)
    {
        var font = Style.UiBold;
        var w = font.GetStringSize(text, HorizontalAlignment.Left, -1, (int)FontSize).X;
        float x = Mathf.Clamp(at.X - w / 2, 8, screen.X - w - 8), y = Mathf.Clamp(at.Y + FontSize * 0.8f, FontSize + 8, screen.Y - 12);
        DrawStringOutline(font, new Vector2(x, y), text, HorizontalAlignment.Left, -1, (int)FontSize, 5, new Color(0.03f, 0.02f, 0.04f, 0.95f));
        DrawString(font, new Vector2(x, y), text, HorizontalAlignment.Left, -1, (int)FontSize, c);
    }
}
