using System;
using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>A gem's well (bd-ui W11): a round seat of dark glass with a bronze bezel, drawn on the Arts page's Skills
/// readout. Closed by rank (a lock, the gem it keeps faint), open and empty (a faint cut-gem outline), or filled (the gem's
/// picture over a faint glow in its colour). One bronze bezel always; selected, it turns ember with a soft glow.</summary>
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
            // the stone is about 71% of its picture across: a 56 px picture shows it 40 x 30 in a 56 px well
            // (the stone cropped to its edge and resized once, crisp: judge round 2 measured the downscaled picture's stone 30 x 22)
            int bw = (int)Mathf.Round(40 * s), bh = (int)Mathf.Round(30 * s);
            var pic = ItemPhotos.StoneIcon(key, bw, bh, size, GemLook.Of(gem).Lightened(0.25f));
            pic.Position = Vector2.Zero;
            if (look == Look.Closed)
            {
                // kept but closed: the stone at 40% value and 40% saturation
                var sh = new Shader { Code = "shader_type canvas_item; void fragment(){ vec4 c = texture(TEXTURE, UV); float g = dot(c.rgb, vec3(0.3, 0.59, 0.11)); COLOR = vec4(mix(vec3(g), c.rgb, 0.4) * 0.4, c.a); }" };
                pic.Material = new ShaderMaterial { Shader = sh };
                if (pic.GetChildCount() > 0 && pic.GetChild(0) is CanvasItem ci) ci.UseParentMaterial = true;
            }
            AddChild(pic);
        }
        if (look == Look.Closed)
        {
            // the lock, 16 px of ink (a 24 px glyph box) at 70%, centred (above a kept stone)
            var lk = new TextureRect { Texture = Glyphs.Texture("lock", 24, new Color("#F2E6C8") with { A = 0.7f }), MouseFilter = MouseFilterEnum.Ignore, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, Size = new Vector2(24, 24) };
            lk.Position = new Vector2((size - 24) / 2f, (size - 24) / 2f);
            AddChild(lk);
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

    /// <summary>A Union's read-only well: no pointer, bezel at 60% (it must not look clickable).</summary>
    public GemSocket ReadOnly() { dim = true; return this; }
    bool dim;

    /// <summary>A brilliant cut seen from the side: a crown trapezoid over a pavilion triangle, with its facet lines.</summary>
    public static void DrawProfile(CanvasItem ci, Vector2 c, float w, Color ink, float line = 1.2f)
    {
        Vector2 P(float x, float y) => c + new Vector2(x, y) * w;
        var outline = new[] { P(-.3f, -.36f), P(.3f, -.36f), P(.5f, -.08f), P(0, .44f), P(-.5f, -.08f), P(-.3f, -.36f) };
        ci.DrawPolyline(outline, ink, line, true);
        ci.DrawLine(P(-.5f, -.08f), P(.5f, -.08f), ink, line, true);
        ci.DrawLine(P(-.3f, -.36f), P(-.14f, -.08f), ink, line * .8f, true); ci.DrawLine(P(.3f, -.36f), P(.14f, -.08f), ink, line * .8f, true);
        ci.DrawLine(P(-.14f, -.08f), P(0, .44f), ink, line * .8f, true); ci.DrawLine(P(.14f, -.08f), P(0, .44f), ink, line * .8f, true);
    }

    public override void _Draw()
    {
        var c = Size / 2;
        float r = Size.X / 2 - 3;
        float k = dim ? 0.6f : 1f;
        // the gem's colour as a faint glow behind the stone (25%)
        if (look == Look.Filled && gem != null)
        {
            var gc = GemLook.Of(gem);
            for (int i = 0; i < 5; i++) DrawCircle(c, r * (0.95f - i * 0.14f), gc with { A = 0.05f });
        }
        // interior: radial dark glass, lighter toward the middle
        var edge = new Color("#0C0A09"); var mid = new Color("#2A231D");
        const int steps = 10;
        for (int i = 0; i < steps; i++)
        {
            float t = i / (float)(steps - 1);
            DrawCircle(c + new Vector2(-r * 0.08f, -r * 0.08f) * t, r * (1 - t * 0.9f), edge.Lerp(mid, t));
        }
        // a soft radial highlight at the top left: 0 -> 18% white, feathered 6 px (open wells only)
        if (look != Look.Closed)
        {
            var hc = c + new Vector2(-r * 0.3f, -r * 0.32f); float hr = r * 0.42f;
            float per = 1f - Mathf.Pow(1f - 0.18f, 1f / 6f);
            for (int i = 0; i < 6; i++) DrawCircle(hc, hr - i, new Color(1, 1, 1, per));
        }
        var cream = new Color("#F2E6C8");
        if (look == Look.Empty)
            DrawProfile(this, c, 24 * s, cream with { A = 0.35f });
        // the one bezel: bronze 3 px, light at the top left to dark at the bottom right, a 1 px dark line inside
        bool hot = Selected;
        if (hot) for (int i = 6; i >= 1; i--) DrawArc(c, r + 1.5f + i * 0.5f, 0, Mathf.Tau, 48, Style.Ember with { A = 0.07f + 0.02f * (6 - i) }, 1.5f + i, true);
        const int n = 48;
        var pts = new Vector2[n + 1]; var cols = new Color[n + 1];
        var dark = look == Look.Closed ? new Color("#4A4440") : new Color("#8A6A3C"); var lite = look == Look.Closed ? new Color("#6A625A") : new Color("#C9A266");
        float hl = hover && !hot ? 0.18f : 0;
        for (int i = 0; i <= n; i++)
        {
            float a = i * Mathf.Tau / n;
            pts[i] = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * (r + 0.5f);
            float lit = 0.5f - 0.5f * Mathf.Cos(a - Mathf.Pi * 1.25f); // 0 at the top left
            var col = hot ? Style.Ember : lite.Lerp(dark, lit).Lightened(hl);
            if (hot && hover) col = Style.EmberHi;
            cols[i] = col with { A = col.A * k };
        }
        DrawPolylineColors(pts, cols, 3, true);
        DrawArc(c, r - 1.5f, 0, Mathf.Tau, 48, new Color(0, 0, 0, 0.7f), 1, true);
    }
}
