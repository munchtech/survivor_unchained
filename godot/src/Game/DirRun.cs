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
    /// <summary>--dirrun-set views: runs out and back along the camera's axes with a stop and a stand after each (her run seen
    /// away, front and side, each stop landing in her idle), for a small room (each leg 1.6 s, back where she began).</summary>
    static readonly bool Views = Args.Get("dirrun-set") == "views";
    static readonly (double At, string Name, double X, double Z)[] ViewSegs =
    {
        // (+Z is toward the camera, down-screen: "toward" runs at the camera, "away" up-screen, seen from behind)
        (0, "toward", 0, 1), (1.6, "stand_t", 0, 0), (4.0, "away", 0, -1), (5.6, "stand_a", 0, 0),
        (8.0, "side_x", 1, 0), (9.6, "stand_x", 0, 0), (12.0, "side_mx", -1, 0), (13.6, "stand_mx", 0, 0),
    };
    /// <summary>--dirrun-set film: the owner's short film (15 Nov) under the ALWAYS facing mode, the cursor leading her as a
    /// player's would (60 m out along A): idle facing away, a turn in place to the camera and back, run away, stop, turn and run
    /// toward, stop, a side run, stop (about 17 s).</summary>
    static readonly bool Film = Args.Get("dirrun-set") == "film";
    static readonly (double At, string Name, double X, double Z, double AX, double AZ)[] FilmSegs =
    {
        // (+Z is toward the camera, down-screen; -Z away, up-screen)
        (0, "idle_away", 0, 0, 0, -1), (2.5, "turn_t", 0, 0, 0, 1), (3.7, "turn_a", 0, 0, 0, -1), (4.9, "away", 0, -1, 0, -1),
        (6.5, "stand_a", 0, 0, 0, -1), (8.7, "toward", 0, 1, 0, 1), (10.3, "stand_t", 0, 0, 0, 1),
        (12.5, "side_x", 1, 0, 1, 0), (14.1, "stand_x", 0, 0, 1, 0),
    };
    static int seg = -1;

    static int FilmSeg(double t)
    {
        while (seg + 1 < FilmSegs.Length && t >= FilmSegs[seg + 1].At)
        {
            seg++;
            GD.Print(FormattableString.Invariant($"DIRSEG {FilmSegs[seg].Name} {t:0.00}"));
        }
        return Math.Max(seg, 0);
    }
    static (double X, double Z)? origin;

    static (double X, double Z) Dir(double headDeg) { double r = headDeg * Math.PI / 180; return (Math.Sin(r), Math.Cos(r)); }

    /// <summary>The script's stick at this fight time, or null when the script is off or not begun.</summary>
    public static (double X, double Z)? Stick(double time)
    {
        if (Start < 0 || time < Start) return null;
        double t = time - Start;
        if (Film)
        {
            var f = FilmSegs[FilmSeg(t)];
            return (f.X, f.Z);
        }
        if (Views)
        {
            while (seg + 1 < ViewSegs.Length && t >= ViewSegs[seg + 1].At)
            {
                seg++;
                GD.Print(FormattableString.Invariant($"DIRSEG {ViewSegs[seg].Name} {t:0.00}"));
            }
            return seg < 0 ? (0, 0) : (ViewSegs[seg].X, ViewSegs[seg].Z);
        }
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
        if (Film)
        {
            var f = FilmSegs[FilmSeg(t)];
            return (px + 60 * f.AX, pz + 60 * f.AZ);
        }
        if (t >= 20 && t < 24)
        {
            var d = Dir(90 * (t - 20));
            return (px + 8 * d.X, pz + 8 * d.Z);
        }
        return (origin.Value.X, origin.Value.Z + 60);
    }
}
