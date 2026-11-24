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
                mat.SetShaderParameter("set_paths", Args.Num("den-set-paths", 1f));
                mat.SetShaderParameter("set_damp", Args.Num("den-set-damp", 0.45f));   // (r13) the damp patches in the open (1: the r12 smudge)     // (r10b) worn ways and damp patches
                mat.SetShaderParameter("set_trod", Args.Num("den-set-trod", 0.5f));     // (r11) the trodden tile's share
                mat.SetShaderParameter("boss_dim", Args.Num("den-boss-dim", 2.3f));     // (r12, with the gloom and the lair pools x0.45: median 67, 12-35 12 %, cool 18.7 % against 68 / 13 / 18.8)     // (r11) the lair measured median 42 against 68 (1.3: 56)
                mat.SetShaderParameter("boss_damp", Args.Num("den-boss-damp", 1.0f));
                mat.SetShaderParameter("boss_gloom", DungeonDress.SetBossGloom);
                mat.SetShaderParameter("gloom_tint", DungeonDress.V3("den-gloom-tint", SurvivorUnchained.View.DenShade.On ? Vector3.One : new Vector3(1.22f, 1.0f, 0.74f)));   // (den r14 judge r13 item 5: the lair's off-light floor falls to warm umber h35-50, was cool/mauve)
                mat.SetShaderParameter("open_grit", Args.Num("den-grit", 0.5f));
                mat.SetShaderParameter("gloom_mix", Args.Num("den-gloom-mix", 0.5f));
                mat.SetShaderParameter("den_chroma", Args.Num("den-chroma", 0.3f));   // (r12: the seed-23 room satShade .35 -> about .2, den_room.png .21)
                mat.SetShaderParameter("den_chroma_hi", Args.Num("den-chroma-hi", 0.22f));   // (r12) its pools in the middle, dark and cool toward the walls
                mat.SetShaderParameter("boss_dry", Args.Num("den-boss-dry", 0.8f));
                mat.SetShaderParameter("boss_sat", SurvivorUnchained.View.DenShade.Num("den-boss-sat", 0f, 0.8f));
                mat.SetShaderParameter("boss_tint", DungeonDress.V3("den-boss-tint", DenShade.On ? new Vector3(0.4f, 0.4f, 0.4f) : new Vector3(0.94f, 0.92f, 0.74f)));   // (den r15 lead: x0.92, lair Lp50 .386 -> .375, lit h 49.8 kept; lane E: the lair too bright)
                if (Args.Get("den-tint") == null) mat.SetShaderParameter("den_tint", SurvivorUnchained.View.DenShade.On ? SurvivorUnchained.View.DenShade.Tint : new Vector3(0.82f, 0.79f, 0.74f));   // (r11 judge: lit (146,104,85) -> (134,95,73))
                  // (r11) the lit floor (150,105,86) against den_room.png (134,95,73): (0.93,0.92,0.96) read pink
                mat.SetShaderParameter("den_sat", SurvivorUnchained.View.DenShade.Num("den-sat", 0f, 0.75f));   // (cool shade lane: the earth's own orange down under the violet shade, or it reads brown-pink)   // (r11 0.68 -> 0.75: 0.55 read pink-grey; the warmth is the lit earth's, den_room.png)   // (r10d 0.55 -> 0.68: the pools' ground read grey-mauve, not warm earth)
            }
        }
        return mat;
    }
}
