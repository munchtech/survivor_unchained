using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A package NPC's hands at rest in a loose curl (R3c, judge: "thin, limp and splayed": the library clips' finger
/// keys left the fingers straight and fanned). After the animation each finger joint of index, middle, ring and
/// pinky is taken Blend of the way from the clip's rotation toward its rest turned about the joint's own X (the
/// knuckle line on this rig: fingers along +Y, the palm toward +Z, and the same positive angle curls both hands,
/// their frames being mirrored), more toward the little finger and most at the middle joint (Curl, degrees). The
/// rest's spread replaces the clip's fan; the clip's own finger motion is kept by the remaining share. The thumb is
/// left to the clip, but for a fist (FistL, FistR), whose thumb is laid over the closed fingers (ThumbFist). Package NPCs only (NpcPackage); a cinematic sets Influence to 0 for a clip's own hand.
/// </summary>
public partial class NpcHands : SkeletonModifier3D
{
    /// <summary>Share of the way to the curled pose (0 the clip, 1 the curl alone).</summary>
    public float Blend = 0.85f;
    /// <summary>The left hand closed round a held shaft (a torch: NpcTorchArm), FistCurl's angles, fully.</summary>
    public bool FistL, FistR;
    /// <summary>A fist's curl per joint (01, 02, 03), degrees, for index, middle, ring and pinky.</summary>
    public static readonly float[][] FistCurl =
    {
        new[] { 62f, 78f, 40f },
        new[] { 68f, 82f, 42f },
        new[] { 72f, 84f, 44f },
        new[] { 76f, 86f, 46f },
    };
    /// <summary>Curl per joint (01, 02, 03), degrees, for index, middle, ring and pinky.</summary>
    public static readonly float[][] Curl =
    {
        new[] { 22f, 36f, 18f },
        new[] { 28f, 42f, 22f },
        new[] { 34f, 48f, 25f },
        new[] { 40f, 54f, 28f },
    };
    static readonly string[] Names = { "index", "middle", "ring", "pinky" };

    /// <summary>A finger (Names' index) closed by FistCurl from its rest, in the hand bone's frame: its _01, _02 and _03 and a
    /// transform at its tip (its _04 leaf's rest place). Null without the chain.</summary>
    static Transform3D[]? FistChain(Skeleton3D sk, string side, int f)
    {
        int h = sk.FindBone($"hand_{side}"), b1 = sk.FindBone($"{Names[f]}_01_{side}"), b2 = sk.FindBone($"{Names[f]}_02_{side}"), b3 = sk.FindBone($"{Names[f]}_03_{side}");
        if (h < 0 || b1 < 0 || b2 < 0 || b3 < 0 || sk.GetBoneParent(b2) != b1 || sk.GetBoneParent(b3) != b2) return null;
        Transform3D Closed(int b, int j)
        {
            var r = sk.GetBoneRest(b);
            return new Transform3D(new Basis((r.Basis.GetRotationQuaternion() * new Quaternion(Vector3.Right, Mathf.DegToRad(FistCurl[f][j]))).Normalized()), r.Origin);
        }
        var g1 = sk.GetBoneGlobalRest(h).AffineInverse() * sk.GetBoneGlobalRest(sk.GetBoneParent(b1)) * Closed(b1, 0);
        var g2 = g1 * Closed(b2, 1);
        var g3 = g2 * Closed(b3, 2);
        int tb = sk.GetBoneChildren(b3).FirstOrDefault(-1);
        return new[] { g1, g2, g3, new Transform3D(g3.Basis, g3 * (tb >= 0 ? sk.GetBoneRest(tb).Origin : sk.GetBoneRest(b3).Origin)) };
    }

    /// <summary>The closed fist's pocket in the hand bone's frame (at rest): the middle finger closed by FistCurl, the centre of
    /// the loop its knuckle, its two joints and its tip make, where a bar held in the fist runs (a lamp's bail, a grip's
    /// origin: PersonView.LampFist and HandFist). Null without a middle finger.</summary>
    public static Vector3? Pocket(Skeleton3D sk, string side) =>
        FistChain(sk, side, 1) is { } c ? (c[0].Origin + c[1].Origin + c[2].Origin + c[3].Origin) / 4 : null;

    /// <summary>Where the fist's thumb tip lies, in the hand bone's frame: over the closed index and middle fingers' middle
    /// joints (their _02 to _03), 12 mm out from the pocket (on the fingers' backs, not into the grip).</summary>
    public static Vector3? ThumbOn(Skeleton3D sk, string side)
    {
        if (FistChain(sk, side, 0) is not { } ix || FistChain(sk, side, 1) is not { } md || Pocket(sk, side) is not Vector3 pocket) return null;
        var on = (ix[1].Origin + ix[2].Origin + md[1].Origin + md[2].Origin) / 4;
        return on + (on - pocket).Normalized() * 0.012f;
    }

    /// <summary>The fist's thumb (thumb_01 to _03 pose rotations): laid over the closed fingers (ThumbOn) from its rest by a
    /// few rounds of the least turn of each joint that brings its tip toward that place (at most 20 degrees a turn), so it
    /// wraps the grip rather than pointing along it. Null without a thumb chain.</summary>
    static (int[] Bones, Quaternion[] Rot)? ThumbFist(Skeleton3D sk, string side)
    {
        int h = sk.FindBone($"hand_{side}"), t1 = sk.FindBone($"thumb_01_{side}"), t2 = sk.FindBone($"thumb_02_{side}"), t3 = sk.FindBone($"thumb_03_{side}");
        if (h < 0 || t1 < 0 || t2 < 0 || t3 < 0 || sk.GetBoneParent(t2) != t1 || sk.GetBoneParent(t3) != t2 || ThumbOn(sk, side) is not Vector3 to) return null;
        int tb = sk.GetBoneChildren(t3).FirstOrDefault(-1);
        // (the tip the mesh's thumb ends in, where there is one: a package's generated thumb need not run along its bones)
        var tipLocal = MeshThumbTip(sk, side) is Vector3 mt ? sk.GetBoneGlobalRest(t3).AffineInverse() * mt : tb >= 0 ? sk.GetBoneRest(tb).Origin : sk.GetBoneRest(t3).Origin;
        var root = sk.GetBoneGlobalRest(h).AffineInverse() * sk.GetBoneGlobalRest(sk.GetBoneParent(t1));
        int[] chain = { t1, t2, t3 };
        var origin = chain.Select(b => sk.GetBoneRest(b).Origin).ToArray();
        var q = chain.Select(b => sk.GetBoneRest(b).Basis.GetRotationQuaternion()).ToArray();
        var g = new Transform3D[3];
        Vector3 Tip()
        {
            var at = root;
            for (int k = 0; k < 3; k++) g[k] = at = at * new Transform3D(new Basis(q[k]), origin[k]);
            return g[2] * tipLocal;
        }
        for (int round = 0; round < 16; round++)
            for (int k = 2; k >= 0; k--)
            {
                var tip = Tip();
                Vector3 from = tip - g[k].Origin, toward = to - g[k].Origin;
                if (from.Length() < 1e-5f || toward.Length() < 1e-5f || from.Normalized().Dot(toward.Normalized()) > 0.99999f) continue;
                var turn = Quaternion.Identity.Slerp(new Quaternion(from.Normalized(), toward.Normalized()), 1f);
                float ang = turn.GetAngle();
                if (ang > Mathf.DegToRad(20)) turn = Quaternion.Identity.Slerp(turn, Mathf.DegToRad(20) / ang);
                var parent = (k == 0 ? root : g[k - 1]).Basis.GetRotationQuaternion();
                q[k] = (parent.Inverse() * turn * parent * q[k]).Normalized();
            }
        return (chain, q);
    }

    /// <summary>The thumb's tip where the skinned mesh has it (the skeleton's rest space): of the vertices its last two bones
    /// carry (half their weight or more), the one furthest from its root joint. Null without such a mesh under the skeleton.</summary>
    public static Vector3? MeshThumbTip(Skeleton3D sk, string side)
    {
        int t1 = sk.FindBone($"thumb_01_{side}"), t2 = sk.FindBone($"thumb_02_{side}"), t3 = sk.FindBone($"thumb_03_{side}");
        if (t1 < 0 || t2 < 0 || t3 < 0) return null;
        var rootAt = sk.GetBoneGlobalRest(t1).Origin;
        float best = -1; var tip = Vector3.Zero;
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>())
        {
            if (mi.Skin is not { } skin || mi.Mesh is not { } mesh) continue;
            var bind = Enumerable.Range(0, skin.GetBindCount()).Select(i => skin.GetBindName(i) is var n && n != "" ? sk.FindBone(n) : skin.GetBindBone(i)).ToArray();
            if (!bind.Contains(t2) && !bind.Contains(t3)) continue;
            for (int s = 0; s < mesh.GetSurfaceCount(); s++)
            {
                var arr = mesh.SurfaceGetArrays(s);
                if (arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil) continue;
                var verts = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var bones = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                var weights = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                if (verts.Length == 0 || bones.Length != weights.Length) continue;
                int per = bones.Length / verts.Length;
                for (int v = 0; v < verts.Length; v++)
                {
                    float on = 0, top = 0; int dom = -1;
                    for (int k = 0; k < per; k++)
                    {
                        int bi = bones[v * per + k]; float w = weights[v * per + k];
                        if (w <= 0 || bi < 0 || bi >= bind.Length) continue;
                        if (bind[bi] == t2 || bind[bi] == t3) on += w;
                        if (w > top) { top = w; dom = bi; }
                    }
                    if (on < 0.5f || dom < 0 || bind[dom] < 0) continue;
                    var p = sk.GetBoneGlobalRest(bind[dom]) * skin.GetBindPose(dom) * verts[v];
                    float d = p.DistanceTo(rootAt);
                    if (d > best) { best = d; tip = p; }
                }
            }
        }
        return best > 0 ? tip : null;
    }

    Skeleton3D? found;
    int[] bones = System.Array.Empty<int>();
    Quaternion[] target = System.Array.Empty<Quaternion>(), fist = System.Array.Empty<Quaternion>();
    bool[] left = System.Array.Empty<bool>();
    // (a fist's thumb, solved when the hand first closes: it reads the mesh)
    (int[] Bones, Quaternion[] Rot)? thumbL, thumbR;
    static readonly (int[], Quaternion[]) NoThumb = (System.Array.Empty<int>(), System.Array.Empty<Quaternion>());

    public NpcHands() { Name = "NpcHands"; }

    void Find(Skeleton3D sk)
    {
        found = sk;
        // (NPC_HAND_CURL scales the curl: a check)
        float scale = System.Environment.GetEnvironmentVariable("NPC_HAND_CURL") is string hc && float.TryParse(hc, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var hv) ? hv : 1f;
        var b = new System.Collections.Generic.List<int>(); var t = new System.Collections.Generic.List<Quaternion>();
        var fq = new System.Collections.Generic.List<Quaternion>(); var lf = new System.Collections.Generic.List<bool>();
        foreach (var side in new[] { "l", "r" })
            for (int f = 0; f < Names.Length; f++)
                for (int j = 0; j < 3; j++)
                {
                    int i = sk.FindBone($"{Names[f]}_0{j + 1}_{side}");
                    if (i < 0) continue;
                    var rest = sk.GetBoneRest(i).Basis.GetRotationQuaternion();
                    b.Add(i); t.Add((rest * new Quaternion(Vector3.Right, Mathf.DegToRad(Curl[f][j] * scale))).Normalized());
                    fq.Add((rest * new Quaternion(Vector3.Right, Mathf.DegToRad(FistCurl[f][j]))).Normalized()); lf.Add(side == "l");
                }
        bones = b.ToArray(); target = t.ToArray(); fist = fq.ToArray(); left = lf.ToArray();
        thumbL = thumbR = null;
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        for (int k = 0; k < bones.Length; k++)
            sk.SetBonePoseRotation(bones[k], (left[k] ? FistL : FistR) ? fist[k] : sk.GetBonePoseRotation(bones[k]).Slerp(target[k], Blend));
        // (a fist's thumb laid over its fingers; a free hand's thumb is the clip's)
        if (FistL) Thumb(sk, thumbL ??= ThumbFist(sk, "l") ?? NoThumb);
        if (FistR) Thumb(sk, thumbR ??= ThumbFist(sk, "r") ?? NoThumb);
    }

    static void Thumb(Skeleton3D sk, (int[] Bones, Quaternion[] Rot)? th)
    {
        if (th is not { } t) return;
        for (int k = 0; k < t.Bones.Length; k++) sk.SetBonePoseRotation(t.Bones[k], t.Rot[k]);
    }
}
