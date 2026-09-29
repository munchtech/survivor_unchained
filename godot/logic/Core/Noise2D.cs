using System;

namespace SurvivorUnchained.Core;

/// <summary>
/// Stefan Gustavson's simplex noise (public domain), permutation seeded the
/// way the web game seeds it, so the same seed shapes the same ground.
/// </summary>
public sealed class Noise2D
{
    static readonly double F2 = 0.5 * (Math.Sqrt(3) - 1);
    static readonly double G2 = (3 - Math.Sqrt(3)) / 6;
    static readonly int[,] Grad = { { 1, 1 }, { -1, 1 }, { 1, -1 }, { -1, -1 }, { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } };

    readonly byte[] perm = new byte[512];

    public Noise2D(uint seed = 1337)
    {
        var p = new byte[256];
        for (int i = 0; i < 256; i++) p[i] = (byte)i;
        uint s = seed == 0 ? 1 : seed;
        for (int i = 255; i > 0; i--)
        {
            s = unchecked(s * 1664525u + 1013904223u);
            int j = (int)(s % (uint)(i + 1));
            (p[i], p[j]) = (p[j], p[i]);
        }
        for (int i = 0; i < 512; i++) perm[i] = p[i & 255];
    }

    /// <summary>Roughly [-1, 1].</summary>
    public double Noise(double xin, double yin)
    {
        double s = (xin + yin) * F2;
        int i = (int)Math.Floor(xin + s), j = (int)Math.Floor(yin + s);
        double t = (i + j) * G2;
        double x0 = xin - (i - t), y0 = yin - (j - t);
        int i1 = x0 > y0 ? 1 : 0, j1 = x0 > y0 ? 0 : 1;
        double x1 = x0 - i1 + G2, y1 = y0 - j1 + G2;
        double x2 = x0 - 1 + 2 * G2, y2 = y0 - 1 + 2 * G2;
        int ii = i & 255, jj = j & 255;
        double n0 = 0, n1 = 0, n2 = 0;
        double t0 = 0.5 - x0 * x0 - y0 * y0;
        if (t0 > 0) { int g = perm[ii + perm[jj]] & 7; t0 *= t0; n0 = t0 * t0 * (Grad[g, 0] * x0 + Grad[g, 1] * y0); }
        double t1 = 0.5 - x1 * x1 - y1 * y1;
        if (t1 > 0) { int g = perm[ii + i1 + perm[jj + j1]] & 7; t1 *= t1; n1 = t1 * t1 * (Grad[g, 0] * x1 + Grad[g, 1] * y1); }
        double t2 = 0.5 - x2 * x2 - y2 * y2;
        if (t2 > 0) { int g = perm[ii + 1 + perm[jj + 1]] & 7; t2 *= t2; n2 = t2 * t2 * (Grad[g, 0] * x2 + Grad[g, 1] * y2); }
        return 70 * (n0 + n1 + n2);
    }

    /// <summary>Fractal sum, normalised to roughly [-1, 1].</summary>
    public double Fbm(double x, double y, int octaves = 4, double lacunarity = 2, double gain = 0.5)
    {
        double amp = 1, freq = 1, sum = 0, norm = 0;
        for (int o = 0; o < octaves; o++)
        {
            sum += Noise(x * freq, y * freq) * amp;
            norm += amp;
            amp *= gain;
            freq *= lacunarity;
        }
        return sum / norm;
    }

    /// <summary>Ridged fractal in [0, 1]: sharp crests, for rock and ridgelines.</summary>
    public double Ridged(double x, double y, int octaves = 4)
    {
        double amp = 0.5, freq = 1, sum = 0;
        for (int o = 0; o < octaves; o++)
        {
            double n = 1 - Math.Abs(Noise(x * freq, y * freq));
            sum += n * n * amp;
            amp *= 0.5;
            freq *= 2.1;
        }
        return sum;
    }
}
