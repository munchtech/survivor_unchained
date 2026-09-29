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
    static Mesh Looked(Mesh mesh, KitLook.Look look, bool foot = false)
    {
        var key = $"{mesh.GetInstanceId()}|{look}|{foot}";
        if (looked.TryGetValue(key, out var m)) return m;
        m = (Mesh)mesh.Duplicate();
        for (int i = 0; i < m.GetSurfaceCount(); i++)
            if (m.SurfaceGetMaterial(i) is Material mat) m.SurfaceSetMaterial(i, KitLook.For(mat, look, foot));
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

    /// <summary>The world kits' pieces, placed one by one in the web game
    /// (the houses and walls too, which it merges): here each piece's parts
    /// as MultiMeshes, one per 32 m bucket so what is off screen is culled.</summary>
    public static Node3D Props(ZoneData z)
    {
        var root = new Node3D { Name = "Props" };
        var groups = new Dictionary<(string, int, int), List<Transform3D>>();
        foreach (var (id, at) in z.Props)
        {
            var k = (id, Mathf.FloorToInt(at.Origin.X / 32), Mathf.FloorToInt(at.Origin.Z / 32));
            if (!groups.TryGetValue(k, out var list)) groups[k] = list = new();
            list.Add(at);
        }
        foreach (var ((id, _, _), list) in groups)
        {
            int slash = id.IndexOf('/');
            string kit = id[..slash], piece = id[(slash + 1)..];
            bool foot = kit is "village" or "custom";
            foreach (var (mesh, local) in PartsOf(kit, piece))
            {
                var mm = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, Mesh = Looked(mesh, KitLook.Look.Plain, foot), InstanceCount = list.Count };
                for (int i = 0; i < list.Count; i++) mm.SetInstanceTransform(i, list[i] * local);
                root.AddChild(new MultiMeshInstance3D { Multimesh = mm, Name = piece });
            }
        }
        return root;
    }

}
