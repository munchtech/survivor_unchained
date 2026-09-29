using System.Text.Json;
using Godot;

namespace SurvivorUnchained.World;

/// <summary>
/// The zone's water, as the web game lays it (src/render/water.ts): a ribbon
/// down the stream's carved bed, each vertex knowing where it is across and
/// along the stream and how deep the water is over the bed there
/// (data/ZONE/water.*, from tools/godot/export_zone.mjs). The look is
/// shaders/water.gdshader: the web game's poisoned stream, with what an
/// engine adds (the bed seen through it, bent by the ripples; how murky by
/// how deep it really is).
/// </summary>
public static class Water
{
    public static Node3D Build(ZoneData z)
    {
        var root = new Node3D { Name = "Water" };
        var dir = $"res://data/{z.Id}";
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
            root.AddChild(new MeshInstance3D { Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        }
        return root;
    }
}
