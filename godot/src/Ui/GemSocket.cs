using System;
using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>A gem's well (bd-ui W11): a round seat of dark glass with a bronze bezel, drawn on the Arts page's Skills
/// readout. Closed by rank (a lock, the gem it keeps faint), open and empty (a faint cut-gem outline), or filled (the gem's
/// picture inside a ring in its colour). Selected, the bezel turns ember; hover lifts it to full.</summary>
public partial class GemSocket : Control
{
    public enum Look { Closed, Empty, Filled }

    readonly Look look;
    readonly SupportDef? gem;
    readonly float s;
    public bool Selected;
    bool hover;
    public event Action? Pressed;

    public GemSocket(Look look, SupportDef? gem, int size = 56)
    {
        this.look = look; this.gem = gem; s = size / 56f;
        CustomMinimumSize = new Vector2(size, size);
        SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        MouseFilter = MouseFilterEnum.Ignore;
        if (gem != null && look != Look.Empty)
        {
            string key = Items.Get(Supports.ItemId(gem.Id)).Icon;
            int px = (int)Mathf.Round(44 * s);
            var pic = ItemPhotos.Icon(key, px, GemLook.Of(gem).Lightened(0.25f));
            pic.Position = new Vector2((size - px) / 2f, (size - px) / 2f);
            pic.Modulate = new Color(1, 1, 1, look == Look.Closed ? 0.4f : 1f);
            AddChild(pic);
        }
    }

    /// <summary>Make it a button: the mouse clicks it, the pad presses it (Nav.Mark by the caller).</summary>
    public GemSocket Clickable()
    {
        MouseFilter = MouseFilterEnum.Stop;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        MouseEntered += () => { hover = true; QueueRedraw(); };
        MouseExited += () => { hover = false; QueueRedraw(); };
        return this;
    }

    public void Press() { Pressed?.Invoke(); }

    public override void _GuiInput(InputEvent e)
    {
        if (e is InputEventMouseButton { ButtonIndex: MouseButton.Left, Pressed: true }) { AcceptEvent(); Press(); }
    }

    public override void _Draw()
    {
        var c = Size / 2;
        float r = Size.X / 2 - 1;
        DrawCircle(c, r, new Color("#1d1610") with { A = 0.85f });
        DrawArc(c, r + 0.5f, 0, Mathf.Tau, 48, new Color(0, 0, 0, 0.6f), 1, true);
        var bezel = Selected ? Style.Ember : look == Look.Closed ? Style.Gold with { A = 0.35f } : Style.Gold with { A = hover ? 1f : 0.75f };
        if (Selected && hover) bezel = Style.EmberHi;
        DrawArc(c, r - 1, 0, Mathf.Tau, 48, bezel, Selected ? 2.5f : 2f, true);
        var cream = new Color("#F2E6C8");
        switch (look)
        {
            case Look.Closed:
            {
                int px = Math.Max(12, (int)(16 * Mathf.Max(s, 0.8f)));
                var at = gem == null ? c : c + new Vector2(r * 0.55f, r * 0.55f);
                DrawTextureRect(Glyphs.Texture("lock", px, cream with { A = 0.3f }), new Rect2(at - new Vector2(px, px) / 2, new Vector2(px, px)), false);
                break;
            }
            case Look.Empty:
            {
                // (no gem glyph in glyphs.json: a hexagonal cut with its table line)
                float hr = 12 * s;
                var pts = new Vector2[7];
                for (int i = 0; i < 7; i++) { float a = Mathf.Pi / 6 + i * Mathf.Tau / 6; pts[i] = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * hr; }
                var line = cream with { A = 0.25f };
                DrawPolyline(pts, line, 1.5f, true);
                DrawLine(pts[1], pts[5], line, 1f, true);
                DrawLine(pts[2], c, line, 1f, true); DrawLine(pts[4], c, line, 1f, true);
                break;
            }
            case Look.Filled:
                if (gem != null) DrawArc(c, r - 3.5f, 0, Mathf.Tau, 48, GemLook.Of(gem), 1.5f, true);
                break;
        }
    }
}
