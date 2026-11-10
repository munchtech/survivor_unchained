using System.Collections.Generic;
using System.Globalization;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// --act CLIP (dev only; nothing changes without it): one of her P4 clips played on her WHOLE BODY for a shot, timed by
/// ActPlan from data/anim/her_events.json. Flags: --act-at S (run seconds to the start, 1.0), --act-travel M (her root moves
/// M meters straight ahead, her facing at the start, over the clip's travel window), --act-hold S (the loop range repeats for
/// S seconds), --act-spin T (turns a second to her left while the loop plays), --act-repeat N (n acts from the first's spot
/// and facing, 1.5 s apart). The clip's place is driven per frame (fullScale; a seek where a held loop jumps back) and her
/// root and facing are set after her other drivers have had their say, so locomotion, rest, look-at and the turn to the view
/// do not move her; when the clip ends she blends back to what she was doing, where the act left her.
/// One log line per act, then the run time each event is hit.
/// Every rendered frame of an act run: `act: scr f=F t=T pelvis=x,y head=x,y foot=x,y box=x0,y0,x1,y1 ppm=P`, her place in the
/// window's pixels (the movie frame's) from the shown pose through the active camera: F the engine's process frame (the movie
/// writer's file index: one file per iteration from 0), T the run clock, her pelvis, the top of her head, the ball of her lower
/// foot, the box round every bone and every held piece (not padded for flesh), the pixels a meter spans at her pelvis.
/// --act-rigid (shots): the camera is carried with her root during the run, no follow lag (WorldScene.Draw); play's camera
/// is not touched without it.
/// </summary>
public partial class PlayerView
{
    static readonly string? ActClip = Args.Get("act");
    static bool ActOn => ActClip != null;
    /// <summary>--act-rigid (with --act, shots only): the view carried rigidly with her root from the act's start.</summary>
    public static readonly bool ActRigid = ActClip != null && Args.Has("act-rigid");

    ActPlan? actPlan;
    bool actInit;
    double actT0;
    int actPass = -1, actEvent;
    double actPos;
    Vector3 actBase;
    float actBaseYaw;
    bool actFading, actShown;
    List<(string Name, double Run)> actEvents = new();

    /// <summary>She is inside an act (started, not yet ended): her rest, fidgets and look-at stand aside.</summary>
    bool ActLive => actPlan != null && actPass >= 0 && actClock() <= actPlan.Start(actPlan.Repeat - 1) + actPlan.Duration + 0.25;
    double actClock() => time - actT0;

    /// <summary>Where the act has put her (null: no act has begun), for the camera and the lights to follow.</summary>
    public Vector3? ActAt => actShown ? Position : null;

    void ActLoad()
    {
        actInit = true;
        actT0 = time - 0;   // (time has run this frame's dt already: the run's clock counts from here)
        MeasInit();
        if (!HasHer(ActClip!)) { GD.PrintErr($"act: no clip '{ActClip}' in her library"); return; }
        var anim = person.Anim.GetAnimation(own.Prefix + ActClip);
        HerEvents.Beats? beats = null;
        var path = ProjectSettings.GlobalizePath("res://data/anim/her_events.json");
        if (Godot.FileAccess.FileExists(path) && HerEvents.Load(Godot.FileAccess.GetFileAsString(path)).TryGetValue(ActClip!, out var bb)) beats = bb;
        double Num(string k, double d) => double.TryParse(Args.Get(k), NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : d;
        actPlan = new ActPlan(anim.Length, beats, anim.LoopMode != Animation.LoopModeEnum.None, Num("act-at", 1.0), Num("act-travel", 0), Num("act-hold", 0),
            Num("act-spin", 0), (int)Num("act-repeat", 1));
        if (actPlan.Travel != 0 && actPlan.WindowWhole) GD.PrintErr($"act: {ActClip} has no takeoff/land or launch/impact in her_events.json: travelling over its whole length");
        if (actPlan.HoldIgnored) GD.PrintErr($"act: {ActClip} has no loop range and its animation does not loop: --act-hold ignored");
        if (actPlan.SpinIgnored) GD.PrintErr($"act: {ActClip} has no loop range and its animation does not loop: --act-spin ignored");
        if (beats == null) GD.Print($"act: {ActClip} has no beats in her_events.json");
    }

    // ---- the blend's foot travel (cm, x and z), per act pass: her skeleton's frame (the clips' own frame and units: the
    // numbers tools/anim/p4.py's checks print) and the world (her node carries the skeleton at her scale, 1.04 on B) ----
    // The points are read where the skeleton has run its modifiers (SkeletonUpdated): outside that, GetBoneGlobalPose is the
    // mixer's pose, and on B a P4 clip's keys under P1BlendBase are stored pre-turned (P4Pack), so the mixer's pose is not hers.
    static readonly string[] MeasBones = { "ball_l", "ball_r", "foot_l", "foot_r", "pelvis" };
    readonly int[] measIdx = new int[5];
    readonly Vector3[] measNode = new Vector3[5], measWorld = new Vector3[5];     // this frame's reading
    readonly Vector3[] measPrevNode = new Vector3[5], measPrevWorld = new Vector3[5];
    readonly Vector3[] measStartNode = new Vector3[5], measStartWorld = new Vector3[5];
    readonly float[] measPathNode = new float[5], measPathWorld = new float[5];
    readonly Vector3[] measPose = new Vector3[5];   // the shown pose's origins (skeleton space), cached each SkeletonUpdated
    bool measInit, measOk, measHave;
    int measStage;   // 0 idle, 1 blend-in window, 2 clip running, 3 blend-back window
    double measT;    // the clock at the stage's start
    double measEndAt;

    static string Cm(float m) => (m * 100f).ToString("0.0", CultureInfo.InvariantCulture);
    static string Xz(Vector3 v) => $"({Cm(v.X)}, {Cm(v.Z)})";

    void MeasInit()
    {
        if (measInit) return;
        measInit = true; measOk = true;
        for (int i = 0; i < 5; i++)
        {
            measIdx[i] = person.Skeleton.FindBone(MeasBones[i]);
            if (measIdx[i] < 0) { GD.PrintErr($"act: measure: no bone '{MeasBones[i]}' in her skeleton: foot travel not measured"); measOk = false; break; }
        }
        if (measOk) { person.Skeleton.SkeletonUpdated += MeasCache; ScrInit(); }
    }

    /// <summary>After every modifier (B's blend base, laws, carriage): the pose that is shown.</summary>
    void MeasCache()
    {
        for (int i = 0; i < 5; i++) measPose[i] = person.Skeleton.GetBoneGlobalPose(measIdx[i]).Origin;
        for (int b = 0; b < scrPose.Length; b++) scrPose[b] = person.Skeleton.GetBoneGlobalPose(b).Origin;
        if (scrHead >= 0) scrHeadUp = person.Skeleton.GetBoneGlobalPose(scrHead).Basis[scrHeadAxis].Normalized() * scrHeadSign;
        measHave = true;
    }

    // ---- her place on the screen, every rendered frame of an act run (the dense sheets crop round it) ----
    Vector3[] scrPose = System.Array.Empty<Vector3>();   // every bone's origin in the shown pose (skeleton space)
    int scrHead = -1, scrHeadAxis = 1;
    float scrHeadSign = 1;
    Vector3 scrHeadUp = Vector3.Up;
    const float ScrHeadTop = 0.22f;   // from the head bone to her crown, along the bone's own up (skeleton meters)

    void ScrInit()
    {
        var skel = person.Skeleton;
        scrPose = new Vector3[skel.GetBoneCount()];
        scrHead = skel.FindBone("head");
        if (scrHead < 0) scrHead = skel.FindBone("Head");
        if (scrHead >= 0)
        {
            // (the head bone's axis that stands up at rest, with its sign)
            var r = skel.GetBoneGlobalRest(scrHead).Basis;
            float best = 0;
            for (int a = 0; a < 3; a++) { float y = r[a].Normalized().Y; if (Mathf.Abs(y) > Mathf.Abs(best)) { best = y; scrHeadAxis = a; } }
            scrHeadSign = best < 0 ? -1 : 1;
            GD.Print($"act: scr head bone '{skel.GetBoneName(scrHead)}' rest y {Cm(skel.GetBoneGlobalRest(scrHead).Origin.Y)} cm, her crown taken {Cm(ScrHeadTop)} cm up the bone");
        }
        else GD.PrintErr("act: scr: no head bone in her skeleton: head= is her highest bone");
        RenderingServer.FramePreDraw += ScrDraw;
        TreeExiting += () => RenderingServer.FramePreDraw -= ScrDraw;
    }

    static string F1(float v) => v.ToString("0.0", CultureInfo.InvariantCulture);
    static string P2(Vector2 v) => $"{F1(v.X)},{F1(v.Y)}";

    /// <summary>Just before the frame is drawn (her pose, her root and the camera are this frame's): one line of her place in it.</summary>
    void ScrDraw()
    {
        if (!IsInstanceValid(this) || !IsInsideTree() || !measHave || actPlan == null) return;
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null) return;
        var skel = person.Skeleton;
        var x = skel.GlobalTransform;
        var proj = cam.GetCameraProjection();
        var inv = cam.GetCameraTransform().AffineInverse();
        Vector2 win = GetTree().Root.Size;
        Vector2 Px(Vector3 w)
        {
            var v = inv * w;
            var c = proj * new Vector4(v.X, v.Y, v.Z, 1);
            float iw = Mathf.Abs(c.W) < 1e-6f ? 1e6f : 1 / c.W;
            return new Vector2((c.X * iw * 0.5f + 0.5f) * win.X, (-c.Y * iw * 0.5f + 0.5f) * win.Y);
        }
        var lo = new Vector2(float.MaxValue, float.MaxValue); var hi = new Vector2(float.MinValue, float.MinValue);
        void Add(Vector2 p) { lo = new Vector2(Mathf.Min(lo.X, p.X), Mathf.Min(lo.Y, p.Y)); hi = new Vector2(Mathf.Max(hi.X, p.X), Mathf.Max(hi.Y, p.Y)); }
        int top = 0;
        for (int b = 0; b < scrPose.Length; b++) { Add(Px(x * scrPose[b])); if (scrPose[b].Y > scrPose[top].Y) top = b; }
        var head = Px(x * (scrHead >= 0 ? scrPose[scrHead] + scrHeadUp * ScrHeadTop : scrPose[top]));
        Add(head);
        // (what she holds and wears on a bone: sword, shield, sheath; each piece's own box)
        foreach (var n in skel.GetChildren())
        {
            if (n is not BoneAttachment3D att) continue;
            foreach (var m in att.FindChildren("*", "MeshInstance3D", true, false))
            {
                if (m is not MeshInstance3D mi || mi.Mesh == null || !mi.IsVisibleInTree()) continue;
                var bx = mi.GetAabb(); var g = mi.GlobalTransform;
                for (int k = 0; k < 8; k++) Add(Px(g * bx.GetEndpoint(k)));
            }
        }
        var pelvisW = x * measPose[4];
        var pelvis = Px(pelvisW);
        var lf = x * measPose[0]; var rf = x * measPose[1];
        var foot = Px(lf.Y <= rf.Y ? lf : rf);
        float ppm = (Px(pelvisW + cam.GlobalBasis.X) - pelvis).Length();
        GD.Print($"act: scr f={Engine.GetProcessFrames()} t={actClock().ToString("0.000", CultureInfo.InvariantCulture)} pelvis={P2(pelvis)} head={P2(head)} foot={P2(foot)} " +
                 $"box={P2(lo)},{P2(hi)} ppm={F1(ppm)}");
    }

    /// <summary>The five points of the pose last shown (measPose), in her skeleton's frame (measNode) and in the world. Called at the
    /// top of ActTick, so it sees the pose the last tree.Advance left and the node transform ActApply left: one frame behind the
    /// pose this frame will show, consistently.</summary>
    bool MeasRead()
    {
        MeasInit();
        if (!measOk || !measHave) return false;
        var skel = person.Skeleton;
        for (int i = 0; i < 5; i++) { measNode[i] = measPose[i]; measWorld[i] = skel.GlobalTransform * measPose[i]; }
        return true;
    }

    /// <summary>--act-raw: the same points off the mixer's pose (GetBoneGlobalPose outside the skeleton's update), in her node's
    /// frame: what this measure read before it was moved to SkeletonUpdated. Not the pose that is shown.</summary>
    string MeasRaw()
    {
        var skel = person.Skeleton;
        var inv = GlobalTransform.AffineInverse();
        var v = new Vector3[5];
        for (int i = 0; i < 5; i++) v[i] = inv * (skel.GlobalTransform * skel.GetBoneGlobalPose(measIdx[i]).Origin);
        var x = inv * skel.GlobalTransform;
        return $"{MeasPoints(v)} [the mixer's pose, node frame; skeleton in her node: scale {x.Basis.Scale.X:0.###}, origin {Xz(x.Origin)}, yaw {Mathf.RadToDeg(x.Basis.GetEuler().Y):0.#} deg]";
    }

    string MeasPoints(Vector3[] v) =>
        $"ball_l {Xz(v[0])} ball_r {Xz(v[1])} foot_l {Xz(v[2])} foot_r {Xz(v[3])} pelvis {Xz(v[4])}";

    string MeasPaths(float[] path, Vector3[] start, Vector3[] cur)
    {
        var sb = new System.Text.StringBuilder();
        for (int i = 0; i < 5; i++)
        {
            float net = new Vector2(cur[i].X - start[i].X, cur[i].Z - start[i].Z).Length();
            sb.Append($"{MeasBones[i]} path {Cm(path[i])} net {Cm(net)}").Append(i < 4 ? ", " : "");
        }
        return sb.ToString();
    }

    /// <summary>Each frame while a pass is measured: add the horizontal moves, print the windows as they close.</summary>
    void MeasStep()
    {
        if (measStage == 0 || !MeasRead()) return;
        for (int i = 0; i < 5; i++)
        {
            if (measStage != 2)
            {
                measPathNode[i] += new Vector2(measNode[i].X - measPrevNode[i].X, measNode[i].Z - measPrevNode[i].Z).Length();
                measPathWorld[i] += new Vector2(measWorld[i].X - measPrevWorld[i].X, measWorld[i].Z - measPrevWorld[i].Z).Length();
            }
            measPrevNode[i] = measNode[i]; measPrevWorld[i] = measWorld[i];
        }
        double c = actClock();
        if (measStage == 1 && c >= measT + 0.25)
        {
            GD.Print($"act: {ActClip} blend-in 0.25 s: {MeasPaths(measPathNode, measStartNode, measNode)} [skeleton frame]");
            measStage = 2;
        }
        if (measStage == 2 && c >= measEndAt)
        {
            GD.Print($"act: {ActClip} end: {MeasPoints(measNode)} [skeleton frame]");
            for (int i = 0; i < 5; i++) { measStartNode[i] = measNode[i]; measStartWorld[i] = measWorld[i]; measPathNode[i] = measPathWorld[i] = 0; }
            measStage = 3; measT = c;
        }
        else if (measStage == 3 && c >= measT + 0.60)
        {
            GD.Print($"act: {ActClip} blend-back 0.60 s: {MeasPaths(measPathWorld, measStartWorld, measWorld)} [world]");
            GD.Print($"act: {ActClip} blend-back 0.60 s: {MeasPaths(measPathNode, measStartNode, measNode)} [skeleton frame]");
            GD.Print($"act: {ActClip} after: {MeasPoints(measNode)} [skeleton frame]");
            if (Args.Has("act-raw")) GD.Print($"act: {ActClip} after, raw: {MeasRaw()}");
            measStage = 0;
        }
    }

    /// <summary>A pass is about to start: its last pose before the clip takes over.</summary>
    void MeasStart(double startRun, double duration)
    {
        if (measStage == 3) GD.Print($"act: {ActClip} blend-back cut short by the next pass");
        measStage = 0;
        if (!MeasRead()) return;
        GD.Print($"act: {ActClip} before: {MeasPoints(measNode)} [skeleton frame]");
        if (Args.Has("act-raw")) GD.Print($"act: {ActClip} before, raw: {MeasRaw()}");
        for (int i = 0; i < 5; i++)
        {
            measStartNode[i] = measPrevNode[i] = measNode[i]; measStartWorld[i] = measPrevWorld[i] = measWorld[i];
            measPathNode[i] = measPathWorld[i] = 0;
        }
        measStage = 1; measT = actClock(); measEndAt = startRun + duration;
    }

    /// <summary>Before the tree advances: start the clip at its time, then each frame set its place for the end of this frame.</summary>
    void ActTick(double dt)
    {
        if (!ActOn) return;
        if (!actInit) ActLoad();
        if (actPlan == null) return;
        MeasStep();
        var s = actPlan.Sample(actClock());
        if (s.Pass < 0) return;
        if (s.Pass != actPass)
        {
            MeasStart(actPlan.Start(s.Pass), actPlan.Duration);
            actPass = s.Pass; actEvent = 0; actPos = 0; actFading = false;
            if (!actShown) { actBase = Position; actBaseYaw = Rotation.Y; actShown = true; }
            if (!FullHer(ActClip!, 1, false)) { GD.PrintErr($"act: {ActClip} would not start"); actPlan = null; return; }
            actEvents = new List<(string, double)>(actPlan.EventsRun(actPass));
            GD.Print($"act: {ActClip} at t={actPlan.Start(actPass):0.00} travel {actPlan.Travel:0.##} m over [{actPlan.Window.A:0.000}, {actPlan.Window.B:0.000}] s, " +
                     $"hold {(actPlan.Loop is { } lp ? actPlan.Passes * (lp.B - lp.A) : 0):0.##} s, spin {actPlan.Spin:0.##} t/s (pass {actPass + 1}/{actPlan.Repeat}, {actPlan.Duration:0.00} s long)");
            if (actPlan.Loop is { } hl)
                GD.Print($"act: {ActClip} loop held over run [{(actPlan.Start(actPass) + hl.A).ToString("0.000", CultureInfo.InvariantCulture)}, " +
                         $"{(actPlan.Start(actPass) + hl.A + actPlan.Passes * (hl.B - hl.A)).ToString("0.000", CultureInfo.InvariantCulture)}] s");
        }
        if (s.Active)
        {
            double scale = 1;
            if (s.Clip < actPos - 1e-6)
            {
                // a held loop jumps back to its start
                tree.Set("parameters/fullSeek/seek_request", s.Clip);
            }
            else scale = System.Math.Max(0, (s.Clip - actPos) / System.Math.Max(1e-4, dt));
            actPos = s.Clip;
            tree.Set("parameters/fullScale/scale", scale);
            // (a looping animation never ends the shot by itself: let it go over its last 0.2 s)
            if (!actFading && actClock() >= actPlan.Start(actPass) + actPlan.Duration - 0.2 && full.Animation != null
                && person.Anim.GetAnimation(full.Animation)?.LoopMode != Animation.LoopModeEnum.None)
            {
                actFading = true;
                tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
            }
        }
        else tree.Set("parameters/fullScale/scale", 1.0);
        while (actEvent < actEvents.Count && actClock() >= actEvents[actEvent].Run)
        {
            GD.Print($"act: {ActClip} event {actEvents[actEvent].Name} hit at t={actEvents[actEvent].Run:0.00} (clip {actPos:0.000} s)");
            actEvent++;
        }
    }

    /// <summary>After her other drivers: her root off the fight's spot by the act's offset along its facing, her yaw turned by the act's.</summary>
    void ActApply()
    {
        if (!ActOn || actPlan == null || !actShown) return;
        var s = actPlan.Sample(actClock());
        if (s.Pass < 0) return;
        var fwd = new Vector3(Mathf.Sin(actBaseYaw), 0, Mathf.Cos(actBaseYaw));
        Position = actBase + fwd * (float)s.Ahead;
        Rotation = new Vector3(0, actBaseYaw + (float)s.Yaw, 0);
        if (carriage != null && ActLive) carriage.Aim = carriage.Bank = carriage.Tilt = carriage.HeadLevel = 0;
        aim = 0;
    }
}
