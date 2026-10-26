using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>--canopy-log's per-zone tally (CanopyLog).</summary>
public partial class CanopyLogger : Node
{
    internal readonly List<CanopyLog.Tree> Trees = new();
    Vector4? fade;

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
        foreach (var t in Trees)
        {
            float flat = new Vector2(t.At.X - her.X, t.At.Z - her.Z).Length();
            if (flat < t.Near) t.Near = flat;
            if (flat > 70) continue;
            var vb = view * (t.At + t.Up * t.Lo);
            var vt = view * (t.At + t.Up * t.Top);
            if (Mathf.Max(vb.Z, vt.Z) > -1)
            {
                if (Mathf.Min(vb.Z, vt.Z) > -1) continue;
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
            if (f > 0.5f) t.Secs += dt;
        }
    }

    public override void _ExitTree()
    {
        var hit = Trees.Where(t => t.Secs > 0).OrderByDescending(t => t.Secs).ToList();
        GD.Print($"canopy-log {GetParent()?.Name}: {hit.Count} of {Trees.Count} trees faded > 0.5");
        foreach (var t in hit)
            GD.Print($"canopy-log tree x {t.At.X:0.0} z {t.At.Z:0.0} {t.Species} faded {t.Secs:0.0} s, her path {t.Near:0.0} m from its trunk{(t.Near < 2 ? " IN LANE" : "")}");
    }
}
