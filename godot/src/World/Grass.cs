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
    public static MultiMeshInstance3D Build(ZoneData z, Vector2 centre, float radius, float cell = 0.3f)
    {
        // A tuft: seven thin tapered blades fanned out from one root, each
        // three segments, leaning outward by its own amount; x across a
        // blade, y up (0..1). Its colour for the shader rides in UV2: the
        // blade's own shade (x) and how far out it leans (y). Thin blades in
        // tufts read as grass from thirty metres up; wide single blades read
        // as paper.
        var blade = new ArrayMesh();
        var verts = new System.Collections.Generic.List<Vector3>();
        var uv2 = new System.Collections.Generic.List<Vector2>();
        var idx = new System.Collections.Generic.List<int>();
        var trng = new RandomNumberGenerator { Seed = 13 };
        for (int b = 0; b < 7; b++)
        {
            float ang = b * Mathf.Tau / 7 + trng.Randf() * 0.6f, lean = 0.1f + trng.Randf() * 0.35f, h = 0.7f + trng.Randf() * 0.5f;
            var dir = new Vector3(Mathf.Cos(ang), 0, Mathf.Sin(ang));
            var across = new Vector3(-dir.Z, 0, dir.X);
            float shade = trng.Randf();
            int o = verts.Count;
            float[] ws = { 0.5f, 0.38f, 0.22f, 0f };
            for (int k = 0; k < 4; k++)
            {
                float t = k / 3f;
                var mid = dir * lean * t * t + Vector3.Up * t * h;
                if (k < 3)
                {
                    verts.Add(mid - across * ws[k] * 0.04f); verts.Add(mid + across * ws[k] * 0.04f);
                    uv2.Add(new Vector2(shade, lean)); uv2.Add(new Vector2(shade, lean));
                }
                else { verts.Add(mid); uv2.Add(new Vector2(shade, lean)); }
            }
            idx.AddRange(new[] { o, o + 2, o + 1, o + 2, o + 3, o + 1, o + 2, o + 4, o + 3, o + 4, o + 5, o + 3, o + 4, o + 6, o + 5 });
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        var ups = new Vector3[verts.Count];
        for (int i = 0; i < ups.Length; i++) ups[i] = Vector3.Up;
        arrays[(int)Mesh.ArrayType.Normal] = ups;
        arrays[(int)Mesh.ArrayType.TexUV2] = uv2.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
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
