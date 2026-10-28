using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
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
    /// <summary>The zone's still water's height (its WATER_Y, set with the global water_level), or none.</summary>
    public static float? Level;
    static readonly List<WeakRef> mats = new();
    static readonly Dictionary<ulong, (Light3D Light, Color Tint)> tints = new();

    /// <summary>A light's streak on the water in its flame's hue (linear sRGB in, as authored), not the light's own colour
    /// (C03: the Warden's amber lantern lit by a #8ac8ff light threw a blue streak). Call as the light moves; null takes
    /// it off. Up to four at once (water.gdshader's streak_at).</summary>
    public static void StreakTint(Light3D light, Color? flame)
    {
        ulong id = light.GetInstanceId();
        if (flame is Color c && light.LightEnergy > 0 && light.Visible) tints[id] = (light, c);
        else if (!tints.Remove(id)) return;
        PushTints();
    }

    static void PushTints()
    {
        var at = new Vector4[4];
        var tint = new Vector3[4];
        int n = 0;
        foreach (var (id, (l, c)) in tints.ToArray())
        {
            if (!GodotObject.IsInstanceValid(l) || !l.IsInsideTree()) { tints.Remove(id); continue; }
            if (n == 4) break;
            var p = l.GlobalPosition;
            var lin = c.SrgbToLinear();
            at[n] = new Vector4(p.X, p.Y, p.Z, 1);
            tint[n++] = new Vector3(lin.R, lin.G, lin.B);
        }
        foreach (var r in mats)
            if (r.GetRef().Obj is ShaderMaterial m) { m.SetShaderParameter("streak_at", at); m.SetShaderParameter("streak_tint", tint); }
    }

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
        // The hand-set look (water_look.json, one object a body of water, in water.json's order) over the exported one: the
        // exporter rewrites water.json, never this.
        var over = FileAccess.FileExists($"{dir}/water_look.json") ? JsonNode.Parse(FileAccess.GetFileAsString($"{dir}/water_look.json")) as JsonArray : null;
        int wi = 0;
        foreach (var w in meta.RootElement.EnumerateArray())
        {
            var look = Merge(w.GetProperty("look"), over != null && wi < over.Count ? over[wi] : null);
            wi++;
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
            mat.SetShaderParameter("grad_tex", Grad());
            mat.SetShaderParameter("stream", w.GetProperty("stream").GetBoolean());
            Look(mat, look);
            Bed(look);
            root.AddChild(new MeshInstance3D { Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            mats.RemoveAll(r => r.GetRef().Obj == null);
            mats.Add(GodotObject.WeakRef(mat));
            PushTints();
        }
        return root;
    }

    static ImageTexture? grad;

    /// <summary>The noise's slopes, once (the shader's grad_tex): RG the slope of its R channel (x, y), BA of its B, per
    /// texel, as 0.5 + slope x 12 (R) and x 6 (B), wrapping as the noise tiles.</summary>
    public static ImageTexture Grad()
    {
        if (grad != null) return grad;
        var src = NoiseTex.Get().GetImage();
        if (src.IsCompressed()) src.Decompress();
        int n = src.GetWidth();
        var px = src.GetData();
        var data = new byte[n * n * 4];
        byte B(double v) => (byte)Math.Clamp(Math.Round(v * 255), 0, 255);
        double At(int x, int y, int c) => px[((((y % n) + n) % n) * n + (((x % n) + n) % n)) * 4 + c] / 255.0;
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                int i = (y * n + x) * 4;
                data[i] = B(0.5 + (At(x + 1, y, 0) - At(x - 1, y, 0)) * 0.5 * 12);
                data[i + 1] = B(0.5 + (At(x, y + 1, 0) - At(x, y - 1, 0)) * 0.5 * 12);
                data[i + 2] = B(0.5 + (At(x + 1, y, 2) - At(x - 1, y, 2)) * 0.5 * 6);
                data[i + 3] = B(0.5 + (At(x, y + 1, 2) - At(x, y - 1, 2)) * 0.5 * 6);
            }
        var img = Image.CreateFromData(n, n, false, Image.Format.Rgba8, data);
        img.GenerateMipmaps();
        return grad = ImageTexture.CreateFromImage(img);
    }

    /// <summary>The exported look with the hand-set one's keys over it (a key in both: the hand-set one; "bed" whole).</summary>
    public static JsonElement Merge(JsonElement look, JsonNode? over)
    {
        if (over is not JsonObject o) return look;
        var n = look.ValueKind == JsonValueKind.Object ? JsonNode.Parse(look.GetRawText()) as JsonObject ?? new JsonObject() : new JsonObject();
        foreach (var (k, v) in o) n[k] = v?.DeepClone();
        return JsonSerializer.SerializeToElement(n);
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
        // (Low Ford r3) the moon glint's hue (sRGB hex; the shader's white as built)
        if (look.TryGetProperty("moon_tint", out var mt) && mt.ValueKind == JsonValueKind.String) mat.SetShaderParameter("moon_tint", new Color(mt.GetString()!));
        mat.SetShaderParameter("glow", look.TryGetProperty("glow", out var g) && g.ValueKind == JsonValueKind.Number ? g.GetSingle() : 0f);
        var flow = new Vector2(0.02f, 0.35f);
        if (look.TryGetProperty("flow", out var f) && f.ValueKind == JsonValueKind.Array) flow = new Vector2(f[0].GetSingle(), f[1].GetSingle());
        mat.SetShaderParameter("flow", flow);
        // E6: the depth, shore, foam and ripple keys (docs/art/look_bible/04_water_shore.md); any left out as the shader has them.
        foreach (var key in Keys)
            if (look.TryGetProperty(key, out var k) && k.ValueKind == JsonValueKind.Number) mat.SetShaderParameter(key, k.GetSingle());
        if (System.Environment.GetEnvironmentVariable("WATER_DEBUG") is { } dbg && int.TryParse(dbg, out var dv)) mat.SetShaderParameter("debug_view", dv);
        // (a look tried without editing the data: WATER_SET="key=v;key=v", any of Keys)
        if (System.Environment.GetEnvironmentVariable("WATER_SET") is { } ws)
            foreach (var kv in ws.Split(';', System.StringSplitOptions.RemoveEmptyEntries))
                if (kv.Split('=') is [var k2, var v2] && System.Array.IndexOf(Keys, k2) >= 0 && float.TryParse(v2, System.Globalization.CultureInfo.InvariantCulture, out var f2)) mat.SetShaderParameter(k2, f2);
    }

    /// <summary>The look's numbers (water.json "look"): clarity (m the bed fades through), deep (m: the body full past it),
    /// shore (m: the sheen fading in from the bank), foam_depth (m: how near the surface a thing breaks it), foam_amt, wake
    /// (m of foam behind a stone or a leg, 0 none), ripple_size (m), ripple_bend, refract, gloss (the glints' roughness),
    /// glint_cap, glint_spread, glint_bend and glint_near (a near light's glint: its roughness, how much steeper its facets, its gain), wake_taper (how fast a wake narrows: length = width / it),
    /// lace_size (m: the shore foam's lace).</summary>
    public static readonly string[] Keys = ["clarity", "deep", "shore", "foam_depth", "foam_amt", "wake", "ripple_size", "ripple_bend", "refract", "gloss", "glint_cap", "glint_spread", "glint_bend", "glint_near", "glint_sheen", "wake_taper", "lace_size", "mirror", "mirror_from", "mirror_to", "mirror_ripple", "streak", "streak_w", "streak_l", "streak_cap", "streak_tame", "streak_h0", "streak_h1", "streak_h2", "streak_h3", "streak_high", "glint_high", "bed_soft", "bed_soft_lod", "bed_soft_depth",
        "moon_rough", "moon_sparse", "moon_gain", "moon_cap", "moon_column", "moon_col_w", "moon_col_l", "moon_break", "lamp_cap", "lamp_pool", "moon_along", "moon_across",
        "foam_emerge", "foam_emerge_r", "moon_taper", "moon_vary", "bank_tint", "bank_depth"];

    /// <summary>The bed and the bank (water.json "look" "bed"; the terrain shader's global water_bed, water_silt): pebbles
    /// (0-1, river stones in the silt), silt (0-1, how far the bed takes the silt's colour), wet (m above the water the bank
    /// is dark and slick), wet_dark (0-1), relief (m: the stones' lit and shaded sides and their tone against the silt fade by
    /// e over it, as the water veils them). None: a dry bank and the ground's own paint under the water.</summary>
    public static void Bed(JsonElement look)
    {
        var b = look.TryGetProperty("bed", out var bb) && bb.ValueKind == JsonValueKind.Object ? bb : default;
        float N(string key, float fallback) => b.ValueKind == JsonValueKind.Object && b.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetSingle() : fallback;
        bool on = b.ValueKind == JsonValueKind.Object;
        // (WATER_NOSTONES: the bed bare, to measure what its stones add)
        float peb = System.Environment.GetEnvironmentVariable("WATER_NOSTONES") is null ? N("pebbles", 0.5f) : 0f;
        RenderingServer.GlobalShaderParameterSet("water_bed", on ? new Vector4(peb, N("silt", 0.6f), N("wet", 0.35f), N("wet_dark", 0.45f)) : Vector4.Zero);
        string silt = on && b.TryGetProperty("silt_color", out var sc) && sc.ValueKind == JsonValueKind.String ? sc.GetString()! : "#4a4234";
        var sl = new Color(silt).SrgbToLinear();
        sl.A = N("relief", 0.08f);
        RenderingServer.GlobalShaderParameterSet("water_silt", sl);
    }
}
