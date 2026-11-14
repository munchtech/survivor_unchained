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
/// left to the clip. Package NPCs only (NpcPackage); a cinematic sets Influence to 0 for a clip's own hand.
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

    Skeleton3D? found;
    int[] bones = System.Array.Empty<int>();
    Quaternion[] target = System.Array.Empty<Quaternion>(), fist = System.Array.Empty<Quaternion>();
    bool[] left = System.Array.Empty<bool>();

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
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        for (int k = 0; k < bones.Length; k++)
            sk.SetBonePoseRotation(bones[k], (left[k] ? FistL : FistR) ? fist[k] : sk.GetBonePoseRotation(bones[k]).Slerp(target[k], Blend));
    }
}
