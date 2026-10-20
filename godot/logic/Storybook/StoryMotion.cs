using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Storybook;

/// <summary>
/// One value moving through keys, smooth and slow: a Hermite curve through
/// every key whose speed is the same either side of each key (no jolt where
/// one move becomes the next), starting from rest and coming to rest at the
/// ends. A key's ease is the segment arriving at it:
///   unset   passes through the keys at speed; eases from rest at the start and to rest at the end
///   inout   comes to rest at this key, and starts this segment from rest
///   in      starts the segment from rest only
///   out     comes to rest at this key only
///   stop    the same as out (a held beat mid-move)
///   linear  not slowed at either end of the segment (a constant speed between two keys)
///   hold    the value stays at the key before, and jumps here (a cut)
/// A key that is a peak or a trough is passed at rest, so the curve never
/// overshoots a value written; between keys it stays monotone.
/// </summary>
public sealed class StoryCurve
{
    readonly double[] t, v, m;
    readonly string?[] ease;

    public StoryCurve(IReadOnlyList<double> times, IReadOnlyList<double> values, IReadOnlyList<string?> eases)
    {
        int n = times.Count;
        t = times.ToArray(); v = values.ToArray(); ease = eases.ToArray();
        for (int i = 1; i < n; i++) if (t[i] < t[i - 1]) throw new FormatException($"keys out of order at {t[i]}");
        m = new double[n];
        for (int i = 0; i < n; i++) m[i] = Tangent(i);
    }

    public int Count => t.Length;

    bool Hold(int seg) => ease[seg + 1] == "hold";

    double Chord(int seg) => t[seg + 1] - t[seg] < 1e-9 ? 0 : (v[seg + 1] - v[seg]) / (t[seg + 1] - t[seg]);

    double Tangent(int i)
    {
        int n = t.Length;
        bool start = i == 0 || Hold(i - 1), end = i == n - 1 || Hold(i);
        if (start && end) return 0;
        string? before = i > 0 ? ease[i] : null, after = i < n - 1 ? ease[i + 1] : null;
        if (start) return after is "linear" or "out" or "stop" ? Chord(i) : 0;
        if (end) return before is "linear" or "in" ? Chord(i - 1) : 0;
        if (before is "inout" or "out" or "stop" || after is "inout" or "in") return 0;
        double d0 = Chord(i - 1), d1 = Chord(i);
        // A peak or a trough is passed at rest: no overshoot.
        if (d0 * d1 <= 0) return 0;
        double span = t[i + 1] - t[i - 1];
        double c = span < 1e-9 ? 0 : (v[i + 1] - v[i - 1]) / span;
        // Kept within three times the gentler side (Fritsch-Carlson), so it stays monotone.
        double lim = 3 * Math.Min(Math.Abs(d0), Math.Abs(d1));
        return Math.Clamp(c, -lim, lim);
    }

    public double At(double time)
    {
        int n = t.Length;
        if (n == 0) return 0;
        if (time <= t[0]) return v[0];
        if (time >= t[n - 1]) return v[n - 1];
        int i = 0;
        while (i < n - 2 && time >= t[i + 1]) i++;
        if (Hold(i)) return v[i];
        double h = t[i + 1] - t[i];
        if (h < 1e-9) return v[i + 1];
        double s = (time - t[i]) / h, s2 = s * s, s3 = s2 * s;
        return (2 * s3 - 3 * s2 + 1) * v[i] + (s3 - 2 * s2 + s) * h * m[i] + (-2 * s3 + 3 * s2) * v[i + 1] + (s3 - s2) * h * m[i + 1];
    }
}

/// <summary>Where the camera is and how it sees: X, Y the canvas point at the
/// screen's centre on the reference plane; Zoom the lens (1: the canvas width
/// fills the screen's); Dolly how far it has moved forward, in depth units;
/// Rot a roll in degrees.</summary>
public readonly record struct StoryView(double X, double Y, double Zoom, double Dolly, double Rot);

/// <summary>A layer's own move: offset, scale and turn about its pivot, and its opacity.</summary>
public readonly record struct LayerPose(double Dx, double Dy, double Scale, double Rot, double Opacity);

public readonly record struct StoryGrade(double Exposure, double Sat, double R, double G, double B);

/// <summary>The keys of a plate's camera, a layer and a grade as curves.</summary>
public static class StoryMotion
{
    sealed class Channels
    {
        public readonly StoryCurve[] C;
        public Channels(List<double> times, List<double[]> vals, List<string?> eases)
        {
            C = new StoryCurve[vals.Count == 0 ? 0 : vals[0].Length];
            for (int k = 0; k < C.Length; k++) C[k] = new StoryCurve(times, vals.Select(x => x[k]).ToList(), eases);
        }
        public double this[int k, double t] => C[k].At(t);
    }

    /// <summary>The camera's path; at rest (the canvas centre, zoom 1) where no key says otherwise.
    /// Zoom moves in log space, so a push reads at an even pace.</summary>
    public static Func<double, StoryView> Camera(IReadOnlyList<StoryCamKey> keys, double canvasW, double canvasH)
    {
        if (keys.Count == 0) { var rest = new StoryView(canvasW / 2, canvasH / 2, 1, 0, 0); return _ => rest; }
        double x = canvasW / 2, y = canvasH / 2, z = 1, d = 0, r = 0;
        var times = new List<double>(); var vals = new List<double[]>(); var eases = new List<string?>();
        foreach (var k in keys.OrderBy(k => k.T))
        {
            x = k.X ?? x; y = k.Y ?? y; z = k.Zoom ?? z; d = k.Dolly ?? d; r = k.Rot ?? r;
            times.Add(k.T); vals.Add([x, y, Math.Log(Math.Max(1e-3, z)), d, r]); eases.Add(k.Ease);
        }
        var ch = new Channels(times, vals, eases);
        return t => new StoryView(ch[0, t], ch[1, t], Math.Exp(ch[2, t]), ch[3, t], ch[4, t]);
    }

    /// <summary>A layer's keys. With the first key after 0, it starts at rest (and its own opacity) at 0.</summary>
    public static Func<double, LayerPose> Layer(IReadOnlyList<StoryLayerKey>? keys, double opacity)
    {
        var rest = new LayerPose(0, 0, 1, 0, opacity);
        if (keys == null || keys.Count == 0) return _ => rest;
        var sorted = keys.OrderBy(k => k.T).ToList();
        double dx = 0, dy = 0, s = 1, r = 0, o = opacity;
        var times = new List<double>(); var vals = new List<double[]>(); var eases = new List<string?>();
        if (sorted[0].T > 0) { times.Add(0); vals.Add([0, 0, 0, 0, opacity]); eases.Add(null); }
        foreach (var k in sorted)
        {
            dx = k.Dx ?? dx; dy = k.Dy ?? dy; s = k.Scale ?? s; r = k.Rot ?? r; o = k.Opacity ?? o;
            times.Add(k.T); vals.Add([dx, dy, Math.Log(Math.Max(1e-3, s)), r, o]); eases.Add(k.Ease);
        }
        var ch = new Channels(times, vals, eases);
        return t => new LayerPose(ch[0, t], ch[1, t], Math.Exp(ch[2, t]), ch[3, t], Math.Clamp(ch[4, t], 0, 1));
    }

    public static Func<double, StoryGrade> Grade(IReadOnlyList<StoryGradeKey>? keys)
    {
        var rest = new StoryGrade(1, 1, 1, 1, 1);
        if (keys == null || keys.Count == 0) return _ => rest;
        double e = 1, s = 1; var tint = (R: 1.0, G: 1.0, B: 1.0);
        var times = new List<double>(); var vals = new List<double[]>(); var eases = new List<string?>();
        foreach (var k in keys.OrderBy(k => k.T))
        {
            e = k.Exposure ?? e; s = k.Sat ?? s;
            if (k.Tint != null) tint = Hex(k.Tint);
            times.Add(k.T); vals.Add([e, s, tint.R, tint.G, tint.B]); eases.Add(k.Ease);
        }
        var ch = new Channels(times, vals, eases);
        return t => new StoryGrade(ch[0, t], ch[1, t], ch[2, t], ch[3, t], ch[4, t]);
    }

    /// <summary>"#rrggbb" (or "#rgb") as 0..1.</summary>
    public static (double R, double G, double B) Hex(string hex)
    {
        var h = hex.TrimStart('#');
        if (h.Length == 3) h = string.Concat(h.Select(c => $"{c}{c}"));
        if (h.Length < 6) throw new FormatException($"not a colour: {hex}");
        int P(int i) => Convert.ToInt32(h.Substring(i, 2), 16);
        return (P(0) / 255.0, P(2) / 255.0, P(4) / 255.0);
    }

    /// <summary>Drawn key poses: how much of each frame shows at t (the newer
    /// over the older, both held full through the crossfade's middle so an
    /// opaque layer never dips).</summary>
    public static double[] Frames(IReadOnlyList<StoryFrame> frames, double t)
    {
        var a = new double[frames.Count];
        if (frames.Count == 0) return a;
        int cur = 0;
        for (int i = 0; i < frames.Count; i++) if (t >= frames[i].T) cur = i;
        a[cur] = 1;
        if (cur > 0 && frames[cur].Fade > 0 && t < frames[cur].T + frames[cur].Fade)
        {
            double k = (t - frames[cur].T) / frames[cur].Fade;
            a[cur] = Math.Min(1, 2 * k);
            a[cur - 1] = Math.Min(1, 2 * (1 - k));
        }
        return a;
    }
}

/// <summary>
/// The 2.5D lens: each layer is a plane at depth z from the camera at rest (1
/// the reference plane), painted as seen from the rest camera (at the canvas
/// centre), so at rest every layer sits where it was painted. A pinhole camera
/// at (X, Y), moved forward by Dolly: a layer at depth z appears z/(z - Dolly)
/// as large, and a pan of the camera by (X - W/2) shifts it by (X - W/2)/z on
/// the reference scale. Zoom magnifies everything alike (no parallax change).
/// </summary>
public static class StoryLens
{
    /// <summary>How near a plane may come before the dolly passes it (depth units).</summary>
    public const double Nearest = 0.05;

    /// <summary>The screen transform of a layer at depth z: screen = (Ox, Oy) + Scale * R(Rot) * p,
    /// for p in canvas px. Screen in pixels; Rot in radians.</summary>
    public static (double Scale, double Ox, double Oy, double Rot) Layer(StoryView cam, double z, double canvasW, double canvasH, double screenW, double screenH)
    {
        double k = screenW / canvasW * cam.Zoom;
        double dz = Math.Max(Nearest, z - cam.Dolly);
        double f = z / dz;
        double cx = canvasW / 2, cy = canvasH / 2;
        // The point at the origin of the canvas, projected; then turned about the screen's centre.
        double ox = k * ((cx - cam.X) / dz - cx * f), oy = k * ((cy - cam.Y) / dz - cy * f);
        double r = cam.Rot * Math.PI / 180, c = Math.Cos(r), s = Math.Sin(r);
        return (k * f, screenW / 2 + c * ox - s * oy, screenH / 2 + s * ox + c * oy, r);
    }

    public static (double X, double Y) Project(StoryView cam, double z, double px, double py, double canvasW, double canvasH, double screenW, double screenH)
    {
        var (sc, ox, oy, r) = Layer(cam, z, canvasW, canvasH, screenW, screenH);
        double c = Math.Cos(r), s = Math.Sin(r);
        return (ox + sc * (c * px - s * py), oy + sc * (s * px + c * py));
    }
}
