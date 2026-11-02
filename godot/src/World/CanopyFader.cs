using System.Collections.Generic;
using System.Diagnostics;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>(Env 23 r2; judge e23 r1: the fade eased by her place stood half-done in nearly every frame, a stipple that crawled
/// in motion) The canopy fade's per-tree state for canopy_fade.w 2 (kit.gdshader OWN_FOLIAGE reads it from each copy's custom
/// data g). Each frame the trees near the ground line from the play camera to her are tested: a tree is WANTED faded when its
/// crown (tapered from crown_r at its base to crown_r * crown_taper at crown_hi, then to its spire's tip) comes within
/// canopy_fade.x m of a sight line from the lens to any of nine points of her outline (feet, knees, hips, chest and shoulders
/// either side, head), and stays wanted until it is canopy_fade.y m clear (the gap: no flicker at the edge); or when its crown
/// comes within 3 m of the lens's plane (out at 3.6 m). Each eases to what it is wanted over Secs, in time, so the dither shows
/// only in those 0.3 s. A teleport (her or the camera 4 m in a frame) snaps. Cost: the trees within Reach of that line, and
/// writes only for the few easing.</summary>
public partial class CanopyFader : Node
{
    public const float Secs = 0.3f;
    const float Cell = 8f, Reach = 9f;
    readonly List<CanopyLog.Tree> trees = new();
    readonly Dictionary<(int, int), List<CanopyLog.Tree>> grid = new();
    readonly List<CanopyLog.Tree> live = new();
    readonly HashSet<CanopyLog.Tree> liveSet = new();
    readonly Vector3[] pts = new Vector3[9];
    Vector3? lastHer, lastCam;
    int stamp;
    /// <summary>This frame: wants that began, trees tested, copies written, the CPU time (ms).</summary>
    public int Started, Tested, Writes;
    public double Ms;
    internal IReadOnlyList<CanopyLog.Tree> Trees => trees;

    public CanopyFader() => ProcessPriority = 1000;

    internal void Add(CanopyLog.Tree t)
    {
        trees.Add(t);
        var k = Key(t.At);
        if (!grid.TryGetValue(k, out var l)) grid[k] = l = new();
        l.Add(t);
    }

    static (int, int) Key(Vector3 p) => (Mathf.FloorToInt(p.X / Cell), Mathf.FloorToInt(p.Z / Cell));

    public override void _Process(double delta)
    {
        long t0 = Stopwatch.GetTimestamp();
        Started = Tested = Writes = 0;
        var her4 = HouseFade.Her;
        var cam = GetViewport().GetCamera3D();
        var fd = KitLook.CanopyFade;
        if (!KitLook.CanopyPlaying || fd.W < 1.5f || her4.W <= 0 || cam == null)
        {
            foreach (var t in live) { t.Want = t.ForHer = t.ForLens = false; t.Ease = 0; Write(t, 0); }
            live.Clear(); liveSet.Clear(); lastHer = null;
            Ms = (Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency;
            return;
        }
        var her = new Vector3(her4.X, her4.Y, her4.Z);
        var ct = cam.GetCameraTransform();
        var eye = ct.Origin;
        bool snap = lastHer is not { } lh || lh.DistanceTo(her) > 4 || lastCam is not { } lc || lc.DistanceTo(eye) > 4;
        lastHer = her; lastCam = eye;
        var view = ct.AffineInverse();
        var side = new Vector3(ct.Basis.X.X, 0, ct.Basis.X.Z).Normalized();
        // her outline (her chest the survivor global, as the shader's: feet 1.1 m under it, the head's top 0.7 m over)
        pts[0] = her + new Vector3(0, -1.0f, 0); pts[1] = her + new Vector3(0, -0.55f, 0);
        pts[2] = her + new Vector3(0, -0.2f, 0) + side * 0.22f; pts[3] = her + new Vector3(0, -0.2f, 0) - side * 0.22f;
        pts[4] = her; pts[5] = her + side * 0.3f; pts[6] = her - side * 0.3f;
        pts[7] = her + new Vector3(0, 0.45f, 0); pts[8] = her + new Vector3(0, 0.65f, 0);
        stamp++;
        var a = new Vector2(eye.X, eye.Z); var b = new Vector2(her.X, her.Z);
        int x0 = Mathf.FloorToInt((Mathf.Min(a.X, b.X) - Reach) / Cell), x1 = Mathf.FloorToInt((Mathf.Max(a.X, b.X) + Reach) / Cell);
        int z0 = Mathf.FloorToInt((Mathf.Min(a.Y, b.Y) - Reach) / Cell), z1 = Mathf.FloorToInt((Mathf.Max(a.Y, b.Y) + Reach) / Cell);
        var ab = b - a;
        for (int cx = x0; cx <= x1; cx++)
            for (int cz = z0; cz <= z1; cz++)
            {
                if (!grid.TryGetValue((cx, cz), out var l)) continue;
                foreach (var t in l)
                {
                    var p = new Vector2(t.At.X, t.At.Z);
                    float u = Mathf.Clamp((p - a).Dot(ab) / Mathf.Max(ab.Dot(ab), 1e-4f), 0, 1);
                    if ((p - (a + ab * u)).Length() > Reach) continue;
                    t.Stamp = stamp; Tested++;
                    Judge(t, eye, view, fd);
                    if (t.Want && liveSet.Add(t)) live.Add(t);
                }
            }
        float step = snap ? 1f : (float)delta / Secs;
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var t = live[i];
            // (a tree out of reach this frame is no longer wanted)
            if (t.Stamp != stamp) t.Want = t.ForHer = t.ForLens = false;
            t.Ease = Mathf.MoveToward(t.Ease, t.Want ? 1 : 0, step);
            float s = t.Ease * t.Ease * (3 - 2 * t.Ease);
            if (Mathf.Abs(s - t.Shown) > 0.002f || (s != t.Shown && (s == 0 || s == 1))) Write(t, s);
            if (!t.Want && t.Ease <= 0) { live.RemoveAt(i); liveSet.Remove(t); }
        }
        Ms = (Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency;
    }

    void Write(CanopyLog.Tree t, float s)
    {
        t.Shown = s;
        foreach (var (mm, i) in t.Inst) { mm.SetInstanceCustomData(i, new Color(t.CustR, s, 0, 0)); Writes++; }
    }

    void Judge(CanopyLog.Tree t, Vector3 eye, Transform3D view, Vector4 fd)
    {
        float sc = t.Up.Length(), rb = t.R * sc, rc = rb * t.Taper, rt = Mathf.Min(rc, 0.25f * sc);
        Vector3 B = t.At + t.Up * t.Lo, C = t.At + t.Up * t.Top, T = t.At + t.Up * t.Tip;
        float zn = Mathf.Max((view * B).Z, Mathf.Max((view * C).Z, (view * T).Z));
        t.ForLens = zn > -(rb + (t.ForLens ? 3.6f : 3.0f));
        bool was = t.Want;
        t.ForHer = Covers(eye, pts, B, C, T, rb, rc, rt, t.ForHer ? fd.Y : fd.X);
        t.Want = t.ForHer || t.ForLens;
        if (t.Want && !was) Started++;
    }

    /// <summary>Whether a crown (B to C, radius rb to rc; C to T, rc to rt) comes within m of a sight line from eye to any of pts.</summary>
    internal static bool Covers(Vector3 eye, Vector3[] pts, Vector3 B, Vector3 C, Vector3 T, float rb, float rc, float rt, float m)
    {
        bool spire = (T - C).LengthSquared() > 0.01f;
        foreach (var q in pts)
        {
            if (Near(eye, q, B, C, rb, rc) < m) return true;
            if (spire && Near(eye, q, C, T, rc, rt) < m) return true;
        }
        return false;
    }

    /// <summary>The least gap between the segment p0-p1 and a cone's surface (axis a0-a1, radius r0 to r1): at the two
    /// segments' closest points and at five points down the axis.</summary>
    internal static float Near(Vector3 p0, Vector3 p1, Vector3 a0, Vector3 a1, float r0, float r1)
    {
        var d1 = p1 - p0; var d2 = a1 - a0; var r = p0 - a0;
        float aa = d1.Dot(d1), ee = d2.Dot(d2), f = d2.Dot(r), c = d1.Dot(r), bb = d1.Dot(d2), den = aa * ee - bb * bb;
        float s = den > 1e-6f ? Mathf.Clamp((bb * f - c * ee) / den, 0, 1) : 0;
        float u = Mathf.Clamp((bb * s + f) / Mathf.Max(ee, 1e-6f), 0, 1);
        s = Mathf.Clamp((bb * u - c) / Mathf.Max(aa, 1e-6f), 0, 1);
        float best = (p0 + d1 * s - (a0 + d2 * u)).Length() - Mathf.Lerp(r0, r1, u);
        for (int k = 0; k <= 4; k++)
        {
            float w = k * 0.25f;
            var x = a0 + d2 * w;
            float sp = Mathf.Clamp((x - p0).Dot(d1) / Mathf.Max(aa, 1e-6f), 0, 1);
            best = Mathf.Min(best, (p0 + d1 * sp - x).Length() - Mathf.Lerp(r0, r1, w));
        }
        return best;
    }
}
