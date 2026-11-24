using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (the tester lane, 24 Nov) Folds a code-built prop's static pieces into one mesh, one surface per material. On D3D12 every
/// mesh surface's vertex, attribute and index buffers are each placed at 64 KB however small they are (measured: 2000
/// one-triangle meshes took 125 MB of video memory, 64 KB apiece, while the buffer counter said 36 B each), so a prop built
/// from 65 boxes and cylinders cost about 12 MB where its bytes are a few KB; folded, it is 5 surfaces. It is also 5 draws
/// instead of 65.
/// What folds: every MeshInstance3D under `root` with no children of its own, no script, a mesh of triangles, the root's
/// layers and shadow setting, and one material per surface (its override, else its surface's). Each lands in its material's
/// surface, moved by its transform relative to the root. What stays: anything else (a light, a piece with its own script,
/// a piece something will move or find by name: do not fold those, keep them out of `root` or pass them in `keep`).
/// Empty Node3Ds left behind are removed. Call it on the prop before it enters the tree.
/// </summary>
public static class MeshMerge
{
    /// <summary>Folds `root`'s static pieces (see the class); returns the new MeshInstance3D, or null if under two folded.</summary>
    public static MeshInstance3D? Fold(Node3D root, ICollection<Node>? keep = null)
    {
        var pieces = new List<(MeshInstance3D Mi, Transform3D T)>();
        Walk(root, Transform3D.Identity, pieces, keep, root);
        if (pieces.Count < 2) return null;
        var byMat = new Dictionary<Material, SurfaceTool>();
        var order = new List<Material>();
        foreach (var (mi, t) in pieces)
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var mat = mi.GetActiveMaterial(s);
                if (!byMat.TryGetValue(mat, out var st))
                {
                    st = new SurfaceTool();
                    st.Begin(Mesh.PrimitiveType.Triangles);
                    byMat[mat] = st;
                    order.Add(mat);
                }
                // AppendFrom carries only the incoming surface's indices: a non-indexed surface (SurfaceTool built without
                // Index(), like MineTub's hull) beside indexed ones would add its vertices and none of its triangles, so index it first.
                if (mi.Mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil)
                {
                    var one = new SurfaceTool();
                    one.CreateFrom(mi.Mesh, s);
                    one.Index();
                    st.AppendFrom(one.Commit(), 0, t);
                }
                else st.AppendFrom(mi.Mesh, s, t);
            }
        var mesh = new ArrayMesh();
        foreach (var mat in order)
        {
            byMat[mat].Commit(mesh);
            mesh.SurfaceSetMaterial(mesh.GetSurfaceCount() - 1, mat);
        }
        var merged = new MeshInstance3D { Name = "Folded", Mesh = mesh, CastShadow = pieces[0].Mi.CastShadow, Layers = pieces[0].Mi.Layers };
        foreach (var (mi, _) in pieces) { mi.GetParent().RemoveChild(mi); mi.Free(); }
        Prune(root);
        root.AddChild(merged);
        return merged;
    }

    static void Walk(Node n, Transform3D t, List<(MeshInstance3D, Transform3D)> into, ICollection<Node>? keep, Node3D root)
    {
        foreach (var c in n.GetChildren())
        {
            if (keep != null && keep.Contains(c)) continue;
            if (c is not Node3D c3) continue;
            var ct = t * c3.Transform;
            if (c is MeshInstance3D mi && Foldable(mi, root, into)) into.Add((mi, ct));
            else Walk(c, ct, into, keep, root);
        }
    }

    static bool Foldable(MeshInstance3D mi, Node3D root, List<(MeshInstance3D Mi, Transform3D)> into)
    {
        if (mi.Mesh == null || mi.GetChildCount() > 0 || mi.GetScript().VariantType != Variant.Type.Nil || !mi.Visible) return false;
        if (into.Count > 0 && (mi.CastShadow != into[0].Mi.CastShadow || mi.Layers != into[0].Mi.Layers)) return false;
        if (mi.Mesh is not (PrimitiveMesh or ArrayMesh)) return false;
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            if (mi.Mesh is ArrayMesh am && am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles || mi.GetActiveMaterial(s) == null) return false;
        return true;
    }

    static bool Prune(Node n)
    {
        bool empty = true;
        foreach (var c in n.GetChildren())
            if (Prune(c) && c.GetType() == typeof(Node3D) && c.GetScript().VariantType == Variant.Type.Nil) { n.RemoveChild(c); c.Free(); }
            else empty = false;
        return empty;
    }

    /// <summary>(dev, --mesh-merge-check) The same prop built unfolded and folded: each material's triangles, in the root's
    /// space, sorted, compared (positions, normals, UVs). Returns the line to print: how many triangles each side and the
    /// largest difference.</summary>
    public static string Check(Node3D plain, Node3D folded)
    {
        var a = Soup(plain); var b = Soup(folded);
        int ta = a.Values.Sum(v => v.Count), tb = b.Values.Sum(v => v.Count);
        float worst = 0;
        bool same = a.Count == b.Count;
        foreach (var (mat, la) in a)
        {
            if (!b.TryGetValue(mat, out var lb) || la.Count != lb.Count) { same = false; continue; }
            for (int i = 0; i < la.Count; i++)
                for (int k = 0; k < la[i].Length; k++) worst = Math.Max(worst, Math.Abs(la[i][k] - lb[i][k]));
        }
        string per = string.Join(", ", a.Select(kv => $"{kv.Value.Count}/{(b.TryGetValue(kv.Key, out var lb) ? lb.Count : -1)}"));
        plain.Free(); folded.Free();
        return $"mesh merge check: {a.Count} materials, {ta} triangles plain, {tb} folded, largest difference {worst:0.######}: {(same && ta == tb && worst < 1e-3f ? "SAME" : "DIFFERENT")} (per material, plain/folded: {per})";
    }

    // each material's triangles as rows of 24 numbers (3 corners x position, normal, uv), corners in order, rows sorted
    static Dictionary<Material, List<float[]>> Soup(Node3D root)
    {
        var d = new Dictionary<Material, List<float[]>>();
        void Go(Node n, Transform3D t)
        {
            foreach (var c in n.GetChildren())
            {
                if (c is not Node3D c3) continue;
                var ct = t * c3.Transform;
                if (c is MeshInstance3D { Mesh: { } m } mi)
                    for (int s = 0; s < m.GetSurfaceCount(); s++)
                    {
                        var arr = m.SurfaceGetArrays(s);
                        var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                        var nr = arr[(int)Mesh.ArrayType.Normal].AsVector3Array();
                        var uv = arr[(int)Mesh.ArrayType.TexUV].AsVector2Array();
                        var ix = arr[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil ? Enumerable.Range(0, v.Length).ToArray() : arr[(int)Mesh.ArrayType.Index].AsInt32Array();
                        var mat = mi.GetActiveMaterial(s);
                        if (!d.TryGetValue(mat, out var list)) d[mat] = list = new List<float[]>();
                        for (int i = 0; i + 2 < ix.Length; i += 3)
                        {
                            var row = new float[24];
                            for (int k = 0; k < 3; k++)
                            {
                                var p = ct * v[ix[i + k]];
                                var q = nr.Length > 0 ? (ct.Basis * nr[ix[i + k]]).Normalized() : Vector3.Zero;
                                var u = uv.Length > 0 ? uv[ix[i + k]] : Vector2.Zero;
                                row[k * 8] = p.X; row[k * 8 + 1] = p.Y; row[k * 8 + 2] = p.Z;
                                row[k * 8 + 3] = q.X; row[k * 8 + 4] = q.Y; row[k * 8 + 5] = q.Z; row[k * 8 + 6] = u.X; row[k * 8 + 7] = u.Y;
                            }
                            list.Add(row);
                        }
                    }
                Go(c, ct);
            }
        }
        Go(root, Transform3D.Identity);
        foreach (var list in d.Values)
            list.Sort((x, y) => { for (int k = 0; k < x.Length; k++) { int c = Math.Round(x[k], 4).CompareTo(Math.Round(y[k], 4)); if (c != 0) return c; } return 0; });
        return d;
    }
}
