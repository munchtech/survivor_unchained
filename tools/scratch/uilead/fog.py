p = 'godot/src/Ui/MapScreen.cs'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
s = s.replace('\r\n', '\n')
a = s.index('    /// <summary>Paper over what has not been walked, with holes where you went.</summary>')
b = s.index('    static readonly Color Dark = new(0.075f, 0.062f, 0.058f);')
b = s.index('\n', b) + 1
new = '''    /// <summary>
    /// The land not yet walked, as a cartographer leaves it: the same sheet,
    /// blank and older (mottled, foxed, browned toward its edge), and where
    /// what you know ends, an ink wash that has bled into the paper and dried
    /// with a darker tide line, ragged as a brush leaves it. The walked land
    /// shows through clean. Opaque wherever nothing was walked: no ink shows
    /// through. (Was a flat dark at 94%: the owner, "it needs to look better".)
    /// </summary>
    static ImageTexture Fog(string seen, int n)
    {
        const int F = 600;
        float c = F / (float)n;
        var known = new float[F * F];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (j * n + i >= seen.Length || seen[j * n + i] != '1') continue;
                float cx = (i + 0.5f) * c, cy = (j + 0.5f) * c, rr = c * 1.3f;
                for (int y = (int)(cy - rr); y <= (int)(cy + rr); y++)
                    for (int x = (int)(cx - rr); x <= (int)(cx + rr); x++)
                    {
                        if (x < 0 || y < 0 || x >= F || y >= F) continue;
                        float d = new Vector2(x - cx, y - cy).Length() / rr;
                        known[y * F + x] = Math.Max(known[y * F + x], 1 - Mathf.SmoothStep(0.5f, 1f, d));
                    }
            }
        for (int pass = 0; pass < 3; pass++) known = Blur(known, F, 5);
        var px = new byte[F * F * 4];
        for (int y = 0; y < F; y++)
            for (int x = 0; x < F; x++)
            {
                float u = x / (float)F, v = y / (float)F;
                // The edge of the known, made ragged by the brush: a broad wobble and a fine one.
                float rag = (Fbm(u * 7, v * 7, 3) - 0.5f) * 0.5f + (Fbm(u * 38, v * 38, 2) - 0.5f) * 0.16f;
                float k = Mathf.Clamp(known[y * F + x] + rag, 0, 1);
                float cover = 1 - Mathf.SmoothStep(0.34f, 0.5f, k);
                if (cover <= 0.001f) continue;
                // The blank sheet: mottled with age, foxed here and there, a fibre grain, browner toward its edge.
                float mottle = Fbm(u * 5 + 11, v * 5 + 3, 4);
                var paper = new Vector3(214, 198, 160).Lerp(new Vector3(178, 154, 112), Mathf.SmoothStep(0.35f, 0.8f, mottle));
                float fox = Mathf.SmoothStep(0.74f, 0.86f, Fbm(u * 26 + 5, v * 26 + 9, 2));
                paper = paper.Lerp(new Vector3(150, 104, 58), fox * 0.45f);
                float grain = (float)(Hash(x, y) - 0.5) * 7 + (float)(Hash(x / 3, y * 2) - 0.5) * 5;
                float edge = Mathf.Min(Mathf.Min(u, 1 - u), Mathf.Min(v, 1 - v));
                paper = paper.Lerp(new Vector3(96, 62, 30), (1 - Mathf.SmoothStep(0f, 0.09f, edge)) * 0.6f);
                // The wash where knowledge ends: sepia bleeding outward, its tide line darkest.
                float tide = Mathf.Exp(-Mathf.Pow((k - 0.31f) / 0.05f, 2));
                float bleed = Mathf.SmoothStep(0.06f, 0.33f, k) * (1 - Mathf.SmoothStep(0.33f, 0.4f, k));
                paper = paper.Lerp(new Vector3(120, 84, 48), bleed * 0.35f).Lerp(new Vector3(74, 46, 22), tide * 0.55f);
                paper += new Vector3(grain, grain, grain * 0.8f);
                int o = (y * F + x) * 4;
                px[o] = (byte)Math.Clamp(paper.X, 0, 255);
                px[o + 1] = (byte)Math.Clamp(paper.Y, 0, 255);
                px[o + 2] = (byte)Math.Clamp(paper.Z, 0, 255);
                px[o + 3] = (byte)Math.Clamp(cover * 255, 0, 255);
            }
        return ImageTexture.CreateFromImage(Image.CreateFromData(F, F, false, Image.Format.Rgba8, px));
    }

    /// <summary>Smooth value noise, summed over octaves (0 to 1).</summary>
    static float Fbm(float x, float y, int octaves)
    {
        float sum = 0, amp = 0.5f, norm = 0;
        for (int o = 0; o < octaves; o++)
        {
            int x0 = (int)Mathf.Floor(x), y0 = (int)Mathf.Floor(y);
            float tx = x - x0, ty = y - y0;
            tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
            float a = (float)Hash(x0, y0), b = (float)Hash(x0 + 1, y0), c = (float)Hash(x0, y0 + 1), d = (float)Hash(x0 + 1, y0 + 1);
            sum += amp * Mathf.Lerp(Mathf.Lerp(a, b, tx), Mathf.Lerp(c, d, tx), ty);
            norm += amp;
            amp *= 0.5f; x *= 2.03f; y *= 2.03f;
        }
        return sum / norm;
    }

    /// <summary>The table the sheet lies on, past the paper's edge: dark leather, lit a little in the middle.</summary>
    static readonly Color Dark = new(0.075f, 0.058f, 0.048f);
'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
print('ok')
