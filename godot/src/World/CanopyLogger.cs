using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>--canopy-log's per-zone tally (CanopyLog). With --canopy-burst N,K (and --shot, the engine at --fixed-fps 60)
/// it also takes K consecutive frames at each of the first N times a tree starts to ease in or out (4 s apart at least),
/// tagged easeNNin_KK / easeNNout_KK, for judging the fade in motion.</summary>
public partial class CanopyLogger : Node
{
    internal readonly List<CanopyLog.Tree> Trees = new();
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
        foreach (var t in Trees)
        {
            float flat = new Vector2(t.At.X - her.X, t.At.Z - her.Z).Length();
            if (flat < t.Near) t.Near = flat;
            if (flat > 70) continue;
            var vb = view * (t.At + t.Up * t.Lo);
            var vt = view * (t.At + t.Up * t.Top);
            // (the shader's: a crown within 1 m of the lens's plane is cut whole)
            float z0 = Mathf.Max(vb.Z, vt.Z);
            bool lens = z0 > -(t.R * t.Up.Length() + 1);
            if (Mathf.Max(vb.Z, vt.Z) > -1)
            {
                if (Mathf.Min(vb.Z, vt.Z) > -1) { if (lens) Lens(t); continue; }
                if (vb.Z > -1) vb = vt.Lerp(vb, (-1 - vt.Z) / (vb.Z - vt.Z));
                else vt = vb.Lerp(vt, (-1 - vb.Z) / (vt.Z - vb.Z));
            }
            var a = new Vector2(vb.X, vb.Y) * (hz / Mathf.Min(vb.Z, -0.5f));
            var b = new Vector2(vt.X, vt.Y) * (hz / Mathf.Min(vt.Z, -0.5f));
            float rr = t.R * t.Up.Length() * hz / Mathf.Min(0.5f * (vb.Z + vt.Z), -0.5f);
            a.Y *= ky; b.Y *= ky;
            var ab = b - a;
            float s = Mathf.Clamp((p - a).Dot(ab) / Mathf.Max(ab.Dot(ab), 1e-4f), 0, 1);
            float d = (p - (a + ab * s)).Length() - rr;
            float f = 1 - Mathf.SmoothStep(fd.X, fd.X + fd.Y, d);
            if (lens) Lens(t);
            f = Mathf.Max(f, Mathf.SmoothStep(-(t.R * t.Up.Length() + 2.5f), -(t.R * t.Up.Length() + 1), z0));
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
            t.F = f;
        }
    }

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
        foreach (var t in hit)
            GD.Print($"canopy-log tree x {t.At.X:0.0} z {t.At.Z:0.0} {t.Species} faded {t.Secs:0.0} s, her path {t.Near:0.0} m from its trunk{(t.Near < 2 ? " IN LANE" : "")}");
    }
}
