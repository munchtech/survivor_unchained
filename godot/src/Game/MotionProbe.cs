using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>
/// --probe: how smoothly she moves across the screen, measured (a developer's
/// switch). Each frame her chest is put on the screen; the step from the last
/// frame is compared with the average step over the frames round it. Smooth
/// motion (however fast) differs from its average by a fraction of a pixel;
/// a figure that stands still for a frame and then jumps differs by most of a
/// jump. Printed every --probe-every seconds (default 4) as the mean step,
/// the judder (its root mean square difference) and the worst, in pixels of
/// the window, with how often the frame held no step of the fight.
/// </summary>
public sealed class MotionProbe
{
    readonly List<Vector2> at = new();
    readonly List<float> dts = new();
    readonly double every = Args.Num("probe-every", 4);
    double t;

    public void Frame(Camera3D cam, Vector3 her, double dt)
    {
        var chest = her + Vector3.Up * 1.1f;
        if (cam.IsPositionBehind(chest)) return;
        at.Add(cam.UnprojectPosition(chest));
        dts.Add((float)dt);
        t += dt;
        if (t < every) return;
        t = 0;
        Report();
        at.Clear();
        dts.Clear();
    }

    void Report()
    {
        const int W = 7;
        int n = at.Count;
        if (n < 2 * W + 3) return;
        var v = new Vector2[n];
        for (int i = 1; i < n; i++) v[i] = at[i] - at[i - 1];
        double sum = 0, sq = 0, worst = 0, mean = 0;
        int k = 0;
        for (int i = W + 1; i < n - W; i++)
        {
            var avg = Vector2.Zero;
            for (int j = -W; j <= W; j++) avg += v[i + j];
            avg /= 2 * W + 1;
            double d = (v[i] - avg).Length();
            sum += d; sq += d * d; worst = Math.Max(worst, d);
            mean += v[i].Length();
            k++;
        }
        float fps = dts.Count / Math.Max(1e-6f, Sum(dts));
        GD.Print($"probe: {k} frames at {fps:0} fps, interp {(SurvivorUnchained.View.Interp.On ? "on" : "off")}: her step {mean / k:0.00} px/frame, " +
                 $"judder rms {Math.Sqrt(sq / k):0.00} px, mean {sum / k:0.00}, worst {worst:0.00}");
    }

    static float Sum(List<float> xs) { float s = 0; foreach (var x in xs) s += x; return s; }
}
