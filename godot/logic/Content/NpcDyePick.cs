namespace SurvivorUnchained.Content;

/// <summary>
/// A Marionette package NPC's per-copy look, as numbers (the view's NpcDye applies it): which palette dye a copy wears
/// in a channel, how much taller or shorter it stands, where in its loops it starts, all from the run's seed and the
/// copy's number (so a shot repeats), and a target colour clamped in Oklab lightness to the channel's range (so a
/// light shawl stays light whatever it is dyed). Colours are linear RGB, 0..1.
/// </summary>
public static class NpcDyePick
{
    /// <summary>A well-mixed 0..1 from (seed, copy, salt).</summary>
    public static double Unit(int seed, int copy, int salt)
    {
        unchecked
        {
            ulong h = 1469598103934665603UL;
            foreach (int v in new[] { seed, copy, salt })
            {
                h ^= (uint)v; h *= 1099511628211UL;
                h ^= h >> 29; h *= 0xBF58476D1CE4E5B9UL; h ^= h >> 32;
            }
            return (h >> 11) * (1.0 / (1UL << 53));
        }
    }

    /// <summary>The palette entry (0..count-1) a copy wears in a channel (0 a, 1 b, 2 hair).</summary>
    public static int Pick(int seed, int copy, int channel, int count) =>
        count <= 0 ? -1 : System.Math.Min(count - 1, (int)(Unit(seed, copy, 101 + channel) * count));

    /// <summary>A copy's height factor: 1 +- scale, evenly.</summary>
    public static double Scale(int seed, int copy, double scale) => 1 + (Unit(seed, copy, 7) * 2 - 1) * scale;

    /// <summary>Where in its loops a copy starts (0..1).</summary>
    public static double Phase(int seed, int copy) => Unit(seed, copy, 13);

    /// <summary>"#rrggbb" (sRGB) to linear RGB; null if it does not parse.</summary>
    public static (double R, double G, double B)? Hex(string? hex)
    {
        if (hex == null) return null;
        var h = hex.TrimStart('#');
        if (h.Length != 6 || !int.TryParse(h, System.Globalization.NumberStyles.HexNumber, null, out int v)) return null;
        static double Lin(int c) { double s = c / 255.0; return s <= 0.04045 ? s / 12.92 : System.Math.Pow((s + 0.055) / 1.055, 2.4); }
        return (Lin((v >> 16) & 255), Lin((v >> 8) & 255), Lin(v & 255));
    }

    /// <summary>Linear luminance (Rec. 709), as the shader's.</summary>
    public static double Lum((double R, double G, double B) c) => 0.2126 * c.R + 0.7152 * c.G + 0.0722 * c.B;

    public static (double L, double A, double B) ToOklab((double R, double G, double B) c)
    {
        double l = System.Math.Cbrt(0.4122214708 * c.R + 0.5363325363 * c.G + 0.0514459929 * c.B);
        double m = System.Math.Cbrt(0.2119034982 * c.R + 0.6806995451 * c.G + 0.1073969566 * c.B);
        double s = System.Math.Cbrt(0.0883024619 * c.R + 0.2817188376 * c.G + 0.6299787005 * c.B);
        return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s);
    }

    public static (double R, double G, double B) FromOklab((double L, double A, double B) o)
    {
        double l = o.L + 0.3963377774 * o.A + 0.2158037573 * o.B;
        double m = o.L - 0.1055613458 * o.A - 0.0638541728 * o.B;
        double s = o.L - 0.0894841775 * o.A - 1.2914855480 * o.B;
        l = l * l * l; m = m * m * m; s = s * s * s;
        static double C(double v) => System.Math.Clamp(v, 0, 1);
        return (C(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
                C(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
                C(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s));
    }

    /// <summary>A target colour with its Oklab lightness held to [lo, hi] (hue and chroma kept).</summary>
    public static (double R, double G, double B) ClampL((double R, double G, double B) c, double lo, double hi)
    {
        var o = ToOklab(c);
        double L = System.Math.Clamp(o.L, lo, hi);
        return L == o.L ? c : FromOklab((L, o.A, o.B));
    }
}
