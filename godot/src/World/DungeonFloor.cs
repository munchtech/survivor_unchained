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
                img.SetPixel(i, j, new Color(z.DungeonTheme == "den" && z.HoleField != null ? DungeonWalls.WallOnly(z.WallField![j * n + i], z.HoleField[j * n + i]) : z.WallField![j * n + i], z.HoleField?[j * n + i] ?? 8f, 0));   // (the den's pits are not walls: DungeonWalls.Ctx.S)
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
        // --env-off rim: the damp lip, wall-foot and pit darkening off (the den pit halo diagnosis, 15 Nov).
        if (System.Array.IndexOf((Args.Get("env-off") ?? "").Split(','), "rim") >= 0) mat.SetShaderParameter("rim_dark", 0f);
        if (!ravine)
        {
            // (the den's own painted set, ground.json "den": tools/look/ground_paint.py build den)
            mat.SetShaderParameter("den_alb", GD.Load<TextureLayered>("res://art/dungeon/den/albedo.png"));
            mat.SetShaderParameter("den_arh", GD.Load<TextureLayered>("res://art/dungeon/den/arh.png"));
            if (DungeonDress.PitDecals) mat.SetShaderParameter("pit_decals", 1f);
            foreach (var r in z.Rooms)
                if (r.Kind == "Boss") mat.SetShaderParameter("boss_c", new Vector3(r.X, r.Z, r.R));
            mat.SetShaderParameter("open_lift", Args.Num("den-open-lift", 1.08f));
            mat.SetShaderParameter("boss_dim", Args.Num("den-boss-dim", 0.95f));
            // (round 8) the earth's tint and the moss tongues' share, for steering the value bands against the targets
            if (Args.Get("den-tint") is string dt && dt.Split(',') is { Length: 3 } tp)
                mat.SetShaderParameter("den_tint", new Vector3(float.Parse(tp[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(tp[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(tp[2], System.Globalization.CultureInfo.InvariantCulture)));
            mat.SetShaderParameter("moss_k", Args.Num("den-moss", 0.35f));
            mat.SetShaderParameter("den_sat", Args.Num("den-sat", 0.65f));
        }
        return mat;
    }
}
