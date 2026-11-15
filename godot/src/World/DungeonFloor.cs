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
    public static ShaderMaterial Material(ZoneData z)
    {
        bool ravine = z.DungeonTheme == "ravine";
        int n = z.Res;
        var img = Image.CreateEmpty(n, n, false, Image.Format.Rgh);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
                img.SetPixel(i, j, new Color(z.WallField![j * n + i], z.HoleField?[j * n + i] ?? 8f, 0));
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_floor.gdshader") };
        mat.SetShaderParameter("field", ImageTexture.CreateFromImage(img));
        mat.SetShaderParameter("half_size", z.Half);
        mat.SetShaderParameter("step", z.Step);
        mat.SetShaderParameter("res", (float)n);
        mat.SetShaderParameter("sheet", GD.Load<TextureLayered>(ArenaGround.Sheet(ravine ? "res://art/arena/dig" : "res://art/arena/hollow", "albedo")));
        mat.SetShaderParameter("ravine", ravine ? 1f : 0f);
        return mat;
    }
}
