using System;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (the game's HUD), round 2: what the meters share. The rings' cooldown as a well that fills
/// from its foot (the part come back lit in the skill's element, a soft meniscus, the rest dark: no line across it,
/// which read as a strike-through), the seconds as gold numerals cut in the bronze, the ranks engraved (round 3), a
/// soft disc for the element's light in the well's glass, and the passives as beads threaded on the crest (round 3).
/// </summary>
public static partial class DgMeters
{
    static ImageTexture? disc;
    /// <summary>A white disc that falls off softly to its edge (64 px), to tint with a draw's modulate.</summary>
    public static Texture2D Disc
    {
        get
        {
            if (disc != null) return disc;
            const int n = 64;
            var im = Image.CreateEmpty(n, n, false, Image.Format.Rgba8);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float d = new Vector2(x + 0.5f - n / 2f, y + 0.5f - n / 2f).Length() / (n / 2f);
                    float a = Mathf.Clamp(1 - d, 0, 1);
                    im.SetPixel(x, y, new Color(1, 1, 1, a * a * (3 - 2 * a)));
                }
            disc = ImageTexture.CreateFromImage(im);
            return disc;
        }
    }

    /// <summary>A well of radius r at c coming back (ready 0..1): above what has come back the well is dark; below
    /// it the glass is lit in the element (tint), brightest at its surface and fading to the foot, so the eye reads a
    /// level rising, not a line drawn across.</summary>
    public static void Level(CanvasItem ci, Vector2 c, float r, float ready, Color tint)
    {
        ready = Math.Clamp(ready, 0, 1);
        float yCut = -r + 2 * r * (1 - ready);
        // the dark: from the top of the well down to the surface
        if (ready < 0.995f)
        {
            const int n = 40;
            var pts = new Vector2[n + 1];
            float a0 = Mathf.Asin(Mathf.Clamp(yCut / r, -1, 1));
            for (int k = 0; k <= n; k++)
            {
                float a = a0 + (-Mathf.Pi - 2 * a0) * k / n;
                pts[k] = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r;
            }
            ci.DrawColoredPolygon(pts, new Color(0.010f, 0.010f, 0.016f, 0.80f));
        }
        if (ready <= 0.01f) return;
        // the lit glass: rows from the surface to the foot, each quad its own colours (bright at the surface)
        var lit = new Color(0.55f, 0.85f, 0.80f).Lerp(tint, 0.65f);
        float depth = r - yCut;
        int rows = Math.Max(2, (int)Math.Ceiling(depth / 2));
        float HalfW(float y) => Mathf.Sqrt(Mathf.Max(0, r * r - y * y));
        var quad = new Vector2[4];
        var cols = new Color[4];
        for (int i = 0; i < rows; i++)
        {
            float y0 = yCut + depth * i / rows, y1 = yCut + depth * (i + 1) / rows;
            float u0 = (y0 - yCut) / Math.Max(1, depth), u1 = (y1 - yCut) / Math.Max(1, depth);
            // (the surface's first 3 px a meniscus, then a slow fade to the foot)
            float Alpha(float y, float u) => 0.05f + 0.11f * (1 - u) + 0.26f * Mathf.Exp(-(y - yCut) / 2.0f);
            float h0 = HalfW(y0), h1 = HalfW(y1);
            quad[0] = c + new Vector2(-h0, y0); quad[1] = c + new Vector2(h0, y0);
            quad[2] = c + new Vector2(h1, y1); quad[3] = c + new Vector2(-h1, y1);
            cols[0] = cols[1] = lit with { A = Alpha(y0, u0) };
            cols[2] = cols[3] = lit with { A = Alpha(y1, u1) };
            ci.DrawPolygon(quad, cols);
        }
    }

    /// <summary>A numeral cut in the bronze: gold, a dark carved outline and a soft drop, centred on at (its caps'
    /// middle).</summary>
    public static void Numeral(CanvasItem ci, Vector2 at, string s, int size, Color gold, float outline = 3)
    {
        var f = Vessel.Figures;
        var ts = f.GetStringSize(s, HorizontalAlignment.Left, -1, size);
        var p = new Vector2(Mathf.Round(at.X - ts.X / 2), Mathf.Round(at.Y + 0.33f * size));
        ci.DrawStringOutline(f, p + new Vector2(0.5f, 1.2f), s, HorizontalAlignment.Left, -1, size, (int)outline + 3, new Color(0, 0, 0, 0.35f));
        ci.DrawStringOutline(f, p, s, HorizontalAlignment.Left, -1, size, (int)outline, new Color(0.035f, 0.025f, 0.015f, 0.92f));
        ci.DrawString(f, p, s, HorizontalAlignment.Left, -1, size, gold);
        // (a hair of light along the figure's top: the gold's lit edge)
        ci.DrawString(f, p + new Vector2(0, -0.6f), s, HorizontalAlignment.Left, -1, size, new Color(1f, 0.95f, 0.8f, 0.28f));
    }

    public static readonly Color Gold = new(0.93f, 0.77f, 0.45f), GoldDull = new(0.62f, 0.52f, 0.36f);

    /// <summary>A numeral engraved in the bronze (round 3, the seats' ranks: a different kind of thing from the key
    /// tags' dark plates and pale letters): a small polished boss on the ring, lit from above, the figure cut into it
    /// dark, the cut's lower wall catching the light (a lit edge a pixel below). hot: the boss polished to gold (ripe
    /// to evolve, or evolved).</summary>
    public static void Engrave(CanvasItem ci, Vector2 at, string s, int size, bool hot)
    {
        var f = Vessel.Figures;
        var ts = f.GetStringSize(s, HorizontalAlignment.Left, -1, size);
        // the boss: a rounded tablet, its shadow, its face graded light to dark down it, a hair of light on its top
        float w = Mathf.Max(13, ts.X + 6), h = size + 2;
        var r = new Rect2(at - new Vector2(w, h) / 2, new Vector2(w, h));
        var sb = new StyleBoxFlat { BgColor = new Color(0, 0, 0, 0.55f), CornerRadiusTopLeft = 5, CornerRadiusTopRight = 5, CornerRadiusBottomLeft = 5, CornerRadiusBottomRight = 5, AntiAliasing = true };
        ci.DrawStyleBox(sb, r.Grow(1.2f) with { Position = r.Position + new Vector2(-1.0f, -0.6f) });
        // (UI 18: the bronze's fills through round 3's grade, dg_figure_cut.bronze_pass on a flat colour; hot stays polished gold)
        sb.BgColor = new Color(0.280f, 0.221f, 0.138f);
        ci.DrawStyleBox(sb, r);
        sb.BgColor = hot ? new Color(0.98f, 0.80f, 0.44f) : new Color(0.451f, 0.363f, 0.239f);
        ci.DrawStyleBox(sb, new Rect2(r.Position + new Vector2(0.8f, 0.6f), new Vector2(w - 1.6f, h * 0.62f)));
        sb.BgColor = hot ? new Color(0.80f, 0.60f, 0.30f) : new Color(0.384f, 0.303f, 0.196f);
        ci.DrawStyleBox(sb, new Rect2(r.Position + new Vector2(0.8f, h * 0.40f), new Vector2(w - 1.6f, h * 0.52f)));
        ci.DrawLine(r.Position + new Vector2(3, 0.7f), r.Position + new Vector2(w - 3, 0.7f), hot ? new Color(1f, 0.92f, 0.72f, 0.7f) : new Color(0.86f, 0.74f, 0.54f, 0.6f), 1, true);
        // the figure cut into it: the lit lower wall, then the cut
        var p = new Vector2(Mathf.Round(at.X - ts.X / 2), Mathf.Round(at.Y + 0.36f * size));
        ci.DrawString(f, p + new Vector2(0, 1.0f), s, HorizontalAlignment.Left, -1, size, hot ? new Color(1f, 0.90f, 0.66f, 0.9f) : new Color(0.80f, 0.68f, 0.48f, 0.85f));
        ci.DrawString(f, p, s, HorizontalAlignment.Left, -1, size, new Color(0.06f, 0.045f, 0.03f, 0.97f));
    }

    /// <summary>The line the beads sit on at x (UI 23: a straight row 20 px over the plate's top line; it was the
    /// river's crest).</summary>
    public static float CrestY(float x) => DgPanel.TopY - 20;

    /// <summary>A bead's size across and how far its middle sits above the crest (round 3: the passives threaded on
    /// the river's crest).</summary>
    public const float BeadD = 27, BeadLift = 3;   // (UI 18 judge P1: 21 -> 27, 1.3x: its glyph and rank unread at 1:1)

    /// <summary>A passive (a boon): round 3 (the judge: the pin over the bar was "the only piece outside the
    /// sculpture"), a bead threaded on the river's crest: a dome of the wells' dark river glass in a bronze collar,
    /// its glyph in gold inlay, its rarity a faint light in the glass, a glint upper left; its rank an engraved
    /// numeral on the bronze at its lower right. Several sit side by side along the crest, each at the crest's
    /// height where it falls (Instrument lays the row; CrestY).</summary>
    public static Control Passive(string icon, int rank, bool ranked, Color rarity) => new PassiveStud(icon, ranked ? rank : -1, rarity);

    partial class PassiveStud : Control
    {
        readonly string icon;
        readonly int rank;
        readonly Color rarity;
        float placed = float.NaN;

        public PassiveStud(string icon, int rank, Color rarity)
        {
            this.icon = icon; this.rank = rank; this.rarity = rarity;
            CustomMinimumSize = new Vector2(rank >= 0 ? BeadD + 8 : BeadD + 2, 28);
            Size = CustomMinimumSize;
            MouseFilter = MouseFilterEnum.Ignore;
            TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        }

        public override void _Process(double delta)
        {
            // (laid out by the row: redraw once it lands, at the crest's height there)
            float x = GlobalPosition.X;
            if (x != placed) { placed = x; QueueRedraw(); }
        }

        public override void _Draw()
        {
            const float R = BeadD / 2, Cx = R + 1;
            float gx = GlobalPosition.X + Cx;
            float dy = CrestY(gx) - BeadLift - (GlobalPosition.Y + 14);
            var c = new Vector2(Cx, 14 + dy);
            // (UI 18 judge P1: "their dark discs don't match the bronze rank beads": the collar now the ranks' own
            // bronze, Engrave's tablet: its dark ground, a lit upper face, a darker lower one and a hair of light on
            // top, wide enough to read as metal round the glass)
            DrawTextureRect(Disc, new Rect2(c + new Vector2(1.0f, 2.4f) - Vector2.One * (R + 3.5f), Vector2.One * (2 * R + 7)), false, new Color(0, 0, 0, 0.55f));
            DrawCircle(c + new Vector2(-0.6f, -0.4f), R + 1.0f, new Color(0, 0, 0, 0.55f), true, -1, true);
            DrawCircle(c, R, new Color(0.280f, 0.221f, 0.138f), true, -1, true);
            DrawArc(c, R - 1.9f, 0, Mathf.Tau, 40, new Color(0.384f, 0.303f, 0.196f), 3.0f, true);
            DrawArc(c, R - 1.9f, Mathf.DegToRad(165), Mathf.DegToRad(375), 32, new Color(0.451f, 0.363f, 0.239f), 3.0f, true);
            DrawArc(c, R - 0.7f, Mathf.DegToRad(200), Mathf.DegToRad(320), 20, new Color(0.86f, 0.74f, 0.54f, 0.6f), 1.0f, true);
            // the glass: an inner shadow ring cut into the bronze, then the dark river glass
            DrawCircle(c, R - 3.4f, new Color(0.06f, 0.045f, 0.03f), true, -1, true);
            DrawCircle(c, R - 4.2f, new Color(0.02f, 0.045f, 0.05f), true, -1, true);
            DrawTextureRect(Disc, new Rect2(c - Vector2.One * (R - 3.5f), Vector2.One * (2 * R - 7)), false, rarity with { A = 0.34f });
            const int gi = 16;
            var (gold, glow) = DgGold.Of(icon, gi);
            var gr = new Rect2(c - Vector2.One * (gi / 2f + DgGold.Pad), Vector2.One * (gi + 2 * DgGold.Pad));
            DrawTextureRect(glow, gr, false, new Color(1f, 0.62f, 0.24f, 0.32f));
            DrawTextureRect(gold, gr, false);
            // the dome's glint and a cool rim of sky low on the glass
            DrawArc(c, R - 5.4f, Mathf.DegToRad(200), Mathf.DegToRad(250), 10, new Color(0.85f, 0.95f, 1f, 0.45f), 1.1f, true);
            DrawArc(c, R - 4.8f, Mathf.DegToRad(30), Mathf.DegToRad(120), 14, new Color(0.45f, 0.75f, 0.70f, 0.18f), 1.0f, true);
            // its rank engraved on a bronze tablet at its lower right, as the seats' ranks are
            if (rank >= 0) Engrave(this, c + new Vector2(R + 0.5f, R - 3.5f), rank.ToString(), 12, false);
        }
    }
}
