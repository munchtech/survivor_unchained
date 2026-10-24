using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The heroine's own carriage, laid over whatever clip is playing (the
/// clips were made for the Quaternius bodies, which are built differently):
/// her fingers eased halfway back to rest, so a relaxed hand is relaxed and
/// not a claw; her upper arms brought in toward her body, which the clips
/// hold out for narrower hips; and a little contrapposto, her weight on one
/// hip and her shoulders answering it.
/// </summary>
public partial class HerPose : SkeletonModifier3D
{
    /// <summary>How far the fingers go back toward rest (0 none, 1 all).</summary>
    public float FingerEase = 0.5f;
    /// <summary>Degrees the upper arms come in toward the body.</summary>
    public float ArmsIn = 9f;
    /// <summary>Degrees of hip tilt (the shoulders answer at half).</summary>
    public float HipTilt = 3.5f;
    /// <summary>Degrees the neck is bowed forward: a body whose neck leans
    /// further forward at rest than the library's (the hero's) has his head
    /// thrown back by its clips without it.</summary>
    public float NeckPitch = 0f;
    /// <summary>How much of what is playing is her own (tools/anim, made on
    /// her skeleton): 0 a library clip, wholly corrected; 1 her own, left as
    /// made. Split in two because the body's halves can play different
    /// clips (a swing over the run): Lower is the pelvis and hips, Upper the
    /// arms and hands.</summary>
    public float Lower, Upper;
    /// <summary>Both halves at once.</summary>
    public float Native { set { Lower = Upper = value; } }
    /// <summary>Her neck as her face's sliders shape it (People.HerFace),
    /// each -1 to 1: longer or shorter (her head carried up or down along
    /// her neck) and slimmer or stronger (her neck bone scaled across it,
    /// her head given its own scale back). By her bones, not a shape key of
    /// her body: what she wears at her throat (a collar, a choker) is
    /// weighted to the same bones and follows.</summary>
    public float NeckLength, NeckWidth;
    /// <summary>How far either end of the sliders goes: metres along her
    /// neck, and how much wider or narrower across it (front to back half that).</summary>
    public const float NeckReach = 0.015f, NeckBreadth = 0.12f;
    /// <summary>--neck-cm X: her neck X cm longer (or, negative, shorter) on top of the slider, past its reach (pictures
    /// of her at other neck lengths, for the owner's choice of hers: 11 October 2026).</summary>
    static readonly float NeckShift = SurvivorUnchained.Args.Num("neck-cm", 0f) / 100f;
    /// <summary>Degrees her chin is raised, a third at her neck and the rest at her head. At creation's Look her idle
    /// carries her head bowed about 12 degrees below her portraits' level gaze, and from the Look's camera her lower
    /// face read 7-17% short and her nose low; raised 12, both meet the portrait within 2% (12 October 2026).</summary>
    public float ChinUp;
    /// <summary>--chin-up DEG: tries another (every figure with her pose).</summary>
    static readonly float? ChinUpTry = SurvivorUnchained.Args.Has("chin-up") ? SurvivorUnchained.Args.Num("chin-up", 0f) : null;
    /// <summary>--head-yaw DEG: turns her head about her neck's up axis, positive to her own left (she faces the
    /// skeleton's +Z, so +Y turns +Z toward +X, her left). --head-pitch DEG: positive lowers her chin, the opposite of
    /// --chin-up. For pictures of the neck at other turns; without them nothing changes.</summary>
    static readonly float HeadYawTry = SurvivorUnchained.Args.Num("head-yaw", 0f);
    static readonly float HeadPitchTry = SurvivorUnchained.Args.Num("head-pitch", 0f);

    /// <summary>Creation's Look only (GameFront.FigureArms sets them as the Look starts and LookOn false as it
    /// ends): her arms brought nearer her body over her own town idle, whatever Upper is. The idle (100STYLE Proud)
    /// hangs her right upper arm 21 deg out of her chest's frontal plane and her left 44 deg, its hand behind her
    /// hip and the arm rolled 47 deg in, and at the Look's camera that breadth read as a "football" (Body 5, 24
    /// October 2026). Degrees: LookArmsDownL/R turn each upper arm toward her body in the frontal plane;
    /// LookRollL/R roll each about its own length, outward (+); LookSwivelL/R swing the elbow back and in about
    /// the shoulder-to-wrist line, the hand's place and turn kept (her left hand stays at her hip). Eased in and
    /// out over LookEase seconds with the idle's crossfade; off the Look nothing here moves.</summary>
    public float LookArmsDownL, LookArmsDownR, LookRollL, LookRollR, LookSwivelL, LookSwivelR;
    public bool LookOn;
    public const float LookEase = 0.3f;
    float lookW;
    /// <summary>The Look's eased weight (0 off it, 1 on it): GameFront's framing pan rides it.</summary>
    public float LookWeight => lookW * lookW * (3 - 2 * lookW);
    /// <summary>--look-arms-down-l/-r, --look-roll-l/-r, --look-swivel-l/-r DEG: try other values on the Look
    /// (they replace GameFront's; off the Look they do nothing).</summary>
    static float? Try(string k) => SurvivorUnchained.Args.Has(k) ? SurvivorUnchained.Args.Num(k, 0f) : null;
    static readonly float? DownLTry = Try("look-arms-down-l"), DownRTry = Try("look-arms-down-r"), RollLTry = Try("look-roll-l"),
        RollRTry = Try("look-roll-r"), SwivelLTry = Try("look-swivel-l"), SwivelRTry = Try("look-swivel-r");

    /// <summary>Creation's Look only, her left hand: the town idle shapes it to rest on her hip, and with the arm
    /// rolled out on the Look it hung beside the hip, its fingers fanned against the grass at the turned Look
    /// (Body 5 judge, 24 October 2026). LookFanL (0 to 1) brings the index, ring and little finger's spread toward
    /// the middle finger's, in the palm's plane; LookCurlL (deg) bends each finger toward the palm at its knuckle
    /// and middle joint, half that at the last; LookThumbL (deg) swings the thumb from under the fingers to beside
    /// the index's middle joint. Axes come from the posed joints (the palm's plane from the knuckles and wrist), so
    /// they hold over any idle (measured: body5/hand/hand.py). Eased with LookWeight like the arm fields.</summary>
    public float LookFanL, LookCurlL, LookThumbL;
    /// <summary>--look-fan-l F, --look-curl-l DEG, --look-thumb-l DEG: try other values on the Look.</summary>
    static readonly float? FanLTry = Try("look-fan-l"), CurlLTry = Try("look-curl-l"), ThumbLTry = Try("look-thumb-l");
    int[] fingL = System.Array.Empty<int>();   // index, middle, ring, pinky: _01, _02, _03 each
    int thumb1L = -1, thumb3L = -1;

    public HerPose() { Name = "HerPose"; }

    /// <summary>The library's own pelvis at rest (UAL), against which a
    /// clip's pelvis track is written.</summary>
    static readonly Vector3 LibraryPelvis = new(0, 0.0501f, 0.9167f);

    // The bones it moves, found once (asking the skeleton for every bone's
    // name each frame made a string of each, and a frame's worth of garbage).
    Skeleton3D? found;
    int pelvis = -1, upperL = -1, upperR = -1, spine3 = -1, neck = -1, head = -1, lowerL = -1, lowerR = -1, handL = -1, handR = -1;
    int[] fingers = System.Array.Empty<int>();

    void Find(Skeleton3D sk)
    {
        found = sk;
        pelvis = sk.FindBone("pelvis");
        upperL = sk.FindBone("upperarm_l");
        upperR = sk.FindBone("upperarm_r");
        lowerL = sk.FindBone("lowerarm_l");
        lowerR = sk.FindBone("lowerarm_r");
        handL = sk.FindBone("hand_l");
        handR = sk.FindBone("hand_r");
        var fl = new System.Collections.Generic.List<int>();
        foreach (var f in new[] { "index", "middle", "ring", "pinky" })
            for (int k = 1; k <= 3; k++) fl.Add(sk.FindBone($"{f}_0{k}_l"));
        fingL = fl.Contains(-1) ? System.Array.Empty<int>() : fl.ToArray();
        thumb1L = sk.FindBone("thumb_01_l");
        thumb3L = sk.FindBone("thumb_03_l");
        spine3 = sk.FindBone("spine_03");
        neck = sk.FindBone("neck_01");
        head = sk.FindBone("Head");
        var list = new System.Collections.Generic.List<int>();
        for (int b = 0; b < sk.GetBoneCount(); b++)
        {
            var name = sk.GetBoneName(b);
            if (name.StartsWith("index") || name.StartsWith("middle") || name.StartsWith("ring") || name.StartsWith("pinky") || name.StartsWith("thumb_02") || name.StartsWith("thumb_03"))
                list.Add(b);
        }
        fingers = list.ToArray();
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        // Clips set the pelvis where the library's stands; hers stands
        // higher (longer legs): the clip's motion kept, measured from hers.
        // (Her own clips are made at her height already: the shift fades
        // with them.)
        float lib = 1 - Mathf.Clamp(Lower, 0, 1), arms = 1 - Mathf.Clamp(Upper, 0, 1);
        int pel = pelvis;
        if (pel >= 0 && lib > 0) sk.SetBonePosePosition(pel, sk.GetBonePosePosition(pel) + (sk.GetBoneRest(pel).Origin - LibraryPelvis) * lib);
        if (arms > 0)
            foreach (int b in fingers)
            {
                var rest = sk.GetBoneRest(b).Basis.GetRotationQuaternion();
                var pose = sk.GetBonePoseRotation(b);
                sk.SetBonePoseRotation(b, pose.Slerp(rest, FingerEase * arms));
            }
        if (arms > 0)
        {
            Turn(sk, upperL, Vector3.Forward, -ArmsIn * arms);
            Turn(sk, upperR, Vector3.Forward, ArmsIn * arms);
            if (NeckPitch != 0) Turn(sk, neck, Vector3.Right, NeckPitch * arms);
        }
        lookW = Mathf.MoveToward(lookW, LookOn ? 1 : 0, (float)delta / LookEase);
        if (lookW > 0) LookArms(sk, LookWeight);
        if (lib > 0)
        {
            Turn(sk, pelvis, Vector3.Forward, HipTilt * lib);
            Turn(sk, spine3, Vector3.Forward, -HipTilt * 0.5f * lib);
        }
        if (neck >= 0 && head >= 0 && (NeckLength != 0 || NeckWidth != 0 || NeckShift != 0))
        {
            // (her head bone lies along her neck bone's own length: its y)
            var along = sk.GetBoneRest(head).Origin.Normalized();
            sk.SetBonePosePosition(head, sk.GetBonePosePosition(head) + along * (NeckLength * NeckReach + NeckShift));
            var across = new Vector3(1 + NeckWidth * NeckBreadth, 1, 1 + NeckWidth * NeckBreadth * 0.5f);
            sk.SetBonePoseScale(neck, sk.GetBonePoseScale(neck) * across);
            sk.SetBonePoseScale(head, sk.GetBonePoseScale(head) / across);
        }
        float up = ChinUpTry ?? ChinUp;
        if (up != 0)
        {
            Turn(sk, neck, Vector3.Right, -up / 3);
            Turn(sk, head, Vector3.Right, -up * 2 / 3);
        }
        // Shot-only head turns, after the chin lift so they turn the head as posed. Half sits on the neck and half on
        // the head, as a real turn does (the measuring scripts posed their "N+H" turns so).
        if (HeadYawTry != 0 || HeadPitchTry != 0)
        {
            Turn(sk, neck, Vector3.Up, HeadYawTry / 2);
            Turn(sk, head, Vector3.Up, HeadYawTry / 2);
            Turn(sk, neck, Vector3.Right, HeadPitchTry / 2);
            Turn(sk, head, Vector3.Right, HeadPitchTry / 2);
        }
    }

    /// <summary>The Look's arm offset at weight w (her left is the skeleton's +X; Vector3.Forward is -Z, so a
    /// positive turn about it brings the left arm in and a negative one the right). Measured on her town idle
    /// (body5/pose/meas.py): the left and right signs below are each side's "in", "outward" and "elbow back".</summary>
    void LookArms(Skeleton3D sk, float w)
    {
        float dl = (DownLTry ?? LookArmsDownL) * w, dr = (DownRTry ?? LookArmsDownR) * w;
        float rl = (RollLTry ?? LookRollL) * w, rr = (RollRTry ?? LookRollR) * w;
        float sl = (SwivelLTry ?? LookSwivelL) * w, sr = (SwivelRTry ?? LookSwivelR) * w;
        if (dl != 0) Turn(sk, upperL, Vector3.Forward, dl);
        if (dr != 0) Turn(sk, upperR, Vector3.Forward, -dr);
        if (rl != 0) Turn(sk, upperL, Along(sk, upperL, lowerL), -rl);
        if (rr != 0) Turn(sk, upperR, Along(sk, upperR, lowerR), rr);
        if (sl != 0) { var a = Along(sk, upperL, handL); Turn(sk, upperL, a, -sl); Turn(sk, handL, a, sl); }
        if (sr != 0) { var a = Along(sk, upperR, handR); Turn(sk, upperR, a, sr); Turn(sk, handR, a, -sr); }
        float fa = (FanLTry ?? LookFanL) * w, cu = (CurlLTry ?? LookCurlL) * w, th = (ThumbLTry ?? LookThumbL) * w;
        if ((fa != 0 || cu != 0 || th != 0) && fingL.Length == 12 && handL >= 0) LookHandL(sk, fa, cu, th);
    }

    /// <summary>The palm's frame from the posed joints: across (index knuckle to little finger's), along (wrist to
    /// middle knuckle, square to across) and their cross, which points out of the back of her left hand.</summary>
    (Vector3 across, Vector3 along, Vector3 back) PalmL(Skeleton3D sk)
    {
        Vector3 P(int b) => sk.GetBoneGlobalPose(b).Origin;
        var a = (P(fingL[9]) - P(fingL[0])).Normalized();
        var m = P(fingL[3]) - P(handL); m = (m - a * a.Dot(m)).Normalized();
        return (a, m, m.Cross(a));
    }

    /// <summary>LookFanL, LookCurlL and LookThumbL at their eased values (see LookFanL).</summary>
    void LookHandL(Skeleton3D sk, float fan, float curl, float thumb)
    {
        Vector3 P(int b) => sk.GetBoneGlobalPose(b).Origin;
        Vector3 Flat(Vector3 v, Vector3 n) => (v - n * n.Dot(v)).Normalized();
        if (fan != 0)
            foreach (int f in new[] { 0, 2, 3 })   // index, ring, pinky toward the middle finger
            {
                var n = PalmL(sk).back;
                var dm = Flat(P(fingL[4]) - P(fingL[3]), n); var dp = Flat(P(fingL[f * 3 + 1]) - P(fingL[f * 3]), n);
                float spread = Mathf.RadToDeg(Mathf.Atan2(dm.Cross(dp).Dot(n), dm.Dot(dp)));
                Turn(sk, fingL[f * 3], n, -fan * spread);
            }
        if (curl != 0)
            for (int f = 0; f < 4; f++)
            {
                var n = PalmL(sk).back;
                var ax = (P(fingL[f * 3 + 1]) - P(fingL[f * 3])).Normalized().Cross(-n).Normalized();   // + toward her palm
                Turn(sk, fingL[f * 3], ax, curl);
                Turn(sk, fingL[f * 3 + 1], ax, curl);
                Turn(sk, fingL[f * 3 + 2], ax, curl / 2);
            }
        if (thumb != 0 && thumb1L >= 0 && thumb3L >= 0)
        {
            // toward a point beside the index's middle joint: 15 mm to its thumb side and 8 mm toward the palm
            var (a, _, n) = PalmL(sk);
            var t0 = P(thumb1L); var target = P(fingL[1]) - a * 0.015f - n * 0.008f;
            var axis = (P(thumb3L) - t0).Normalized().Cross((target - t0).Normalized());
            if (axis.LengthSquared() > 1e-8f) Turn(sk, thumb1L, axis.Normalized(), thumb);
        }
    }

    /// <summary>The line from one bone's head to another's, in the skeleton's space.</summary>
    static Vector3 Along(Skeleton3D sk, int from, int to) =>
        from < 0 || to < 0 ? Vector3.Down : (sk.GetBoneGlobalPose(to).Origin - sk.GetBoneGlobalPose(from).Origin).Normalized();

    /// <summary>A bone turned about an axis of the skeleton's own space, by
    /// `degrees`, about its head.</summary>
    static void Turn(Skeleton3D sk, int b, Vector3 axis, float degrees)
    {
        if (b < 0) return;
        var g = sk.GetBoneGlobalPose(b);
        var r = new Basis(axis, Mathf.DegToRad(degrees));
        var ng = new Transform3D(r * g.Basis, g.Origin);
        int p = sk.GetBoneParent(b);
        var local = p >= 0 ? sk.GetBoneGlobalPose(p).AffineInverse() * ng : ng;
        sk.SetBonePoseRotation(b, local.Basis.GetRotationQuaternion());
    }
}
