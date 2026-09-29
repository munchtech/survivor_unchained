using System.Collections.Generic;
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
    readonly OmniLight3D[] lights;
    readonly float[] phases;
    readonly bool[] lit;
    readonly List<(int Light, Node3D Fire)> fires = new();
    readonly List<GpuParticles3D> chimneys = new();
    readonly List<(int Light, GpuParticles3D Moths)> moths = new();
    readonly ShaderMaterial ground;
    MultiMeshInstance3D? grass;
    double time;
    public bool Night { get; private set; }

    /// <param name="grassAround">Where to grow the meadow (the web game grows
    /// it round the survivor as they go); null for none.</param>
    public ZoneView(ZoneData z, Vector2? grassAround = null, float grassRadius = 26)
    {
        Data = z;
        Name = $"Zone_{z.Id}";
        var g = Ground.Build(z);
        ground = (ShaderMaterial)g.Mesh.SurfaceGetMaterial(0);
        AddChild(g);
        AddChild(Water.Build(z));
        AddChild(Dressing.Flora(z));
        AddChild(Dressing.Props(z));
        Landmarks = new Landmarks(z);
        AddChild(Landmarks.Root);
        if (grassAround is Vector2 at) GrowGrass(at, grassRadius);

        var meta = z.Meta;
        lights = new OmniLight3D[meta.Lights.Count];
        phases = new float[meta.Lights.Count];
        lit = new bool[meta.Lights.Count];
        var lightRoot = new Node3D { Name = "Lights" };
        AddChild(lightRoot);
        for (int i = 0; i < meta.Lights.Count; i++)
        {
            var l = z.Lights[i];
            phases[i] = (float)(MathX.Hash1(i, 7) * 100);
            lights[i] = new OmniLight3D
            {
                Name = $"Light{i}", Position = l.At, LightColor = l.Color,
                // three.js's intensity I lights to I/pi what Godot's energy E lights to E.
                LightEnergy = l.Intensity / Mathf.Pi,
                OmniRange = l.Distance > 0 ? l.Distance : 60, OmniAttenuation = 1.7f,
                // The big lights (fires, lanterns) cast shadows near the camera.
                ShadowEnabled = l.Intensity >= 8, DistanceFadeShadow = 28, DistanceFadeEnabled = true,
                DistanceFadeBegin = 45, DistanceFadeLength = 20, LightVolumetricFogEnergy = 1.2f,
            };
            lightRoot.AddChild(lights[i]);
        }
        var fx = new Node3D { Name = "Fires" };
        AddChild(fx);
        foreach (var f in meta.Fires)
        {
            var fire = Campfire.Build(new Vector3((float)f.X, (float)f.Y, (float)f.Z), (float)f.Size, ring: false);
            fx.AddChild(fire);
            fires.Add((f.Light, fire));
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
        for (int i = 0; i < lights.Length; i++) SetLit(i, z.Lights[i].On);
        SetNight(false);
    }

    /// <summary>A node of the landmarks the runtime reaches for, by name.</summary>
    public Node3D? Node(string name) => Landmarks.Nodes.TryGetValue(name, out var n) ? n : null;

    public bool IsLit(int light) => lit[light];

    /// <summary>A light on or off, its glowing bits and its fire with it.</summary>
    public void SetLit(int light, bool on)
    {
        lit[light] = on;
        lights[light].Visible = on;
        foreach (var g in Data.Meta.Lights[light].Glow) if (Node(g) is Node3D n) n.Visible = on;
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
    }

    /// <summary>How far the blight has drawn back (0..1): the ground's veins
    /// and the grass (the Verge's water is the runtime's).</summary>
    public void SetHeal(float heal)
    {
        ground.SetShaderParameter("heal", heal);
        grass?.Multimesh.Mesh.SurfaceGetMaterial(0)?.Set("shader_parameter/heal", heal);
    }

    /// <summary>The meadow round a place (again, as the survivor moves on).</summary>
    public void GrowGrass(Vector2 at, float radius = 26)
    {
        grass?.QueueFree();
        grass = Grass.Build(Data, at, radius);
        AddChild(grass);
    }

    public override void _Process(double delta)
    {
        time += delta;
        float t = (float)time;
        // Every lit light's own flicker (the web game's formula).
        for (int i = 0; i < lights.Length; i++)
        {
            if (!lit[i]) continue;
            var l = Data.Lights[i];
            if (l.Flicker <= 0) continue;
            float ph = phases[i];
            float f = 1 + (Mathf.Sin(t * 8.3f + ph) * 0.5f + Mathf.Sin(t * 19.7f + ph * 1.7f) * 0.3f + Mathf.Sin(t * 3.1f + ph) * 0.2f) * l.Flicker;
            lights[i].LightEnergy = l.Intensity / Mathf.Pi * f;
            lights[i].Position = l.At + new Vector3(0, Mathf.Sin(t * 11 + ph) * 0.03f * l.Flicker, 0);
        }
    }
}
