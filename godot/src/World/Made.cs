using System;
using System.Collections.Generic;
using Godot;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.View;

/// <summary>
/// What things made in code (Shapes) are made of, and the small parts they
/// share: materials that read as what they are (brass, glass, linen, wood,
/// and photographed stone, wood and earth from Poly Haven, CC0, in
/// art/materials), placing a mesh, a light, a chain, a rivet, a lantern.
/// The item photographs (Ui/ItemModels) and the pieces that stand in the
/// world (Pieces) both use them.
/// </summary>
public static class Made
{
    /* ---------------------------------------------------------- materials -- */

    public static StandardMaterial3D Mat(string c, float metal = 0, float rough = 0.8f, bool twoSided = false) => new()
    {
        AlbedoColor = new Color(c), Metallic = metal, Roughness = rough,
        CullMode = twoSided ? BaseMaterial3D.CullModeEnum.Disabled : BaseMaterial3D.CullModeEnum.Back,
    };

    public static StandardMaterial3D Gold() => Mat("#e0b25e", 1, 0.3f);
    public static StandardMaterial3D Brass() => Mat("#b98a4c", 1, 0.38f);
    public static StandardMaterial3D Silver() => Mat("#d8dce4", 1, 0.2f);
    public static StandardMaterial3D Iron() => Mat("#4a4744", 0.85f, 0.48f);
    public static StandardMaterial3D Steel() => Mat("#a9abb2", 1, 0.3f);
    public static StandardMaterial3D Bone() => Mat("#e6d9bc", 0, 0.55f);

    public static StandardMaterial3D Glow(string c, float energy, string? albedo = null) => new()
    {
        AlbedoColor = new Color(albedo ?? c), Roughness = 0.3f, EmissionEnabled = true, Emission = new Color(c), EmissionEnergyMultiplier = energy,
    };

    public static StandardMaterial3D Gem(string c, float glow = 0.35f) => new()
    {
        AlbedoColor = new Color(c), Metallic = 0.25f, Roughness = 0.04f, EmissionEnabled = true, Emission = new Color(c), EmissionEnergyMultiplier = glow,
        ClearcoatEnabled = true, Clearcoat = 1, ClearcoatRoughness = 0.02f,
    };

    /// <summary>Glass: no colour of its own, only what it reflects (the
    /// studio's lights are far brighter than white, so a little is plenty),
    /// darkening what is behind it a touch.</summary>
    public static StandardMaterial3D Glass(string c = "#0c1012", float alpha = 0.18f) => new()
    {
        AlbedoColor = new Color(c) with { A = alpha }, Transparency = BaseMaterial3D.TransparencyEnum.Alpha, Roughness = 0.05f, MetallicSpecular = 0.3f,
    };

    public static StandardMaterial3D Cloth(string c, bool twoSided = false, float tile = 6) => new()
    {
        AlbedoColor = new Color(c), AlbedoTexture = Weave(), Uv1Scale = new Vector3(tile, tile, 1), Roughness = 0.95f,
        RimEnabled = true, Rim = 0.35f, RimTint = 0.7f, CullMode = twoSided ? BaseMaterial3D.CullModeEnum.Disabled : BaseMaterial3D.CullModeEnum.Back,
    };

    public static StandardMaterial3D Grain(string light, string dark, int planks = 1, float rough = 0.7f) => new()
    {
        AlbedoTexture = Wood(new Color(light), new Color(dark), planks), Roughness = rough,
    };

    static readonly Dictionary<string, StandardMaterial3D> surfaces = new();

    /// <summary>A photographed surface (art/materials/ID: its colour, its
    /// relief, and ambient occlusion and roughness in one sheet), laid on by
    /// where it is on the piece (triplanar, so nothing made needs its own
    /// UVs), repeating every so many metres; tinted.</summary>
    public static StandardMaterial3D Surface(string id, float metres, string? tint = null)
    {
        var key = $"{id}|{metres}|{tint}";
        if (surfaces.TryGetValue(key, out var m)) return m;
        string dir = $"res://art/materials/{id}";
        var orm = GD.Load<Texture2D>(ResourceLoader.Exists($"{dir}/arm.jpg") ? $"{dir}/arm.jpg" : $"{dir}/arh.jpg");
        m = new StandardMaterial3D
        {
            AlbedoTexture = GD.Load<Texture2D>($"{dir}/albedo.jpg"), AlbedoColor = tint != null ? new Color(tint) : Colors.White,
            NormalEnabled = true, NormalTexture = GD.Load<Texture2D>($"{dir}/normal.jpg"),
            Roughness = 1, RoughnessTexture = orm, RoughnessTextureChannel = BaseMaterial3D.TextureChannel.Green,
            AOEnabled = true, AOTexture = orm, AOTextureChannel = BaseMaterial3D.TextureChannel.Red,
            Uv1Triplanar = true, Uv1TriplanarSharpness = 4, Uv1Scale = Vector3.One / metres,
        };
        surfaces[key] = m;
        return m;
    }

    /* ------------------------------------------------------------ helpers -- */

    public static MeshInstance3D Add(Node3D to, Mesh mesh, Material mat, Transform3D? at = null)
    {
        var mi = new MeshInstance3D { Mesh = mesh, MaterialOverride = mat, Transform = at ?? Transform3D.Identity };
        to.AddChild(mi);
        return mi;
    }

    public static MeshInstance3D Add(Node3D to, Build b, Material mat, bool tangents = false) => Add(to, b.Mesh(tangents), mat);

    public static Transform3D At(float x, float y, float z) => new(Basis.Identity, new Vector3(x, y, z));
    public static Transform3D At(Basis b, float x, float y, float z) => new(b, new Vector3(x, y, z));
    public static Basis Rot(float x, float y, float z) => new Basis(Vector3.Right, x) * new Basis(Vector3.Up, y) * new Basis(Vector3.Back, z);

    /// <summary>+Y turned to face the camera (+Z).</summary>
    public static readonly Basis Facing = new(Vector3.Right, Mathf.Pi / 2);

    public static SphereMesh Ball(float r) => new() { Radius = r, Height = r * 2, RadialSegments = 16, Rings = 8 };

    public static OmniLight3D Light(string c, float energy, float range, Vector3 at) => new()
    {
        LightColor = new Color(c), LightEnergy = energy, OmniRange = range, Position = at, ShadowEnabled = false,
    };

    /// <summary>A chain of links from one point to another.</summary>
    public static void Chain(Build b, Vector3 from, Vector3 to, float link, float wire)
    {
        var d = to - from;
        int n = Math.Max(2, (int)(d.Length() / (link * 1.6f)));
        var t = d.Normalized();
        var side = t.Cross(Mathf.Abs(t.Z) < 0.9f ? Vector3.Back : Vector3.Right).Normalized();
        for (int k = 0; k <= n; k++)
        {
            var p = from + d * ((float)k / n);
            var w = k % 2 == 0 ? side : t.Cross(side);
            Tube(b, Path(12, s => p + t * (link * Mathf.Cos(s * Mathf.Tau)) + w * (link * 0.55f * Mathf.Sin(s * Mathf.Tau)), true), wire, 5, true);
        }
    }

    /// <summary>A crescent: a disc less another, offset up (horns up).</summary>
    public static Vector2[] Crescent(float ro, float ri, float off, int n = 24)
    {
        float y = (ro * ro - ri * ri + off * off) / (2 * off), x = Mathf.Sqrt(Mathf.Max(0, ro * ro - y * y));
        float a0 = Mathf.Atan2(y, x), b0 = Mathf.Atan2(y - off, x);
        var l = new List<Vector2>();
        for (int i = 0; i <= n; i++) { float a = a0 - (Mathf.Pi + 2 * a0) * i / n; l.Add(new Vector2(ro * Mathf.Cos(a), ro * Mathf.Sin(a))); }
        for (int i = 1; i < n; i++) { float a = -Mathf.Pi - b0 + (Mathf.Pi + 2 * b0) * i / n; l.Add(new Vector2(ri * Mathf.Cos(a), off + ri * Mathf.Sin(a))); }
        return l.ToArray();
    }

    public static readonly Vector2[] Leaf = Pts(0, -0.12f, 0.04f, -0.06f, 0.045f, 0.02f, 0.025f, 0.09f, 0, 0.13f, -0.025f, 0.09f, -0.045f, 0.02f, -0.04f, -0.06f);

    /// <summary>A round-headed rivet, its head toward +Z.</summary>
    public static Build Rivet()
    {
        var b = new Build();
        Lathe(b, Pts(0.035f, 0, 0.03f, 0.02f, 0, 0.03f), 10, At(Facing, 0, 0, 0));
        return b;
    }

    /// <summary>An iron lantern: glass panes, a candle burning in it (the
    /// flame at the origin, 0.8 below the top of its ring), with a light of
    /// its own or not.</summary>
    public static Node3D Lantern(bool light)
    {
        var root = new Node3D();
        var turn = new Basis(Vector3.Up, Mathf.Pi / 4);
        var iron = new Build();
        Lathe(iron, Pts(0, -0.5f, 0.3f, -0.5f, 0.3f, -0.5f, 0.3f, -0.42f, 0.3f, -0.42f, 0.24f, -0.4f, 0, -0.4f), 4, At(turn, 0, 0, 0));
        Lathe(iron, Pts(0, 0.34f, 0.32f, 0.34f, 0.32f, 0.34f, 0.32f, 0.4f, 0.32f, 0.4f, 0.06f, 0.62f, 0.06f, 0.62f, 0.06f, 0.68f, 0, 0.7f), 4, At(turn, 0, 0, 0));
        var frame = iron.Faceted();
        foreach (float x in new[] { -0.19f, 0.19f })
            foreach (float z in new[] { -0.19f, 0.19f })
                Tube(frame, new List<Vector3> { new(x, -0.42f, z), new(x, 0.36f, z) }, 0.022f, 6);
        Tube(frame, Path(4, t => new Vector3(0.19f * Mathf.Sign(Mathf.Cos(t * Mathf.Tau + 0.1f)), 0, 0.19f * Mathf.Sign(Mathf.Sin(t * Mathf.Tau + 0.1f))), true), 0.012f, 5, true);
        Tube(frame, Circle(new Vector3(0, 0.8f, 0), 0.1f, Vector3.Right, Vector3.Up, 24), 0.018f, 6, true);
        Add(root, frame, Mat("#3a3836", 0.85f, 0.45f));
        Add(root, new BoxMesh { Size = new Vector3(0.36f, 0.74f, 0.36f) }, Glass("#1a140c", 0.14f), At(0, -0.03f, 0));
        Add(root, new CylinderMesh { TopRadius = 0.065f, BottomRadius = 0.07f, Height = 0.3f, RadialSegments = 16 }, Mat("#e8dcc0", 0, 0.6f), At(0, -0.25f, 0));
        var flame = new Build();
        Lathe(flame, Pts(0, -0.08f, 0.035f, -0.05f, 0.045f, 0, 0.03f, 0.06f, 0, 0.12f), 16, At(0, -0.02f, 0));
        Add(root, flame, Glow("#ffb050", 4));
        if (light) root.AddChild(Light("#ffa050", 2, 1.4f, new Vector3(0, 0, 0)));
        return root;
    }

    /* -------------------------------------------------------------- wands -- */

    /// <summary>An apprentice's wand: turned ash, a brass collar, a clear
    /// crystal held at its tip.</summary>
    public static Node3D Wand()
    {
        var root = new Node3D();
        var wood = new Build();
        Lathe(wood, Pts(0, -0.6f, 0.04f, -0.6f, 0.046f, -0.56f, 0.04f, -0.5f, 0.05f, -0.44f, 0.044f, -0.3f, 0.037f, -0.26f, 0.033f, 0.1f, 0.025f, 0.4f, 0.021f, 0.48f, 0, 0.5f), 16, textured: true);
        Add(root, wood, Grain("#8a6a48", "#4a3018"));
        var brass = new Build();
        Lathe(brass, Pts(0.044f, -0.31f, 0.049f, -0.29f, 0.049f, -0.26f, 0.04f, -0.24f), 16);
        for (int k = 0; k < 3; k++)
        {
            float a = k * Mathf.Tau / 3;
            var d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Tube(brass, new List<Vector3> { d * 0.02f + Vector3.Up * 0.46f, d * 0.045f + Vector3.Up * 0.53f, d * 0.02f + Vector3.Up * 0.6f }, 0.007f, 4);
        }
        Add(root, brass, Brass());
        var crystal = new Build();
        Lathe(crystal, Pts(0, 0, 0.05f, 0.04f, 0.045f, 0.14f, 0, 0.22f), 6, At(0, 0.47f, 0));
        Add(root, crystal.Faceted(), Gem("#7ac0ff", 1.1f));
        return root;
    }

    /// <summary>The Grave Tether: blackwood, a claw of bone at its head
    /// clutching a dark light, a coil of it winding down the shaft.</summary>
    public static Node3D DarkWand()
    {
        var root = new Node3D();
        var shaft = new Build();
        Tube(shaft, Path(24, t => new Vector3(0.02f * Mathf.Sin(t * 11), Mathf.Lerp(-0.62f, 0.4f, t), 0.015f * Mathf.Cos(t * 7))),
            t => Mathf.Lerp(0.04f, 0.022f, t) + 0.005f * Mathf.Sin(t * 70), 8);
        Add(root, shaft, Mat("#1e1a18", 0, 0.5f));
        var bone = new Build();
        for (int k = 0; k < 3; k++)
        {
            float a = k * Mathf.Tau / 3;
            var d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Tube(bone, new List<Vector3> { d * 0.02f + Vector3.Up * 0.38f, d * 0.08f + Vector3.Up * 0.45f, d * 0.075f + Vector3.Up * 0.55f, d * 0.03f + Vector3.Up * 0.6f }, t => 0.016f * (1 - 0.7f * t), 5);
        }
        Lathe(bone, Pts(0.03f, 0.34f, 0.04f, 0.36f, 0.035f, 0.4f, 0.02f, 0.41f), 12);
        Add(root, bone, Bone());
        Add(root, Ball(0.065f), Glow("#8a4aff", 1.6f, "#4a2a8a"), At(0, 0.5f, 0));
        var coil = new Build();
        Tube(coil, Path(60, t =>
        {
            float y = Mathf.Lerp(0.4f, -0.3f, t), a = t * Mathf.Tau * 3.5f, r = Mathf.Lerp(0.035f, 0.05f, t) + 0.01f;
            return new Vector3(r * Mathf.Cos(a), y, r * Mathf.Sin(a));
        }), t => 0.009f * (1 - t) + 0.002f, 4);
        Add(root, coil, Glow("#8a4aff", 0.9f, "#3a1a6a"));
        return root;
    }

}
