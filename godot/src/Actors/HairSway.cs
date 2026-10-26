using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her hair's swing, given to her hair's shader (shaders/heroine_hair.gdshader).
/// A style that hangs (a tail, a braid, long hair down her back) has a chain
/// (heroine_hair_&lt;style&gt;.chain.json, from tools/assets/heroine_hair.py):
/// a line of points down the middle of what hangs. Here it is a rope of
/// masses, pinned at its root, carried by its bone, falling under its own
/// weight, holding its length, drawn gently back toward how it hangs at rest,
/// and kept out of her head, neck and back; how far each point has swung
/// from where it would hang goes to the shader, which moves the hair along
/// it with it. So a stride, a stop or a turn sets it swinging, and when she
/// leans into a run it falls away from her back rather than through it.
/// A style without one (short hair) has a single mass on a spring below her
/// head, its lag moving the ends a little.
/// </summary>
public partial class HairSway : Node
{
    /// <summary>Her hairstyle (its chain's file).</summary>
    [Export] public string Style = "";
    /// <summary>Overall strength: 0 still, 1 as tuned.</summary>
    [Export] public float Amount = 1f;

    // The single mass: about one and a half swings a second, dying away over
    // two or three (hair is heavier and slower than flesh).
    const float Stiffness = 90f, Damping = 4.5f, Reach = 0.12f;
    // Where it hangs from her head, in her skeleton's space at rest (she
    // faces +Z): a hand below it and a little behind.
    static readonly Vector3 Hang = new(0, -0.25f, -0.08f);

    /// <summary>A ball the chain is kept out of (W: stretched that far each way across her back). Behind: one down her neck and back, which pushes it out behind her
    /// only. (On all fours in chain_haul, her head up, where her tail would hang from her head runs through her
    /// chest; pushed out the nearest way, the chain came out of her front. What hangs from her head is never in
    /// front of her chest. The tip that showed in her plunge, outfits judge h1, 11 October 2026, was her tail not
    /// swinging at all: its weights reached the shader upside down, tools/scratch/face17/uv2flip.py.)</summary>
    sealed class Ball { public int Bone; public Vector3 At; public float R, W, WB, Bulge, Pad; public bool Behind, OutOnly; }

    // Her forearms, from the elbow to past the fist, in the skeleton's space at rest: the shader pushes her hair out of
    // them (a lock by her ear as her throwing arm comes past her head, animation judge 20), and balls at her shoulders and
    // upper arms keep the chain out (a braid falling beside her as she lies face down). The balls' radii are her limb's
    // with its pauldron and half a braid; the shader's her forearm's with its bracer, as her hair is its surface.
    int[] foreBone = [], fistBone = [];
    Vector3[] elbowRest = [], fistRest = [];
    const float ForearmR = 0.05f;
    Vector3[] arms = new Vector3[4], armsThen = new Vector3[4];

    MeshInstance3D? mesh;
    Skeleton3D? sk;
    int head = -1;
    Vector3 p, v;
    bool live;
    // The chain: its bone, its points at rest (skeleton space), now and a
    // step ago (world), its links' lengths, what it is kept out of.
    int bone = -1;
    Transform3D bind = Transform3D.Identity;
    float stiff, bend, corner;
    Vector3[] rest = [], x = [], xp = [];
    // Read-only view of the chain's world points (root first), for the HAIRCLEAR debug in anim_review.gd.
    public Vector3[] ChainWorld => x;
    float[] link = [];
    Ball[] balls = [];
    // Its own stiffness once the hold has let go (bend, from its file: a braid's a little more than a tail's or long
    // hair's), kept within 60 degrees at each joint and its first link within 75 of how it leaves her head: with none it
    // buckled into knots and coils as she fell, and hooked at the tie (hair judge hj2, death).
    static readonly float Cap = Mathf.DegToRad(60), Cone = Mathf.DegToRad(75);
    // Each correction that keeps it its length is mostly not made a speed (0.9, "dynamic follow the leader", Müller
    // 2012): made one, the chain whipped and knotted as her head fell 1.5 m at 2.3 m/s. And its speed against her head
    // dies 3% a step, as hair moves with the air about her. Both, the push of its rest out of her, the bend and the
    // limits act only as far as the hold has let go: held, a braid's swing over her shoulder as she threw was 5 cm
    // smaller, and the tie's limit cut a tail's swing by 8 (hair judge hj2 passed them held).
    const float Follow = 0.9f, Drag = 0.03f;
    // This frame's: where the chain's points would hang, and the balls they are kept out of.
    Vector3[] target = new Vector3[8], pushed = new Vector3[8], corr = new Vector3[8], at = [], back = [], across = [];
    float[] hold = new float[8], grip = new float[8], free = new float[8];
    Vector3[] vel = new Vector3[8], touch = new Vector3[8], start = new Vector3[8], surf = new Vector3[8];
    // Last frame's balls: how fast a surface it touches moves (contact keeps pace with her body falling away from it:
    // stopped dead in the world, long hair was left 6-14 cm in the air as her back fell away at 2 m/s, death c8).
    Vector3[] atThen = [], acrossThen = [];
    int stepsNow = 1;
    bool[] grounded = new bool[8];
    // How long since any of it lay on the ground, and since each point's rest last stopped hanging down.
    float offFloor = 1e3f;
    float[] hungFor = new float[8];
    Vector3 rootThen;
    // What the shader is given (in the mesh's space): this frame's swing and where her head
    // is, and last frame's, for the motion vectors (MotionClock).
    Vector3 sway, headAt;
    Basis headTurn = Basis.Identity;
    Vector3[] swung = new Vector3[8], swungThen = new Vector3[8];
    // And the chain at rest (where it hangs, carried by its bone) and how each place along it has turned, so the shader
    // turns her hair with it, not only moves it (moved only, a braid swung sideways went edge-on flat, and cards burst
    // where it bent).
    Vector3[] restAt = new Vector3[8], restThen = new Vector3[8];
    Vector4[] turnAt = new Vector4[8], turnThen = new Vector4[8];
    bool drawn;
    // The laid shape (hair solver 6, after five rounds of physics left the swing flagging and rodding as she lay down
    // and got up: hair judge hj3). Of a procedural drape, the chain frozen where it lies, or shapes set by hand, the
    // drape: it needs nothing per style or per clip and works for any fall or get-up. It is the chain with no
    // momentum: carried with its root's move (not its turn), settled under gravity, kept out of her and off the floor,
    // so it lies on her back or the ground as she lies, and hangs as she sits or crouches; with no speed of its own it
    // can't stream out as a flag or stand off as a rod. How far she is down (her upper back's height over the floor
    // and her spine's lean from upright) blends the swing into it; once down it is held until she is up (her head
    // high, her spine upright), then the swing comes back over half a second, started from the drape.
    float down;
    Vector3[] drape = new Vector3[8];
    Vector3 drapeRoot, rootPrev;
    int[] neckBalls = [], backBalls = [], lowBalls = [];
    const float DownLo = 0.45f, DownHi = 0.95f, FlatLo = 0.3f, FlatHi = 0.7f, UpLo = 1.1f, UpHi = 1.35f, UprightLo = 0.8f, UprightHi = 0.95f,
        DownRise = 0.7f, DownFall = 0.5f, DrapeStep = 0.02f;
    const int DrapePasses = 4;
    // The round carry (hair solver 8). Getting up from all fours, her neck came up into the tail or braid hanging below her
    // face, and the drape (carried with her move, not her turn) kept it down the front of her throat until she stood, then
    // flipped it behind her in a frame (hair judge hj4, get_up c8-c14). So once she has been fully down and is rising (her
    // head over 70 cm up, her spine past 0.45 upright), what hangs in front of her neck and chest is swung round her near
    // side about her spine's line through her neck (pushed out of her sideways, never through her neck) to her back, at
    // most 180 degrees in 0.35 s, and the swing is not given back until it is round. Only a tail or a braid (tied at her
    // head): long hair falling forward over both shoulders is natural, and passed.
    bool laidFull; int side; int fileBalls;
    readonly bool[] round = new bool[8];
    const float RoundLo = 0.45f, RoundHi = 0.85f, RoundHead = 0.7f, RoundFront = 0.015f, RoundTop = 0.12f, RoundTime = 0.35f;
    static readonly float RoundTo = Mathf.DegToRad(60);

    public HairSway() { Name = "HairSway"; }

    /// <summary>Hang it as it hangs at rest in her pose now, still: after a cut that sets her pose afresh (a
    /// review sheet seeking back to a clip's start, a cinematic's handover), so the jump isn't a fling.</summary>
    public void Settle() { live = false; }

    public override void _Ready()
    {
        mesh = GetParent() as MeshInstance3D;
        sk = mesh?.GetParent() as Skeleton3D;
        if (sk == null) return;
        // Stepped once her skeleton's final pose is made (SkeletonUpdated: her modifiers' corrections in it, HerCarriage's
        // lift of her chest and head and the rest), as she is drawn. (18 October, face 30: stepped in _Process, it read
        // her pose before them, so the chain's rest and her balls stood where her head and back were before the lift,
        // and the hair it carries, skinned on the lifted head, hung 3-9 cm off its chain, into her back: a braid's
        // lower half and its tie, a tail's tips. If no pose is made in a frame, _Process steps it. OLDPOSE=1 as before.)
        if (!OS.HasEnvironment("OLDPOSE")) sk.SkeletonUpdated += OnPosed;
        head = sk.FindBone("Head");
        FindForearms();
        var file = $"res://art/people/heroine_hair_{Style}.chain.json";
        if (Style == "" || !FileAccess.FileExists(file)) return;
        var d = Json.ParseString(FileAccess.GetFileAsString(file)).AsGodotDictionary();
        bone = sk.FindBone((string)d["bone"]);
        // Its rest carried as the hair itself is skinned: by its own skin's bind of that bone (the hair's file's), not
        // her skeleton's rest. (18 October, face 30: her skeleton's Head rest is not the one the hair was built and
        // bound on (her neck's rebuild), so the chain's rest stood 2-9 cm behind the hair down a braid or tail: the
        // chain lay on her back, kept out of her, and the hair it carries hung 6-9 cm into her, a braid's lower half
        // and its tie gone into her back at the Look. NOBIND=1 uses her skeleton's rest again, to compare.)
        bind = sk.GetBoneGlobalRest(bone).AffineInverse();
        if (mesh!.Skin is { } skin && !OS.HasEnvironment("NOBIND"))
            for (int i = 0; i < skin.GetBindCount(); i++)
                if (skin.GetBindName(i) == (string)d["bone"] || (skin.GetBindName(i) == "" && skin.GetBindBone(i) == bone)) { bind = skin.GetBindPose(i); break; }
        stiff = (float)d["stiff"];
        bend = d.ContainsKey("bend") ? (float)d["bend"] : 0.03f;
        corner = d.ContainsKey("corner") ? Mathf.DegToRad((float)d["corner"]) : 0f;
        var pts = d["points"].AsGodotArray();
        rest = new Vector3[pts.Count];
        for (int i = 0; i < rest.Length; i++) rest[i] = Vec(pts[i]);
        link = new float[rest.Length];
        for (int i = 1; i < rest.Length; i++) link[i] = rest[i].DistanceTo(rest[i - 1]);
        var bs = d["spheres"].AsGodotArray();
        var list = new System.Collections.Generic.List<Ball>();
        for (int i = 0; i < bs.Count; i++)
        {
            var b = bs[i].AsGodotDictionary();
            var name = (string)b["bone"];
            list.Add(new Ball { Bone = sk.FindBone(name), At = Vec(b["at"]), R = (float)b["r"], Behind = name.StartsWith("neck") || name.StartsWith("spine") });
            // Her back is wide and flat: those down her spine are stretched 6 cm each way across it (as far back as at her
            // spine to 6 cm out, and reaching her sides), so a braid that swings over her shoulder as she throws and then
            // bends forward lies on her back, not 2-4 cm into it beside her spine, hidden (hair judge hj2).
            if (name.StartsWith("spine")) list[^1].W = 0.06f;
            // And toward her back they reach wider still and further back (face 30): her back is flat across her shoulder
            // blades, which stand 1.4-1.9 cm further back than her spine's furrow (the balls' reach is set at her spine),
            // so a tail swung aside as she spun at the Look (135-360 degrees a second) lay along the balls' curve with its
            // strands 1-1.5 cm into her shoulder blade and the warden's straps. So each spine ball's line widens toward her
            // back (to 8 cm each way at her waist, 14 at her shoulder blades) and reaches out by up to 1.6 cm more from 0.5
            // to 4 cm off her middle, where her shoulder blades rise (her middle, as the hair hangs, is as it was). Only
            // toward her back: sideways and in front they are as they were. Env NOBACKWIDE=1 leaves it out, to compare.
            if (name.StartsWith("spine")) { list[^1].WB = Lerp3(BackY, BackW, list[^1].At.Y); list[^1].Bulge = Lerp3(BackY, BackOut, list[^1].At.Y); }
        }
        // (her shoulders and upper arms only: her forearm and fist sweeping past her head as she threw kicked the chain
        // up over her head, hair judge hj1; the shader keeps her hair out of her forearms)
        foreach (var (shoulder, elbow, _) in Limbs())
        {
            Vector3 s = sk.GetBoneGlobalRest(shoulder).Origin, e = sk.GetBoneGlobalRest(elbow).Origin;
            list.Add(new Ball { Bone = shoulder, At = s, R = 0.08f + ArmPad, Pad = ArmPad });
            list.Add(new Ball { Bone = shoulder, At = s.Lerp(e, 0.5f), R = 0.065f + ArmPad, Pad = ArmPad });
        }
        // (and the hair's own thickness on them, as the balls down her back have it, and one more between them: a tail
        // flung round her at 360 degrees a second went 1-1.5 cm into the back of her arm in the waist between the two,
        // and over her shoulder into the warden's pauldron. Kept for the swing alone: lying, the drape has its own pad.)
        foreach (var (shoulder, elbow, _) in Limbs())
        {
            Vector3 s = sk.GetBoneGlobalRest(shoulder).Origin, e = sk.GetBoneGlobalRest(elbow).Origin;
            list.Add(new Ball { Bone = shoulder, At = s.Lerp(e, 0.25f), R = 0.072f + ArmPad, Pad = ArmPad, OutOnly = true });
        }
        balls = list.ToArray();
        fileBalls = bs.Count;
        int[] Of(string n) { var l = new System.Collections.Generic.List<int>(); for (int k = 0; k < bs.Count; k++) if ((string)bs[k].AsGodotDictionary()["bone"] == n) l.Add(k); return l.ToArray(); }
        neckBalls = Of("neck_01"); backBalls = Of("spine_03"); lowBalls = Of("spine_01");
        ridgeBone = backBalls.Length > 0 ? balls[backBalls[0]].Bone : -1;
        bool can = ridgeBone >= 0 && balls.Length >= fileBalls + 4 && !OS.HasEnvironment("NORIDGE");
        pony = can && Style == "ponytail" && !OS.HasEnvironment("NOPONYRIDGE");
        ridge = can && Style == "braid" || pony;
    }

    // (her back toward its spine balls, by height in her skeleton's rest: each line's half-width, and how much further
    // out it reaches beside her middle; that from BackFrom to BackTo off her middle; her arm balls' pad)
    static readonly float[] BackY = [1.30f, 1.40f, 1.50f], BackW = [0.08f, 0.12f, 0.14f], BackOut = [0.008f, 0.016f, 0.016f];
    const float BackFrom = 0.005f, BackTo = 0.04f, ArmPad = 0.022f;
    static readonly bool NoBackWide = OS.HasEnvironment("NOBACKWIDE");
    static float Lerp3(float[] xs, float[] ys, float y)
    {
        if (y <= xs[0]) return ys[0];
        if (y >= xs[^1]) return ys[^1];
        int k = 1; while (xs[k] < y) k++;
        return Mathf.Lerp(ys[k - 1], ys[k], (y - xs[k - 1]) / (xs[k] - xs[k - 1]));
    }

    /// <summary>Her arms' bones (shoulder, elbow, hand), each side that has them.</summary>
    System.Collections.Generic.IEnumerable<(int, int, int)> Limbs()
    {
        foreach (var s in new[] { "l", "r" })
        {
            int u = sk!.FindBone("upperarm_" + s), l = sk.FindBone("lowerarm_" + s), h = sk.FindBone("hand_" + s);
            if (u >= 0 && l >= 0 && h >= 0) yield return (u, l, h);
        }
    }

    void FindForearms()
    {
        var f = new System.Collections.Generic.List<(int, int, Vector3, Vector3)>();
        foreach (var (_, elbow, fist) in Limbs())
        {
            Vector3 e = sk!.GetBoneGlobalRest(elbow).Origin, h = sk.GetBoneGlobalRest(fist).Origin;
            f.Add((elbow, fist, e, h + (h - e).Normalized() * 0.05f));
        }
        foreBone = f.ConvertAll(a => a.Item1).ToArray();
        fistBone = f.ConvertAll(a => a.Item2).ToArray();
        elbowRest = f.ConvertAll(a => a.Item3).ToArray();
        fistRest = f.ConvertAll(a => a.Item4).ToArray();
    }

    static Vector3 Vec(Variant v)
    {
        var a = v.AsGodotArray();
        return new Vector3((float)a[0], (float)a[1], (float)a[2]);
    }

    /// <summary>A bone's move from rest, in the skeleton's space.</summary>
    Transform3D Moved(int b) => sk!.GetBoneGlobalPose(b) * sk.GetBoneGlobalRest(b).AffineInverse();

    /// <summary>A point kept out of the balls (i: the chain's point it is, which then touches; -1 none).</summary>
    Vector3 Out(Vector3 q, float scale, int i, Vector3? came = null)
    {
        var q0 = q;
        for (int b = 0; b < balls.Length; b++)
        {
            // (the nearest point of its line across her back)
            var w = across[b];
            float ww = w.LengthSquared();
            var c = ww > 0 ? at[b] + w * Mathf.Clamp((q - at[b]).Dot(w) / ww, -1f, 1f) : at[b];
            var off = q - c;
            float r = balls[b].R * scale;
            if (balls[b].WB > balls[b].W && ww > 0 && off.Dot(back[b]) > 0 && !NoBackWide)
            {
                var w2 = w * (1f + (balls[b].WB / balls[b].W - 1f) * Mathf.SmoothStep(0f, 1f, off.Dot(back[b]) / r));
                c = at[b] + w2 * Mathf.Clamp((q - at[b]).Dot(w2) / w2.LengthSquared(), -1f, 1f);
                off = q - c;
                float u = Mathf.Abs((q - at[b]).Dot(w)) / Mathf.Sqrt(ww) / scale;
                r += balls[b].Bulge * scale * Mathf.SmoothStep(BackFrom, BackTo, u) * Mathf.SmoothStep(0f, 1f, off.Dot(back[b]) / r);
            }
            if (off.LengthSquared() >= r * r) continue;
            // (in front of a ball down her back: mirrored behind it, then out)
            // (but not one that was in front of it already, lying beside her as she lies face down, once the hold has let
            // go: mirrored, a braid by her shoulder jumped 10 cm up onto her back, death c13)
            if (balls[b].Behind && off.Dot(back[b]) < 0 && !(i > 0 && free[i] > 0.5f && (start[i] - c).Dot(back[b]) < 0)
                && !(came is Vector3 cf && (cf - c).Dot(back[b]) < 0))
                off -= 2 * off.Dot(back[b]) * back[b];
            var n = off.LengthSquared() > 1e-10f ? off.Normalized() : back[b];
            q = c + n * r;
            if (i > 0)
            {
                touch[i] = n; grip[i] = Mathf.Max(grip[i], 0.1f);
                float t = ww > 0 ? Mathf.Clamp((q0 - at[b]).Dot(w) / ww, -1f, 1f) : 0;
                surf[i] = atThen.Length == balls.Length ? (c - (atThen[b] + acrossThen[b] * t)) / stepsNow : Vector3.Zero;
            }
        }
        return q;
    }

    /// <summary>A direction kept within an angle of another (both of unit length).</summary>
    static Vector3 Within(Vector3 dir, Vector3 want, float most)
    {
        if (dir.Dot(want) >= Mathf.Cos(most)) return dir;
        var axis = want.Cross(dir);
        if (axis.LengthSquared() < 1e-12f) axis = want.Cross(Mathf.Abs(want.X) < 0.9f ? Vector3.Right : Vector3.Back);
        return want.Rotated(axis.Normalized(), most);
    }

    double pending = -1;
    ulong posedFrame;

    public override void _Process(double delta)
    {
        if (OS.HasEnvironment("OLDPOSE") || Engine.GetProcessFrames() > posedFrame + 2) { pending = -1; Step(delta); return; }
        pending = System.Math.Max(pending, 0) + delta;
    }

    void OnPosed()
    {
        if (!IsInstanceValid(this) || !IsInsideTree()) return;
        posedFrame = Engine.GetProcessFrames();
        if (pending < 0) return;
        var d = pending;
        pending = -1;
        Step(d);
    }

    public override void _ExitTree()
    {
        if (sk != null && IsInstanceValid(sk)) sk.SkeletonUpdated -= OnPosed;
    }

    void Step(double delta)
    {
        if (mesh == null || sk == null || head < 0) return;
        float dt = Mathf.Clamp((float)delta, 0f, 1f / 20);
        var local = mesh.GlobalTransform.AffineInverse();
        var world = sk.GlobalTransform;
        var pose = sk.GetBoneGlobalPose(head);
        // Last frame's swing is kept for the motion vectors' look back (MotionClock); this frame's is made afresh.
        (swungThen, swung) = (swung, swungThen);
        System.Array.Clear(swung);
        (restThen, restAt) = (restAt, restThen);
        (turnThen, turnAt) = (turnAt, turnThen);
        System.Array.Fill(turnAt, new Vector4(0, 0, 0, 1));
        System.Array.Clear(restAt);
        var swayThen = sway;
        var headThen = headAt;
        sway = Vector3.Zero;
        if (bone >= 0 && rest.Length == 8)
        {
            var moved = world * (sk.GetBoneGlobalPose(bone) * bind);
            for (int i = 0; i < 8; i++) target[i] = moved * rest[i];
            if (at.Length != balls.Length) { at = new Vector3[balls.Length]; back = new Vector3[balls.Length]; across = new Vector3[balls.Length]; }
            for (int i = 0; i < balls.Length; i++)
            {
                var mv = Moved(balls[i].Bone);
                at[i] = world * (mv * balls[i].At);
                back[i] = (world.Basis * mv.Basis * Vector3.Forward).Normalized();   // (her back: -z at rest)
                across[i] = world.Basis * mv.Basis * new Vector3(balls[i].W, 0, 0);    // (her left to right, its half-width)
            }
            // How stiff each point is held to its rest: all of it while its rest hangs down from the root (within about
            // 30 degrees: she leans into a run or a throw, and long hair lies on her back as it did), none once that rest
            // is level or up (lying, folded forward, her head tipped back): its rest is gravity's shape as she stands,
            // and held to it as she lay or folded it stood off her as a rod (judge 20, hair judge hj2).
            // It is let go at once, but taken back over half a second, and not while it lies on the ground: taken back
            // at once, a braid lying by her face as her head rolled over was snatched up into a rod (hair judge hj1).
            // And it's taken back for the whole chain or not at all: not while any of it lies on the ground or for half a
            // second after (a tail's free end stiffened and hooked up off its middle pinned on the floor), and at each point
            // only once its rest has hung down for half a second unbroken.
            bool lying = false;
            for (int i = 1; i < 8; i++) { lying |= grounded[i]; grounded[i] = false; }
            offFloor = lying ? 0 : offFloor + dt;
            for (int i = 1; i < 8; i++)
            {
                // (and none at all by 57 degrees: held so, a braid hanging from her bowed head stood off her back as a
                // rod as she dropped to her knees, death c4; from 40 degrees down as it was, so a run or a throw is unchanged)
                float dn = (target[i] - target[0]).Normalized().Dot(Vector3.Down);
                float u = Mathf.SmoothStep(0.35f, 0.85f, dn) * Mathf.SmoothStep(0.55f, 0.77f, dn);
                float want = stiff * u;
                hungFor[i] = u > 0.98f ? hungFor[i] + dt : 0;
                if (!live || want <= hold[i]) hold[i] = want;
                else if (offFloor > 0.5f && hungFor[i] > 0.5f) hold[i] = Mathf.Min(want, hold[i] + stiff * dt / 0.5f);
            }
            // (her skeleton is scaled: its links' lengths and the balls' sizes are taken as she is drawn, not from the
            // file, which left the chain 4% short, its tip 2 cm high)
            float scale = world.Basis.Scale.X;
            if (!live || dt <= 0)
            {
                x = (Vector3[])target.Clone(); xp = (Vector3[])target.Clone(); rootThen = target[0]; offFloor = 1e3f; live = true; atThen = []; justSettled = true;
                for (int i = 1; i < 8; i++) link[i] = target[i].DistanceTo(target[i - 1]);
            }
            if (OS.HasEnvironment("HAIRDUMP")) Dump(dt, world.Origin.Y);
            // Steps of about 1/120 s whatever the frame rate (four at 30 fps, as it was tuned and judged): the
            // stiffness and the damping are per step, so at 60 fps four steps held it twice as stiff.
            int steps = Mathf.Max(1, Mathf.CeilToInt(dt * 120f - 1e-3f));
            float h = dt / steps;
            stepsNow = steps;
            var fall = new Vector3(0, -9.8f, 0) * h * h;
            // (the ground she stands or lies on: her skeleton's own floor)
            float floor = world.Origin.Y + 0.015f;
            // Where it's held to: its rest, but out of her and off the ground (as she folds, its rest lies inside her
            // back, and the hold drew it in, to be pushed out each pass, a knot at the root).
            for (int i = 0; i < 8; i++) free[i] = stiff > 0 ? 1f - hold[i] / stiff : 1f;
            pushed[0] = target[0];
            for (int i = 1; i < 8; i++)
            {
                var q = Out(target[i], scale, -1);
                q.Y = Mathf.Max(q.Y, floor);
                pushed[i] = target[i] + (q - target[i]) * free[i];
            }
            // Its root's own step, and how fast the rest may move against it: 2.5 m/s (a whipped tail's tip moves about
            // that fast against her head); pushed by her arm or snatched back to its rest, it was thrown 70 cm in two
            // frames (hair judge hj1, throw).
            var rootStep = (target[0] - rootThen) / steps;
            rootThen = target[0];
            float most = 2.5f * h;
            for (int s = 0; s < steps; s++)
            {
                for (int i = 1; i < 8; i++)
                {
                    var was = x[i];
                    start[i] = was;
                    vel[i] = (x[i] - xp[i]) * 0.985f;
                    var rel = (vel[i] - rootStep) * (1f - Drag * free[i]);
                    if (rel.LengthSquared() > most * most) rel = rel.Normalized() * most;
                    vel[i] = rootStep + rel;
                    x[i] += vel[i] + fall;
                    xp[i] = was;
                }
                x[0] = target[0];
                for (int k = 0; k < 3; k++)
                {
                    // A braid (its file's corner) bent past that angle where the hold still has it rounds the corner by the
                    // corner moving toward the middle of its neighbours, not as a speed (as the bend): flung over her
                    // shoulder as she threw, it lodged on her trapezius beside her neck, and nothing pulls a held point
                    // down from below (the links are kept by moving what hangs), so it showed a Z for half a second (hair
                    // judge hj4). Capped the other way, as the free chain is, the rest of it was thrown over her shoulder
                    // (hair solver 9); a tail's or long hair's throw moved 3-12 cm with it, so it is the braid's alone.
                    if (corner > 0)
                        for (int i = 1; i < 7; i++)
                        {
                            float th = Mathf.Acos(Mathf.Clamp((x[i] - x[i - 1]).Normalized().Dot((x[i + 1] - x[i]).Normalized()), -1f, 1f));
                            if (th <= corner) continue;
                            var mv = ((x[i - 1] + x[i + 1]) * 0.5f - x[i]) * (0.5f * Mathf.SmoothStep(corner, corner + Mathf.DegToRad(30), th) * (1f - free[i]));
                            x[i] += mv; xp[i] += mv;
                        }
                    // (how each link turned from its rest, carried down the chain: the next link's rest bend is kept from it)
                    var turn = Quaternion.Identity;
                    for (int i = 1; i < 8; i++)
                    {
                        x[i] += (pushed[i] - x[i]) * hold[i];
                        var restDir = (target[i] - target[i - 1]).Normalized();
                        var wantDir = turn * restDir;
                        var dir = (x[i] - x[i - 1]).Normalized();
                        // Bent back toward its rest as far as the hold has let go, without that becoming a speed (made
                        // one, a tail swaying as she stopped was pumped into swinging side to side).
                        float kb = i == 1 ? 0 : bend * free[i];
                        var bent = kb > 0 ? (dir + (wantDir - dir) * kb).Normalized() : dir;
                        // (the limit opens out toward none as the hold comes back)
                        float limit = (i == 1 ? Cone : Cap) + (Mathf.Pi - (i == 1 ? Cone : Cap)) * (1f - free[i]);
                        if (free[i] > 0.02f && limit < Mathf.Pi - 1e-6f) bent = Within(bent, wantDir, limit);
                        xp[i] += (bent - dir) * link[i];
                        var to = x[i - 1] + bent * link[i];
                        corr[i] = to - x[i];
                        x[i] = to;
                        x[i] = Out(x[i], scale, i);
                        if (x[i].Y < floor) { x[i].Y = floor; touch[i] = Vector3.Up; grip[i] = 0.5f; grounded[i] = true; surf[i] = Vector3.Zero; }
                        if (i < 7) turn = new Quaternion(restDir, (x[i] - x[i - 1]).Normalized());
                    }
                }
                for (int i = 1; i < 7; i++) xp[i] += Follow * free[i] * corr[i + 1];
                // What touches her or the ground is stopped going into it, not thrown back out (being pushed out of her
                // was a velocity: a tail lying by her head as it settled was flung up off the floor), and slowed along it.
                for (int i = 1; i < 8; i++)
                {
                    if (grip[i] == 0) continue;
                    // Once the hold has let go, against her body as it moves: a surface falling away from it carries it at
                    // its own pace along the normal (one coming at it still gives it no speed: no fling).
                    var n = touch[i];
                    var u = n * Mathf.Min(0f, surf[i].Dot(n)) * Mathf.SmoothStep(0.1f, 0.5f, free[i]);
                    var r = vel[i] - u;
                    r -= n * Mathf.Min(0f, r.Dot(n));
                    xp[i] = x[i] - u - r * (1f - grip[i]);
                    grip[i] = 0; surf[i] = Vector3.Zero;
                }
            }
            Lay(dt, world.Origin.Y, floor, scale);
            if (atThen.Length != balls.Length) { atThen = new Vector3[balls.Length]; acrossThen = new Vector3[balls.Length]; }
            System.Array.Copy(at, atThen, balls.Length); System.Array.Copy(across, acrossThen, balls.Length);
            for (int i = 0; i < 8; i++) swung[i] = local.Basis * ((down > 0 && down < 1 - 1e-4f && i > 0 ? lay[i] : x[i]) - target[i]) * Amount;
            Turn(local);
            if (OS.HasEnvironment("HAIRDRAW")) Draw();
            if (OS.HasEnvironment("HAIRBODY"))
            {
                // (each point in her body's rest space, by spine_03: to check against her torso's shape)
                var inv = (world * Moved(sk.FindBone("spine_03"))).AffineInverse();
                var line = $"HAIRBODY f{Engine.GetProcessFrames()}";
                for (int i = 0; i < 8; i++) { var q = inv * x[i]; line += $" {q.X:F3},{q.Y:F3},{q.Z:F3}"; }
                GD.Print(line);
            }
            if (OS.HasEnvironment("HAIRDEBUG") && Engine.GetProcessFrames() % 20 == 0)
            {
                float inside = 0;
                for (int i = 1; i < 8; i++)
                    for (int b = 0; b < balls.Length; b++)
                        inside = Mathf.Max(inside, balls[b].R - target[i].DistanceTo(at[b]));
                GD.Print($"HAIR swung {swung[7]} max-in {inside:F3} tgt7 {target[7]} x7 {x[7]}");
            }
        }
        else
        {
            var turned = pose.Basis * sk.GetBoneGlobalRest(head).Basis.Inverse();
            var single = world * (pose.Origin + turned * Hang);
            if (!live || dt <= 0) { p = single; v = Vector3.Zero; live = true; }
            const int steps = 4;
            float h = dt / steps;
            for (int i = 0; i < steps; i++)
            {
                v += (Stiffness * (single - p) - Damping * v) * h;
                p += v * h;
            }
            var off = p - single;
            if (off.Length() > Reach) { off = off.Normalized() * Reach; p = single + off; }
            sway = local.Basis * off * Amount;
        }
        headAt = local * (world * pose.Origin);
        // (her head's turn from its rest, in the hair's own space: the shader's highlights pick her front and crown
        // locks by where they lie on her head at rest, so a lock keeps its colour as she turns her head)
        var lw = (local * world).Basis;
        headTurn = (lw * (pose.Basis * sk.GetBoneGlobalRest(head).Basis.Inverse()) * lw.Inverse()).Orthonormalized();
        (armsThen, arms) = (arms, armsThen);
        for (int a = 0; a < 2; a++)
        {
            bool has = a < foreBone.Length;
            arms[2 * a] = has ? local * (world * (Moved(foreBone[a]) * elbowRest[a])) : Vector3.Zero;
            arms[2 * a + 1] = has ? local * (world * (Moved(fistBone[a]) * fistRest[a])) : Vector3.Zero;
        }
        // (Its first frame has no last: it stood as it stands.)
        if (!drawn) { swayThen = sway; headThen = headAt; System.Array.Copy(swung, swungThen, 8); System.Array.Copy(arms, armsThen, 4); System.Array.Copy(restAt, restThen, 8); System.Array.Copy(turnAt, turnThen, 8); drawn = true; }
        // (The basis and the arrays made into Godot's values once a frame and freed as soon as they are given, not per
        // pass and left to the collector: each is a tracked, finalized wrapper that outlived the young collection, ~60%
        // of what every collection kept in play, and the cause of its 10-30 ms pauses.)
        using Variant vTurn = headTurn, vChain = swung, vChainThen = swungThen, vArms = arms, vArmsThen = armsThen,
            vRest = restAt, vRestThen = restThen, vTurnAt = turnAt, vTurnThen = turnThen;
        float armR = foreBone.Length > 0 ? ForearmR : 0f;
        for (int s = 0; s < mesh.Mesh.GetSurfaceCount(); s++)
            if (mesh.GetSurfaceOverrideMaterial(s) is ShaderMaterial first)
                for (var m = first; m != null; m = m.NextPass as ShaderMaterial)   // (a blended pass over its solid parts swings with them: HairDraw.Passes)
                {
                    m.SetShaderParameter(SwayName, sway);
                    m.SetShaderParameter(HeadName, headAt);
                    m.SetShaderParameter(HeadTurnName, vTurn);
                    m.SetShaderParameter(ChainName, vChain);
                    m.SetShaderParameter(SwayThenName, swayThen);
                    m.SetShaderParameter(HeadThenName, headThen);
                    m.SetShaderParameter(ChainThenName, vChainThen);
                    m.SetShaderParameter(ArmsName, vArms);
                    m.SetShaderParameter(ArmsThenName, vArmsThen);
                    m.SetShaderParameter(ArmRName, armR);
                    m.SetShaderParameter(RestName, vRest);
                    m.SetShaderParameter(RestThenName, vRestThen);
                    m.SetShaderParameter(TurnName, vTurnAt);
                    m.SetShaderParameter(TurnThenName, vTurnThen);
                }
    }

    static Vector3 Mean(Vector3[] a, int[] k) { var m = Vector3.Zero; foreach (var j in k) m += a[j]; return k.Length > 0 ? m / k.Length : m; }

    /// <summary>The laid shape (see the fields): the down weight, the drape, the chain blended into it, and the swing
    /// started from it while she is fully down.</summary>
    void Lay(float dt, float ground, float floor, float scale)
    {
        if (neckBalls.Length == 0 || backBalls.Length == 0 || lowBalls.Length == 0) return;
        bool first = !drawn || down < 0;
        Vector3 neck = Mean(at, neckBalls), low = Mean(at, lowBalls);
        float upright = (neck - low).Normalized().Y, backH = Mean(at, backBalls).Y - ground;
        float headH = (sk!.GlobalTransform * sk.GetBoneGlobalPose(head).Origin).Y - ground;
        float d = (1 - Mathf.SmoothStep(DownLo, DownHi, backH)) * (1 - Mathf.SmoothStep(FlatLo, FlatHi, upright));
        float up = Mathf.SmoothStep(UpLo, UpHi, headH) * Mathf.SmoothStep(UprightLo, UprightHi, upright);
        bool carrying = System.Array.IndexOf(round, true) >= 0;
        if (first || justSettled) down = d;
        else if (d > down) down = Mathf.Min(d, down + dt / DownRise);
        else if (!carrying) down = Mathf.Max(0, down - up * dt / DownFall);
        if (down >= 1 - 1e-4f) laidFull = true;
        else if (down <= 0) { laidFull = false; side = 0; System.Array.Clear(round); }
        if (first || justSettled || down <= 0) System.Array.Copy(x, drape, 8);
        else
        {
            var carry = target[0] - drapeRoot;
            for (int i = 0; i < 8; i++) drape[i] += carry;
            drape[0] = target[0];
            var upAx = (neck - low).Normalized();
            var bk = back[neckBalls[0]]; bk = (bk - upAx * bk.Dot(upAx)).Normalized();
            var ac = upAx.Cross(bk);
            var shoulders = balls.Length >= fileBalls + 4 ? (at[fileBalls] + at[fileBalls + 2]) * 0.5f : neck;
            bool armed = laidFull && bone == head && upright > RoundLo && headH > RoundHead;
            float thMax = Mathf.Pi - (Mathf.Pi - RoundTo) * Mathf.SmoothStep(RoundLo, RoundHi, upright), turnMost = Mathf.Pi * dt / (pony ? PonyRoundTime : RoundTime) / DrapePasses;
            // (the angle round her spine from straight behind her, toward the side it goes round; in front on the far side
            // it goes round the near side too)
            float Round(Vector3 q, out float hg, out float b, out float rho)
            {
                var r = q - neck; hg = r.Dot(upAx); float a = r.Dot(ac); b = r.Dot(bk); rho = Mathf.Sqrt(a * a + b * b);
                float th = Mathf.Atan2(side * a, b);
                return th < -Mathf.Pi / 2 ? th + 2 * Mathf.Pi : th;
            }
            if (armed)
            {
                if (side == 0)
                {
                    float sa = 0;
                    for (int i = 1; i < 8; i++) { var r = drape[i] - neck; if (r.Dot(bk) < -RoundFront && r.Dot(upAx) < RoundTop) sa += r.Dot(ac); }
                    side = sa >= 0 ? 1 : -1;
                }
                for (int i = 1; i < 8; i++)
                {
                    float th = Round(drape[i], out float hg, out float b, out float rho);
                    if (rho < 0.02f) continue;
                    if (!round[i] && b < -RoundFront && hg < RoundTop) round[i] = true;
                    // (a braid's: let go tip last, not while the next point toward the tip is still in front of the plane
                    // through her shoulders)
                    if (round[i] && th <= RoundTo + 1e-3f && !(ridge && i < 7 && (drape[i + 1] - shoulders).Dot(bk) < 0)) round[i] = false;
                }
            }
            bool on = ridge && System.Array.IndexOf(round, true) >= 0;
            if (on) { RidgeAt(scale); System.Array.Copy(drape, carried, 8); }
            for (int k = 0; k < DrapePasses; k++)
                for (int i = 1; i < 8; i++)
                {
                    var came = drape[i];
                    drape[i].Y -= DrapeStep;
                    drape[i] = drape[i - 1] + (drape[i] - drape[i - 1]).Normalized() * link[i];
                    drape[i] = round[i] ? Sideways(drape[i], upAx, scale) : Out(drape[i], scale, -1, came);
                    if (on) drape[i] = OffRidge(drape[i]);
                    drape[i].Y = Mathf.Max(drape[i].Y, floor);
                    if (armed && round[i])
                    {
                        float th = Round(drape[i], out _, out _, out _);
                        if (th > thMax) drape[i] = neck + (drape[i] - neck).Rotated(upAx, -side * Mathf.Min(th - thMax, turnMost));
                    }
                }
            if (on)
            {
                if (down >= 1 - 1e-4f) RidgeLinks();
                // (and no point moves more than 7 cm a frame against her root's carry, a tail's 6: its tip flicked 11 cm
                // over her shoulder)
                float most = pony ? PonyMove : RidgeMove;
                for (int i = 1; i < 8; i++)
                {
                    var dv = drape[i] - carried[i];
                    if (dv.LengthSquared() > most * most) drape[i] = carried[i] + dv.Normalized() * most;
                }
            }
        }
        drapeRoot = target[0];
        if (down > 0)
        {
            int steps = Mathf.Max(1, Mathf.CeilToInt(dt * 120f - 1e-3f));
            var step = first || justSettled ? Vector3.Zero : (target[0] - rootPrev) / steps;
            bool full = down >= 1 - 1e-4f;
            for (int i = 1; i < 8; i++)
            {
                if (full) { x[i] = drape[i]; xp[i] = drape[i] - step; }
                else lay[i] = x[i] + (drape[i] - x[i]) * down;
            }
        }
        rootPrev = target[0];
        justSettled = false;
    }
    bool justSettled;

    /// <summary>A point being carried round her (the round carry) kept out of her neck and back sideways, square to her
    /// spine, so it goes round her and is never pushed back the way it came. But one above a ball's middle (along her
    /// spine) goes up onto it, the nearest way: pushed square to her spine there, a point over the line across her upper
    /// back was thrown forward each pass by the slant between that line and her spine, so the carry stuck with the tail in
    /// front, its link through her neck, and never ended (hair solver 11, get_up). And it is kept out of her shoulders and
    /// upper arms, grown by her pauldron, the nearest way (over the top when above the joint): carried through them, the
    /// tail lay 4-6 cm inside her shoulder and its pad as she stood (hair judge hj5).</summary>
    Vector3 Sideways(Vector3 q, Vector3 upAx, float scale)
    {
        for (int b = 0; b < balls.Length; b++)
        {
            if (balls[b].OutOnly) continue;
            bool arm = b >= fileBalls;
            var w = across[b];
            float ww = w.LengthSquared(), r = (balls[b].R - balls[b].Pad + (arm ? PadR : 0)) * scale;
            var c = ww > 0 ? at[b] + w * Mathf.Clamp((q - at[b]).Dot(w) / ww, -1f, 1f) : at[b];
            var off = q - c;
            if (off.LengthSquared() >= r * r) continue;
            if (arm || off.Dot(upAx) > 0) { q = c + (off.LengthSquared() > 1e-10f ? off.Normalized() : upAx) * r; continue; }
            var u = upAx * off.Dot(upAx); var flat = off - u;
            if (flat.LengthSquared() < 1e-10f || u.LengthSquared() >= r * r) continue;
            q = c + u + flat.Normalized() * Mathf.Sqrt(r * r - u.LengthSquared());
        }
        return q;
    }
    Vector3[] lay = new Vector3[8];
    // (the warden's pauldron, the bulkiest, reaches 10 cm over her shoulder joint, its ball 8; and half the tail)
    const float PadR = 0.025f;

    // The ridge (hair solver 14, a braid's only; env NORIDGE=1 turns it off to compare). Getting up, the braid carried
    // round from the front of her right shoulder to her back cut 3-4 cm through the ridge between her neck and shoulder
    // (k46-48), which no ball covers: a skin driver lifts her trapezius 1-4 cm there as she rises, and the chain dropped
    // down her back while its tip was still in front, a U through her (hair judges hj6, jh1). So while the carry is on,
    // a tapered capsule each side along that ridge (on spine_03, from beside her neck to her acromion, 4.5 cm to 8.5,
    // grown 3.5 for her pauldron and half the braid) keeps the drape's points and links out of it, a carried point is
    // let go tip last, and no point moves more than 7 cm a frame. Offline (tools/scratch/face19/sv14): segments 4-7
    // -3.7 -> -0.6 cm, the carry ends k53, the largest move 9.3 (was 9.4); every other clip 0.00 cm.
    // A tail (hair solver 15) hugs the base of her neck, where the ridge alone left it cutting 3.6 cm (segments 3-4, 4-10
    // cm out): so it has a slope capsule more each side, from above the base of her neck (3.5 cm) down to the ridge's
    // neck end, and the margin 4.5. Those held it in front of her shoulder until k60 and then let it through her warden
    // collar (k56, -4.8), so its carry is quicker (180 degrees in 0.15 s, not 0.35) and no point moves over 6 cm a frame.
    // Offline and in Godot (tools/scratch/face19/sv15): segments 4-7 k28-60 -4.1 -> -0.8 cm (warden and reaver; k40-52
    // -0.3), the carry ends k52 (k51), the largest move k40-60 6.2 (7.7), k28-60 10.8 at k31 (10.1 at k30);
    // every other clip 0.00 offline. On by default (judge jp1 PASS, ship NEW, 12 Oct); NOPONYRIDGE=1 turns it off.
    bool ridge, pony;
    int ridgeBone = -1;
    static readonly Vector3 RidgeA = new(-0.1069f, 1.5404f, -0.0536f), RidgeB = new(-0.2115f, 1.501f, -0.0434f), SlopeA = new(-0.05f, 1.585f, -0.05f);
    const float RidgeRA = 0.045f, RidgeRB = 0.085f, RidgeMargin = 0.035f, RidgeMove = 0.07f;
    const float SlopeR = 0.035f, PonyMargin = 0.045f, PonyMove = 0.06f, PonyRoundTime = 0.15f;
    readonly Vector3[] ridgeA = new Vector3[2], ridgeB = new Vector3[2], slopeA = new Vector3[2], carried = new Vector3[8];
    float ridgeRA, ridgeRB, slopeR;

    /// <summary>This frame's ridge capsules (her right, then her left), carried by spine_03.</summary>
    void RidgeAt(float scale)
    {
        var m = sk!.GlobalTransform * Moved(ridgeBone);
        var mirror = new Vector3(-1, 1, 1);
        ridgeA[0] = m * RidgeA; ridgeB[0] = m * RidgeB; ridgeA[1] = m * (RidgeA * mirror); ridgeB[1] = m * (RidgeB * mirror);
        float mg = pony ? PonyMargin : RidgeMargin;
        ridgeRA = (RidgeRA + mg) * scale; ridgeRB = (RidgeRB + mg) * scale;
        if (pony) { slopeA[0] = m * SlopeA; slopeA[1] = m * (SlopeA * mirror); slopeR = (SlopeR + mg) * scale; }
    }

    /// <summary>Capsule c of this frame's: 0-1 the ridges (her right, then her left), and a tail's 2-3 its slopes (from
    /// above the base of her neck to each ridge's neck end).</summary>
    void Capsule(int c, out Vector3 a, out Vector3 b, out float ra, out float rb)
    {
        if (c < 2) { a = ridgeA[c]; b = ridgeB[c]; ra = ridgeRA; rb = ridgeRB; }
        else { a = slopeA[c - 2]; b = ridgeA[c - 2]; ra = slopeR; rb = ridgeRA; }
    }

    /// <summary>A point kept out of the ridge capsules the nearest way.</summary>
    Vector3 OffRidge(Vector3 p)
    {
        for (int c = 0; c < (pony ? 4 : 2); c++)
        {
            Capsule(c, out var a, out var b, out float ra, out float rb);
            var ab = b - a;
            float t = Mathf.Clamp((p - a).Dot(ab) / ab.LengthSquared(), 0f, 1f), r = ra + (rb - ra) * t;
            var o = p - (a + ab * t);
            if (o.LengthSquared() >= r * r) continue;
            p = a + ab * t + (o.LengthSquared() > 1e-12f ? o.Normalized() : Vector3.Up) * r;
        }
        return p;
    }

    /// <summary>The drape's links kept out of the ridge: a link (below the first) whose deepest of 41 places is in a
    /// capsule has its far end swung out over it, and what hangs below is laid on again at its lengths (twice).</summary>
    void RidgeLinks()
    {
        for (int it = 0; it < 2; it++)
            for (int i = 2; i < 8; i++)
                for (int c = 0; c < (pony ? 4 : 2); c++)
                {
                    Capsule(c, out var a, out var b, out float ra, out float rb);
                    var ab = b - a;
                    float best = float.MaxValue, bs = 0, bt = 0; Vector3 bx = Vector3.Zero, bc = Vector3.Zero;
                    for (int j = 0; j <= 40; j++)
                    {
                        float s = j / 40f;
                        var q = drape[i - 1] + (drape[i] - drape[i - 1]) * s;
                        float t = Mathf.Clamp((q - a).Dot(ab) / ab.LengthSquared(), 0f, 1f);
                        var cq = a + ab * t;
                        float dd = q.DistanceTo(cq);
                        if (dd < best) { best = dd; bs = s; bt = t; bx = q; bc = cq; }
                    }
                    float rr = ra + (rb - ra) * bt;
                    if (best >= rr || bs < 0.05f) continue;
                    var to = drape[i] + (bx - bc).Normalized() * ((rr - best) / bs);
                    drape[i] = drape[i - 1] + (to - drape[i - 1]).Normalized() * link[i];
                    for (int j = i + 1; j < 8; j++) drape[j] = drape[j - 1] + (drape[j] - drape[j - 1]).Normalized() * link[j];
                }
    }

    // (env HAIRDUMP: each frame's inputs and the chain as it starts, for an offline replica)
    void Dump(float dt, float ground)
    {
        static string V(Vector3 a) => $"[{a.X:F5},{a.Y:F5},{a.Z:F5}]";
        var sb = new System.Text.StringBuilder($"HAIRDUMP {{\"f\":{Engine.GetProcessFrames()},\"dt\":{dt:F6},\"ground\":{ground:F5}");
        sb.Append(",\"target\":[").Append(string.Join(",", System.Array.ConvertAll(target, V))).Append(']');
        sb.Append(",\"x\":[").Append(string.Join(",", System.Array.ConvertAll(x, V))).Append(']');
        sb.Append(",\"xp\":[").Append(string.Join(",", System.Array.ConvertAll(xp, V))).Append(']');
        sb.Append(",\"at\":[").Append(string.Join(",", System.Array.ConvertAll(at, V))).Append(']');
        sb.Append(",\"back\":[").Append(string.Join(",", System.Array.ConvertAll(back, V))).Append(']');
        sb.Append(",\"across\":[").Append(string.Join(",", System.Array.ConvertAll(across, V))).Append(']');
        sb.Append(",\"r\":[").Append(string.Join(",", System.Array.ConvertAll(balls, b => b.R.ToString("F5")))).Append(']');
        sb.Append(",\"behind\":[").Append(string.Join(",", System.Array.ConvertAll(balls, b => b.Behind ? "1" : "0"))).Append(']');
        var hb = sk!.GetBoneGlobalPose(head);
        sb.Append(",\"head\":[").Append(V(sk.GlobalTransform * hb.Origin)).Append(',').Append(V(sk.GlobalTransform.Basis * hb.Basis.X))
          .Append(',').Append(V(sk.GlobalTransform.Basis * hb.Basis.Y)).Append(',').Append(V(sk.GlobalTransform.Basis * hb.Basis.Z)).Append(']');
        sb.Append(",\"stiff\":").Append(stiff.ToString("F5")).Append('}');
        GD.Print(sb.ToString());
    }

    // A debugging view (env HAIRDRAW): the chain's points drawn over everything (yellow, the tip red) and its balls
    // (blue, see-through), to see where it runs against her body.
    MeshInstance3D[] dots = [];
    void Draw()
    {
        if (dots.Length == 0)
        {
            var list = new System.Collections.Generic.List<MeshInstance3D>();
            for (int i = 0; i < 8 + balls.Length; i++)
            {
                bool ball = i >= 8;
                float r = ball ? balls[i - 8].R : 0.012f;
                var m = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, NoDepthTest = !ball,
                    AlbedoColor = ball ? new Color(0.2f, 0.5f, 1f, 0.25f) : i == 7 ? Colors.Red : Colors.Yellow,
                    Transparency = ball ? BaseMaterial3D.TransparencyEnum.Alpha : BaseMaterial3D.TransparencyEnum.Disabled };
                var d = new MeshInstance3D { Mesh = new SphereMesh { Radius = r, Height = 2 * r, RadialSegments = 16, Rings = 8 }, MaterialOverride = m, TopLevel = true };
                AddChild(d); list.Add(d);
            }
            dots = list.ToArray();
        }
        for (int i = 0; i < 8; i++) dots[i].GlobalPosition = x[i];
        for (int b = 0; b < balls.Length; b++) dots[8 + b].GlobalPosition = at[b];
    }

    // The parameters' names made once: a string given where a name is wanted
    // is a new name each call, and every frame's left for the collector.
    static readonly StringName HeadTurnName = "head_turn";
    static readonly StringName SwayName = "sway", HeadName = "head", ChainName = "chain",
        SwayThenName = "sway_then", HeadThenName = "head_then", ChainThenName = "chain_then",
        ArmsName = "arms", ArmsThenName = "arms_then", ArmRName = "arm_r",
        RestName = "chain_rest", RestThenName = "chain_rest_then", TurnName = "chain_turn", TurnThenName = "chain_turn_then";

    /// <summary>The chain at rest and how far each place along it has turned, in the mesh's space. Each link's turn is
    /// carried down from the root (each joint's bend now, less its bend at rest, laid on the link before's turn), so a
    /// twist doesn't build up as it would from each link's own shortest turn, and no link flips as it swings past
    /// half a turn from its rest. Each point takes the mean of its two links'; the root none (her hair at the tie is held).</summary>
    readonly Quaternion[] seg = new Quaternion[7];

    void Turn(Transform3D local)
    {
        for (int i = 0; i < 8; i++) restAt[i] = local * target[i];
        Vector3 d0 = Vector3.Zero, e0 = Vector3.Zero;
        for (int j = 0; j < 7; j++)
        {
            Vector3 d = restAt[j + 1] - restAt[j], e = d + swung[j + 1] - swung[j];
            if (d.LengthSquared() < 1e-12f || e.LengthSquared() < 1e-12f) { seg[j] = j > 0 ? seg[j - 1] : Quaternion.Identity; continue; }
            d = d.Normalized(); e = e.Normalized();
            seg[j] = j == 0 ? Arc(d, e) : (Arc(e0, e) * seg[j - 1] * Arc(d0, d).Inverse()).Normalized();
            d0 = d; e0 = e;
        }
        turnAt[0] = new Vector4(0, 0, 0, 1);
        // (long hair's wide sheet turned no more than 20 degrees at any point: its cards reach 13 cm from the chain, and
        // turned 40-75 degrees as it bent over her shoulder lying face down they stood 4-9 cm off her (hair judge hj3,
        // death c10-c11), and fanned into a spray at its end as she sat up (get_up_back c4). Running, stopping and
        // throwing it turns 17 or less, so they are unchanged; a braid's or a tail's strands lie within 5 cm of it and
        // turn freely.)
        float most = Style == "long" ? SheetTurn : Mathf.Pi;
        for (int i = 1; i < 8; i++)
        {
            var q = i == 7 ? seg[6] : seg[i - 1].Slerp(seg[i], 0.5f);
            if (q.W < 0) q = -q;
            if (2 * Mathf.Acos(Mathf.Min(q.W, 1f)) > most)
            {
                // (its axis scaled to the cap's half-angle by hand: Godot's Quaternion(axis, angle) throws in a debug build
                // when the axis is a hair off unit length, as GetAxis()'s often is, and that frame's swing never reached the
                // shader: her hair was drawn with the last frame's chain on this frame's pose, a strand standing 5 cm off
                // her back as she fell, death c8-c9, hair solver 7)
                var axis = new Vector3(q.X, q.Y, q.Z);
                axis *= Mathf.Sin(most / 2) / axis.Length();
                q = new Quaternion(axis.X, axis.Y, axis.Z, Mathf.Cos(most / 2));
            }
            turnAt[i] = new Vector4(q.X, q.Y, q.Z, q.W);
        }
    }

    static readonly float SheetTurn = Mathf.DegToRad(20);

    /// <summary>The shortest turn from one direction to another (both of unit length).</summary>
    static Quaternion Arc(Vector3 a, Vector3 b)
    {
        float c = a.Dot(b);
        if (c > 0.999999f) return Quaternion.Identity;
        if (c < -0.999999f) return new Quaternion(a.Cross(Mathf.Abs(a.X) < 0.9f ? Vector3.Right : Vector3.Up).Normalized(), Mathf.Pi);
        return new Quaternion(a, b);
    }
}
