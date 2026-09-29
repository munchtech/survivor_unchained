using System;
using System.Globalization;

namespace SurvivorUnchained.World;

/// <summary>
/// The moments of the day (the web game's render/atmosphere.ts PRESETS):
/// night in the wild, night inside walls, dusk, dawn and a hard country's
/// day. Presets blend, so dusk can slide into night over an expedition and
/// dawn can break over a boss's corpse.
/// </summary>
public static class Atmospheres
{
    static readonly GradeSettings NightGrade = new([0.015, 0.025, 0.04], [1.0, 1.0, 1.02], [1.03, 1.0, 0.97],
        "#35646e", "#e6a25a", 0.2, 1.0, 0.14, 1.18);

    public static readonly AtmospherePreset Night = new(
        new SkySettings("#03050d", "#18203a", "#07080c", "#3c5a8c", 24, 1, 1),
        "#b8cbf2", 2.2, 52, 128, 0.6,
        "#3f5780", "#241e16", 0.95, 0.6, "#101a24", 0.0095, 1.42, "#8fb2ff", 0.55, NightGrade);

    /// <summary>Night inside walls: the moon is a cold wash, and what light
    /// there is comes from lamps, doorways and braziers.</summary>
    public static readonly AtmospherePreset NightTown = Night with
    {
        Sky = Night.Sky with { Glow = "#2c4470" },
        KeyColor = "#9fb6e6", KeyIntensity = 1.35, KeyElevation = 48, ShadowStrength = 0.55,
        HemiSky = "#2c3e62", HemiGround = "#1a150f", HemiIntensity = 0.58, EnvIntensity = 0.4,
        FogColor = "#0b121c", FogDensity = 0.011, Exposure = 1.32, Rim = "#86a4e8", RimStrength = 0.42,
        Grade = NightGrade with
        {
            Lift = [0.01, 0.018, 0.035], ShadowTint = "#2a4a66", HighlightTint = "#ffa34e", TintStrength = 0.3,
            Saturation = 0.98, Vibrance = 0.16, Contrast = 1.22,
        },
    };

    public static readonly AtmospherePreset Dusk = new(
        new SkySettings("#141a36", "#b0583a", "#120c0c", "#ff8a4a", 7, 0.25, 0),
        "#ffae70", 2.3, 18, 200, 0.78,
        "#5a5a90", "#2a1a10", 0.7, 0.7, "#3a2a34", 0.0085, 1.05, "#ffb884", 0.32,
        new([0.03, 0.02, 0.05], [1.0, 1.0, 1.02], [1.05, 1.0, 0.95], "#4a4a8a", "#ffb070", 0.2, 1.0, 0.12, 1.16));

    public static readonly AtmospherePreset Dawn = new(
        new SkySettings("#3b5a8f", "#f2b48a", "#2a2220", "#ffd2a0", 6, 0, 0),
        "#ffd1a0", 2.8, 22, 20, 0.8,
        "#8aa0d0", "#3a2a1a", 0.85, 0.85, "#a89aa0", 0.0065, 1.0, "#ffd8b0", 0.2,
        new([0.02, 0.02, 0.04], [1.0, 1.0, 1.0], [1.04, 1.01, 0.97], "#56709a", "#ffc88a", 0.16, 0.96, 0.12, 1.14));

    /// <summary>Day in a hard country: a thin sun through high cloud, cold in
    /// the shadows, the air never quite clear.</summary>
    public static readonly AtmospherePreset Day = new(
        new SkySettings("#4a5a70", "#a8b0b4", "#34302c", "#f0e2c8", 8, 0, 0),
        "#f4e6cc", 2.7, 44, 55, 0.8,
        "#8a9aac", "#3e3226", 0.9, 0.8, "#8e969a", 0.0062, 0.9, "#dfe8f4", 0.16,
        new([0.012, 0.014, 0.022], [1.0, 1.0, 1.0], [1.02, 1.0, 0.97], "#3e5462", "#f0d8b0", 0.16, 0.95, 0.1, 1.12));

    public static AtmospherePreset ByName(string name) => name switch
    {
        "night" => Night, "nightTown" => NightTown, "dusk" => Dusk, "dawn" => Dawn, "day" => Day,
        _ => throw new ArgumentException($"no atmosphere {name}"),
    };

    static double Lerp(double a, double b, double t) => a + (b - a) * t;
    static double[] Lerp3(double[] a, double[] b, double t) => [Lerp(a[0], b[0], t), Lerp(a[1], b[1], t), Lerp(a[2], b[2], t)];

    /// <summary>a blended toward b by t (colours mixed in linear light, as
    /// three.js mixes them).</summary>
    public static AtmospherePreset Blend(AtmospherePreset a, AtmospherePreset b, double t) => new(
        new SkySettings(Mix(a.Sky.Top, b.Sky.Top, t), Mix(a.Sky.Horizon, b.Sky.Horizon, t), Mix(a.Sky.Bottom, b.Sky.Bottom, t),
            Mix(a.Sky.Glow, b.Sky.Glow, t), Lerp(a.Sky.GlowPower, b.Sky.GlowPower, t), Lerp(a.Sky.Stars, b.Sky.Stars, t), Lerp(a.Sky.Moon, b.Sky.Moon, t)),
        Mix(a.KeyColor, b.KeyColor, t), Lerp(a.KeyIntensity, b.KeyIntensity, t), Lerp(a.KeyElevation, b.KeyElevation, t),
        Lerp(a.KeyAzimuth, b.KeyAzimuth, t), Lerp(a.ShadowStrength, b.ShadowStrength, t),
        Mix(a.HemiSky, b.HemiSky, t), Mix(a.HemiGround, b.HemiGround, t), Lerp(a.HemiIntensity, b.HemiIntensity, t),
        Lerp(a.EnvIntensity, b.EnvIntensity, t), Mix(a.FogColor, b.FogColor, t), Lerp(a.FogDensity, b.FogDensity, t),
        Lerp(a.Exposure, b.Exposure, t), Mix(a.Rim, b.Rim, t), Lerp(a.RimStrength, b.RimStrength, t),
        new GradeSettings(Lerp3(a.Grade.Lift, b.Grade.Lift, t), Lerp3(a.Grade.Gamma, b.Grade.Gamma, t), Lerp3(a.Grade.Gain, b.Grade.Gain, t),
            Mix(a.Grade.ShadowTint, b.Grade.ShadowTint, t), Mix(a.Grade.HighlightTint, b.Grade.HighlightTint, t),
            Lerp(a.Grade.TintStrength, b.Grade.TintStrength, t), Lerp(a.Grade.Saturation, b.Grade.Saturation, t),
            Lerp(a.Grade.Vibrance, b.Grade.Vibrance, t), Lerp(a.Grade.Contrast, b.Grade.Contrast, t)));

    /* ------------------------------------------------------------ colour -- */

    /// <summary>'#rrggbb' as linear rgb (three.js's Color.set with colour
    /// management on).</summary>
    public static (double R, double G, double B) Linear(string hex)
    {
        int v = int.Parse(hex.AsSpan(1), NumberStyles.HexNumber);
        return (ToLinear(((v >> 16) & 255) / 255.0), ToLinear(((v >> 8) & 255) / 255.0), ToLinear((v & 255) / 255.0));
    }

    /// <summary>Linear rgb as '#rrggbb' (Color.getHexString).</summary>
    public static string Hex(double r, double g, double b)
    {
        static int C(double x) => (int)Math.Floor(Math.Clamp(ToSrgb(x), 0, 1) * 255 + 0.5);
        return $"#{C(r):x2}{C(g):x2}{C(b):x2}";
    }

    static double ToLinear(double c) => c < 0.04045 ? c * 0.0773993808 : Math.Pow(c * 0.9478672986 + 0.0521327014, 2.4);
    static double ToSrgb(double c) => c < 0.0031308 ? c * 12.92 : 1.055 * Math.Pow(c, 0.41666) - 0.055;

    static string Mix(string a, string b, double t)
    {
        var (ar, ag, ab) = Linear(a);
        var (br, bg, bb) = Linear(b);
        return Hex(Lerp(ar, br, t), Lerp(ag, bg, t), Lerp(ab, bb, t));
    }
}
