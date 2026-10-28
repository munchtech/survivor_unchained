using System.Collections.Generic;
using Godot;
using N = System.Numerics;
using SurvivorUnchained.Play;

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
///   length, where the deltoid is held by the shoulder girdle; on her (Body 5
///   A2: a side with upperarm_twist_02) a chain of four carries the turn
///   evenly down the humerus, the shoulder's share takes 0.30 of it, and the
///   roll is unwrapped frame to frame (Play/ArmTwist; rig_helpers.json
///   "twist_chain"); a body without the chain drives as before;
/// - each share bone (shoulder, elbow, knee) takes half its joint's bend and,
///   at the elbow and knee, pushes the flesh out across the bend as a bent
///   tube is pushed (its own Z), so a joint bends round a corner and keeps its
///   flesh instead of folding flat.
/// - a panel bone (the Reaver's front loincloth) swings forward with her
///   leading thigh (Core/PanelSwing.cs), so the thigh lifts it at a
///   stride's foot strike instead of showing through it.
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
        public float Push, From, To; // a point's push out across the bend (metres), eased in over these degrees
        public float Squeeze, SqueezeX, SqueezeFrom; // a point's width drawn in along its X toward SqueezeX (metres), eased in from SqueezeFrom to To
        public bool Hinge;          // a share's half-bend is about its own hinge (spec "hinge"; Play/ElbowHinge)
        public float RollK;         // a share's part of the upper arm's roll, in a chained arm (twist_chain "roll")
    }

    sealed class Side
    {
        public int Forearm = -1, Hand = -1;
        public Quaternion ForearmRest, HandRest;
        public Vector3 Axis, Thumb0;
        // The upper arm's twist chain (twist_chain): on only where the side has its gate bone.
        public bool Chain;
        public int Upper = -1;
        public Quaternion UpperRest;
        public float UnwrapMax = 270f;
        public float LastRoll = float.NaN;   // last frame's unwrapped roll (degrees)
        public readonly List<Helper> Helpers = new();
        public readonly List<Corrective> Correctives = new();
    }

    /// <summary>A corrective shape (helpers.py "correctives"): a blend shape
    /// of that name on her body and the pieces she wears near the joint,
    /// eased in (smoothstep) from From to To degrees of the joint's bend.</summary>
    sealed class Corrective
    {
        public required string Name;
        public required int Bone;
        public required float From, To;
        public bool Flex;                    // (Body 19) keyed on the flexion (Play/ElbowPsd), not the whole swing
        public float[]? Keys;                // an in-between [lo, at, hi] (Play/ElbowPsd.Weight)
        public readonly List<(MeshInstance3D Mesh, int Shape)> On = new();
    }

    /// <summary>A hanging front panel's bone (the Reaver's loincloth), turned
    /// forward about her lateral axis with the leading thigh (Core/PanelSwing).</summary>
    sealed class Panel
    {
        public int Bone;
        public Quaternion ParentRest, Rest; // the pelvis's global rest; the panel's own rest
        public Vector3 Axis;                // her lateral axis (+X her right) in the pelvis's frame
        public Core.PanelSwing.Law Law;
        public readonly int[][] Chains = new int[2][];   // each thigh up to (not with) the pelvis
        public readonly Vector3[] Rest0 = new Vector3[2]; // each thigh's line at rest, her rest axes
        public double Last = double.NaN;                  // last frame's turn (degrees), for its fall
        public Core.PanelSwing.FoldLaw? Fold;             // the lower half's fold (its mesh's blend shapes), if any
        public string[] FoldShapes = System.Array.Empty<string>();
        public readonly Core.PanelSwing.FoldState FoldState = new();
        public readonly List<(MeshInstance3D Mi, int[] Idx)> FoldOn = new();
        public string[] SideShapes = System.Array.Empty<string>();   // (Body 18) its halves over each thigh lifted
        public double SideFrom, SideTo;
        public readonly List<(MeshInstance3D Mi, int[] Idx)> SideOn = new();
        public Core.PanelSwing.SprintLaw? Sprint;          // (Body 18 r4) the sprint law, if any
        public readonly Core.PanelSwing.SprintState SprintState = new();
    }

    Skeleton3D? found;
    readonly List<Side> sides = new();
    readonly List<Panel> panels = new();
    // Her meshes come and go (an outfit put on): look for the shapes again.
    bool rescan = true;

    void MarkRescan(Node _) => rescan = true;

    void Rescan(Skeleton3D sk)
    {
        rescan = false;
        // (a panel's fold shapes on whatever mesh carries them: the Reaver's outfit)
        foreach (var p in panels)
        {
            p.FoldOn.Clear();
            p.SideOn.Clear();
            if (p.Fold == null) continue;
            foreach (var n in sk.GetChildren())
                if (n is MeshInstance3D mi && mi.Mesh != null && !mi.IsQueuedForDeletion())
                {
                    var idx = System.Array.ConvertAll(p.FoldShapes, nm => mi.FindBlendShapeByName(nm));
                    if (System.Array.Exists(idx, i => i >= 0)) p.FoldOn.Add((mi, idx));
                    var sdx = System.Array.ConvertAll(p.SideShapes, nm => mi.FindBlendShapeByName(nm));
                    if (System.Array.Exists(sdx, i => i >= 0)) p.SideOn.Add((mi, sdx));
                }
        }
        foreach (var side in sides)
            foreach (var c in side.Correctives)
            {
                c.On.Clear();
                foreach (var n in sk.GetChildren())
                    if (n is MeshInstance3D mi && mi.Mesh != null && !mi.IsQueuedForDeletion())
                    {
                        int i = mi.FindBlendShapeByName(c.Name);
                        if (i >= 0) c.On.Add((mi, i));
                    }
            }
    }

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
        if (found != null && IsInstanceValid(found))
        {
            found.ChildEnteredTree -= MarkRescan;
            found.ChildExitingTree -= MarkRescan;
        }
        found = sk;
        sk.ChildEnteredTree += MarkRescan;
        sk.ChildExitingTree += MarkRescan;
        rescan = true;
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
            // Her upper arm's twist chain (helpers SPEC "twist_chain"), where this side has it.
            var amounts = new Dictionary<string, float>();
            var rolls = new Dictionary<string, float>();
            if (s.ContainsKey("twist_chain"))
            {
                var tc = s["twist_chain"].AsGodotDictionary();
                one.Upper = sk.FindBone(((string)tc["roll_bone"]).Replace("{s}", side));
                one.Chain = one.Upper >= 0 && sk.FindBone(((string)tc["gate"]).Replace("{s}", side)) >= 0;
                if (one.Chain)
                {
                    one.UpperRest = sk.GetBoneRest(one.Upper).Basis.GetRotationQuaternion();
                    one.UnwrapMax = (float)(double)tc["unwrap_max"];
                    foreach (var (k, v) in tc["amounts"].AsGodotDictionary()) amounts[((string)k).Replace("{s}", side)] = (float)(double)v;
                    foreach (var (k, v) in tc["roll"].AsGodotDictionary()) rolls[((string)k).Replace("{s}", side)] = (float)(double)v;
                }
            }
            var byName = new Dictionary<string, Godot.Collections.Dictionary>();
            foreach (var hv in s["helpers"].AsGodotArray())
                byName[(string)hv.AsGodotDictionary()["name"]] = hv.AsGodotDictionary();
            foreach (var hv in s["helpers"].AsGodotArray())
            {
                var h = hv.AsGodotDictionary();
                // A point is its share's twin: it bends and swells as the share does.
                var sh = h.ContainsKey("share") ? byName[(string)h["share"]] : h;
                string hname = ((string)h["name"]).Replace("{s}", side);
                int bone = sk.FindBone(hname);
                int src = sk.FindBone(((string)h["bone"]).Replace("{s}", side));
                if (bone < 0 || src < 0) continue;
                var helper = new Helper
                {
                    Kind = (string)h["kind"], Bone = bone, Source = src,
                    Amount = amounts.TryGetValue(hname, out var ca) ? ca : (float)(double)h["amount"],
                    RollK = rolls.TryGetValue(hname, out var rk) ? rk : 0f,
                    Hinge = h.ContainsKey("hinge") && (bool)h["hinge"],
                    Bulge = sh.ContainsKey("bulge") ? (float)(double)sh["bulge"] : 0f,
                    BulgeMax = sh.ContainsKey("bulge_max") ? (float)(double)sh["bulge_max"] : 1f,
                    Pivot = sh.ContainsKey("pivot") ? (float)(double)sh["pivot"] : 0f,
                    Push = h.ContainsKey("push") ? (float)(double)h["push"] : 0f,
                    From = h.ContainsKey("from") ? (float)(double)h["from"] : 0f,
                    To = h.ContainsKey("to") ? (float)(double)h["to"] : 180f,
                    Squeeze = h.ContainsKey("squeeze") ? (float)(double)h["squeeze"] : 0f,
                    SqueezeX = h.ContainsKey("squeeze_x") ? (float)(double)h["squeeze_x"] : 0f,
                    SqueezeFrom = h.ContainsKey("squeeze_from") ? (float)(double)h["squeeze_from"] : 0f,
                    RestOrigin = sk.GetBoneRest(bone).Origin,
                };
                if (helper.Kind == "share" || helper.Kind == "point")
                    helper.Own = sk.GetBoneRest(src).Basis.GetRotationQuaternion().Inverse() * sk.GetBoneRest(bone).Basis.GetRotationQuaternion();
                one.Helpers.Add(helper);
            }
            if (s.ContainsKey("correctives"))
                foreach (var cv in s["correctives"].AsGodotArray())
                {
                    var c = cv.AsGodotDictionary();
                    int bone = sk.FindBone(((string)c["bone"]).Replace("{s}", side));
                    if (bone < 0) continue;
                    var keys = c.ContainsKey("keys") ? c["keys"].AsGodotArray() : null;
                    one.Correctives.Add(new Corrective
                    {
                        Name = ((string)c["name"]).Replace("{s}", side), Bone = bone,
                        From = c.ContainsKey("from") ? (float)(double)c["from"] : 0f,
                        To = c.ContainsKey("to") ? (float)(double)c["to"] : 1f,
                        Flex = c.ContainsKey("on") && (string)c["on"] == "flex",
                        Keys = keys == null ? null : new[] { (float)(double)keys[0], (float)(double)keys[1], (float)(double)keys[2] },
                    });
                }
            sides.Add(one);
        }
        // Panel bones (helpers.py SPEC "panels"): one centred bone each.
        panels.Clear();
        if (s.ContainsKey("panels"))
            foreach (var pv in s["panels"].AsGodotArray())
            {
                var p = pv.AsGodotDictionary();
                int bone = sk.FindBone((string)p["name"]), parent = sk.FindBone((string)p["parent"]);
                var thighs = p["thighs"].AsGodotArray();
                int tl = sk.FindBone((string)thighs[0]), tr = sk.FindBone((string)thighs[1]);
                if (bone < 0 || parent < 0 || tl < 0 || tr < 0) continue;
                var gp = sk.GetBoneGlobalRest(parent).Basis.GetRotationQuaternion();
                var one = new Panel
                {
                    Bone = bone, ParentRest = gp, Rest = sk.GetBoneRest(bone).Basis.GetRotationQuaternion(),
                    Axis = (gp.Inverse() * new Vector3(-1, 0, 0)).Normalized(),
                    Law = new Core.PanelSwing.Law((double)p["amount"], (double)p["soft"], (double)p["spread_from"], (double)p["spread_to"], (double)p["spread_damp"],
                        p.ContainsKey("fall_tau") ? (double)p["fall_tau"] : 0.04, p.ContainsKey("fall_rate") ? (double)p["fall_rate"] : 450,
                        p.ContainsKey("drop") ? (double)p["drop"] : 0, p.ContainsKey("drop_from") ? (double)p["drop_from"] : 45),
                };
                if (p.ContainsKey("sprint"))
                {
                    var sd = p["sprint"].AsGodotDictionary();
                    var am = sd["amp"].AsGodotArray();
                    var rg = sd["range"].AsGodotArray();
                    one.Sprint = new Core.PanelSwing.SprintLaw((double)am[0], (double)am[1], (double)rg[0], (double)rg[1], (double)sd["decay"],
                        (double)sd["amount"], (double)sd["fall_tau"], (double)sd["fall_rate"], (double)sd["hz"], (double)sd["zeta"]);
                }
                if (p.ContainsKey("fold"))
                {
                    var f = p["fold"].AsGodotDictionary();
                    var c = f["contact"].AsGodotArray();
                    one.Fold = new Core.PanelSwing.FoldLaw((double)f["step"], (double)f["neg"], (double)f["hz"], (double)f["zeta"], (double)f["rest"],
                        (double)c[0], (double)c[1], (int)f["substeps"]);
                    var sh = f["shapes"].AsGodotArray();
                    one.FoldShapes = new[] { (string)sh[0], (string)sh[1], (string)sh[2] };
                    if (f.ContainsKey("side"))
                    {
                        var sd = f["side"].AsGodotDictionary();
                        var ss = sd["shapes"].AsGodotArray();
                        var sw = sd["swing"].AsGodotArray();
                        one.SideShapes = new[] { (string)ss[0], (string)ss[1] };
                        one.SideFrom = (double)sw[0]; one.SideTo = (double)sw[1];
                    }
                }
                foreach (var (t, i) in new[] { (tl, 0), (tr, 1) })
                {
                    var chain = new List<int>();
                    for (int j = t; j >= 0 && j != parent; j = sk.GetBoneParent(j)) chain.Add(j);
                    one.Chains[i] = chain.ToArray();
                    var q = Quaternion.Identity;
                    foreach (int j in one.Chains[i]) q = sk.GetBoneRest(j).Basis.GetRotationQuaternion() * q;
                    one.Rest0[i] = gp * (q * Vector3.Up);
                }
                panels.Add(one);
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

    static N.Quaternion Nq(Quaternion q) => new(q.X, q.Y, q.Z, q.W);
    static Quaternion Gq(N.Quaternion q) => new(q.X, q.Y, q.Z, q.W);

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        if (rescan) Rescan(sk);
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
            // The upper arm's roll, once, unwrapped from the last frame's (a chained arm only).
            float roll = 0f;
            if (side.Chain)
            {
                roll = ArmTwist.Unwrap(side.LastRoll, ArmTwist.Roll(Nq(side.UpperRest), Nq(sk.GetBonePoseRotation(side.Upper))), side.UnwrapMax);
                side.LastRoll = roll;
            }
            foreach (var h in side.Helpers)
            {
                switch (h.Kind)
                {
                    case "forearm_twist":
                        sk.SetBonePoseRotation(h.Bone, new Quaternion(Vector3.Up, turn * h.Amount));
                        break;
                    case "counter_twist":
                    {
                        if (side.Chain && h.Source == side.Upper)
                        {
                            sk.SetBonePoseRotation(h.Bone, Gq(ArmTwist.Counter(roll, h.Amount)));
                            break;
                        }
                        var rest = sk.GetBoneRest(h.Source).Basis.GetRotationQuaternion();
                        var (_, _, deg) = TwistY(rest.Inverse() * sk.GetBonePoseRotation(h.Source));
                        sk.SetBonePoseRotation(h.Bone, new Quaternion(Vector3.Up, Mathf.DegToRad(-deg * h.Amount)));
                        break;
                    }
                    case "share":
                    case "point":
                    {
                        var rest = sk.GetBoneRest(h.Source).Basis.GetRotationQuaternion();
                        var (bend, _, _) = TwistY(rest.Inverse() * sk.GetBonePoseRotation(h.Source));
                        var turned = (rest * Quaternion.Identity.Slerp(bend, h.Amount) * h.Own).Normalized();
                        if (h.Hinge)
                            turned = Gq(ElbowHinge.Share(Nq(rest), Nq(sk.GetBonePoseRotation(h.Source)), h.Amount, Nq(h.Own)));
                        if (side.Chain && h.RollK != 0f)
                            turned = Gq(ArmTwist.Share(Nq(rest), Nq(sk.GetBonePoseRotation(h.Source)), h.Amount, Nq(h.Own), roll, h.RollK));
                        sk.SetBonePoseRotation(h.Bone, turned);
                        if (h.Bulge > 0 || h.Push > 0 || h.Squeeze > 0)
                        {
                            // The skin's weights over a joint are a quadratic
                            // Bezier's, so a point halfway round lies at
                            // (cos(bend/2) + stretch) / 2 of its rest distance: a
                            // stretch of 2 - cos(bend/2) along the share's Z (across
                            // the bend) keeps it there, a rounded corner (helpers.bulge).
                            float rad = 2 * Mathf.Acos(Mathf.Min(1f, Mathf.Abs(bend.W)));
                            float k = 2f - Mathf.Cos(rad / 2);
                            float stretch = Mathf.Min(1 + h.Bulge * (k - 1), h.BulgeMax);
                            // A point is drawn in across the bend (its X, the hinge axis)
                            // toward SqueezeX, eased in from SqueezeFrom to To degrees
                            // (helpers.point_squeeze): from behind, the tip narrows.
                            float q = 0f;
                            if (h.Squeeze > 0)
                            {
                                float v = Mathf.Clamp((Mathf.RadToDeg(rad) - h.SqueezeFrom) / (h.To - h.SqueezeFrom), 0f, 1f);
                                q = h.Squeeze * v * v * (3 - 2 * v);
                            }
                            sk.SetBonePoseScale(h.Bone, new Vector3(1 - q, 1, stretch));
                            // About its pivot (helpers.bulge): the crease side held still,
                            // the stretch's push all on the outside of the bend.
                            // A point is pushed out across the bend (its -Z, away from
                            // the crease), eased in over From..To degrees (helpers.point_push).
                            float push = 0f;
                            if (h.Push > 0)
                            {
                                float u = Mathf.Clamp((Mathf.RadToDeg(rad) - h.From) / (h.To - h.From), 0f, 1f);
                                push = h.Push * u * u * (3 - 2 * u);
                            }
                            if (h.Pivot != 0 || push != 0 || q != 0)
                                sk.SetBonePosePosition(h.Bone, h.RestOrigin + turned * new Vector3(q * h.SqueezeX, 0, (1 - stretch) * h.Pivot - push));
                        }
                        break;
                    }
                }
            }
            // Her corrective shapes from their joints' bend as the clips and
            // layers leave it (the forearm's roll already handed down), as
            // helpers.bend reads it: the swing from rest, the turn about the
            // bone's own line left out.
            foreach (var c in side.Correctives)
            {
                var rest = sk.GetBoneRest(c.Bone).Basis.GetRotationQuaternion();
                float deg;
                if (c.Flex) deg = ElbowPsd.Flexion(Nq(rest), Nq(sk.GetBonePoseRotation(c.Bone)));
                else
                {
                    var (swing2, _, _) = TwistY(rest.Inverse() * sk.GetBonePoseRotation(c.Bone));
                    deg = Mathf.RadToDeg(2 * Mathf.Acos(Mathf.Min(1f, Mathf.Abs(swing2.W))));
                }
                float w;
                if (c.Keys != null) w = ElbowPsd.Weight(c.Keys[0], c.Keys[1], c.Keys[2], deg);
                else
                {
                    float v = Mathf.Clamp((deg - c.From) / (c.To - c.From), 0f, 1f);
                    w = v * v * (3 - 2 * v);
                }
                foreach (var (mi, i) in c.On)
                    if (IsInstanceValid(mi)) mi.SetBlendShapeValue(i, w);
            }
        }
        // The panels: each thigh's line in the pelvis's frame (her rest axes
        // carried with it), its forward swing and spread from rest, and the
        // panel turned by the law about her lateral axis, its bottom forward.
        foreach (var p in panels)
        {
            double fl = 0, fr = 0, al = 0, ar = 0;
            for (int i = 0; i < 2; i++)
            {
                var q = Quaternion.Identity;
                foreach (int j in p.Chains[i]) q = sk.GetBonePoseRotation(j) * q;
                var v = p.ParentRest * (q * Vector3.Up);
                var v0 = p.Rest0[i];
                var (sw, sp) = Core.PanelSwing.SwingSpread(v.X, v.Y, v.Z, v0.X, v0.Y, v0.Z, i == 0 ? 1 : -1);
                if (i == 0) { fl = sw; al = sp; } else { fr = sw; ar = sp; }
            }
            // (up with the thigh at once, down as a loose flap falls: Core/PanelSwing.Fall)
            // (Body 18 r4: in a sprint the law blends to its sprint numbers: Core/PanelSwing.Sprint)
            var pl = p.Law;
            double g = 0;
            if (p.Sprint is { } spr)
            {
                g = Core.PanelSwing.Sprint(spr, p.SprintState, Core.PanelSwing.Lead(pl, fl, fr), delta);
                pl = Core.PanelSwing.Blend(pl, spr, g);
            }
            double law = Core.PanelSwing.Turn(pl, fl, fr, al, ar);
            p.Last = Core.PanelSwing.Fall(pl, p.Last, law, delta);
            float deg = (float)p.Last;
            sk.SetBonePoseRotation(p.Bone, (new Quaternion(p.Axis, Mathf.DegToRad(deg)) * p.Rest).Normalized());
            // (the lower half: a pendulum lying on the leading thigh, its fold as the mesh's shapes: Core/PanelSwing.Fold)
            if (p.Fold is { } fold0 && p.FoldOn.Count > 0)
            {
                var fold = p.Sprint is { } spr2 ? Core.PanelSwing.Blend(fold0, spr2, g) : fold0;
                var (wa, wb, wn) = Core.PanelSwing.FoldWeights(fold, Core.PanelSwing.Fold(fold, p.FoldState, law, pl.Amount, p.Last, delta));
                foreach (var (mi, idx) in p.FoldOn)
                    if (IsInstanceValid(mi))
                    {
                        if (idx[0] >= 0) mi.SetBlendShapeValue(idx[0], (float)wa);
                        if (idx[1] >= 0) mi.SetBlendShapeValue(idx[1], (float)wb);
                        if (idx[2] >= 0) mi.SetBlendShapeValue(idx[2], (float)wn);
                    }
            }
            // (Body 18: the half over each thigh lifted as that thigh swings forward: Core/PanelSwing.SideWeights)
            if (p.SideOn.Count > 0)
            {
                var (sl, sr) = Core.PanelSwing.SideWeights(fl, fr, p.SideFrom, p.SideTo);
                foreach (var (mi, idx) in p.SideOn)
                    if (IsInstanceValid(mi))
                    {
                        if (idx[0] >= 0) mi.SetBlendShapeValue(idx[0], (float)sl);
                        if (idx[1] >= 0) mi.SetBlendShapeValue(idx[1], (float)sr);
                    }
            }
        }
    }
}
