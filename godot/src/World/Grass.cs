using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A meadow around the fight: blades on a jittered grid of cells, as the web
/// game grows them, each turned at random; shaders/grass.gdshader decides
/// from the ground's paint which grow and how tall. A patch of the zone, not
/// all of it: the slice stays in one place.
/// </summary>
public static class Grass
{
    public static MultiMeshInstance3D Build(ZoneData z, Vector2 centre, float radius, float cell = 0.21f)
    {
        // A tapered, three-segment blade: x across, y up (0..1).
        var blade = new ArrayMesh();
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = new Vector3[]
        {
            new(-0.5f, 0, 0), new(0.5f, 0, 0), new(-0.4f, 0.34f, 0), new(0.4f, 0.34f, 0),
            new(-0.26f, 0.68f, 0), new(0.26f, 0.68f, 0), new(0, 1, 0),
        };
        var up = Vector3.Up;
        arrays[(int)Mesh.ArrayType.Normal] = new[] { up, up, up, up, up, up, up };
        arrays[(int)Mesh.ArrayType.Index] = new[] { 0, 2, 1, 2, 3, 1, 2, 4, 3, 4, 5, 3, 4, 6, 5 };
        blade.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);

        int n = (int)(radius * 2 / cell);
        var at = new System.Collections.Generic.List<Transform3D>(n * n);
        var rng = new RandomNumberGenerator { Seed = 7 };
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float x = centre.X - radius + (i + rng.Randf()) * cell, zz = centre.Y - radius + (j + rng.Randf()) * cell;
                if (new Vector2(x - centre.X, zz - centre.Y).Length() > radius) continue;
                var basis = new Basis(Vector3.Up, rng.Randf() * Mathf.Tau);
                at.Add(new Transform3D(basis, new Vector3(x, z.HeightAt(x, zz) - 0.02f, zz)));
            }
        var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = blade, InstanceCount = at.Count };
        for (int i = 0; i < at.Count; i++) mm.SetInstanceTransform(i, at[i]);

        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/grass.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("splat", ImageTexture.CreateFromImage(z.Splat));
        mat.SetShaderParameter("g_alb", GD.Load<TextureLayered>("res://art/ground/albedo.jpg"));
        using var meta = JsonDocument.Parse(FileAccess.GetFileAsString("res://art/ground/ground.json"));
        mat.SetShaderParameter("meadow_scale", 1f / meta.RootElement.GetProperty("layers")[0].GetProperty("metres").GetSingle());
        mat.SetShaderParameter("zone_size", z.Size);
        mat.SetShaderParameter("leaves", z.Leaves);
        blade.SurfaceSetMaterial(0, mat);
        return new MultiMeshInstance3D { Multimesh = mm, Name = "Grass", CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
    }
}
