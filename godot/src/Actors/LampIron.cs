using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A keeper's lamp-iron: a flat-topped square cage of old black iron, riveted straps, glass behind
/// the bars, hung by a ring at the top (tools/assets/lamp_iron.py, art/props/keeper_lamp; concept A).
/// The Warden carries one, and the same pattern burns in the toll tower's window (C04) and stands on
/// Vonnra's table (C09), so the eye can tie them together before anyone says so. The flame is the
/// caller's (Fire puts the Warden's in it). Only the cage throws shadows: from a light at the flame,
/// the bars stripe whatever it lights; the top, ring and bail don't, so the light still reaches up.
/// </summary>
public static class LampIron
{
    /// <summary>Where the flame sits, from the ring at the top (the origin).</summary>
    public const float FlameY = -0.15f;
    /// <summary>The underside of the feet: set it here to stand the lamp on a sill.</summary>
    public const float FootY = -0.23f;
    /// <summary>The wick's top, where the flame stands.</summary>
    public const float WickY = -0.1815f;
    /// <summary>The Warden's lantern (tools/assets/warden_lamp.py, concept A): the flame's middle, the wick's top and the
    /// feet, from its ring; and its cage (inner half-width, the rim under the dome, the base plate's top).</summary>
    public const float WardenFlameY = -0.166f, WardenWickY = -0.2085f, WardenFootY = -0.282f;
    static readonly Vector3 WardenCage = new(0.0505f, -0.078f, -0.258f);
    const string Scene = "res://art/props/keeper_lamp/keeper_lamp.glb";
    const string WardenScene = "res://art/props/keeper_lamp/warden_lamp.glb";
    const string Masks = "res://art/props/keeper_lamp/iron_masks.png";
    static ShaderMaterial? iron, blade;
    static Shader? glassShader;

    /// <summary>The lamp's old iron (shaders/keeper_iron.gdshader), shared.</summary>
    public static ShaderMaterial Iron => iron ??= Sooty(IronMat(false));

    static ShaderMaterial Sooty(ShaderMaterial m) { m.SetShaderParameter("soot_k", 1f); return m; }

    static ShaderMaterial IronMat(bool sword)
    {
        var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/keeper_iron.gdshader") };
        m.SetShaderParameter("masks", GD.Load<Texture2D>(Masks));
        if (sword)
        {
            // A blade: no silt line (it's long, not standing in its own muck), a little more wear on its edges.
            m.SetShaderParameter("silt_k", 0f);
            m.SetShaderParameter("tile", 6f);
            m.SetShaderParameter("rust_k", 0.6f);
            m.SetShaderParameter("wear", 1.15f);
            // (its leather grip: a warm dark brown, not the lamp's cord)
            // (Warden 7 r3, the vertex colours read at last: the grip dull dark leather, the guard and pommel dark iron worn
            // at the edges only, the blade a mid steel with a bright honed edge, its stain faint)
            m.SetShaderParameter("cord", new Vector3(0.036f, 0.024f, 0.016f));
            m.SetShaderParameter("cord_pitch", 0.024f);
            m.SetShaderParameter("cord_groove", 0.3f);
            m.SetShaderParameter("edge_lo", 0.5f);
            m.SetShaderParameter("edge_hi", 0.85f);
            m.SetShaderParameter("cord_spec", 0.22f);
            m.SetShaderParameter("cord_rough", 0.8f);
            // (Warden 7 lamp solver: the flat 204 at s12 at 0.40, target 130-160; the guard and pommel 165-197, target 55-75:
            // darker iron and worn steel, rougher, specular 0.3 on the fittings)
            m.SetShaderParameter("blade_flat", new Vector3(1, 1, 0.975f) * SurvivorUnchained.Args.Num("blade-flat", 0.28f));
            m.SetShaderParameter("iron", new Vector3(0.030f, 0.029f, 0.027f));
            m.SetShaderParameter("steel", new Vector3(0.16f, 0.157f, 0.152f));
            m.SetShaderParameter("edge_rough", 0.6f);
            m.SetShaderParameter("iron_spec", 0.3f);
            m.SetShaderParameter("blade_edge", new Vector3(0.72f, 0.72f, 0.70f));
            m.SetShaderParameter("blade_stain", 0.5f);
            m.SetShaderParameter("blade_rough", 0.52f);
            m.SetShaderParameter("bevel_rough", 0.3f);
            m.SetShaderParameter("iron_metal", 0.45f);
            m.SetShaderParameter("iron_rough", 0.82f);
            m.SetShaderParameter("wet", 0.2f);
        }
        return m;
    }

    /// <summary>The lamp-iron; with a bail, the link through its ring that long, to hang it by.</summary>
    public static Node3D Make(float bail = 0) => Build(Scene, bail, false);

    /// <summary>The Ford-Warden's lantern (concept A: tall, a ribbed dome, dark glass), its own iron so its flame can
    /// light it (LampFire); with a bail, hung as Make's. His chest pendant is the same, small and unlit.</summary>
    public static Node3D MakeWarden(float bail = 0) => Build(WardenScene, bail, true);

    /// <summary>The flame's middle in this lamp's own frame (the Warden's or the sill lamp's).</summary>
    public static float FlameOf(Node3D lamp) => lamp.HasMeta("flame_y") ? (float)lamp.GetMeta("flame_y") : FlameY;

    static Node3D Build(string scene, float bail, bool warden)
    {
        if (!ResourceLoader.Exists(scene)) { GD.PushWarning($"LampIron: no {scene}, the primitive lamp"); return Primitive(bail); }
        var lamp = new Node3D { Name = "LampIron" };
        var model = GD.Load<PackedScene>(scene).Instantiate<Node3D>();
        ShaderMaterial ironMat = Iron;
        if (warden)
        {
            lamp.SetMeta("flame_y", WardenFlameY);
            lamp.SetMeta("wick_y", WardenWickY);
            ironMat = Sooty(IronMat(false));
            ironMat.SetShaderParameter("cage", WardenCage);
            ironMat.SetShaderParameter("silt_top", -0.236f);
            ironMat.SetShaderParameter("silt_fade", 0.04f);
            ironMat.SetShaderParameter("flame_o", new Vector3(0, WardenFlameY, 0));
            ironMat.SetShaderParameter("tile", 11f);
            // (Warden 7: its bars and small parts are all bevel to the convexity mask, so at the sill lamp's wear the whole
            // cage read worn steel and mirrored the night sky pale: a little bright wear on the edges only, a darker steel)
            ironMat.SetShaderParameter("wear", SurvivorUnchained.Args.Num("lamp-wear", 0.4f));
            ironMat.SetShaderParameter("steel", new Vector3(1, 0.98f, 0.95f) * SurvivorUnchained.Args.Num("lamp-steel", 0.17f));
            ironMat.SetShaderParameter("iron", new Vector3(1, 0.95f, 0.88f) * SurvivorUnchained.Args.Num("lamp-ironk", 0.04f));
            lamp.SetMeta("iron", ironMat);
        }
        lamp.AddChild(model);
        glassShader ??= GD.Load<Shader>("res://shaders/keeper_glass.gdshader");
        foreach (var n in model.FindChildren("*", "MeshInstance3D", true, false))
        {
            var mi = (MeshInstance3D)n;
            string name = mi.Name.ToString();
            if (name.StartsWith("Glass"))
            {
                var g = new ShaderMaterial { Shader = glassShader };
                g.SetShaderParameter("masks", GD.Load<Texture2D>(Masks));
                g.SetShaderParameter("lit", 0f);
                if (warden)
                {
                    g.SetShaderParameter("dark", 1f);
                    g.SetShaderParameter("flame_at", new Vector3(0, WardenFlameY, 0));
                    // (Warden 7 r1: the panes lit round the flame, a halo two or three flames wide; at 0.026 and 0.12 the lamp read a dark box)
                    g.SetShaderParameter("spot_r", SurvivorUnchained.Args.Num("lamp-spot", 0.045f));
                    g.SetShaderParameter("glow_k", SurvivorUnchained.Args.Num("lamp-glowk", 0.3f));
                    g.SetShaderParameter("frost", SurvivorUnchained.Args.Num("lamp-frost", 0.8f));
                    g.SetShaderParameter("reflect_col", new Vector3(0.13f, 0.17f, 0.24f));
                    g.SetShaderParameter("edge_k", 0.25f);
                    // (Warden 7 lamp solver: the dome's glass frosted and lit read pale over its eight ribs, a round birdcage from
                    // above at s11; it is smoked, soot-dark glass under the hood, only a little of the flame in it)
                    if (name.StartsWith("GlassDome"))
                    {
                        g.SetShaderParameter("frost", SurvivorUnchained.Args.Num("lamp-dome-frost", 0f));
                        g.SetShaderParameter("glow_k", SurvivorUnchained.Args.Num("lamp-dome-glowk", 0.12f));
                        g.SetShaderParameter("reflect_col", new Vector3(0.07f, 0.09f, 0.12f));
                    }
                }
                mi.MaterialOverride = g;
                if (warden && System.Environment.GetEnvironmentVariable("WARDEN_LAMP_GLASS") == "0") mi.Visible = false;   // (for pictures)
                // (every pane and the dome's glass: no shadow. The dome's glass threw one, so his own lamp's light never
                // reached the fist it hangs from or the hood over it: Warden 7 r1 "it lights nothing near it")
                mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                if (lamp.HasMeta("glass")) { lamp.SetMeta("glass2", g); continue; }
                lamp.SetMeta("glass", g);
                continue;
            }
            mi.MaterialOverride = ironMat;
            if (name.StartsWith("Cage")) continue;
            mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
            if (name.StartsWith("Bail"))
            {
                mi.Visible = bail > 0;
                // The link reaches 0.092 above the ring as made; the fist closes 0.02 under its top.
                if (bail > 0) mi.Scale = new Vector3(1, (bail + 0.022f) / 0.092f, 1);
            }
        }
        return lamp;
    }

    /// <summary>The glass's light: the flame's colour (linear) and how lit (0 dark glass).</summary>
    public static void Glass(Node3D lamp, Color linear, float lit)
    {
        foreach (var key in new[] { "glass", "glass2" })
        {
            if (!lamp.HasMeta(key) || lamp.GetMeta(key).Obj is not ShaderMaterial g) continue;
            g.SetShaderParameter("glow", new Vector3(linear.R, linear.G, linear.B));
            g.SetShaderParameter("lit", lit);
        }
        // The Warden's lantern: its flame lights its own iron (keeper_iron inner_k), out with it.
        if (lamp.HasMeta("iron") && lamp.GetMeta("iron").Obj is ShaderMaterial im)
        {
            im.SetShaderParameter("inner_col", new Vector3(linear.R, linear.G, linear.B));
            im.SetShaderParameter("inner_k", InnerK * lit);
        }
    }

    /// <summary>WARDEN_LAMP_PROBE: every mesh of a lamp (name, shown, layers, shadow, its material and the glass's lit), its box in
    /// the world and its distance from the camera (Warden 7: which mesh draws at the play camera).</summary>
    public static string Dump(Node3D lamp)
    {
        var sb = new System.Text.StringBuilder();
        var cam = lamp.GetViewport()?.GetCamera3D();
        foreach (var n in lamp.FindChildren("*", "GeometryInstance3D", true, false))
        {
            var gi = (GeometryInstance3D)n;
            var mat = gi.MaterialOverride;
            string mn = mat is ShaderMaterial sm ? System.IO.Path.GetFileName(sm.Shader?.ResourcePath ?? "?") + (sm.Shader?.ResourcePath?.Contains("glass") == true ? " lit " + sm.GetShaderParameter("lit") + " glow_k " + sm.GetShaderParameter("glow_k") + " frost " + sm.GetShaderParameter("frost") : " inner " + sm.GetShaderParameter("inner_k")) : mat?.GetType().Name ?? "none";
            if (mat == null && gi is MeshInstance3D m0 && m0.Mesh != null) mn = "surf0 " + (m0.GetActiveMaterial(0)?.GetType().Name ?? "none");
            var bb = gi.GetAabb(); var c = gi.GlobalTransform * (bb.Position + bb.Size / 2);
            sb.Append('\n').Append($"  {gi.GetPath()} vis {gi.IsVisibleInTree()} layers {gi.Layers:X} shadow {gi.CastShadow} {mn} centre {c} size {gi.GlobalTransform.Basis.Scale.X * bb.Size} cam {(cam != null ? cam.GlobalPosition.DistanceTo(c) : -1):0.00}");
        }
        return sb.ToString();
    }

    /// <summary>--lamp-iron-inner K: how strongly the Warden's flame lights his lantern's own iron (for pictures).</summary>
    static readonly float InnerK = SurvivorUnchained.Args.Num("lamp-iron-inner", 0.3f);
    /// <summary>The layer a lit lantern's meshes go on, so its own light can leave it out (ZoneView.LampLayer).</summary>
    public const uint OwnLayer = 1u << 11;
    /// <summary>The Watch blade's layer, alone, so the Warden's lamp light can leave it to a weaker twin (BossViews).</summary>
    public const uint SwordLayer = 1u << 15;

    /// <summary>The Warden's flame in a lamp made here: the flame kit's cold flame on the wick (no light of
    /// its own: the caller's light is the lamp's) and a soft glow round it.</summary>
    public static LampFire Fire(Node3D lamp) => new(lamp);

    /// <summary>The Warden's old Watch blade (tools/assets/watch_blade.py) in its corroded iron, for Arms.</summary>
    public static Node3D WatchBlade()
    {
        var model = GD.Load<PackedScene>("res://art/weapons/watch_blade.glb").Instantiate<Node3D>();
        if (blade == null)
        {
            blade = IronMat(true);
            // (a look test's overrides: WARDEN_BLADE="blade_rough=0.3;debug_view=1")
            if (System.Environment.GetEnvironmentVariable("WARDEN_BLADE") is { Length: > 0 } ov)
                foreach (var kv in ov.Split(';', System.StringSplitOptions.RemoveEmptyEntries))
                    if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f))
                        blade.SetShaderParameter(k.Trim(), f);
        }
        foreach (var n in model.FindChildren("*", "MeshInstance3D", true, false)) { ((MeshInstance3D)n).MaterialOverride = blade; ((MeshInstance3D)n).Layers = SwordLayer; }
        return model;
    }

    /// <summary>The old lamp of code primitives, if the model is missing.</summary>
    static Node3D Primitive(float bail)
    {
        var mat = new StandardMaterial3D { AlbedoColor = new Color("#1e1c1a"), Metallic = 0.7f, Roughness = 0.38f };
        var lamp = new Node3D { Name = "LampIron" };
        void Add(Mesh m, Vector3 at) { m.SurfaceSetMaterial(0, mat); lamp.AddChild(new MeshInstance3D { Mesh = m, Position = at }); }
        Add(new BoxMesh { Size = new Vector3(0.13f, 0.018f, 0.13f) }, new Vector3(0, -0.06f, 0));
        Add(new BoxMesh { Size = new Vector3(0.13f, 0.02f, 0.13f) }, new Vector3(0, -0.22f, 0));
        foreach (var (x, z) in new[] { (-1, -1), (-1, 1), (1, -1), (1, 1) })
            Add(new BoxMesh { Size = new Vector3(0.012f, 0.16f, 0.012f) }, new Vector3(x * 0.058f, -0.14f, z * 0.058f));
        Add(new TorusMesh { InnerRadius = 0.022f, OuterRadius = 0.032f, Rings = 12, RingSegments = 6 }, Vector3.Zero);
        if (bail > 0) Add(new BoxMesh { Size = new Vector3(0.007f, bail, 0.007f) }, new Vector3(0, bail / 2 + 0.02f, 0));
        return lamp;
    }
}

/// <summary>
/// The flame in the Warden's lamp: the flame kit's simulated cold flame standing on the wick (white-hot at
/// its heart, pale blue out to its edge; warm when a cinematic tints it), a soft Gaussian glow round it, and
/// the glass catching its light. Look() is the cinematic's say (GameCinema "lamp": flame, flameColor, halo).
/// </summary>
public sealed class LampFire
{
    /// <summary>The flame and its glow (hide it to put the lamp out).</summary>
    public readonly Node3D Node;
    readonly Node3D lamp;
    readonly Flame flame;
    readonly ShaderMaterial glow;
    static readonly Color Cold = new(0.32f, 0.58f, 1f);
    bool lastLit = true;
    readonly float flameY, boost;
    /// <summary>--warden-flame-k K: the Warden's flame's brightness over the kit's (a bright point at the play camera).</summary>
    static readonly float ColdPale = SurvivorUnchained.Args.Num("warden-flame-pale", 0.4f);
    static readonly float FlameBoost = SurvivorUnchained.Args.Num("warden-flame-k", 1.6f);
    /// <summary>--warden-flame S: the Warden's flame's size (the kit's lamp card is 0.16 at 1), for pictures.</summary>
    static readonly float FlameScale = SurvivorUnchained.Args.Num("warden-flame", 0.72f);
    Color col = Cold;
    float level = 1;
    /// <summary>--warden-halo K: the soft glow's strength round the flame (Warden 7 r1: 0.32 to 0.5, a halo 2-3x the flame's width).</summary>
    static readonly float HaloK = SurvivorUnchained.Args.Num("warden-halo", 0.85f);

    internal LampFire(Node3D lamp)
    {
        this.lamp = lamp;
        Node = new Node3D { Name = "Fire" };
        lamp.AddChild(Node);
        // The kit's lamp card is 0.16 tall at scale 1; this flame stands about 0.07 of the lamp's measure.
        bool warden = lamp.HasMeta("flame_y");
        flameY = LampIron.FlameOf(lamp);
        boost = warden ? FlameBoost : 1f;
        float wick = lamp.HasMeta("wick_y") ? (float)lamp.GetMeta("wick_y") : LampIron.WickY;
        // (the Warden's lantern: a taller flame, a bright point at the play camera; its meshes on their own layer, so the
        // light at the flame leaves them out and their iron is lit by the shader instead, never white a few cm from it)
        flame = FlameKit.Add(Node, new Vector3(0, wick - 0.0025f, 0), FlameKind.Lamp, cold: true, scale: warden ? FlameScale : 0.46f, light: false);
        if (warden)
            foreach (var n in lamp.FindChildren("*", "GeometryInstance3D", true, false))
                if (n is GeometryInstance3D gi && !Node.IsAncestorOf(gi)) gi.Layers = LampIron.OwnLayer;
        // Its soft edge against what is behind it, tight: the cage's far bars are a few cm behind it.
        flame.SetCard("soft", 0.015f);
        glow = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/lamp_glow.gdshader") };
        Node.AddChild(new MeshInstance3D
        {
            Name = "Glow", Mesh = new QuadMesh { Size = Vector2.One * (warden ? 0.15f : 0.17f), Material = glow },
            Position = new Vector3(0, flameY, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        });
        // (Warden 7 lamp solver: drawn after the frosted panes round it, at 0.92 alpha they veiled the flame and the lantern
        // read a flat pale box at s12 with no core; the flame and its glow sort in front of the glass, the iron still hides them)
        if (warden) foreach (var n in Node.FindChildren("*", "GeometryInstance3D", true, false)) ((GeometryInstance3D)n).SortingOffset = 1f;
        if (warden && System.Environment.GetEnvironmentVariable("WARDEN_LAMP_FIRE") == "0") Node.Scale = Vector3.One * 1e-4f;   // (for pictures)
        Look(null, 1, 1);
    }

    /// <summary>The flame's brightness (1 as built), hue (null: the Warden's cold blue; a warm hue turns it to the
    /// kit's warm flame) and its glow's strength.</summary>
    public void Look(Color? hue, float flameLevel, float halo)
    {
        bool warm = hue is Color h && h.R > h.B;
        flame.SetCard("cold", warm ? 0f : 1f);
        // (the Warden's: paled less, so its edge stays blue and its clipped heart doesn't turn cream under the night grade)
        flame.SetCard("cold_pale", warm ? 0f : boost > 1 ? ColdPale : 1f);
        // Its white-hot heart pulled a little toward blue: the night grade warms what clips, and the core read cream.
        flame.SetCard("core_blue", warm ? 0f : boost > 1 ? 1f : 0.45f);
        // The cinematics' levels were set for the old 3.2-linear egg (C02's night 0.28): 0.28 is the kit's flame a little under its own (its core clipped and the night grade warmed it).
        float k = Mathf.Clamp(0.45f + 0.35f * flameLevel / 0.28f, 0.3f, 1.1f);
        flame.SetCard("intensity", k * boost);
        col = Cold;
        if (hue is Color c && Mathf.Max(c.R, Mathf.Max(c.G, c.B)) > 1e-4f)
        {
            var l = c.SrgbToLinear();
            col = new Color(l.R, l.G, l.B) / Mathf.Max(l.R, Mathf.Max(l.G, l.B));
        }
        level = k;
        glow.SetShaderParameter("color", new Vector3(col.R, col.G, col.B));
        glow.SetShaderParameter("strength", HaloK * halo * k);
        LampIron.Glass(lamp, col, lastLit ? k : 0);
    }

    /// <summary>Burning or not (the glass goes dark with it).</summary>
    public void Lit(bool on)
    {
        if (Node.Visible != on) Node.Visible = on;
        if (on == lastLit) return;
        lastLit = on;
        LampIron.Glass(lamp, col, on ? level : 0);
    }

    /// <summary>Where the flame burns, in the world.</summary>
    public Vector3 At => lamp.ToGlobal(new Vector3(0, flameY, 0));
}
