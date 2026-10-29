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
/// swings as slowly as its length makes it) kept off capsules on the body's legs, pelvis and spine (radii measured from
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

    /// <summary>The body's capsules (bone to bone): the legs a hanging back piece swings against, the pelvis and spine it
    /// drapes over.</summary>
    static readonly (string A, string B)[] Body =
    {
        ("thigh_l", "calf_l"), ("calf_l", "foot_l"), ("thigh_r", "calf_r"), ("calf_r", "foot_r"),
        ("pelvis", "spine_01"), ("spine_01", "spine_02"), ("spine_02", "spine_03"), ("spine_03", "neck_01"),
    };
    static readonly Dictionary<string, (int A, int B, float R)[]> capsuleCache = new();
    public static readonly bool Debug = System.Environment.GetEnvironmentVariable("PIECE_SPRINGS_DBG") == "1";
    public static readonly bool Off = Args.Get("springs") == "off" || System.Environment.GetEnvironmentVariable("PIECE_SPRINGS") == "0";

    readonly string what;
    readonly List<Link> links;
    readonly List<Corrective> correctives;
    readonly List<MeshInstance3D> meshes;
    readonly (int A, int B, float R)[] capsules;   // (skeleton units)

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

    PieceSprings(string what, List<Link> links, List<Corrective> correctives, List<MeshInstance3D> meshes, (int, int, float)[] capsules)
    {
        Name = "PieceSprings_" + what.Replace('/', '_');
        this.what = what; this.links = links; this.correctives = correctives; this.meshes = meshes; this.capsules = capsules;
    }

    /// <summary>Starts the chains afresh on the next frame, at a settled hang (a cinematic's cut).</summary>
    public void Cut() { cut = true; why = "Cut()"; }

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
        return o;
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
        List<MeshInstance3D> pieceMeshes, Transform3D pkgToSkel)
    {
        if (Off || (links.Count == 0 && correctives.Count == 0)) return null;
        var sk = p.Skeleton;
        // (each link's head and tail into the skeleton's frame; its radius by the frame's scale)
        float fs = pkgToSkel.Basis.Scale.X;
        var ls = links.Where(l => sk.FindBone(l.Bone) >= 0)
            .Select(l => l with { Head = pkgToSkel * l.Head, Tail = pkgToSkel * l.Tail, Radius = l.Radius * fs }).ToList();
        var caps = ls.Count > 0 ? Capsules(p, package) : Array.Empty<(int, int, float)>();
        var m = new PieceSprings(what, ls, correctives, pieceMeshes, caps);
        sk.AddChild(m);
        return m;
    }

    /// <summary>The body's capsules (Body) with radii from its mesh: of the vertices each bone carries most (at the
    /// bind), the 80th percentile of their distance off its segment (robe and all), once a package.</summary>
    static (int A, int B, float R)[] Capsules(People.Person p, string package)
    {
        if (capsuleCache.TryGetValue(package, out var have)) return have;
        var sk = p.Skeleton;
        var segs = Body.Select(x => (A: sk.FindBone(x.A), B: sk.FindBone(x.B))).Where(x => x.A >= 0 && x.B >= 0).ToArray();
        var dist = segs.Select(_ => new List<float>()).ToArray();
        var byBone = new Dictionary<int, int>();
        for (int i = 0; i < segs.Length; i++) byBone.TryAdd(segs[i].A, i);
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
            var l = dist[c];
            if (l.Count < 20) continue;
            l.Sort();
            float r = Math.Clamp(l[(int)(l.Count * 0.8f)], 0.03f, 0.3f);
            o.Add((segs[c].A, segs[c].B, r));
        }
        GD.Print($"springs: {package}'s body capsules " + string.Join(", ", o.Select(x => $"{sk.GetBoneName(x.Item1)}-{sk.GetBoneName(x.Item2)} r{x.Item3 * 100:0.0} cm")));
        return capsuleCache[package] = o.ToArray();
    }

    static N.Vector3 Nv(Vector3 v) => new(v.X, v.Y, v.Z);
    static Vector3 Gv(N.Vector3 v) => new(v.X, v.Y, v.Z);

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

    /// <summary>Where each particle would be riding the body rigidly (world), and the capsules (world); at the bind's
    /// rest (bind) or the pose as it is.</summary>
    void Targets(Skeleton3D sk, bool bind)
    {
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

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (!setUp) { setUp = true; Setup(sk); }
        if (sim != null) Swing(sk, (float)delta);
        Drive(sk);
    }

    void Swing(Skeleton3D sk, float dt)
    {
        if (sim == null) return;
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
            if (!cut && life > 0 && (at.DistanceTo(lastRoot[r]) > Math.Max(0.35f * scale, 12 * dt)
                || basis.GetRotationQuaternion().AngleTo(lastRootBasis[r].GetRotationQuaternion()) > Mathf.DegToRad(40)))
            { cut = true; why = "the body jumped"; }
            lastRoot[r] = at; lastRootBasis[r] = basis;
        }
        if (dt > 0.25f && !cut) { cut = true; why = $"a {dt:0.00} s frame"; }
        var down = Nv(-Vector3.Up);
        float? ground = W.Origin.Y;
        if (cut || dt <= 0)
        {
            if (dt <= 0 && !cut) { Write(sk); return; }
            sim.Reset(targets, cols, ground, down);
            if (Debug) GD.Print($"springs: {what}: reset ({why}) at {life:0.00} s");
            cut = false;
            sinceReset = 0;
            resetX = sim.Positions.ToArray(); resetT = (N.Vector3[])targets.Clone();
        }
        else sim.Step(dt, targets, cols, ground, down);
        life += dt;
        Write(sk);
        if (Debug) Measure(sk, dt);
    }

    /// <summary>Each spring bone turned from riding rigidly to point at its simulated tail.</summary>
    void Write(Skeleton3D sk)
    {
        var inv = sk.GlobalTransform.AffineInverse();
        var x = sim!.Positions;
        foreach (int i in order)
        {
            var parent = parentLink[i] >= 0 ? posed[parentLink[i]] : sk.GetBoneGlobalPose(bodyParent[i]);
            var g = parent * rest[i];
            var want = inv * Gv(x[linkParticle[i]]) - g.Origin;
            var have = g.Basis * tailLocal[i];
            if (want.LengthSquared() > 1e-12f && have.LengthSquared() > 1e-12f)
            {
                var q = new Quaternion(have.Normalized(), want.Normalized());
                g = new Transform3D(new Basis(q) * g.Basis, g.Origin);
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
        GD.Print($"springs: {what} t {life:0.0} inside (cm, worst so far) {string.Join(", ", parts)}; {pitch}");
    }
}
