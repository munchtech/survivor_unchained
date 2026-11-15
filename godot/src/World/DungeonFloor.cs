using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A dungeon's floor, by rule from its walkable field (shaders/dungeon_floor.gdshader): the den's packed warm earth,
/// darker at the walls' feet and black down its pits; the ravine's cobbled warm dirt with thin grass away from the edge.
/// The field rides a texture (r: metres inside the walkable edge, MapBuild.WallField; g: metres outside the holes,
/// HoleField), so the floor knows where it is without a splat.
/// </summary>
public static class DungeonFloor
{
    static ZoneData? fieldOf;
    static ImageTexture? field;

    /// <summary>The walkable field as a texture (r: metres inside the edge; g: metres outside the holes), one per zone.</summary>
    public static ImageTexture Field(ZoneData z)
    {
        if (fieldOf == z && field != null) return field;
        int n = z.Res;
        var img = Image.CreateEmpty(n, n, false, Image.Format.Rgh);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
                img.SetPixel(i, j, new Color(z.WallField![j * n + i], z.HoleField?[j * n + i] ?? 8f, 0));
        fieldOf = z;
        return field = ImageTexture.CreateFromImage(img);
    }

    public static ShaderMaterial Material(ZoneData z)
    {
        bool ravine = z.DungeonTheme == "ravine";
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_floor.gdshader") };
        mat.SetShaderParameter("field", Field(z));
        mat.SetShaderParameter("half_size", z.Half);
        mat.SetShaderParameter("step", z.Step);
        mat.SetShaderParameter("res", (float)z.Res);
        mat.SetShaderParameter("sheet", GD.Load<TextureLayered>(ArenaGround.Sheet(ravine ? "res://art/arena/dig" : "res://art/arena/hollow", "albedo")));
        mat.SetShaderParameter("ravine", ravine ? 1f : 0f);
        if (!ravine)
        {
            // (the den's own painted set, ground.json "den": tools/look/ground_paint.py build den)
            mat.SetShaderParameter("den_alb", GD.Load<TextureLayered>("res://art/dungeon/den/albedo.png"));
            mat.SetShaderParameter("den_arh", GD.Load<TextureLayered>("res://art/dungeon/den/arh.png"));
        }
        return mat;
    }
}
