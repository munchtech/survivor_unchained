using System.Text.Json;
using Godot;

namespace SurvivorUnchained.World;

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
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);

        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/terrain.gdshader") };
        var splat = ImageTexture.CreateFromImage(WithMips(z.Splat));
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("splat", splat);
        mat.SetShaderParameter("g_alb", GD.Load<TextureLayered>("res://art/ground/albedo.jpg"));
        mat.SetShaderParameter("g_nor", GD.Load<TextureLayered>("res://art/ground/normal.jpg"));
        mat.SetShaderParameter("g_arh", GD.Load<TextureLayered>("res://art/ground/arh.jpg"));
        mat.SetShaderParameter("zone_size", z.Size);
        mat.SetShaderParameter("leaves", z.Leaves);
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString("res://art/ground/ground.json"));
        var scales = new Godot.Collections.Array<float>();
        foreach (var l in meta.RootElement.GetProperty("layers").EnumerateArray()) scales.Add(1f / l.GetProperty("metres").GetSingle());
        mat.SetShaderParameter("g_scale", scales);
        mesh.SurfaceSetMaterial(0, mat);
        var ground = new MeshInstance3D { Mesh = mesh, Name = "Ground", CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        // What falls lands on it: the same heights as a physics heightmap
        // (one sample a metre here, as the zone's grid is).
        var body = new StaticBody3D { Name = "GroundBody", CollisionLayer = 1 };
        var shape = new HeightMapShape3D { MapWidth = n, MapDepth = n, MapData = z.Heights };
        body.AddChild(new CollisionShape3D { Shape = shape, Scale = new Vector3(z.Step, 1, z.Step) });
        ground.AddChild(body);
        return ground;
    }

    static Image WithMips(Image img)
    {
        var copy = (Image)img.Duplicate();
        copy.Convert(Image.Format.Rgba8);
        copy.GenerateMipmaps();
        return copy;
    }
}
