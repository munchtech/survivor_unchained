using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The zone's water, as the web game lays it (src/render/water.ts): a ribbon
/// down the stream's carved bed, each vertex knowing where it is across and
/// along the stream and how deep the water is over the bed there
/// (data/zones/ZONE/water.*, from tools/godot/export_zone.mjs); still water
/// (a river ford) as a plane. The look is shaders/water.gdshader, coloured
/// as the zone colours it, with what an engine adds (the bed seen through
/// it, bent by the ripples; how murky by how deep it really is).
/// </summary>
public static class Water
{
    public static Node3D Build(ZoneData z)
    {
        var root = new Node3D { Name = "Water" };
        var dir = z.Dir;
        // A zone with no bed of its own keeps a dry ground (the globals outlive the zone).
        RenderingServer.GlobalShaderParameterSet("water_bed", Vector4.Zero);
        if (!FileAccess.FileExists($"{dir}/water.json")) return root;
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString($"{dir}/water.json"));
        var bin = FileAccess.GetFileAsBytes($"{dir}/water.bin");
        int at = 0;
        float[] Floats(int n) { var f = new float[n]; System.Buffer.BlockCopy(bin, at, f, 0, n * 4); at += n * 4; return f; }
        var shader = GD.Load<Shader>("res://shaders/water.gdshader");
        foreach (var w in meta.RootElement.EnumerateArray())
        {
            int nv = w.GetProperty("vertices").GetInt32(), ni = w.GetProperty("indices").GetInt32();
            var pos = Floats(nv * 3);
            var flow = Floats(nv * 2);
            var depth = Floats(nv);
            var idx = new int[ni];
            System.Buffer.BlockCopy(bin, at, idx, 0, ni * 4);
            at += ni * 4;
            var verts = new Vector3[nv];
            var uv = new Vector2[nv];
            var uv2 = new Vector2[nv];
            var nrm = new Vector3[nv];
            for (int i = 0; i < nv; i++)
            {
                verts[i] = new Vector3(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]);
                uv[i] = new Vector2(flow[i * 2], flow[i * 2 + 1]);
                uv2[i] = new Vector2(depth[i], 0);
                nrm[i] = Vector3.Up;
            }
            // Godot's front faces wind the other way from three.js's.
            for (int i = 0; i < ni; i += 3) (idx[i + 1], idx[i + 2]) = (idx[i + 2], idx[i + 1]);
            var arrays = new Godot.Collections.Array();
            arrays.Resize((int)Mesh.ArrayType.Max);
            arrays[(int)Mesh.ArrayType.Vertex] = verts;
            arrays[(int)Mesh.ArrayType.Normal] = nrm;
            arrays[(int)Mesh.ArrayType.TexUV] = uv;
            arrays[(int)Mesh.ArrayType.TexUV2] = uv2;
            arrays[(int)Mesh.ArrayType.Index] = idx;
            var mesh = new ArrayMesh();
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
            var mat = new ShaderMaterial { Shader = shader };
            mat.SetShaderParameter("noise_tex", NoiseTex.Get());
            mat.SetShaderParameter("stream", w.GetProperty("stream").GetBoolean());
            Look(mat, w.GetProperty("look"));
            Bed(w.GetProperty("look"));
            root.AddChild(new MeshInstance3D { Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        }
        return root;
    }

    /// <summary>The water's colours as the zone gives them (WaterOpts: sRGB
    /// hex), any it leaves out as the web game's water has them.</summary>
    public static void Look(ShaderMaterial mat, JsonElement look)
    {
        string Hex(string key, string fallback) => look.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString()! : fallback;
        mat.SetShaderParameter("color", new Color(Hex("color", "#0e1c20")));
        mat.SetShaderParameter("murk", new Color(Hex("murk", "#061012")));
        mat.SetShaderParameter("shallow", new Color(Hex("shallow", "#4a4230")));
        mat.SetShaderParameter("foam_color", new Color(Hex("foam", "#cfd8d4")));
        mat.SetShaderParameter("sky", new Color(Hex("sky", "#1c2c3c")));
        mat.SetShaderParameter("glow", look.TryGetProperty("glow", out var g) && g.ValueKind == JsonValueKind.Number ? g.GetSingle() : 0f);
        var flow = new Vector2(0.02f, 0.35f);
        if (look.TryGetProperty("flow", out var f) && f.ValueKind == JsonValueKind.Array) flow = new Vector2(f[0].GetSingle(), f[1].GetSingle());
        mat.SetShaderParameter("flow", flow);
        // E6: the depth, shore, foam and ripple keys (docs/art/look_bible/04_water_shore.md); any left out as the shader has them.
        foreach (var key in Keys)
            if (look.TryGetProperty(key, out var k) && k.ValueKind == JsonValueKind.Number) mat.SetShaderParameter(key, k.GetSingle());
        if (System.Environment.GetEnvironmentVariable("WATER_DEBUG") is { } dbg && int.TryParse(dbg, out var dv)) mat.SetShaderParameter("debug_view", dv);
    }

    /// <summary>The look's numbers (water.json "look"): clarity (m the bed fades through), deep (m: the body full past it),
    /// shore (m: the sheen fading in from the bank), foam_depth (m: how near the surface a thing breaks it), foam_amt, wake
    /// (m of foam behind a stone or a leg, 0 none), ripple_size (m), ripple_bend, refract, gloss (the glints' roughness).</summary>
    public static readonly string[] Keys = ["clarity", "deep", "shore", "foam_depth", "foam_amt", "wake", "ripple_size", "ripple_bend", "refract", "gloss"];

    /// <summary>The bed and the bank (water.json "look" "bed"; the terrain shader's global water_bed, water_silt): pebbles
    /// (0-1, river stones in the silt), silt (0-1, how far the bed takes the silt's colour), wet (m above the water the bank
    /// is dark and slick), wet_dark (0-1). None: a dry bank and the ground's own paint under the water.</summary>
    public static void Bed(JsonElement look)
    {
        var b = look.TryGetProperty("bed", out var bb) && bb.ValueKind == JsonValueKind.Object ? bb : default;
        float N(string key, float fallback) => b.ValueKind == JsonValueKind.Object && b.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetSingle() : fallback;
        bool on = b.ValueKind == JsonValueKind.Object;
        RenderingServer.GlobalShaderParameterSet("water_bed", on ? new Vector4(N("pebbles", 0.5f), N("silt", 0.6f), N("wet", 0.35f), N("wet_dark", 0.45f)) : Vector4.Zero);
        string silt = on && b.TryGetProperty("silt_color", out var sc) && sc.ValueKind == JsonValueKind.String ? sc.GetString()! : "#4a4234";
        RenderingServer.GlobalShaderParameterSet("water_silt", new Color(silt).SrgbToLinear());
    }
}
