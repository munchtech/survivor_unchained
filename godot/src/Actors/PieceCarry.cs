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
        public int Moved;
    }

    static readonly Dictionary<string, (ArrayMesh Mesh, Skin Skin, int Moved)> cache = new();

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
                continue;
            }
            // (the mesh's frame into the skeleton's at the bind: each bind's bone rest times its pose, one for all)
            var bindBone = binds.Select(n => n != "" ? sk.FindBone(n) : -1).ToArray();
            for (int b = 0; b < bindBone.Length; b++) if (bindBone[b] < 0 && binds[b] == "") bindBone[b] = skin.GetBindBone(b);
            var toSkel = Enumerable.Range(0, bindBone.Length).Where(b => bindBone[b] >= 0)
                .Select(b => sk.GetBoneGlobalRest(bindBone[b]) * skin.GetBindPose(b)).ToList();
            if (toSkel.Count == 0) continue;
            var m2s = toSkel[0];
            float spread = toSkel.Max(t => t.Origin.DistanceTo(m2s.Origin) + (t.Basis.X - m2s.Basis.X).Length() + (t.Basis.Y - m2s.Basis.Y).Length());
            if (spread > 1e-3f) GD.PushWarning($"springs: {what}: {mi.Name}'s binds disagree on its frame ({spread:0.0000}); carried by the first");
            var j = new Job { Mi = mi, Src = src, Key = key };
            int ns = src.GetSurfaceCount();
            j.Arr = new Godot.Collections.Array[ns]; j.Pos = new N.Vector3[ns][]; j.Tris = new int[ns][];
            j.Bones = new int[ns][]; j.Weights = new float[ns][]; j.Ks = new int[ns];
            for (int s = 0; s < ns; s++)
            {
                var arr = src.SurfaceGetArrays(s);
                j.Arr[s] = arr;
                if (src.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles
                    || arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil || arr[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil)
                    continue;
                var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                j.Pos[s] = v.Select(p => Nv(m2s * p)).ToArray();
                j.Tris[s] = arr[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil ? Enumerable.Range(0, v.Length).ToArray() : arr[(int)Mesh.ArrayType.Index].AsInt32Array();
                j.Bones[s] = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                j.Weights[s] = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                j.Ks[s] = v.Length > 0 ? j.Bones[s].Length / v.Length : 4;
            }
            j.LinkBind = Enumerable.Range(0, links.Count).Select(i => binds.Length + i).ToArray();
            yield return System.Threading.Tasks.Task.Run(() =>
            {
                for (int s = 0; s < ns; s++)
                {
                    if (j.Pos[s] == null) continue;
                    var (link, sh) = SpringCarry.Assign(j.Pos[s], j.Tris[s], segs, rule, share);
                    j.Moved += SpringCarry.Apply(j.Bones[s], j.Weights[s], j.Ks[s], link, sh, j.LinkBind);
                }
            });
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
                ns2.AddNamedBind(l.Bone, (b >= 0 ? sk.GetBoneGlobalRest(b).AffineInverse() : Transform3D.Identity) * m2s);
            }
            mi.Mesh = mesh; mi.Skin = ns2;
            cache[key] = (mesh, ns2, j.Moved);
            GD.Print($"springs: {what}: {mi.Name}: {j.Moved} vertices carried ({rule.ToString().ToLowerInvariant()})");
        }
    }

    static N.Vector3 Nv(Vector3 v) => new(v.X, v.Y, v.Z);
}
