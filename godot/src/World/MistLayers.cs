using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Thin mist lying on a zone's river (look bible 1c, "mist in layers"): three sheets stacked a little over
/// the water along its course (the water mask), each at its own height and pace, lying in drifting banks with
/// clear water between (river_mist.gdshader), fading where they meet the banks and stones, so none has an edge
/// of its own. Unlit: the air's preset colours them (Tint, from Atmosphere.Set), the key lighting each bank's
/// near side, and sets how thick they lie: play's presets lay them, the cinematics' presets (Mist 0) leave the
/// river as their shots were judged.
/// </summary>
public static class MistLayers
{
    static readonly List<ShaderMaterial> mats = new();
    static readonly List<Node3D> roots = new();
    static readonly float[] Rise = { 0.25f, 0.7f, 1.4f }, Share = { 1f, 0.7f, 0.45f }, Drift = { 0.02f, 0.03f, 0.014f }, BankDrift = { 0.22f, 0.3f, 0.4f };
    // Each sheet's most (the three stacked: 1 - 0.78 x 0.85 x 0.9, about 40% veiled at the thickest, so the bed shows through).
    static readonly float[] Cap = { 0.22f, 0.15f, 0.1f };
    static Color tint = new(0.3f, 0.36f, 0.45f), keyLight;
    static float thick;
    // (MIST_OFF=1: the sheets hidden, to see the water under them)
    static bool shown = System.Environment.GetEnvironmentVariable("MIST_OFF") != "1";

    /// <summary>False: the sheets hidden whatever the air (the perf flip "mist").</summary>
    public static bool Shown { get => shown; set { if (shown == value) return; shown = value; Apply(); } }

    /// <summary>The sheets for a zone with a river (a water mask and its "WATER_Y"), or null.</summary>
    public static Node3D? Build(ZoneData z)
    {
        var m = z.Meta;
        if (m.WaterMask == null || !m.Places.TryGetValue("WATER_Y", out var wy)) return null;
        float y0 = (float)wy.GetDouble();
        // The river's course: for each metre-wide step across the zone (x), the middle and half-width of its water.
        double size = m.Size, step = 4;
        var course = new List<(float X, float Z, float Hw)>();
        for (double x = -size / 2 + step / 2; x < size / 2; x += step)
        {
            double lo = double.MaxValue, hi = double.MinValue;
            for (double zz = -size / 2; zz < size / 2; zz += 1)
                if (m.WaterAt(x, zz)) { lo = System.Math.Min(lo, zz); hi = System.Math.Max(hi, zz); }
            if (lo <= hi) course.Add(((float)x, (float)((lo + hi) / 2), (float)((hi - lo) / 2 + 5)));
        }
        if (course.Count < 2) return null;
        mats.RemoveAll(mt => !GodotObject.IsInstanceValid(mt));
        var root = new Node3D { Name = "MistLayers" };
        for (int k = 0; k < Rise.Length; k++)
        {
            var verts = new List<Vector3>(); var uv = new List<Vector2>(); var uv2 = new List<Vector2>(); var idx = new List<int>();
            float along = 0;
            for (int i = 0; i < course.Count; i++)
            {
                var c = course[i];
                if (i > 0) along += new Vector2(c.X - course[i - 1].X, c.Z - course[i - 1].Z).Length();
                // Across the course: (z) at its edges and middle, the middle a hand higher each layer.
                float[] off = { -c.Hw, 0, c.Hw }, mid = { 0, 1, 0 };
                for (int j = 0; j < 3; j++)
                {
                    verts.Add(new Vector3(c.X, y0 + Rise[k], c.Z + off[j]));
                    uv.Add(new Vector2(off[j], along));
                    uv2.Add(new Vector2(mid[j], 0));
                }
                if (i == 0) continue;
                int a = (i - 1) * 3, b = i * 3;
                for (int j = 0; j < 2; j++) idx.AddRange(new[] { a + j, b + j, a + j + 1, a + j + 1, b + j, b + j + 1 });
            }
            var arrays = new Godot.Collections.Array();
            arrays.Resize((int)Mesh.ArrayType.Max);
            arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
            arrays[(int)Mesh.ArrayType.TexUV] = uv.ToArray();
            arrays[(int)Mesh.ArrayType.TexUV2] = uv2.ToArray();
            arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
            var mesh = new ArrayMesh();
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/river_mist.gdshader") };
            mat.SetShaderParameter("noise_tex", NoiseTex.Get());
            mat.SetShaderParameter("drift", Drift[k]);
            mat.SetShaderParameter("bank_drift", BankDrift[k]);
            mat.SetShaderParameter("layer", (float)k);
            mat.SetShaderParameter("cap", Cap[k]);
            mat.SetMeta("share", Share[k]);
            mats.Add(mat);
            root.AddChild(new MeshInstance3D { Name = $"Mist{k}", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        }
        roots.Add(root);
        Apply();
        return root;
    }

    /// <summary>The air's colour for the mist, how thick it lies (0: none), and the key's light (linear, its energy in).</summary>
    public static void Tint(Color mist, float thickness, Color key)
    {
        if (tint == mist && Mathf.IsEqualApprox(thick, thickness) && keyLight == key) return;
        tint = mist; thick = thickness; keyLight = key;
        Apply();
    }

    static void Apply()
    {
        mats.RemoveAll(mt => !GodotObject.IsInstanceValid(mt));
        roots.RemoveAll(r => !GodotObject.IsInstanceValid(r));
        foreach (var r in roots) r.Visible = shown && thick > 0.001f;
        foreach (var mt in mats)
        {
            mt.SetShaderParameter("mist", tint);
            mt.SetShaderParameter("key_light", new Vector3(keyLight.R, keyLight.G, keyLight.B));
            mt.SetShaderParameter("opacity", thick * (float)mt.GetMeta("share"));
        }
    }
}
