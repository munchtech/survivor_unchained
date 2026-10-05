using System;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Cinema;

/// <summary>
/// How a cinematic that ends in play hands her back (docs/cinematics/README.md, 5a):
/// play begins exactly where it leaves her, facing as she faces, still walking
/// if she was; its last shot blends into the game's camera; and her own body
/// plays that last shot, from a cut ("play"), so nothing is swapped in sight.
/// These read it from the timeline; the game does it (GameCinema).
/// </summary>
public static class CineHandover
{
    /// <summary>Where the timeline leaves her: the last place or move it gives
    /// her that names a mark, as (x, z, heading), heading as NpcActor turns
    /// (0 faces south, pi/2 east). A move faces its own heading, or the way
    /// she walks. Null where it never puts her on a mark.</summary>
    public static (double X, double Z, double Heading)? EndPose(CineSchedule s)
    {
        var f = s.File;
        (double X, double Z, double Heading)? at = null;
        if (f.Cast.TryGetValue("her", out var cast) && cast.Mark is string start)
        {
            var m = f.Mark(start);
            at = (m.X, m.Z, m.Heading);
        }
        foreach (var tc in s.Cues.Where(c => c.Cue.Actor == "her" && c.Cue.Do is "place" or "move"))
        {
            var c = tc.Cue;
            string? mark = c.Do == "place" ? c.Str("mark") : c.Str("to");
            if (mark == null) continue;
            var m = f.Mark(mark);
            double heading = m.Heading;
            if (c.Do == "move")
            {
                if (c.Has("heading")) heading = c.Get("heading").GetDouble();
                else if (at is { } from && Math.Abs(m.X - from.X) + Math.Abs(m.Z - from.Z) > 1e-3) heading = Math.Atan2(m.X - from.X, m.Z - from.Z);
            }
            else if (c.Has("heading")) heading = c.Get("heading").GetDouble();
            at = (m.X, m.Z, heading);
        }
        return at;
    }

    /// <summary>The last shot's blend into the game's camera, in seconds (0: it cuts).</summary>
    public static double Blend(CineSchedule s)
    {
        var last = s.Shots[^1];
        var m = last.Shot.Cam?.Move;
        if (m is not { Follow: true }) return 0;
        double a = CineSchedule.Offset(m.Start, last.Dur), b = m.End.ValueKind == JsonValueKind.Undefined ? last.Dur : CineSchedule.Offset(m.End, last.Dur);
        return b >= last.Dur - 1e-6 ? b - a : 0;
    }

    /// <summary>Whether her own body takes the last shot from its first frame (a cut).</summary>
    public static bool PlaysLastShot(CineSchedule s)
    {
        var last = s.Shots[^1];
        return !last.Shot.Hold && s.Cues.Any(c => c.Shot == last && c.Cue.Do == "play" && c.T <= last.Start + 1e-6);
    }

    /// <summary>The smallest angle between two headings, in degrees.</summary>
    public static double Turn(double a, double b)
    {
        double d = (a - b) % (2 * Math.PI);
        if (d > Math.PI) d -= 2 * Math.PI;
        if (d < -Math.PI) d += 2 * Math.PI;
        return Math.Abs(d) * 180 / Math.PI;
    }
}
