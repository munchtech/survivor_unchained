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
    sealed class Ball { public int Bone; public Vector3 At; public float R, W; public bool Behind; }

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
    float stiff, bend;
    Vector3[] rest = [], x = [], xp = [];
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
    Vector3[] vel = new Vector3[8], touch = new Vector3[8];
    bool[] grounded = new bool[8];
    // How long since any of it lay on the ground, and since each point's rest last stopped hanging down.
    float offFloor = 1e3f;
    float[] hungFor = new float[8];
    Vector3 rootThen;
    // What the shader is given (in the mesh's space): this frame's swing and where her head
    // is, and last frame's, for the motion vectors (MotionClock).
    Vector3 sway, headAt;
    Vector3[] swung = new Vector3[8], swungThen = new Vector3[8];
    bool drawn;

    public HairSway() { Name = "HairSway"; }

    /// <summary>Hang it as it hangs at rest in her pose now, still: after a cut that sets her pose afresh (a
    /// review sheet seeking back to a clip's start, a cinematic's handover), so the jump isn't a fling.</summary>
    public void Settle() { live = false; }

    public override void _Ready()
    {
        mesh = GetParent() as MeshInstance3D;
        sk = mesh?.GetParent() as Skeleton3D;
        if (sk == null) return;
        head = sk.FindBone("Head");
        FindForearms();
        var file = $"res://art/people/heroine_hair_{Style}.chain.json";
        if (Style == "" || !FileAccess.FileExists(file)) return;
        var d = Json.ParseString(FileAccess.GetFileAsString(file)).AsGodotDictionary();
        bone = sk.FindBone((string)d["bone"]);
        stiff = (float)d["stiff"];
        bend = d.ContainsKey("bend") ? (float)d["bend"] : 0.03f;
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
        }
        // (her shoulders and upper arms only: her forearm and fist sweeping past her head as she threw kicked the chain
        // up over her head, hair judge hj1; the shader keeps her hair out of her forearms)
        foreach (var (shoulder, elbow, _) in Limbs())
        {
            Vector3 s = sk.GetBoneGlobalRest(shoulder).Origin, e = sk.GetBoneGlobalRest(elbow).Origin;
            list.Add(new Ball { Bone = shoulder, At = s, R = 0.08f });
            list.Add(new Ball { Bone = shoulder, At = s.Lerp(e, 0.5f), R = 0.065f });
        }
        balls = list.ToArray();
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
    Vector3 Out(Vector3 q, float scale, int i)
    {
        for (int b = 0; b < balls.Length; b++)
        {
            // (the nearest point of its line across her back)
            var w = across[b];
            float ww = w.LengthSquared();
            var c = ww > 0 ? at[b] + w * Mathf.Clamp((q - at[b]).Dot(w) / ww, -1f, 1f) : at[b];
            var off = q - c;
            float r = balls[b].R * scale;
            if (off.LengthSquared() >= r * r) continue;
            // (in front of a ball down her back: mirrored behind it, then out)
            if (balls[b].Behind && off.Dot(back[b]) < 0) { off -= 2 * off.Dot(back[b]) * back[b]; }
            var n = off.LengthSquared() > 1e-10f ? off.Normalized() : back[b];
            q = c + n * r;
            if (i > 0) { touch[i] = n; grip[i] = Mathf.Max(grip[i], 0.1f); }
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

    public override void _Process(double delta)
    {
        if (mesh == null || sk == null || head < 0) return;
        float dt = Mathf.Clamp((float)delta, 0f, 1f / 20);
        var local = mesh.GlobalTransform.AffineInverse();
        var world = sk.GlobalTransform;
        var pose = sk.GetBoneGlobalPose(head);
        // Last frame's swing is kept for the motion vectors' look back (MotionClock); this frame's is made afresh.
        (swungThen, swung) = (swung, swungThen);
        System.Array.Clear(swung);
        var swayThen = sway;
        var headThen = headAt;
        sway = Vector3.Zero;
        if (bone >= 0 && rest.Length == 8)
        {
            var moved = world * Moved(bone);
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
                float u = Mathf.SmoothStep(0.35f, 0.85f, (target[i] - target[0]).Normalized().Dot(Vector3.Down));
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
                x = (Vector3[])target.Clone(); xp = (Vector3[])target.Clone(); rootThen = target[0]; offFloor = 1e3f; live = true;
                for (int i = 1; i < 8; i++) link[i] = target[i].DistanceTo(target[i - 1]);
            }
            if (OS.HasEnvironment("HAIRDUMP")) Dump(dt, world.Origin.Y);
            // Steps of about 1/120 s whatever the frame rate (four at 30 fps, as it was tuned and judged): the
            // stiffness and the damping are per step, so at 60 fps four steps held it twice as stiff.
            int steps = Mathf.Max(1, Mathf.CeilToInt(dt * 120f - 1e-3f));
            float h = dt / steps;
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
                        if (x[i].Y < floor) { x[i].Y = floor; touch[i] = Vector3.Up; grip[i] = 0.5f; grounded[i] = true; }
                        if (i < 7) turn = new Quaternion(restDir, (x[i] - x[i - 1]).Normalized());
                    }
                }
                for (int i = 1; i < 7; i++) xp[i] += Follow * free[i] * corr[i + 1];
                // What touches her or the ground is stopped going into it, not thrown back out (being pushed out of her
                // was a velocity: a tail lying by her head as it settled was flung up off the floor), and slowed along it.
                for (int i = 1; i < 8; i++)
                {
                    if (grip[i] == 0) continue;
                    var v = vel[i] - touch[i] * Mathf.Min(0f, vel[i].Dot(touch[i]));
                    xp[i] = x[i] - v * (1f - grip[i]);
                    grip[i] = 0;
                }
            }
            for (int i = 0; i < 8; i++) swung[i] = local.Basis * (x[i] - target[i]) * Amount;
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
        (armsThen, arms) = (arms, armsThen);
        for (int a = 0; a < 2; a++)
        {
            bool has = a < foreBone.Length;
            arms[2 * a] = has ? local * (world * (Moved(foreBone[a]) * elbowRest[a])) : Vector3.Zero;
            arms[2 * a + 1] = has ? local * (world * (Moved(fistBone[a]) * fistRest[a])) : Vector3.Zero;
        }
        // (Its first frame has no last: it stood as it stands.)
        if (!drawn) { swayThen = sway; headThen = headAt; System.Array.Copy(swung, swungThen, 8); System.Array.Copy(arms, armsThen, 4); drawn = true; }
        for (int s = 0; s < mesh.Mesh.GetSurfaceCount(); s++)
            if (mesh.GetSurfaceOverrideMaterial(s) is ShaderMaterial first)
                foreach (var m in SurvivorUnchained.View.HairDraw.Passes(first))   // (a blended pass over its solid parts swings with them)
                {
                    m.SetShaderParameter(SwayName, sway);
                    m.SetShaderParameter(HeadName, headAt);
                    m.SetShaderParameter(ChainName, swung);
                    m.SetShaderParameter(SwayThenName, swayThen);
                    m.SetShaderParameter(HeadThenName, headThen);
                    m.SetShaderParameter(ChainThenName, swungThen);
                    m.SetShaderParameter(ArmsName, arms);
                    m.SetShaderParameter(ArmsThenName, armsThen);
                    m.SetShaderParameter(ArmRName, foreBone.Length > 0 ? ForearmR : 0f);
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
    static readonly StringName SwayName = "sway", HeadName = "head", ChainName = "chain",
        SwayThenName = "sway_then", HeadThenName = "head_then", ChainThenName = "chain_then",
        ArmsName = "arms", ArmsThenName = "arms_then", ArmRName = "arm_r";
}
