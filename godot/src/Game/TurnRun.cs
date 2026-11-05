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
    public static readonly double Start = Args.Has("fig8") ? Args.Num("fig8", 3) : -1;
    static int beat;
    static double t0 = -1;

    /// <summary>The script's move at this fight time, or null when the script is off or not begun.</summary>
    public static (double X, double Z)? Stick(double time)
    {
        if (Start < 0 || time < Start) return null;
        double t = time - Start;
        double h = double.NaN;
        foreach (var (at, head) in Steps) if (t >= at) h = head;
        while (beat < Beats.Length && t >= Beats[beat]) { Shots.WantFrames($"s{beat:00}", 1); beat++; }
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
