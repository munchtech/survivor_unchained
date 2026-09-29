using System;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The web game's tiling noise (src/render/noiseTex.ts), made the same way,
/// hash for hash: four octaves of value noise in four channels, 256 px, so
/// the ground varies here exactly as it does there.
/// </summary>
public static class NoiseTex
{
    static ImageTexture? cached;

    static double Hash(int x, int y, int s)
    {
        int h = unchecked((int)((long)x * 374761393 + (long)y * 668265263 + (long)s * 982451653));
        h = unchecked((int)((long)(h ^ (int)((uint)h >> 13)) * 1274126177));
        h ^= (int)((uint)h >> 16);
        return (uint)h / 4294967296.0;
    }

    static double Tile(double u, double v, int period, int seed)
    {
        double x = u * period, y = v * period;
        int xi = (int)Math.Floor(x), yi = (int)Math.Floor(y);
        double xf = x - xi, yf = y - yi;
        double sx = xf * xf * (3 - 2 * xf), sy = yf * yf * (3 - 2 * yf);
        int W(int i) => ((i % period) + period) % period;
        double a = Hash(W(xi), W(yi), seed), b = Hash(W(xi + 1), W(yi), seed);
        double c = Hash(W(xi), W(yi + 1), seed), d = Hash(W(xi + 1), W(yi + 1), seed);
        double top = a + (b - a) * sx;
        return top + ((c + (d - c) * sx) - top) * sy;
    }

    static double Fbm(double u, double v, int basePeriod, int seed)
    {
        double sum = 0, amp = 0.5, norm = 0;
        int p = basePeriod;
        for (int o = 0; o < 4; o++) { sum += Tile(u, v, p, seed + o * 17) * amp; norm += amp; amp *= 0.5; p *= 2; }
        return sum / norm;
    }

    public static ImageTexture Get()
    {
        if (cached != null) return cached;
        const int N = 256;
        var data = new byte[N * N * 4];
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                double u = (double)x / N, v = (double)y / N;
                int i = (y * N + x) * 4;
                data[i] = (byte)Math.Round(Fbm(u, v, 4, 1) * 255);
                data[i + 1] = (byte)Math.Round(Fbm(u, v, 8, 2) * 255);
                data[i + 2] = (byte)Math.Round(Fbm(u, v, 16, 3) * 255);
                data[i + 3] = (byte)Math.Round(Tile(u, v, 64, 4) * 255);
            }
        var img = Image.CreateFromData(N, N, false, Image.Format.Rgba8, data);
        img.GenerateMipmaps();
        cached = ImageTexture.CreateFromImage(img);
        return cached;
    }
}
