using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The colour textures, as Godot should have them. The shared assets carry
/// their colour sheets as KTX2 (Basis UASTC, sRGB) for the web game; Godot
/// 4.5.1 decodes those to linear values and then samples them as sRGB again,
/// so every painted surface came out too dark and too saturated (cloth,
/// skin, brick, bark). The original images are kept in art/srgb and imported
/// by Godot itself (BC7 or ASTC, with mipmaps); at start they take over the
/// KTX2 paths in the resource cache, so every model that names a KTX2 sheet
/// (the people, the kits, the set dressing) gets the right one without
/// knowing. Normal, roughness and occlusion sheets are linear and stay KTX2.
/// </summary>
public static class Textures
{
    /// <summary>Asset paths (under res://assets, without extension) of the sRGB sheets.</summary>
    static readonly string[] Srgb =
    {
        "env/nature/Bark_DeadTree",
        "env/nature/Bark_NormalTree",
        "env/nature/Bark_TwistedTree",
        "env/nature/Flowers",
        "env/nature/Grass",
        "env/nature/Leaf_Pine_C",
        "env/nature/Leaves",
        "env/nature/Leaves_NormalTree_C",
        "env/nature/Leaves_TwistedTree_C",
        "env/nature/Mushrooms",
        "env/nature/PathRocks_Diffuse",
        "env/nature/Rocks_Diffuse",
        "env/props/T_Page_Noise",
        "env/props/T_Trim_Cloth_BaseColor",
        "env/props/T_Trim_Furniture_BaseColor",
        "env/props/T_Trim_Metal_BaseColor",
        "env/props/T_Trim_Props_BaseColor",
        "env/village/T_Brick_BaseColor",
        "env/village/T_MetalOrnaments_BaseColor",
        "env/village/T_Plaster_BaseColor",
        "env/village/T_RedBrick_BaseColor",
        "env/village/T_RockTrim_BaseColor",
        "env/village/T_RoundTiles_BaseColor",
        "env/village/T_UnevenBrick_BaseColor",
        "env/village/T_VineLeaf_png",
        "env/village/T_WoodTrim_BaseColor",
        "people/T_Eye_Brown",
        "people/T_Hair_1_BaseColor",
        "people/T_Hair_2_BaseColor",
        "people/T_Peasant_BaseColor",
        "people/T_Ranger_BaseColor",
        "people/T_Regular_Female_Dark_BaseColor",
        "people/T_Regular_Male_Dark_BaseColor",
        "people/T_Superhero_Female_Dark_BaseColor",
        "people/T_Superhero_Male_Dark",
    };

    static readonly List<Texture2D> keep = new();

    /// <summary>--kit-paint DIR (style r2, a developer's switch, default off): painted kit
    /// sheets (tools/assets/paint_tex.py) take the place of the sRGB ones where DIR has one by
    /// the same name (T_UnevenBrick_BaseColor.webp ...), so every piece using that sheet changes
    /// (the well and the village houses alike); DIR/kit_paint.json gives the shader weather each
    /// painted sheet is drawn with (KitLook), DIR/folk.json overrides folk looks (ZoneData), and
    /// the cloth stall takes DIR's painted canvas and wood (Landmarks). DIR is a res:// path or
    /// a folder inside the project (as given from the worktree root, or absolute).</summary>
    public static readonly string? KitPaint = ResDir(SurvivorUnchained.Args.Get("kit-paint"));

    static string? ResDir(string? d)
    {
        if (string.IsNullOrEmpty(d) || d == "1") return null;
        if (d.StartsWith("res://")) return d.TrimEnd('/');
        d = d.Replace('\\', '/').TrimEnd('/');
        var proj = ProjectSettings.GlobalizePath("res://").Replace('\\', '/').TrimEnd('/');
        if (System.IO.Path.IsPathRooted(d))
            return d.StartsWith(proj + "/", System.StringComparison.OrdinalIgnoreCase) ? "res://" + d[(proj.Length + 1)..] : null;
        // (relative to the worktree root, as the shot scripts give it: Godot itself runs in godot/)
        var i = d.StartsWith("godot/") ? 0 : d.LastIndexOf("/godot/", System.StringComparison.Ordinal) + 1;
        return "res://" + (i > 0 || d.StartsWith("godot/") ? d[(i + 6)..] : d);
    }

    /// <summary>Under --kit-paint, the shader weather (saturation kept, colour multiply) of a
    /// painted sheet, by the path the models name it by; null for any other.</summary>
    public static (float Sat, Vector3 Tint)? PaintedWeather(Texture2D? t) =>
        t != null && painted.TryGetValue(t.ResourcePath.GetFile().GetBaseName(), out var w) ? w : null;

    static readonly Dictionary<string, (float, Vector3)> painted = new();

    static void LoadWeather()
    {
        var f = $"{KitPaint}/kit_paint.json";
        if (!FileAccess.FileExists(f)) return;
        var doc = System.Text.Json.JsonDocument.Parse(FileAccess.GetFileAsString(f));
        foreach (var e in doc.RootElement.EnumerateObject())
        {
            var t = e.Value.GetProperty("weather_tint");
            painted[e.Name] = ((float)e.Value.GetProperty("weather_sat").GetDouble(),
                new Vector3((float)t[0].GetDouble(), (float)t[1].GetDouble(), (float)t[2].GetDouble()));
        }
    }

    /// <summary>Once, before any model loads.</summary>
    public static void Mend()
    {
        if (keep.Count > 0) return;
        if (KitPaint != null) LoadWeather();
        foreach (var p in Srgb)
        {
            var paintedPath = KitPaint != null ? $"{KitPaint}/{p.GetFile()}.webp" : null;
            bool usePaint = paintedPath != null && ResourceLoader.Exists(paintedPath);
            if (paintedPath != null && !usePaint) painted.Remove(p.GetFile());
            var fixedPath = usePaint ? paintedPath! : $"res://art/srgb/{p}.webp";
            if (!ResourceLoader.Exists(fixedPath)) continue;
            var t = GD.Load<Texture2D>(fixedPath);
            t.TakeOverPath($"res://assets/{p}.ktx2");
            keep.Add(t);
        }
        if (KitPaint != null) GD.Print($"kit-paint: {KitPaint}: {painted.Count} painted sheets");
    }
}
