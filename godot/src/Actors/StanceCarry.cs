using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Her left arm carries the off-hand piece out in a stance (Twin Fangs' dagger, Breaker's mace). View only: laid after the
/// move graph and HerArmHold, over the arm the clips hold low, so the piece is seen from the top play camera and not hidden
/// under her body. The upper arm turns out from her side (about her forward axis) and forward, the forearm bends, by the
/// stance's stances.json "held"."carry_l"; the weight eases 0 to 1 while the piece is drawn and no swing owns the arm.
/// Never the right arm. --carry OUT,FWD,ELBOW,WRIST overrides the stance's values (for tuning).
/// </summary>
public partial class StanceCarry : SkeletonModifier3D
{
    /// <summary>What PlayerView feeds each frame: the stance's carry (null: none) and whether it applies now.</summary>
    public ArmCarry? Carry;
    public bool On;
    public float W { get; private set; }
    const float EaseSeconds = 0.15f;
    ArmCarry? last;
    int pelvis = -1, upper = -1, lower = -1, hand = -1;
    bool ready;
    static readonly ArmCarry? Override = Parse(Args.Get("carry"));

    static ArmCarry? Parse(string? s)
    {
        if (string.IsNullOrEmpty(s)) return null;
        var p = s.Split(',');
        double D(int i) => i < p.Length && double.TryParse(p[i], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : 0;
        return new ArmCarry { Out = D(0), Fwd = D(1), Elbow = D(2), Wrist = D(3) };
    }

    public StanceCarry() { Name = "StanceCarry"; }

    static void Turn(Skeleton3D sk, int b, Vector3 axis, float degrees)
    {
        if (b < 0 || degrees == 0) return;
        var g = sk.GetBoneGlobalPose(b);
        var ng = new Transform3D(new Basis(axis.Normalized(), Mathf.DegToRad(degrees)) * g.Basis, g.Origin);
        int p = sk.GetBoneParent(b);
        var local = p >= 0 ? sk.GetBoneGlobalPose(p).AffineInverse() * ng : ng;
        sk.SetBonePoseRotation(b, local.Basis.GetRotationQuaternion());
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (GetSkeleton() is not Skeleton3D sk) return;
        var c = Override != null && Carry != null ? Override : Carry;
        if (c != null) last = c;
        float target = On && c != null ? 1f : 0f;
        W = Mathf.MoveToward(W, target, (float)delta / EaseSeconds);
        if (W <= 0f || last == null) return;
        if (!ready)
        {
            ready = true;
            pelvis = sk.FindBone("pelvis"); upper = sk.FindBone("upperarm_l"); lower = sk.FindBone("lowerarm_l"); hand = sk.FindBone("hand_l");
        }
        if (pelvis < 0 || upper < 0 || lower < 0) return;
        var pb = sk.GetBoneGlobalPose(pelvis).Basis;
        var f = (pb * Vector3.Back).Normalized();
        var side = Vector3.Up.Cross(f).Normalized();   // her left, on skeleton axes (flipped below if the rig faces the other way)
        float k = Mathf.SmoothStep(0f, 1f, W);
        // Out about her forward axis, forward about her lateral axis, the elbow about the forearm's own hinge.
        Turn(sk, upper, f, (float)last.Out * k * OutSign);
        Turn(sk, upper, side, (float)last.Fwd * k * FwdSign);
        if (last.Elbow != 0)
        {
            var g = sk.GetBoneGlobalPose(lower);
            Turn(sk, lower, (g.Basis * Vector3.Right).Normalized(), (float)last.Elbow * k * ElbowSign);
        }
        if (hand >= 0 && last.Wrist != 0)
        {
            Turn(sk, hand, f, (float)last.Wrist * k * OutSign);   // tilts the piece out from her side (about her forward axis)
        }
    }

    // Sign conventions of the rig (set by looking; --carry-signs OUT,FWD,ELBOW for a check).
    static readonly float[] Signs = SignsArg();
    static float[] SignsArg()
    {
        var s = (Args.Get("carry-signs") ?? "1,-1,-1").Split(',');
        var r = new float[] { 1, 1, 1 };
        for (int i = 0; i < 3 && i < s.Length; i++) if (float.TryParse(s[i], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v)) r[i] = v;
        return r;
    }
    static float OutSign => Signs[0];
    static float FwdSign => Signs[1];
    static float ElbowSign => Signs[2];
}
