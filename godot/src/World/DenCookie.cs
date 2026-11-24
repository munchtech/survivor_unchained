using Godot;

namespace SurvivorUnchained.View;

/// <summary>(real light lane, 23 Nov 2026; the owner: "use what real shipped games would use and stop trying to force the
/// light. it can have paint but an actual light too") The den's light pools are a real spot light with a projected
/// texture (Godot's Light3D.LightProjector, the same feature as Unreal's light functions and Unity's light cookies): this
/// is that texture, the gap in the roof the sun comes through. Painted, not noise: two or three broad lobes with one clean
/// edge, even inside (a sun pool has no shading of its own), nothing outside. A few variants, made once and kept; each
/// light turns its own about the shaft, so no two pools on a screen share an outline.
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
        float edge = Mathf.Max(SurvivorUnchained.Args.Num("den-rl-cookie-edge", 0.02f), 0.004f), warp = SurvivorUnchained.Args.Num("den-rl-cookie-warp", 0.15f);
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
        var px = new byte[Px * Px * 4];
        for (int y = 0; y < Px; y++)
            for (int x = 0; x < Px; x++)
            {
                var p = new Vector2((x + 0.5f) / Px * 2f - 1f, (y + 0.5f) / Px * 2f - 1f);
                float f = 1e9f;
                for (int i = 0; i < n; i++)
                {
                    var q = (p - c[i]).Rotated(-rot[i]);
                    f = Mathf.Min(f, ((q / rad[i]).Length() - 1f) * Mathf.Min(rad[i].X, rad[i].Y));
                }
                f += warp * noise.GetNoise2D(p.X, p.Y);
                float val = 1f - Mathf.SmoothStep(-edge, edge, f);
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
