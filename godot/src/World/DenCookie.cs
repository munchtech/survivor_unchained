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
    static readonly int Px = (int)SurvivorUnchained.Args.Num("den-rl-cookie-px", 384f);   // (256 with mipmaps landed soft all round: DungeonLight sets the projectors' filter to linear, no mipmaps)
    static readonly ImageTexture?[] made = new ImageTexture?[Variants];

    public static ImageTexture Get(int v)
    {
        v = ((v % Variants) + Variants) % Variants;
        if (made[v] is { } t && GodotObject.IsInstanceValid(t)) return t;
        float edge = Mathf.Max(SurvivorUnchained.Args.Num("den-rl-cookie-edge", 0.03f), 0.004f), soft = Mathf.Max(SurvivorUnchained.Args.Num("den-rl-cookie-soft", 0.12f), edge), warp = SurvivorUnchained.Args.Num("den-rl-cookie-warp", 0.10f);
        float arc = Mathf.DegToRad(SurvivorUnchained.Args.Num("den-rl-cookie-arc", 75f));   // the crisp stretch: this far either side of the cookie's +x
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
        float jag = SurvivorUnchained.Args.Num("den-rl-cookie-jag", 0.03f), rim = SurvivorUnchained.Args.Num("den-rl-cookie-rim", 0.85f);   // (judge 3: 0.6 was a spot's falloff, hot in the middle; 0.85: an even fill, the outline carries the shape)
        float rootsK = SurvivorUnchained.Args.Num("den-rl-cookie-roots", 1f), dapK = SurvivorUnchained.Args.Num("den-rl-cookie-dapples", 0f);   // (cool shade lane: off. Small they do not read at the game camera (judge 3); large they are stray coins beside a cut-out pool)
        float rootW = SurvivorUnchained.Args.Num("den-rl-cookie-root-w", 0.7f);
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
        // the roots over the gap (cool shade lane, judge 3: "the forking root falls on its top rim"): one trunk that comes in from
        // outside and runs ACROSS THE OPENING'S MIDDLE (aimed at the lobes' centroid), with one or two limbs forking off it inside
        // the opening (a Y, never an X: two straight lines crossing read as a crosshair); each wavy, thinner toward its tip.
        // The trunk comes from the cookie's +y or -y side, so it runs along the crisp stretch (+x), not into it.
        var mid = Vector2.Zero; { float ws = 0f; for (int i = 0; i < n; i++) { float wgt = rad[i].X * rad[i].Y; mid += c[i] * wgt; ws += wgt; } mid /= ws; }
        int nr = rootsK > 0f ? 2 + (v % 2) : 0;
        var ro = new Vector2[nr]; var rd = new Vector2[nr]; var rw = new float[nr]; var bend = new float[nr]; var len = new float[nr]; var ph = new float[nr];
        if (nr > 0)
        {
            float a0 = (rng.Randf() < 0.5f ? 0.5f : 1.5f) * Mathf.Pi + (rng.Randf() - 0.5f) * 1.2f;
            var o = mid + new Vector2(Mathf.Cos(a0), Mathf.Sin(a0)) * 0.8f;
            float at = a0 + Mathf.Pi + (rng.Randf() - 0.5f) * 0.2f;   // at the middle, within a tenth of the cone's radius
            ro[0] = o; rd[0] = new Vector2(Mathf.Cos(at), Mathf.Sin(at)); rw[0] = (0.075f + 0.02f * rng.Randf()) * rootW; bend[0] = (rng.Randf() - 0.5f) * 0.12f; len[0] = 1.45f + 0.2f * rng.Randf(); ph[0] = rng.Randf() * Mathf.Tau;
            for (int i = 1; i < nr; i++)
            {
                float sAt = i == 1 ? 0.5f + 0.15f * rng.Randf() : 0.85f + 0.1f * rng.Randf(), side = rng.Randf() < 0.5f ? 1f : -1f;
                var perp = new Vector2(-rd[0].Y, rd[0].X);
                if (i == 2) side = -Mathf.Sign(rd[1].Dot(perp));   // the second fork on the other side
                ro[i] = o + rd[0] * sAt + perp * (bend[0] * sAt * sAt + 0.035f * Mathf.Sin(sAt * 6.5f + ph[0]));
                float ai = at + side * (0.55f + 0.3f * rng.Randf());
                rd[i] = new Vector2(Mathf.Cos(ai), Mathf.Sin(ai)); rw[i] = (0.045f + 0.015f * rng.Randf()) * rootW;
                bend[i] = (rng.Randf() - 0.5f) * 0.3f; len[i] = 0.55f + 0.25f * rng.Randf(); ph[i] = rng.Randf() * Mathf.Tau;
            }
        }
        // the dapples: small openings beside the big one, kept only where they fall just outside its rim
        var dap = new System.Collections.Generic.List<Vector3>();
        for (int i = 0; i < 90 && dap.Count < (dapK > 0f ? 3 : 0); i++)
        {
            var q = new Vector2(rng.Randf() * 1.6f - 0.8f, rng.Randf() * 1.6f - 0.8f);
            float fq = Sdf(q), r = SurvivorUnchained.Args.Num("den-rl-cookie-dapple-r", 0.05f) * (0.75f + 0.5f * rng.Randf());   // (judge 3: 12-18 px across, or they do not read at the game camera)
            if (fq > r + 0.03f && fq < r + 0.14f && q.Length() + r < 0.86f && !dap.Exists(d0 => new Vector2(d0.X, d0.Y).DistanceTo(q) < 0.3f)) dap.Add(new Vector3(q.X, q.Y, r));
        }
        var px = new byte[Px * Px * 4];
        for (int y = 0; y < Px; y++)
            for (int x = 0; x < Px; x++)
            {
                var p = new Vector2((x + 0.5f) / Px * 2f - 1f, (y + 0.5f) / Px * 2f - 1f);
                float f = Sdf(p);
                // (judge 3: "no crisp stretch of edge reads anywhere") crisp over ONE stretch, the outline within --den-rl-cookie-arc of the
                // cookie's +x seen from the opening's middle; soft over the rest. The light turns the cookie so that stretch is seen.
                var pm = p - mid;
                float e = Mathf.Lerp(soft, edge, Mathf.SmoothStep(Mathf.Cos(arc + 0.35f), Mathf.Cos(arc), pm.X / Mathf.Max(pm.Length(), 1e-4f)));
                float val = 1f - Mathf.SmoothStep(-e, e, f);
                val *= Mathf.Lerp(rim, 1f, Mathf.SmoothStep(0f, 0.22f, -f));   // the rim at --den-rl-cookie-rim of the core
                foreach (var dp in dap)
                    val = Mathf.Max(val, dapK * (1f - Mathf.SmoothStep(dp.Z - 0.015f, dp.Z + 0.015f, (p - new Vector2(dp.X, dp.Y)).Length())));
                for (int i = 0; i < nr; i++)
                {
                    var q = p - ro[i];
                    float along = q.Dot(rd[i]);
                    if (along < 0f || along > len[i]) continue;
                    float across = Mathf.Abs(q.Dot(new Vector2(-rd[i].Y, rd[i].X)) - bend[i] * along * along - 0.035f * Mathf.Sin(along * 6.5f + ph[i]) - 0.03f * noise.GetNoise2D(along * 1.5f + 20f * i, ph[i]));
                    float w = rw[i] * (1f - 0.55f * along / len[i]);   // thinner toward the tip, never to a hair: a hair does not read at the game camera
                    val *= Mathf.Lerp(1f, Mathf.SmoothStep(w * 0.7f, w + 0.02f, across), rootsK * Mathf.SmoothStep(0f, 0.12f, len[i] - along));
                }
                val *= 1f - Mathf.SmoothStep(0.88f, 0.97f, p.Length());   // nothing at the cone's own rim
                byte b = (byte)Mathf.Clamp(Mathf.Round(val * 255f), 0f, 255f);
                int o = (y * Px + x) * 4;
                px[o] = b; px[o + 1] = b; px[o + 2] = b; px[o + 3] = 255;
            }
        var img = Image.CreateFromData(Px, Px, false, Image.Format.Rgba8, px);
        if (SurvivorUnchained.Args.Get("den-rl-cookie-dump") is string dump) img.SavePng($"{dump}_{v}.png");   // (a look at the texture itself)
        img.GenerateMipmaps();
        return made[v] = ImageTexture.CreateFromImage(img);
    }
}
