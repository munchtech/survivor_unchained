using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her helper bones (tools/anim/helpers.py, built into her by
/// tools/assets/heroine_rig.py; the hero's alike), driven from whatever pose
/// the clips and the other layers leave, last of all:
/// - the forearm bone kept on its hinge: any roll a clip gives it on the
///   elbow is handed down to the hand (the hand ends where it was), and the
///   hand's turn about the forearm is shared along it by its twist bones, so
///   the skin turns as the radius rolls over the ulna, never wrung at the
///   elbow or the wrist;
/// - the shoulder's twist bone half undoes the upper arm's turn about its
///   length, where the deltoid is held by the shoulder girdle;
/// - each share bone (shoulder, elbow, knee) takes half its joint's bend and,
///   at the elbow and knee, pushes the flesh out across the bend as a bent
///   tube is pushed (its own Z), so a joint bends round a corner and keeps its
///   flesh instead of folding flat.
/// A body without the helpers is left as it is. The numbers are in
/// art/people/rig_helpers.json, written by helpers.py, so the tools and the
/// game drive them alike.
/// </summary>
public partial class HerJoints : SkeletonModifier3D
{
    public HerJoints() { Name = "HerJoints"; }

    sealed class Helper
    {
        public required string Kind;
        public required int Bone, Source;
        public required float Amount, Bulge, BulgeMax;
        public float Pivot;         // metres along the share's Z its stretch holds still (the crease side)
        public Vector3 RestOrigin;
        public Quaternion Own;      // a share's turn about its line, from the bone it shares
    }

    sealed class Side
    {
        public int Forearm = -1, Hand = -1;
        public Quaternion ForearmRest, HandRest;
        public Vector3 Axis, Thumb0;
        public readonly List<Helper> Helpers = new();
    }

    Skeleton3D? found;
    readonly List<Side> sides = new();

    static Godot.Collections.Dictionary? spec;

    static Godot.Collections.Dictionary? Spec()
    {
        if (spec != null) return spec;
        const string file = "res://art/people/rig_helpers.json";
        if (!FileAccess.FileExists(file)) return null;
        spec = Json.ParseString(FileAccess.GetFileAsString(file)).AsGodotDictionary();
        return spec;
    }

    void Find(Skeleton3D sk)
    {
        found = sk;
        sides.Clear();
        var s = Spec();
        if (s == null) return;
        foreach (var side in new[] { "l", "r" })
        {
            var one = new Side();
            one.Forearm = sk.FindBone($"lowerarm_{side}");
            one.Hand = sk.FindBone($"hand_{side}");
            // No twist bones down the forearm: not a body built with helpers.
            if (one.Forearm < 0 || one.Hand < 0 || sk.FindBone($"lowerarm_twist_01_{side}") < 0) continue;
            one.ForearmRest = sk.GetBoneRest(one.Forearm).Basis.GetRotationQuaternion();
            var handRest = sk.GetBoneRest(one.Hand);
            one.HandRest = handRest.Basis.GetRotationQuaternion();
            one.Axis = handRest.Origin.Normalized();
            one.Thumb0 = one.HandRest * Vector3.Back;
            foreach (var hv in s["helpers"].AsGodotArray())
            {
                var h = hv.AsGodotDictionary();
                int bone = sk.FindBone(((string)h["name"]).Replace("{s}", side));
                int src = sk.FindBone(((string)h["bone"]).Replace("{s}", side));
                if (bone < 0 || src < 0) continue;
                var helper = new Helper
                {
                    Kind = (string)h["kind"], Bone = bone, Source = src, Amount = (float)(double)h["amount"],
                    Bulge = h.ContainsKey("bulge") ? (float)(double)h["bulge"] : 0f,
                    BulgeMax = h.ContainsKey("bulge_max") ? (float)(double)h["bulge_max"] : 1f,
                    Pivot = h.ContainsKey("pivot") ? (float)(double)h["pivot"] : 0f,
                    RestOrigin = sk.GetBoneRest(bone).Origin,
                };
                if (helper.Kind == "share")
                    helper.Own = sk.GetBoneRest(src).Basis.GetRotationQuaternion().Inverse() * sk.GetBoneRest(bone).Basis.GetRotationQuaternion();
                one.Helpers.Add(helper);
            }
            sides.Add(one);
        }
    }

    /// <summary>d split as swing * twist, the twist about the bone's own +Y.</summary>
    static (Quaternion Swing, Quaternion Twist, float Degrees) TwistY(Quaternion d)
    {
        var t = new Quaternion(0, d.Y, 0, d.W);
        float n = t.Length();
        t = n > 1e-9f ? t / n : Quaternion.Identity;
        if (t.W < 0) t = -t;
        float deg = Mathf.RadToDeg(2 * Mathf.Atan2(t.Y, t.W));
        return (d * t.Inverse(), t, deg);
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        foreach (var side in sides)
        {
            // The forearm bone kept on its hinge: its roll goes to the hand.
            var (swing, twist, _) = TwistY(side.ForearmRest.Inverse() * sk.GetBonePoseRotation(side.Forearm));
            sk.SetBonePoseRotation(side.Forearm, (side.ForearmRest * swing).Normalized());
            var hand = (twist * sk.GetBonePoseRotation(side.Hand)).Normalized();
            sk.SetBonePoseRotation(side.Hand, hand);
            // The hand's turn about the forearm: its thumb side's way across
            // the forearm against where it lies at rest (a bend toward the
            // palm or to the side leaves it).
            var a = side.Axis;
            var t0 = side.Thumb0 - a * side.Thumb0.Dot(a);
            var t = hand * Vector3.Back;
            t -= a * t.Dot(a);
            float turn = t0.LengthSquared() > 1e-12f && t.LengthSquared() > 1e-12f ? Mathf.Atan2(t0.Cross(t).Dot(a), t0.Dot(t)) : 0f;
            foreach (var h in side.Helpers)
            {
                switch (h.Kind)
                {
                    case "forearm_twist":
                        sk.SetBonePoseRotation(h.Bone, new Quaternion(Vector3.Up, turn * h.Amount));
                        break;
                    case "counter_twist":
                    {
                        var rest = sk.GetBoneRest(h.Source).Basis.GetRotationQuaternion();
                        var (_, _, deg) = TwistY(rest.Inverse() * sk.GetBonePoseRotation(h.Source));
                        sk.SetBonePoseRotation(h.Bone, new Quaternion(Vector3.Up, Mathf.DegToRad(-deg * h.Amount)));
                        break;
                    }
                    case "share":
                    {
                        var rest = sk.GetBoneRest(h.Source).Basis.GetRotationQuaternion();
                        var (bend, _, _) = TwistY(rest.Inverse() * sk.GetBonePoseRotation(h.Source));
                        var turned = (rest * Quaternion.Identity.Slerp(bend, h.Amount) * h.Own).Normalized();
                        sk.SetBonePoseRotation(h.Bone, turned);
                        if (h.Bulge > 0)
                        {
                            // The skin's weights over a joint are a quadratic
                            // Bezier's, so a point halfway round lies at
                            // (cos(bend/2) + stretch) / 2 of its rest distance: a
                            // stretch of 2 - cos(bend/2) along the share's Z (across
                            // the bend) keeps it there, a rounded corner (helpers.bulge).
                            float rad = 2 * Mathf.Acos(Mathf.Min(1f, Mathf.Abs(bend.W)));
                            float k = 2f - Mathf.Cos(rad / 2);
                            float stretch = Mathf.Min(1 + h.Bulge * (k - 1), h.BulgeMax);
                            sk.SetBonePoseScale(h.Bone, new Vector3(1, 1, stretch));
                            // About its pivot (helpers.bulge): the crease side held still,
                            // the stretch's push all on the outside of the bend.
                            if (h.Pivot != 0)
                                sk.SetBonePosePosition(h.Bone, h.RestOrigin + turned * new Vector3(0, 0, (1 - stretch) * h.Pivot));
                        }
                        break;
                    }
                }
            }
        }
    }
}
