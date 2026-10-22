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
    const string Scene = "res://art/props/keeper_lamp/keeper_lamp.glb";
    const string Masks = "res://art/props/keeper_lamp/iron_masks.png";
    static ShaderMaterial? iron, blade;
    static Shader? glassShader;

    /// <summary>The lamp's old iron (shaders/keeper_iron.gdshader), shared.</summary>
    public static ShaderMaterial Iron => iron ??= IronMat(false);

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
        }
        return m;
    }

    /// <summary>The lamp-iron; with a bail, the link through its ring that long, to hang it by.</summary>
    public static Node3D Make(float bail = 0)
    {
        if (!ResourceLoader.Exists(Scene)) { GD.PushWarning("LampIron: no keeper_lamp.glb, the primitive lamp"); return Primitive(bail); }
        var lamp = new Node3D { Name = "LampIron" };
        var model = GD.Load<PackedScene>(Scene).Instantiate<Node3D>();
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
                mi.MaterialOverride = g;
                mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                lamp.SetMeta("glass", g);
                continue;
            }
            mi.MaterialOverride = Iron;
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
        if (!lamp.HasMeta("glass") || lamp.GetMeta("glass").Obj is not ShaderMaterial g) return;
        g.SetShaderParameter("glow", new Vector3(linear.R, linear.G, linear.B));
        g.SetShaderParameter("lit", lit);
    }

    /// <summary>The Warden's flame in a lamp made here: the flame kit's cold flame on the wick (no light of
    /// its own: the caller's light is the lamp's) and a soft glow round it.</summary>
    public static LampFire Fire(Node3D lamp) => new(lamp);

    /// <summary>The Warden's old Watch blade (tools/assets/watch_blade.py) in its corroded iron, for Arms.</summary>
    public static Node3D WatchBlade()
    {
        var model = GD.Load<PackedScene>("res://art/weapons/watch_blade.glb").Instantiate<Node3D>();
        blade ??= IronMat(true);
        foreach (var n in model.FindChildren("*", "MeshInstance3D", true, false)) ((MeshInstance3D)n).MaterialOverride = blade;
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
    Color col = Cold;
    float level = 1;

    internal LampFire(Node3D lamp)
    {
        this.lamp = lamp;
        Node = new Node3D { Name = "Fire" };
        lamp.AddChild(Node);
        // The kit's lamp card is 0.16 tall at scale 1; this flame stands about 0.07 of the lamp's measure.
        flame = FlameKit.Add(Node, new Vector3(0, LampIron.WickY - 0.0025f, 0), FlameKind.Lamp, cold: true, scale: 0.46f, light: false);
        // Its soft edge against what is behind it, tight: the cage's far bars are a few cm behind it.
        flame.SetCard("soft", 0.015f);
        glow = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/lamp_glow.gdshader") };
        Node.AddChild(new MeshInstance3D
        {
            Name = "Glow", Mesh = new QuadMesh { Size = Vector2.One * 0.17f, Material = glow },
            Position = new Vector3(0, LampIron.FlameY, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        });
        Look(null, 1, 1);
    }

    /// <summary>The flame's brightness (1 as built), hue (null: the Warden's cold blue; a warm hue turns it to the
    /// kit's warm flame) and its glow's strength.</summary>
    public void Look(Color? hue, float flameLevel, float halo)
    {
        bool warm = hue is Color h && h.R > h.B;
        flame.SetCard("cold", warm ? 0f : 1f);
        flame.SetCard("cold_pale", warm ? 0f : 1f);
        // The cinematics' levels were set for the old 3.2-linear egg (C02's night 0.28): 0.28 and up is the kit's own flame.
        float k = Mathf.Clamp(0.55f + 0.45f * flameLevel / 0.28f, 0.3f, 1.25f);
        flame.SetCard("intensity", k);
        col = Cold;
        if (hue is Color c && Mathf.Max(c.R, Mathf.Max(c.G, c.B)) > 1e-4f)
        {
            var l = c.SrgbToLinear();
            col = new Color(l.R, l.G, l.B) / Mathf.Max(l.R, Mathf.Max(l.G, l.B));
        }
        level = k;
        glow.SetShaderParameter("color", new Vector3(col.R, col.G, col.B));
        glow.SetShaderParameter("strength", 0.32f * halo * k);
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
    public Vector3 At => lamp.ToGlobal(new Vector3(0, LampIron.FlameY, 0));
}
