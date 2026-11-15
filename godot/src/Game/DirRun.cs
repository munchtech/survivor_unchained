using System;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>--dirrun T0: a scripted run for the directional legs and the two facing modes (aim-move), from T0 seconds of fight
/// time: forward, strafe left, strafe right, backpedal, the four diagonals, a stick circle, a pointer sweep, a 180, a 90, a stop.
/// Headings are degrees, 0 = +Z, 90 = +X (her left when she faces +Z), increasing toward +X. The aim is a fixed point 60 m ahead of
/// her start (+Z) except in the sweep. Each segment start prints "DIRSEG name t".</summary>
public static class DirRun
{
    public static readonly double Start = Args.Has("dirrun") ? Args.Num("dirrun", 3) : -1;

    static readonly (double At, string Name)[] Segs =
    {
        (0, "forward"), (2, "strafe_left"), (4, "strafe_right"), (6, "backpedal"), (8, "diag_fl"), (10, "diag_fr"),
        (12, "diag_bl"), (14, "diag_br"), (16, "circle"), (20, "sweep"), (24, "fwd2"), (25, "the180"), (26, "the90"), (27, "stop"),
    };
    static int seg = -1;
    static (double X, double Z)? origin;

    static (double X, double Z) Dir(double headDeg) { double r = headDeg * Math.PI / 180; return (Math.Sin(r), Math.Cos(r)); }

    /// <summary>The script's stick at this fight time, or null when the script is off or not begun.</summary>
    public static (double X, double Z)? Stick(double time)
    {
        if (Start < 0 || time < Start) return null;
        double t = time - Start;
        while (seg + 1 < Segs.Length && t >= Segs[seg + 1].At)
        {
            seg++;
            GD.Print(FormattableString.Invariant($"DIRSEG {Segs[seg].Name} {t:0.00}"));
        }
        double s = Math.Sqrt(0.5);
        return seg switch
        {
            0 => (0, 1),
            1 => (1, 0),
            2 => (-1, 0),
            3 => (0, -1),
            4 => (s, s),
            5 => (-s, s),
            6 => (s, -s),
            7 => (-s, -s),
            8 => Dir(90 * (t - 16)),
            9 => (1, 0),
            10 => (0, 1),
            11 => (0, -1),
            12 => (1, 0),
            _ => (0, 0),
        };
    }

    /// <summary>The script's cursor (world point) at this fight time given her position, or null before the script begins.</summary>
    public static (double X, double Z)? Pointer(double time, double px, double pz)
    {
        if (Start < 0 || time < Start) return null;
        origin ??= (px, pz);
        double t = time - Start;
        if (t >= 20 && t < 24)
        {
            var d = Dir(90 * (t - 20));
            return (px + 8 * d.X, pz + 8 * d.Z);
        }
        return (origin.Value.X, origin.Value.Z + 60);
    }
}
