using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.View;

/// <summary>
/// A zone, stood up from its exported data (ZoneData): the ground, the
/// water, the flora, the kits' pieces, the landmarks, and what the web
/// game's ZoneKit keeps alive (src/world/zones/kit.ts): its lights, which
/// the runtime lights and puts out (a light's glowing bits and its fire go
/// with it), the fires, chimney smoke, moths round the lamps after dark,
/// and what only shows after dark.
///
/// The web game can afford a dozen lights and moves them to the lamps
/// nearest the survivor; here every lamp is a light of its own, faded out
/// with distance from the camera, and the big ones cast shadows near it.
/// </summary>
public partial class ZoneView : Node3D
{
    public readonly ZoneData Data;
    public readonly Landmarks Landmarks;
    readonly List<OmniLight3D> lights = new();
    readonly List<float> phases = new();
    readonly List<bool> lit = new();
    /// <summary>Every light's spec: the zone's, then those the runtime set down.</summary>
    readonly List<ZoneData.LightSpec> specs;
    readonly Dictionary<int, MeshInstance3D> flames = new();
    readonly Node3D lightRoot;
    readonly HashSet<string> stopped = new();
    readonly List<(int Light, Node3D Fire)> fires = new();
    readonly HashSet<string> fireGlow = new();
    readonly List<GpuParticles3D> chimneys = new();
    readonly List<(int Light, GpuParticles3D Moths)> moths = new();
    readonly ShaderMaterial ground;
    MultiMeshInstance3D? grass;
    readonly Node3D props;
    double time;
    public bool Night { get; private set; }

    /// <param name="grassAround">Where to grow the meadow (the web game grows
    /// it round the survivor as they go); null for none.</param>
    public ZoneView(ZoneData z, Vector2? grassAround = null, float grassRadius = 40)
    {
        Data = z;
        Name = $"Zone_{z.Id}";
        Perf.Lap("zone view", true);
        var g = Ground.Build(z);
        ground = (ShaderMaterial)g.Mesh.SurfaceGetMaterial(0);
        AddChild(g);
        AddChild(Water.Build(z));
        Perf.Lap("ground and water");
        AddChild(Dressing.Flora(z));
        Perf.Lap("flora");
        props = Dressing.Props(z);
        AddChild(props);
        Perf.Lap("props");
        Landmarks = new Landmarks(z);
        AddChild(Landmarks.Root);
        Perf.Lap("landmarks");
        if (grassAround is Vector2 at) GrowGrass(at, grassRadius);
        Perf.Lap("grass");

        var meta = z.Meta;
        specs = new List<ZoneData.LightSpec>(z.Lights);
        lightRoot = new Node3D { Name = "Lights" };
        AddChild(lightRoot);
        for (int i = 0; i < meta.Lights.Count; i++) MakeLight(z.Lights[i]);
        var fx = new Node3D { Name = "Fires" };
        AddChild(fx);
        foreach (var f in meta.Fires)
        {
            // The web game's ring of stones round it goes; the scanned pit takes its place.
            var fat = new Vector3((float)f.X, (float)f.Y, (float)f.Z);
            HideLandmarksNear(fat, 0.85f * (float)f.Size);
            var fire = Campfire.Build(fat, (float)f.Size, ring: true);
            fx.AddChild(fire);
            fires.Add((f.Light, fire));
            // The web game marks a fire's flame with a glowing ball; here the
            // fire has flames of its own, and the ball would only bloom white.
            if (f.Light >= 0 && f.Light < meta.Lights.Count)
                foreach (var glow in meta.Lights[f.Light].Glow) { fireGlow.Add(glow); if (Node(glow) is Node3D ball) ball.Visible = false; }
        }
        foreach (var c in meta.Chimneys)
        {
            var smoke = Campfire.ChimneySmoke();
            smoke.Position = new Vector3((float)c.X, (float)c.Y, (float)c.Z);
            fx.AddChild(smoke);
            chimneys.Add(smoke);
        }
        foreach (var m in meta.Moths)
        {
            var p = Campfire.Moths();
            p.Position = z.Lights[m].At;
            fx.AddChild(p);
            moths.Add((m, p));
        }
        for (int i = 0; i < lights.Count; i++) SetLit(i, z.Lights[i].On);
        SetNight(false);
    }

    OmniLight3D MakeLight(ZoneData.LightSpec l)
    {
        int i = lights.Count;
        phases.Add((float)(MathX.Hash1(i, 7) * 100));
        lit.Add(false);
        var light = new OmniLight3D
        {
            Name = $"Light{i}", Position = l.At, LightColor = l.Color,
            // three.js's intensity I lights to I/pi what Godot's energy E lights to E.
            LightEnergy = l.Intensity / Mathf.Pi,
            OmniRange = l.Distance > 0 ? l.Distance : 60, OmniAttenuation = 1.7f,
            // The big lights (fires, lanterns) cast shadows near the camera, at dusk and by night (Shadows).
            ShadowEnabled = CastsShadow(l), DistanceFadeShadow = 28, DistanceFadeEnabled = true,
            DistanceFadeBegin = 45, DistanceFadeLength = 20, LightVolumetricFogEnergy = 1.2f,
        };
        lights.Add(light);
        lightRoot.AddChild(light);
        return light;
    }

    /// <summary>A light set down now (a torch, a lamp lit in play), with a
    /// small flame that glows while it is on. Returns its index.</summary>
    public int AddLight(Vector3 at, Color color, float intensity, float distance, float flicker, float glowSize, Color glowColor)
    {
        var spec = new ZoneData.LightSpec(at, color, intensity, distance, flicker, true);
        int i = lights.Count;
        specs.Add(spec);
        MakeLight(spec);
        if (glowSize > 0)
        {
            var c = glowColor.SrgbToLinear() * 3;
            var flame = new MeshInstance3D
            {
                Mesh = new SphereMesh { Radius = glowSize, Height = glowSize * 2.4f, RadialSegments = 8, Rings = 4 },
                MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(c.R, c.G, c.B) },
                Position = at, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            };
            lightRoot.AddChild(flame);
            flames[i] = flame;
        }
        SetLit(i, true);
        return i;
    }

    /// <summary>A light that goes where something carries it.</summary>
    public void MoveLight(int light, Vector3 at)
    {
        specs[light] = specs[light] with { At = at };
        lights[light].Position = at;
        if (flames.TryGetValue(light, out var f)) f.Position = at;
    }

    /// <summary>A light turned up or down (a cinematic's grade: the camp's fire
    /// burned down to embers), its colour changed, its flicker slowed; 1 is as built.</summary>
    public void SetLevel(int light, float level, Color? color = null, float flickerRate = 1)
    {
        if (light < 0 || light >= lights.Count) return;
        levels[light] = (level, flickerRate);
        if (color is Color c) lights[light].LightColor = c;
        if (specs[light].Flicker <= 0) lights[light].LightEnergy = specs[light].Intensity / Mathf.Pi * level;
    }

    readonly Dictionary<int, (float Level, float Rate)> levels = new();

    /// <summary>A fire's flames scaled (0: embers only); its embers and smoke stay.</summary>
    public void SetFire(int light, float flames)
    {
        foreach (var (l, fire) in fires)
        {
            if (l != light || fire.GetNodeOrNull<Node3D>("Flames") is not Node3D f) continue;
            f.Visible = flames > 0.02f;
            f.Scale = new Vector3(Mathf.Sqrt(Mathf.Max(flames, 0.02f)), Mathf.Max(flames, 0.02f), Mathf.Sqrt(Mathf.Max(flames, 0.02f)));
        }
    }

    /// <summary>A turning piece (the pump's wheel) stops.</summary>
    public void Stop(string node) => stopped.Add(node);

    /// <summary>A node of the landmarks the runtime reaches for, by name.</summary>
    public Node3D? Node(string name) => Landmarks.Nodes.TryGetValue(name, out var n) ? n : null;

    public bool IsLit(int light) => lit[light];

    /// <summary>A light on or off, its glowing bits and its fire with it.</summary>
    public void SetLit(int light, bool on)
    {
        lit[light] = on;
        lights[light].Visible = on;
        if (flames.TryGetValue(light, out var flame)) flame.Visible = on;
        if (light < Data.Meta.Lights.Count)
            foreach (var g in Data.Meta.Lights[light].Glow) if (Node(g) is Node3D n) n.Visible = on && !fireGlow.Contains(g);
        foreach (var (l, fire) in fires) if (l == light) Burn(fire, on);
        foreach (var (l, p) in moths) if (l == light) p.Emitting = on && Night;
    }

    static void Burn(Node3D fire, bool on)
    {
        fire.Visible = on;
        foreach (var c in fire.GetChildren()) if (c is GpuParticles3D p) p.Emitting = on;
    }

    /// <summary>After dark or not: night-only pieces show, moths come to the
    /// lamps, chimney smoke goes dark.</summary>
    public void SetNight(bool on)
    {
        Night = on;
        foreach (var n in Data.Meta.NightNodes) if (Node(n) is Node3D node) node.Visible = on;
        foreach (var (l, p) in moths) p.Emitting = on && lit[l];
        foreach (var c in chimneys) Campfire.ChimneyLook(c, on);
        Shadows();
    }

    bool dusk, lampShadows = SurvivorUnchained.Play.Graphics.Current.LampShadows;

    /// <summary>Whether it is dusk (the game's clock): the lamps cast shadows then, as by night.</summary>
    public void SetDusk(bool on)
    {
        dusk = on;
        Shadows();
    }

    /// <summary>The big lamps and fires cast shadows only at dusk and by night
    /// (the owner's call): by day their light is faint beside the sun's, and
    /// in town their shadows were two thirds of every frame's shadow draws.
    /// Never at the lowest quality.</summary>
    bool CastsShadow(ZoneData.LightSpec l) => l.Intensity >= 8 && lampShadows && (Night || dusk);

    void Shadows()
    {
        for (int i = 0; i < lights.Count; i++)
        {
            bool cast = CastsShadow(specs[i]);
            if (lights[i].ShadowEnabled != cast) lights[i].ShadowEnabled = cast;
        }
    }

    /// <summary>How far the blight has drawn back (0..1): the ground's veins
    /// and the grass (the Verge's water is the runtime's).</summary>
    public void SetHeal(float heal)
    {
        healed = heal;
        ground.SetShaderParameter("heal", heal);
        grass?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/heal", heal);
    }

    float healed;

    /// <summary>The kit pieces of a kind within r of a point, taken away in
    /// play (the strongbox carried off, the crates rolled into the stream):
    /// each one's instance collapsed to nothing where it stood.</summary>
    public void HideProps(string id, float x, float z, float r)
    {
        foreach (var mmi in props.GetChildren().OfType<MultiMeshInstance3D>())
        {
            if (!mmi.HasMeta("prop") || mmi.GetMeta("prop").AsString() != id) continue;
            var at = mmi.GetMeta("at").AsGodotArray<Vector3>();
            for (int i = 0; i < at.Count; i++)
                if (new Vector2(at[i].X - x, at[i].Z - z).Length() < r)
                    mmi.Multimesh.SetInstanceTransform(i, new Transform3D(new Basis(Vector3.Zero, Vector3.Zero, Vector3.Zero), at[i]));
        }
    }

    /// <summary>Hide the low landmark pieces within `radius` of a point on
    /// the ground (what a fire's scanned pit replaces).</summary>
    void HideLandmarksNear(Vector3 at, float radius)
    {
        foreach (var n in Landmarks.Root.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D mi) continue;
            // Not yet in the tree: its place relative to the landmarks' root (at the origin).
            var t = Transform3D.Identity;
            for (Node? p = mi; p != null && p != Landmarks.Root; p = p.GetParent()) if (p is Node3D p3) t = p3.Transform * t;
            var box = t * mi.GetAabb();
            var c = box.GetCenter();
            // Only what lies on the ground (stones, logs), not what hangs over it (a pot).
            if (new Vector2(c.X - at.X, c.Z - at.Z).Length() < radius && box.Size.Y < 0.7f && box.Size.X < radius * 2.2f && box.Position.Y < at.Y + 0.25f) mi.Visible = false;
        }
    }

    /// <summary>The meadow round a place, built once; it follows `at` (FollowGrass).</summary>
    public void GrowGrass(Vector2 at, float radius = 40)
    {
        grass?.QueueFree();
        grass = Grass.Build(Data, at, radius, grassCell);
        grassAt = at;
        grassRadius = radius;
        AddChild(grass);
    }

    float grassCell = 0.3f, grassRadius = 40;
    Vector2 grassAt;

    /// <summary>How far apart the meadow's tufts are (the picture's quality): regrown if it changed.</summary>
    public void GrassCell(float cell)
    {
        if (Mathf.IsEqualApprox(cell, grassCell)) return;
        grassCell = cell;
        if (grass == null) return;
        var centre = (Vector2)grass.Multimesh.Mesh.SurfaceGetMaterial(0).Get("shader_parameter/centre");
        GrowGrass(grassAt, grassRadius);
        FollowGrass(centre);
        if (healed != 0) SetHeal(healed);
    }

    /// <summary>Whether the big lamps may cast shadows (the picture's quality).</summary>
    public void LampShadows(bool on)
    {
        lampShadows = on;
        Shadows();
    }

    /// <summary>The meadow's middle, every frame: the shader moves the tufts.</summary>
    public void FollowGrass(Vector2 at) => grass?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/centre", at);

    public override void _Process(double delta)
    {
        time += delta;
        float t = (float)time;
        // The pump's wheel turns while the pump runs.
        if (!stopped.Contains("pump_wheel") && Node("pump_wheel") is Node3D wheel) wheel.RotateObjectLocal(Vector3.Right, (float)delta * 0.8f);
        // Every lit light's own flicker (the web game's formula).
        for (int i = 0; i < lights.Count; i++)
        {
            if (!lit[i]) continue;
            var l = specs[i];
            if (l.Flicker <= 0) continue;
            float ph = phases[i];
            var (level, rate) = levels.TryGetValue(i, out var lv) ? lv : (1f, 1f);
            float ft = t * rate;
            float f = 1 + (Mathf.Sin(ft * 8.3f + ph) * 0.5f + Mathf.Sin(ft * 19.7f + ph * 1.7f) * 0.3f + Mathf.Sin(ft * 3.1f + ph) * 0.2f) * l.Flicker;
            lights[i].LightEnergy = l.Intensity / Mathf.Pi * f * level;
            lights[i].Position = l.At + new Vector3(0, Mathf.Sin(t * 11 + ph) * 0.03f * l.Flicker, 0);
        }
    }
}
