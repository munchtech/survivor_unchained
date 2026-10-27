using System;
using System.Globalization;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>
/// --prop SPEC[;SPEC...], SPEC = PATH@dx,dz[,yaw[,height]]: a model stood in the place, for pictures. PATH is a res://
/// .glb/.gltf, or an absolute .glb read at run time (no import needed). Placed dx,dz metres from her start, on the
/// ground there, yaw in degrees; height (metres) scales it uniformly so its box is that tall. Its meshes cast shadows.
/// </summary>
public partial class Game
{
    void PropShot()
    {
        if (Args.Get("prop") is not string arg || scene == null || Battle?.Player is not { } pl) return;
        foreach (var spec in arg.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            int at = spec.LastIndexOf('@');
            if (at <= 0) { GD.PushWarning($"prop: bad spec {spec}"); continue; }
            var path = spec[..at];
            var nums = spec[(at + 1)..].Split(',');
            double N(int i, double d) => i < nums.Length && double.TryParse(nums[i], NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : d;
            double x = pl.X + N(0, 0), z = pl.Z + N(1, 0), yaw = N(2, 0), want = N(3, 0);
            Node? root = null;
            if (path.StartsWith("res://")) root = GD.Load<PackedScene>(path)?.Instantiate();
            else
            {
                var doc = new GltfDocument(); var state = new GltfState();
                if (doc.AppendFromFile(path, state) == Error.Ok) root = doc.GenerateScene(state);
            }
            if (root is not Node3D n) { GD.PushWarning($"prop: could not load {path}"); root?.Free(); continue; }
            var box = PropBox(n, Transform3D.Identity);
            double s = want > 0 && box.Size.Y > 1e-4 ? want / box.Size.Y : 1;
            n.Name = "ShotProp";
            n.Scale = Vector3.One * (float)s;
            n.RotationDegrees = new Vector3(0, (float)yaw, 0);
            scene.AddChild(n);
            // (feet on the ground: the box's lowest point, scaled, sits at the ground height)
            n.Position = new Vector3((float)x, (float)scene.HeightAt(x, z) - (float)(box.Position.Y * s), (float)z);
            SetShadows(n);
            GD.Print($"prop: {path} at ({x:0.##},{z:0.##}) yaw {yaw:0.##} scale {s:0.###} aabb {box.Size.X * s:0.##}x{box.Size.Y * s:0.##}x{box.Size.Z * s:0.##}");
        }
    }

    static Aabb PropBox(Node n, Transform3D to)
    {
        Aabb box = default; bool any = false;
        void Walk(Node c, Transform3D t)
        {
            if (c is Node3D n3) t *= n3.Transform;
            if (c is MeshInstance3D mi && mi.Mesh != null)
            {
                var b = t * mi.Mesh.GetAabb();
                box = any ? box.Merge(b) : b; any = true;
            }
            foreach (var k in c.GetChildren()) Walk(k, t);
        }
        // (the root's own transform is left out: the box is in its local space, before scale and yaw)
        foreach (var k in n.GetChildren()) Walk(k, to);
        return box;
    }

    static void SetShadows(Node n)
    {
        if (n is GeometryInstance3D g) g.CastShadow = GeometryInstance3D.ShadowCastingSetting.On;
        foreach (var k in n.GetChildren()) SetShadows(k);
    }
}
