using Godot;

namespace SurvivorUnchained.View;

/// <summary>(real light lane, 23 Nov 2026; the owner: "use what real shipped games would use and stop trying to force the
/// light. it can have paint but an actual light too") The den's light pools are a real spot light with a projected
/// texture (Godot's Light3D.LightProjector, the same feature as Unreal's light functions and Unity's light cookies): this
/// is that texture, the gap in the roof the sun comes through. Painted, not noise: two or three broad lobes with one clean
/// edge, even inside (a sun pool has no shading of its own), nothing outside. A few variants, made once and kept; each
/// light turns its own about the shaft, so no two pools on a screen share an outline.
/// (judge 2) and an inside: the roots across the gap as shadows (--den-rl-cookie-roots 0: none), dapples by the rim
/// (--den-rl-cookie-dapples 0), a finer jag (--den-rl-cookie-jag), the rim dimmer than the core (--den-rl-cookie-rim).
/// --den-rl-cookie-edge: the edge's half width as a share of the cone's radius; --den-rl-cookie-warp: how far the outline
/// wanders from its ellipses.</summary>
public static class DenCookie
{
    public const int Variants = 4;
    const int Px = 256;
    static readonly ImageTexture?[] made = new ImageTexture?[Variants];

    public static ImageTexture Get(int v)
    {
        v = ((v % Variants) + Variants) % Variants;
        if (made[v] is { } t && GodotObject.IsInstanceValid(t)) return t;
        float edge = Mathf.Max(SurvivorUnchained.Args.Num("den-rl-cookie-edge", 0.02f), 0.004f), warp = SurvivorUnchained.Args.Num("den-rl-cookie-warp", 0.10f);
        var rng = new RandomNumberGenerator { Seed = (ulong)(7919 * (v + 1)) };
        int n = 2 + (v % 2);
        var c = new Vector2[n]; var rad = new Vector2[n]; var rot = new float[n];
        for (int i = 0; i < n; i++)
        {
            // the first lobe at the middle, the others leaning out of it: always one connected opening
            float a = rng.Randf() * Mathf.Tau, d = i == 0 ? 0f : 0.26f + 0.12f * rng.Randf();
            c[i] = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * d;
            rad[i] = new Vector2(0.42f + 0.12f * rng.Randf(), 0.30f + 0.10f * rng.Randf()) * (i == 0 ? 1f : 0.8f);
            rot[i] = rng.Randf() * Mathf.Pi;
        }
        var noise = new FastNoiseLite { Seed = 31 + v, NoiseType = FastNoiseLite.NoiseTypeEnum.Simplex, Frequency = 1.6f, FractalOctaves = 2 };
        // (judge 2: "the pool has no gap inside it. It is a smooth, over-bright blob") the gap's own inside: a finer jag on the
        // outline (a second, higher octave: more low warp only makes lobes), an edge that is crisp here and soft there, the roots
        // that cross the gap as shadows over the pool, a few dapples just outside the rim, and a core hotter than the rim
        var fine = new FastNoiseLite { Seed = 57 + v, NoiseType = FastNoiseLite.NoiseTypeEnum.Simplex, Frequency = 6f, FractalOctaves = 2 };
        float jag = SurvivorUnchained.Args.Num("den-rl-cookie-jag", 0.03f), rim = SurvivorUnchained.Args.Num("den-rl-cookie-rim", 0.6f);
        float rootsK = SurvivorUnchained.Args.Num("den-rl-cookie-roots", 1f), dapK = SurvivorUnchained.Args.Num("den-rl-cookie-dapples", 1f);
        float Sdf(Vector2 p)
        {
            float f = 1e9f;
            for (int i = 0; i < n; i++)
            {
                var q = (p - c[i]).Rotated(-rot[i]);
                f = Mathf.Min(f, ((q / rad[i]).Length() - 1f) * Mathf.Min(rad[i].X, rad[i].Y));
            }
            return f + warp * noise.GetNoise2D(p.X, p.Y) + jag * fine.GetNoise2D(p.X, p.Y);
        }
        // the roots over the gap: one root coming in from the rim and forking across the opening (a Y, never an X: two straight
        // lines crossing read as a crosshair), each limb wavy, thinning to nothing at its tip; --den-rl-cookie-roots scales how dark
        int nr = rootsK > 0f ? 2 + (v % 2) : 0;
        var ro = new Vector2[nr]; var rd = new Vector2[nr]; var rw = new float[nr]; var bend = new float[nr]; var len = new float[nr]; var ph = new float[nr];
        {
            float a0 = rng.Randf() * Mathf.Tau;
            var o = new Vector2(Mathf.Cos(a0), Mathf.Sin(a0)) * 0.8f;
            float spread = 0.5f + 0.3f * rng.Randf(), lean = (rng.Randf() - 0.5f) * 0.5f;
            for (int i = 0; i < nr; i++)
            {
                float ai = a0 + Mathf.Pi + lean + spread * ((nr == 1 ? 0.5f : i / (float)(nr - 1)) - 0.5f) * 2f * (0.8f + 0.4f * rng.Randf());
                ro[i] = o; rd[i] = new Vector2(Mathf.Cos(ai), Mathf.Sin(ai)); rw[i] = (i == 0 ? 0.085f : 0.055f) + 0.025f * rng.Randf();
                bend[i] = (rng.Randf() - 0.5f) * 0.35f; len[i] = 1.1f + 0.5f * rng.Randf(); ph[i] = rng.Randf() * Mathf.Tau;
            }
        }
        // the dapples: small openings beside the big one, kept only where they fall just outside its rim
        var dap = new System.Collections.Generic.List<Vector3>();
        for (int i = 0; i < 60 && dap.Count < (dapK > 0f ? 5 : 0); i++)
        {
            var q = new Vector2(rng.Randf() * 1.6f - 0.8f, rng.Randf() * 1.6f - 0.8f);
            float fq = Sdf(q), r = 0.035f + 0.04f * rng.Randf();
            if (fq > r + 0.02f && fq < r + 0.14f && q.Length() + r < 0.86f) dap.Add(new Vector3(q.X, q.Y, r));
        }
        var px = new byte[Px * Px * 4];
        for (int y = 0; y < Px; y++)
            for (int x = 0; x < Px; x++)
            {
                var p = new Vector2((x + 0.5f) / Px * 2f - 1f, (y + 0.5f) / Px * 2f - 1f);
                float f = Sdf(p);
                float e = edge * (1f + 2.5f * (0.5f + 0.5f * noise.GetNoise2D(p.X * 0.6f + 9f, p.Y * 0.6f - 4f)));   // crisp here, soft there
                float val = 1f - Mathf.SmoothStep(-e, e, f);
                val *= Mathf.Lerp(rim, 1f, Mathf.SmoothStep(0f, 0.22f, -f));   // the rim at --den-rl-cookie-rim of the core
                foreach (var dp in dap)
                    val = Mathf.Max(val, rim * (1f - Mathf.SmoothStep(dp.Z - 0.02f, dp.Z + 0.02f, (p - new Vector2(dp.X, dp.Y)).Length())));
                for (int i = 0; i < nr; i++)
                {
                    var q = p - ro[i];
                    float along = q.Dot(rd[i]);
                    if (along < 0f || along > len[i]) continue;
                    float across = Mathf.Abs(q.Dot(new Vector2(-rd[i].Y, rd[i].X)) - bend[i] * along * along - 0.035f * Mathf.Sin(along * 6.5f + ph[i]) - 0.03f * noise.GetNoise2D(along * 1.5f + 20f * i, ph[i]));
                    float w = rw[i] * (1f - along / len[i]);
                    val *= Mathf.Lerp(1f, Mathf.SmoothStep(w * 0.7f, w + 0.02f, across), rootsK * Mathf.SmoothStep(0f, 0.12f, len[i] - along));
                }
                val *= 1f - Mathf.SmoothStep(0.88f, 0.97f, p.Length());   // nothing at the cone's own rim
                byte b = (byte)Mathf.Clamp(Mathf.Round(val * 255f), 0f, 255f);
                int o = (y * Px + x) * 4;
                px[o] = b; px[o + 1] = b; px[o + 2] = b; px[o + 3] = 255;
            }
        var img = Image.CreateFromData(Px, Px, false, Image.Format.Rgba8, px);
        img.GenerateMipmaps();
        return made[v] = ImageTexture.CreateFromImage(img);
    }
}
