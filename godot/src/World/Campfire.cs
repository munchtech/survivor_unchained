using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A campfire: a ring of made stones round our own logs and ash bed
/// (art/world/campfire), the flame kit's camp fire (FlameKit.cs: a
/// simulated flame on upright cards, shaders/flame_mv.gdshader),
/// embers and smoke of GPU particles, and its own light.
/// </summary>
public static class Campfire
{
    /// <summary>The render layer the coals are drawn on (layer 10), kept out
    /// of the fire's own lights.</summary>
    public const uint CoalLayer = 1 << 9;
    /// <summary>(C01 set) The ring's stones and the ash bed (layer 15), also kept out of the fire's own light: a light
    /// lifted a third of a metre over the coals (C01's burnt-down fire) stood a hand off their tops and blew them out
    /// white ("bulbs"; the bed a white glare). They take the coals' low glow instead (<see cref="RingGlow"/>), so
    /// only the stones' inner faces and the ash nearest the coals are lit, warm, and their tops stay dark.</summary>
    public const uint RingLayer = 1u << 14;
    /// <summary>--campfire-ring K: the coals' glow on the ring's inner faces and the ash bed (for pictures).</summary>
    static readonly float RingK = SurvivorUnchained.Args.Num("campfire-ring", 0.9f);

    // The embers' and smoke's looks, shared by every fire, so a close camera can keep them off the space in front of it.
    static StandardMaterial3D? emberLook, smokeLook;

    /// <summary>Embers and smoke nearer the camera than so far (metres) drawn not at all, fading in over the
    /// next 35 cm; 0 for all of them. The Look's close portrait: an ember drifting between the lens and her
    /// is a soft orange disc across her neck.</summary>
    public static void ClearNear(float metres)
    {
        foreach (var m in new[] { emberLook, smokeLook })
        {
            if (m == null) continue;
            m.DistanceFadeMode = metres > 0 ? BaseMaterial3D.DistanceFadeModeEnum.PixelAlpha : BaseMaterial3D.DistanceFadeModeEnum.Disabled;
            m.DistanceFadeMinDistance = metres;
            m.DistanceFadeMaxDistance = metres + 0.35f;
        }
    }

    /// <param name="ring">Lay its own stones and logs (not where the web
    /// game's are already laid).</param>
    /// <param name="parts">Which of flames, embers, smoke (for telling
    /// them apart).</param>
    public static Node3D Build(Vector3 at, float size = 1, bool ring = true, string parts = "coals,flames,embers,smoke")
    {
        var root = new Node3D { Name = "Campfire", Position = at };
        // CAMPFIRE_PARTS picks the layers, for pictures of each alone.
        parts = System.Environment.GetEnvironmentVariable("CAMPFIRE_PARTS") ?? parts;
        if (ring) Ring(root, size);
        if (parts.Contains("coals")) root.AddChild(Wood(size) ?? Coals(size));
        if (parts.Contains("flames")) root.AddChild(FilmedFlames(size) ?? Flames(size));
        if (parts.Contains("embers")) root.AddChild(Embers(size));
        if (parts.Contains("smoke")) root.AddChild(Smoke(size));
        if (SurvivorUnchained.Args.Has("fire-probe")) root.TreeEntered += () => root.GetTree().CreateTimer(13).Timeout += () => Probe(root);
        return root;
    }

    /// <summary>--fire-probe: what stands within 2.5 m of the fire (layers, shading) and the lights reaching it, printed once.</summary>
    static void Probe(Node3D fire)
    {
        var at = fire.GlobalPosition;
        foreach (var n in fire.GetTree().Root.FindChildren("*", "GeometryInstance3D", true, false))
        {
            if (n is not GeometryInstance3D g || !g.IsVisibleInTree()) continue;
            var c = g.GlobalTransform * g.GetAabb().GetCenter();
            var cam = fire.GetViewport().GetCamera3D();
            var sp = cam != null && !cam.IsPositionBehind(c) ? cam.UnprojectPosition(c) : new Vector2(-1, -1);
            if (new Vector2(c.X - at.X, c.Z - at.Z).Length() > 2.5f && !(sp.X >= 0 && sp.X < 300 && sp.Y > 650 && sp.Y < 1000 && c.DistanceTo(cam!.GlobalPosition) < 12)) continue;
            string mat = g is MeshInstance3D mi && mi.Mesh != null && mi.Mesh.GetSurfaceCount() > 0
                ? ((mi.MaterialOverride ?? mi.GetActiveMaterial(0)) is BaseMaterial3D bm ? $"std {bm.ShadingMode}" : (mi.MaterialOverride ?? mi.GetActiveMaterial(0))?.GetType().Name ?? "none") : g.GetType().Name;
            GD.Print($"FIREPROBE geo {g.GetPath()} layers {g.Layers} at {c - at} screen {sp} {mat} shadow {g.CastShadow}");
        }
        foreach (var n in fire.GetTree().Root.FindChildren("*", "Light3D", true, false))
            if (n is Light3D l && l.IsVisibleInTree() && (l is DirectionalLight3D || l.GlobalPosition.DistanceTo(at) < 15))
                GD.Print($"FIREPROBE light {l.GetPath()} mask {l.LightCullMask} e {l.LightEnergy:0.00} col {l.LightColor} at {l.GlobalPosition - at} shadow {l.ShadowEnabled}");
    }

    static void Ring(Node3D root, float size)
    {
        if (ResourceLoader.Exists("res://art/materials/rock_boulder_dry/albedo.jpg"))
        {
            root.AddChild(Stones(size));
            return;
        }
        if (ResourceLoader.Exists("res://art/world/stone_fire_pit.glb"))
        {
            // The scan is a metre and a half across; a fire of size 1 is about
            // that. Sunk a little, so no stone floats on uneven ground.
            var pit = GD.Load<PackedScene>("res://art/world/stone_fire_pit.glb").Instantiate<Node3D>();
            pit.Scale = Vector3.One * size * 1.05f;
            pit.Position = new Vector3(0, -0.02f * size, 0);
            root.AddChild(pit);
            return;
        }
        // The ring: kit pebbles, turned and sized a little differently each.
        var rng = new RandomNumberGenerator { Seed = 11 };
        for (int i = 0; i < 9; i++)
        {
            float a = i / 9f * Mathf.Tau + rng.Randf() * 0.2f;
            var stone = GD.Load<PackedScene>($"res://assets/env/nature/Pebble_Round_{1 + i % 5}.gltf").Instantiate<Node3D>();
            stone.Position = new Vector3(Mathf.Cos(a) * 0.62f, -0.05f, Mathf.Sin(a) * 0.62f) * size;
            stone.Rotation = new Vector3(0, rng.Randf() * Mathf.Tau, 0);
            stone.Scale = Vector3.One * (1.6f + rng.Randf() * 0.5f) * size;
            root.AddChild(stone);
        }
        // Logs laid in a star, charred toward the middle.
        var bark = new StandardMaterial3D
        {
            AlbedoTexture = GD.Load<Texture2D>("res://assets/env/nature/Bark_DeadTree.ktx2"),
            NormalEnabled = true, NormalTexture = GD.Load<Texture2D>("res://assets/env/nature/Bark_DeadTree_Normal.ktx2"),
            Uv1Scale = new Vector3(1, 2, 1), Roughness = 0.9f, AlbedoColor = new Color(0.55f, 0.5f, 0.46f),
        };
        for (int i = 0; i < 4; i++)
        {
            float a = i / 4f * Mathf.Tau + 0.4f;
            var log = new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.07f * size, BottomRadius = 0.08f * size, Height = 0.8f * size, RadialSegments = 10 }, MaterialOverride = bark };
            log.Position = new Vector3(Mathf.Cos(a) * 0.22f, 0.09f, Mathf.Sin(a) * 0.22f) * size;
            log.Basis = new Basis(new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a)), Mathf.DegToRad(72)) ;
            root.AddChild(log);
        }
    }

    /// <summary>The ring: eleven field stones, rounded and uneven, laid end to
    /// end round the fire and bedded a third into the ground, sooted black on
    /// the faces toward the fire. Made, not scanned, so they hold their shape
    /// in a close-up (the scanned pit's few thousand faces read as cut facets
    /// at half a metre, in C01).</summary>
    static MeshInstance3D Stones(float size)
    {
        var b = new Shapes.Build();
        var rng = new RandomNumberGenerator { Seed = 41 };
        const int n = 11;
        for (int k = 0; k < n; k++)
        {
            float a = k * Mathf.Tau / n + (rng.Randf() - 0.5f) * 0.22f;
            float len = 0.26f + 0.1f * rng.Randf(), wid = 0.18f + 0.07f * rng.Randf(), hi = 0.17f + 0.08f * rng.Randf();
            var at = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * (0.6f + 0.06f * rng.Randf());
            at.Y = hi * 0.06f;
            // Long side along the ring, each turned and tipped a little its own way.
            var basis = new Basis(Vector3.Up, -a + Mathf.Pi / 2 + (rng.Randf() - 0.5f) * 0.5f) * new Basis(Vector3.Right, (rng.Randf() - 0.5f) * 0.3f);
            Stone(b, new Transform3D(basis.Scaled(new Vector3(len, hi, wid)), at), rng.Randf() * 100);
        }
        // Soot: the faces toward the fire and low down blackened, fading outward.
        var col = new Color[b.P.Count];
        for (int i = 0; i < col.Length; i++)
        {
            var p = b.P[i];
            float inward = Mathf.Clamp(-(b.N[i].X * p.X + b.N[i].Z * p.Z) / Mathf.Max(0.01f, new Vector2(p.X, p.Z).Length()), 0, 1);
            float near = 1 - Mathf.SmoothStep(0.45f, 0.75f, new Vector2(p.X, p.Z).Length());
            float soot = Mathf.Clamp(inward * 0.85f + near * 0.5f, 0, 1) * 0.82f;
            // (C01 set) the whole stone weathered dark (a fire ring's stones are smoked through): the moon finds
            // only a dull grey on their tops; the inner faces, sooted, take the coals' glow
            float dark = 0.5f * (1 - soot);
            col[i] = new Color(dark + 0.04f, dark + 0.035f, dark + 0.03f);
        }
        for (int i = 0; i < b.P.Count; i++) b.P[i] *= size;
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = b.P.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = b.N.ToArray();
        arr[(int)Mesh.ArrayType.TexUV] = b.U.ToArray();
        arr[(int)Mesh.ArrayType.Color] = col;
        arr[(int)Mesh.ArrayType.Index] = b.I.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        var st = new SurfaceTool();
        st.CreateFrom(mesh, 0);
        st.GenerateTangents();
        var mat = (StandardMaterial3D)Made.Surface("rock_boulder_dry", 0.7f, "#8c867c").Duplicate();
        mat.VertexColorUseAsAlbedo = true;
        var stones = new MeshInstance3D { Name = "Stones", Mesh = st.Commit(), MaterialOverride = mat, Layers = RingLayer };
        stones.AddChild(RingGlow(size));
        return stones;
    }

    /// <summary>(C01 set) The coals' glow on what sits round them (RingLayer): low in the middle, so it reaches the
    /// stones' inner faces and the ash, not their tops (a hand over the middle, it comes from below them).</summary>
    static OmniLight3D RingGlow(float size) => new()
    {
        Name = "RingGlow", Position = new Vector3(0, 0.08f * size, 0), LightColor = new Color(1f, 0.42f, 0.12f),
        LightEnergy = RingK, OmniRange = 1.05f * size, OmniAttenuation = 1.2f, ShadowEnabled = false, LightSpecular = 0.2f,
        LightCullMask = RingLayer,
    };

    /// <summary>A field stone: a sphere of 24 by 14, pushed out and in by
    /// slow noise for its shape and quicker noise for its knobs, its
    /// underside flattened; placed and sized by `at`.</summary>
    static void Stone(Shapes.Build b, Transform3D at, float seed)
    {
        const int rings = 14, segs = 24;
        int v0 = b.P.Count, i0 = b.I.Count;
        float Nz(Vector3 d, float f) => Mathf.Sin(d.X * f + seed) * Mathf.Sin(d.Y * f * 1.3f + seed * 1.7f) * Mathf.Sin(d.Z * f * 0.9f + seed * 0.6f);
        for (int i = 0; i <= rings; i++)
            for (int s = 0; s <= segs; s++)
            {
                float phi = Mathf.Pi * i / rings, th = Mathf.Tau * s / segs;
                var d = new Vector3(Mathf.Sin(phi) * Mathf.Cos(th), Mathf.Cos(phi), Mathf.Sin(phi) * Mathf.Sin(th));
                float k = 1 + 0.16f * Nz(d, 2.1f) + 0.07f * Nz(d, 4.7f) + 0.025f * Nz(d, 11f);
                var p = d * 0.5f * k;
                if (p.Y < -0.15f) p.Y = -0.15f + (p.Y + 0.15f) * 0.3f;
                b.V(at * p, Vector3.Up, new Vector2((float)s / segs, (float)i / rings));
            }
        for (int i = 0; i < rings; i++)
            for (int s = 0; s < segs; s++)
            {
                int a0 = v0 + i * (segs + 1) + s, a2 = a0 + segs + 1;
                b.I.Add(a0); b.I.Add(a0 + 1); b.I.Add(a2 + 1);
                b.I.Add(a0); b.I.Add(a2 + 1); b.I.Add(a2);
            }
        // Each triangle turned to face out from the stone's middle; then
        // normals from the faces, welded across the seam and the poles.
        var mid = at.Origin;
        for (int k = i0; k < b.I.Count; k += 3)
        {
            int a = b.I[k], c1 = b.I[k + 1], c2 = b.I[k + 2];
            var face = (b.P[c2] - b.P[a]).Cross(b.P[c1] - b.P[a]);
            if (face.Dot(b.P[a] + b.P[c1] + b.P[c2] - 3 * mid) < 0) { b.I[k + 1] = c2; b.I[k + 2] = c1; }
        }
        b.Warp(v0, i0, p => p, weld: true);
    }

    /// <summary>--campfire-ember K, --campfire-bounce K, --campfire-wash K: the logs' ember cracks, the ash bed's and the logs' warm wash, for pictures.</summary>
    static readonly float EmberK = SurvivorUnchained.Args.Num("campfire-ember", 3f);
    static readonly float BounceK = SurvivorUnchained.Args.Num("campfire-bounce", 0f);
    static readonly float WashK = SurvivorUnchained.Args.Num("campfire-wash", 4.5f);

    /// <summary>What the fire burns on, our own (tools/assets/env_campfire.py, art/world/campfire): five
    /// logs in a collapsed star, burnt toward the middle with ember cracks that breathe
    /// (shaders/campfire_wood.gdshader), real end caps; a flat ash bed with a few coals. The logs
    /// are on <see cref="CoalLayer"/>, out of the fire's light, washed warm in their shader and lit
    /// from below by the coals' glow; the bed takes the fire's light. Null without the model.</summary>
    static Node3D? Wood(float size)
    {
        const string path = "res://art/world/campfire/campfire.glb";
        if (!ResourceLoader.Exists(path)) return null;
        var scene = GD.Load<PackedScene>(path).Instantiate<Node3D>();
        var root = new Node3D { Name = "Coals", Scale = Vector3.One * size };
        var shader = GD.Load<Shader>("res://shaders/campfire_wood.gdshader");
        ShaderMaterial? look = null;
        foreach (var name in new[] { "Logs", "Bed" })
        {
            if (scene.FindChild(name, true, false) is not MeshInstance3D src) continue;
            if (look == null && src.GetActiveMaterial(0) is StandardMaterial3D std)
            {
                look = new ShaderMaterial { Shader = shader };
                look.SetShaderParameter("albedo_tex", std.AlbedoTexture);
                look.SetShaderParameter("normal_tex", std.NormalTexture);
                look.SetShaderParameter("ember_tex", std.EmissionTexture);
                look.SetShaderParameter("ember_k", EmberK);
                look.SetShaderParameter("bounce_k", BounceK);
            }
            var mat = look;
            if (look != null) { mat = (ShaderMaterial)look.Duplicate(); if (name == "Bed") mat.SetShaderParameter("bed", 1f); }
            var mi = new MeshInstance3D { Name = name, Mesh = src.Mesh, MaterialOverride = mat };
            // The bed takes the fire's light too (on the coals' layer its pale ash showed moonlit blue
            // under the flames); it casts no shadow.
            // (C01 set) and it is out of that light (RingLayer): lifted over it, the light made a white glare of the ash.
            if (name == "Bed") { mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off; mi.Layers = RingLayer; }
            // The logs read dark with their cracks glowing, washed warm by the flames in the shader
            // (floodlit by the light over the flames they were orange cobs).
            else { mi.Layers = CoalLayer; mat?.SetShaderParameter("wash_k", WashK); }
            root.AddChild(mi);
        }
        scene.Free();
        // The coals' own glow, falling off within a metre: what is held just over them (a hand, in
        // C01) and the logs' undersides are lit from below, deep orange.
        root.AddChild(new OmniLight3D
        {
            Name = "Glow", Position = new Vector3(0, 0.1f, 0), LightColor = new Color(1f, 0.36f, 0.08f),
            LightEnergy = 0.35f, OmniRange = 1.1f * size, OmniAttenuation = 1.6f, ShadowEnabled = false, LightSpecular = 0.3f,
            LightCullMask = 0xFFFFF & ~CoalLayer,
        });
        return root;
    }

    /// <summary>The procedural bed, used when the model is missing. What the fire burns on and what is left when it burns down:
    /// a bed of ash, a low heap of charcoal lumps, and four sticks laid in a
    /// star, their inner ends burnt to coal (shaders/coals.gdshader). A hand
    /// held over it in C01 is lit by it, and the title's flames stand on it.</summary>
    static MeshInstance3D Coals(float size)
    {
        var b = new Shapes.Build();
        var rng = new RandomNumberGenerator { Seed = 23 };
        // The ash: a lumpy disc, highest in the middle.
        int rings = 7, segs = 28;
        int c0 = b.V(new Vector3(0, 0.03f, 0) * size, Vector3.Up);
        for (int i = 1; i <= rings; i++)
            for (int s = 0; s < segs; s++)
            {
                float r = 0.42f * i / rings, a = Mathf.Tau * s / segs;
                // Its rim dips under the ground, unevenly, so it has no edge.
                float h = 0.03f * (1 - Mathf.Pow(r / 0.42f, 1.5f)) + 0.008f * (rng.Randf() - 0.5f) - (i == rings ? 0.012f + 0.012f * rng.Randf() : 0);
                b.V(new Vector3(Mathf.Cos(a) * r, h - 0.004f, Mathf.Sin(a) * r) * size, Vector3.Up);
            }
        for (int s = 0; s < segs; s++) b.Tri(c0, 1 + s, 1 + (s + 1) % segs);
        for (int i = 0; i < rings - 1; i++)
            for (int s = 0; s < segs; s++)
            {
                int a0 = 1 + i * segs + s, a1 = 1 + i * segs + (s + 1) % segs;
                b.Quad(a0, a1, a1 + segs, a0 + segs);
            }
        // The charcoal: lumps heaped low, each a stone of a few flat faces.
        for (int k = 0; k < 30; k++)
        {
            float r = 0.3f * Mathf.Sqrt(rng.Randf()), a = rng.Randf() * Mathf.Tau;
            float len = 0.05f + 0.06f * rng.Randf(), wid = 0.03f + 0.03f * rng.Randf(), hi = 0.022f + 0.022f * rng.Randf();
            var at = new Vector3(Mathf.Cos(a) * r, 0.025f + 0.045f * (1 - r / 0.32f) + hi * 0.3f, Mathf.Sin(a) * r);
            var basis = new Basis(Vector3.Up, rng.Randf() * Mathf.Tau) * new Basis(Vector3.Forward, (rng.Randf() - 0.5f) * 0.5f);
            Lump(b, new Transform3D(basis.Scaled(new Vector3(len, hi, wid) * size), at * size), rng);
        }
        // The sticks, laid in a star from the stones to the middle, burnt from the middle out.
        for (int k = 0; k < 4; k++)
        {
            float a = k * Mathf.Tau / 4 + 0.5f + 0.3f * rng.Randf(), r0 = 0.06f + 0.05f * rng.Randf(), rad = 0.032f + 0.012f * rng.Randf();
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            int kk = k;
            var path = Shapes.Path(9, t => (dir * Mathf.Lerp(r0, 0.6f, t) + new Vector3(0, Mathf.Lerp(0.05f, 0.13f, t) + 0.006f * Mathf.Sin(t * 9 + kk), 0)) * size);
            Shapes.Tube(b, path, t => rad * size * (0.55f + 0.45f * Mathf.SmoothStep(0, 0.35f, t)), 10);
        }
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/coals.gdshader") };
        mat.SetShaderParameter("size", size);
        // On a layer of their own, which neither their glow nor their fire's
        // light reaches: the light comes from them, so they are not lit by it.
        var coals = new MeshInstance3D { Name = "Coals", Mesh = b.Faceted().Mesh(), MaterialOverride = mat, Layers = CoalLayer };
        // Their own glow, falling off within a metre: what is held just over
        // them (a hand, in C01) is lit from below, deep orange.
        coals.AddChild(new OmniLight3D
        {
            Name = "Glow", Position = new Vector3(0, 0.1f, 0) * size, LightColor = new Color(1f, 0.36f, 0.08f),
            LightEnergy = 0.35f, OmniRange = 1.1f * size, OmniAttenuation = 1.6f, ShadowEnabled = false, LightSpecular = 0.3f,
            LightCullMask = 0xFFFFF & ~CoalLayer,
        });
        return coals;
    }

    /// <summary>A charcoal lump: a sphere of a few rings, each corner pushed in
    /// or out, placed and sized by `at`.</summary>
    static void Lump(Shapes.Build b, Transform3D at, RandomNumberGenerator rng)
    {
        const int rings = 4, segs = 7;
        int v0 = b.P.Count;
        var bump = new float[(rings + 1) * segs];
        for (int i = 0; i < bump.Length; i++) bump[i] = 0.8f + 0.4f * rng.Randf();
        for (int i = 0; i <= rings; i++)
            for (int s = 0; s < segs; s++)
            {
                float phi = Mathf.Pi * i / rings, th = Mathf.Tau * s / segs;
                var d = new Vector3(Mathf.Sin(phi) * Mathf.Cos(th), Mathf.Cos(phi), Mathf.Sin(phi) * Mathf.Sin(th));
                b.V(at * (d * 0.5f * bump[i * segs + s]), (at.Basis * d).Normalized());
            }
        for (int i = 0; i < rings; i++)
            for (int s = 0; s < segs; s++)
            {
                int a0 = v0 + i * segs + s, a1 = v0 + i * segs + (s + 1) % segs;
                b.Quad(a0, a1, a1 + segs, a0 + segs);
            }
    }

    /// <summary>A soft round sprite: bright middle, nothing at the edge.</summary>
    static Texture2D Blob(Color inner, Color outer)
    {
        var g = new Gradient();
        g.SetColor(0, inner);
        g.SetColor(1, outer);
        return new GradientTexture2D
        {
            Gradient = g, Fill = GradientTexture2D.FillEnum.Radial, Width = 64, Height = 64,
            FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
        };
    }

    static StandardMaterial3D Sprite(Texture2D tex, bool additive)
    {
        return new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
            Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
            BlendMode = additive ? BaseMaterial3D.BlendModeEnum.Add : BaseMaterial3D.BlendModeEnum.Mix,
            BillboardMode = BaseMaterial3D.BillboardModeEnum.Particles,
            VertexColorUseAsAlbedo = true,
            AlbedoTexture = tex,
            DepthDrawMode = BaseMaterial3D.DepthDrawModeEnum.Disabled,
            NoDepthTest = false,
        };
    }

    /// <summary>A colour over a particle's life; HDR, so a flame can be
    /// brighter than white and bloom.</summary>
    static GradientTexture1D Ramp(params (float At, Color C)[] stops)
    {
        var g = new Gradient();
        g.Offsets = System.Array.ConvertAll(stops, s => s.At);
        g.Colors = System.Array.ConvertAll(stops, s => s.C);
        return new GradientTexture1D { Gradient = g, UseHdr = true };
    }

    static CurveTexture Curve(params (float At, float V)[] pts)
    {
        var c = new Curve();
        foreach (var (at, v) in pts) c.AddPoint(new Vector2(at, v));
        return new CurveTexture { Curve = c };
    }

    /// <summary>The flame: the kit's camp fire (FlameKit, three simulated cards out of step); its one
    /// shadowed light stays the zone's.</summary>
    static Node3D? FilmedFlames(float size)
    {
        var root = new Node3D { Name = "Flames" };
        FlameKit.Add(root, Vector3.Zero, FlameKind.Camp, scale: size, light: false);
        return root;
    }

    static GpuParticles3D Flames(float size)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.18f * size,
            Direction = Vector3.Up, Spread = 10, InitialVelocityMin = 0.7f * size, InitialVelocityMax = 1.3f * size,
            Gravity = new Vector3(0, 0.8f, 0), DampingMin = 0.5f, DampingMax = 1f,
            ScaleMin = 0.55f * size, ScaleMax = 0.95f * size,
            ScaleCurve = Curve((0, 0.6f), (0.3f, 1f), (1, 0.35f)),
            AngleMin = -10, AngleMax = 10,
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 0.6f, TurbulenceNoiseScale = 2.5f, TurbulenceInfluenceMin = 0.05f, TurbulenceInfluenceMax = 0.12f,
        };
        // The colour, the licking edge and how much light it adds are the
        // flame shader's (shaders/flame.gdshader).
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flame.gdshader") };
        var (first, count) = Sprites.Range("muzzle");
        mat.SetShaderParameter("sprites", Sprites.Array);
        mat.SetShaderParameter("first_tongue", (float)first);
        mat.SetShaderParameter("tongues", (float)count);
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("glow", 0.55f);
        return new GpuParticles3D
        {
            Name = "Flames", Amount = 16, Lifetime = 0.8, ProcessMaterial = p, Position = new Vector3(0, 0.1f, 0),
            DrawPass1 = new QuadMesh { Size = new Vector2(0.45f, 0.9f), CenterOffset = new Vector3(0, 0.3f, 0), Material = mat },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Preprocess = 1.0,
        };
    }

    /// <summary>--ember-w W, --ember-l L: a spark's streak (m). Thin, so at the close-up it is a streak 1-3 px wide, not a
    /// soft round disc (11 mm wide, a radial blob, it read as an orb). 12 cm long, not 40 (E7b r3: at the close-up a 40 cm streak
    /// read as a thin straight white line through the flames, the same in every shot); they wander more, so their paths bend.</summary>
    static readonly float EmberW = SurvivorUnchained.Args.Num("ember-w", 0.006f), EmberL = SurvivorUnchained.Args.Num("ember-l", 0.12f);

    /// <summary>Sparks: few and small, each a short streak along its flight, rising off the coals,
    /// wandering a little and fading within a metre or two (not a spray).</summary>
    static GpuParticles3D Embers(float size)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.16f * size,
            Direction = Vector3.Up, Spread = 14, InitialVelocityMin = 0.8f, InitialVelocityMax = 1.7f,
            Gravity = new Vector3(0.05f, 0.35f, 0), DampingMin = 0.3f, DampingMax = 0.6f,
            ScaleMin = 0.6f, ScaleMax = 1.1f, ScaleCurve = Curve((0, 1f), (0.7f, 0.8f), (1, 0.15f)),
            ParticleFlagAlignY = true, LifetimeRandomness = 0.45,
            // Hot, not blinding: kept just under the bloom's threshold, so the glow doesn't
            // spread them into one orange ball over the fire.
            ColorRamp = Ramp((0, new Color(1.05f, 0.6f, 0.2f, 1)), (0.55f, new Color(0.95f, 0.34f, 0.06f, 0.9f)), (1, new Color(0.5f, 0.1f, 0.02f, 0))),
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 1.2f, TurbulenceNoiseScale = 1.2f, TurbulenceInfluenceMin = 0.1f, TurbulenceInfluenceMax = 0.24f,
        };
        if (emberLook == null)
        {
            // Drawn along its velocity (align Y), turned to the camera about it; sized by the
            // process scale (a particle billboard drops it unless told to keep it).
            emberLook = Sprite(Blob(Colors.White, new Color(1, 1, 1, 0)), true);
            emberLook.BillboardMode = BaseMaterial3D.BillboardModeEnum.FixedY;
            emberLook.BillboardKeepScale = true;
        }
        return new GpuParticles3D
        {
            Name = "Embers", Amount = 12, Lifetime = 1.9, ProcessMaterial = p, Position = new Vector3(0, 0.22f, 0) * size,
            DrawPass1 = new QuadMesh { Size = new Vector2(EmberW, EmberL) * size, Material = emberLook },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Preprocess = 2.0,
        };
    }

    /// <summary>Smoke: a thin dark thread off the top of the flames, drifting with the air and
    /// opening as it climbs, gone by about 3 m (never a grey blanket over the fire from above).</summary>
    static GpuParticles3D Smoke(float size)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.12f * size,
            Direction = Vector3.Up, Spread = 6, InitialVelocityMin = 0.55f, InitialVelocityMax = 0.75f,
            DampingMin = 0.05f, DampingMax = 0.12f, Gravity = new Vector3(0.16f, 0.06f, 0.05f),
            ScaleMin = 0.8f, ScaleMax = 1.2f, ScaleCurve = Curve((0, 0.35f), (1, 1.7f)),
            AngleMin = -180, AngleMax = 180, AngularVelocityMin = -20, AngularVelocityMax = 20,
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 0.8f, TurbulenceNoiseScale = 1.2f, TurbulenceInfluenceMin = 0.03f, TurbulenceInfluenceMax = 0.07f,
            // Dark: night smoke is barely lit (linear values), and thin.
            ColorRamp = Ramp((0, new Color(0.03f, 0.028f, 0.025f, 0)), (0.15f, new Color(0.035f, 0.032f, 0.03f, 0.3f)), (0.6f, new Color(0.04f, 0.04f, 0.042f, 0.13f)), (1, new Color(0.045f, 0.045f, 0.05f, 0))),
        };
        if (smokeLook == null) { smokeLook = Sprite(Sprites.Puff, false); smokeLook.BillboardKeepScale = true; }
        return new GpuParticles3D
        {
            Name = "Smoke", Amount = 14, Lifetime = 3.2, ProcessMaterial = p, Position = new Vector3(0, 0.95f, 0) * size,
            DrawPass1 = new QuadMesh { Size = new Vector2(0.55f, 0.55f) * size, Material = smokeLook },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Preprocess = 3.2,
        };
    }

    /// <summary>A chimney's smoke: a thin grey thread leaning with the wind
    /// (the web game's ZoneKit.chimney), grey by day, dark after it.</summary>
    public static GpuParticles3D ChimneySmoke()
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.12f,
            Direction = new Vector3(0.4f, 1, 0.1f).Normalized(), Spread = 8, InitialVelocityMin = 0.9f, InitialVelocityMax = 1.2f,
            DampingMin = 0.2f, DampingMax = 0.3f, Gravity = new Vector3(0.12f, 0, 0.03f),
            ScaleMin = 0.5f, ScaleMax = 0.6f, ScaleCurve = Curve((0, 1f), (1, 5.2f)),
            AngleMin = -180, AngleMax = 180, AngularVelocityMin = -15, AngularVelocityMax = 15,
        };
        var smoke = new GpuParticles3D
        {
            Name = "Chimney", Amount = 15, Lifetime = 4.5, ProcessMaterial = p, Preprocess = 4.5,
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = Sprite(Sprites.Puff, false) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
        ChimneyLook(smoke, false);
        return smoke;
    }

    /// <summary>A wick just put out (the tower's lamp in C04): a thread of smoke, thin
    /// where it leaves the flame and wavering as it climbs and opens. It stops
    /// coming after a breath or two and the last of it thins away.</summary>
    public static GpuParticles3D WickSmoke(Color col)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Point,
            Direction = Vector3.Up, Spread = 2, InitialVelocityMin = 0.46f, InitialVelocityMax = 0.52f,
            DampingMin = 0.06f, DampingMax = 0.1f, Gravity = new Vector3(0.03f, 0.02f, 0.01f),
            // Sized in the mesh (a billboard ignores the process scale); it opens as it climbs.
            ScaleCurve = Curve((0, 0.45f), (0.4f, 1.3f), (1, 3.6f)),
            AngleMin = -180, AngleMax = 180, AngularVelocityMin = -30, AngularVelocityMax = 30,
            // Straight while it is hot, then it starts to curl.
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 1.2f, TurbulenceNoiseScale = 0.5f, TurbulenceNoiseSpeed = new Vector3(0, 0.3f, 0),
            TurbulenceInfluenceMin = 0.05f, TurbulenceInfluenceMax = 0.09f, TurbulenceInfluenceOverLife = Curve((0, 0f), (0.35f, 0.12f), (1, 0.6f)),
        };
        var a = col.SrgbToLinear();
        p.ColorRamp = Ramp((0, a with { A = 0 }), (0.04f, a with { A = 0.9f }), (0.5f, a with { A = 0.6f }), (1, a with { A = 0 }));
        return new GpuParticles3D
        {
            Name = "WickSmoke", Amount = 130, Lifetime = 2.4, ProcessMaterial = p, Emitting = true,
            DrawPass1 = new QuadMesh { Size = new Vector2(0.06f, 0.06f), Material = Sprite(Sprites.Puff, false) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
    }

    public static void ChimneyLook(GpuParticles3D smoke, bool night)
    {
        // The web game's colours (linear here, its alpha along the life).
        Color a = new Color(night ? "#2a2c34" : "#8a8680").SrgbToLinear(), b = new Color(night ? "#14161c" : "#6a6864").SrgbToLinear();
        float alpha = night ? 0.3f : 0.22f;
        ((ParticleProcessMaterial)smoke.ProcessMaterial).ColorRamp =
            Ramp((0, a with { A = 0 }), (0.15f, a with { A = alpha }), (1, b with { A = 0 }));
    }

    /// <summary>Moths about a lamp after dark: pale specks that dart and
    /// circle (the web game's ZoneKit.moths).</summary>
    public static GpuParticles3D Moths()
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Ring, EmissionRingRadius = 0.5f, EmissionRingInnerRadius = 0.3f,
            EmissionRingHeight = 0.6f, EmissionRingAxis = Vector3.Up,
            Direction = Vector3.Right, Spread = 180, InitialVelocityMin = 0.8f, InitialVelocityMax = 1.4f,
            Gravity = Vector3.Zero, DampingMin = 0.3f, DampingMax = 0.5f, ScaleMin = 0.05f, ScaleMax = 0.06f,
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 3f, TurbulenceNoiseScale = 0.8f, TurbulenceInfluenceMin = 0.3f, TurbulenceInfluenceMax = 0.6f,
            ColorRamp = Ramp((0, new Color(1.6f, 1.45f, 1.1f, 0)), (0.1f, new Color(1.6f, 1.45f, 1.1f, 0.9f)), (1, new Color(1.3f, 1.05f, 0.6f, 0))),
        };
        // Godot's particle billboard drops the particle's scale unless told to keep it: the specks
        // were drawn a metre across, cream puffballs round every lamp from dusk on.
        var look = Sprite(Blob(Colors.White, new Color(1, 1, 1, 0)), true);
        look.BillboardKeepScale = true;
        return new GpuParticles3D
        {
            Name = "Moths", Amount = 7, Lifetime = 2.1, ProcessMaterial = p, Emitting = false,
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = look },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
    }
}
