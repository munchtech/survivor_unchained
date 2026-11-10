using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The damage numbers on the HUD's canvas (M4 lead 6). They were Label3Ds in the world: the day's grade and the
/// tonemap warmed bone to peach and white to cream (measured (245,180,140) and (254,211,180) by day), and her strap
/// (HerLight.Under, on the HUD) drew over them. Now a number is a place in the world and what it says (Num), and the
/// Sheet draws each at that place's point on screen, at the size the Label3D had there, after the grade and in its own
/// colours by day and by night: bone at 85% is bone at 85%. The Sheet stands in the HUD over the strap and the
/// ground's names and under the HUD's own parts (GameHud.NumberHost); with no HUD (a tool's scene) on a layer of its own.
/// </summary>
public partial class Hits
{
    /// <summary>One number of the pool: where it stands in the world, and what the Sheet draws there.</summary>
    public sealed class Num
    {
        public Vector3 GlobalPosition;
        /// <summary>(Hits stands at the world's origin: a number's place is the world's.)</summary>
        public Vector3 Position { get => GlobalPosition; set => GlobalPosition = value; }
        public string Text = "";
        public int FontSize = 64;
        public Color Modulate = Colors.White, OutlineModulate = new("#0b0906");
        /// <summary>A crit's punch (1.35 easing to 1 over 0.08 s).</summary>
        public float Scale = 1;
        public bool Visible;
    }

    /// <summary>The Long Cut's total (Total): white-gold.</summary>
    static readonly Color TotalGold = new("#ffe9a8");

    Sheet? sheet;
    CanvasLayer? ownLayer;
    bool sheetLive;

    /// <summary>Each frame: the Sheet kept where it belongs and redrawn while a number shows (and once after the last).</summary>
    void SheetFrame(bool live)
    {
        if (!live && !sheetLive) return;
        if (sheet == null || !IsInstanceValid(sheet)) sheet = new Sheet(this);
        Node? host = SurvivorUnchained.Ui.GameHud.NumberHost;
        if (host == null || !IsInstanceValid(host))
        {
            if (ownLayer == null || !IsInstanceValid(ownLayer)) { ownLayer = new CanvasLayer { Layer = 10, Name = "HitNumbers" }; AddChild(ownLayer); }
            host = ownLayer;
        }
        var at = sheet.GetParent();
        if (at != host)
        {
            at?.RemoveChild(sheet);
            host.AddChild(sheet);
        }
        sheetLive = live;
        sheet.QueueRedraw();
    }

    public override void _ExitTree()
    {
        if (sheet != null && IsInstanceValid(sheet)) sheet.QueueFree();
        sheet = null;
    }

    /// <summary>Where she stands (her feet, on the ground, as drawn: WorldScene sets it each frame); null where there is
    /// no heroine (a tool's scene): then only the strap is kept clear.</summary>
    public Vector3? HerFeet;
    /// <summary>Her box in the world, for the numbers: her height with her hair (m), half her width with her arms and
    /// shield (m, along the camera's right), and how far her boots stand toward the camera of her feet's point (m).</summary>
    const float HerTall = 1.85f, HerHalf = 0.35f, HerToe = 0.15f;

    /// <summary>Her body's rect on screen now: her feet's point and her head's (feet + HerTall up) projected, HerHalf
    /// to each side at her middle's depth; null without her or with her behind the camera. Projected, not fixed px:
    /// it holds at any resolution and zoom.</summary>
    Rect2? HerBox(Camera3D cam)
    {
        if (HerFeet is not Vector3 f || cam.IsPositionBehind(f)) return null;
        Vector2 feet = cam.UnprojectPosition(f), head = cam.UnprojectPosition(f + Vector3.Up * HerTall);
        var mid = f + Vector3.Up * (HerTall / 2);
        float half = (cam.UnprojectPosition(mid + cam.GlobalBasis.X * HerHalf) - cam.UnprojectPosition(mid)).Length();
        // (her toes: the ground a boot's length toward the camera of her feet's point)
        var toCam = cam.GlobalPosition - f; toCam.Y = 0;
        float toe = toCam.LengthSquared() > 1e-6f ? cam.UnprojectPosition(f + toCam.Normalized() * HerToe).Y : feet.Y;
        float x0 = Mathf.Min(feet.X, head.X) - half, x1 = Mathf.Max(feet.X, head.X) + half;
        float y0 = Mathf.Min(feet.Y, head.Y), y1 = Mathf.Max(Mathf.Max(feet.Y, head.Y), toe);
        return new Rect2(x0, y0, x1 - x0, y1 - y0);
    }

    /// <summary>A number that would start on her (her body: head, torso, legs; or the strap under her), or lift into
    /// either in its first 0.3 s, starts beside her instead (HitsPlace.HerNudge: sideways, to the side of her centre
    /// line it is on, clear of both at once). Every number goes through it (Show, Reclear): the foes' she strikes and
    /// the red one for a blow she takes. M4 lead 6: at 1:1 in a crowd they were drawn on her head and torso, and she
    /// is hard enough to find. The strap hidden, her body is still kept clear; without her, the strap alone.</summary>
    Vector3 BesideHer(Vector3 at, string text, int size)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null) return at;
        Rect2? body = HerBox(cam), strap = SurvivorUnchained.Ui.HerLight.Live?.Under.OnScreen;
        if (body == null && strap == null) return at;
        if (NumBox(cam, at, text, size) is not Rect2 b) return at;
        float rise = cam.UnprojectPosition(at).Y - cam.UnprojectPosition(at + Vector3.Up * (float)HitsPlace.RiseIn(HitsPlace.Young)).Y;
        // (the gaps are px at 1080)
        float k = GetViewport().GetVisibleRect().Size.Y / 1080f;
        float herX = (body ?? strap)!.Value.GetCenter().X;
        static HitsPlace.Box? B(Rect2? r) => r is Rect2 q ? new HitsPlace.Box(q.Position.X, q.Position.Y, q.End.X, q.End.Y) : null;
        float dx = HitsPlace.HerNudge(B(b)!.Value, rise, herX, B(body), B(strap), out int hit, HitsPlace.BodyGap * k, HitsPlace.StrapGap * k);
        if (dx == 0) return at;
        if (herShots++ < 12)
        {
            string on = hit == (HitsPlace.HitBody | HitsPlace.HitStrap) ? "body and strap" : hit == HitsPlace.HitBody ? "body" : "strap";
            static string R(Rect2? r) => r is Rect2 q ? $"({q.Position.X:0},{q.Position.Y:0} {q.Size.X:0}x{q.Size.Y:0})" : "(none)";
            GD.Print($"hits: number '{text}' size {size} box {R(b)} rising {rise:0} px moved {dx:0} px clear of her {on}: body {R(body)} strap {R(strap)}");
        }
        float depth = (at - cam.GlobalPosition).Dot(-cam.GlobalBasis.Z);
        var c = b.GetCenter();
        return cam.ProjectPosition(new Vector2(c.X + dx, c.Y), depth);
    }

    static int herShots;

    /// <summary>Draws the pool's numbers on the canvas: each at its place's point on screen, its text's middle there,
    /// at the Label3D's size (a font px is NumPixel metres at its depth), outline first.</summary>
    public sealed partial class Sheet : Control
    {
        readonly Hits hits;
        Font? font;

        public Sheet(Hits hits)
        {
            this.hits = hits;
            Name = "HitNumbers";
            MouseFilter = MouseFilterEnum.Ignore;
            SetAnchorsPreset(LayoutPreset.FullRect);
        }

        public override void _Draw()
        {
            if (!IsInstanceValid(hits) || !hits.IsVisibleInTree()) return;
            var cam = GetViewport()?.GetCamera3D();
            if (cam == null) return;
            font ??= ThemeDB.FallbackFont;
            // (screen px to this control's own: the host stands unscaled at the screen's corner, but not by contract)
            var inv = GetGlobalTransform().AffineInverse();
            var up = cam.GlobalBasis.Y;
            foreach (var (n, t) in hits.numbers)
            {
                if (t >= 1 || !n.Visible || n.Text.Length == 0 || n.Modulate.A <= 0.004f || cam.IsPositionBehind(n.GlobalPosition)) continue;
                var p = cam.UnprojectPosition(n.GlobalPosition);
                // screen px per font px here (over 100 font px, for the float's sake)
                float per = (cam.UnprojectPosition(n.GlobalPosition + up * (100 * NumPixel)) - p).Length() / 100f;
                float px = n.FontSize * per;
                if (px < 4) continue;
                // (the face is cut at a whole even size, a handful of sizes in the cache, and the rest is the transform's)
                int fs = Mathf.Max(8, Mathf.RoundToInt(px / 2) * 2);
                float s = px / fs * n.Scale;
                int ol = Mathf.Max(1, Mathf.RoundToInt(NumOutline * per * fs / px));
                var size = font.GetStringSize(n.Text, HorizontalAlignment.Left, -1, fs);
                var o = new Vector2(-size.X / 2, (font.GetAscent(fs) - font.GetDescent(fs)) / 2);
                DrawSetTransform(inv * p, 0, new Vector2(s, s));
                DrawStringOutline(font, o, n.Text, HorizontalAlignment.Left, -1, fs, ol, n.OutlineModulate);
                DrawString(font, o, n.Text, HorizontalAlignment.Left, -1, fs, n.Modulate);
            }
            DrawSetTransform(Vector2.Zero, 0, Vector2.One);
        }
    }
}
