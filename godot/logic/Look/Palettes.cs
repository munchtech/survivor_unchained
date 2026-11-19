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
/// <summary>(lane J, night glow) A palette's light sources: cap, stem and light colours (sRGB hex), the light's energy and range (m),
/// the share of tree feet that get a cluster, the most clusters in a zone, the mushrooms a cluster [min, max], the cap radius [min, max] (m).
/// (lead 2: the woods alone put no cluster in the opening frame (one a 97 m2, most under a crown): the clusters now also line the
/// zone's walked paths, "paths" by name, one every "step" m, "side" [min, max] m off the centre line, a light on "path_light" of
/// them and on "wood_light" of the woods' ones; "alt" a second source (cap, light colours) on "alt_share" of the clusters.)</summary>
public sealed record PaletteGlow(string Cap, string Stem, string Light, double Energy, double Range, double Share, int Max, int CapsMin, int CapsMax, double SizeMin, double SizeMax,
    string[]? Paths = null, double Step = 4, double SideMin = 2.8, double SideMax = 4.4, double PathLight = 0.5, double WoodLight = 0.25,
    string AltCap = "#e8c8ff", string AltLight = "#b070ff", double AltShare = 0);

public static class Palettes
{
    public static PaletteGlow? ReadGlow(JsonElement e)
    {
        if (!e.TryGetProperty("glow", out var g) || g.ValueKind != JsonValueKind.Object) return null;
        double D(string k, double d) => g.TryGetProperty(k, out var v) ? v.GetDouble() : d;
        string S(string k, string d) => g.TryGetProperty(k, out var v) ? v.GetString()! : d;
        var caps = g.TryGetProperty("caps", out var c) ? (c[0].GetInt32(), c[1].GetInt32()) : (3, 7);
        var size = g.TryGetProperty("size", out var z) ? (z[0].GetDouble(), z[1].GetDouble()) : (0.08, 0.22);
        var side = g.TryGetProperty("side", out var sd) ? (sd[0].GetDouble(), sd[1].GetDouble()) : (2.8, 4.4);
        string[]? paths = g.TryGetProperty("paths", out var ps) ? System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(ps.EnumerateArray(), x => x.GetString()!)) : null;
        return new PaletteGlow(S("cap", "#bff8ff"), S("stem", "#5fd0e0"), S("light", "#55e0ff"), D("energy", 1.6), D("range", 3.2), D("share", 0.45), (int)D("max", 40), caps.Item1, caps.Item2, size.Item1, size.Item2,
            paths, D("step", 4), side.Item1, side.Item2, D("path_light", 0.5), D("wood_light", 0.25), S("alt_cap", "#e8c8ff"), S("alt_light", "#b070ff"), D("alt_share", 0));
    }

    /// <summary>The classes in their order (the shader's PAL_* index).</summary>
    public static readonly string[] Classes = ["leaf", "grass", "ground", "path", "stone", "bark"];
    public const int Row = 12;
    public const int EmberAt = 6 * Row;   // (ember: near m, far m, keep, 0: within near m of her light the palette is taken back by keep, none again at far m)
    public const int ValueAt = EmberAt + 4;   // (lead 2: each class its own "value", default the palette's: [leaf, grass, ground, path], [stone, bark, 0, 0])
    public static int Size => Classes.Length * Row + 12;

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
        if (e.TryGetProperty("ember", out var em))
        {
            r[EmberAt] = em.TryGetProperty("near", out var n) ? n.GetDouble() : 0;
            r[EmberAt + 1] = em.TryGetProperty("far", out var f) ? f.GetDouble() : 0;
            r[EmberAt + 2] = em.TryGetProperty("keep", out var kp) ? kp.GetDouble() : 0;
        }
        // (value: 0 the ramp's own value, 1 the albedo's own luminance kept and only the ramp's hue and chroma taken, so the
        // lanes' tuned values hold and only the colour turns; saturated albedos at the sun's full value clip to white)
        r[EmberAt + 3] = e.TryGetProperty("value", out var vk) ? vk.GetDouble() : 0;
        // (lead 2: one value for every class clipped the day's bright bushes at .4 and flattened the sand path at .8: a class
        // may name its own, e.g. the path its ramp's value (low), the leaves the albedo's (high))
        for (int c = 0; c < Classes.Length; c++)
            r[ValueAt + c] = e.TryGetProperty(Classes[c], out var kc) && kc.TryGetProperty("value", out var cv) ? cv.GetDouble() : r[EmberAt + 3];
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
            r[EmberAt + 2] *= k;
            return r;
        }
        var m = new double[a.Length];
        for (int i = 0; i < m.Length; i++) m[i] = a[i] + (b[i] - a[i]) * t;
        return m;
    }
}
