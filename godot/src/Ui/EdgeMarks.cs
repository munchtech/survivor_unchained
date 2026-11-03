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
    /// <summary>Points these marks keep clear of (the goal's arrow): slid along the border, never drawn on them.</summary>
    public List<Vector2> Keep = new();

    public EdgeMarks() { MouseFilter = MouseFilterEnum.Ignore; }

    static GradientTexture2D? soft;

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
            p = Clear(p, box);
            var dir = d.Normalized();
            float a = Mathf.Lerp(0.7f, 1f, m.Near);
            var c = m.Color with { A = a };
            // A Legendary lying untaken: UI art's amber chevron, turned to point at it, breathing with
            // the pillar's light, its glow thrown round it (docs/design/LOOT_DESIGN.md §8.2).
            if (m.Glyph == "legendary" && UiArt.Art("hud/pointer_legendary.png") is { } chevron)
            {
                float t = Time.GetTicksMsec() / 1000f, breath = 0.85f + 0.15f * Mathf.Sin(t * 3.2f);
                var s = chevron.GetSize() * (1.4f + 0.1f * Mathf.Sin(t * 3.2f));
                // (a soft light, never a disc with an edge)
                soft ??= new GradientTexture2D
                {
                    Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
                    Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.45f, 1f } },
                };
                DrawTextureRect(soft, new Rect2(p - new Vector2(46, 46), new Vector2(92, 92)), false, m.Color with { A = 0.4f * breath });
                DrawSetTransform(p, dir.Angle());
                DrawTextureRect(chevron, new Rect2(-s / 2, s), false, Colors.White with { A = breath });
                DrawSetTransform(Vector2.Zero);
                QueueRedraw();
                continue;
            }
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

    /// <summary>A border point slid along the border, away from any kept point nearer than 56 px.</summary>
    Vector2 Clear(Vector2 p, Rect2 box)
    {
        for (int pass = 0; pass < 4; pass++)
        {
            Vector2? near = null;
            foreach (var k in Keep) if (p.DistanceTo(k) < 56) { near = k; break; }
            if (near is not Vector2 kp) break;
            // The side of the box the point lies on: the tangent runs along it.
            float dl = Mathf.Abs(p.X - box.Position.X), dr = Mathf.Abs(p.X - box.End.X), dt = Mathf.Abs(p.Y - box.Position.Y), db = Mathf.Abs(p.Y - box.End.Y);
            float least = Mathf.Min(Mathf.Min(dl, dr), Mathf.Min(dt, db));
            var normal = least == dl ? Vector2.Right : least == dr ? Vector2.Left : least == dt ? Vector2.Down : Vector2.Up;
            var tangent = new Vector2(-normal.Y, normal.X);
            float away = (p - kp).Dot(tangent);
            if (Mathf.Abs(away) < 0.01f) away = 1;
            var dirAway = tangent * Mathf.Sign(away);
            // Far enough along the tangent that the distance is 56 (the other offset is across the border).
            float across = (p - kp).Dot(normal);
            float along = Mathf.Sqrt(Mathf.Max(0, 56 * 56 - across * across));
            var q = kp + normal * across + dirAway * (along + 0.5f);
            q = new Vector2(Mathf.Clamp(q.X, box.Position.X, box.End.X), Mathf.Clamp(q.Y, box.Position.Y, box.End.Y));
            // Clamped into a corner, short of 56: slide the other way instead.
            if (q.DistanceTo(kp) < 56)
            {
                q = kp + normal * across - dirAway * (along + 0.5f);
                q = new Vector2(Mathf.Clamp(q.X, box.Position.X, box.End.X), Mathf.Clamp(q.Y, box.Position.Y, box.End.Y));
            }
            p = q;
        }
        return p;
    }
}
