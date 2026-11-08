using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// P1's body B (tools/body; published by tools/body/publish_p1.py into art/people/body_p1) in the game behind
/// --body p1; A (heroine.glb) stays the default and is untouched. Under the flag B is the actor: body.glb's scene is
/// her root (the same Armature/Skeleton3D path as A's, so every track and filter path holds), her skeleton plays the
/// clips baked onto it offline (clips.res, her_clips.res: the clip bridge, tools/body/bake_clips.sh), and B's own laws
/// (P1Laws: P1Rig.Drive, rig.json) are its only deformation layers; A is not loaded. Systems keyed to A's bone names
/// ask Bone (A's role map, P1Retarget.Role on a_skeleton.json: B's spine_03 is mid-back, A's chest is B's spine_05);
/// meshes laid later on her skeleton skinned to A (her hair, a head piece) are rebound to B once (Rebind). Play tier:
/// play.glb's body on the same skeleton (lod_p1_body), switched by HerLod's rule, its correctives by play_rig.json.
/// Derivation: (a) the owner's rebuild ("B is the actor", 5 Nov) and the rule A default, B only behind a flag;
/// (c) inherited: HerLod's switch, headbake's rebind transform.
/// </summary>
public static class P1Body
{
    public const string Dir = "res://art/people/body_p1/";
    /// <summary>--body p1, and a published B (with its baked clips) to load.</summary>
    public static bool On => Args.Get("body") == "p1" && ResourceLoader.Exists(Dir + "body.glb") && ResourceLoader.Exists(Dir + "clips.res");
    static PackedScene? close, play;
    static readonly Dictionary<string, JsonDocument> rigs = new();
    static AnimationLibrary? clips, herClips;

    public static JsonElement Rig(string file)
    {
        if (!rigs.TryGetValue(file, out var d))
            rigs[file] = d = JsonDocument.Parse(FileAccess.GetFileAsString(Dir + file));
        return d.RootElement;
    }

    /// <summary>The published spec's "skin" block (publish.json): B's placeholder skin settings on its body material, her head left alone. The skin's rim and its glancing sheen drew a lit line round every form at the Look, whatever the shape (P1 R1 round 7, measured with --skin-set).</summary>
    public static void ApplySkin(ShaderMaterial m)
    {
        // (B's cavity map (its own baked AO about her armpits, topo_bake cavity_keep) as the skin's cavity_map: there it takes
        // a bounce of the lamps' light where they can't reach (heroine_skin.gdshader's cavity_bounce, the spec's "skin");
        // P1 R1 round 33, S3, the armpit blot)
        if (ResourceLoader.Exists(Dir + "cavity.png")) m.SetShaderParameter("cavity_map", GD.Load<Texture2D>(Dir + "cavity.png"));
        if (!Rig("publish.json").TryGetProperty("skin", out var skin) || skin.ValueKind != JsonValueKind.Object) return;
        foreach (var kv in skin.EnumerateObject()) m.SetShaderParameter(kv.Name, kv.Value.GetSingle());
    }

    /// <summary>The library clips baked onto B (People.Clips' names, loops as set there).</summary>
    public static AnimationLibrary Clips()
    {
        if (clips != null) return clips;
        clips = GD.Load<AnimationLibrary>(Dir + "clips.res");
        foreach (var name in clips.GetAnimationList())
            if (People.IsCycle(name)) clips.GetAnimation(name).LoopMode = Animation.LoopModeEnum.Linear;
        return clips;
    }

    /// <summary>Her own clips baked onto B (OwnClips.Her's names; its meta stays heroine_clips.json).</summary>
    public static AnimationLibrary? HerClips() => herClips ??= ResourceLoader.Exists(Dir + "her_clips.res") ? GD.Load<AnimationLibrary>(Dir + "her_clips.res") : null;

    // ------------------------------------------------------------------ A's skeleton and the role map --
    /// <summary>A's skeleton as a_skeleton.json has it (the clip bridge writes it from heroine.glb).</summary>
    public sealed record ASkeleton(string[] Names, int[] Parent, P1M4[] Rest, Dictionary<string, int> Index);
    static ASkeleton? aSkel;
    public static ASkeleton A
    {
        get
        {
            if (aSkel != null) return aSkel;
            using var d = JsonDocument.Parse(FileAccess.GetFileAsString(Dir + "a_skeleton.json"));
            var r = d.RootElement;
            var names = r.GetProperty("names").EnumerateArray().Select(x => x.GetString()!).ToArray();
            var parent = r.GetProperty("parent").EnumerateArray().Select(x => x.GetInt32()).ToArray();
            var rest = r.GetProperty("rest").EnumerateArray().Select(m => P1M4.FromRows(m.EnumerateArray().SelectMany(row => row.EnumerateArray()).Select(x => x.GetDouble()).ToArray())).ToArray();
            var index = new Dictionary<string, int>();
            for (int i = 0; i < names.Length; i++) index[names[i]] = i;
            return aSkel = new ASkeleton(names, parent, rest, index);
        }
    }

    static P1Rig? bRig;
    static P1Retarget? role;
    /// <summary>B's rig (rig.json) on B's skeleton (every B skeleton is body.glb's: one, cached).</summary>
    public static P1Rig RigOf(Skeleton3D b)
    {
        if (bRig != null) return bRig;
        int n = b.GetBoneCount();
        return bRig = new P1Rig(Enumerable.Range(0, n).Select(i => b.GetBoneName(i)).ToArray(), Enumerable.Range(0, n).Select(i => b.GetBoneParent(i)).ToArray(),
            Enumerable.Range(0, n).Select(i => M(b.GetBoneGlobalRest(i))).ToArray(), Rig("rig.json"));
    }

    public static P1Retarget RoleMap(Skeleton3D b) => role ??= new P1Retarget(A.Names, A.Parent, A.Rest, RigOf(b));

    /// <summary>B's skeleton (body.glb's, under the flag).</summary>
    public static bool IsB(Skeleton3D? sk) => sk != null && sk.HasMeta("p1_b");

    static Vector3? eyesFromHead;
    /// <summary>Where the cameras aim on B's head at rest, from her Head joint (skeleton space), once: the point A's
    /// cameras aim at on A's (People.HerEyesOffset over A's Head rest, a_skeleton.json), since B's head IS A's head at
    /// A's world rest; the HeroineEyes mesh's box centre only without A's rest. (P1 A round 14: the eyes' box centre
    /// sits 7.8 mm over and 7.3 mm in front of A's aim, so the Look framed B 7.8 mm lower than A, breasts and all.)</summary>
    public static Vector3 EyesFromHead(Skeleton3D sk)
    {
        if (eyesFromHead is Vector3 e) return e;
        var head = sk.GetBoneGlobalRest(sk.FindBone("Head")).Origin;
        if (ARest("Head") is Transform3D aHead) { eyesFromHead = aHead.Origin + People.HerEyesOffset - head; return eyesFromHead.Value; }
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>())
            if (mi.Name == "HeroineEyes" && mi.Mesh != null) { var c = mi.Mesh.GetAabb().GetCenter(); eyesFromHead = c - head; return c - head; }
        return new Vector3(0, 0.082f, 0.111f);
    }

    /// <summary>The bone that plays A bone aName's part on this skeleton: FindBone on A (and anyone else); on B the role
    /// map (spine_03 -> B's chest, spine_05; neck_01 -> its B bone; limbs by name; panel_front -> its nearest ancestor's).</summary>
    public static int Bone(Skeleton3D sk, string aName)
    {
        if (!IsB(sk) || !A.Index.TryGetValue(aName, out int a)) return sk.FindBone(aName);
        return RoleMap(sk).Role(a);
    }

    /// <summary>Bone's name (a BoneAttachment's BoneName).</summary>
    public static string BoneName(Skeleton3D sk, string aName) => IsB(sk) && Bone(sk, aName) is int j and >= 0 ? sk.GetBoneName(j) : aName;

    /// <summary>Turn shares laid on A's chain bones, as bone indices: on B spread over its chain by role, the total kept.</summary>
    public static (int Bone, float Share)[] Spread(Skeleton3D sk, (string Bone, float Share)[] shares)
    {
        if (!IsB(sk)) return shares.Select(s => (sk.FindBone(s.Bone), s.Share)).ToArray();
        return RoleMap(sk).Spread(shares.Select(s => (s.Bone, (double)s.Share))).Select(s => (s.B, (float)s.Share)).ToArray();
    }

    /// <summary>A bone's A rest (skeleton space) as a_skeleton.json has it; null if A has none.</summary>
    public static Transform3D? ARest(string aName) => A.Index.TryGetValue(aName, out int a) ? T(A.Rest[a]) : null;

    // ------------------------------------------------------------------ her root under the flag --
    /// <summary>B as her root: body.glb's scene (its meshes on its skeleton), play.glb's body on the same skeleton
    /// (lod_p1_body, hidden till HerLod's rule), the skeleton marked as B's.</summary>
    public static Node3D Load(out Skeleton3D skel)
    {
        close ??= GD.Load<PackedScene>(Dir + "body.glb");
        var root = close.Instantiate<Node3D>();
        skel = (Skeleton3D)root.FindChildren("*", "Skeleton3D", true, false)[0];
        skel.SetMeta("p1_b", true);
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>()) mi.SetMeta("p1_b", true);
        int meshes = skel.GetChildren().OfType<MeshInstance3D>().Count();
        string tier = "none";
        if (ResourceLoader.Exists(Dir + "play.glb"))
        {
            play ??= GD.Load<PackedScene>(Dir + "play.glb");
            var ps = play.Instantiate<Node3D>();
            var bp = (Skeleton3D)ps.FindChildren("*", "Skeleton3D", true, false)[0];
            tier = SameRest(skel, bp);
            if (bp.GetNodeOrNull<MeshInstance3D>("Heroine") is MeshInstance3D lod)
            {
                bp.RemoveChild(lod);
                lod.Owner = null;
                lod.Name = "lod_p1_body";
                lod.Visible = false;
                lod.SetMeta("p1_b", true);
                skel.AddChild(lod);
                lod.Skeleton = "..";
            }
            ps.Free();
        }
        GD.Print($"p1: B native ({meshes} meshes, {skel.GetBoneCount()} bones at {root.GetPathTo(skel)}; play tier {tier})");
        return root;
    }

    /// <summary>play.glb's rests against body.glb's (one skeleton for both tiers): 0.1 mm, 0.01 deg.</summary>
    static string SameRest(Skeleton3D b, Skeleton3D p)
    {
        double dt = 0, da = 0; int missing = 0;
        for (int i = 0; i < p.GetBoneCount(); i++)
        {
            int j = b.FindBone(p.GetBoneName(i));
            if (j < 0) { missing++; continue; }
            var x = b.GetBoneGlobalRest(j); var y = p.GetBoneGlobalRest(i);
            dt = System.Math.Max(dt, x.Origin.DistanceTo(y.Origin));
            da = System.Math.Max(da, Mathf.RadToDeg(x.Basis.Orthonormalized().GetRotationQuaternion().AngleTo(y.Basis.Orthonormalized().GetRotationQuaternion())));
        }
        bool same = dt <= 1e-4 && da <= 0.01 && missing == 0 && p.GetBoneCount() == b.GetBoneCount();
        if (!same) GD.PushWarning($"p1: play.glb's skeleton is not body.glb's: rests off up to {dt * 1000:F2} mm, {da:F3} deg, {missing} bones missing ({p.GetBoneCount()} vs {b.GetBoneCount()})");
        return same ? "on (rests equal)" : $"on (rests off {dt * 1000:F2} mm {da:F3} deg)";
    }

    // ------------------------------------------------------------------ meshes skinned to A --
    /// <summary>A mesh laid on B's skeleton but skinned to A's bones (her hair, a head piece) taken onto B, once: each
    /// bind pose to inverse(B rest[role]) A rest bind, so at rest it is exactly where A draws it, and it moves with the
    /// B bone that plays its A bone's part. Marked (meta p1_rebound); B's own meshes (meta p1_b) are left.</summary>
    public static void Rebind(Skeleton3D b, MeshInstance3D mi)
    {
        if (!IsB(b) || mi.HasMeta("p1_b") || mi.HasMeta("p1_rebound") || mi.Skin is not Skin skin) return;
        mi.SetMeta("p1_rebound", true);
        var rig = RigOf(b); var map = RoleMap(b);
        var nw = new Skin();
        for (int i = 0; i < skin.GetBindCount(); i++)
        {
            string nm = skin.GetBindName(i);
            int ai = nm != "" ? (A.Index.TryGetValue(nm, out int k) ? k : -1) : skin.GetBindBone(i);
            int bi = ai >= 0 && ai < A.Names.Length ? map.Role(ai) : (nm != "" ? b.FindBone(nm) : -1);
            if (ai < 0 || ai >= A.Names.Length || bi < 0) { nw.AddNamedBind(bi >= 0 ? b.GetBoneName(bi) : b.GetBoneName(0), skin.GetBindPose(i)); continue; }
            nw.AddNamedBind(b.GetBoneName(bi), T(rig.Rest[bi].Inverse() * A.Rest[ai] * M(skin.GetBindPose(i))));
        }
        if (Args.Has("p1-probe")) HairFit(b, mi, skin, nw);
        mi.Skin = nw;
        if (Args.Has("p1-probe")) GD.Print($"p1: {mi.Name} rebound to B ({skin.GetBindCount()} binds)");
    }

    /// <summary>(--p1-probe) A mesh's rest world as A draws it (old skin, A's rest) against B (new skin, B's rest): the
    /// bounding boxes' corners and the worst vertex, mm; and its centroid from B's Head joint.</summary>
    static void HairFit(Skeleton3D b, MeshInstance3D mi, Skin was, Skin now)
    {
        var arr = mi.Mesh.SurfaceGetArrays(0);
        var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
        var bo = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
        var we = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
        if (v.Length == 0 || bo.Length == 0) return;
        int per = bo.Length / v.Length;
        Vector3 Skinned(Skin sk, bool onA, int i)
        {
            var acc = Vector3.Zero;
            for (int k = 0; k < per; k++)
            {
                float wk = we[i * per + k];
                if (wk == 0) continue;
                int bind = bo[i * per + k];
                string nm = sk.GetBindName(bind);
                Transform3D rest;
                if (onA) { int a = nm != "" && A.Index.TryGetValue(nm, out int q) ? q : sk.GetBindBone(bind); rest = a >= 0 && a < A.Names.Length ? T(A.Rest[a]) : Transform3D.Identity; }
                else { int j = b.FindBone(nm); rest = j >= 0 ? b.GetBoneGlobalRest(j) : Transform3D.Identity; }
                acc += wk * (rest * sk.GetBindPose(bind) * v[i]);
            }
            return acc;
        }
        Vector3 lo1 = Vector3.One * 1e9f, hi1 = -lo1, lo2 = lo1, hi2 = hi1, sum = Vector3.Zero;
        float worst = 0;
        for (int i = 0; i < v.Length; i++)
        {
            var p1 = Skinned(was, true, i); var p2 = Skinned(now, false, i);
            lo1 = lo1.Min(p1); hi1 = hi1.Max(p1); lo2 = lo2.Min(p2); hi2 = hi2.Max(p2); sum += p2;
            worst = Mathf.Max(worst, p1.DistanceTo(p2));
        }
        var dl = (lo1 - lo2).Abs(); var dh = (hi1 - hi2).Abs();
        float box = Mathf.Max(Mathf.Max(dl.X, Mathf.Max(dl.Y, dl.Z)), Mathf.Max(dh.X, Mathf.Max(dh.Y, dh.Z)));
        var head = b.GetBoneGlobalRest(b.FindBone("Head")).Origin;
        GD.Print($"p1: hair fit {mi.Name}: {v.Length} verts, A box {hi1 - lo1} m, bbox corners off {box * 1000:F4} mm, worst vertex {worst * 1000:F4} mm; " +
                 $"centroid from B's Head joint {(sum / v.Length - head) * 1000} mm");
    }

    // ------------------------------------------------------------------ skin-tight pieces --
    record struct PieceB(Mesh Mesh, Skin Skin, string Tier, int Verts);
    static Dictionary<string, List<PieceB>>? pieces;

    /// <summary>B's carries of A's skin-tight pieces (pieces.glb + pieces.json: tools/body/skin_pieces.py, the ink slot),
    /// by the A node's name as Godot imports it; their skins' binds named by B's bones.</summary>
    static Dictionary<string, List<PieceB>> Pieces()
    {
        if (pieces != null) return pieces;
        pieces = new();
        if (!ResourceLoader.Exists(Dir + "pieces.glb") || !FileAccess.FileExists(Dir + "pieces.json")) return pieces;
        var doc = Rig("pieces.json").GetProperty("pieces");
        var scene = GD.Load<PackedScene>(Dir + "pieces.glb").Instantiate<Node3D>();
        foreach (var mi in scene.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>())
        {
            if (!doc.TryGetProperty(mi.Name.ToString(), out var r) || r.TryGetProperty("missing", out _) || mi.Skin == null || mi.Mesh == null) continue;
            var ps = mi.GetNode<Skeleton3D>(mi.Skeleton);
            var skin = new Skin();
            for (int i = 0; i < mi.Skin.GetBindCount(); i++)
            {
                string nm = mi.Skin.GetBindName(i);
                skin.AddNamedBind(nm != "" ? nm : ps.GetBoneName(mi.Skin.GetBindBone(i)), mi.Skin.GetBindPose(i));
            }
            string a = r.GetProperty("a_godot_name").GetString()!;
            if (!pieces.TryGetValue(a, out var l)) pieces[a] = l = new List<PieceB>();
            l.Add(new PieceB(mi.Mesh, skin, r.GetProperty("tier").GetString()!, r.GetProperty("verts").GetInt32()));
        }
        scene.Free();
        GD.Print($"p1: {pieces.Values.Sum(l => l.Count)} skin-tight pieces carried onto B ({string.Join(", ", pieces.Keys)})");
        return pieces;
    }

    /// <summary>A's skin-tight piece (an ink-slot mesh laid on her skeleton by HerWear or HerLod) made B's: the node,
    /// its slot rules, its material overrides and its mesh's surface materials kept; its mesh and skin B's carry
    /// (P1Laws keeps its blend shapes at its body's). Null if B carries no such piece.</summary>
    public static string? Piece(Skeleton3D b, MeshInstance3D mi)
    {
        if (!IsB(b) || mi.Mesh == null || !Pieces().TryGetValue(mi.Name.ToString(), out var list)) return null;
        int nv = mi.Mesh is ArrayMesh am && am.GetSurfaceCount() > 0 ? am.SurfaceGetArrayLen(0) : (mi.Mesh.GetSurfaceCount() > 0 ? mi.Mesh.SurfaceGetArrays(0)[(int)Mesh.ArrayType.Vertex].AsVector3Array().Length : -1);
        var c = list.FirstOrDefault(x => x.Verts == nv);
        if (c.Mesh == null) { if (list.Count != 1) return null; c = list[0]; }
        var m = (Mesh)c.Mesh.Duplicate();
        for (int s = 0; s < m.GetSurfaceCount() && s < mi.Mesh.GetSurfaceCount(); s++) m.SurfaceSetMaterial(s, mi.Mesh.SurfaceGetMaterial(s));
        mi.Mesh = m;
        mi.Skin = c.Skin;
        mi.SetMeta("p1_piece", c.Tier);
        if (Args.Has("p1-probe")) GD.Print($"p1: {mi.Name} (A's, {nv} verts) worn as B's carry ({c.Tier} tier, {m.GetSurfaceCount()} surfaces)");
        return c.Tier;
    }

    public static P1M4 M(Transform3D t)
    {
        var m = P1M4.Id;
        var c = new[] { t.Basis.Column0, t.Basis.Column1, t.Basis.Column2 };
        for (int k = 0; k < 3; k++) { m[0, k] = c[k].X; m[1, k] = c[k].Y; m[2, k] = c[k].Z; }
        m[0, 3] = t.Origin.X; m[1, 3] = t.Origin.Y; m[2, 3] = t.Origin.Z;
        return m;
    }

    public static Transform3D T(P1M4 m) => new(
        new Basis(new Vector3((float)m[0, 0], (float)m[1, 0], (float)m[2, 0]), new Vector3((float)m[0, 1], (float)m[1, 1], (float)m[2, 1]),
                  new Vector3((float)m[0, 2], (float)m[1, 2], (float)m[2, 2])),
        new Vector3((float)m[0, 3], (float)m[1, 3], (float)m[2, 3]));
}

/// <summary>
/// B's own laws on B's skeleton, after every pose-writing modifier and before P1Jiggle and HerFaceLife (kept so as
/// children are added: PlayerView's carriage, holds, head turns): B's helpers carried at rest from their parents,
/// P1Rig.Drive (rig.json: the girdle from the arm, the helper rows, the correctives), the bones it changed written
/// back as local poses, the corrective shape weights set on the close meshes (and on the play body by its own rig,
/// play_rig.json, while it draws). Also: the play tier's switch (HerLod's rule), meshes skinned to A rebound or
/// left off (P1Body.Rebind), and the --p1-probe lines every 120 frames.
/// </summary>
public partial class P1Laws : SkeletonModifier3D
{
    Skeleton3D? sk;
    P1Rig? rig, playRig;
    int[] order = System.Array.Empty<int>();
    P1M4[] restLocal = System.Array.Empty<P1M4>();
    MeshInstance3D? body, lod;
    readonly List<MeshInstance3D> closeMeshes = new();
    /// <summary>A's skin-tight pieces worn as B's carries (P1Body.Piece): the mesh set, its tier, and each blend shape's
    /// index on its body (close: Heroine, play: lod_p1_body) beside its own, so it rides its body's shapes.</summary>
    readonly List<(MeshInstance3D Mi, Mesh Set, bool Play, (int Body, int Own)[] Shapes)> worn = new();
    bool? playOn;
    static readonly string LodMode = Args.Get("lod") ?? "auto";
    P1M4[]? lastG;
    Dictionary<string, double> weights = new();
    bool reorderQueued, offsetsPrinted, driveFailed;

    public P1Laws() { Name = "P1Laws"; }

    sealed record Held(Skeleton3D Sk, Node3D Mount, int Bone, Quaternion AFrame, Transform3D At, int Upper, Quaternion UpperAFrame, Quaternion ARestLocal);
    static readonly List<Held> follow = new();

    /// <summary>A held piece's mount on B (Arms.Hold; `at` its transform in A's bone frame), laid each frame where A's bone
    /// frame is: B's bone as the clip and the layers left it (before the laws), times its A frame (P1Retarget.AFrame). On a
    /// forearm A's own hinge rule then (HerJoints: the swing from A's rest local kept, its twist about y on the hand), which
    /// differs from B's law (the roll about the bone's posed line relative to its parent's turn): B's shield, on B's unrolled
    /// forearm, sat 3 deg off A's in the guard and 16-20 deg off through fight_close's blow (358-366).</summary>
    public static void Follow(Skeleton3D sk, Node3D mount, string aBone, Transform3D at)
    {
        int j = P1Body.Bone(sk, aBone);
        var map = P1Body.RoleMap(sk);
        if (j < 0 || map.AFrame(j) is not { } af) return;
        static Quaternion Q(P1M3 r) => P1Body.T(P1M4.From(r, new P1V(0, 0, 0))).Basis.GetRotationQuaternion();
        int u = -1; var uf = Quaternion.Identity; var rl = Quaternion.Identity;
        if (aBone.StartsWith("lowerarm_") && P1Body.A.Index.TryGetValue(aBone, out int a) && P1Body.A.Parent[a] is int ap and >= 0
            && P1Body.Bone(sk, P1Body.A.Names[ap]) is int bu and >= 0 && map.AFrame(bu) is { } ufm)
        {
            u = bu; uf = Q(ufm);
            rl = Q(P1Retarget.Rot(P1Body.A.Rest[ap]).T() * P1Retarget.Rot(P1Body.A.Rest[a]));
        }
        follow.Add(new Held(sk, mount, j, Q(af), at, u, uf, rl));
    }

    static Quaternion Q4(P1M4 m) => P1Body.T(P1M4.From(P1Retarget.Rot(m), new P1V(0, 0, 0))).Basis.GetRotationQuaternion();

    public override void _Ready()
    {
        sk = GetSkeleton() ?? GetParent() as Skeleton3D;
        if (sk == null) return;
        sk.ChildEnteredTree += OnChild;
        rig = P1Body.RigOf(sk);
        int n = rig.Names.Length;
        var o = new List<int>(); var seen = new bool[n];
        void Visit(int j) { if (seen[j]) return; if (rig.Parent[j] >= 0) Visit(rig.Parent[j]); seen[j] = true; o.Add(j); }
        for (int j = 0; j < n; j++) Visit(j);
        order = o.ToArray();
        restLocal = Enumerable.Range(0, n).Select(j => rig.Parent[j] < 0 ? rig.Rest[j] : rig.Rest[rig.Parent[j]].Inverse() * rig.Rest[j]).ToArray();
        if (FileAccess.FileExists(P1Body.Dir + "play_rig.json")) playRig = new P1Rig(rig.Names, rig.Parent, rig.Rest, P1Body.Rig("play_rig.json"));
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>().Where(m => m.HasMeta("p1_b")))
            if (mi.Name == "lod_p1_body") lod = mi; else closeMeshes.Add(mi);
        body = closeMeshes.FirstOrDefault(m => m.Name == "Heroine");
        reorderQueued = true;
        Callable.From(Reorder).CallDeferred();   // (her skeleton is busy setting up its children now)
    }

    public override void _ExitTree() { if (sk != null) sk.ChildEnteredTree -= OnChild; }

    void OnChild(Node n)
    {
        if (n is SkeletonModifier3D && n != this && n is not HerJiggle && n is not P1Jiggle && n is not HerFaceLife && !reorderQueued)
        {
            reorderQueued = true;
            Callable.From(Reorder).CallDeferred();
        }
    }

    /// <summary>P1Laws after every other modifier, then the springs (P1Jiggle; a HerJiggle if one was added), then HerFaceLife.</summary>
    void Reorder()
    {
        reorderQueued = false;
        if (sk == null || GetParent() != sk) return;
        sk.MoveChild(this, -1);
        foreach (var m in sk.GetChildren().OfType<HerJiggle>().ToList()) sk.MoveChild(m, -1);
        foreach (var m in sk.GetChildren().OfType<P1Jiggle>().ToList()) sk.MoveChild(m, -1);
        foreach (var m in sk.GetChildren().OfType<HerFaceLife>().ToList()) sk.MoveChild(m, -1);
    }

    static P1M4 Local(Skeleton3D s, int j) => P1Body.M(new Transform3D(new Basis(s.GetBonePoseRotation(j)).Scaled(s.GetBonePoseScale(j)), s.GetBonePosePosition(j)));

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (sk == null || rig == null) return;
        int n = rig.Names.Length;
        var L = new P1M4[n]; var G = new P1M4[n];
        foreach (int j in order)
        {
            L[j] = rig.Helpers.Contains(j) ? restLocal[j] : Local(sk, j);
            int p = rig.Parent[j];
            G[j] = p < 0 ? L[j] : G[p] * L[j];
        }
        P1M4[] G2; Dictionary<string, double> w;
        try { (G2, w) = rig.Drive(G); }
        catch (System.Exception e)
        {
            // (rig.json and P1Rig.cs out of step, e.g. a law changed before its republish: the helpers held at rest, no
            // laws, said once; nothing else of hers stops)
            if (!driveFailed) GD.PushError($"p1: P1Rig.Drive failed, B's laws off ({e.GetType().Name}: {e.Message})");
            driveFailed = true;
            G2 = G; w = new Dictionary<string, double>();
        }
        foreach (int j in order)
        {
            int p = rig.Parent[j];
            var L2 = p < 0 ? G2[j] : G2[p].Inverse() * G2[j];
            bool helper = rig.Helpers.Contains(j);
            double d = 0;
            for (int k = 0; k < 12; k++) d = System.Math.Max(d, System.Math.Abs(L2.A[k] - L[j].A[k]));
            if (d < 1e-7 && !helper) continue;
            var lin = L2.Lin();
            var sc = new Vector3((float)lin.Col(0).Len(), (float)lin.Col(1).Len(), (float)lin.Col(2).Len());
            sk.SetBonePosePosition(j, new Vector3((float)L2[0, 3], (float)L2[1, 3], (float)L2[2, 3]));
            sk.SetBonePoseRotation(j, P1Body.T(P1M4.From(P1Retarget.Rot(L2), new P1V(0, 0, 0))).Basis.GetRotationQuaternion());
            sk.SetBonePoseScale(j, sc);
        }
        lastG = G2; weights = w;
        // held mounts laid in A's bone frame (Follow)
        for (int i = follow.Count - 1; i >= 0; i--)
        {
            var h = follow[i];
            if (!GodotObject.IsInstanceValid(h.Mount) || !GodotObject.IsInstanceValid(h.Sk)) { follow.RemoveAt(i); continue; }
            if (h.Sk != sk) continue;
            var a = (Q4(G[h.Bone]) * h.AFrame).Normalized();
            if (h.Upper >= 0)
            {
                // A's forearm on its hinge (HerJoints.TwistY): local = rest local * swing * twist, the twist about y dropped
                var au = (Q4(G[h.Upper]) * h.UpperAFrame).Normalized();
                var d = (h.ARestLocal.Inverse() * au.Inverse() * a).Normalized();
                var t = new Quaternion(0, d.Y, 0, d.W);
                t = t.Length() > 1e-9f ? t.Normalized() : Quaternion.Identity;
                a = (au * h.ARestLocal * d * t.Inverse()).Normalized();
            }
            var local = (Q4(G2[h.Bone]).Inverse() * a).Normalized();
            h.Mount.Transform = new Transform3D(new Basis(local), Vector3.Zero) * h.At;
        }
        for (int i = worn.Count - 1; i >= 0; i--)
        {
            var p = worn[i];
            var on = p.Play ? lod : body;
            if (!GodotObject.IsInstanceValid(p.Mi) || on == null) { worn.RemoveAt(i); continue; }
            foreach (var (bk, ok) in p.Shapes) p.Mi.SetBlendShapeValue(ok, on.GetBlendShapeValue(bk));
        }
        foreach (var mi in closeMeshes)
            foreach (var kv in w)
                if (mi.FindBlendShapeByName(kv.Key) is int k and >= 0) mi.SetBlendShapeValue(k, (float)kv.Value);
        if (lod is { Visible: true } && playRig != null && !driveFailed)
            foreach (var kv in playRig.CorrectiveWeights(G2))
                if (lod.FindBlendShapeByName(kv.Key) is int k and >= 0) lod.SetBlendShapeValue(k, (float)kv.Value);
    }

    public override void _Process(double delta)
    {
        if (sk == null) return;
        // (a piece worn as B's whose mesh was set again since, e.g. a garment tuck laid it anew: carried again)
        foreach (var p in worn.Where(p => GodotObject.IsInstanceValid(p.Mi) && p.Mi.Mesh != p.Set).ToList())
        {
            worn.Remove(p);
            p.Mi.RemoveMeta("p1_piece");
        }
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>())
        {
            if (mi.HasMeta("p1_b") || mi.HasMeta("p1_rebound") || mi.HasMeta("p1_piece") || mi.Skin == null) continue;
            // (her hair and a head piece rebound; A's skin-tight pieces (the ink slot) worn as B's carries of them; A's
            // other outfit pieces are cut from A's surface and stay off B till P1's refit)
            bool hair = mi.GetChildren().OfType<HairSway>().Any(), head = mi.Name.ToString().Contains("_head_");
            if (hair || head) P1Body.Rebind(sk, mi);
            else if (P1Body.Piece(sk, mi) is string tier) Wear(mi, tier == "play");
            else if (mi.Visible) { mi.Visible = false; if (Args.Has("p1-probe")) GD.Print($"p1: {mi.Name} (A's) left off B"); }
        }
        PlaySwitch();
        if (Args.Has("p1-probe") && lastG != null && Engine.GetProcessFrames() % 120 == 0) Probe(lastG);
    }

    void Wear(MeshInstance3D mi, bool play)
    {
        var on = play ? lod : body;
        var sh = new List<(int, int)>();
        if (on?.Mesh is ArrayMesh bm && mi.Mesh is ArrayMesh pm)
            for (int k = 0; k < pm.GetBlendShapeCount(); k++)
                if (on.FindBlendShapeByName(pm.GetBlendShapeName(k)) is int j and >= 0) sh.Add((j, k));
        worn.Add((mi, mi.Mesh, play, sh.ToArray()));
    }

    /// <summary>HerLod's rule for the play tier: in play (no held camera) beyond Far, back within Near; --lod on|off.</summary>
    void PlaySwitch()
    {
        if (lod == null || body == null || sk == null) return;
        bool want = LodMode == "on";
        if (LodMode == "auto" && (HerLod.InPlay || HerLod.FilmFollows) && GetViewport()?.GetCamera3D() is Camera3D cam)
        {
            float d = cam.GlobalPosition.DistanceTo(sk.GlobalPosition + Vector3.Up);
            want = playOn == true ? d > HerLod.Near : d > HerLod.Far;
        }
        if (want != playOn)
        {
            playOn = want;
            lod.Visible = want;
            body.Visible = !want;
            if (Args.Has("p1-probe")) GD.Print($"p1: {(want ? "play" : "close")} tier");
        }
        if (want)
            for (int s = 0; s < lod.Mesh.GetSurfaceCount() && s < body.Mesh.GetSurfaceCount(); s++)
                if (lod.GetSurfaceOverrideMaterial(s) != body.GetSurfaceOverrideMaterial(s)) lod.SetSurfaceOverrideMaterial(s, body.GetSurfaceOverrideMaterial(s));
    }

    /// <summary>(--p1-probe) Per side: the shoulder joint's height over the pelvis against B's rest (mm), the clavicle's and
    /// scapula's turns from rest (deg), the arm's elevation from hanging (deg), trap's head height over the pelvis against
    /// rest (mm); the corrective weights; the tier; once, B's Head to the teeth's and hair's rest centroids.</summary>
    void Probe(P1M4[] G)
    {
        var r = rig!;
        int pel = r.Index["pelvis"];
        double Up(int j, P1M4[] g) => g[j][1, 3] - g[pel][1, 3];
        double Turn(int j)
        {
            int p = r.Parent[j];
            var l = p < 0 ? G[j] : G[p].Inverse() * G[j];
            var rl = p < 0 ? r.Rest[j] : r.Rest[p].Inverse() * r.Rest[j];
            return P1Rig.RotVec(P1Retarget.Rot(rl).T() * P1Retarget.Rot(l)).Len() * 180 / System.Math.PI;
        }
        var parts = new List<string>();
        foreach (var s in new[] { "l", "r" })
        {
            int u = r.Index["upperarm_" + s], lo = r.Index["lowerarm_" + s];
            var dir = G[lo].T() - G[u].T();
            double elev = System.Math.Acos(System.Math.Clamp(-dir.Y / dir.Len(), -1, 1)) * 180 / System.Math.PI;
            string trap = r.Index.TryGetValue("trap_" + s, out int t) ? $"{(Up(t, G) - Up(t, r.Rest)) * 1000:F1}" : "-";
            parts.Add($"{s}: shoulder {(Up(u, G) - Up(u, r.Rest)) * 1000:F1} mm, clavicle {Turn(r.Index["clavicle_" + s]):F1} deg, scap {(r.Index.TryGetValue("scap_" + s, out int sc) ? Turn(sc).ToString("F1") : "-")} deg, arm elevation {elev:F1} deg, trap {trap} mm");
        }
        GD.Print($"p1: probe frame {Engine.GetProcessFrames()} ({(playOn == true ? "play" : "close")} tier{(driveFailed ? ", LAWS OFF: Drive failed" : "")}): {string.Join("; ", parts)}; weights " +
                 string.Join(" ", weights.Where(k => k.Value > 0.001).Select(k => $"{k.Key}={k.Value:F2}")));
        if (offsetsPrinted || sk == null) return;
        offsetsPrinted = true;
        var head = sk.GetBoneGlobalRest(sk.FindBone("Head")).Origin;
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>())
        {
            string nm = mi.Name.ToString().ToLowerInvariant();
            if (!nm.Contains("teeth") && !mi.HasMeta("p1_rebound") || mi.Mesh == null || mi.Skin == null) continue;
            var aabb = mi.Mesh.GetAabb();
            // (the mesh's rest centroid in skeleton space: its bind-pose box centre carried by its first bind's rest)
            var arr = mi.Mesh.SurfaceGetArrays(0);
            var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            var bo = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
            if (v.Length == 0 || bo.Length == 0) continue;
            int per = bo.Length / v.Length;
            var sum = Vector3.Zero;
            for (int i = 0; i < v.Length; i++)
            {
                int bind = bo[i * per];
                int j = sk.FindBone(mi.Skin.GetBindName(bind));
                sum += (j >= 0 ? sk.GetBoneGlobalRest(j) : Transform3D.Identity) * mi.Skin.GetBindPose(bind) * v[i];
            }
            GD.Print($"p1: offset {mi.Name}: rest centroid from B's Head joint {(sum / v.Length - head) * 1000} mm (box {aabb.Size * 1000} mm)");
        }
    }
}
