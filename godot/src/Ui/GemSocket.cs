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
            int px = (int)Mathf.Round(44 * s);
            var pic = ItemPhotos.Icon(key, px, GemLook.Of(gem).Lightened(0.25f));
            pic.Position = new Vector2((size - px) / 2f, (size - px) / 2f);
            if (look == Look.Closed)
            {
                // kept but closed: the stone at 45%, drawn toward grey
                var sh = new Shader { Code = "shader_type canvas_item; void fragment(){ vec4 c = texture(TEXTURE, UV); float g = dot(c.rgb, vec3(0.3, 0.59, 0.11)); COLOR = vec4(mix(c.rgb, vec3(g), 0.75), c.a * 0.45); }" };
                pic.Material = new ShaderMaterial { Shader = sh };
            }
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
        // the crescent of light at the top left
        DrawArc(c, r * 0.8f, Mathf.Pi * 1.08f, Mathf.Pi * 1.42f, 14, new Color(1, 1, 1, 0.25f), 3f * Mathf.Max(s, 0.8f), true);
        // the gem's picture sits above (a child); marks
        var cream = new Color("#F2E6C8");
        if (look == Look.Closed)
            DrawTextureRect(Glyphs.Texture("lock", 16, cream with { A = 0.6f }), new Rect2(c - new Vector2(8, 8) + (gem == null ? Vector2.Zero : new Vector2(r * 0.55f, r * 0.55f)), new Vector2(16, 16)), false);
        else if (look == Look.Empty)
            DrawProfile(this, c, 24 * s, cream with { A = 0.35f });
        // the one bezel: bronze 3 px, light at the top left to dark at the bottom right, a 1 px dark line inside
        bool hot = Selected;
        if (hot) for (int i = 6; i >= 1; i--) DrawArc(c, r + 1.5f + i * 0.5f, 0, Mathf.Tau, 48, Style.Ember with { A = 0.07f + 0.02f * (6 - i) }, 1.5f + i, true);
        const int n = 48;
        var pts = new Vector2[n + 1]; var cols = new Color[n + 1];
        var dark = new Color("#8A6A3C"); var lite = new Color("#C9A266");
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
