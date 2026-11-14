using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using N = System.Numerics;

namespace SurvivorUnchained.View;

/// <summary>
/// A worn piece's vertices given to its spring bones at dress time (her wear: HerWear; her pieces' files are skinned to
/// her body bones only). Play/SpringCarry picks the vertices (row "carry": island or blend, reach, share); here a mesh is
/// read, the pick run off the main thread, and the mesh remade with the new weights and a bind per spring bone (its
/// blend shapes kept, as HerWear.BuildLay does). Once a mesh and its springs: a remade mesh is cached by its source mesh
/// and the links (a re-dress or her cinematic double reuses it), deterministic. A mesh whose skin already binds one of
/// the spring bones (R&D's and B's pieces come weighted) is left as it is.
/// </summary>
public static class PieceCarry
{
    /// <summary>One spring link in the skeleton's rest frame (its bone, head and tail), with the carry's reach.</summary>
    public readonly record struct Spring(string Bone, Vector3 Head, Vector3 Tail, float Reach);

    sealed class Job
    {
        public MeshInstance3D Mi = null!;
        public ArrayMesh Src = null!;
        public string Key = "";
        public Godot.Collections.Array[] Arr = Array.Empty<Godot.Collections.Array>();
        public N.Vector3[][] Pos = Array.Empty<N.Vector3[]>();
        public int[][] Tris = Array.Empty<int[]>();
        public int[][] Bones = Array.Empty<int[]>();
        public float[][] Weights = Array.Empty<float[]>();
        public int[] Ks = Array.Empty<int>();
        public int[] LinkBind = Array.Empty<int>();
        public Transform3D[] ToSkel = Array.Empty<Transform3D>();
        public Transform3D M = Transform3D.Identity;   // (the springs' binds' frame: the bind most vertices ride most)
        public Vector3[]?[] Vs = Array.Empty<Vector3[]?>(), Ns = Array.Empty<Vector3[]?>();
        public float[]?[] Ts = Array.Empty<float[]?>();
        public int Moved, Reframed;
        public float Off;
        public Vector3[][] V = Array.Empty<Vector3[]>();
        public Vector3[]?[] Nr = Array.Empty<Vector3[]?>();
        public float[]?[] Tg = Array.Empty<float[]?>();
        // (PlateFollow's view of the mesh: the original binds' weights, each surface's carry, its shapes' offsets as read)
        public int[] BindBone = Array.Empty<int>();
        public int[][] Bones0 = Array.Empty<int[]>();
        public float[][] W0 = Array.Empty<float[]>();
        public N.Vector3[][] NormSk = Array.Empty<N.Vector3[]>();
        public int[][] LinkOut = Array.Empty<int[]>();
        public Vector3[]?[][] ShD = Array.Empty<Vector3[]?[]>(), ShDn = Array.Empty<Vector3[]?[]>();
        public int ShapeCount;
        public PlateFollow.MeshIn? Follow;
    }

    /// <summary>The remade meshes' PlateFollow data (by the ArrayMesh a MeshInstance3D now draws), for a row that follows.</summary>
    static readonly Dictionary<ArrayMesh, PlateFollow.MeshIn> followOf = new();
    public static PlateFollow.MeshIn? FollowOf(MeshInstance3D mi) => mi.Mesh is ArrayMesh am && followOf.TryGetValue(am, out var f) ? f : null;

    /// <summary>All the job's skinned surfaces as one PlateFollow mesh: rest places and normals in the skeleton's frame, the
    /// influences' skeleton bones and original weights, the carried vertices' links, the shapes' offsets in skeleton axes.</summary>
    static PlateFollow.MeshIn BuildFollow(Job j)
    {
        int ns = j.Pos.Length, total = 0, K = 1;
        for (int s = 0; s < ns; s++) if (j.Pos[s] != null) { total += j.Pos[s].Length; K = Math.Max(K, j.Ks[s]); }
        var place = new N.Vector3[total]; var nrm = new N.Vector3[total]; var bone = new int[total * K]; var wt = new float[total * K]; var link = new int[total];
        var sd = new N.Vector3[]?[j.ShapeCount]; var sdn = new N.Vector3[]?[j.ShapeCount];
        Array.Fill(bone, -1);
        var rot = j.M.Basis;
        int off = 0;
        for (int s = 0; s < ns; s++)
        {
            if (j.Pos[s] == null) continue;
            int n = j.Pos[s].Length, k = j.Ks[s];
            for (int i = 0; i < n; i++)
            {
                place[off + i] = j.Pos[s][i];
                nrm[off + i] = j.NormSk[s][i];
                link[off + i] = j.LinkOut[s][i];
                for (int q = 0; q < k; q++)
                {
                    int b = j.Bones0[s][i * k + q];
                    bone[(off + i) * K + q] = b >= 0 && b < j.BindBone.Length ? j.BindBone[b] : -1;
                    wt[(off + i) * K + q] = j.W0[s][i * k + q];
                }
            }
            for (int h = 0; h < j.ShapeCount; h++)
            {
                if (j.ShD[s][h] is not { } d) continue;
                sd[h] ??= new N.Vector3[total]; sdn[h] ??= new N.Vector3[total];
                var dn = j.ShDn[s][h];
                for (int i = 0; i < n; i++)
                {
                    sd[h]![off + i] = Nv(rot * d[i]);
                    if (dn != null) sdn[h]![off + i] = Nv(rot * dn[i]);
                }
            }
            off += n;
        }
        return new PlateFollow.MeshIn { K = K, Place = place, Normal = nrm, Bone = bone, Weight = wt, At = null, ChannelBase = 0, ShapeD = sd, ShapeDn = sdn, Link = link };
    }

    /// <summary>The pick, off the main thread: each vertex's rest place (its weights' blend of its binds' frames), the
    /// carry (SpringCarry), and each vertex now wholly on a spring put in the springs' binds' frame (M) where its own
    /// blend was another (its place, normal and tangent; its blend shapes' offsets stay as they were).</summary>
    static void Pick(Job j, SpringCarry.Seg[] segs, SpringCarry.Rule rule, float share)
    {
        int ns = j.Pos.Length;
        var votes = new int[Math.Max(1, j.ToSkel.Length)];
        for (int s = 0; s < ns; s++)
        {
            if (j.Pos[s] == null) continue;
            int k = j.Ks[s];
            for (int i = 0; i < j.Pos[s].Length; i++)
            {
                int best = 0;
                for (int q = 1; q < k; q++) if (j.Weights[s][i * k + q] > j.Weights[s][i * k + best]) best = q;
                int b = j.Bones[s][i * k + best];
                if (b >= 0 && b < j.ToSkel.Length) votes[b]++;
            }
        }
        if (j.ToSkel.Length > 0) j.M = j.ToSkel[Array.IndexOf(votes, votes.Max())];
        var mInv = j.M.AffineInverse();
        j.Vs = new Vector3[]?[ns]; j.Ns = new Vector3[]?[ns]; j.Ts = new float[]?[ns];
        j.Bones0 = new int[ns][]; j.W0 = new float[ns][]; j.NormSk = new N.Vector3[ns][]; j.LinkOut = new int[ns][];
        for (int s = 0; s < ns; s++)
        {
            if (j.Pos[s] == null) continue;
            var v = j.V[s]; var nr = j.Nr[s]; var tg = j.Tg[s];
            int k = j.Ks[s];
            var bo = j.Bones[s]; var w = j.Weights[s];
            // (each vertex's blended frame at the bind: its place, and its axes for the normal and tangent)
            var at = new Vector3[v.Length];
            var basis = new Basis[v.Length];
            for (int i = 0; i < v.Length; i++)
            {
                Vector3 p = Vector3.Zero, c0 = Vector3.Zero, c1 = Vector3.Zero, c2 = Vector3.Zero;
                float sum = 0;
                for (int q = 0; q < k; q++)
                {
                    float wq = w[i * k + q];
                    int b = bo[i * k + q];
                    if (wq <= 0 || b < 0 || b >= j.ToSkel.Length) continue;
                    var t = j.ToSkel[b];
                    p += (t * v[i]) * wq;
                    c0 += t.Basis.Column0 * wq; c1 += t.Basis.Column1 * wq; c2 += t.Basis.Column2 * wq;
                    sum += wq;
                }
                if (sum > 1e-6f) { at[i] = p / sum; basis[i] = new Basis(c0 / sum, c1 / sum, c2 / sum); }
                else { at[i] = j.M * v[i]; basis[i] = j.M.Basis; }
                j.Pos[s][i] = Nv(at[i]);
            }
            var (link, sh) = SpringCarry.Assign(j.Pos[s], j.Tris[s], segs, rule, share);
            // (copies of the weights as they came, before Apply moves them onto the springs)
            j.Bones0[s] = (int[])bo.Clone(); j.W0[s] = (float[])w.Clone();
            j.NormSk[s] = new N.Vector3[v.Length]; j.LinkOut[s] = new int[v.Length];
            for (int i = 0; i < v.Length; i++)
            {
                j.NormSk[s][i] = nr != null ? Nv((basis[i] * nr[i]).Normalized()) : N.Vector3.UnitY;
                j.LinkOut[s][i] = link[i] >= 0 && sh[i] >= 0.999f ? link[i] : -1;
            }
            j.Moved += SpringCarry.Apply(bo, w, k, link, sh, j.LinkBind);
            Vector3[]? nv = null, nn = null; float[]? nt = null;
            for (int i = 0; i < v.Length; i++)
            {
                if (link[i] < 0 || sh[i] < 0.999f) continue;
                var to = mInv * at[i];
                float off = to.DistanceTo(v[i]);
                if (off < 1e-5f) continue;
                nv ??= (Vector3[])v.Clone();
                nv[i] = to;
                var rot = mInv.Basis * basis[i];
                if (nr != null) { nn ??= (Vector3[])nr.Clone(); nn[i] = (rot * nr[i]).Normalized(); }
                if (tg != null)
                {
                    nt ??= (float[])tg.Clone();
                    var tv = (rot * new Vector3(tg[i * 4], tg[i * 4 + 1], tg[i * 4 + 2])).Normalized();
                    nt[i * 4] = tv.X; nt[i * 4 + 1] = tv.Y; nt[i * 4 + 2] = tv.Z;
                }
                j.Reframed++;
                j.Off = Math.Max(j.Off, off);
            }
            j.Vs[s] = nv; j.Ns[s] = nn; j.Ts[s] = nt;
        }
        j.Follow = BuildFollow(j);
    }

    static readonly Dictionary<string, (ArrayMesh Mesh, Skin Skin, int Moved, PlateFollow.MeshIn? Follow)> cache = new();

    /// <summary>Carries each mesh onto the springs: steps for HerWear.ApplySteps (a task yielded is the pick on a
    /// worker; the mesh is made after it). Prints a line per mesh carried.</summary>
    public static IEnumerable<System.Threading.Tasks.Task?> Steps(Skeleton3D sk, IEnumerable<MeshInstance3D> meshes, IReadOnlyList<Spring> links,
        SpringCarry.Rule rule, float share, string what)
    {
        if (links.Count == 0) yield break;
        var segs = links.Select(l => new SpringCarry.Seg(Nv(l.Head), Nv(l.Tail), l.Reach)).ToArray();
        string sig = $"{rule}|{share:R}|" + string.Join(";", links.Select(l => $"{l.Bone}:{l.Head}:{l.Tail}:{l.Reach:R}"));
        foreach (var mi in meshes)
        {
            if (!GodotObject.IsInstanceValid(mi) || mi.Mesh is not ArrayMesh src || mi.Skin == null) continue;
            var skin = mi.Skin;
            var binds = Enumerable.Range(0, skin.GetBindCount()).Select(b => skin.GetBindName(b).ToString()).ToArray();
            if (links.Any(l => binds.Contains(l.Bone))) continue;   // (weighted to its springs already)
            string key = src.GetInstanceId() + "|" + sig;
            if (cache.TryGetValue(key, out var got))
            {
                mi.Mesh = got.Mesh; mi.Skin = got.Skin;
                if (got.Follow != null) followOf[got.Mesh] = got.Follow;
                continue;
            }
            // (each bind's frame into the skeleton's at the bind: its bone's rest times its pose; they need not agree, so a
            // vertex's rest place is its own weights' blend of them, and the springs' binds take the frame most vertices ride)
            var bindBone = binds.Select(n => n != "" ? sk.FindBone(n) : -1).ToArray();
            for (int b = 0; b < bindBone.Length; b++) if (bindBone[b] < 0 && binds[b] == "") bindBone[b] = skin.GetBindBone(b);
            var j = new Job { Mi = mi, Src = src, Key = key };
            j.ToSkel = Enumerable.Range(0, bindBone.Length).Select(b => bindBone[b] >= 0 ? sk.GetBoneGlobalRest(bindBone[b]) * skin.GetBindPose(b) : Transform3D.Identity).ToArray();
            int ns = src.GetSurfaceCount();
            j.Arr = new Godot.Collections.Array[ns]; j.Pos = new N.Vector3[ns][]; j.Tris = new int[ns][];
            j.Bones = new int[ns][]; j.Weights = new float[ns][]; j.Ks = new int[ns];
            j.V = new Vector3[ns][]; j.Nr = new Vector3[]?[ns]; j.Tg = new float[]?[ns];
            for (int s = 0; s < ns; s++)
            {
                var arr = src.SurfaceGetArrays(s);
                j.Arr[s] = arr;
                if (src.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles
                    || arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil || arr[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil)
                    continue;
                var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                j.V[s] = v;
                j.Nr[s] = arr[(int)Mesh.ArrayType.Normal].VariantType == Variant.Type.Nil ? null : arr[(int)Mesh.ArrayType.Normal].AsVector3Array();
                j.Tg[s] = arr[(int)Mesh.ArrayType.Tangent].VariantType == Variant.Type.Nil ? null : arr[(int)Mesh.ArrayType.Tangent].AsFloat32Array();
                j.Pos[s] = new N.Vector3[v.Length];
                j.Tris[s] = arr[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil ? Enumerable.Range(0, v.Length).ToArray() : arr[(int)Mesh.ArrayType.Index].AsInt32Array();
                j.Bones[s] = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                j.Weights[s] = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                j.Ks[s] = v.Length > 0 ? j.Bones[s].Length / v.Length : 4;
            }
            j.BindBone = bindBone;
            j.ShapeCount = src.GetBlendShapeCount();
            j.ShD = new Vector3[]?[ns][]; j.ShDn = new Vector3[]?[ns][];
            for (int s = 0; s < ns; s++)
            {
                j.ShD[s] = new Vector3[j.ShapeCount][]; j.ShDn[s] = new Vector3[j.ShapeCount][];
                if (j.Pos[s] == null || j.ShapeCount == 0 || DisplayServer.GetName() == "headless") continue;
                var sa = src.SurfaceGetBlendShapeArrays(s);
                bool relative = src.BlendShapeMode == Mesh.BlendShapeMode.Relative;
                for (int h = 0; h < j.ShapeCount && h < sa.Count; h++)
                {
                    var sv = sa[h][(int)Mesh.ArrayType.Vertex];
                    if (sv.VariantType == Variant.Type.Nil) continue;
                    var a = sv.AsVector3Array();
                    if (a.Length != j.V[s].Length) continue;
                    var d = new Vector3[a.Length];
                    for (int i = 0; i < a.Length; i++) d[i] = relative ? a[i] : a[i] - j.V[s][i];
                    j.ShD[s][h] = d;
                    var snv = sa[h][(int)Mesh.ArrayType.Normal];
                    if (snv.VariantType != Variant.Type.Nil && j.Nr[s] != null)
                    {
                        var an = snv.AsVector3Array();
                        if (an.Length == a.Length)
                        {
                            var dn = new Vector3[a.Length];
                            for (int i = 0; i < a.Length; i++) dn[i] = relative ? an[i] : an[i] - j.Nr[s]![i];
                            j.ShDn[s][h] = dn;
                        }
                    }
                }
            }
            j.LinkBind = Enumerable.Range(0, links.Count).Select(i => binds.Length + i).ToArray();
            yield return System.Threading.Tasks.Task.Run(() => Pick(j, segs, rule, share));
            if (j.Moved == 0)
            {
                if (PieceSprings.Debug) GD.Print($"springs: {what}: {mi.Name}: no vertices in reach of its springs");
                continue;
            }
            // (the mesh remade with the new weights: HerWear.BuildLay's way)
            var mesh = new ArrayMesh { BlendShapeMode = src.BlendShapeMode };
            bool shapes = src.GetBlendShapeCount() > 0 && DisplayServer.GetName() != "headless";
            if (shapes) for (int k = 0; k < src.GetBlendShapeCount(); k++) mesh.AddBlendShape(src.GetBlendShapeName(k));
            for (int s = 0; s < ns; s++)
            {
                var arr = j.Arr[s];
                if (j.Pos[s] != null)
                {
                    arr[(int)Mesh.ArrayType.Bones] = j.Bones[s];
                    arr[(int)Mesh.ArrayType.Weights] = j.Weights[s];
                    if (j.Vs[s] != null) arr[(int)Mesh.ArrayType.Vertex] = j.Vs[s]!;
                    if (j.Ns[s] != null) arr[(int)Mesh.ArrayType.Normal] = j.Ns[s]!;
                    if (j.Ts[s] != null) arr[(int)Mesh.ArrayType.Tangent] = j.Ts[s]!;
                }
                long fmt = (long)src.SurfaceGetFormat(s);
                var flags = (Mesh.ArrayFormat)(fmt & ((long)Mesh.ArrayFormat.FlagUse8BoneWeights | (0xFFFL << (int)Mesh.ArrayFormat.FormatCustom0Shift)));
                mesh.AddSurfaceFromArrays(src.SurfaceGetPrimitiveType(s), arr, shapes ? src.SurfaceGetBlendShapeArrays(s) : new Godot.Collections.Array<Godot.Collections.Array>(), null, flags);
                mesh.SurfaceSetMaterial(s, src.SurfaceGetMaterial(s));
                mesh.SurfaceSetName(s, src.SurfaceGetName(s));
            }
            mesh.ResourceName = src.ResourceName;
            var ns2 = (Skin)skin.Duplicate();
            foreach (var l in links)
            {
                int b = sk.FindBone(l.Bone);
                ns2.AddNamedBind(l.Bone, (b >= 0 ? sk.GetBoneGlobalRest(b).AffineInverse() : Transform3D.Identity) * j.M);
            }
            mi.Mesh = mesh; mi.Skin = ns2;
            cache[key] = (mesh, ns2, j.Moved, j.Follow);
            if (j.Follow != null) followOf[mesh] = j.Follow;
            GD.Print($"springs: {what}: {mi.Name}: {j.Moved} vertices carried ({rule.ToString().ToLowerInvariant()})"
                + (j.Reframed > 0 ? $", {j.Reframed} of them re-framed (their binds' frames off the springs' by up to {j.Off * 1000:0.0} mm)" : ""));
        }
    }

    static N.Vector3 Nv(Vector3 v) => new(v.X, v.Y, v.Z);
}
