using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The zone's ground: a heightfield mesh from the exported heights, shaded by
/// shaders/terrain.gdshader with the photoscanned materials in art/ground.
/// </summary>
public static class Ground
{
    public static MeshInstance3D Build(ZoneData z)
    {
        int n = z.Res;
        var verts = new Vector3[n * n];
        var normals = new Vector3[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
                verts[j * n + i] = new Vector3(-z.Half + i * z.Step, z.Heights[j * n + i], -z.Half + j * z.Step);
        // Normals from the neighbours' heights (central differences).
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float hl = z.Heights[j * n + Mathf.Max(i - 1, 0)], hr = z.Heights[j * n + Mathf.Min(i + 1, n - 1)];
                float hd = z.Heights[Mathf.Max(j - 1, 0) * n + i], hu = z.Heights[Mathf.Min(j + 1, n - 1) * n + i];
                normals[j * n + i] = new Vector3(hl - hr, 2 * z.Step, hd - hu).Normalized();
            }
        var idx = new int[(n - 1) * (n - 1) * 6];
        int p = 0;
        for (int j = 0; j < n - 1; j++)
            for (int i = 0; i < n - 1; i++)
            {
                int a = j * n + i, b = a + 1, c = a + n, d = c + 1;
                // Alternate the diagonal so slopes do not all crease the same
                // way (as the web game); wound clockwise, as Godot draws front faces.
                if (((i + j) & 1) == 1) { idx[p++] = a; idx[p++] = b; idx[p++] = c; idx[p++] = b; idx[p++] = d; idx[p++] = c; }
                else { idx[p++] = a; idx[p++] = d; idx[p++] = c; idx[p++] = a; idx[p++] = b; idx[p++] = d; }
            }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts;
        arrays[(int)Mesh.ArrayType.Normal] = normals;
        arrays[(int)Mesh.ArrayType.Index] = idx;
        // An arena's ground knows, vertex by vertex, how far inside its ring it
        // is: eased in COLOR (the dark past it), and in metres in CUSTOM0, a float,
        // because the lip is drawn along it as a line a hand wide.
        var flags = (Mesh.ArrayFormat)0;
        if (z.Inside is double[] inside)
        {
            var cols = new Color[n * n];
            var metres = new float[n * n];
            for (int k = 0; k < cols.Length; k++)
            {
                cols[k] = new Color(Mathf.SmoothStep(-16f, -3f, (float)inside[k]), 0, 0);
                metres[k] = (float)inside[k];
            }
            arrays[(int)Mesh.ArrayType.Color] = cols;
            arrays[(int)Mesh.ArrayType.Custom0] = metres;
            flags = (Mesh.ArrayFormat)((long)Mesh.ArrayCustomFormat.RFloat << (int)Mesh.ArrayFormat.FormatCustom0Shift);
        }
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays, null, null, flags);
        if (z.Place != null)
        {
            mesh.SurfaceSetMaterial(0, ArenaGround.Material(z));
            return Finish(z, mesh);
        }

        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/terrain.gdshader") };
        // The paint reconciled with the roads, and the road, wet and puddle mask (GroundPaint.cs).
        var paint = GroundPaint.Ahead(z);
        var splat = ImageTexture.CreateFromImage(WithMips(paint.Splat));
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("splat", splat);
        mat.SetShaderParameter("paint_mask", ImageTexture.CreateFromImage(paint.Mask));
        mat.SetShaderParameter("mask_texel", z.Size / paint.Mask.GetWidth());
        mat.SetShaderParameter("g_alb", GD.Load<TextureLayered>("res://art/ground/albedo.jpg"));
        mat.SetShaderParameter("g_nor", GD.Load<TextureLayered>("res://art/ground/normal.jpg"));
        mat.SetShaderParameter("g_arh", GD.Load<TextureLayered>("res://art/ground/arh.jpg"));
        // The setts' 2K variants: only where the paint lays setts (64 MB of VRAM otherwise idle).
        bool setts = HasSetts(paint.Splat);
        // Style r2 (--setts-paint): the painted setts (env_ground.py --paint; the same sizes and layers) and their mud.
        bool sp = SurvivorUnchained.Args.Has("setts-paint");
        string st = sp ? "res://art/ground/setts_paint_" : "res://art/ground/setts_";
        mat.SetShaderParameter("s_alb", GD.Load<TextureLayered>(setts ? st + "albedo.jpg" : "res://art/ground/albedo.jpg"));
        mat.SetShaderParameter("s_nor", GD.Load<TextureLayered>(setts ? st + "normal.jpg" : "res://art/ground/normal.jpg"));
        mat.SetShaderParameter("s_arh", GD.Load<TextureLayered>(setts ? st + "arh.jpg" : "res://art/ground/arh.jpg"));
        // Picture switches for the sweeps (look bible 1f); the defaults are the chosen values.
        mat.SetShaderParameter("h_amp", SurvivorUnchained.Args.Num("ground-h-amp", 1.0f));
        mat.SetShaderParameter("h_depth", SurvivorUnchained.Args.Num("ground-h-depth", 0.08f));
        mat.SetShaderParameter("edge_k", SurvivorUnchained.Args.Num("ground-edge-k", 1.6f));
        mat.SetShaderParameter("macro_amt", SurvivorUnchained.Args.Num("ground-macro", 1.0f));
        var zg = FloraSpecies.GroundFor(z.Id);
        mat.SetShaderParameter("rut_depth", SurvivorUnchained.Args.Num("ground-rut-depth", zg.TryGetValue("rut_depth", out var zrd) ? zrd : 0.018f));
        mat.SetShaderParameter("wet_amt", SurvivorUnchained.Args.Num("ground-wet", 1.0f));
        mat.SetShaderParameter("debug_view", (int)SurvivorUnchained.Args.Num("ground-debug", 0f));
        mat.SetShaderParameter("expo_tex", paint.Exposure);
        mat.SetShaderParameter("frost_tone", SurvivorUnchained.Args.Num("frost-tone", 1.7f));
        mat.SetShaderParameter("frost_cap", SurvivorUnchained.Args.Num("frost-cap", 0.1f));
        mat.SetShaderParameter("frost_reach", SurvivorUnchained.Args.Num("frost-reach", 0.5f));
        mat.SetShaderParameter("meadow_amt", SurvivorUnchained.Args.Num("ground-meadow", 1f));
        mat.SetShaderParameter("warm_at", WarmAt(z));
        // Judge 1's fix round (E3 C): what stands near the ground, and its switches.
        mat.SetShaderParameter("near_tex", paint.Near);
        foreach (var (u, sw, v) in new[] { ("rut_dark", "ground-rut-dark", 0.45f), ("crown_lift", "ground-crown", 0.12f), ("grime", "setts-grime", 0.08f),
            ("gutter_w", "setts-gutter", 0.4f), ("lane_lift", "setts-lane", 0.32f), ("edge_drop", "setts-edge-drop", 0.6f), ("weeds", "setts-weeds", 1f),
            ("meadow_val", "ground-meadow-val", 0.13f), ("frost_crisp", "frost-crisp", 1f), ("frost_dawn", "frost-dawn", 0.12f), ("frost_soft", "frost-soft", 0.3f), ("setts_bump", "setts-bump", 0.32f), ("night_dew", "ground-night-dew", 0.35f), ("pud_dark", "ground-pud-dark", 0.45f), ("night_spec", "ground-night-spec", 0.12f),
            ("verge_soft", "ground-verge-soft", 0.8f), ("rut_sun", "ground-rut-sun", 0.35f), ("pud_rim", "ground-pud-rim", 0.45f), ("mirror_amt", "ground-mirror", 1f), ("mirror_rut", "ground-mirror-rut", 1f), ("night_tuft", "ground-night-tuft", 1f), ("night_val", "ground-night-val", 0.7f),
            ("setts_mud", "setts-mud", 1f), ("setts_reach", "setts-reach", 1.5f), ("setts_moss", "setts-moss", 1f), ("setts_collar", "setts-collar", 0f), ("mud_tone", "setts-mud-tone", 1f), ("mud_sat", "setts-mud-sat", 1.45f), ("mud_spec", "setts-mud-spec", 0.1f), ("mud_paint", "setts-mud-paint", 0f), ("mud_ao", "setts-mud-ao", 0.8f), ("mud_warm", "setts-mud-warm", 1f),
                 ("setts_kerb", "setts-kerb", 1f), ("setts_wild", "setts-wild", 0f), ("setts_ruts", "setts-ruts", 0f), ("kerb_in", "setts-kerb-in", 0.28f), ("kerb_w", "setts-kerb-w", 0.3f), ("setts_turn", "setts-turn", 1f), ("setts_lf", "setts-lf", 1f), ("mud_pool", "setts-mud-pool", 1f), ("close_bump", "setts-close-bump", 2.2f),
                 ("rut_soft", "ground-rut-soft", 0f), ("rut_blur", "ground-rut-blur", 0.3f), ("road_rime", "ground-road-rime", 1f), ("crown_grass", "ground-crown-grass", 0.45f), ("pud_night", "ground-pud-night", 0f), ("pud_mud", "ground-pud-mud", 0f), ("pud_sheen", "ground-pud-sheen", 0f),
                 ("foot_damp", "ground-foot-damp", 0f), ("foot_w", "ground-foot-w", 0.6f),
                 ("camp_scorch", "ground-camp-scorch", 0f), ("scorch_r", "ground-scorch-r", 1f), ("trample", "ground-trample", 0f), ("path_hw", "ground-path-hw", 0.2f), ("path_lift", "ground-path-lift", 0f),
                 ("mud_night_floor", "setts-mud-night-floor", 0.75f), ("mud_night_wet", "setts-mud-night-wet", 1f), ("road_night", "ground-road-night", 0f), ("verge_litter", "ground-verge-litter", 0f), ("verge_mip", "ground-verge-mip", 5f), ("litter_wood", "ground-litter-wood", 0.5f) })
            mat.SetShaderParameter(u, SurvivorUnchained.Args.Num(sw, zg.TryGetValue(u, out var zv) ? zv : sp && PaintDefaults.TryGetValue(u, out var pv) ? pv : v));
        // (E8 later r2) the zone's footpaths (flora_species.json "ground_paths": polylines of [x, z]), as segments
        var segs = FloraSpecies.PathsFor(z.Id);
        int nseg = segs.Count;
        if (nseg > 0) { while (segs.Count < 12) segs.Add(Vector4.Zero); mat.SetShaderParameter("path_seg", segs.ToArray()); }
        mat.SetShaderParameter("path_n", nseg);
        mat.SetShaderParameter("zone_size", z.Size);
        mat.SetShaderParameter("leaves", z.Leaves);
        mat.SetShaderParameter("blight_glow", new Color(z.Meta.BlightGlow));
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString("res://art/ground/ground.json"));
        var scales = new Godot.Collections.Array<float>();
        foreach (var l in meta.RootElement.GetProperty("layers").EnumerateArray()) scales.Add(1f / l.GetProperty("metres").GetSingle());
        // Style r2 (--setts-paint): the painted stones a size up, toward the target's chunkier cobbles (lead 4 at 1:1: 1.35
        // reads as a cobbled square, 1.7 as outlined flagstones; 1.6 with half the value spread after judge r2). --setts-paint-scale N; 1 is the 4 m tile; layer 4 is the setts.
        if (sp) scales[4] /= SurvivorUnchained.Args.Num("setts-paint-scale", 1.6f);
        mat.SetShaderParameter("g_scale", scales);
        mesh.SurfaceSetMaterial(0, mat);
        return Finish(z, mesh);
    }

    /// <summary>The fires' warmth, where no frost lies: (x, z, radius), four at most.</summary>
    public static Vector4[] WarmAt(ZoneData z)
    {
        var w = new Vector4[4];
        for (int i = 0; i < Mathf.Min(4, z.Meta.Fires.Count); i++)
        {
            var f = z.Meta.Fires[i];
            w[i] = new Vector4((float)f.X, (float)f.Z, 2.5f + 2f * (float)f.Size, 0);
        }
        return w;
    }

    static MeshInstance3D Finish(ZoneData z, ArrayMesh mesh)
    {
        int n = z.Res;
        var ground = new MeshInstance3D { Mesh = mesh, Name = "Ground", CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        // What falls lands on it: the same heights as a physics heightmap
        // (one sample a metre here, as the zone's grid is).
        var body = new StaticBody3D { Name = "GroundBody", CollisionLayer = 1 };
        var shape = new HeightMapShape3D { MapWidth = n, MapDepth = n, MapData = z.Heights };
        body.AddChild(new CollisionShape3D { Shape = shape, Scale = new Vector3(z.Step, 1, z.Step) });
        ground.AddChild(body);
        return ground;
    }

    /// <summary>The defaults under --setts-paint (each switch still wins): the mud darker, browner, less saturated, matte
    /// and painted; the wear lane a little lighter.</summary>
    static readonly System.Collections.Generic.Dictionary<string, float> PaintDefaults = new()
    {
        ["mud_tone"] = 0.85f, ["mud_sat"] = 1.3f, ["mud_spec"] = 0.02f, ["mud_paint"] = 1f, ["lane_lift"] = 0.42f,
    };

    /// <summary>Does the paint lay setts anywhere (its G over a third)?</summary>
    static bool HasSetts(Image splat)
    {
        var d = splat.GetData();
        for (int k = 1; k < d.Length; k += 4) if (d[k] > 85) return true;
        return false;
    }

    static Image WithMips(Image img)
    {
        var copy = (Image)img.Duplicate();
        copy.Convert(Image.Format.Rgba8);
        copy.GenerateMipmaps();
        return copy;
    }
}
