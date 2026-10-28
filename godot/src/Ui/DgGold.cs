using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (the game's HUD), piece 5: the skills' glyphs as gold inlay in the rings' dark wells, as
/// the concept has them (its GOLDGLYPH: the game's line glyph, gold, cut into the glass with a dark carved edge
/// below-right and a warm light under it). Made once per glyph and size from the line glyph (Glyphs.Texture), at
/// twice the size shown with mipmaps: the gold with a ridge of light along each stroke, lit from the upper left;
/// and, apart, its soft light (white, for the caller to tint: by default an ember gold, with a faint share of the
/// skill's school colour so neighbours differ). The shapes tell the skills apart; the light only hints.
/// </summary>
public static class DgGold
{
    /// <summary>The padding round the glyph in the textures, in shown px (draw them g + 2 * Pad across).</summary>
    public const int Pad = 4;
    static readonly Dictionary<string, (ImageTexture Gold, ImageTexture Glow)> cache = new();
    static readonly Color Lo = new(0.42f, 0.29f, 0.12f), Mid = new(0.86f, 0.69f, 0.40f), Hi = new(1f, 0.95f, 0.78f);

    public static (Texture2D Gold, Texture2D Glow) Of(string key, int size)
    {
        var ck = $"{key}|{size}";
        if (cache.TryGetValue(ck, out var hit)) return hit;
        int s2 = size * 2, pad = Pad * 2, w = s2 + 2 * pad;
        var src = Glyphs.Texture(key, s2, Colors.White, 2.1f, line: true).GetImage();
        if (src.IsCompressed()) src.Decompress();
        src.Convert(Image.Format.Rgba8);
        var a = new float[w * w];
        for (int y = 0; y < Math.Min(s2, src.GetHeight()); y++)
            for (int x = 0; x < Math.Min(s2, src.GetWidth()); x++)
                a[(y + pad) * w + x + pad] = src.GetPixel(x, y).A;
        var h = Blur(Blur(a, w, 1), w, 1);          // the stroke's height: its ridge
        var glow = Blur(Blur(Blur(a, w, 3), w, 3), w, 2);
        var gold = Image.CreateEmpty(w, w, false, Image.Format.Rgba8);
        var gl = Image.CreateEmpty(w, w, false, Image.Format.Rgba8);
        for (int y = 0; y < w; y++)
            for (int x = 0; x < w; x++)
            {
                int i = y * w + x;
                // the carved edge: the glyph's shape, dark, 2 px (1 shown) down and right, under the gold
                float sh = 0.85f * At(a, w, x - 2, y - 2);
                float ga = a[i];
                // the gold: the ridge lit, the slope facing the upper left brighter, the far slope darker
                float gx = At(h, w, x + 1, y) - At(h, w, x - 1, y), gy = At(h, w, x, y + 1) - At(h, w, x, y - 1);
                float face = Math.Clamp(-(gx * -0.6f + gy * -0.8f) * 2.2f, -1, 1);
                float ridge = Math.Clamp(h[i] * 1.3f, 0, 1);
                var c = Lo.Lerp(Mid, Math.Clamp(0.35f + 0.65f * ridge + 0.35f * face, 0, 1));
                c = c.Lerp(Hi, Math.Clamp((ridge - 0.65f) * 1.6f + face * 0.5f, 0, 1));
                // over the carved shadow
                float oa = ga + sh * (1 - ga);
                var o = oa > 0 ? new Color(c.R * ga / oa, c.G * ga / oa, c.B * ga / oa, oa) : new Color(0, 0, 0, 0);
                gold.SetPixel(x, y, o);
                gl.SetPixel(x, y, new Color(1, 1, 1, Math.Clamp(glow[i] * 1.6f, 0, 1)));
            }
        gold.GenerateMipmaps();
        gl.GenerateMipmaps();
        var made = (ImageTexture.CreateFromImage(gold), ImageTexture.CreateFromImage(gl));
        cache[ck] = made;
        return made;
    }

    static float At(float[] a, int w, int x, int y) => x < 0 || y < 0 || x >= w || y >= w ? 0 : a[y * w + x];

    /// <summary>A box blur of radius r, both ways.</summary>
    static float[] Blur(float[] a, int w, int r)
    {
        var t = new float[a.Length];
        var o = new float[a.Length];
        float n = 2 * r + 1;
        for (int y = 0; y < w; y++)
            for (int x = 0; x < w; x++)
            {
                float s = 0;
                for (int k = -r; k <= r; k++) s += At(a, w, x + k, y);
                t[y * w + x] = s / n;
            }
        for (int y = 0; y < w; y++)
            for (int x = 0; x < w; x++)
            {
                float s = 0;
                for (int k = -r; k <= r; k++) s += At(t, w, x, y + k);
                o[y * w + x] = s / n;
            }
        return o;
    }
}
