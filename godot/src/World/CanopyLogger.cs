using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>--canopy-log's per-zone tally (CanopyLog). With --canopy-burst N,K (and --shot, the engine at --fixed-fps 60)
/// it also takes K consecutive frames at each of the first N times a tree starts to ease in or out (4 s apart at least),
/// tagged easeNNin_KK / easeNNout_KK, for judging the fade in motion.</summary>
public partial class CanopyLogger : Node
{
    /// <summary>The zone's fader: its trees, and (canopy_fade.w 2) their fades as drawn.</summary>
    internal CanopyFader Fader = null!;
    IReadOnlyList<CanopyLog.Tree> Trees => Fader.Trees;
    public CanopyLogger() => ProcessPriority = 1001;
    Vector4? fade;
    static readonly int[]? Burst = SurvivorUnchained.Args.Get("canopy-burst") is string cb && cb.Split(',') is { Length: 2 } bp
        && int.TryParse(bp[0], out var bn) && int.TryParse(bp[1], out var bk) ? new[] { bn, bk } : null;
    static int events;
    static double lastEvent = -99;
    static string burstTag = "";
    static int burstLeft;
    static CanopyLog.Tree? burstTree;

    public override void _Process(double delta)
    {
        var her4 = HouseFade.Her;
        if (her4.W <= 0 || GetViewport().GetCamera3D() is not { } cam) return;
        var her = new Vector3(her4.X, her4.Y, her4.Z);
        fade ??= KitLook.CanopyFade;
        if (!KitLook.CanopyPlaying) return;
    var fd = fade.Value;
        var view = cam.GetCameraTransform().AffineInverse();
        var hv = view * her;
        float hz = Mathf.Min(hv.Z, -0.5f);
        float ky = 1f / Mathf.Max(Mathf.Abs(cam.GetCameraTransform().Basis.Z.Y), 0.3f);
        var p = new Vector2(hv.X, hv.Y * ky);
        float dt = (float)delta;
        if (burstLeft > 0) { SurvivorUnchained.Shots.Want($"{burstTag}_{Burst![1] - burstLeft:00}", -0.001); burstLeft--; }
        // (w 2, the shader's: her body, feet to head, on the screen)
        var fv = view * (her - new Vector3(0, 1.1f, 0));
        var tv = view * (her + new Vector3(0, 0.7f, 0));
        var f0 = new Vector2(fv.X, fv.Y) * (hz / Mathf.Min(fv.Z, -0.5f));
        var f1 = new Vector2(tv.X, tv.Y) * (hz / Mathf.Min(tv.Z, -0.5f));
        int inFrame = 0, easing = 0, crossed = 0, byLens = 0, part = 0; string dbg = "";
        var vp = GetViewport().GetVisibleRect().Size;
        foreach (var t in Trees)
        {
            float flat = new Vector2(t.At.X - her.X, t.At.Z - her.Z).Length();
            if (flat < t.Near) t.Near = flat;
            if (flat > 70) continue;
            float f, fHer;
            bool lens;
            if (fd.W > 1.5f)
            {
                // (w 2: the fader's own, as drawn)
                f = t.Shown; fHer = t.ForHer ? 1 : 0; lens = t.ForLens;
                if (lens) Lens(t);
                if (cam.IsPositionBehind(t.At + t.Up * t.Top) && cam.IsPositionBehind(t.At)) { t.F = f; continue; }
                goto tally;
            }
            var vb = view * (t.At + t.Up * t.Lo);
            var vt = view * (t.At + t.Up * t.Top);
            // (the shader's: a crown within 1 m of the lens's plane is cut whole)
            float z0 = Mathf.Max(vb.Z, vt.Z);
            lens = z0 > -(t.R * t.Up.Length() + 1);
            if (Mathf.Max(vb.Z, vt.Z) > -1)
            {
                if (Mathf.Min(vb.Z, vt.Z) > -1) { if (lens) Lens(t); continue; }
                if (vb.Z > -1) vb = vt.Lerp(vb, (-1 - vt.Z) / (vb.Z - vt.Z));
                else vt = vb.Lerp(vt, (-1 - vb.Z) / (vt.Z - vb.Z));
            }
            var a = new Vector2(vb.X, vb.Y) * (hz / Mathf.Min(vb.Z, -0.5f));
            var b = new Vector2(vt.X, vt.Y) * (hz / Mathf.Min(vt.Z, -0.5f));
            float rr = t.R * t.Up.Length() * hz / Mathf.Min(0.5f * (vb.Z + vt.Z), -0.5f);
            if (fd.W > 1.5f)
            {
                var ab = b - a; var fb = f1 - f0;
                static float T(Vector2 q, Vector2 o, Vector2 e) => Mathf.Clamp((q - o).Dot(e) / Mathf.Max(e.Dot(e), 1e-4f), 0, 1);
                float r1 = rr * t.Taper, t0 = T(f0, a, ab), t1 = T(f1, a, ab);
                float d0 = (f0 - (a + ab * t0)).Length() - Mathf.Lerp(rr, r1, t0), d1 = (f1 - (a + ab * t1)).Length() - Mathf.Lerp(rr, r1, t1);
                float d2 = (a - (f0 + fb * T(a, f0, fb))).Length() - rr, d3 = (b - (f0 + fb * T(b, f0, fb))).Length() - r1;
                float c1 = ab.X * (f0.Y - a.Y) - ab.Y * (f0.X - a.X), c2 = ab.X * (f1.Y - a.Y) - ab.Y * (f1.X - a.X);
                float c3 = fb.X * (a.Y - f0.Y) - fb.Y * (a.X - f0.X), c4 = fb.X * (b.Y - f0.Y) - fb.Y * (b.X - f0.X);
                float d = (c1 * c2 < 0 && c3 * c4 < 0 ? -Mathf.Lerp(rr, r1, c3 / (c3 - c4)) : Mathf.Min(Mathf.Min(d0, d1), Mathf.Min(d2, d3))) - 0.35f;
                f = (1 - Mathf.SmoothStep(fd.X, fd.X + fd.Y, d)) * Mathf.SmoothStep(-0.5f, 0.5f, z0 + t.R * t.Up.Length() - hv.Z);
            }
            else
            {
                a.Y *= ky; b.Y *= ky;
                var ab = b - a;
                float s = Mathf.Clamp((p - a).Dot(ab) / Mathf.Max(ab.Dot(ab), 1e-4f), 0, 1);
                float d = (p - (a + ab * s)).Length() - rr;
                f = 1 - Mathf.SmoothStep(fd.X, fd.X + fd.Y, d);
            }
            if (lens) Lens(t);
            fHer = f;
            f = Mathf.Max(f, Mathf.SmoothStep(-(t.R * t.Up.Length() + 2.5f), -(t.R * t.Up.Length() + 1), z0));
        tally:
            if (f > 0.5f) t.Secs += dt;
            if (Burst != null && burstLeft == 0 && events < Burst[0] && SurvivorUnchained.Shots.Clock - lastEvent > 4)
            {
                // (caught mid-ease, the dither at its thickest: the screen door the motion judge saw)
                string? dir = f is > 0.3f and < 0.7f ? (f > t.F ? "in" : f < t.F ? "out" : "held") : null;
                if (dir != null)
                {
                    events++; lastEvent = SurvivorUnchained.Shots.Clock;
                    burstTag = $"ease{events:00}{dir}"; burstLeft = Burst[1]; burstTree = t;
                    GD.Print($"canopy-ease {burstTag} tree x {t.At.X:0.0} z {t.At.Z:0.0} {t.Species} f {t.F:0.00}->{f:0.00} at {lastEvent:0.00}s");
                }
            }
            if (t == burstTree && burstLeft > 0) GD.Print($"canopy-ease {burstTag} f {f:0.00}");
            // (the per-frame tally: a faded tree's stump on the screen; a tree mid-ease; one crossing half either way)
            bool seen = !cam.IsPositionBehind(t.At) && new Rect2(Vector2.Zero, vp).HasPoint(cam.UnprojectPosition(t.At));
            if (f > 0.5f && seen) { inFrame++; if (fHer <= 0.5f) byLens++; }
            if (f > 0.5f && seen && Dbg) dbg += $" [{t.Species[0]} {t.At.X - her.X:0.0},{t.At.Z - her.Z:0.0}]";
            if (f is > 0.02f and < 0.98f && seen) easing++;
            if (f is > 0.002f and < 0.998f && seen) part++;
            if ((f > 0.5f) != (t.F > 0.5f) && seen) crossed++;
            t.F = f;
        }
        frames++; sumIn += inFrame; maxIn = Mathf.Max(maxIn, inFrame); sumEase += easing; crossings += crossed;
        if (crossed > 0) crossFrames++;
        if (part > 0) partFrames++;
        started += Fader.Started; sumMs += Fader.Ms; maxMs = System.Math.Max(maxMs, Fader.Ms); sumTested += Fader.Tested; sumWrites += Fader.Writes;
        GD.Print($"canopy-frame {SurvivorUnchained.Shots.Clock:0.000} faded {inFrame} lens {byLens} easing {easing} crossed {crossed} her {her.X:0.0},{her.Z:0.0} " +
            $"part {part} started {Fader.Started} tested {Fader.Tested} writes {Fader.Writes} cpu {Fader.Ms:0.0000} set {Fader.MsSet:0.0000} judge {Fader.MsJudge:0.0000}{dbg}");
    }
    static readonly bool Dbg = SurvivorUnchained.Args.Has("canopy-trees");
    int frames, sumIn, maxIn, sumEase, crossings, crossFrames, partFrames, started, sumTested, sumWrites;
    double sumMs, maxMs;

    /// <summary>A crown cut whole at the lens (counted; with --canopy-burst, a burst of the frames as it is).</summary>
    void Lens(CanopyLog.Tree t)
    {
        lensFrames++;
        if (Burst == null || burstLeft > 0 || events >= Burst[0] + 3 || SurvivorUnchained.Shots.Clock - lastLens < 6) return;
        lastLens = SurvivorUnchained.Shots.Clock; events++;
        burstTag = $"lens{events:00}"; burstLeft = Burst[1]; burstTree = t;
        GD.Print($"canopy-ease {burstTag} tree x {t.At.X:0.0} z {t.At.Z:0.0} {t.Species} at the lens, at {lastLens:0.00}s");
    }
    static double lastLens = -99;
    int lensFrames;

    public override void _ExitTree()
    {
        var hit = Trees.Where(t => t.Secs > 0).OrderByDescending(t => t.Secs).ToList();
        GD.Print($"canopy-log {GetParent()?.Name}: {hit.Count} of {Trees.Count} trees faded > 0.5; {lensFrames} tree-frames cut at the lens");
        if (frames > 0)
            GD.Print($"canopy-stats {GetParent()?.Name}: {frames} frames, stumps in frame mean {(float)sumIn / frames:0.00} max {maxIn}, " +
                $"easing mean {(float)sumEase / frames:0.00}, {crossings} half-crossings in {crossFrames} frames; part-faded in {partFrames} frames " +
                $"({100f * partFrames / frames:0.0}%), {started} fades started; fader cpu mean {sumMs / frames:0.0000} ms max {maxMs:0.0000} ms, " +
                $"trees tested mean {(float)sumTested / frames:0.0}, writes mean {(float)sumWrites / frames:0.00}");
        foreach (var t in hit)
            GD.Print($"canopy-log tree x {t.At.X:0.0} z {t.At.Z:0.0} {t.Species} faded {t.Secs:0.0} s, her path {t.Near:0.0} m from its trunk{(t.Near < 2 ? " IN LANE" : "")}");
    }
}
