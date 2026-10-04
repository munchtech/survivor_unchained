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
        foreach (var s in z.Streams) root.AddChild(Stream(z, s));
        return root;
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
        // Emission points: the ring, a little either side of the edge.
        var pts = new List<Vector3>();
        foreach (float off in new[] { -2.5f, -1f, 0.5f, 2f }) pts.AddRange(Ring(z, off, 0.15f));
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
            foreach (int side in new[] { -1, 1 })
            {
                var e = p + across * side * hw;
                verts.Add(new Vector3(e.X, y, e.Y));
                uv.Add(new Vector2(side * hw, along));
                uv2.Add(new Vector2(0.6f, 0));
                nrm.Add(Vector3.Up);
            }
            if (i > 0)
            {
                int a = (i - 1) * 2, b = i * 2;
                idx.AddRange(new[] { a, a + 1, b, a + 1, b + 1, b });
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
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/water.gdshader") };
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("stream", true);
        // The Dig's slurry in it: a dull sheen, the shallows ochre, no glow to speak of.
        mat.SetShaderParameter("color", new Color("#1e2218"));
        mat.SetShaderParameter("murk", new Color("#090b07"));
        mat.SetShaderParameter("shallow", new Color("#3a3524"));
        mat.SetShaderParameter("foam_color", new Color("#8a8668"));
        mat.SetShaderParameter("sky", new Color("#1a2430"));
        mat.SetShaderParameter("glow", 0.06f);
        mat.SetShaderParameter("flow", new Vector2(0.02f, 0.3f));
        return new MeshInstance3D { Name = "Stream", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
    }
}
