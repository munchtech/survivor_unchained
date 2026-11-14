using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using N = System.Numerics;

namespace SurvivorUnchained.View;

/// <summary>
/// A package piece's spring bones and corrective shapes (Warden 7: the Ford-Warden's cape and capelet hem, armor/hood.glb),
/// from the piece's manifest entry, for any baked package piece:
/// "springs": [{bone, parent, head, tail, radius, [stiffness]}] (rest head and tail in the package frame, metres; a
/// bone's parent another spring bone or a body bone) and
/// "correctives": [{shape, bone, axis: "pitch", from, to, [ref: "root"|"parent"|"pelvis"|BONE]}].
/// NpcPackage adds the spring bones to the body's skeleton (AddBones) before it binds the piece's skin, so the piece's
/// meshes (full, lod1 and shadow, and HerLod's merged draw, which keeps bind names) ride them; this modifier, last on
/// the skeleton, swings them each frame (Play/ClothChains: heavy soaked wool, world units, so a 2.08x giant's cape
/// swings as slowly as its length makes it) kept off capsules on the body's legs, pelvis, spine and upper arms (Play/BodyCapsules; radii measured from
/// the body mesh, never closer than at the bind) and the ground, and drives each corrective's blend shape on every
/// mesh of the piece that has it (0 at from degrees, 1 at to, smoothstep). A cut resets the chains to a settled hang:
/// the camera changing or jumping, the body jumping (a teleport, a cinematic's re-pose), a long frame, or Cut().
/// PIECE_SPRINGS_DBG=1 prints, every second, each chain's worst link inside each body capsule (cm, package units)
/// and the corrective's pitch and weight, and after each reset the first frames' swing.
/// </summary>
public partial class PieceSprings : SkeletonModifier3D
{
    public sealed record Link(string Bone, string Parent, Vector3 Head, Vector3 Tail, float Radius, float Stiffness);
    public sealed record Corrective(string Shape, string Bone, string Axis, float From, float To, string Ref);

    static readonly Dictionary<string, (int A, int B, float R)[]> capsuleCache = new();
    public static readonly bool Debug = System.Environment.GetEnvironmentVariable("PIECE_SPRINGS_DBG") == "1";
    public static readonly bool Off = Args.Get("springs") == "off" || System.Environment.GetEnvironmentVariable("PIECE_SPRINGS") == "0";
    /// <summary>--springs-legacy (measuring only): the springs as they were before her-springs: no upper-arm capsules and
    /// a pinned link not held to its head's distance (ClothChains.HoldPinnedToHead).</summary>
    public static readonly bool Legacy = Args.Has("springs-legacy");

    readonly string what;
    readonly List<Link> links;
    readonly List<Corrective> correctives;
    readonly List<MeshInstance3D> meshes;
    readonly (int A, int B, float R)[] capsules;   // (skeleton units)
    readonly bool followRow;                       // (the row's carry says follow: Play/PlateFollow)
    readonly MeshInstance3D? bodyMi;
    readonly PlateFollow.MeshIn? bodyIn;

    // (set up on the first frame, on the skeleton)
    ClothChains? sim;
    int[] bone = Array.Empty<int>(), parentLink = Array.Empty<int>(), bodyParent = Array.Empty<int>(), linkParticle = Array.Empty<int>(), headParticle = Array.Empty<int>();
    int[] order = Array.Empty<int>();             // links, parents first
    Transform3D[] rest = Array.Empty<Transform3D>(), rigid = Array.Empty<Transform3D>(), posed = Array.Empty<Transform3D>();
    Vector3[] tailLocal = Array.Empty<Vector3>();
    N.Vector3[] targets = Array.Empty<N.Vector3>();
    ClothChains.Capsule[] cols = Array.Empty<ClothChains.Capsule>();
    readonly List<(int Bone, int Ref, Vector3 BoneRest, Transform3D RefRest, Corrective C, List<(MeshInstance3D Mi, int Shape)> On)> drive = new();
    float scale = 1;
    bool cut = true;
    Camera3D? lastCam;
    Transform3D lastCamAt;
    Vector3[] lastRoot = Array.Empty<Vector3>();
    Basis[] lastRootBasis = Array.Empty<Basis>();
    // (PIECE_SPRINGS_DBG)
    float[] worst = Array.Empty<float>();
    double dbgT, life;
    int sinceReset = -1;
    N.Vector3[] resetX = Array.Empty<N.Vector3>(), resetT = Array.Empty<N.Vector3>();
    string why = "first frame";
    long swingTicks; int swingFrames;   // (PIECE_SPRINGS_DBG: the swing's own time, targets to write)
    // (PlateFollow rows)
    PlateFollow? follow;
    PlateFollow.Xf[] skinX = Array.Empty<PlateFollow.Xf>();
    Transform3D[] restInv = Array.Empty<Transform3D>();
    float[] chW = Array.Empty<float>();
    readonly List<(MeshInstance3D Mi, int Base, int Count)> chans = new();

    PieceSprings(string what, List<Link> links, List<Corrective> correctives, List<MeshInstance3D> meshes, (int, int, float)[] capsules,
        bool followRow = false, MeshInstance3D? bodyMi = null, PlateFollow.MeshIn? bodyIn = null)
    {
        Name = NodeName(what);
        this.what = what; this.links = links; this.correctives = correctives; this.meshes = meshes; this.capsules = capsules;
        this.followRow = followRow; this.bodyMi = bodyMi; this.bodyIn = bodyIn;
    }

    /// <summary>A piece's springs with any link's radius under 0 (or not finite): refused whole, so the piece stays as
    /// weighted (ClothChains.RadiusOk), with a warning naming the link.</summary>
    static List<Link> Refused(List<Link> links)
    {
        var bad = links.FirstOrDefault(l => !ClothChains.RadiusOk(l.Radius));
        if (bad == null) return links;
        GD.PushWarning($"springs: link {bad.Bone}'s radius {bad.Radius} is under 0: the piece's springs are refused");
        return new();
    }

    /// <summary>The node's name for a piece (a package's "name/piece", her row's "warden.skirt": no '/' or '.').</summary>
    public static string NodeName(string what) => "PieceSprings_" + what.Replace('/', '_').Replace('.', '_');

    /// <summary>An armor row's springs (Rpg.ArmorIndex: her pieces), as a package entry's are read.</summary>
    public static List<Link> FromRows(IEnumerable<SurvivorUnchained.Rpg.SpringRow>? rows) =>
        rows?.Where(r => r.Bone != "" && r.Parent != "" && r.Head?.Length == 3 && r.Tail?.Length == 3)
            .Select(r => new Link(r.Bone, r.Parent, new Vector3((float)r.Head[0], (float)r.Head[1], (float)r.Head[2]),
                new Vector3((float)r.Tail[0], (float)r.Tail[1], (float)r.Tail[2]), (float)r.Radius, (float)r.Stiffness)).ToList() is { } l ? Refused(l) : new();

    /// <summary>An armor row's correctives.</summary>
    public static List<Corrective> FromRows(IEnumerable<SurvivorUnchained.Rpg.CorrectiveRow>? rows) =>
        rows?.Where(r => r.Shape != "" && r.Bone != "")
            .Select(r => new Corrective(r.Shape, r.Bone, r.Axis, (float)r.From, (float)r.To, Args.Get("corrective-ref") ?? r.Ref ?? DefaultRef)).ToList() ?? new();

    /// <summary>Starts the chains afresh on the next frame, at a settled hang (a cinematic's cut).</summary>
    public void Cut() { cut = true; why = "Cut()"; }

    /// <summary>The same piece's swing on another body (a cinematic's double) taken over as it is: no settle, no
    /// jump (H4 r3: C02's Warden's cape swung anew at the hand-back). Waits for this one's first frame if need be.</summary>
    public void TakeFrom(PieceSprings o) => from = o;
    PieceSprings? from;
    /// <summary>Frames after a take-over in which the body is not taken to have jumped (the double's last frame and this
    /// body's first differ by a frame's pose: read as a jump it reset the cape to a settled hang, a visible swap).</summary>
    int tookGrace;
    void Took()
    {
        var o = from!; from = null;
        if (sim == null || o.sim == null || !IsInstanceValid(o) || !sim.CopyFrom(o.sim)) { GD.Print($"springs: {what}: not taken over"); return; }
        cut = false; life = Math.Max(life, 1); tookGrace = 3;
        lastCam = o.lastCam; lastCamAt = o.lastCamAt;
        if (o.lastRoot.Length == lastRoot.Length) { Array.Copy(o.lastRoot, lastRoot, lastRoot.Length); Array.Copy(o.lastRootBasis, lastRootBasis, lastRootBasis.Length); }
        GD.Print($"springs: {what}: taken over");
    }

    /// <summary>Each piece's springs under one node taking over the same piece's under another.</summary>
    public static void TakeAll(Node to, Node fromRoot)
    {
        foreach (var n in to.FindChildren("PieceSprings_*", "", true, false))
            if (n is PieceSprings ps && fromRoot.FindChildren(n.Name, "", true, false).FirstOrDefault() is PieceSprings src) ps.TakeFrom(src);
    }

    /// <summary>Cut() on every piece's springs under a node.</summary>
    public static void CutAll(Node root)
    {
        foreach (var n in root.FindChildren("PieceSprings_*", "", true, false)) if (n is PieceSprings ps) ps.Cut();
    }

    /// <summary>A piece entry's "springs", read (none: an empty list).</summary>
    public static List<Link> ReadSprings(Variant v)
    {
        var o = new List<Link>();
        if (v.VariantType != Variant.Type.Array) return o;
        static Vector3 P(Variant a) { var x = a.AsGodotArray(); return new Vector3((float)x[0], (float)x[1], (float)x[2]); }
        foreach (var e in v.AsGodotArray())
        {
            if (e.VariantType != Variant.Type.Dictionary) continue;
            var d = e.AsGodotDictionary();
            if (!d.ContainsKey("bone") || !d.ContainsKey("parent") || !d.ContainsKey("head") || !d.ContainsKey("tail")) continue;
            o.Add(new Link((string)d["bone"], (string)d["parent"], P(d["head"]), P(d["tail"]),
                d.TryGetValue("radius", out var r) ? (float)r : 0.04f, d.TryGetValue("stiffness", out var s) ? (float)s : 0));
        }
        return Refused(o);
    }

    /// <summary>A piece entry's "correctives", read.</summary>
    public static List<Corrective> ReadCorrectives(Variant v)
    {
        var o = new List<Corrective>();
        if (v.VariantType != Variant.Type.Array) return o;
        foreach (var e in v.AsGodotArray())
        {
            if (e.VariantType != Variant.Type.Dictionary) continue;
            var d = e.AsGodotDictionary();
            if (!d.ContainsKey("shape") || !d.ContainsKey("bone")) continue;
            o.Add(new Corrective((string)d["shape"], (string)d["bone"], d.TryGetValue("axis", out var a) ? (string)a : "pitch",
                d.TryGetValue("from", out var f) ? (float)f : 0, d.TryGetValue("to", out var t) ? (float)t : 90,
                Args.Get("corrective-ref") ?? (d.TryGetValue("ref", out var r) ? (string)r : DefaultRef)));
        }
        return o;
    }

    /// <summary>What a corrective's pitch is measured against when the manifest does not say: the skeleton's own frame
    /// (the bone's lean off its rest, whole body: the Ford-Warden's C02 s7 stoop reads 72-84 deg on spine_03 so).</summary>
    public const string DefaultRef = "root";

    /// <summary>The spring bones the body lacks, added to its skeleton under their parents (parents first), at the piece
    /// skeleton's rest where it has them, else at the manifest's head with the parent's axes. pkgToSkel: the package frame
    /// into the skeleton's (the piece scene's armature transform, inverted).</summary>
    public static int AddBones(Skeleton3D to, Skeleton3D? from, List<Link> links, Transform3D pkgToSkel, string what)
    {
        int added = 0;
        var pending = new List<Link>(links);
        for (int pass = 0; pass < links.Count + 1 && pending.Count > 0; pass++)
            foreach (var l in pending.ToList())
            {
                if (to.FindBone(l.Bone) >= 0) { pending.Remove(l); continue; }
                int pi = to.FindBone(l.Parent);
                if (pi < 0) continue;   // (its parent is a spring bone not added yet)
                Transform3D global;
                int fb = from?.FindBone(l.Bone) ?? -1;
                if (from != null && fb >= 0) global = from.GetBoneGlobalRest(fb);
                else global = new Transform3D(to.GetBoneGlobalRest(pi).Basis, pkgToSkel * l.Head);
                to.AddBone(l.Bone);
                int b = to.FindBone(l.Bone);
                to.SetBoneParent(b, pi);
                var local = to.GetBoneGlobalRest(pi).AffineInverse() * global;
                to.SetBoneRest(b, local);
                to.SetBonePosePosition(b, local.Origin);
                to.SetBonePoseRotation(b, local.Basis.GetRotationQuaternion());
                to.SetBonePoseScale(b, Vector3.One);
                pending.Remove(l);
                added++;
            }
        foreach (var l in pending) GD.PushWarning($"springs: {what}'s bone {l.Bone} has no parent {l.Parent} on the body");
        if (added > 0) GD.Print($"springs: {what}: {added} bones added to the body's skeleton ({to.GetBoneCount()} now)");
        return added;
    }

    /// <summary>The springs and correctives of one piece, on its person's skeleton (last of its modifiers): null when
    /// it has neither.</summary>
    public static PieceSprings? Attach(People.Person p, string what, string package, List<Link> links, List<Corrective> correctives,
        List<MeshInstance3D> pieceMeshes, Transform3D pkgToSkel, bool follow = false)
    {
        if (Off || (links.Count == 0 && correctives.Count == 0)) return null;
        var sk = p.Skeleton;
        // (each link's head and tail into the skeleton's frame; its radius by the frame's scale)
        float fs = pkgToSkel.Basis.Scale.X;
        var ls = links.Where(l => sk.FindBone(l.Bone) >= 0)
            .Select(l => l with { Head = pkgToSkel * l.Head, Tail = pkgToSkel * l.Tail, Radius = l.Radius * fs }).ToList();
        follow &= !Legacy && ls.Count > 0;
        MeshInstance3D? bmi = null; PlateFollow.MeshIn? bin = null;
        if (follow)
        {
            ClothChains.HoldPinnedToHead = true;
            (bmi, bin) = BodyOf(p, package);
        }
        var caps = ls.Count > 0 && !follow ? Capsules(p, package) : Array.Empty<(int, int, float)>();
        var m = new PieceSprings(what, ls, correctives, pieceMeshes, caps, follow, bmi, bin);
        sk.AddChild(m);
        return m;
    }

    /// <summary>The body's capsules (Play/BodyCapsules) with radii from its mesh: of the vertices its carrier bones carry
    /// most (at the bind), the 80th percentile of their distance off its segment (robe and all), once a package (her: a body).</summary>
    static (int A, int B, float R)[] Capsules(People.Person p, string package)
    {
        if (capsuleCache.TryGetValue(package, out var have)) return have;
        var sk = p.Skeleton;
        ClothChains.HoldPinnedToHead = !Legacy;
        var segs = BodyCapsules.Table.Where(x => !Legacy || !x.A.StartsWith("upperarm")).Select(x => (A: sk.FindBone(x.A), B: sk.FindBone(x.B), Carry: x.Carry.Select(n => sk.FindBone(n)).Where(b => b >= 0).ToArray()))
            .Where(x => x.A >= 0 && x.B >= 0).ToArray();
        var dist = segs.Select(_ => new List<float>()).ToArray();
        var byBone = new Dictionary<int, int>();
        for (int i = 0; i < segs.Length; i++) foreach (int b in segs[i].Carry) byBone.TryAdd(b, i);
        foreach (var mi in p.Meshes.Where(mi => mi.GetParent() == sk && mi.Skin != null && mi.Mesh != null && !mi.HasMeta("her_wear") && !p.Hair.Contains(mi)))
        {
            var skin = mi.Skin;
            var bindBone = Enumerable.Range(0, skin.GetBindCount()).Select(b => skin.GetBindName(b) is var n && n != "" ? sk.FindBone(n) : skin.GetBindBone(b)).ToArray();
            var bindTo = Enumerable.Range(0, skin.GetBindCount()).Select(b => bindBone[b] >= 0 ? sk.GetBoneGlobalRest(bindBone[b]) * skin.GetBindPose(b) : Transform3D.Identity).ToArray();
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var arr = mi.Mesh.SurfaceGetArrays(s);
                if (arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil || arr[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil) continue;
                var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var bo = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                var w = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                if (v.Length == 0) continue;
                int k = bo.Length / v.Length;
                for (int i = 0; i < v.Length; i++)
                {
                    int best = 0;
                    for (int j = 1; j < k; j++) if (w[i * k + j] > w[i * k + best]) best = j;
                    if (w[i * k + best] < 0.5f) continue;
                    int bind = bo[i * k + best];
                    if (bind < 0 || bind >= bindBone.Length || !byBone.TryGetValue(bindBone[bind], out int c)) continue;
                    var at = bindTo[bind] * v[i];
                    var a = sk.GetBoneGlobalRest(segs[c].A).Origin; var b = sk.GetBoneGlobalRest(segs[c].B).Origin;
                    var (_, _, d) = ClothChains.Closest(Nv(at), Nv(at), Nv(a), Nv(b));
                    dist[c].Add(d);
                }
            }
        }
        var o = new List<(int, int, float)>();
        for (int c = 0; c < segs.Length; c++)
        {
            if (BodyCapsules.Radius(dist[c]) is float r) o.Add((segs[c].A, segs[c].B, r));
        }
        GD.Print($"springs: {package}'s body capsules " + string.Join(", ", o.Select(x => $"{sk.GetBoneName(x.Item1)}-{sk.GetBoneName(x.Item2)} r{x.Item3 * 100:0.0} cm")));
        return capsuleCache[package] = o.ToArray();
    }

    static readonly Dictionary<string, PlateFollow.MeshIn?> bodyCache = new();

    /// <summary>The person's body mesh (the one with the most vertices of the skinned meshes on the skeleton, not her wear
    /// or hair) and its PlateFollow data (cached by package): rest places and normals where each vertex's binds put it
    /// (they disagree by up to 42 mm, so each influence's own place too), skeleton bones, weights, shapes in the
    /// dominant influence's axes.</summary>
    static (MeshInstance3D?, PlateFollow.MeshIn?) BodyOf(People.Person p, string package)
    {
        var sk = p.Skeleton;
        MeshInstance3D? best = null; int bestN = 0;
        foreach (var mi in p.Meshes.Where(mi => GodotObject.IsInstanceValid(mi) && mi.GetParent() == sk && mi.Skin != null && mi.Mesh != null && !mi.HasMeta("her_wear") && !p.Hair.Contains(mi)))
        {
            int n = 0;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++) n += mi.Mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Vertex].AsVector3Array().Length;
            if (n > bestN) { bestN = n; best = mi; }
        }
        if (best == null) return (null, null);
        if (bodyCache.TryGetValue(package, out var have)) return (best, have);
        var skin = best.Skin; var mesh = best.Mesh;
        var bindBone = Enumerable.Range(0, skin.GetBindCount()).Select(b => skin.GetBindName(b) is var nm && nm != "" ? sk.FindBone(nm) : skin.GetBindBone(b)).ToArray();
        var bindTo = Enumerable.Range(0, bindBone.Length).Select(b => bindBone[b] >= 0 ? sk.GetBoneGlobalRest(bindBone[b]) * skin.GetBindPose(b) : Transform3D.Identity).ToArray();
        int ns = mesh.GetSurfaceCount(), total = 0, K = 1;
        var arrs = new Godot.Collections.Array?[ns];
        for (int s = 0; s < ns; s++)
        {
            var arr = mesh.SurfaceGetArrays(s);
            if (arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil || arr[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil) continue;
            int n = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array().Length;
            if (n == 0) continue;
            arrs[s] = arr; total += n; K = Math.Max(K, arr[(int)Mesh.ArrayType.Bones].AsInt32Array().Length / n);
        }
        var place = new N.Vector3[total]; var nrm = new N.Vector3[total]; var bone = new int[total * K]; var wt = new float[total * K]; var at = new N.Vector3[total * K];
        Array.Fill(bone, -1);
        int shapes = best.GetBlendShapeCount();
        bool relative = mesh is ArrayMesh am0 && am0.BlendShapeMode == Mesh.BlendShapeMode.Relative;
        bool readShapes = shapes > 0 && DisplayServer.GetName() != "headless";
        var sd = new N.Vector3[]?[shapes]; var sdn = new N.Vector3[]?[shapes];
        int off = 0;
        for (int s = 0; s < ns; s++)
        {
            if (arrs[s] is not { } arr) continue;
            var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            var nr = arr[(int)Mesh.ArrayType.Normal].VariantType == Variant.Type.Nil ? null : arr[(int)Mesh.ArrayType.Normal].AsVector3Array();
            var bo = arr[(int)Mesh.ArrayType.Bones].AsInt32Array(); var w = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
            int k = bo.Length / v.Length;
            var dom = new int[v.Length];
            for (int i = 0; i < v.Length; i++)
            {
                Vector3 pp = Vector3.Zero, nn = Vector3.Zero; float sum = 0; int bq = 0;
                for (int q = 0; q < k; q++)
                {
                    float wq = w[i * k + q]; int b = bo[i * k + q];
                    bone[(off + i) * K + q] = b >= 0 && b < bindBone.Length ? bindBone[b] : -1;
                    wt[(off + i) * K + q] = wq;
                    at[(off + i) * K + q] = b >= 0 && b < bindTo.Length ? Nv(bindTo[b] * v[i]) : N.Vector3.Zero;
                    if (wq > w[i * k + bq]) bq = q;
                    if (wq <= 0 || b < 0 || b >= bindTo.Length) continue;
                    pp += bindTo[b] * v[i] * wq;
                    if (nr != null) nn += bindTo[b].Basis * nr[i] * wq;
                    sum += wq;
                }
                dom[i] = bo[i * k + bq];
                place[off + i] = Nv(sum > 1e-6f ? pp / sum : v[i]);
                nrm[off + i] = nr != null && nn.LengthSquared() > 1e-12f ? Nv(nn.Normalized()) : N.Vector3.UnitY;
                for (int q = 0; q < k; q++)
                    if (bo[i * k + q] is int b2 && (b2 < 0 || b2 >= bindTo.Length)) at[(off + i) * K + q] = place[off + i];
                for (int q = k; q < K; q++) at[(off + i) * K + q] = place[off + i];
            }
            if (readShapes && mesh is ArrayMesh am)
            {
                var sa = am.SurfaceGetBlendShapeArrays(s);
                for (int h = 0; h < shapes && h < sa.Count; h++)
                {
                    var sv = sa[h][(int)Mesh.ArrayType.Vertex];
                    if (sv.VariantType == Variant.Type.Nil) continue;
                    var a = sv.AsVector3Array();
                    if (a.Length != v.Length) continue;
                    var an = sa[h][(int)Mesh.ArrayType.Normal].VariantType == Variant.Type.Nil || nr == null ? null : sa[h][(int)Mesh.ArrayType.Normal].AsVector3Array();
                    sd[h] ??= new N.Vector3[total]; sdn[h] ??= new N.Vector3[total];
                    for (int i = 0; i < v.Length; i++)
                    {
                        var f = dom[i] >= 0 && dom[i] < bindTo.Length ? bindTo[dom[i]].Basis : Basis.Identity;
                        sd[h]![off + i] = Nv(f * (relative ? a[i] : a[i] - v[i]));
                        if (an != null && an.Length == v.Length) sdn[h]![off + i] = Nv(f * (relative ? an[i] : an[i] - nr![i]));
                    }
                }
            }
            off += v.Length;
        }
        var o = new PlateFollow.MeshIn { K = K, Place = place, Normal = nrm, Bone = bone, Weight = wt, At = at, ChannelBase = 0, ShapeD = sd, ShapeDn = sdn, Link = null };
        bodyCache[package] = o;
        GD.Print($"springs: {package}'s body for plate follow: {best.Name}, {total} vertices, {shapes} shapes");
        return (best, o);
    }

    static N.Vector3 Nv(Vector3 v) => new(v.X, v.Y, v.Z);
    static Vector3 Gv(N.Vector3 v) => new(v.X, v.Y, v.Z);
    static Quaternion Gq(N.Quaternion q) => new(q.X, q.Y, q.Z, q.W);
    static PlateFollow.Xf Xf(Transform3D t) => new(Nv(t.Basis.Column0), Nv(t.Basis.Column1), Nv(t.Basis.Column2), Nv(t.Origin));

    void Setup(Skeleton3D sk)
    {
        scale = sk.GlobalTransform.Basis.Scale.X;
        // the correctives: the bone, its reference, the meshes with the shape
        foreach (var c in correctives)
        {
            int b = sk.FindBone(c.Bone);
            if (b < 0) { GD.PushWarning($"springs: {what}'s corrective {c.Shape} has no bone {c.Bone}"); continue; }
            if (c.Axis != "pitch") { GD.PushWarning($"springs: {what}'s corrective {c.Shape}: axis {c.Axis} is not known (pitch)"); continue; }
            int r = c.Ref switch { "root" => -1, "parent" => sk.GetBoneParent(b), _ => sk.FindBone(c.Ref) };
            var on = new List<(MeshInstance3D, int)>();
            foreach (var mi in meshes)
                if (IsInstanceValid(mi) && mi.FindBlendShapeByName(c.Shape) is int i && i >= 0) on.Add((mi, i));
            if (on.Count == 0) GD.PushWarning($"springs: {what}'s corrective {c.Shape}: no mesh has the shape");
            drive.Add((b, r, sk.GetBoneGlobalRest(b).Basis.Y, r >= 0 ? sk.GetBoneGlobalRest(r) : Transform3D.Identity, c, on));
        }
        if (links.Count == 0) return;
        int n = links.Count;
        bone = links.Select(l => sk.FindBone(l.Bone)).ToArray();
        var idx = new Dictionary<string, int>();
        for (int i = 0; i < n; i++) idx[links[i].Bone] = i;
        parentLink = links.Select(l => idx.TryGetValue(l.Parent, out int pi) ? pi : -1).ToArray();
        bodyParent = bone.Select(b => sk.GetBoneParent(b)).ToArray();
        rest = bone.Select(b => sk.GetBoneRest(b)).ToArray();
        tailLocal = new Vector3[n];
        for (int i = 0; i < n; i++)
        {
            int child = Array.FindIndex(parentLink, p => p == i);
            tailLocal[i] = child >= 0 ? rest[child].Origin : sk.GetBoneGlobalRest(bone[i]).AffineInverse() * links[i].Tail;
        }
        var (lp, par, rootLink) = ClothChains.Order(links.Select(l => (l.Bone, l.Parent)).ToList());
        linkParticle = lp;
        headParticle = lp.Select(p => par[p]).ToArray();
        order = Enumerable.Range(0, n).OrderBy(i => lp[i]).ToArray();
        var radius = new float[par.Length];
        var stiffness = new float[par.Length];
        for (int i = 0; i < n; i++) { radius[lp[i]] = links[i].Radius * scale; stiffness[lp[i]] = links[i].Stiffness; }
        sim = new ClothChains(par, radius, ClothChains.Tuning.Wool, stiffness);
        if (followRow) SetupFollow(sk, par);
        rigid = new Transform3D[n]; posed = new Transform3D[n];
        targets = new N.Vector3[par.Length];
        cols = new ClothChains.Capsule[capsules.Length];
        worst = new float[capsules.Length];
        roots = Enumerable.Range(0, par.Length).Where(p => par[p] < 0).ToArray();
        lastRoot = new Vector3[roots.Length];
        lastRootBasis = new Basis[roots.Length];
        // (the bind: how close each link may come to each capsule)
        Targets(sk, true);
        sim.SetRest(targets, cols);
        Targets(sk, false);
        GD.Print($"springs: {what}: {n} links in {roots.Length} chains, {capsules.Length} body capsules, {drive.Count} correctives (pitch against {string.Join("/", correctives.Select(c => c.Ref))})");
    }
    int[] roots = Array.Empty<int>();
    bool setUp;

    /// <summary>The plates' follow (Play/PlateFollow): links as PlateFollow's, the piece meshes' and the body's data on
    /// one blend shape channel list (the body's shapes first), the chains' collider hooked into the sim. Falls back to
    /// the capsules' way (none here) when no link has a vertex.</summary>
    void SetupFollow(Skeleton3D sk, int[] par)
    {
        var pl = Enumerable.Range(0, links.Count).Select(i => new PlateFollow.Link(Nv(links[i].Head), Nv(links[i].Tail), parentLink[i])).ToList();
        int ch = 0;
        chans.Clear();
        if (bodyMi != null && bodyIn != null) { chans.Add((bodyMi, 0, bodyIn.ShapeD.Length)); ch = bodyIn.ShapeD.Length; }
        var pieces = new List<PlateFollow.MeshIn>();
        foreach (var mi in meshes)
        {
            if (!IsInstanceValid(mi) || mi.Name.ToString().StartsWith("lod_") || PieceCarry.FollowOf(mi) is not { } f) continue;
            // (a copy: the cached one is shared by every dress, its channel base is this node's)
            pieces.Add(new PlateFollow.MeshIn
            {
                K = f.K, Place = f.Place, Normal = f.Normal, Bone = f.Bone, Weight = f.Weight, At = f.At, ChannelBase = ch,
                ShapeD = f.ShapeD, ShapeDn = f.ShapeDn, Link = f.Link,
            });
            chans.Add((mi, ch, f.ShapeD.Length));
            ch += f.ShapeD.Length;
        }
        follow = PlateFollow.Build(pl, linkParticle, par, pieces, bodyIn, PlateFollow.Tuning.Plate);
        if (follow == null)
        {
            GD.PushWarning($"springs: {what}: follow: no plate vertices on its meshes, the links ride their bones");
            return;
        }
        chW = new float[ch];
        skinX = new PlateFollow.Xf[sk.GetBoneCount()];
        restInv = Enumerable.Range(0, skinX.Length).Select(b => sk.GetBoneGlobalRest(b).AffineInverse()).ToArray();
        sim!.Hook = follow.Collide;
        GD.Print($"springs: {what}: follow, {follow.Links} plates, {follow.PlatePoints} plate points, {follow.BodyPoints} body points");
    }

    /// <summary>PlateFollow's targets this frame (world), and each link's rigid place for the cut test.</summary>
    void FollowTargets(Skeleton3D sk)
    {
        var W = sk.GlobalTransform;
        for (int b = 0; b < skinX.Length; b++) skinX[b] = Xf(sk.GetBoneGlobalPose(b) * restInv[b]);
        foreach (var (mi, bs, n) in chans)
            if (IsInstanceValid(mi)) for (int s = 0; s < n; s++) chW[bs + s] = mi.GetBlendShapeValue(s);
        follow!.Update(skinX, Xf(W), chW, targets);
        var inv = W.AffineInverse();
        for (int i = 0; i < bone.Length; i++)
            rigid[i] = new Transform3D(new Basis(Gq(follow.Fitted(i))) * sk.GetBoneGlobalRest(bone[i]).Basis, inv * Gv(targets[headParticle[i]]));
    }

    /// <summary>Where each particle would be riding the body rigidly (world), and the capsules (world); at the bind's
    /// rest (bind) or the pose as it is.</summary>
    void Targets(Skeleton3D sk, bool bind)
    {
        if (follow != null && !bind) { FollowTargets(sk); return; }
        var W = sk.GlobalTransform;
        Transform3D G(int b) => bind ? sk.GetBoneGlobalRest(b) : sk.GetBoneGlobalPose(b);
        foreach (int i in order)
        {
            var parent = parentLink[i] >= 0 ? rigid[parentLink[i]] : G(bodyParent[i]);
            rigid[i] = parent * rest[i];
            targets[linkParticle[i]] = Nv(W * (rigid[i] * tailLocal[i]));
            if (parentLink[i] < 0) targets[headParticle[i]] = Nv(W * rigid[i].Origin);
        }
        for (int c = 0; c < capsules.Length; c++)
            cols[c] = new ClothChains.Capsule(Nv(W * G(capsules[c].A).Origin), Nv(W * G(capsules[c].B).Origin), capsules[c].R * scale);
    }

    /// <summary>Kept last of its skeleton's modifiers (over the finished pose: joints, jiggle, arm sets), as a modifier
    /// added after it (her live swap, a dev probe) would read its swing before its own; GazeCarry stays after it (a head
    /// look). On B (P1Laws) the laws keep the order (P1Laws.Reorder: the springs after them).</summary>
    public override void _Ready()
    {
        if (GetParent() is Skeleton3D sk) { sk.ChildEnteredTree += OnSibling; keptOn = sk; }
    }
    public override void _ExitTree() { if (keptOn != null) keptOn.ChildEnteredTree -= OnSibling; keptOn = null; }
    Skeleton3D? keptOn;
    bool keepQueued;
    void OnSibling(Node n)
    {
        if (n is not SkeletonModifier3D || n is PieceSprings || n is GazeCarry || keepQueued) return;
        keepQueued = true;
        Callable.From(KeepLast).CallDeferred();
    }
    /// <summary>Every piece's springs after the other modifiers (P1Laws' bodies excepted), GazeCarry after them.</summary>
    public static void KeepLast(Skeleton3D sk)
    {
        if (sk.GetNodeOrNull("P1Laws") != null) return;
        foreach (var m in sk.GetChildren().OfType<PieceSprings>().ToList()) sk.MoveChild(m, -1);
        foreach (var m in sk.GetChildren().OfType<GazeCarry>().ToList()) sk.MoveChild(m, -1);
    }
    void KeepLast()
    {
        keepQueued = false;
        if (IsInstanceValid(this) && GetParent() is Skeleton3D sk) KeepLast(sk);
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (!setUp) { setUp = true; Setup(sk); }
        if (from != null) Took();
        if (sim != null) Swing(sk, (float)delta);
        Drive(sk);
    }

    void Swing(Skeleton3D sk, float dt)
    {
        if (sim == null) return;
        long t0 = Debug ? System.Diagnostics.Stopwatch.GetTimestamp() : 0;
        Targets(sk, false);
        var W = sk.GlobalTransform;
        // (a cut: the camera changed or jumped; the body jumped; a long frame)
        var cam = GetViewport()?.GetCamera3D();
        if (cam != null)
        {
            var ct = cam.GlobalTransform;
            if (!cut && lastCam != null && (cam != lastCam || ct.Origin.DistanceTo(lastCamAt.Origin) > Math.Max(1.0f, 25 * dt)
                || ct.Basis.GetRotationQuaternion().AngleTo(lastCamAt.Basis.GetRotationQuaternion()) > Mathf.DegToRad(25)))
            { cut = true; why = cam != lastCam ? "camera changed" : "camera jumped"; }
            lastCam = cam; lastCamAt = ct;
        }
        for (int r = 0; r < roots.Length; r++)
        {
            var at = Gv(targets[roots[r]]);
            int li = Array.FindIndex(headParticle, h => h == roots[r]);
            var basis = (W.Basis * rigid[li].Basis).Orthonormalized();
            if (!cut && life > 0 && tookGrace <= 0 && (at.DistanceTo(lastRoot[r]) > Math.Max(0.35f * scale, 12 * dt)
                || basis.GetRotationQuaternion().AngleTo(lastRootBasis[r].GetRotationQuaternion()) > Mathf.DegToRad(40)))
            { cut = true; why = "the body jumped"; }
            lastRoot[r] = at; lastRootBasis[r] = basis;
        }
        if (dt > 0.25f && !cut && tookGrace <= 0) { cut = true; why = $"a {dt:0.00} s frame"; }
        if (tookGrace > 0) tookGrace--;
        var down = Nv(-Vector3.Up);
        float? ground = W.Origin.Y;
        if (cut || dt <= 0)
        {
            if (dt <= 0 && !cut) { Write(sk); return; }
            if (follow != null) { follow.Cut(); Targets(sk, false); }
            sim.Reset(targets, cols, ground, down);
            if (Debug) GD.Print($"springs: {what}: reset ({why}) at {life:0.00} s");
            cut = false;
            sinceReset = 0;
            resetX = sim.Positions.ToArray(); resetT = (N.Vector3[])targets.Clone();
        }
        else sim.Step(dt, targets, cols, ground, down);
        life += dt;
        Write(sk);
        if (Debug) { swingTicks += System.Diagnostics.Stopwatch.GetTimestamp() - t0; swingFrames++; Measure(sk, dt); }
    }

    /// <summary>Each spring bone turned from riding rigidly to point at its simulated tail.</summary>
    void Write(Skeleton3D sk)
    {
        var inv = sk.GlobalTransform.AffineInverse();
        var x = sim!.Positions;
        foreach (int i in order)
        {
            var parent = parentLink[i] >= 0 ? posed[parentLink[i]] : sk.GetBoneGlobalPose(bodyParent[i]);
            Transform3D g;
            if (follow != null)
            {
                // (the plates' own fit turned to point at the tail particle, hinged at its head particle)
                var (turn, head) = follow.Pose(i, x);
                g = new Transform3D(new Basis(Gq(turn)) * sk.GetBoneGlobalRest(bone[i]).Basis, Gv(head));
            }
            else
            {
                g = parent * rest[i];
                var want = inv * Gv(x[linkParticle[i]]) - g.Origin;
                var have = g.Basis * tailLocal[i];
                if (want.LengthSquared() > 1e-12f && have.LengthSquared() > 1e-12f)
                {
                    var q = new Quaternion(have.Normalized(), want.Normalized());
                    g = new Transform3D(new Basis(q) * g.Basis, g.Origin);
                }
            }
            posed[i] = g;
            var local = parent.AffineInverse() * g;
            sk.SetBonePoseRotation(bone[i], local.Basis.GetRotationQuaternion());
            sk.SetBonePosePosition(bone[i], local.Origin);
        }
    }

    float Pitch(Skeleton3D sk, (int Bone, int Ref, Vector3 BoneRest, Transform3D RefRest, Corrective C, List<(MeshInstance3D Mi, int Shape)> On) d, int refBone, Transform3D refRest)
    {
        var now = sk.GetBoneGlobalPose(d.Bone).Basis.Y;
        if (refBone >= 0) now = refRest.Basis * (sk.GetBoneGlobalPose(refBone).Basis.Inverse() * now);
        return ClothChains.Pitch(Nv(d.BoneRest), Nv(now));
    }

    void Drive(Skeleton3D sk)
    {
        foreach (var d in drive)
        {
            float deg = Pitch(sk, d, d.Ref, d.RefRest);
            float w = ClothChains.Weight(deg, d.C.From, d.C.To);
            foreach (var (mi, i) in d.On) if (IsInstanceValid(mi)) mi.SetBlendShapeValue(i, w);
        }
    }

    void Measure(Skeleton3D sk, float dt)
    {
        var pen = sim!.Penetration(cols);
        for (int c = 0; c < pen.Length; c++) worst[c] = Math.Max(worst[c], pen[c]);
        if (sinceReset >= 0 && sinceReset < 3)
        {
            // (the first frames' swing: how far the chains moved off riding the body since the reset, cm, package units)
            float sw = 0;
            for (int i = 0; i < resetX.Length; i++) sw = Math.Max(sw, ((sim.Positions[i] - resetX[i]) - (targets[i] - resetT[i])).Length());
            GD.Print($"springs: {what}: frame {sinceReset + 1} after the reset: swing {sw / scale * 100:0.00} cm");
            sinceReset++;
        }
        dbgT += dt;
        if (dbgT < 1) return;
        dbgT = 0;
        string Cm(float v) => (v / scale * 100).ToString("0.0");
        var parts = new List<string>();
        for (int c = 0; c < capsules.Length; c++) parts.Add($"{sk.GetBoneName(capsules[c].A)} {Cm(worst[c])}");
        string pitch = string.Join(" ", drive.Select(d =>
            $"{d.C.Shape} root {Pitch(sk, d, -1, Transform3D.Identity):0} parent {Pitch(sk, d, sk.GetBoneParent(d.Bone), sk.GetBoneGlobalRest(sk.GetBoneParent(d.Bone))):0}"
            + (sk.FindBone("pelvis") is int pv && pv >= 0 ? $" pelvis {Pitch(sk, d, pv, sk.GetBoneGlobalRest(pv)):0}" : "")
            + $" w {ClothChains.Weight(Pitch(sk, d, d.Ref, d.RefRest), d.C.From, d.C.To):0.00}"));
        GD.Print($"springs: {what} t {life:0.0} inside (cm, worst so far) {string.Join(", ", parts)}; {pitch}"
            + (follow != null ? $" follow pushes {follow.Pushes} deepest {follow.Deepest * 100:0.0} cm" : "")
            + $"; {swingTicks * 1000.0 / System.Diagnostics.Stopwatch.Frequency / Math.Max(1, swingFrames):0.00} ms a frame");
        swingTicks = 0; swingFrames = 0;
    }
}
