using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>
/// --lookdev-fx (L1 B6): the FX language's proof on the lookdev stage: cel bolts (FxCel.Bolt, the cinder's, exactly as
/// BattleFx.Flight draws one) held in flight by the fire row, one where the close view sees it beside her and one where
/// the play view sees it by the camp's fire. Needs --fx-cel on (FxCel.On); nothing at --cel off (today's cinder).
/// --lookdev-fx-at X,Y,LIFT[;X,Y,LIFT...]: the bolts' heads (stage metres: right of her, toward the lens, up), flying left.
/// --lookdev-fx-size S: their width (0.85, a rank-1 cinder's).
/// --lookdev-fx-cost N: N more bolts in a grid round her, shown and hidden in turns of 1.5 s, the viewport's GPU time
/// averaged over each kind of turn (lines "fxcost: on MS off MS n N"): the effect's cost.
/// --lookdev-fx-chart R,G,B;R,G,B...: the calibration chart: each linear color (HDR, before exposure) as an unshaded opaque
/// patch 40 px square on the screen, 12 to a row from (60, 60) at 56 px steps (1080 lines), drawn as the bolts' bands are
/// (unshaded, before the exposure, AgX and grade): what each comes out as is measured by tools/style/fx_measure.py chart,
/// which writes the bands' emit. Lines "fxchart: I X Y R G B" name each patch's centre.
/// </summary>
public partial class Game
{
    static readonly bool LookFxOn = Args.Has("lookdev-fx") || Args.Has("lookdev-fx-cost");
    Batch? lookBolts;
    readonly List<(float X, float Y, float Lift)> lookBoltAt = new();
    int lookFxCost;
    double lookFxT0;
    readonly double[] lookFxSum = new double[2];
    readonly int[] lookFxN = new int[2];
    int lookFxPhase = -1, lookFxInPhase;
    Batch? lookChart;
    readonly List<Color> lookChartC = new();

    const string ChartShader = @"shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;
varying vec3 tint;
void vertex() { tint = COLOR.rgb; }
void fragment() { ALBEDO = tint; ALPHA = 1.0; }";

    void LookChart()
    {
        if (Args.Get("lookdev-fx-chart") is not string spec || GetViewport().GetCamera3D() is not { } c) return;
        if (lookChart == null)
        {
            lookChart = new Batch(new QuadMesh { Size = Vector2.One }, 400, new ShaderMaterial { Shader = new Shader { Code = ChartShader } }) { Name = "LookChart" };
            scene!.AddChild(lookChart);
            foreach (var one in spec.Split(';'))
            {
                var v = one.Split(',');
                if (v.Length < 3) continue;
                float F(string x) => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture);
                lookChartC.Add(new Color(F(v[0]), F(v[1]), F(v[2])));
            }
        }
        var vp = GetViewport().GetVisibleRect().Size;
        float k = vp.Y / 1080f;
        lookChart.Begin();
        for (int i = 0; i < lookChartC.Count; i++)
        {
            var at = new Vector2(60 + 56 * (i % 12), 60 + 56 * (i / 12)) * k;
            var w = c.ProjectPosition(at, 6f);
            float size = (c.ProjectPosition(at + new Vector2(20 * k, 0), 6f) - w).Length() * 2;
            lookChart.Add(new Transform3D(c.GlobalTransform.Basis.Scaled(Vector3.One * size), w), lookChartC[i]);
            if (lookFxN[0] == 0 && Engine.GetProcessFrames() % 600 == 0) GD.Print($"fxchart: {i} {at.X / k:0} {at.Y / k:0} {lookChartC[i].R:0.####} {lookChartC[i].G:0.####} {lookChartC[i].B:0.####}");
        }
        lookChart.End();
    }

    void LookFx(double dt)
    {
        if (lookBuiltAt >= 0 && scene != null) LookChart();
        if (!LookFxOn || !FxCel.On || lookBuiltAt < 0 || scene == null) return;
        if (lookBolts == null)
        {
            lookBolts = new Batch(new QuadMesh { Size = Vector2.One }, 400, FxCel.Bolt(School.Fire)) { Name = "LookBolts" };
            scene.AddChild(lookBolts);
            if (FxAfter.On) FxAfter.Adopt(lookBolts);
            var spec = Args.Get("lookdev-fx-at") ?? "0.75,-0.35,1.35;4.4,-1.6,1.2";
            foreach (var one in spec.Split(';'))
            {
                var v = one.Split(',');
                if (v.Length < 3) continue;
                float F(string x) => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture);
                lookBoltAt.Add((F(v[0]), F(v[1]), F(v[2])));
            }
            lookFxCost = (int)Args.Num("lookdev-fx-cost", 0f);
            for (int i = 0; i < lookFxCost; i++) lookBoltAt.Add((-4f + 8f * (i % 10) / 9f, -3f + 6f * (i / 10) / Mathf.Max(1, (lookFxCost - 1) / 10), 1.2f));
            lookFxT0 = Shots.Clock;
            if (lookFxCost > 0) RenderingServer.ViewportSetMeasureRenderTime(GetViewport().GetViewportRid(), true);
        }
        float size = Args.Num("lookdev-fx-size", 0.85f);
        lookBolts.Begin();
        foreach (var (x, y, lift) in lookBoltAt)
        {
            var w = lookP + lookR * x + lookF * y;
            w.Y = lookP.Y + lift;
            lookBolts.Add(FxCel.BoltAt(w, -lookR, size), new Color(((int)(x * 13 + y * 7) & 63) / 63f, 0, 0, 1));
        }
        lookBolts.End();
        if (lookFxCost <= 0) return;
        // the cost: turns of 1.5 s, bolts shown (1) and hidden (0); the first 20 frames of a turn left out (the change settling)
        int phase = (int)((Shots.Clock - lookFxT0) / 1.5) % 2 == 0 ? 1 : 0;
        if (phase != lookFxPhase) { lookFxPhase = phase; lookFxInPhase = 0; lookBolts.Visible = phase == 1; }
        else if (++lookFxInPhase > 20)
        {
            lookFxSum[phase] += RenderingServer.ViewportGetMeasuredRenderTimeGpu(GetViewport().GetViewportRid());
            lookFxN[phase]++;
            if ((lookFxN[0] + lookFxN[1]) % 120 == 0 && lookFxN[0] > 0 && lookFxN[1] > 0)
                GD.Print($"fxcost: on {lookFxSum[1] / lookFxN[1]:0.000} off {lookFxSum[0] / lookFxN[0]:0.000} n {lookBoltAt.Count} frames {lookFxN[1]}+{lookFxN[0]}");
        }
    }
}
