using System;

namespace SurvivorUnchained.Look;

/// <summary>(lane E lead 8, 17 Nov; judge 5: "2-4 forks 8-25 px x 1-2 px + 2-3 broken chunks 6-10 px") The storm fissure's
/// forks and broken chunks (BattleFx.P7Storm.cs P7Fissure, shaders/fx_p7_b.gdshaderinc mode 18), picked along the part of the
/// line on screen, in px at the play camera (1080 lines) from where the gap opens. The shader snaps each fork to the gap's
/// nearest knot and sends it out on the kink's outer side. Numbers: fx_language.json p7 storm.line.fork
/// [count min, max, px long min, max, px at the root, px at the tip, from, to (shares of the run)] and storm.line.chunk
/// [count min, max, px wide min, max, px long min, max, from, to (shares of the taper)].</summary>
public static class FissureMarks
{
    /// <summary>A fork: px along, px long, its turn 0..1 (the shader's angle and kink), px wide at the root.</summary>
    public readonly record struct Fork(float At, float Long, float Turn, float Root);
    /// <summary>A broken chunk: px along (its middle), px wide at most, px long, its salt (the hole's corners).</summary>
    public readonly record struct Chunk(float At, float Wide, float Long, float Salt);

    /// <summary>The gap's width (px) at `at` px: gap [at her end, at the taper's end, power] over `taper` px.</summary>
    public static float GapAt(float at, float taper, float[] gap) =>
        gap[1] + (gap[0] - gap[1]) * MathF.Pow(Math.Clamp(1 - at / Math.Max(taper, 1), 0, 1), gap[2]);

    /// <summary>The forks and chunks on a run of `run` px (the visible part) whose gap tapers over `taper` px; `r` 0..1.
    /// Spread evenly (one per stretch, jittered in its middle), a chunk never within `apart` px of a fork's root, at least
    /// 1.5 times the gap where it lies (inside the judge's px). A run too short for them gets fewer, never squeezed.</summary>
    public static (Fork[] Forks, Chunk[] Chunks) Pick(float run, float taper, float[] fork, float[] chunk, float[] gap, Func<float> r, float apart = 9)
    {
        taper = Math.Clamp(taper, 1, Math.Max(run, 1));
        float f0 = fork[6] * run, f1 = fork[7] * run;
        int nf = Fit((int)fork[0] + (int)MathF.Floor(r() * (fork[1] - fork[0] + 0.999f)), f1 - f0, 3 * fork[2]);
        var forks = new Fork[nf];
        for (int i = 0; i < nf; i++)
        {
            float bin = (f1 - f0) / nf, at = f0 + (i + 0.2f + 0.6f * r()) * bin;
            float l = fork[3] + (fork[2] - fork[3]) * Math.Clamp(at / Math.Max(run, 1), 0, 1);
            forks[i] = new Fork(at, Math.Clamp(l * (0.85f + 0.3f * r()), fork[2], fork[3]), r(), fork[4]);
        }
        float c0 = chunk[6] * taper, c1 = chunk[7] * taper;
        int nc = Fit((int)chunk[0] + (int)MathF.Floor(r() * (chunk[1] - chunk[0] + 0.999f)), c1 - c0, 2.5f * chunk[5]);
        var chunks = new Chunk[nc];
        for (int i = 0; i < nc; i++)
        {
            float bin = (c1 - c0) / nc, at = c0 + (i + 0.25f + 0.5f * r()) * bin;
            // clear of the forks' roots: stepped along its stretch (never out of it)
            for (int k = 0; k < 4; k++)
            {
                bool near = false;
                foreach (var f in forks) near |= MathF.Abs(f.At - at) < apart + 0.5f * chunk[5];
                if (!near) break;
                // (lead 9) half a chunk inside its stretch, so two never run into one hole
                float edge = Math.Min(0.5f * chunk[5], 0.25f * bin);
                at = Math.Clamp(at + (k % 2 == 0 ? 1 : -2) * (apart + 0.5f * chunk[5]), c0 + i * bin + edge, c0 + (i + 1) * bin - edge);
            }
            float w = chunk[2] + (chunk[3] - chunk[2]) * r();
            w = Math.Clamp(MathF.Max(w, 1.5f * GapAt(at, taper, gap)), chunk[2], chunk[3]);
            chunks[i] = new Chunk(at, w, chunk[4] + (chunk[5] - chunk[4]) * r(), 0.05f + 0.9f * r());
        }
        return (forks, chunks);
    }

    /// <summary>(lane E lead 9, 17 Nov; judge 6: "it spans 380 px, about 57 px past the storm's ring") How far the drawn
    /// line runs, at most: reach[0] x the storm's ring radius `ringR` less reach[1] m, never past `len` (the sim's line,
    /// clipped); reach[0] 0 or no ring: `len`. View only.</summary>
    public static float Reach(float len, float ringR, float[] reach) =>
        reach.Length == 0 || reach[0] <= 0 || ringR <= 0 ? len : Math.Min(len, Math.Max(0, reach[0] * ringR - (reach.Length > 1 ? reach[1] : 0)));

    /// <summary>`n` marks, but no more than fit `span` px at `each` px apart.</summary>
    static int Fit(int n, float span, float each) => Math.Max(0, Math.Min(n, (int)MathF.Floor(span / Math.Max(each, 1))));

    /// <summary>(lane E lead 8, 17 Nov) How far the drawn line runs: from (x0,z0) toward (x1,z1) in `step` m, stopping at the
    /// first point `blocked` calls blocked, then `back` m short of it so the taper ends on open floor. Returns the full length
    /// when nothing blocks; view only (the sim's line is untouched). `blockedAt` is the length of the first blocked step, or -1.</summary>
    public static float ClipRun(Func<double, double, bool> blocked, double x0, double z0, double x1, double z1, out float blockedAt, float step = 0.2f, float back = 0.3f)
    {
        double len = Math.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0));
        blockedAt = -1;
        if (len < 1e-6) return 0;
        double dx = (x1 - x0) / len, dz = (z1 - z0) / len;
        for (double a = step; a <= len + 1e-9; a += step)
            if (blocked(x0 + dx * a, z0 + dz * a)) { blockedAt = (float)a; return (float)Math.Max(0, a - back); }
        return (float)len;
    }
}
