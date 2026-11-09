using System;
using System.Collections.Generic;
using System.Text.Json;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Look;

/// <summary>(L1 B4) A lighting rig's key: where it comes from (world azimuth and elevation in degrees for the play rigs,
/// as Atmosphere.Set reads them; for a camera rig, degrees round from the lens toward its right and up), its color
/// (sRGB hex), intensity and cast-shadow opacity. Null: the preset's own. (L1 lead 8, S2b-N2) Scale: a level on the key's
/// intensity, the rig's or the preset's own (so a rig over several places, arena_night, sets the night's level and each place
/// keeps its own moon relative to the others).</summary>
public sealed record RigKey(double? Az = null, double? El = null, string? Color = null, double? Intensity = null, double? Shadow = null, double? Scale = null);

/// <summary>The fill: the cel model's colored fill in the key's shade band (cel_fill's hue, cel_rig.y its share of the
/// key) and the sky's light (the hemisphere's sky and ground hues, its intensity and the environment's). (L1 lead 8, S2b-N2)
/// SkyScale, with no hemi of the rig's own: the preset's own sky light (its hemi times its sky's luminance) kept under the
/// rig's sky color, times this level (a rig over several places recolors their skies and sets the level; each keeps its own).</summary>
public sealed record RigFill(string? Color = null, double? Strength = null, string? Sky = null, string? Ground = null, double? Hemi = null, double? Env = null, double? SkyScale = null);

/// <summary>The stepped rim: its color (sRGB hex), strength (cel_rig.z) and width in 1 - n.v (cel_rig.w; a material
/// class's own step and width multiply it: B2).</summary>
public sealed record RigRim(string? Color = null, double? Strength = null, double? Width = null);

/// <summary>The moon through a canopy (bible rule 9): how much of the sky the crowns close where the canopy stands (0: no
/// dapple), how dark a leaf's shadow is (1: the key wholly off), and the crowns' height over the ground (m).</summary>
public sealed record RigDapple(double? Cover = null, double? Strength = null, double? Height = null, double? Size = null, double? Floor = null);

/// <summary>One rig (godot/data/look/rigs.json): what it is FROM, its key, fill, rim, the ink rig color (B5's, linear rgb),
/// shadow hardness (cel_rig.x), the grade (a named GradeSettings, Atmospheres.GradeNamed), the exposure and her ember's
/// strength (and, L1 C2, its reach and color: ember_reach, ember_color; absent: the preset's), and the canopy's dapple. Camera: the key is camera-relative (the close-up and the Look).
/// (L1 W2) grade_curve: the grade's tone curve on Oklab L ([in, out] pairs; GradeSettings.Curve); warm_keep: the grade's
/// warm-source term (GradeSettings.WarmKeep); ember_give: how the moon gives way to her light in its reach
/// ([key, sky, fade start, gone] as shares; AtmospherePreset.EmberGive). (L1 lead 7 S1) scene_color: the grade's lightness-only
/// term (GradeSettings.SceneColor); (S2) scene_moon: the Moon step after it (GradeSettings.SceneMoon).</summary>
public sealed record LightRig(string Id, string From, bool Camera, RigKey Key, RigFill Fill, RigRim Rim, double[]? Ink,
    double? Hardness, string? Grade, double? Exposure, double? Ember, RigDapple Dapple, double? Fires = null,
    double? EmberReach = null, string? EmberColor = null, double[]? Curve = null, double? WarmKeep = null, double[]? EmberGive = null, double? SceneColor = null, double? SceneMoon = null,
    double[]? EmberPool = null, string? EmberEdge = null)
{
    /// <summary>(B4r2) The fires' light under this rig, a share of their own (1: as built; rule 3, one warm light a scene:
    /// by day the sun is it, and a fire burning by day is a glow at its flames, not a light on her across the square).</summary>
    public double FireShare => Fires ?? 1;
}

/// <summary>The lighting rigs as data (L1 B4; docs/design/LOOK_BIBLE.md rules 1-3, 5, 7-9, 11): every scene's light under
/// the cel model is a rig named by its preset (AtmospherePreset.Rig), so the rig's numbers live in one place. A rig may
/// name a base and change only what differs ("base"). Lit applies a preset's rig under cel; --cel off lights by the preset
/// as it is (Atmosphere.Set never calls it).</summary>
public sealed class RigSet
{
    public readonly Dictionary<string, LightRig> Rigs = new();
    /// <summary>Crown radius (m) and cover (0..1) per flora kind: the canopy mask's trees (CanopyMask).</summary>
    public readonly Dictionary<string, (double R, double Cover)> Crowns = new();

    public LightRig? this[string id] => Rigs.TryGetValue(id, out var r) ? r : null;

    public static RigSet Parse(string json)
    {
        var set = new RigSet();
        using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true });
        var root = doc.RootElement;
        var raw = new Dictionary<string, JsonElement>();
        foreach (var p in root.GetProperty("rigs").EnumerateObject()) raw[p.Name] = p.Value.Clone();
        LightRig Resolve(string id, int depth)
        {
            if (set.Rigs.TryGetValue(id, out var done)) return done;
            if (depth > 8 || !raw.TryGetValue(id, out var e)) throw new FormatException($"rigs.json: no rig {id} (or a base loop)");
            LightRig? b = e.TryGetProperty("base", out var be) ? Resolve(be.GetString()!, depth + 1) : null;
            var r = Read(id, e, b);
            set.Rigs[id] = r;
            return r;
        }
        foreach (var id in raw.Keys) Resolve(id, 0);
        if (root.TryGetProperty("crowns", out var cr))
            foreach (var p in cr.EnumerateObject())
                set.Crowns[p.Name] = (p.Value[0].GetDouble(), p.Value[1].GetDouble());
        return set;
    }

    // (a value: the rig's; null: not the rig's, the preset keeps its own (an arena place's moon); absent: the base's)
    static double? D(JsonElement e, string k, double? b) => e.ValueKind == JsonValueKind.Object && e.TryGetProperty(k, out var v)
        ? v.ValueKind == JsonValueKind.Number ? v.GetDouble() : v.ValueKind == JsonValueKind.Null ? null : throw new FormatException($"rigs.json: {k} is not a number")
        : b;
    static string? S(JsonElement e, string k, string? b) => e.ValueKind == JsonValueKind.Object && e.TryGetProperty(k, out var v)
        ? v.ValueKind == JsonValueKind.String ? v.GetString() : v.ValueKind == JsonValueKind.Null ? null : throw new FormatException($"rigs.json: {k} is not a string")
        : b;
    static JsonElement O(JsonElement e, string k) => e.TryGetProperty(k, out var v) ? v : default;
    // (a list of numbers, or of [x, y] pairs flattened; null: none; absent: the base's)
    static double[]? A(JsonElement e, string k, double[]? b)
    {
        if (!e.TryGetProperty(k, out var v)) return b;
        if (v.ValueKind == JsonValueKind.Null) return null;
        if (v.ValueKind != JsonValueKind.Array) throw new FormatException($"rigs.json: {k} is not a list");
        var r = new List<double>();
        foreach (var x in v.EnumerateArray())
            if (x.ValueKind == JsonValueKind.Array) foreach (var y in x.EnumerateArray()) r.Add(y.GetDouble());
            else r.Add(x.GetDouble());
        return r.ToArray();
    }

    static LightRig Read(string id, JsonElement e, LightRig? b)
    {
        var k = O(e, "key"); var f = O(e, "fill"); var r = O(e, "rim"); var d = O(e, "dapple");
        double[]? ink = b?.Ink;
        if (e.TryGetProperty("ink", out var ie))
        {
            ink = new double[3];
            for (int i = 0; i < 3; i++) ink[i] = ie[i].GetDouble();
        }
        return new LightRig(id,
            S(e, "from", null) ?? throw new FormatException($"rigs.json: {id} names no 'from'"),
            e.TryGetProperty("camera", out var ce) ? ce.GetBoolean() : b?.Camera ?? false,
            new RigKey(D(k, "az", b?.Key.Az), D(k, "el", b?.Key.El), S(k, "color", b?.Key.Color), D(k, "intensity", b?.Key.Intensity), D(k, "shadow", b?.Key.Shadow), D(k, "scale", b?.Key.Scale)),
            new RigFill(S(f, "color", b?.Fill.Color), D(f, "strength", b?.Fill.Strength), S(f, "sky", b?.Fill.Sky), S(f, "ground", b?.Fill.Ground),
                D(f, "hemi", b?.Fill.Hemi), D(f, "env", b?.Fill.Env), D(f, "sky_scale", b?.Fill.SkyScale)),
            new RigRim(S(r, "color", b?.Rim.Color), D(r, "strength", b?.Rim.Strength), D(r, "width", b?.Rim.Width)),
            ink, D(e, "hardness", b?.Hardness), S(e, "grade", b?.Grade), D(e, "exposure", b?.Exposure), D(e, "ember", b?.Ember),
            new RigDapple(D(d, "cover", b?.Dapple.Cover), D(d, "strength", b?.Dapple.Strength), D(d, "height", b?.Dapple.Height), D(d, "size", b?.Dapple.Size), D(d, "floor", b?.Dapple.Floor)),
            D(e, "fires", b?.Fires), D(e, "ember_reach", b?.EmberReach), S(e, "ember_color", b?.EmberColor),
            A(e, "grade_curve", b?.Curve), D(e, "warm_keep", b?.WarmKeep), A(e, "ember_give", b?.EmberGive), D(e, "scene_color", b?.SceneColor), D(e, "scene_moon", b?.SceneMoon),
            A(e, "ember_pool", b?.EmberPool), S(e, "ember_edge", b?.EmberEdge));
    }
}

public static class Rigs
{
    /// <summary>The rigs the game lights by (the Godot side loads godot/data/look/rigs.json at start; tests set their own).</summary>
    public static RigSet Current { get; set; } = new();

    /// <summary>The preset as its rig lights it under the cel model: the rig's key, fill, rim, ink, hardness, grade,
    /// exposure, ember and dapple over the preset's own; what is not the rig (sky, fog, air, river, frost) stays the
    /// preset's. A preset naming no rig (or one not in the set) is returned as it is; so is one already lit.</summary>
    public static AtmospherePreset Lit(AtmospherePreset p) => Lit(p, Current);

    public static AtmospherePreset Lit(AtmospherePreset p, RigSet set)
    {
        if (p.IsLit) return p;
        if (p.CelTwin is { } twin) return twin;
        if (p.Rig == "" || set[p.Rig] is not { } r || r.Camera) return p;
        var k = r.Key; var f = r.Fill; var m = r.Rim;
        return p with
        {
            KeyAzimuth = k.Az ?? p.KeyAzimuth, KeyElevation = k.El ?? p.KeyElevation, KeyColor = k.Color ?? p.KeyColor,
            KeyIntensity = (k.Intensity ?? p.KeyIntensity) * (k.Scale ?? 1), ShadowStrength = k.Shadow ?? p.ShadowStrength,
            CelFillColor = f.Color ?? p.CelFillColor, CelFill = f.Strength ?? p.CelFill,
            HemiSky = f.Sky ?? p.HemiSky, HemiGround = f.Ground ?? p.HemiGround, HemiIntensity = f.Hemi ?? (f.SkyScale is { } ss ? p.HemiIntensity * SkyLum(p.HemiSky) / Math.Max(SkyLum(f.Sky ?? p.HemiSky), 1e-4) * ss : p.HemiIntensity), EnvIntensity = f.Env ?? p.EnvIntensity,
            CelRimColor = m.Color ?? p.CelRimColor, CelRim = m.Strength ?? p.CelRim, CelRimWidth = m.Width ?? p.CelRimWidth,
            CelInk = r.Ink is { } ink ? ink : p.CelInk, CelShadow = r.Hardness ?? p.CelShadow,
            Grade = Graded(r.Grade is { } g ? Atmospheres.GradeNamed(g) ?? p.Grade : p.Grade, r),
            EmberGive = r.EmberGive ?? p.EmberGive,
            EmberPool = r.EmberPool ?? p.EmberPool, EmberEdge = r.EmberEdge ?? p.EmberEdge,
            Exposure = r.Exposure ?? p.Exposure, Ember = r.Ember ?? p.Ember,
            EmberReach = r.EmberReach ?? p.EmberReach, EmberColor = r.EmberColor ?? p.EmberColor,
            DappleCover = r.Dapple.Cover ?? p.DappleCover, DappleStrength = r.Dapple.Strength ?? p.DappleStrength,
            DappleHeight = r.Dapple.Height ?? p.DappleHeight, DappleSize = r.Dapple.Size ?? p.DappleSize, DappleFloor = r.Dapple.Floor ?? p.DappleFloor,
            IsLit = true, CelTwin = null, Source = p,
        };
    }

    /// <summary>(S2b-N2) An sRGB hex's linear luminance (0.05 if it is not one).</summary>
    static double SkyLum(string hex) => SurvivorUnchained.Content.NpcDyePick.Hex(hex) is { } c ? SurvivorUnchained.Content.NpcDyePick.Lum(c) : 0.05;

    /// <summary>(L1 W2) The rig's grade with its tone curve and warm-source term over it (absent: the grade's own).</summary>
    static GradeSettings Graded(GradeSettings g, LightRig r) =>
        r.Curve == null && r.WarmKeep == null && r.SceneColor == null && r.SceneMoon == null ? g
            : g with { Curve = r.Curve ?? g.Curve, WarmKeep = r.WarmKeep ?? g.WarmKeep, SceneColor = r.SceneColor ?? g.SceneColor, SceneMoon = r.SceneMoon ?? g.SceneMoon };
    /// <summary>A camera rig's key direction in the camera's frame: (right, up, back) of the unit vector toward the light,
    /// for az degrees round from the lens toward its right and el up (GameLookdev's --lookdev-key convention).</summary>
    public static (double Right, double Up, double Back) CameraKey(double az, double el)
    {
        double a = az * Math.PI / 180, e = el * Math.PI / 180;
        return (Math.Sin(a) * Math.Cos(e), Math.Sin(e), Math.Cos(a) * Math.Cos(e));
    }

    /// <summary>The canopy's mask over a zone (L1 B4, bible rule 9): res x res bytes, row by row from -z, each the share of
    /// the sky the crowns close there (0..255), from the trees' placement (x, z, kind, scale) and RigSet.Crowns' radius and
    /// cover per kind; a crown is a disc with a soft metre-wide edge, and crowns overlapping take the larger.</summary>
    public static byte[] CanopyMask(IEnumerable<(double X, double Z, string Kind, double Scale)> trees, RigSet set, double size, int res)
    {
        var m = new float[res * res];
        double px = size / res, half = size / 2;
        foreach (var (x, z, kind, scale) in trees)
        {
            if (!set.Crowns.TryGetValue(kind, out var c) || c.Cover <= 0) continue;
            double r = c.R * Math.Max(scale, 0.1), edge = 1.0;
            int i0 = Math.Max(0, (int)((x + half - r - edge) / px)), i1 = Math.Min(res - 1, (int)((x + half + r + edge) / px));
            int j0 = Math.Max(0, (int)((z + half - r - edge) / px)), j1 = Math.Min(res - 1, (int)((z + half + r + edge) / px));
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    double dx = (i + 0.5) * px - half - x, dz = (j + 0.5) * px - half - z;
                    double t = Math.Clamp((r + edge * 0.5 - Math.Sqrt(dx * dx + dz * dz)) / edge, 0, 1);
                    float v = (float)(c.Cover * t * t * (3 - 2 * t));
                    if (v > m[j * res + i]) m[j * res + i] = v;
                }
        }
        var b = new byte[res * res];
        for (int i = 0; i < b.Length; i++) b[i] = (byte)Math.Round(m[i] * 255);
        return b;
    }

    /// <summary>sRGB hex to linear rgb (the ink rig's and the tests' colors).</summary>
    public static (double R, double G, double B) Linear(string hex) => Atmospheres.Linear(hex);
}
