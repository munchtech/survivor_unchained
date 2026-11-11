using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Play;

/// <summary>
/// The --act shot harness's timing (dev only; PlayerView.Act.cs is the glue): one of her clips played on her whole body at
/// run time `At`, optionally travelling, held over its loop range and spun while that range plays, n times from the same
/// spot with a gap between. Given the clip's length, its beats (her_events.json, frames at 60 fps) and the flags, at any run
/// time: the clip's place in seconds, the root's offset ahead in meters, the root's yaw in radians (positive turns her to
/// her LEFT, counter-clockwise from above, as Godot's Y rotation and skills-p7's PlayerView.P7.cs turn her).
/// - Loop: the beats' loop [a, b] (a clip with none whose animation loops whole is held over [0, length]). From its start
///   the range repeats whole passes until `hold` seconds are covered (rounded up to a whole pass, so the clip leaves the
///   loop at b, where its seam is built seamless); with no hold it plays once. Then the clip plays on to its end.
/// - Travel: over the clip's travel window, linear in time: takeoff to land, else launch to impact, else the whole clip.
///   With a loop, a window's clip seconds past b are those after the held passes.
/// - Spin: the yaw runs at `spin` turns a second from the loop's first start to its last end, and stays where it ends.
/// - Repeat: pass i starts at At + i (duration + gap) from the spot and facing of the first; between and after the passes
///   the offset and yaw stay where the pass left them.
/// </summary>
public sealed class ActPlan
{
    public readonly record struct State(bool Active, int Pass, double Clip, double Ahead, double Yaw);

    public readonly double Length, At, Travel, Spin, Gap;
    public readonly int Repeat;
    /// <summary>The loop range in clip seconds (null: none) and how many whole passes it plays.</summary>
    public readonly (double A, double B)? Loop;
    public readonly int Passes;
    /// <summary>The travel window in clip seconds; Whole: neither pair of events was there, so the whole clip.</summary>
    public readonly (double A, double B) Window;
    public readonly bool WindowWhole;
    /// <summary>A hold or a spin was asked of a clip with no loop range (and an animation that does not loop): ignored.</summary>
    public readonly bool HoldIgnored, SpinIgnored;
    /// <summary>One pass's length in run seconds.</summary>
    public readonly double Duration;
    readonly HerEvents.Beats? beats;
    readonly double loopRun;   // the loop's total run seconds

    public ActPlan(double length, HerEvents.Beats? beats, bool animLoops, double at = 1.0, double travel = 0, double hold = 0,
                   double spin = 0, int repeat = 1, double gap = 1.5)
    {
        Length = Math.Max(0.001, length); this.beats = beats; At = at; Travel = travel; Spin = spin; Gap = gap; Repeat = Math.Max(1, repeat);
        var lp = beats?.LoopSeconds;
        if (lp is { } l && l.B - l.A > 1e-6) Loop = (Math.Clamp(l.A, 0, Length), Math.Clamp(l.B, 0, Length));
        else if (animLoops) Loop = (0, Length);
        if (Loop is { } r && r.B - r.A <= 1e-6) Loop = null;
        HoldIgnored = hold > 0 && Loop == null;
        SpinIgnored = spin != 0 && Loop == null;
        if (Loop is { } q) { Passes = hold > 0 ? Math.Max(1, (int)Math.Ceiling(hold / (q.B - q.A) - 1e-6)) : 1; loopRun = Passes * (q.B - q.A); }
        else { Passes = 1; loopRun = 0; }
        Duration = Length + (Loop is { } z ? (Passes - 1) * (z.B - z.A) : 0);
        var ta = beats?.EventSeconds("takeoff"); var tl = beats?.EventSeconds("land");
        var tb = beats?.EventSeconds("launch"); var ti = beats?.EventSeconds("impact");
        if (ta is { } a1 && tl is { } b1 && b1 > a1) Window = (a1, b1);
        else if (tb is { } a2 && ti is { } b2 && b2 > a2) Window = (a2, b2);
        else { Window = (0, Length); WindowWhole = true; }
    }

    /// <summary>Run time of a clip second on the pass's first reach of it (past the loop's end: after the held passes).</summary>
    public double ClipToPass(double c)
        => Loop is { } l && c > l.B + 1e-9 ? c + (Passes - 1) * (l.B - l.A) : c;

    /// <summary>The run time (since the pass's start) the clip's place first reaches an event; null: no such event.</summary>
    public double? EventPass(string name) => beats?.EventSeconds(name) is double s ? ClipToPass(s) : null;

    /// <summary>The clip's place (seconds) `u` seconds into a pass.</summary>
    public double ClipAt(double u)
    {
        u = Math.Clamp(u, 0, Duration);
        if (Loop is not { } l) return Math.Min(u, Length);
        if (u < l.A) return u;
        double into = u - l.A;
        if (into >= loopRun - 1e-9) return Math.Min(Length, l.B + (into - loopRun));
        return l.A + into % (l.B - l.A);
    }

    /// <summary>Run time of pass i's start.</summary>
    public double Start(int i) => At + i * (Duration + Gap);

    /// <summary>The act at run time t.</summary>
    public State Sample(double t)
    {
        if (t < At) return new State(false, -1, 0, 0, 0);
        int i = Math.Min(Repeat - 1, (int)Math.Floor((t - At) / (Duration + Gap)));
        double u = t - Start(i);
        bool active = u <= Duration;
        u = Math.Clamp(u, 0, Duration);
        double ahead = 0;
        if (Travel != 0)
        {
            double ua = ClipToPass(Window.A), ub = ClipToPass(Window.B);
            ahead = Travel * Math.Clamp(ub > ua ? (u - ua) / (ub - ua) : 1, 0, 1);
        }
        double yaw = 0;
        if (Spin != 0 && Loop is { } l) yaw = Spin * Math.Tau * Math.Clamp(u - l.A, 0, loopRun);
        return new State(active, i, ClipAt(u), ahead, yaw);
    }

    /// <summary>The events in order of their time with the run time each is hit in pass i.</summary>
    public IEnumerable<(string Name, double Run)> EventsRun(int i)
        => (beats?.Events ?? Array.Empty<(string, int)>()).Select(e => (e.Name, Start(i) + ClipToPass(HerEvents.Beats.Sec(e.Frame))));
}
