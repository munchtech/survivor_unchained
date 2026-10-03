using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>Something that matters, off the screen: where it is (on the
/// screen's plane), what it is, and how near.</summary>
public readonly record struct Beyond(Vector2 At, string Glyph, Color Color, float Near);

/// <summary>
/// Arrows at the screen's edge for what matters and cannot be seen (the
/// thing that rules an arena, elites, chests): a survivors-like's way of
/// saying "there is something over there" without a minimap. Each sits where
/// the line from the middle of the screen to the thing crosses an inset
/// border, points outward, carries its glyph, and fades with distance.
/// </summary>
public partial class EdgeMarks : Control
{
    readonly List<Beyond> marks = new();
    const float Inset = 64;

    public EdgeMarks() { MouseFilter = MouseFilterEnum.Ignore; }

    public void Show(IEnumerable<Beyond> list)
    {
        marks.Clear();
        marks.AddRange(list);
        QueueRedraw();
    }

    public override void _Draw()
    {
        var size = GetViewportRect().Size;
        var mid = size / 2;
        // Inside the HUD's bands: below the clock and the corner's words, above the skills and hands.
        var box = new Rect2(Inset, 160, size.X - Inset * 2, size.Y - 160 - 210);
        foreach (var m in marks)
        {
            var d = m.At - mid;
            if (d.LengthSquared() < 1) continue;
            // Where the line from the middle meets the border.
            float tx = d.X != 0 ? ((d.X > 0 ? box.End.X : box.Position.X) - mid.X) / d.X : float.MaxValue;
            float ty = d.Y != 0 ? ((d.Y > 0 ? box.End.Y : box.Position.Y) - mid.Y) / d.Y : float.MaxValue;
            var p = mid + d * Mathf.Min(tx, ty);
            var dir = d.Normalized();
            float a = Mathf.Lerp(0.7f, 1f, m.Near);
            var c = m.Color with { A = a };
            // The arrow, pointing out.
            var tip = p + dir * 30;
            var side = new Vector2(-dir.Y, dir.X) * 9;
            DrawColoredPolygon(new[] { tip, p + dir * 14 + side, p + dir * 14 - side }, c);
            // The disc with its glyph.
            DrawCircle(p, 17, new Color(0.04f, 0.03f, 0.05f, 0.9f * a));
            DrawArc(p, 17, 0, Mathf.Tau, 32, c, 2.5f, true);
            var tex = Glyphs.Texture(m.Glyph, 48, m.Color);
            DrawTextureRect(tex, new Rect2(p - new Vector2(12, 12), new Vector2(24, 24)), false, Colors.White with { A = a });
        }
    }
}
