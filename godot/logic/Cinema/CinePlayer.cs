using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Cinema;

/// <summary>A point in the world (metres; y up).</summary>
public readonly record struct V3(double X, double Y, double Z)
{
    public static V3 operator +(V3 a, V3 b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
    public static V3 operator -(V3 a, V3 b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);
    public static V3 operator *(V3 a, double k) => new(a.X * k, a.Y * k, a.Z * k);
    public double Length => Math.Sqrt(X * X + Y * Y + Z * Z);
    public V3 Unit => Length < 1e-9 ? new V3(0, 0, -1) : this * (1 / Length);
    public static V3 Lerp(V3 a, V3 b, double k) => a + (b - a) * k;
}

/// <summary>A shot placed in time.</summary>
public sealed record ShotSpan(CineShot Shot, int Index, double Start, double Dur)
{
    public double End => Start + Dur;
}

/// <summary>A cue placed in time; Order keeps cues at the same moment in the order written.</summary>
public sealed record TimedCue(double T, int Order, CineCue Cue, ShotSpan Shot);

/// <summary>Where the camera is at a moment, and how it sees.</summary>
public readonly record struct CamPose(V3 Pos, V3 At, double Hfov, double Roll, double? Focus, double Fstop, double Lens, double Handheld, double FollowK, bool Black, bool Hold);

/// <summary>
/// A cinematic laid out in time for one survivor: which shots are theirs
/// (calling, background, hair), how long each runs once its lines are known
/// (a shot holds to the end of the lines it fits, so a longer take makes a
/// longer shot and everything after it moves), and every cue at its moment.
/// The same file and the same takes always give the same schedule.
/// </summary>
public sealed class CineSchedule
{
    public readonly CineFile File;
    public readonly List<ShotSpan> Shots = new();
    public readonly List<TimedCue> Cues = new();
    public double Length { get; private set; }

    /// <param name="lineSeconds">How long a line runs (its take, or a reading time), by its VO id ("conversation.node").</param>
    public CineSchedule(CineFile f, CineContext ctx, Func<string, double> lineSeconds)
    {
        File = f;
        double t = 0;
        int order = 0;
        // Where each line said so far ends: a line can run on over a cut (a shot
        // may fit a line begun before it), and a cue can wait for one ("after:id").
        var ends = new Dictionary<string, double>();
        foreach (var shot in f.Shots)
        {
            if (shot.When != null && !shot.When.Holds(ctx)) continue;
            var cues = shot.Cues.Where(c => c.When == null || c.When.Holds(ctx)).ToList();
            double dur = shot.Dur;
            foreach (var c in cues.Where(c => c.Do == "line"))
                ends[c.Str("id")!] = t + At(c.At, shot.Dur, t, ends, wait: true) + lineSeconds(c.Str("id")!);
            foreach (var id in shot.Fit ?? new())
            {
                if (!ends.TryGetValue(id, out var end)) throw new FormatException($"{f.Id} shot {shot.Id}: fits {id}, which it does not say");
                dur = Math.Max(dur, end - t + shot.Tail);
            }
            var span = new ShotSpan(shot, Shots.Count, t, dur);
            Shots.Add(span);
            foreach (var c in cues)
            {
                double ct = t + At(c.At, dur, t, ends);
                if (c.Do == "line") ends[c.Str("id")!] = ct + lineSeconds(c.Str("id")!);
                Cues.Add(new TimedCue(ct, order++, c, span));
            }
            t += dur;
        }
        Length = t;
        Cues.Sort((a, b) => a.T != b.T ? a.T.CompareTo(b.T) : a.Order.CompareTo(b.Order));
    }

    /// <summary>A cue's time in its shot: as Offset, or "after:conversation.node+0.4",
    /// that long after a line already said ends (its take), from this shot's start.</summary>
    static double At(JsonElement at, double dur, double shotStart, Dictionary<string, double> ends, bool wait = false)
    {
        if (at.ValueKind != JsonValueKind.String || !at.GetString()!.StartsWith("after:")) return Offset(at, dur);
        var s = at.GetString()![6..].Replace(" ", "");
        // Ids hold no signs, so the first sign after the conversation's dot begins the offset.
        int k = s.IndexOfAny(['+', '-'], Math.Max(0, s.IndexOf('.')));
        string id = k > 0 ? s[..k] : s;
        double add = k > 0 ? double.Parse(s[k..], CultureInfo.InvariantCulture) : 0;
        if (!ends.TryGetValue(id, out var end)) throw new FormatException($"waits for {id}, which is not said before it");
        // Before the shot is fitted, a wait is not cut short by the length written.
        return Math.Clamp(end + add - shotStart, 0, wait ? double.MaxValue : dur);
    }

    /// <summary>A time in a shot: seconds from its start, or "end", "end-0.8" from its end.</summary>
    public static double Offset(JsonElement at, double dur)
    {
        switch (at.ValueKind)
        {
            case JsonValueKind.Undefined or JsonValueKind.Null: return 0;
            case JsonValueKind.Number: return Math.Min(at.GetDouble(), dur);
            case JsonValueKind.String:
            {
                var s = at.GetString()!.Replace(" ", "");
                if (s == "end") return dur;
                if (s.StartsWith("end-")) return Math.Max(0, dur - double.Parse(s[4..], CultureInfo.InvariantCulture));
                return Math.Min(double.Parse(s, CultureInfo.InvariantCulture), dur);
            }
            default: throw new FormatException($"a time is a number or \"end-N\", not {at}");
        }
    }

    public ShotSpan ShotAt(double t)
    {
        foreach (var s in Shots) if (t < s.End) return s;
        return Shots[^1];
    }
}

/// <summary>
/// The camera, from the shot's numbers: a place and a point to look at, a
/// lens, a focus; a move within the shot (to a new place, along a spline, a
/// push), eased; the last shot's blend into the game's own camera. Places
/// are resolved by the caller (marks, the ground's height, an actor's head),
/// so this is the same in the game and in the tests.
/// </summary>
public static class CineCamera
{
    /// <summary>A full-frame focal length as horizontal field of view (degrees):
    /// 50 mm is 39.6Â°, the scripts' table (docs/cinematics/README.md section 4).</summary>
    public static double Hfov(double mm) => 2 * Math.Atan(36 / (2 * mm)) * 180 / Math.PI;

    public static double Ease(string ease, double k)
    {
        k = Math.Clamp(k, 0, 1);
        return ease switch
        {
            "linear" => k,
            "in" => k * k,
            "out" => 1 - (1 - k) * (1 - k),
            // A long, gentle start and settle: a dolly grip's move.
            "inout" => k * k * (3 - 2 * k),
            "slow" => k * k * k * (k * (k * 6 - 15) + 10),
            _ => k,
        };
    }

    public static CamPose Eval(ShotSpan span, double local, Func<JsonElement, V3> place)
    {
        var shot = span.Shot;
        if (shot.Black || shot.Cam == null) return new CamPose(default, default, 50, 0, null, 2.8, 50, 0, 0, shot.Black, shot.Hold || !shot.Black);
        var c = shot.Cam;
        V3 pos = place(c.Pos), at = place(c.At);
        double lens = c.Lens, roll = c.Roll, k = 0;
        double? focus = Focus(c.Focus, pos, place);
        var m = c.Move;
        if (m != null)
        {
            double s = CineSchedule.Offset(m.Start, span.Dur), e = m.End.ValueKind == JsonValueKind.Undefined ? span.Dur : CineSchedule.Offset(m.End, span.Dur);
            k = Ease(m.Ease, e > s ? (local - s) / (e - s) : local >= s ? 1 : 0);
            V3 at1 = m.At.ValueKind != JsonValueKind.Undefined ? place(m.At) : at;
            V3 pos1 = m.Pos.ValueKind != JsonValueKind.Undefined ? place(m.Pos) : pos + (at - pos).Unit * m.Push;
            if (m.Path is { Count: > 0 })
            {
                var pts = new List<V3> { pos };
                pts.AddRange(m.Path.Select(place));
                if (m.Pos.ValueKind != JsonValueKind.Undefined) pts.Add(pos1);
                pos = Spline(pts, k);
            }
            else pos = V3.Lerp(pos, pos1, k);
            at = V3.Lerp(at, at1, k);
            // A zoom is eased in the field of view, as the eye sees it.
            if (m.Lens is double l1) lens = 18 / Math.Tan(Lerp(Hfov(lens), Hfov(l1), k) * Math.PI / 360);
            if (m.Roll is double r1) roll = Lerp(roll, r1, k);
            if (m.Focus.ValueKind != JsonValueKind.Undefined && Focus(m.Focus, pos, place) is double f1) focus = focus is double f0 ? Lerp(f0, f1, k) : f1;
        }
        return new CamPose(pos, at, Hfov(lens), roll, focus, c.Fstop, lens, c.Handheld, m is { Follow: true } ? k : 0, false, false);
    }

    static double Lerp(double a, double b, double k) => a + (b - a) * k;

    static double? Focus(JsonElement f, V3 cam, Func<JsonElement, V3> place) => f.ValueKind switch
    {
        JsonValueKind.Number => f.GetDouble(),
        JsonValueKind.Undefined or JsonValueKind.Null => null,
        _ => (place(f) - cam).Length,
    };

    /// <summary>Catmull-Rom through the points, k from the first to the last.</summary>
    public static V3 Spline(List<V3> p, double k)
    {
        if (p.Count == 1) return p[0];
        int n = p.Count - 1;
        double u = Math.Clamp(k, 0, 1) * n;
        int i = Math.Min((int)u, n - 1);
        double t = u - i;
        V3 p0 = p[Math.Max(0, i - 1)], p1 = p[i], p2 = p[i + 1], p3 = p[Math.Min(n, i + 2)];
        double t2 = t * t, t3 = t2 * t;
        return (p1 * 2 + (p2 - p0) * t + (p0 * 2 - p1 * 5 + p2 * 4 - p3) * t2 + (p1 * 3 - p0 - p2 * 3 + p3) * t3) * 0.5;
    }
}

/// <summary>
/// A cinematic playing: its clock, the cues it crosses as the clock moves
/// (each exactly once, in order, however the frames fall), the shot and
/// the camera now, and the skip, which lands on the end: everything that
/// lasts is done, nothing that is only heard or seen.
/// </summary>
public sealed class CinePlayer
{
    public readonly CineSchedule S;
    public double T { get; private set; }
    int next;
    public bool Done => T >= S.Length && next >= S.Cues.Count;
    public bool Skipped { get; private set; }

    public CinePlayer(CineSchedule s) { S = s; }

    /// <summary>The clock moved on: the cues it has reached (a cue fires on the
    /// first frame at or past its moment; Advance(0) at the start fires those at 0).</summary>
    public List<TimedCue> Advance(double dt)
    {
        T = Math.Min(S.Length, T + Math.Max(0, dt));
        var o = new List<TimedCue>();
        while (next < S.Cues.Count && S.Cues[next].T <= T) o.Add(S.Cues[next++]);
        return o;
    }

    /// <summary>Whether a held skip counts now (a cinematic seen before can be skipped at once).</summary>
    public bool CanSkip(bool seenBefore) => !Skipped && (seenBefore || T >= S.File.Skip.From);

    /// <summary>Straight to the end: the cues still to come that last, in order.</summary>
    public List<TimedCue> SkipToEnd()
    {
        Skipped = true;
        var o = S.Cues.Skip(next).Where(c => c.Cue.Lasting).ToList();
        next = S.Cues.Count;
        T = S.Length;
        return o;
    }

    public ShotSpan Shot => S.ShotAt(T);
    public double Local => T - Shot.Start;
    public CamPose Camera(Func<JsonElement, V3> place) => CineCamera.Eval(Shot, Local, place);

    /// <summary>How far the bars are in (0..1).</summary>
    public double Bars
    {
        get
        {
            var b = S.File.Bars;
            double inK = b.In <= 0 ? 1 : Math.Clamp(T / b.In, 0, 1);
            double outK = b.Out <= 0 ? 1 : Math.Clamp((S.Length - T) / b.Out, 0, 1);
            return Math.Min(inK, outK);
        }
    }
}
