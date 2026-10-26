using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A townsperson's shadow as one draw (MR4: a kit person's eight or so meshes each cast into every sun cascade and
/// every lamp, about 33 shadow draws a person). Their opaque meshes on the skeleton are joined, as their shadow only,
/// into one skinned mesh a weight count (the pattern of her HerLod.Merge), their shape keys baked in as set (a
/// woman's figure: it never changes after she is made), and the meshes themselves stop casting. The same geometry on
/// the same bones: the same shadow. Each kit mesh's arrays are read once a session (shared by everyone wearing it);
/// the join runs on a worker, and until it lands the meshes cast as before. --folk-shadow off: none (to compare).
/// </summary>
public static class FolkShadow
{
    public static readonly bool Off = Args.Get("folk-shadow") == "off";

    /// <summary>One surface's arrays as C# arrays (read once; never written).</summary>
    sealed class Surf
    {
        public Vector3[] V = null!, N = null!; public int[] Bones = null!; public float[] W = null!; public int[] Ix = null!;
        public int Per; public bool Eight;
        /// <summary>Each shape key's positions (as the mesh gives them back: whole positions, not offsets), or null.</summary>
        public Vector3[]?[] Shapes = System.Array.Empty<Vector3[]?>();
    }

    static readonly Dictionary<ulong, Surf?[]> read = new();
    static int told;

    /// <summary>A mesh's surfaces, read once (null: a surface that can't join: not skinned triangles).</summary>
    static Surf?[] Read(ArrayMesh am)
    {
        lock (read) return ReadLocked(am);
    }

    static Surf?[] ReadLocked(ArrayMesh am)
    {
        if (read.TryGetValue(am.GetInstanceId(), out var got)) return got;
        var o = new Surf?[am.GetSurfaceCount()];
        int nShapes = am.GetBlendShapeCount();
        for (int s = 0; s < o.Length; s++)
        {
            if (am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) continue;
            using var a = am.SurfaceGetArrays(s);
            var vv = a[(int)Mesh.ArrayType.Vertex];
            if (vv.VariantType == Variant.Type.Nil || a[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil
                || a[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil || a[(int)Mesh.ArrayType.Normal].VariantType == Variant.Type.Nil) continue;
            var v = vv.AsVector3Array();
            if (v.Length == 0) continue;
            var sf = new Surf
            {
                V = v, N = a[(int)Mesh.ArrayType.Normal].AsVector3Array(), Bones = a[(int)Mesh.ArrayType.Bones].AsInt32Array(),
                W = a[(int)Mesh.ArrayType.Weights].AsFloat32Array(),
                Ix = a[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil ? Enumerable.Range(0, v.Length).ToArray() : a[(int)Mesh.ArrayType.Index].AsInt32Array(),
                Eight = ((long)am.SurfaceGetFormat(s) & (long)Mesh.ArrayFormat.FlagUse8BoneWeights) != 0,
            };
            sf.Per = sf.Bones.Length / v.Length;
            if (nShapes > 0)
            {
                sf.Shapes = new Vector3[]?[nShapes];
                var shapes = am.SurfaceGetBlendShapeArrays(s);
                for (int k = 0; k < nShapes && k < shapes.Count; k++)
                {
                    var sv = shapes[k][(int)Mesh.ArrayType.Vertex];
                    if (sv.VariantType != Variant.Type.Nil && sv.AsVector3Array() is { } p && p.Length == v.Length) sf.Shapes[k] = p;
                }
            }
            o[s] = sf;
        }
        read[am.GetInstanceId()] = o;
        return o;
    }

    /// <summary>What a material casts: opaque only (nothing cut out or see-through, one pass); its faces both sides
    /// (the person shader's cull_disabled) or the front. Null: it can't join.</summary>
    static bool? TwoSided(Material? m) => m switch
    {
        null => false,
        BaseMaterial3D b when b.Transparency == BaseMaterial3D.TransparencyEnum.Disabled && b.NextPass == null && !b.Grow
            && b.CullMode != BaseMaterial3D.CullModeEnum.Front => b.CullMode == BaseMaterial3D.CullModeEnum.Disabled,
        ShaderMaterial sm when sm.NextPass == null && sm.Shader?.ResourcePath == "res://shaders/person.gdshader" => true,
        _ => null,
    };

    static StandardMaterial3D? oneSide, twoSides;
    /// <summary>The shadow's material: casts as the source's did (its faces culled alike).</summary>
    static StandardMaterial3D Caster(bool two) => two
        ? twoSides ??= new StandardMaterial3D { CullMode = BaseMaterial3D.CullModeEnum.Disabled, ResourceName = "folk_shadow_two_sided" }
        : oneSide ??= new StandardMaterial3D { ResourceName = "folk_shadow" };

    /// <summary>A source taken for the join: its surfaces, its weights' map into the merged skin, its shape weights.</summary>
    sealed class Piece { public required Surf S; public required int[] Map; public required float[] Shape; }

    public sealed class Job
    {
        internal readonly List<MeshInstance3D> From = new();
        internal readonly List<(string Bone, Transform3D Pose)> Binds = new();
        internal Task<List<(bool Eight, bool Two, Vector3[] V, Vector3[] N, int[] B, float[] W, int[] Ix)>>? Work;
        public bool Done => Work == null || Work.IsCompleted;
    }

    /// <summary>On the main thread, as a kit person is made: its casters read, the join begun on a worker (null: nothing to join).</summary>
    public static Job? Begin(People.Person p)
    {
        if (Off || !p.Kit) return null;
        var skel = p.Skeleton;
        var job = new Job();
        var pieces = new List<((bool Eight, bool Two) K, Piece P)>();
        foreach (var mi in p.Meshes)
        {
            if (!GodotObject.IsInstanceValid(mi) || mi.GetParent() != skel || mi.Mesh is not ArrayMesh am || mi.Skin is not Skin sk) continue;
            if (mi.CastShadow != GeometryInstance3D.ShadowCastingSetting.On || !mi.Visible || !mi.Transform.IsEqualApprox(Transform3D.Identity)) continue;
            var surfs = Read(am);
            bool ok = surfs.All(x => x != null);
            var two = new bool[surfs.Length];
            for (int s = 0; ok && s < surfs.Length; s++)
                if (TwoSided(mi.GetSurfaceOverrideMaterial(s) ?? am.SurfaceGetMaterial(s)) is bool t) two[s] = t; else ok = false;
            if (!ok) continue;
            var map = new int[sk.GetBindCount()];
            for (int b = 0; b < map.Length; b++)
            {
                string bone = sk.GetBindName(b).ToString();
                if (bone.Length == 0) bone = skel.GetBoneName(sk.GetBindBone(b));
                var pose = sk.GetBindPose(b);
                int at = job.Binds.FindIndex(x => x.Bone == bone && x.Pose.IsEqualApprox(pose));
                if (at < 0) { at = job.Binds.Count; job.Binds.Add((bone, pose)); }
                map[b] = at;
            }
            var shape = new float[am.GetBlendShapeCount()];
            for (int k = 0; k < shape.Length; k++) shape[k] = mi.GetBlendShapeValue(k);
            for (int s = 0; s < surfs.Length; s++) pieces.Add(((surfs[s]!.Eight, two[s]), new Piece { S = surfs[s]!, Map = map, Shape = shape }));
            job.From.Add(mi);
        }
        if (job.From.Count < 2) return null;
        var groups = pieces.GroupBy(x => x.K).Select(g => (g.Key, g.Select(x => x.P).ToArray())).ToList();
        job.Work = Task.Run(() => groups.Select(g => Join(g.Key.Eight, g.Key.Two, g.Item2)).ToList());
        return job;
    }

    /// <summary>The pieces end to end, their shape keys baked (no Godot calls: a worker).</summary>
    static (bool, bool, Vector3[], Vector3[], int[], float[], int[]) Join(bool eight, bool two, Piece[] src)
    {
        int nv = 0, ni = 0, nb = 0;
        foreach (var p in src) { nv += p.S.V.Length; ni += p.S.Ix.Length; nb += p.S.Bones.Length; }
        var V = new Vector3[nv]; var N = new Vector3[nv]; var B = new int[nb]; var W = new float[nb]; var Ix = new int[ni];
        int av = 0, ai = 0, ab = 0;
        foreach (var p in src)
        {
            var s = p.S;
            int n = s.V.Length;
            System.Array.Copy(s.V, 0, V, av, n);
            System.Array.Copy(s.N, 0, N, av, n);
            // A shape key as set: base + weight * (shape - base), each key (relative and normalized alike).
            for (int k = 0; k < p.Shape.Length && k < s.Shapes.Length; k++)
                if (p.Shape[k] != 0 && s.Shapes[k] is { } sh)
                    for (int i = 0; i < n; i++) V[av + i] += (sh[i] - s.V[i]) * p.Shape[k];
            for (int i = 0; i < s.Bones.Length; i++) B[ab + i] = s.Bones[i] < p.Map.Length ? p.Map[s.Bones[i]] : 0;
            System.Array.Copy(s.W, 0, W, ab, s.W.Length);
            for (int i = 0; i < s.Ix.Length; i++) Ix[ai + i] = s.Ix[i] + av;
            av += n; ai += s.Ix.Length; ab += s.Bones.Length;
        }
        return (eight, two, V, N, B, W, Ix);
    }

    /// <summary>On the main thread, once the join is done: the shadow mesh laid on the skeleton, the meshes' own
    /// casting off.</summary>
    public static void Finish(People.Person p, Job job)
    {
        if (job.Work == null || !GodotObject.IsInstanceValid(p.Skeleton)) return;
        var parts = job.Work.Result;
        job.Work = null;
        // (a source taken off since, or made to cast otherwise: left as it is)
        if (job.From.Any(m => !GodotObject.IsInstanceValid(m) || m.GetParent() != p.Skeleton || m.CastShadow != GeometryInstance3D.ShadowCastingSetting.On)) return;
        var skin = new Skin();
        foreach (var (bone, pose) in job.Binds) skin.AddNamedBind(bone, pose);
        var mesh = new ArrayMesh();
        foreach (var (eight, two, V, N, B, W, Ix) in parts)
        {
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Mesh.ArrayType.Max);
            arr[(int)Mesh.ArrayType.Vertex] = V;
            arr[(int)Mesh.ArrayType.Normal] = N;
            arr[(int)Mesh.ArrayType.Bones] = B;
            arr[(int)Mesh.ArrayType.Weights] = W;
            arr[(int)Mesh.ArrayType.Index] = Ix;
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr, null, null, eight ? Mesh.ArrayFormat.FlagUse8BoneWeights : 0);
            mesh.SurfaceSetMaterial(mesh.GetSurfaceCount() - 1, Caster(two));
        }
        var mi = new MeshInstance3D { Name = "folk_shadow", Mesh = mesh, Skin = skin, Layers = 2, CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly };
        p.Skeleton.AddChild(mi);
        mi.Skeleton = "..";
        foreach (var m in job.From) m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
        if (told++ < 3) GD.Print($"folk shadow: {job.From.Count} casters into 1 ({mesh.GetSurfaceCount()} surfaces, {parts.Sum(x => x.V.Length)} vertices); left casting: {p.Meshes.Count(m => GodotObject.IsInstanceValid(m) && m.CastShadow == GeometryInstance3D.ShadowCastingSetting.On)}");
    }
}
