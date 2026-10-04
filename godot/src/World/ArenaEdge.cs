using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Maps;

namespace SurvivorUnchained.View;

/// <summary>
/// What an ember arena has round and over its ground, past what any zone has:
/// the scar's lip (sparks rising off the charred ring all the way round, and a
/// low curtain of smoke lit from below just outside it, so the place beyond
/// goes into the dark), the mist lying in its low ground (a fog volume, in
/// patches), and its streams' water.
/// </summary>
public static class ArenaEdge
{
    public static Node3D Build(ZoneData z)
    {
        var root = new Node3D { Name = "ArenaEdge" };
        var place = z.Place!;
        var ember = new Color(place.Air.Ember);
        root.AddChild(Sparks(z, ember));
        root.AddChild(Curtain(z, ember));
        if (place.Air.MistDensity > 0) root.AddChild(Mist(z));
        foreach (var s in z.Streams)
        {
            root.AddChild(Stream(z, s));
            // Mist lying along it, in two sheets, the lower thicker.
            foreach (var (lift, op) in new[] { (0.45f, 0.16f), (1.3f, 0.08f) })
                root.AddChild(MistSheet(z, s, 3.5f, lift, op, new Color(place.Air.MistColor)));
        }
        foreach (var r in z.Rails) root.AddChild(Rails(z, r));
        foreach (var v in z.Vents) root.AddChild(Vent(z, v, ember, new Color(place.Air.HazeColor)));
        return root;
    }

    /// <summary>Smoke breathing up out of the ground (the Dig's pit): slow,
    /// thick, red underneath where the glow below lights it, going dark and
    /// thin as it rises; it gives the pit its height from thirty metres up.</summary>
    static GpuParticles3D Vent(ZoneData z, (double X, double Z, double R) v, Color ember, Color smoke)
    {
        float x = (float)v.X, zz = (float)v.Z, r = (float)v.R;
        var ramp = new Gradient();
        ramp.SetColor(0, new Color(ember.R, ember.G * 0.7f, ember.B * 0.5f, 0));
        ramp.SetColor(1, new Color(smoke.R * 0.8f, smoke.G * 0.8f, smoke.B * 0.8f, 0));
        ramp.AddPoint(0.12f, new Color(ember.R * 0.85f, ember.G * 0.55f, ember.B * 0.4f, 0.5f));
        ramp.AddPoint(0.4f, new Color(smoke.R * 1.6f + ember.R * 0.12f, smoke.G * 1.6f + ember.G * 0.06f, smoke.B * 1.6f, 0.42f));
        var grow = new Curve();
        grow.AddPoint(new Vector2(0, 0.45f));
        grow.AddPoint(new Vector2(1, 1.6f));
        var proc = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = r,
            Direction = Vector3.Up, Spread = 14,
            InitialVelocityMin = 0.7f, InitialVelocityMax = 1.5f,
            Gravity = new Vector3(0.12f, 0.18f, 0.05f),
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 0.6f, TurbulenceNoiseScale = 6f, TurbulenceInfluenceMin = 0.02f, TurbulenceInfluenceMax = 0.08f,
            ScaleMin = 2.6f, ScaleMax = 4.4f, ScaleCurve = new CurveTexture { Curve = grow },
            AngleMin = 0, AngleMax = 360, AngularVelocityMin = -8, AngularVelocityMax = 8,
            ColorRamp = new GradientTexture1D { Gradient = ramp },
        };
        var mat = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, BillboardMode = BaseMaterial3D.BillboardModeEnum.Particles,
            BillboardKeepScale = true, ParticlesAnimHFrames = 1, ParticlesAnimVFrames = 1,
            VertexColorUseAsAlbedo = true, AlbedoTexture = Puff(), Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
            ProximityFadeEnabled = true, ProximityFadeDistance = 2f,
        };
        return new GpuParticles3D
        {
            Name = "Vent", Amount = 48, Lifetime = 10, Preprocess = 10, ProcessMaterial = proc,
            DrawPass1 = new QuadMesh { Size = Vector2.One, Material = mat },
            Position = new Vector3(x, z.HeightAt(x, zz) - 3f, zz),
            VisibilityAabb = new Aabb(new Vector3(-20, -6, -20), new Vector3(40, 40, 40)),
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, FixedFps = 30,
        };
    }

    static Texture2D? puff;

    /// <summary>A soft, torn puff of smoke.</summary>
    static Texture2D Puff()
    {
        if (puff != null) return puff;
        const int n = 64;
        var noise = new FastNoiseLite { NoiseType = FastNoiseLite.NoiseTypeEnum.Perlin, Frequency = 0.06f, FractalOctaves = 4, Seed = 3 };
        var img = Image.CreateEmpty(n, n, false, Image.Format.Rgba8);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float d = new Vector2(i + 0.5f - n / 2f, j + 0.5f - n / 2f).Length() / (n / 2f);
                float body = Mathf.Clamp(1 - d, 0, 1);
                float a = Mathf.Clamp(body * body * (0.55f + 0.9f * noise.GetNoise2D(i, j)), 0, 1);
                img.SetPixel(i, j, new Color(1, 1, 1, a));
            }
        return puff = ImageTexture.CreateFromImage(img);
    }

    /// <summary>A line of rails: sleepers of black timber, some gone, and two
    /// iron rails rusted down their sides with their tops worn bright by the
    /// carts. From thirty metres up, the bright tops are the one straight
    /// line in the working; they catch the moon and the lamps.</summary>
    static Node3D Rails(ZoneData z, (double X, double Z, double Hw)[] path)
    {
        var root = new Node3D { Name = "Rails" };
        const float Gauge = 0.55f, Bed = 0.1f, RailH = 0.09f, RailW = 0.07f;
        // Walk the path a step at a time: points, their directions and across.
        var pts = new List<(Vector3 P, Vector3 Across)>();
        for (int i = 0; i < path.Length; i++)
        {
            var a = path[System.Math.Max(i - 1, 0)];
            var b = path[System.Math.Min(i + 1, path.Length - 1)];
            var dir = new Vector2((float)(b.X - a.X), (float)(b.Z - a.Z)).Normalized();
            var p = new Vector2((float)path[i].X, (float)path[i].Z);
            pts.Add((new Vector3(p.X, z.HeightAt(p.X, p.Y), p.Y), new Vector3(-dir.Y, 0, dir.X)));
        }
        // Sleepers every 0.75 m, each laid on the ground where it lies.
        var rng = new RandomNumberGenerator { Seed = 41 };
        var ties = new List<Transform3D>();
        float along = 0, next = 0;
        for (int i = 1; i < pts.Count; i++)
        {
            float seg = pts[i].P.DistanceTo(pts[i - 1].P);
            while (next <= along + seg)
            {
                float t = (next - along) / seg;
                var p = pts[i - 1].P.Lerp(pts[i].P, t);
                var across = pts[i - 1].Across.Lerp(pts[i].Across, t).Normalized();
                next += 0.75f;
                if (rng.Randf() < 0.07f) continue;
                p.Y = z.HeightAt(p.X, p.Z) + Bed * 0.35f;
                var basis = new Basis(Vector3.Up, Mathf.Atan2(across.X, across.Z) + rng.RandfRange(-0.06f, 0.06f));
                ties.Add(new Transform3D(basis, p));
            }
            along += seg;
        }
        var tieMesh = new BoxMesh { Size = new Vector3(0.24f, Bed, 1.75f) };
        tieMesh.Material = new StandardMaterial3D { AlbedoColor = new Color("#2b241d"), Roughness = 0.92f };
        var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = tieMesh, InstanceCount = ties.Count };
        for (int i = 0; i < ties.Count; i++) mm.SetInstanceTransform(i, ties[i]);
        root.AddChild(new MultiMeshInstance3D { Name = "Sleepers", Multimesh = mm, CastShadow = GeometryInstance3D.ShadowCastingSetting.On });

        // The rails: a top and two sides each, following the ground.
        var tops = new SurfaceTool();
        var sides = new SurfaceTool();
        tops.Begin(Mesh.PrimitiveType.Triangles);
        sides.Begin(Mesh.PrimitiveType.Triangles);
        foreach (int s in new[] { -1, 1 })
        {
            for (int i = 1; i < pts.Count; i++)
            {
                var (p0, a0) = pts[i - 1];
                var (p1, a1) = pts[i];
                var c0 = p0 + a0 * s * Gauge + Vector3.Up * Bed;
                var c1 = p1 + a1 * s * Gauge + Vector3.Up * Bed;
                var h = Vector3.Up * RailH;
                // Top, then the two sides, as quads.
                Quad(tops, c0 - a0 * RailW / 2 + h, c0 + a0 * RailW / 2 + h, c1 + a1 * RailW / 2 + h, c1 - a1 * RailW / 2 + h, Vector3.Up);
                Quad(sides, c0 + a0 * RailW / 2, c1 + a1 * RailW / 2, c1 + a1 * RailW / 2 + h, c0 + a0 * RailW / 2 + h, a0);
                Quad(sides, c1 - a1 * RailW / 2, c0 - a0 * RailW / 2, c0 - a0 * RailW / 2 + h, c1 - a1 * RailW / 2 + h, -a0);
            }
        }
        var mesh = tops.Commit();
        sides.Commit(mesh);
        mesh.SurfaceSetMaterial(0, new StandardMaterial3D { AlbedoColor = new Color("#8d8a86"), Metallic = 1, Roughness = 0.32f });
        mesh.SurfaceSetMaterial(1, new StandardMaterial3D { AlbedoColor = new Color("#4a2c1c"), Metallic = 0.35f, Roughness = 0.75f });
        root.AddChild(new MeshInstance3D { Name = "Iron", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.On });
        return root;
    }

    /// <summary>A quad a..d, counter-clockwise seen from the side it faces,
    /// wound back the other way (Godot draws clockwise faces), with one normal.</summary>
    static void Quad(SurfaceTool st, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 n)
    {
        foreach (var v in new[] { a, c, b, a, d, c })
        {
            st.SetNormal(n);
            st.AddVertex(v);
        }
    }

    /// <summary>The rim, every two degrees, `off` metres out from the edge, on the ground.</summary>
    static List<Vector3> Ring(ZoneData z, float off, float lift)
    {
        var pts = new List<Vector3>();
        foreach (var (x, zz) in z.Rim)
        {
            var d = new Vector2((float)x, (float)zz);
            var p = d + d.Normalized() * off;
            pts.Add(new Vector3(p.X, z.HeightAt(p.X, p.Y) + lift, p.Y));
        }
        return pts;
    }

    /// <summary>Sparks off the ring: small, hot, rising and going out.</summary>
    static GpuParticles3D Sparks(ZoneData z, Color ember)
    {
        // Emission points: along the lip's burning line, just past where she can
        // stand (arena_ground.gdshader's lip_at), and a few off the coals beyond it.
        var pts = new List<Vector3>();
        foreach (float off in new[] { 1.3f, 1.8f, 2.3f, 3.5f }) pts.AddRange(Ring(z, off, 0.1f));
        var img = Image.CreateEmpty(pts.Count, 1, false, Image.Format.Rgbf);
        for (int i = 0; i < pts.Count; i++) img.SetPixel(i, 0, new Color(pts[i].X, pts[i].Y, pts[i].Z));
        var ramp = new Gradient();
        ramp.SetColor(0, new Color(1f, 0.75f, 0.4f, 1));
        ramp.SetColor(1, new Color(ember.R * 0.6f, ember.G * 0.3f, ember.B * 0.2f, 0));
        ramp.AddPoint(0.35f, new Color(ember.R, ember.G * 0.8f, ember.B * 0.6f, 0.9f));
        var proc = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Points,
            EmissionPointTexture = ImageTexture.CreateFromImage(img),
            EmissionPointCount = pts.Count,
            Direction = Vector3.Up, Spread = 25,
            InitialVelocityMin = 0.6f, InitialVelocityMax = 2.2f,
            Gravity = new Vector3(0, 0.35f, 0),
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 1.2f, TurbulenceNoiseScale = 3.5f, TurbulenceInfluenceMin = 0.05f, TurbulenceInfluenceMax = 0.25f,
            ScaleMin = 0.5f, ScaleMax = 1.3f,
            ColorRamp = new GradientTexture1D { Gradient = ramp },
        };
        var mat = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, BlendMode = BaseMaterial3D.BlendModeEnum.Add,
            BillboardMode = BaseMaterial3D.BillboardModeEnum.Particles, VertexColorUseAsAlbedo = true,
            AlbedoTexture = Dot(), Transparency = BaseMaterial3D.TransparencyEnum.Alpha, NoDepthTest = false,
            AlbedoColor = new Color(2.2f, 2.2f, 2.2f),
        };
        return new GpuParticles3D
        {
            Name = "RingSparks", Amount = 700, Lifetime = 2.6, Preprocess = 3, ProcessMaterial = proc,
            DrawPass1 = new QuadMesh { Size = new Vector2(0.09f, 0.09f), Material = mat },
            VisibilityAabb = new Aabb(new Vector3(-150, -20, -150), new Vector3(300, 60, 300)),
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, FixedFps = 30,
        };
    }

    static Texture2D? dot;

    /// <summary>A soft round spark.</summary>
    static Texture2D Dot()
    {
        if (dot != null) return dot;
        const int n = 32;
        var img = Image.CreateEmpty(n, n, false, Image.Format.Rgba8);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float d = new Vector2(i + 0.5f - n / 2f, j + 0.5f - n / 2f).Length() / (n / 2f);
                float a = Mathf.Clamp(1 - d, 0, 1);
                img.SetPixel(i, j, new Color(1, 1, 1, a * a));
            }
        return dot = ImageTexture.CreateFromImage(img);
    }

    /// <summary>A low wall of smoke just past the ring, lit from below by it:
    /// the place beyond goes on, into the dark.</summary>
    static MeshInstance3D Curtain(ZoneData z, Color ember)
    {
        const float H = 7f;
        var low = Ring(z, 3.5f, -0.5f);
        var verts = new List<Vector3>();
        var uvs = new List<Vector2>();
        var idx = new List<int>();
        float along = 0;
        for (int i = 0; i <= low.Count; i++)
        {
            var p = low[i % low.Count];
            if (i > 0) along += p.DistanceTo(low[(i - 1) % low.Count]);
            verts.Add(p); uvs.Add(new Vector2(along, 0));
            verts.Add(p + new Vector3(0, H, 0)); uvs.Add(new Vector2(along, 1));
            if (i > 0)
            {
                int a = (i - 1) * 2, b = i * 2;
                idx.AddRange(new[] { a, b, a + 1, a + 1, b, b + 1 });
            }
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        arrays[(int)Mesh.ArrayType.TexUV] = uvs.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ember_curtain.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("ember", ember);
        mat.SetShaderParameter("smoke", new Color(z.Place!.Air.HazeColor));
        return new MeshInstance3D { Name = "RingSmoke", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
    }

    /// <summary>Mist lying in the low ground, in patches, thickest at the foot.</summary>
    static FogVolume Mist(ZoneData z)
    {
        var air = z.Place!.Air;
        var noise = new FastNoiseLite { NoiseType = FastNoiseLite.NoiseTypeEnum.Perlin, Frequency = 0.045f, FractalOctaves = 3 };
        var tex = new NoiseTexture3D { Width = 64, Height = 8, Depth = 64, Seamless = true, Noise = noise, Normalize = true };
        var mat = new FogMaterial
        {
            Density = (float)air.MistDensity, Albedo = new Color(air.MistColor), HeightFalloff = (float)air.MistFalloff,
            EdgeFade = 0.4f, DensityTexture = tex,
        };
        float y = z.HeightAt(0, 0);
        return new FogVolume
        {
            Name = "Mist", Shape = RenderingServer.FogVolumeShape.Box, Size = new Vector3(200, (float)air.MistHeight * 2 + 1.5f, 200),
            Position = new Vector3(0, y - 0.6f + (float)air.MistHeight * 0.5f, 0), Material = mat,
        };
    }

    /// <summary>A sheet of mist along a stream, `extra` metres wider than it
    /// each side, `lift` over the water (or the ground, where that is higher).</summary>
    static MeshInstance3D MistSheet(ZoneData z, (double X, double Z, double Hw)[] s, float extra, float lift, float opacity, Color colour)
    {
        var verts = new List<Vector3>();
        var uv = new List<Vector2>();
        var uv2 = new List<Vector2>();
        var idx = new List<int>();
        float along = 0;
        for (int i = 0; i < s.Length; i++)
        {
            var p = new Vector2((float)s[i].X, (float)s[i].Z);
            var q = new Vector2((float)s[System.Math.Min(i + 1, s.Length - 1)].X, (float)s[System.Math.Min(i + 1, s.Length - 1)].Z);
            var r = new Vector2((float)s[System.Math.Max(i - 1, 0)].X, (float)s[System.Math.Max(i - 1, 0)].Z);
            var dir = (q - r).Normalized();
            var across = new Vector2(-dir.Y, dir.X);
            if (i > 0) along += p.DistanceTo(r);
            float hw = (float)s[i].Hw + extra;
            float water = z.HeightAt(p.X, p.Y) + 0.5f;
            foreach (int side in new[] { -1, 0, 1 })
            {
                var e = p + across * side * hw;
                verts.Add(new Vector3(e.X, Mathf.Max(water, z.HeightAt(e.X, e.Y)) + lift, e.Y));
                uv.Add(new Vector2(side * hw, along));
                uv2.Add(new Vector2(side == 0 ? 1 : 0, 0));
            }
            if (i > 0)
            {
                int a = (i - 1) * 3, b = i * 3;
                idx.AddRange(new[] { a, a + 1, b, a + 1, b + 1, b, a + 1, a + 2, b + 1, a + 2, b + 2, b + 1 });
            }
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        arrays[(int)Mesh.ArrayType.TexUV] = uv.ToArray();
        arrays[(int)Mesh.ArrayType.TexUV2] = uv2.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/mist_sheet.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("mist", colour);
        mat.SetShaderParameter("opacity", opacity);
        return new MeshInstance3D { Name = "Mist", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
    }

    /// <summary>A stream's water: a ribbon down its course over its carved bed.</summary>
    static MeshInstance3D Stream(ZoneData z, (double X, double Z, double Hw)[] s)
    {
        var verts = new List<Vector3>();
        var uv = new List<Vector2>();
        var uv2 = new List<Vector2>();
        var nrm = new List<Vector3>();
        var idx = new List<int>();
        float along = 0;
        for (int i = 0; i < s.Length; i++)
        {
            var p = new Vector2((float)s[i].X, (float)s[i].Z);
            var q = new Vector2((float)s[System.Math.Min(i + 1, s.Length - 1)].X, (float)s[System.Math.Min(i + 1, s.Length - 1)].Z);
            var r = new Vector2((float)s[System.Math.Max(i - 1, 0)].X, (float)s[System.Math.Max(i - 1, 0)].Z);
            var dir = (q - r).Normalized();
            var across = new Vector2(-dir.Y, dir.X);
            if (i > 0) along += p.DistanceTo(r);
            float hw = (float)s[i].Hw + 0.7f;
            // The water's top: the bed's middle and a hand over it.
            float y = z.HeightAt(p.X, p.Y) + 0.5f;
            // Bank, middle, bank: UV2.x is how far from the bank (0 at it), so
            // the shallows and the scum keep to the edges and the slurry's
            // light to the deep middle.
            foreach (int side in new[] { -1, 0, 1 })
            {
                var e = p + across * side * hw;
                verts.Add(new Vector3(e.X, y, e.Y));
                uv.Add(new Vector2(side * hw, along));
                uv2.Add(new Vector2(side == 0 ? 1 : 0, 0));
                nrm.Add(Vector3.Up);
            }
            if (i > 0)
            {
                int a = (i - 1) * 3, b = i * 3;
                idx.AddRange(new[] { a, a + 1, b, a + 1, b + 1, b, a + 1, a + 2, b + 1, a + 2, b + 2, b + 1 });
            }
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        arrays[(int)Mesh.ArrayType.Normal] = nrm.ToArray();
        arrays[(int)Mesh.ArrayType.TexUV] = uv.ToArray();
        arrays[(int)Mesh.ArrayType.TexUV2] = uv2.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        // The Dig's slurry in it (shaders/slurry_stream.gdshader).
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/slurry_stream.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        return new MeshInstance3D { Name = "Stream", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
    }
}
