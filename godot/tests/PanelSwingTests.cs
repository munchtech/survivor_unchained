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
}
