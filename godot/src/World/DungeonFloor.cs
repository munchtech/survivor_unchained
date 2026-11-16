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
            if (DungeonDress.SetMode > 0 && Args.Num("den-set-floor", 1f) > 0f)   // (den round 10: the painted set's floor tiles)
            {
                mat.SetShaderParameter("set_floor", GD.Load<TextureLayered>("res://art/dungeon/den/set/floor.png"));
                mat.SetShaderParameter("set_k", 1f);
                mat.SetShaderParameter("set_gain", Args.Num("den-set-floor-gain", 1.05f));
                mat.SetShaderParameter("set_band", Args.Num("den-set-band", 0f));       // (r11 0.3 -> 0: it multiplied a blurred copy of the tile back in, clouds)
                mat.SetShaderParameter("set_sharp", Args.Num("den-set-sharp", 1f));     // (r11) the two turns switched, not averaged; tiles read sharper
                mat.SetShaderParameter("set_clouds", Args.Num("den-set-clouds", 0.35f)); // (r11) the slow damp/leaf/value clouds' share under the set
                mat.SetShaderParameter("set_paths", Args.Num("den-set-paths", 1f));     // (r10b) worn ways and damp patches
                mat.SetShaderParameter("set_trod", Args.Num("den-set-trod", 0.5f));     // (r11) the trodden tile's share
                if (Args.Get("den-tint") == null) mat.SetShaderParameter("den_tint", new Vector3(0.93f, 0.92f, 0.96f));   // (r11) the floor's quartiles ran 6-11% too blue against den_room.png
                mat.SetShaderParameter("den_sat", Args.Num("den-sat", 0.68f));   // (r10d 0.55 -> 0.68: the pools' ground read grey-mauve, not warm earth)
            }
        }
        return mat;
    }
}
