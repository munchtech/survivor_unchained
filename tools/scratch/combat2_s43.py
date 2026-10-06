W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zone.cs": [
        ("""    IOrb Orb(string color, double size);""",
         """    IOrb Orb(string color, double size);
    /// <summary>The Kindling's ember-core: a lump of raw ember, split by glowing fissures that widen
    /// as it is broken (Light: 0 whole, 1 nearly broken). A plain orb where nothing better is drawn.</summary>
    IOrb EmberCore(double size) => Orb("#ff7a2a", size * 0.45);"""),
    ],
    W + "src/Game/WorldScene.cs": [
        ("""    public IOrb Orb(string color, double size)
    {""", """    public IOrb EmberCore(double size)
    {
        var o = new EmberCoreView(size);
        AddChild(o);
        return o;
    }

    public IOrb Orb(string color, double size)
    {"""),
    ],
    W + "src/Actors/BossViews.cs": [
        ("""public partial class OrbView : Node3D, IOrb
{""", """/// <summary>The Kindling's ember-core (shaders/ember_core.gdshader): a dark crust knobbled out of a
/// sphere, its fissures glowing from inside and widening as it is broken, its own warm light.</summary>
public partial class EmberCoreView : Node3D, IOrb
{
    readonly MeshInstance3D lump;
    readonly ShaderMaterial mat;
    readonly OmniLight3D light;

    public EmberCoreView(double size)
    {
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ember_core.gdshader") };
        lump = new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = (float)size, Height = (float)size * 2, RadialSegments = 40, Rings = 20 },
            MaterialOverride = mat,
        };
        AddChild(lump);
        light = new OmniLight3D { LightColor = new Color("#ff7a2a"), OmniRange = 9, OmniAttenuation = 1.6f, LightEnergy = 1.4f, ShadowEnabled = false };
        light.Position = new Vector3(0, (float)size * 1.2f, 0);
        AddChild(light);
        Visible = false;
    }

    bool IOrb.Visible { get => Visible; set => Visible = value; }

    public void Place(double x, double y, double z, double spin, double scale)
    {
        Position = new Vector3((float)x, (float)y, (float)z);
        lump.Rotation = new Vector3(0, (float)spin, 0);
        lump.Scale = Vector3.One * (float)scale;
    }

    public double Light
    {
        set
        {
            float heat = Mathf.Clamp((float)value, 0, 1);
            mat.SetShaderParameter("heat", heat);
            light.LightEnergy = 1.2f + 3.5f * heat;
        }
    }

    void IOrb.Dispose() => QueueFree();
}

public partial class OrbView : Node3D, IOrb
{"""),
    ],
    W + "logic/Play/Zones/ArenaRun.cs": [
        ("""        coreOrb = G.Look.Orb("#ff7a2a", 1.5);""", """        coreOrb = G.Look.EmberCore(0.95);"""),
        ("""            coreOrb.Place(core.X, 0.7 + 0.08 * Math.Sin(ct * 2.4), core.Z, ct * 0.4, 1 + 0.06 * Math.Sin(ct * 5.1) + 0.25 * hurt);
            coreOrb.Light = 1.2 + 0.4 * Math.Sin(ct * 5.1) + 1.4 * hurt;""",
         """            coreOrb.Place(core.X, G.Look.HeightAt(core.X, core.Z) + 0.45, core.Z, ct * 0.15, 1 + 0.03 * Math.Sin(ct * 5.1) + 0.12 * hurt);
            coreOrb.Light = Math.Min(1, hurt + 0.08 * Math.Sin(ct * 5.1));"""),
    ],
}
