using System;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (--hud drowned), round 2: what the meters share. The rings' cooldown as a well that fills
/// from its foot (the part come back lit in the skill's element, a soft meniscus, the rest dark: no line across it,
/// which read as a strike-through), the seconds and the rank as gold numerals cut in the bronze, a soft disc for the
/// element's light in the well's glass, and the passives' small gold studs over the bar.
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

    /// <summary>A passive (a boon) over the bar: a small sunk stud of the river's bronze, its glyph in gold inlay, its
    /// rarity a faint light in the well (not the glyph's colour), its rank a gold numeral at its lower right.</summary>
    public static Control Passive(string icon, int rank, bool ranked, Color rarity) => new PassiveStud(icon, ranked ? rank : -1, rarity);

    partial class PassiveStud : Control
    {
        readonly string icon;
        readonly int rank;
        readonly Color rarity;

        public PassiveStud(string icon, int rank, Color rarity)
        {
            this.icon = icon; this.rank = rank; this.rarity = rarity;
            CustomMinimumSize = new Vector2(28, 28);
            Size = CustomMinimumSize;
            MouseFilter = MouseFilterEnum.Ignore;
            TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        }

        public override void _Draw()
        {
            var c = new Vector2(14, 14);
            // the stud: a dark well in a bronze rim, lit from the upper left
            DrawCircle(c + new Vector2(0.6f, 1.2f), 12.6f, new Color(0, 0, 0, 0.45f), true, -1, true);
            DrawCircle(c, 12f, new Color(0.30f, 0.22f, 0.12f), true, -1, true);
            DrawArc(c, 11.2f, Mathf.DegToRad(160), Mathf.DegToRad(300), 24, new Color(0.78f, 0.62f, 0.38f, 0.85f), 1.3f, true);
            DrawArc(c, 11.2f, Mathf.DegToRad(-20), Mathf.DegToRad(120), 24, new Color(0.10f, 0.13f, 0.10f, 0.9f), 1.3f, true);
            DrawCircle(c, 9.4f, new Color(0.025f, 0.05f, 0.05f), true, -1, true);
            DrawTextureRect(Disc, new Rect2(c - Vector2.One * 10, Vector2.One * 20), false, rarity with { A = 0.30f });
            const int gi = 14;
            var (gold, glow) = DgGold.Of(icon, gi);
            var gr = new Rect2(c - Vector2.One * (gi / 2f + DgGold.Pad), Vector2.One * (gi + 2 * DgGold.Pad));
            DrawTextureRect(glow, gr, false, new Color(1f, 0.62f, 0.24f, 0.30f));
            DrawTextureRect(gold, gr, false);
            if (rank >= 0) Numeral(this, c + new Vector2(10, 9), rank.ToString(), 12, Gold, 3);
        }
    }
}
