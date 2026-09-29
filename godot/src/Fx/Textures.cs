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

    /// <summary>Once, before any model loads.</summary>
    public static void Mend()
    {
        if (keep.Count > 0) return;
        foreach (var p in Srgb)
        {
            var fixedPath = $"res://art/srgb/{p}.webp";
            if (!ResourceLoader.Exists(fixedPath)) continue;
            var t = GD.Load<Texture2D>(fixedPath);
            t.TakeOverPath($"res://assets/{p}.ktx2");
            keep.Add(t);
        }
    }
}
