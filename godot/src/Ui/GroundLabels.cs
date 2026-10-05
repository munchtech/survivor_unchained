using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>A drop's name on the ground: where (on the screen), what it says, its tier's colour, and
/// how loud it is (0 quiet, 1 shown, 2 emphasised, 3 a Legendary's).</summary>
public readonly record struct GroundLabel(Vector2 At, string Text, Color Color, int Loud, bool Set);

/// <summary>
/// Names over loot on the ground (docs/design/LOOT_DESIGN.md §8.1), as the ARPGs label their drops:
/// the item filter decides what is labelled at all, the tier its colour, and the louder ones a larger
/// hand and a light of their own. Set as type on the world, the same family as the notices (the
/// owner: "transparent and stylized"): a dark outline and shadow under every letter keep it legible
/// over cobbles and grass, with no plate. A set's name carries the chain-link before it; a
/// Legendary's is in display capitals in amber light. Labels that would overlap stack upward, nearest
/// the ground first, so a boss's hoard reads as a list and never as a smear.
/// </summary>
public partial class GroundLabels : Control
{
    readonly List<GroundLabel> labels = new();
    static GradientTexture2D? soft;

    public GroundLabels()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        soft ??= new GradientTexture2D
        {
            Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
            Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.5f, 1f } },
        };
    }

    /// <summary>Where the HUD's words are this frame (a tip, the corner, the notices, a banner): a label
    /// that would fall on one gives way to it, faint, and never runs through its words.</summary>
    public readonly List<Rect2> KeepOut = new();

    public void Show(IEnumerable<GroundLabel> list)
    {
        labels.Clear();
        labels.AddRange(list);
        QueueRedraw();
    }

    public override void _Draw()
    {
        // Lowest on the screen first: they are nearest the camera's ground and keep their place.
        labels.Sort((a, b) => b.At.Y.CompareTo(a.At.Y));
        var placed = new List<Rect2>();
        var link = UiArt.Icon("glyph", "link_set_14");
        foreach (var l in labels)
        {
            bool grand = l.Loud >= 3;
            var font = grand ? Style.Display : l.Loud >= 1 ? Style.UiBold : Style.Ui;
            int size = l.Loud switch { >= 3 => 21, 2 => 17, 1 => 15, _ => 14 };
            var text = grand ? l.Text.ToUpperInvariant() : l.Text;
            var ts = font.GetStringSize(text, HorizontalAlignment.Left, -1, size);
            float markW = l.Set ? 18 : 0;
            var box = new Rect2(l.At.X - (ts.X + markW) / 2, l.At.Y - ts.Y - 20, ts.X + markW, ts.Y + 2);
            for (int k = 0; k < 8 && placed.Exists(r => r.Grow(2).Intersects(box)); k++) box.Position -= new Vector2(0, box.Size.Y + 3);
            // Still on another after stepping up (a heap): left unsaid rather than written over it.
            if (placed.Exists(r => r.Grow(1).Intersects(box))) continue;
            placed.Add(box);
            // Under the HUD's own words it gives way: faint, and its light not drawn.
            bool under = KeepOut.Exists(r => r.Intersects(box.Grow(4)));
            if (under) { DrawString(font, new Vector2(box.Position.X + (l.Set ? 18 : 0), box.Position.Y + font.GetAscent(size)), text, HorizontalAlignment.Left, -1, size, l.Color with { A = 0.14f }); continue; }
            // A soft shade under the words (no shape), and for what matters a light of its colour.
            DrawTextureRect(soft!, box.Grow(l.Loud >= 2 ? 16 : 10), false, new Color(0, 0, 0, l.Loud >= 1 ? 0.5f : 0.3f));
            if (l.Loud >= 2) DrawTextureRect(soft!, box.Grow(grand ? 30 : 18), false, l.Color with { A = grand ? 0.3f : 0.16f });
            var at = new Vector2(box.Position.X + markW, box.Position.Y + font.GetAscent(size));
            if (l.Set)
            {
                var r = new Rect2(box.Position.X, box.Position.Y + (box.Size.Y - 14) / 2, 14, 14);
                if (link != null) DrawTextureRect(link, r, false, l.Color);
                else DrawArc(r.GetCenter(), 5, 0, Mathf.Tau, 16, l.Color, 2, true);
            }
            int outline = grand ? 6 : 5;
            DrawStringOutline(font, at + new Vector2(0, 2), text, HorizontalAlignment.Left, -1, size, outline + 2, new Color(0, 0, 0, 0.45f));
            DrawStringOutline(font, at, text, HorizontalAlignment.Left, -1, size, outline, new Color(0.03f, 0.02f, 0.02f, 0.85f));
            DrawString(font, at, text, HorizontalAlignment.Left, -1, size, l.Loud == 0 ? l.Color with { A = 0.82f } : l.Color);
        }
    }
}
