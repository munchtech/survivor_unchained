using SurvivorUnchained.Core;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The loincloth panel's swing (Core/PanelSwing.cs) as the tools
/// have it (tools/anim/helpers.py panel_turn and _swing_spread, values
/// printed from them), with rig_helpers.json's numbers.</summary>
public class PanelSwingTests
{
    static readonly PanelSwing.Law Law = new(1.15, 12.0, 8.0, 20.0, 0.6);

    [Theory]
    [InlineData(0, 0, 0, 0, 0.0)]
    [InlineData(10, 38, 4, 1, 33.349999999999994)]       // run foot strike (frame 14)
    [InlineData(34, 26, 0, 3, 29.133333333333333)]       // legs crossing: the smooth max
    [InlineData(30, 30, 0, 0, 27.599999999999998)]
    [InlineData(-38, -20, 0, 0, 0.0)]                    // both back: never swings back
    [InlineData(84, 90, 25, 17, 37.605)]                 // sit_log: knees apart, damped
    [InlineData(5, -3, 2, 2, 0.2608796296296295)]
    [InlineData(86, -35, 4, -5, 88.55)]                  // sprint knee drive
    [InlineData(12, 0, 10, 11, 3.6201416015624996)]
    public void TurnMatchesTheTools(double fl, double fr, double al, double ar, double want)
        => Assert.Equal(want, PanelSwing.Turn(Law, fl, fr, al, ar), 9);

    [Fact]
    public void SwingAndSpreadMatchTheTools()
    {
        var (s, o) = PanelSwing.SwingSpread(0.059, -0.998, 0.003, 0.059, -0.998, 0.003, 1);
        Assert.Equal(0.0, s, 9); Assert.Equal(0.0, o, 9);
        (s, o) = PanelSwing.SwingSpread(0.05, -0.5, 0.86, 0.059, -0.998, 0.003, 1);
        Assert.Equal(59.65424868697773, s, 9); Assert.Equal(-0.5164313121980157, o, 9);
        (s, o) = PanelSwing.SwingSpread(-0.3, -0.9, 0.3, -0.059, -0.998, 0.003, -1);
        Assert.Equal(18.262717539544067, s, 9); Assert.Equal(14.075187828925216, o, 9);
    }

    [Theory]
    [InlineData(double.NaN, 40, 1 / 30.0, 40.0)]                    // first frame: the law
    [InlineData(90, 79.2, 1 / 30.0, 83.89366065187644)]             // run f5 -> f6: lags the fall
    [InlineData(84, 60.4, 1 / 30.0, 70.65651772076704)]
    [InlineData(100, 40, 1 / 30.0, 85.0)]                           // capped: 450 deg/s, 15 a frame
    [InlineData(100, 40, 1 / 60.0, 92.5)]
    [InlineData(100, 99, 1 / 60.0, 99.65924063020044)]
    [InlineData(105.3, 99.2, 1 / 144.0, 104.32780483434048)]
    [InlineData(80, 20, 0.5, 20.000223599190324)]                  // a long frame: all the way down
    [InlineData(50, 51, 1 / 60.0, 51.0)]                            // rising: the law at once
    [InlineData(70, 30, 0.0, 70.0)]                                 // no time: held
    public void FallMatchesTheTools(double prev, double target, double dt, double want)
        => Assert.Equal(want, PanelSwing.Fall(Law, prev, target, dt), 9);

    [Fact]
    public void FallsNoFasterThanTheRateAndNeverBelowTheLaw()
    {
        // The law dropping 60 degrees in one step: the panel takes it at most 450 deg/s, whatever the frame rate.
        foreach (double dt in new[] { 1 / 30.0, 1 / 60.0, 1 / 144.0 })
        {
            double th = 100, t = 0;
            while (t < 0.5)
            {
                double next = PanelSwing.Fall(Law, th, 40, dt);
                Assert.InRange(th - next, 0, 450 * dt + 1e-9);
                Assert.True(next >= 40);
                th = next; t += dt;
            }
            Assert.InRange(th, 40, 40.01);
        }
    }

    [Fact]
    public void SmoothAcrossTheLegsCrossing()
    {
        // As one thigh passes the other the turn changes by no more than its inputs do.
        double last = PanelSwing.Turn(Law, 40, 20, 0, 0);
        for (double d = -20; d <= 20; d += 0.5)
        {
            double t = PanelSwing.Turn(Law, 30 - d / 2, 30 + d / 2, 0, 0);
            if (d > -20) Assert.InRange(System.Math.Abs(t - last), 0, 1.15 * 0.5 + 1e-9);
            last = t;
        }
    }
    static readonly PanelSwing.FoldLaw Fold = new(25.0, 25.0, 1.6, 0.45, 0.0, 1.12, 9.0, 4);

    [Fact]
    public void FoldMatchesTheTools()
    {
        // One run of frames through helpers.py panel_fold (turn, the upper's turn, dt -> fold, values printed from it):
        // lying on the rising thigh, trailing it forward as it falls, capped at two steps, swinging back to plumb.
        var st = new PanelSwing.FoldState();
        (double turn, double th, double dt, double want)[] seq =
        {
            (10, 11.5, 1 / 30.0, -10.760869565217389), (30, 34.5, 1 / 30.0, -14.282608695652172),
            (70, 80.5, 1 / 30.0, -21.32608695652172), (84, 96.6, 1 / 30.0, -9.67300837855241),
            (60, 85, 1 / 30.0, 13.577133866600235), (35, 60, 1 / 30.0, 37.3017178573525),
            (30, 45, 1 / 30.0, 41.70652326800622), (28, 36, 1 / 30.0, 34.352328749763515),
            (28, 32.2, 1 / 60.0, 28.918194229131295), (5, 6, 1 / 144.0, 50.0),
            (0, 0, 0.5, 0.27510640043084555), (0, 0, 0.0, 0.27510640043084555),   // (a long frame: substeps so w h <= 1)
        };
        foreach (var (turn, th, dt, want) in seq)
            Assert.Equal(want, PanelSwing.Fold(Fold, st, turn, 1.15, th, dt), 9);
        var (a, b, n) = PanelSwing.FoldWeights(Fold, 37.3017178573525);
        Assert.Equal(1.0, a, 9); Assert.Equal(0.4920687142941, b, 9); Assert.Equal(0.0, n, 9);
        (a, b, n) = PanelSwing.FoldWeights(Fold, -21.32608695652172);
        Assert.Equal(0.0, a, 9); Assert.Equal(0.0, b, 9); Assert.Equal(0.8530434782608688, n, 9);
    }

    // (Body 18) the drop past drop_from (rig_helpers.json "drop" 0.4, "drop_from" 45): helpers.panel_turn's numbers
    static readonly PanelSwing.Law Dropped = new(1.15, 12.0, 8.0, 20.0, 0.6, 0.04, 450, 0.4, 45);

    [Theory]
    [InlineData(77, 10, 2, 1, 68.99999999999999)]
    [InlineData(30, 5, 0, 0, 24.15)]
    [InlineData(95, 90, 25, 25, 40.029583333333335)]
    [InlineData(60, 62, 3, 4, 59.31249999999999)]
    public void DropMatchesTheTools(double fl, double fr, double al, double ar, double want) =>
        Assert.Equal(want, PanelSwing.Turn(Dropped, fl, fr, al, ar), 9);

    [Fact]
    public void DropNeverRaisesTheTurnAndLeavesTheWalkAlone()
    {
        for (double f = 0; f <= 110; f += 0.5)
        {
            Assert.True(PanelSwing.Turn(Dropped, f, 0, 0, 0) <= PanelSwing.Turn(Law, f, 0, 0, 0) + 1e-12);
            if (f <= 40) Assert.Equal(PanelSwing.Turn(Law, f, 0, 0, 0), PanelSwing.Turn(Dropped, f, 0, 0, 0), 12);
            // (still rising with the thigh: never turns back as the knee comes up)
            Assert.True(PanelSwing.Turn(Dropped, f + 0.5, 0, 0, 0) >= PanelSwing.Turn(Dropped, f, 0, 0, 0));
        }
    }

    [Fact]
    public void SideWeightsMatchTheTools()
    {
        var (l, r) = PanelSwing.SideWeights(77, 10, 20, 60);
        Assert.Equal(1.0, l, 12); Assert.Equal(0.0, r, 12);
        (l, r) = PanelSwing.SideWeights(35, 45, 20, 60);
        Assert.Equal(0.31640625, l, 12); Assert.Equal(0.68359375, r, 12);
    }

    // (Body 18 r4) the sprint law (rig_helpers.json "panels" "sprint"): helpers.panel_sprint / sprint_blend's numbers
    static readonly PanelSwing.SprintLaw Spr = new(81, 86, 30, 40, 10, 0.5, 0.012, 1200, 19, 1);

    [Fact]
    public void SprintMatchesTheTools()
    {
        var st = new PanelSwing.SprintState();
        (double lead, double dt, double want)[] seq =
        {
            (40, 0, 0.0), (91, 1 / 30.0, 1.0), (60, 1 / 30.0, 1.0), (32, 1 / 30.0, 1.0), (50, 1 / 30.0, 1.0),
            (88, 1 / 30.0, 1.0), (70, 0.5, 0.824592592592597), (70, 0.5, 0.0), (70, 1.0, 0.0),
        };
        foreach (var (lead, dt, want) in seq)
            Assert.Equal(want, PanelSwing.Sprint(Spr, st, lead, dt), 9);
        var b = PanelSwing.Blend(Dropped, Spr, 0.25);
        Assert.Equal(0.9874999999999999, b.Amount, 9); Assert.Equal(0.033, b.FallTau, 9); Assert.Equal(637.5, b.FallRate, 9);
        var fb = PanelSwing.Blend(Fold, Spr, 0.25);
        Assert.Equal(5.949999999999999, fb.Hz, 9); Assert.Equal(0.5875, fb.Zeta, 9);
        Assert.Equal(19.983333333333334, PanelSwing.Turn(PanelSwing.Blend(Dropped, Spr, 1.0), 49, -20, 2, 1), 9);
    }

    [Fact]
    public void SprintNeverCountsASeatOrARun()
    {
        // a seat: the thighs held at 88 (sit_log): no swing, no sprint
        var st = new PanelSwing.SprintState();
        for (int i = 0; i < 120; i++) Assert.Equal(0.0, PanelSwing.Sprint(Spr, st, 88, 1 / 60.0), 12);
        // a run (lead 34..79, a peak each 0.33 s: either thigh leads): never
        st = new PanelSwing.SprintState();
        for (int i = 0; i < 240; i++)
            Assert.Equal(0.0, PanelSwing.Sprint(Spr, st, 56.5 - 22.5 * System.Math.Cos(i / 60.0 * 2 * System.Math.PI * 3.0), 1 / 60.0), 12);
        // a sprint (lead 32..91): all of it once the first stride is in
        st = new PanelSwing.SprintState();
        for (int i = 0; i < 240; i++)
        {
            double g = PanelSwing.Sprint(Spr, st, 61.5 - 29.5 * System.Math.Cos(i / 60.0 * 2 * System.Math.PI * 3.0), 1 / 60.0);
            if (i > 30) Assert.Equal(1.0, g, 9);
        }
    }

    [Fact]
    public void StiffFoldHoldsAtALongFrame()
    {
        var f = PanelSwing.Blend(Fold, Spr, 1.0);
        var st = new PanelSwing.FoldState();
        (double turn, double th, double dt, double want)[] seq = { (40, 20, 1 / 60.0, 50.0), (10, 20, 0.1, -6.6), (10, 20, 0.25, -6.6), (0, 5, 0.5, 3.199728) };
        foreach (var (turn, th, dt, want) in seq)
            Assert.Equal(want, PanelSwing.Fold(f, st, turn, 0.5, th, dt), 5);
    }
}
