using System;
using System.Text.Json;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Look;

/// <summary>(lane J art-color, 19 Nov; the owner's day and night reference, owner_ref_night_day_colors_19nov) The world's
/// colour per time of day, as data: rigs.json "palettes", named by a rig's "palette", carried on the air
/// (AtmospherePreset.Palette), blended by the clock (Atmospheres.Blend) and set as shader globals (Atmosphere.SetPalette;
/// shaders/palette.gdshaderinc). Each class is a ramp of three colours (dark, mid, lit) laid over the albedo's own value
/// (the square root of its linear luminance, from lo to hi), so a surface keeps its painted variation and takes the time's hue: autumn by day,
/// violet and teal by night. Only the world's classes take it: her skin, hair, eyes and gear never do (lane E's skin band).
/// Flattened per class: [dark r g b (linear), amount, mid r g b, lo, lit r g b, hi].</summary>
public static class Palettes
{
    /// <summary>The classes in their order (the shader's PAL_* index).</summary>
    public static readonly string[] Classes = ["leaf", "grass", "ground", "path", "stone", "bark"];
    public const int Row = 12;
    public static int Size => Classes.Length * Row;

    public static double[] Read(string name, JsonElement e)
    {
        var r = new double[Size];
        for (int c = 0; c < Classes.Length; c++)
        {
            if (!e.TryGetProperty(Classes[c], out var k)) continue;   // (absent: amount 0, the class as built)
            var ramp = k.GetProperty("ramp");
            if (ramp.GetArrayLength() != 3) throw new FormatException($"rigs.json palette {name}.{Classes[c]}: ramp needs 3 colours");
            var range = k.TryGetProperty("range", out var rg) ? (rg[0].GetDouble(), rg[1].GetDouble()) : (0.15, 0.55);
            int o = c * Row;
            for (int i = 0; i < 3; i++)
            {
                var (R, G, B) = Atmospheres.Linear(ramp[i].GetString()!);
                r[o + i * 4] = R; r[o + i * 4 + 1] = G; r[o + i * 4 + 2] = B;
            }
            r[o + 3] = k.TryGetProperty("amount", out var am) ? am.GetDouble() : 1;
            r[o + 7] = range.Item1;
            r[o + 11] = Math.Max(range.Item2, range.Item1 + 1e-3);
        }
        return r;
    }

    /// <summary>a toward b by t; a missing palette is the other's with its amounts faded (the class as built at the end).</summary>
    public static double[]? Blend(double[]? a, double[]? b, double t)
    {
        if (t <= 0) return a;
        if (t >= 1) return b;
        if (a == null && b == null) return null;
        if (a == null || b == null)
        {
            var src = a ?? b!;
            double k = a == null ? t : 1 - t;
            var r = (double[])src.Clone();
            for (int c = 0; c < Classes.Length; c++) r[c * Row + 3] *= k;
            return r;
        }
        var m = new double[a.Length];
        for (int i = 0; i < m.Length; i++) m[i] = a[i] + (b[i] - a[i]) * t;
        return m;
    }
}
