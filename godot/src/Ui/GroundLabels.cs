using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>A drop's name on the ground: where (on the screen), what it says, its tier's colour, and
/// how loud it is (0 quiet, 1 shown, 2 emphasised, 3 a Legendary's).</summary>
public readonly record struct GroundLabel(Vector2 At, string Text, Color Color, int Loud, bool Set);

/// <summary>
/// Names over loot on the ground (docs/design/LOOT_DESIGN.md §8.1), as the ARPGs label their drops:
/// the item filter decides what is labelled at all, the tier its colour, and the louder ones get a
/// plate, a border and a larger hand. Labels that would overlap stack upward, nearest the ground
/// first, so a boss's hoard reads as a list and never as a smear.
/// </summary>
public partial class GroundLabels : Control
{
    readonly List<GroundLabel> labels = new();

    public GroundLabels() { MouseFilter = MouseFilterEnum.Ignore; }

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
        foreach (var l in labels)
        {
            var font = l.Loud >= 2 ? Style.UiBold : Style.Ui;
            int size = l.Loud switch { >= 3 => 20, 2 => 16, 1 => 14, _ => 13 };
            var text = l.Loud >= 3 ? l.Text.ToUpperInvariant() : l.Text;
            var ts = font.GetStringSize(text, HorizontalAlignment.Left, -1, size);
            float padX = l.Loud >= 2 ? 9 : 6, padY = l.Loud >= 2 ? 4 : 2;
            var box = new Rect2(l.At.X - ts.X / 2 - padX, l.At.Y - ts.Y - padY * 2 - 18, ts.X + padX * 2, ts.Y + padY * 2);
            for (int k = 0; k < 8 && placed.Exists(r => r.Grow(1).Intersects(box)); k++) box.Position -= new Vector2(0, box.Size.Y + 2);
            placed.Add(box);
            // A plate for what is worth reading; a quiet thing is only its words.
            if (l.Loud >= 1) DrawRect(box, new Color(0.04f, 0.035f, 0.045f, l.Loud >= 2 ? 0.86f : 0.7f));
            if (l.Loud >= 2) DrawRect(box, l.Color with { A = 0.9f }, false, l.Loud >= 3 ? 2 : 1);
            // A set's second border: never read by colour alone (UI design; UI art's chain mark to come).
            if (l.Set) DrawRect(box.Grow(-3), l.Color with { A = 0.7f }, false, 1);
            DrawString(font, new Vector2(box.Position.X + padX, box.Position.Y + padY + font.GetAscent(size)), text,
                HorizontalAlignment.Left, -1, size, l.Loud == 0 ? l.Color with { A = 0.8f } : l.Color);
        }
    }
}
