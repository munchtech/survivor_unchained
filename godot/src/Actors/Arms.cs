using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Weapons worth holding (res://assets/weapons: Sketchfab CC-BY/CC0, see
/// public/assets/CREDITS.md), each turned and scaled to one convention so
/// any hand can take any of them, as the web game does (src/render/arms.ts):
/// +Y the shaft from the grip out, the grip at the origin; +X the blade's
/// width; +Z its thickness. The model's principal axes say which way it
/// lies; what they cannot (which end is the grip, where the hand goes, its
/// length in life) is written per weapon.
/// </summary>
public static class Arms
{
    /// <summary>A weapon: its file (and the node in it, where a file holds
    /// several), its length in life, where along it the hand grips (0 the
    /// butt, 1 the tip); held pistol-fashion (a crossbow) or not.</summary>
    public sealed record Spec(string File, float Length, float Grip, bool Flip = false, float Roll = 0, string? Node = null, bool Pistol = false);

    public static readonly Dictionary<string, Spec> All = new()
    {
        ["chevalier_sword"] = new("chevalier_sword", 1.0f, 0.1f),
        ["viking_sword"] = new("viking_sword", 0.92f, 0.13f),
        ["longsword"] = new("longsword", 1.05f, 0.22f, Flip: true),
        ["zweihander"] = new("zweihander", 1.6f, 0.2f),
        ["mace"] = new("mace", 0.75f, 0.12f),
        ["viking_axe"] = new("viking_axe", 0.8f, 0.15f, Roll: Mathf.Pi),
        ["snake_axe"] = new("snake_axe", 1.3f, 0.22f),
        ["mage_staff"] = new("mage_staff", 1.75f, 0.45f),
        ["short_staff"] = new("mage_staff", 1.1f, 0.3f),
        ["crossbow"] = new("crossbow", 0.85f, 0.3f, Pistol: true),
        ["shield_round"] = new("shield_round", 0.66f, 0.5f),
        ["daggers"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004"),
        ["dagger_b"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004_01"),
    };

    /// <summary>A weapon, normalised (a new node each call).</summary>
    public static Node3D Make(string id)
    {
        var spec = All[id];
        var model = GD.Load<PackedScene>($"res://assets/weapons/{spec.File}.glb").Instantiate<Node3D>();
        if (spec.Node != null)
        {
            // One weapon of several in the file: the rest go (the meshes
            // not under the node named, however deep).
            void Keep(Node n, bool wanted)
            {
                foreach (var c in n.GetChildren())
                {
                    bool mine = wanted || c.Name == spec.Node;
                    if (c is MeshInstance3D m && !mine) { m.QueueFree(); m.GetParent().RemoveChild(m); continue; }
                    Keep(c, mine);
                }
            }
            Keep(model, false);
        }
        var pts = new List<Vector3>();
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D c3 ? at * c3.Transform : at;
                if (c is MeshInstance3D mi && mi.Mesh != null)
                    for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                        foreach (var v in (Vector3[])mi.Mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Vertex]) pts.Add(t * v);
                Walk(c, t);
            }
        }
        Walk(model, Transform3D.Identity);
        var (axes, mean) = Principal(pts);
        var (lng, mid) = (axes[0], axes[1]);
        if (spec.Flip) lng = -lng;
        var shrt = mid.Cross(lng);
        // Extent along each new axis, and its middle.
        var basis = new[] { mid, lng, shrt };
        var lo = new float[] { float.MaxValue, float.MaxValue, float.MaxValue };
        var hi = new float[] { float.MinValue, float.MinValue, float.MinValue };
        foreach (var p in pts)
            for (int a = 0; a < 3; a++) { var d = p.Dot(basis[a]); lo[a] = Mathf.Min(lo[a], d); hi[a] = Mathf.Max(hi[a], d); }
        var centre = Vector3.Zero;
        for (int a = 0; a < 3; a++) centre += basis[a] * (lo[a] + hi[a]) / 2;
        // Rows of the turn: model axes -> (X = mid, Y = long, Z = short).
        var turn = new Basis(mid, lng, shrt).Transposed();
        if (spec.Roll != 0) turn = new Basis(Vector3.Up, spec.Roll) * turn;
        float k = spec.Length / (hi[1] - lo[1]);
        var inner = new Node3D { Name = "inner" };
        model.Position = -centre;
        inner.AddChild(model);
        inner.Basis = turn.Scaled(Vector3.One * k);
        inner.Position = new Vector3(0, spec.Length * (0.5f - spec.Grip), 0);
        var holder = new Node3D { Name = $"arm:{id}" };
        holder.AddChild(inner);
        return holder;
    }

    /// <summary>Principal axes of a point cloud, longest spread first, each
    /// signed to agree with the file axis it lies nearest.</summary>
    static (Vector3[] Axes, Vector3 Mean) Principal(List<Vector3> pts)
    {
        var mean = Vector3.Zero;
        foreach (var p in pts) mean += p / pts.Count;
        var c = new double[3, 3];
        foreach (var p in pts)
        {
            var d = p - mean;
            double[] v = { d.X, d.Y, d.Z };
            for (int a = 0; a < 3; a++) for (int b = 0; b < 3; b++) c[a, b] += v[a] * v[b] / pts.Count;
        }
        var (values, vectors) = Jacobi(c);
        var order = new[] { 0, 1, 2 };
        Array.Sort(order, (a, b) => values[b].CompareTo(values[a]));
        var axes = new Vector3[3];
        for (int i = 0; i < 3; i++)
        {
            int k = order[i];
            var e = new Vector3((float)vectors[0, k], (float)vectors[1, k], (float)vectors[2, k]).Normalized();
            var big = new[] { Mathf.Abs(e.X), Mathf.Abs(e.Y), Mathf.Abs(e.Z) };
            int at = Array.IndexOf(big, Mathf.Max(big[0], Mathf.Max(big[1], big[2])));
            if (e[at] < 0) e = -e;
            axes[i] = e;
        }
        return (axes, mean);
    }

    /// <summary>Eigen-decomposition of a symmetric 3x3 (cyclic Jacobi);
    /// eigenvectors in the columns.</summary>
    static (double[] Values, double[,] Vectors) Jacobi(double[,] a0)
    {
        var a = (double[,])a0.Clone();
        var vec = new double[,] { { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 } };
        var pairs = new[] { (0, 1), (0, 2), (1, 2) };
        for (int sweep = 0; sweep < 32; sweep++)
        {
            if (a[0, 1] * a[0, 1] + a[0, 2] * a[0, 2] + a[1, 2] * a[1, 2] < 1e-18) break;
            foreach (var (p, q) in pairs)
            {
                if (Math.Abs(a[p, q]) < 1e-14) continue;
                double theta = (a[q, q] - a[p, p]) / (2 * a[p, q]);
                double t = Math.Sign(theta == 0 ? 1 : theta) / (Math.Abs(theta) + Math.Sqrt(theta * theta + 1));
                double cs = 1 / Math.Sqrt(t * t + 1), sn = t * cs;
                for (int k = 0; k < 3; k++) { double akp = a[k, p], akq = a[k, q]; a[k, p] = cs * akp - sn * akq; a[k, q] = sn * akp + cs * akq; }
                for (int k = 0; k < 3; k++) { double apk = a[p, k], aqk = a[q, k]; a[p, k] = cs * apk - sn * aqk; a[q, k] = sn * apk + cs * aqk; }
                for (int k = 0; k < 3; k++) { double vkp = vec[k, p], vkq = vec[k, q]; vec[k, p] = cs * vkp - sn * vkq; vec[k, q] = sn * vkp + cs * vkq; }
            }
        }
        return (new[] { a[0, 0], a[1, 1], a[2, 2] }, vec);
    }

    /// <summary>Mount a weapon in a person's hand (or a shield on the
    /// forearm), the way the web game's sockets hold them: in the hand's
    /// space the fingers run +Y and the thumb side is +Z.</summary>
    public static Node3D Hold(People.Person person, string id, string bone = "hand_r")
    {
        var att = new BoneAttachment3D { BoneName = bone };
        person.Skeleton.AddChild(att);
        var mount = new Node3D { Name = $"mount:{bone}" };
        att.AddChild(mount);
        bool forearm = bone.StartsWith("lowerarm");
        var x = new Vector3(0, 1, 0);
        var y = forearm ? new Vector3(0, 0, -1) : new Vector3(0, 0, 1);
        mount.Basis = new Basis(x, y, x.Cross(y));
        mount.Position = forearm ? new Vector3(0, 0.14f, 0) : new Vector3(-0.025f, 0.075f, 0);
        var w = Make(id);
        if (All[id].Pistol)
        {
            // Held pistol-fashion: the stock along the fingers, its top out
            // of the thumb side, sitting on the fist rather than through it.
            w.Basis = new Basis(new Vector3(0, 0, 1), new Vector3(1, 0, 0), new Vector3(0, 1, 0));
            w.Position = new Vector3(0, 0.05f, 0);
        }
        mount.AddChild(w);
        return mount;
    }
}
