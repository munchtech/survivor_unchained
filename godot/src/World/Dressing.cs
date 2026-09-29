using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// What stands on the ground: the nature kit's trees, rocks and undergrowth
/// (one MultiMesh per part of a piece per 48 m bucket, as the web game
/// buckets them, so what is off screen is culled), the kit props placed one
/// by one, and the zone's lamps and fires.
/// </summary>
public static class Dressing
{
    /// Undergrowth: walked through, no shadow of its own.
    static readonly HashSet<string> Low = new() { "fern", "flowers", "plant", "clover", "mushroom", "pebble" };

    static readonly Dictionary<string, List<(Mesh Mesh, Transform3D Local)>> parts = new();

    /// <summary>The meshes of a kit piece, with where each sits in it.</summary>
    static List<(Mesh Mesh, Transform3D Local)> PartsOf(string kit, string piece)
    {
        var key = $"{kit}/{piece}";
        if (parts.TryGetValue(key, out var list)) return list;
        list = new();
        var scene = GD.Load<PackedScene>($"res://assets/env/{key}.gltf").Instantiate<Node3D>();
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D c3 ? at * c3.Transform : at;
                if (c is MeshInstance3D mi && mi.Mesh != null) list.Add((mi.Mesh, t));
                Walk(c, t);
            }
        }
        Walk(scene, Transform3D.Identity);
        scene.Free();
        parts[key] = list;
        return list;
    }

    static readonly Dictionary<string, Mesh> looked = new();

    /// <summary>A piece's mesh with its kind's look (KitLook): one copy per
    /// mesh and look, its surfaces' materials swapped.</summary>
    static Mesh Looked(Mesh mesh, KitLook.Look look)
    {
        var key = $"{mesh.GetInstanceId()}|{look}";
        if (looked.TryGetValue(key, out var m)) return m;
        m = (Mesh)mesh.Duplicate();
        for (int i = 0; i < m.GetSurfaceCount(); i++)
            if (m.SurfaceGetMaterial(i) is Material mat) m.SurfaceSetMaterial(i, KitLook.For(mat, look));
        looked[key] = m;
        return m;
    }

    public static Node3D Flora(ZoneData z)
    {
        var root = new Node3D { Name = "Flora" };
        foreach (var g in z.Flora)
        {
            var low = Low.Contains(g.Kind);
            foreach (var (mesh, local) in PartsOf("nature", g.Piece))
            {
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = Looked(mesh, g.Look), InstanceCount = g.At.Length };
                for (int i = 0; i < g.At.Length; i++) mm.SetInstanceTransform(i, g.At[i] * local);
                root.AddChild(new MultiMeshInstance3D
                {
                    Multimesh = mm,
                    Name = $"{g.Kind}:{g.Piece}",
                    CastShadow = low ? GeometryInstance3D.ShadowCastingSetting.Off : GeometryInstance3D.ShadowCastingSetting.On,
                    // Undergrowth goes before it gets small on screen.
                    VisibilityRangeEnd = low ? 70 : 0,
                });
            }
        }
        return root;
    }

    public static Node3D Props(ZoneData z)
    {
        var root = new Node3D { Name = "Props" };
        foreach (var (id, at) in z.Props)
        {
            var node = GD.Load<PackedScene>($"res://assets/env/{id}.gltf").Instantiate<Node3D>();
            node.Transform = at;
            root.AddChild(node);
        }
        return root;
    }

    /// <summary>Everything else the web game stands up in the zone (its
    /// camps, the Hunters' Blind, ruins, the KayKit props), exported where
    /// it stands (tools/godot/export_zone.mjs). Shadows from the big pieces
    /// only.</summary>
    public static Node3D Landmarks(ZoneData z)
    {
        var root = GD.Load<PackedScene>($"res://data/{z.Id}/landmarks.glb").Instantiate<Node3D>();
        root.Name = "Landmarks";
        void Walk(Node n)
        {
            foreach (var c in n.GetChildren())
            {
                if (c is MeshInstance3D m && m.GetAabb().Size.Length() < 0.8f)
                    m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                Walk(c);
            }
        }
        Walk(root);
        return root;
    }

    /// <summary>The zone's lamps and fires, lit ones only; flicker is the
    /// fire's own (Flicker).</summary>
    public static Node3D Lights(ZoneData z, Vector3 near)
    {
        var root = new Node3D { Name = "Lights" };
        foreach (var l in z.Lights)
        {
            if (!l.On) continue;
            // Shadows from the lights near the fight only: each is six
            // renders of everything around it.
            bool shadow = l.At.DistanceTo(near) < 30;
            var o = new OmniLight3D
            {
                Position = l.At,
                LightColor = l.Color,
                // The web game's candela-like intensities, into Godot's energy.
                LightEnergy = l.Intensity * 0.22f,
                OmniRange = l.Distance * 1.3f,
                OmniAttenuation = 1.4f,
                ShadowEnabled = shadow,
                LightVolumetricFogEnergy = 1.5f,
            };
            root.AddChild(o);
            if (l.Flicker > 0) o.AddChild(new Flicker(o, l.Flicker));
        }
        return root;
    }
}

/// <summary>A fire's light: never still, never steady.</summary>
public partial class Flicker : Node
{
    readonly OmniLight3D light;
    readonly float amount, base_;
    readonly float phase;
    double t;

    public Flicker() { light = null!; }
    public Flicker(OmniLight3D light, float amount)
    {
        this.light = light;
        this.amount = amount;
        base_ = light.LightEnergy;
        phase = (float)GD.RandRange(0, 100);
    }

    public override void _Process(double delta)
    {
        t += delta;
        float f = 1 + (Mathf.Sin((float)t * 8.3f + phase) * 0.5f + Mathf.Sin((float)t * 19.7f + phase * 1.7f) * 0.3f + Mathf.Sin((float)t * 3.1f + phase) * 0.2f) * amount;
        light.LightEnergy = base_ * f;
    }
}
