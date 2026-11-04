using System;
using Godot;
using SurvivorUnchained.Sound;

namespace SurvivorUnchained.Play;

/* The one cut rule (H4, the owner 3 Nov: "the transition out of the cinematic into play is jarring").
 * Every cinematic hands back to play the same way, whatever its last shot did:
 *  1. the camera eases from the cinematic's last frame into the play camera (about a second; less when the
 *     last shot already blended into it, half a second after a skip), its look leading its move so she
 *     stays in the frame;
 *  2. her body carries what it was doing (a walk eases out, no pop to idle; the input is held, the carry is not);
 *  3. the HUD fades in as the camera lands, never over the move;
 *  4. control returns when the camera has landed (SoundHooks "cine.to_play").
 * --cutlog prints each frame from 2.5 s before a cinematic ends to 2.5 s after control: the camera, the
 * HUD, control and her pose, for tools/experience/cut_check.py (the numbers every cut is held to). */
public partial class Game
{
    sealed class Seam
    {
        public Transform3D From;
        public float FromVfov;
        public double T, Dur;
        public bool Hud;
        /// <summary>Whether control is held after it (a zone that captured it meanwhile).</summary>
        public bool After;
        /// <summary>Where the film's last frame stood from her (the point it turns round, SeamFocus) and how it
        /// was turned off a look straight at her.</summary>
        public Vector3 FromOff;
        public Quaternion FromTurn;
        public bool Arc;
    }
    Seam? seam;
    /// <summary>A cinematic's hand-back still easing into play (the camera moving, control not yet given).</summary>
    public bool InSeam => seam != null;

    /// <summary>How long the ease takes: about a second from a frame well away from play's,
    /// a third of one when the last shot already landed on it (only the HUD and control left).</summary>
    public static double SeamLength(float metres, float degrees, bool skipped)
    {
        if (metres < 0.6f && degrees < 4) return 0.35;
        // (C01's eye-level frame to play's, 23 m and 60 degrees, takes 1.6 s: 1.35 s swung 180 degrees a second)
        double d = Math.Clamp(0.7 + metres / 40.0 + degrees / 180.0, 0.8, 1.6);
        return skipped ? Math.Min(d, 0.6) : d;
    }

    /// <summary>The point the ease turns round: her body 1.1 m up (null: she is not drawn).</summary>
    Vector3? SeamFocus() => scene?.Player is { } pv && !pv.Hidden ? pv.GlobalPosition + Vector3.Up * 1.1f : null;

    /// <summary>A turn looking from one point straight at another (no roll).</summary>
    static Quaternion LookTurn(Vector3 from, Vector3 at)
    {
        var d = at - from;
        if (d.LengthSquared() < 1e-6f) return Quaternion.Identity;
        return Basis.LookingAt(d, Mathf.Abs(d.Normalized().Y) > 0.999f ? Vector3.Forward : Vector3.Up).GetRotationQuaternion();
    }

    /// <summary>The hand-back begun: the camera stands at the cinematic's last frame (from, its vertical
    /// field of view), play's camera already placed where it will land; her own body at her mark.</summary>
    void BeginSeam(Transform3D from, float fromVfov, bool skipped)
    {
        var to = camera.GlobalTransform;
        float metres = from.Origin.DistanceTo(to.Origin);
        float degrees = Mathf.RadToDeg((-from.Basis.Z).AngleTo(-to.Basis.Z));
        seam = new Seam { From = from, FromVfov = fromVfov, Dur = SeamLength(metres, degrees, skipped) };
        // (H4 judge r1: a free blend of place and turn rose and tilted past her, 0.5 s of empty road at C01. The ease turns
        // round her instead: the camera swings on an arc about her body, its look kept on her, each end's own framing of
        // her (how far it was turned off her) blended between.)
        if (SeamFocus() is Vector3 f && (from.Origin - f).Length() > 0.3f)
        {
            seam.Arc = true;
            seam.FromOff = from.Origin - f;
            seam.FromTurn = LookTurn(from.Origin, f).Inverse() * from.Basis.GetRotationQuaternion();
        }
        controls.Captured = true;
        // The look eases over the same time: a grade table changed at the hand-back blends in rather than
        // switching (Atmosphere.GlideLuts; the H4 r1 brightness pops).
        air.GlideLuts(Math.Max(0.5, seam.Dur), 0.4);
        if (Args.Has("cutlog")) GD.Print($"CUTSEAM {cineId} dur={seam.Dur:0.00} metres={metres:0.00} degrees={degrees:0.0} skipped={skipped} arc={seam.Arc}");
    }

    /// <summary>Each frame after the world (play's camera placed): the camera laid between the two.</summary>
    void SeamFrame(double dt)
    {
        if (seam is not { } s) return;
        // Another cinematic or a held view took the camera: the ease gives way at once (its HUD and control too).
        if (cine != null || showing) { seam = null; if (cine == null) { controls.Captured = s.After; hud.ShowPlay(true, 0.3f); } return; }
        s.T += dt;
        double k = Math.Clamp(s.T / s.Dur, 0, 1);
        float e = (float)SurvivorUnchained.Cinema.CineCamera.Ease("slow", k);
        var play = camera.GlobalTransform;
        if (s.Arc && SeamFocus() is Vector3 f && (play.Origin - f).Length() > 0.3f)
        {
            // Round her: the way from her slerped and its length eased in proportion (a crane rising off a close frame
            // pulls back evenly on screen), the look on her each frame, turned off her as each end frames her.
            Vector3 d0 = s.FromOff, d1 = play.Origin - f;
            float l0 = d0.Length(), l1 = d1.Length();
            Vector3 u0 = d0 / l0, u1 = d1 / l1;
            var dir = u0.Dot(u1) > 0.99999f ? u1 : u0.Slerp(u1, e).Normalized();
            float len = Mathf.Exp(Mathf.Lerp(Mathf.Log(l0), Mathf.Log(l1), e));
            var pos = f + dir * len;
            var toTurn = LookTurn(play.Origin, f).Inverse() * play.Basis.GetRotationQuaternion();
            var q = LookTurn(pos, f) * s.FromTurn.Slerp(toTurn, e);
            camera.GlobalTransform = new Transform3D(new Basis(q.Normalized()), pos);
        }
        else
        {
            // Place and turn on the same ease (no body to turn round: she is hidden).
            var q = s.From.Basis.GetRotationQuaternion().Slerp(play.Basis.GetRotationQuaternion(), e);
            camera.GlobalTransform = new Transform3D(new Basis(q), s.From.Origin.Lerp(play.Origin, e));
        }
        camera.Fov = Mathf.Lerp(s.FromVfov, camera.Fov, e);
        // The HUD comes in as the camera settles (its fade ends just after it lands).
        if (!s.Hud && k >= Math.Max(0, 1 - 0.25 / s.Dur)) { s.Hud = true; hud.ShowPlay(true, 0.5f); }
        if (k < 1) return;
        seam = null;
        controls.Captured = s.After;
        controls.ClearLatches();
        SoundHooks.Play("cine.to_play");
        cutLogLeft = Args.Has("cutlog") ? 3.0 : 0;
        if (Args.Has("cutlog")) GD.Print($"CUTCONTROL {cineId}");
    }

    /* ------------------------------------------------------- the cut log -- */

    double cutLogLeft, cutClock;
    bool cutLogging;

    /// <summary>--cutlog: a line a frame through every hand-back (see the top of this file).</summary>
    void CutLog(double dt)
    {
        if (!Args.Has("cutlog")) return;
        bool near = cine != null && cine.ToEnd <= 2.5 && cine.EndsInPlay;
        if (!near && seam == null && cutLogLeft <= 0) { cutLogging = false; return; }
        if (!cutLogging) { cutLogging = true; cutClock = cine != null ? -cine.ToEnd : 0; }
        else cutClock += dt;
        if (seam == null && cine == null) cutLogLeft -= dt;
        var c = camera.GlobalTransform;
        var f = -c.Basis.Z;
        float vfov = camera.KeepAspect == Camera3D.KeepAspectEnum.Width ? VfovOf(camera.Fov) : camera.Fov;
        var pose = cine?.HerPose() ?? PlayHerPose();
        string her = pose is { } hp ? $"root={hp.Root.X:0.000},{hp.Root.Y:0.000},{hp.Root.Z:0.000} head={hp.Head.X:0.000},{hp.Head.Y:0.000},{hp.Head.Z:0.000} hand={hp.Hand.X:0.000},{hp.Hand.Y:0.000},{hp.Hand.Z:0.000}" : "her=-";
        GD.Print($"CUTLOG {cineId} t={cutClock:0.000} dt={dt:0.0000} phase={(cine != null ? "cine" : seam != null ? "seam" : "play")} shot={cine?.ShotIndex ?? -1} " +
                 $"pos={c.Origin.X:0.000},{c.Origin.Y:0.000},{c.Origin.Z:0.000} fwd={f.X:0.0000},{f.Y:0.0000},{f.Z:0.0000} vfov={vfov:0.00} " +
                 $"hud={hud.PlayAlpha:0.00} cap={(controls.Captured ? 1 : 0)} {her}{Scr(pose)}{AirLog()}");
    }

    /// <summary>Where her head and feet land on screen, as fractions of the frame (u right, v down; 9 behind the lens).</summary>
    string Scr((Vector3 Root, Vector3 Head, Vector3 Hand)? pose)
    {
        if (pose is not { } p) return "";
        var size = GetViewport().GetVisibleRect().Size;
        string P(Vector3 w)
        {
            if (camera.IsPositionBehind(w)) return "9,9";
            var u = camera.UnprojectPosition(w);
            return $"{u.X / size.X:0.0000},{u.Y / size.Y:0.0000}";
        }
        return $" scr={P(p.Root + p.Head)},{P(p.Root)}";
    }

    /// <summary>The look's switches, for finding a pop: exposure, the key's strength, direction and shadow reach and
    /// mode, the saturation, the fog, the lamps' cinematic shadows, the grade table shown.</summary>
    string AirLog()
    {
        var kd = -air.Key.GlobalTransform.Basis.Z;
        ulong lut = air.Env.AdjustmentColorCorrection?.GetInstanceId() ?? 0;
        return $" air={air.Env.TonemapExposure:0.000},{air.Key.LightEnergy:0.000},{kd.X:0.000},{kd.Y:0.000},{kd.Z:0.000},{air.Key.DirectionalShadowMaxDistance:0},"
             + $"{(int)air.Key.DirectionalShadowMode},{air.Env.AdjustmentSaturation:0.000},{air.Env.FogDensity:0.0000},{(SurvivorUnchained.View.ShadowLamp.Suspended ? 1 : 0)} lut={lut % 1000000}";
    }

    float VfovOf(float hfov)
    {
        var size = GetViewport().GetVisibleRect().Size;
        return Mathf.RadToDeg(2 * Mathf.Atan(Mathf.Tan(Mathf.DegToRad(hfov) / 2) * size.Y / size.X));
    }

    /// <summary>Her drawn body in play: its root, and her head and right hand relative to it.</summary>
    (Vector3 Root, Vector3 Head, Vector3 Hand)? PlayHerPose()
    {
        if (scene?.Player is not { } pv || pv.Hidden) return null;
        return SurvivorUnchained.Play.Game.PoseOf(pv.GlobalPosition, pv.Person.Skeleton);
    }

    internal static (Vector3 Root, Vector3 Head, Vector3 Hand)? PoseOf(Vector3 root, Skeleton3D? sk)
    {
        if (sk == null) return null;
        int h = sk.FindBone("Head"), r = sk.FindBone("hand_r");
        if (h < 0 || r < 0) return null;
        var hw = sk.GlobalTransform * sk.GetBoneGlobalPose(h).Origin;
        var rw = sk.GlobalTransform * sk.GetBoneGlobalPose(r).Origin;
        return (root, hw - root, rw - root);
    }
}
