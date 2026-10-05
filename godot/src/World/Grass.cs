using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A meadow around the fight: tufts on a jittered grid of cells, each turned
/// at random; shaders/grass.gdshader decides from the ground's paint which
/// grow and how tall. The grid is built once and never again: the shader
/// wraps every tuft to the copy of it nearest the survivor (`centre`), and
/// stands it on the ground from a texture of the zone's heights, so the
/// meadow reaches the edge of the picture and follows without a hitch.
/// </summary>
public static class Grass
{
    public static MultiMeshInstance3D Build(ZoneData z, Vector2 centre, float radius, float cell = 0.3f)
    {
        if (z.Place != null && z.GrassMask != null) return Arena(z, centre, radius, cell);
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

        // (Wider cells at the lower qualities: fewer tufts, a thinner meadow.)
        int n = (int)(radius * 2 / cell);
        var at = new System.Collections.Generic.List<Transform3D>(n * n);
        var rng = new RandomNumberGenerator { Seed = 7 };
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float x = centre.X - radius + (i + rng.Randf()) * cell, zz = centre.Y - radius + (j + rng.Randf()) * cell;
                var basis = new Basis(Vector3.Up, rng.Randf() * Mathf.Tau);
                at.Add(new Transform3D(basis, new Vector3(x, 0, zz)));
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
        mat.SetShaderParameter("span", radius * 2);
        mat.SetShaderParameter("centre", centre);
        // The ground's heights, a texel per sample, read bilinear.
        var g = z.Ground;
        var hb = new byte[g.Heights.Length * 4];
        System.Buffer.BlockCopy(g.Heights, 0, hb, 0, hb.Length);
        mat.SetShaderParameter("heights", ImageTexture.CreateFromImage(Image.CreateFromData(g.Res, g.Res, false, Image.Format.Rf, hb)));
        mat.SetShaderParameter("h_size", (float)g.Size);
        mat.SetShaderParameter("h_res", (float)g.Res);
        blade.SurfaceSetMaterial(0, mat);
        return new MultiMeshInstance3D
        {
            Multimesh = mm, Name = "Grass", CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            // It is wherever the survivor is: never culled as a whole.
            CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f)),
        };
    }

    /// <summary>A tussock: long blades arching out from one root, the outer
    /// ones lying over further, the longest drooping at the tip; a metre
    /// tall before the shader sizes it. Each blade four segments, tapered.
    /// UV.y is how far up the blade (0 root, 1 tip), UV.x the blade's own
    /// shade. From above it reads as a mound of blades lit on its back, dark
    /// in its heart, which is how grass looks from thirty metres up.</summary>
    static ArrayMesh Tussock(int blades, float halfWidth)
    {
        var verts = new System.Collections.Generic.List<Vector3>();
        var uv = new System.Collections.Generic.List<Vector2>();
        var idx = new System.Collections.Generic.List<int>();
        var rng = new RandomNumberGenerator { Seed = 29 };
        for (int b = 0; b < blades; b++)
        {
            float ang = b * Mathf.Tau / blades * 2.618f + rng.Randf() * 0.5f;
            var dir = new Vector3(Mathf.Cos(ang), 0, Mathf.Sin(ang));
            var across = new Vector3(-dir.Z, 0, dir.X);
            // The inner blades stand, the outer arch over and droop at the tip.
            float outer = rng.Randf();
            float lean = 0.08f + 0.4f * outer, h = 0.6f + 0.4f * (1 - outer * 0.5f) * (0.75f + 0.25f * rng.Randf());
            float droop = outer > 0.5f ? 0.3f * (outer - 0.5f) / 0.5f : 0;
            var foot = dir * 0.06f * Mathf.Sqrt(rng.Randf());
            float shade = rng.Randf();
            int o = verts.Count;
            // Three segments: root, the arch, the tip.
            float[] ws = { 1f, 0.7f, 0f };
            for (int k = 0; k < 3; k++)
            {
                float t = k / 2f;
                var mid = foot + dir * lean * h * Mathf.Pow(t, 1.3f) + Vector3.Up * (t * h - droop * h * t * t);
                if (k < 2)
                {
                    verts.Add(mid - across * ws[k] * halfWidth); verts.Add(mid + across * ws[k] * halfWidth);
                    uv.Add(new Vector2(shade, t)); uv.Add(new Vector2(shade, t));
                }
                else { verts.Add(mid); uv.Add(new Vector2(shade, 1)); }
            }
            idx.AddRange(new[] { o, o + 2, o + 1, o + 2, o + 3, o + 1, o + 2, o + 4, o + 3 });
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        var ups = new Vector3[verts.Count];
        for (int i = 0; i < ups.Length; i++) ups[i] = Vector3.Up;
        arrays[(int)Mesh.ArrayType.Normal] = ups;
        arrays[(int)Mesh.ArrayType.TexUV] = uv.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return mesh;
    }

    /// <summary>A cell's scatter of fallen leaves: n leaves, each a pointed oval eleven
    /// centimetres long before the shader sizes it, lying flat and curled a little along its
    /// spine, turned every way. COLOR.rg is each leaf's middle in the cell, COLOR.b its own
    /// hash (shaders/arena_leaves.gdshader); UV.y is 1 on the curl's crown.</summary>
    static ArrayMesh LeafScatter(int n, float cell)
    {
        var verts = new System.Collections.Generic.List<Vector3>();
        var cols = new System.Collections.Generic.List<Color>();
        var uv = new System.Collections.Generic.List<Vector2>();
        var idx = new System.Collections.Generic.List<int>();
        var rng = new RandomNumberGenerator { Seed = 53 };
        for (int k = 0; k < n; k++)
        {
            float mx = rng.Randf(), mz = rng.Randf(), own = (k + 0.5f) / n;
            var mid = new Vector3((mx - 0.5f) * cell, 0, (mz - 0.5f) * cell);
            float ang = rng.Randf() * Mathf.Tau, len = 0.11f * (0.8f + 0.4f * rng.Randf()), wid = len * (0.38f + 0.2f * rng.Randf());
            var along = new Vector3(Mathf.Cos(ang), 0, Mathf.Sin(ang));
            var across = new Vector3(-along.Z, 0, along.X);
            float curl = len * (0.08f + 0.12f * rng.Randf());
            var col = new Color(mx, mz, own);
            int o = verts.Count;
            // Tip, two shoulders each side, the stalk end; the spine raised (the curl).
            (float t, float w, float up)[] ring = { (-0.5f, 0, 0), (-0.25f, 0.42f, 0), (0.12f, 0.5f, 0), (0.5f, 0, 0), (0.12f, -0.5f, 0), (-0.25f, -0.42f, 0) };
            verts.Add(mid + Vector3.Up * curl); cols.Add(col); uv.Add(new Vector2(0, 1));
            foreach (var (t, w, _) in ring)
            {
                verts.Add(mid + along * t * len + across * w * wid);
                cols.Add(col); uv.Add(new Vector2(0, 0));
            }
            for (int s = 0; s < ring.Length; s++) idx.AddRange(new[] { o, o + 1 + s, o + 1 + (s + 1) % ring.Length });
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        var ups = new Vector3[verts.Count];
        for (int i = 0; i < ups.Length; i++) ups[i] = Vector3.Up;
        arrays[(int)Mesh.ArrayType.Normal] = ups;
        arrays[(int)Mesh.ArrayType.Color] = cols.ToArray();
        arrays[(int)Mesh.ArrayType.TexUV] = uv.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return mesh;
    }

    /// <summary>An ember arena's fallen leaves (ArenaGround.LeafLook), where its paint lays
    /// them (the grass mask's R), or null for a place with none.</summary>
    public static MultiMeshInstance3D? Leaves(ZoneData z, Vector2 centre, float radius, float cellQuality)
    {
        if (z.Place == null || z.GrassMask == null || ArenaGround.LeavesOf(z.Place.Id) is not { } look) return null;
        const float Cell = 0.6f;
        var mesh = LeafScatter(look.PerCell, Cell);
        float step = Cell * Mathf.Max(1, cellQuality / 0.3f);
        int n = (int)(radius * 2 / step);
        var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = mesh, InstanceCount = n * n };
        var rng = new RandomNumberGenerator { Seed = 19 };
        int i = 0;
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
            {
                float x = centre.X - radius + (k + rng.Randf()) * step, zz = centre.Y - radius + (j + rng.Randf()) * step;
                mm.SetInstanceTransform(i++, new Transform3D(new Basis(Vector3.Up, rng.Randf() * Mathf.Tau), new Vector3(x, 0, zz)));
            }
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/arena_leaves.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("splat", ImageTexture.CreateFromImage(z.GrassMask!));
        mat.SetShaderParameter("zone_size", z.Size);
        mat.SetShaderParameter("density", look.Density);
        mat.SetShaderParameter("size", look.Size);
        mat.SetShaderParameter("cell_span", Cell);
        mat.SetShaderParameter("span", radius * 2);
        mat.SetShaderParameter("centre", centre);
        var g = z.Ground;
        var hb = new byte[g.Heights.Length * 4];
        System.Buffer.BlockCopy(g.Heights, 0, hb, 0, hb.Length);
        mat.SetShaderParameter("heights", ImageTexture.CreateFromImage(Image.CreateFromData(g.Res, g.Res, false, Image.Format.Rf, hb)));
        mat.SetShaderParameter("h_size", (float)g.Size);
        mat.SetShaderParameter("h_res", (float)g.Res);
        mesh.SurfaceSetMaterial(0, mat);
        return new MultiMeshInstance3D
        {
            Multimesh = mm, Name = "Leaves", CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f)),
        };
    }

    /// <summary>An ember arena's grass: tussocks where its paint grows them
    /// (shaders/arena_grass.gdshader), coloured and sized by its place
    /// (ArenaGround.Grass). The grid is sparser than a meadow's (a tussock
    /// is a dozen blades), and as wide as the arena camera sees.</summary>
    static MultiMeshInstance3D Arena(ZoneData z, Vector2 centre, float radius, float cell)
    {
        var look = ArenaGround.GrassOf(z.Place!.Id);
        var mesh = Tussock(look.Blades, look.Width);
        // The picture's quality widens the meadow's cells; the tussocks' with it.
        float step = look.Cell * cell / 0.3f;
        int n = (int)(radius * 2 / step);
        var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = mesh, InstanceCount = n * n };
        var rng = new RandomNumberGenerator { Seed = 7 };
        int i = 0;
        for (int j = 0; j < n; j++)
            for (int k = 0; k < n; k++)
            {
                float x = centre.X - radius + (k + rng.Randf()) * step, zz = centre.Y - radius + (j + rng.Randf()) * step;
                mm.SetInstanceTransform(i++, new Transform3D(new Basis(Vector3.Up, rng.Randf() * Mathf.Tau), new Vector3(x, 0, zz)));
            }
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/arena_grass.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("splat", ImageTexture.CreateFromImage(z.GrassMask!));
        mat.SetShaderParameter("zone_size", z.Size);
        ArenaGround.Grass(mat, z);
        mat.SetShaderParameter("span", radius * 2);
        mat.SetShaderParameter("centre", centre);
        var g = z.Ground;
        var hb = new byte[g.Heights.Length * 4];
        System.Buffer.BlockCopy(g.Heights, 0, hb, 0, hb.Length);
        mat.SetShaderParameter("heights", ImageTexture.CreateFromImage(Image.CreateFromData(g.Res, g.Res, false, Image.Format.Rf, hb)));
        mat.SetShaderParameter("h_size", (float)g.Size);
        mat.SetShaderParameter("h_res", (float)g.Res);
        mesh.SurfaceSetMaterial(0, mat);
        return new MultiMeshInstance3D
        {
            Multimesh = mm, Name = "Grass", CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f)),
        };
    }
}
