using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// P7 (the skills lead, 9 Nov): her body in Bladestorm and Iron Vow, built from clips she already has until A1 keys real
/// ones (a spin loop, a brace), and Heroic Leap's clip fitted to the sim's air.
/// - The storm: her heavy cut (sword_heavy) driven to its f8 (all the way round to her left, the blade level and out) in a
///   0.1 s wind-in and held there while her root yaws 2.25 turns a second (blade leading, the way the cut sweeps); her
///   travel leans her (up to 9 degrees into her steering). Released, the cut plays on into her guard as the turn bleeds off;
///   broken, she plants: the turn stops in 0.08 s and the cut's follow-through lands the blow.
/// - The vow: her bull rush's plant (f12, shield cocked in, the lead foot stamped) snapped to in two frames and held for the
///   brace; the burst plays its shove (f13-15) and recoil on into her guard.
/// - The leap: the clip's crouch run in 0.06 s, its flight (0.42 s about the pelvis's apex) stretched over the sim's air, the
///   landing at its own pace from the land event.
/// The clip's place is driven per frame (fullScale) along a list of keys, (seconds since the start, clip seconds).
/// </summary>
public partial class PlayerView
{
    const string P7SpinClip = "sword_heavy", P7VowClip = "bull_rush";
    const double P7SpinHold = 8 / 30.0, P7VowHold = 12 / 30.0;
    const float P7SpinRate = 2.25f * Mathf.Tau;

    enum P7State { None, Spin, SpinOut, Vow, VowOut }
    P7State p7State;
    // the driven clip: its keys (time since p7T0, clip seconds), its place, the scale set for the tree's next advance
    readonly List<(double T, double C)> p7Keys = new();
    double p7T0, p7Pos, p7Scale = -1;
    float p7Yaw, p7YawRate, p7YawDecay;
    Vector3 p7Lean;
    double p7OutUntil;

    /// <summary>The sim's Bladestorm and Iron Vow events (WorldScene forwards them).</summary>
    public void OnP7(CombatEvent e)
    {
        if (!mine) return;
        switch (e)
        {
            case Ev.Spin { Phase: SpinPhase.Start }:
                if (!own.Has(P7SpinClip) || !FullHer(P7SpinClip, P7SpinHold / 0.1, false)) return;
                P7Drive((0, 0), (0.1, P7SpinHold));
                p7State = P7State.Spin;
                p7Yaw = Rotation.Y; p7YawRate = 0; p7YawDecay = 0;
                break;
            case Ev.Spin { Phase: SpinPhase.End } when p7State == P7State.Spin:
                // released: the cut plays on into her guard while the turn bleeds off
                P7Release(1.6); p7YawDecay = 7; p7State = P7State.SpinOut; p7OutUntil = time + 0.45;
                break;
            case Ev.Spin { Phase: SpinPhase.Break } when p7State is P7State.Spin or P7State.SpinOut:
                // broken: she plants; the follow-through is the blow
                P7Release(1.25); p7YawDecay = 40; p7State = P7State.SpinOut; p7OutUntil = time + 0.5;
                break;
            case Ev.Brace { Phase: BracePhase.Start }:
                if (!own.Has(P7VowClip) || !FullHer(P7VowClip, P7VowHold / 0.034, false)) return;
                P7Drive((0, 0), (0.034, P7VowHold));
                p7State = P7State.Vow;
                break;
            case Ev.Brace { Phase: BracePhase.Burst } when p7State == P7State.Vow:
                P7Release(1.3); p7State = P7State.VowOut; p7OutUntil = time + 0.4;
                break;
        }
    }

    /// <summary>Drive the whole-body clip along these keys from now (its place starts at the first key's).</summary>
    void P7Drive(params (double T, double C)[] keys)
    {
        p7Keys.Clear(); p7Keys.AddRange(keys);
        p7T0 = time; p7Pos = keys[0].C;
        p7Scale = keys.Length > 1 && keys[1].T > keys[0].T ? (keys[1].C - keys[0].C) / (keys[1].T - keys[0].T) : 1;
        tree.Set("parameters/fullScale/scale", p7Scale);
    }

    /// <summary>Before the tree advances (Update's top): the driven clip moves on at the scale set for it.</summary>
    void P7Tick(double dt)
    {
        if (p7Scale >= 0) p7Pos += p7Scale * dt;
    }

    /// <summary>From where it is held, on to the clip's end at `rate`.</summary>
    void P7Release(double rate)
    {
        double len = person.Anim.GetAnimation(full.Animation)?.Length ?? p7Pos + 0.5;
        P7Drive((0, p7Pos), (System.Math.Max(0.02, (len - p7Pos) / rate), len));
    }

    double P7KeyAt(double t)
    {
        if (p7Keys.Count == 0) return p7Pos;
        if (t <= p7Keys[0].T) return p7Keys[0].C;
        for (int i = 1; i < p7Keys.Count; i++)
            if (t <= p7Keys[i].T) return Mathf.Lerp((float)p7Keys[i - 1].C, (float)p7Keys[i].C, (float)((t - p7Keys[i - 1].T) / System.Math.Max(1e-6, p7Keys[i].T - p7Keys[i - 1].T)));
        return p7Keys[^1].C;
    }

    /// <summary>Heroic Leap's clip fitted to the air: its crouch in 0.06 s, its flight (0.42 s about the pelvis's apex) over
    /// the sim's air, its landing at its own pace. False: the clip has no pelvis track to time it by.</summary>
    bool P7LeapFit(double air)
    {
        var anim = person.Anim.GetAnimation(full.Animation);
        if (anim == null) return false;
        int tr = -1;
        for (int i = 0; i < anim.GetTrackCount(); i++)
            if (anim.TrackGetType(i) == Animation.TrackType.Position3D && anim.TrackGetPath(i).ToString().EndsWith(":pelvis")) { tr = i; break; }
        if (tr < 0) return false;
        double apex = 0, top = double.NegativeInfinity;
        for (double t = 0; t <= anim.Length; t += 1 / 60.0)
        {
            double y = anim.PositionTrackInterpolate(tr, t).Y;
            if (y > top) { top = y; apex = t; }
        }
        double t0 = System.Math.Clamp(apex - 0.21, 0.02, anim.Length), t1 = System.Math.Min(anim.Length, apex + 0.21);
        P7Drive((0, 0), (0.06, t0), (System.Math.Max(0.1, air), t1), (System.Math.Max(0.1, air) + (anim.Length - t1), anim.Length));
        p7State = P7State.None;
        if (SurvivorUnchained.Args.Has("clip")) GD.Print($"p7 leap fit: apex {apex:0.00} s, flight {t0:0.00}-{t1:0.00} over the air {air:0.00} s, clip {anim.Length:0.00} s");
        return true;
    }

    /// <summary>Each frame (Update, after her facing is chosen): the driven clip's pace, the storm's turn and lean.</summary>
    void P7Step(Battle b, double dt, float sp)
    {
        if (p7Scale >= 0)
        {
            bool on = (bool)tree.Get("parameters/fullShot/active");
            double want = P7KeyAt(time - p7T0 + dt);
            p7Scale = on ? System.Math.Max(0, (want - p7Pos) / System.Math.Max(1e-4, dt)) : -1;
            if (p7Scale >= 0) tree.Set("parameters/fullScale/scale", p7Scale);
            if (!on) p7Keys.Clear();
        }
        if (p7State == P7State.None) return;
        var p = b.Player;
        if (p7State is P7State.Spin or P7State.SpinOut)
        {
            if (p7State == P7State.Spin) p7YawRate = Mathf.Min(P7SpinRate, p7YawRate + P7SpinRate * (float)dt / 0.1f);
            else p7YawRate *= Mathf.Exp(-p7YawDecay * (float)dt);
            p7Yaw += p7YawRate * (float)dt;
            // her steering in the lean: into where she is going, up to 9 degrees at her storm pace
            var v = new Vector3((float)p.Vx, 0, (float)p.Vz);
            var want = p7State == P7State.Spin ? v * Mathf.DegToRad(2.2f) : Vector3.Zero;
            if (want.Length() > Mathf.DegToRad(9)) want = want.Normalized() * Mathf.DegToRad(9);
            p7Lean = p7Lean.Lerp(want, 1 - Mathf.Exp(-10 * (float)dt));
            float la = p7Lean.Length();
            var q = new Quaternion(Vector3.Up, p7Yaw);
            if (la > 1e-4f) q = new Quaternion(Vector3.Up.Cross(p7Lean / la).Normalized(), la) * q;
            Quaternion = q;
            if (carriage != null) carriage.Bank = carriage.Tilt = 0;
            if (p7State == P7State.SpinOut && time > p7OutUntil)
            {
                // home: her facing the way she goes again, upright (the facing code takes the yaw from here)
                Rotation = new Vector3(0, p7Yaw, 0);
                p7State = P7State.None;
                artTail = time;
            }
        }
        else if (p7State == P7State.Vow)
        {
            // planted; once the plant is over she may walk, and the run takes her legs back
            if (sp > 0.6f && (bool)tree.Get("parameters/fullShot/active"))
            {
                tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
                p7State = P7State.None; p7Scale = -1; p7Keys.Clear();
            }
        }
        else if (p7State == P7State.VowOut && time > p7OutUntil) { p7State = P7State.None; artTail = time; }
    }
}
