using System;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>--fig8 T0: a scripted run for measuring her turns (H6, owner note N27), from T0 seconds of fight time:
/// a straight second, a figure-eight of 45-degree key steps (one loop each way), a straight second, a 180, a 90,
/// then a stop. Each frame logs the stick, her velocity, her facing, her speed, her run blend's speed, her lean and the camera's yaw
/// ("TURN ..." lines, tools/combat/turn_measure.py), and asks for a picture at the strip's beats (fig8_sNN).</summary>
public static class TurnRun
{
    /// <summary>The script's steps: (from, heading in degrees; 0 = +Z, 90 = +X; NaN = no move).</summary>
    static readonly (double At, double Head)[] Steps = Build();
    static (double, double)[] Build()
    {
        // --run8 T0 (A1 lead 21): straight runs in all 8 directions, opposite pairs in turn so she stays near the start
        // (0, 180, 45, 225, 90, 270, 135, 315 deg: 0 = +Z, toward the play camera at its yaw 0), each 1.6 s from a 0.6 s stand.
        // --sprint8 T0 (A1 L23): the same 8 legs with her sprint on (GameCinema.PlayMove adds the sprint buff while she is moving):
        // each leg 2.2 s from a 0.8 s stand, so the sprint is up ~0.4 s in and runs 3+ full 0.7 s cycles before the stop.
        if (Args.Has("run8") || Args.Has("sprint8"))
        {
            double leg = Args.Has("sprint8") ? 2.2 : 1.6, gap = Args.Has("sprint8") ? 3.0 : 2.2;
            var r = new System.Collections.Generic.List<(double, double)>();
            double t8 = 0;
            foreach (double h8 in new double[] { 0, 180, 45, 225, 90, 270, 135, 315 }) { r.Add((t8, h8)); r.Add((t8 + leg, double.NaN)); t8 += gap; }
            return r.ToArray();
        }
        // --aimsweep T0 / --press8 T0 (A1 L22): she runs straight (+X, then -X back for the second side) with her aim held off her travel
        // (the off-travel view switch): Press specs below (repeated slot-3 presses: only a blow sets aimHold, 0.45 s each).
        if (Args.Has("aimsweep")) return new (double, double)[] { (0, 90), (15.5, double.NaN), (16.5, 270), (31.5, double.NaN) };
        if (Args.Has("press8")) return new (double, double)[] { (0, 90), (5.5, double.NaN), (6.5, 270), (12, double.NaN) };
        var s = new System.Collections.Generic.List<(double, double)> { (0, 90) };
        double t = 1;
        for (int i = 1; i <= 8; i++) { s.Add((t, 90 + 45 * i)); t += 0.25; }
        for (int i = 1; i <= 8; i++) { s.Add((t, 90 - 45 * i)); t += 0.25; }
        s.Add((t, 90)); t += 1;       // straight
        s.Add((t, 270)); t += 1;      // the 180 (at 6 s)
        s.Add((t, 180)); t += 1;      // the 90 (at 7 s)
        s.Add((t, double.NaN));       // stop (8 s)
        return s.ToArray();
    }
    /// <summary>Pictures at these script times: across the loops, the 180 and its settle.</summary>
    static readonly double[] Beats = { 1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25, 4.75, 5.9, 6.05, 6.12, 6.2, 6.3, 6.45, 6.7, 7.1 };
    public static readonly double Start = Args.Has("fig8") ? Args.Num("fig8", 3) : Args.Has("run8") ? Args.Num("run8", 3) : Args.Has("sprint8") ? Args.Num("sprint8", 3)
        : Args.Has("aimsweep") ? Args.Num("aimsweep", 2) : Args.Has("press8") ? Args.Num("press8", 2) : -1;

    /// <summary>The aim sweep's off-travel angle (deg) at sweep time u (0..13 s): 0 to 60 and 2 s held in the hysteresis band (60 +/- 12.5,
    /// 39 deg/s at most), 60 to 180 and back to 60 (3 s each, 40 deg/s), the band again, then 60 to 0 (1.5 s).</summary>
    public static double SweepAngle(double u)
    {
        if (u < 1.5) return 40 * u;
        if (u < 3.5) return 60 + 12.5 * Math.Sin(Math.PI * (u - 1.5));
        if (u < 6.5) return 60 + 40 * (u - 3.5);
        if (u < 9.5) return 180 - 40 * (u - 6.5);
        if (u < 11.5) return 60 + 12.5 * Math.Sin(Math.PI * (u - 9.5));
        return Math.Max(0, 60 - 40 * (u - 11.5));
    }

    /// <summary>The scripted presses of --aimsweep / --press8 (a ScriptedPress spec on the fight's clock), or null.</summary>
    public static string? PressSpec()
    {
        var inv = System.Globalization.CultureInfo.InvariantCulture;
        string Spec(int slot, double at, double travelHead, double off)
        {
            double h = (travelHead + off) * Math.PI / 180;
            return string.Format(inv, "{0}:{1:0.000}:{2:0.000},{3:0.000}", slot, Start + at, 14 * Math.Sin(h), 14 * Math.Cos(h));
        }
        var l = new System.Collections.Generic.List<string>();
        if (Args.Has("aimsweep"))
        {
            // side A: running +X (heading 90), the aim turned to +off; side B: running -X (270), the aim at -off (the mirror)
            foreach (var (t0, head, sg) in new[] { (1.0, 90.0, 1.0), (17.0, 270.0, -1.0) })
                for (double u = 0; u < 13; u += 0.35) l.Add(Spec(3, t0 + u, head, sg * SweepAngle(u)));
        }
        else if (Args.Has("press8"))
        {
            // 2 each at 180 (behind), 90 and 270 off travel, from slots 1 and 3, >= 1.2 s apart
            double[] at = { 1.2, 2.4, 3.6, 4.8, 7.7, 8.9 }; double[] off = { 180, 180, 90, 90, 270, 270 };
            for (int i = 0; i < 6; i++) l.Add(Spec(i % 2 == 0 ? 1 : 3, at[i], i < 4 ? 90 : 270, off[i]));
        }
        else return null;
        return string.Join(';', l);
    }
    static int beat;
    static double t0 = -1;

    /// <summary>The script's move at this fight time, or null when the script is off or not begun.</summary>
    public static (double X, double Z)? Stick(double time)
    {
        if (Start < 0 || time < Start) return null;
        double t = time - Start;
        double h = double.NaN;
        foreach (var (at, head) in Steps) if (t >= at) h = head;
        while (!Args.Has("run8") && !Args.Has("sprint8") && beat < Beats.Length && t >= Beats[beat]) { Shots.WantFrames($"s{beat:00}", 1); beat++; }
        if (double.IsNaN(h)) return (0, 0);
        double r = h * Math.PI / 180;
        return (Math.Sin(r), Math.Cos(r));
    }

    /// <summary>One frame's line: script time, stick heading, velocity heading, facing (all degrees), speed, lean, camera yaw.</summary>
    public static void Log(double time, double sx, double sz, double vx, double vz, float face, float bank, float anim, double x, double z)
    {
        if (Start < 0 || time < Start) return;
        float cam = (Engine.GetMainLoop() as SceneTree)?.Root.GetViewport().GetCamera3D()?.GlobalRotation.Y ?? 0;
        double sh = sx * sx + sz * sz > 0.01 ? Math.Atan2(sx, sz) * 180 / Math.PI : double.NaN;
        GD.Print(FormattableString.Invariant($"TURN {time - Start:0.0000} stick {sh:0.0} vel {Math.Atan2(vx, vz) * 180 / Math.PI:0.0} face {Mathf.RadToDeg(face):0.0} sp {Math.Sqrt(vx * vx + vz * vz):0.000} bank {bank:0.00} anim {anim:0.000} cam {Mathf.RadToDeg(cam):0.00} at {x:0.00} {z:0.00}"));
    }
}
