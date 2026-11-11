using SurvivorUnchained.View;
using Xunit;

namespace SurvivorUnchained.Tests;

public class FeelRulesTests
{
    [Fact]
    public void FoldKeepsTwoAndAddsTheRestIntoTheFirst()
    {
        var shown = FeelRules.Fold(new double[] { 50, 40, 30, 20, 10 }, false, out var folded);
        Assert.Equal(2, shown.Count);
        Assert.Equal((0, 50.0 + 30 + 20 + 10), shown[0]);
        Assert.Equal((1, 40.0), shown[1]);
        Assert.Equal(new[] { 0, 1, 0, 0, 0 }, folded);
    }

    [Fact]
    public void FoldMassStepIsOneTotal()
    {
        var shown = FeelRules.Fold(new double[] { 5, 4, 3, 2, 1 }, true, out var folded);
        Assert.Single(shown);
        Assert.Equal(15.0, shown[0].Sum);
        Assert.All(folded, f => Assert.Equal(0, f));
    }

    [Fact]
    public void FoldSmallInputs()
    {
        var one = FeelRules.Fold(new double[] { 7 }, false, out var f1);
        Assert.Single(one);
        Assert.Equal(7.0, one[0].Sum);
        Assert.Equal(new[] { 0 }, f1);
        var none = FeelRules.Fold(new double[0], false, out var f0);
        Assert.Empty(none);
        Assert.Empty(f0);
    }

    [Fact]
    public void NumberSpotIsAwayFromHerAndOverTheBody()
    {
        var (x, y) = FeelRules.NumberSpot(100, 200, 140, 300, 0, 60, 40);
        Assert.Equal(120 + FeelRules.NumberAside, x);
        Assert.Equal(200 - FeelRules.NumberOver, y + 20);
        var (xl, _) = FeelRules.NumberSpot(100, 200, 140, 300, 500, 60, 40);
        Assert.Equal(120 - FeelRules.NumberAside, xl);
        var (x2, y2) = FeelRules.NumberSpot(100, 200, 140, 300, 0, 60, 40, 2);
        Assert.Equal(120 + 2 * FeelRules.NumberAside, x2);
        Assert.Equal(200 - 2 * FeelRules.NumberOver, y2 + 20);
    }

    [Fact]
    public void KillDimWindow()
    {
        Assert.Equal(1f, FeelRules.KillDim(-1));
        Assert.Equal(0.3f, FeelRules.KillDim(0));
        Assert.Equal(0.3f, FeelRules.KillDim(16));
        Assert.Equal(1f, FeelRules.KillDim(22));
        float mid = FeelRules.KillDim(19);
        Assert.InRange(mid, 0.3001f, 0.9999f);
        Assert.Equal(1f, FeelRules.KillDim(23));
    }

    [Fact]
    public void LaunchRimHoldsThenFades()
    {
        Assert.Equal(1f, FeelRules.LaunchRim(0));
        Assert.Equal(1f, FeelRules.LaunchRim(12));
        Assert.Equal(0f, FeelRules.LaunchRim(18));
        float mid = FeelRules.LaunchRim(15);
        Assert.InRange(mid, 0.0001f, 0.9999f);
        Assert.Equal(0f, FeelRules.LaunchRim(-1));
    }

    [Fact]
    public void ReactRisesThenFalls()
    {
        Assert.Equal(0f, FeelRules.React(0));
        Assert.Equal(1f, FeelRules.React(0.04));
        Assert.Equal(0f, FeelRules.React(0.12));
        Assert.True(FeelRules.React(0.015) > 0 && FeelRules.React(0.015) < 1);
        Assert.True(FeelRules.React(0.02) < FeelRules.React(0.03));
        Assert.True(FeelRules.React(0.1) < FeelRules.React(0.07));
    }

    [Fact]
    public void TintedWindow()
    {
        Assert.False(FeelRules.Tinted(5));
        for (int n = 6; n <= 9; n++) Assert.True(FeelRules.Tinted(n));
        Assert.False(FeelRules.Tinted(10));
    }

    [Fact]
    public void TellDimsItsFillOnlyAndKeepsItsEdge()
    {
        float dim = FeelRules.KillDim(5);
        Assert.Equal(0.3f, FeelRules.TellFill(dim, 1.0f, false));
        Assert.True(FeelRules.TellEdge(dim, 1.0f, false) >= 0.6f);
        // outside the window nothing changes
        Assert.Equal(1f, FeelRules.TellFill(FeelRules.KillDim(40), 1.0f, false));
        Assert.Equal(1f, FeelRules.TellEdge(FeelRules.KillDim(40), 1.0f, false));
        // a standing wall (far from landing) dims as any tell
        Assert.Equal(0.3f, FeelRules.TellFill(dim, float.MaxValue, false));
    }

    [Fact]
    public void TellNeverDimsInItsLastThirdOfASecondNorAnyLane()
    {
        float dim = FeelRules.KillDim(5);
        Assert.Equal(1f, FeelRules.TellFill(dim, 0.3f, false));
        Assert.Equal(1f, FeelRules.TellEdge(dim, 0.1f, false));
        Assert.Equal(1f, FeelRules.TellFill(dim, 2f, true));
        Assert.Equal(1f, FeelRules.TellEdge(dim, 2f, true));
    }

    [Fact]
    public void AMassKillsLateBlowsJoinItsTotalForThreeFramesOnly()
    {
        Assert.False(FeelRules.MassTail(0));   // the mass step itself folds by Fold
        Assert.True(FeelRules.MassTail(1));
        Assert.True(FeelRules.MassTail(3));
        Assert.False(FeelRules.MassTail(4));
        Assert.False(FeelRules.MassTail(-1));
    }

    // F1 r6 (judge r5 fixes 1-3): the number path.

    static bool Clear((float X, float Y) p, float w, float h, FeelRules.Flight f) =>
        !FeelRules.CrossesFlight(p.X - w / 2, p.Y - h / 2, p.X + w / 2, p.Y + h / 2, f);

    [Fact]
    public void CrossesFlightSeesTheWholeThrowNotJustTheStart()
    {
        // a body at x 900..960, thrown 200 px right
        var f = new FeelRules.Flight(900, 500, 960, 600, 200, 0);
        Assert.True(FeelRules.CrossesFlight(1080, 540, 1120, 560, f));    // where it lands
        Assert.True(FeelRules.CrossesFlight(1000, 540, 1040, 560, f));    // on the way
        Assert.False(FeelRules.CrossesFlight(1000, 440, 1040, 490, f));   // over the path
        Assert.False(FeelRules.CrossesFlight(800, 540, 880, 560, f));     // behind it
        // diagonal: a box beside the hull's slanted edge but inside its bounding box is clear
        var d = new FeelRules.Flight(0, 0, 50, 50, 300, -300);
        Assert.False(FeelRules.CrossesFlight(0, -300, 40, -260, d));
        Assert.True(FeelRules.CrossesFlight(150, -150, 190, -110, d));
    }

    [Fact]
    public void ALaunchedNumberGoesAcrossTheThrowNeverAlongIt()
    {
        const float w = 120, h = 60;
        // judge r5 m4b: her at x 600, the body thrown away from her, up and right on screen
        var f = new FeelRules.Flight(900, 500, 960, 600, 260, -220);
        var old = FeelRules.NumberSpot(f.X0, f.Y0, f.X1, f.Y1, 600, w, h);
        Assert.False(Clear(old, w, h, f));   // the round 5 spot: the body flies in under it
        var p = FeelRules.NumberSpotLaunched(f, null, 600, w, h);
        Assert.True(Clear(p, w, h, f));
        Assert.True(p.X < 930);              // on the side it does not fly to
        Assert.True(p.Y + h / 2 <= f.Y0);    // still over its top
    }

    [Fact]
    public void AThrowUpTheScreenPutsTheNumberBesideItAwayFromHer()
    {
        const float w = 120, h = 60;
        var f = new FeelRules.Flight(900, 500, 960, 600, 0, -300);
        var right = FeelRules.NumberSpotLaunched(f, null, 600, w, h);
        Assert.True(Clear(right, w, h, f));
        Assert.True(right.X - w / 2 >= f.X1);
        var left = FeelRules.NumberSpotLaunched(f, null, 1400, w, h);
        Assert.True(Clear(left, w, h, f));
        Assert.True(left.X + w / 2 <= f.X0);
    }

    [Fact]
    public void ALaunchedNumberKeepsOffTheStepsOtherThrowsAndItsOwnRise()
    {
        const float w = 120, h = 60;
        var f = new FeelRules.Flight(900, 500, 960, 600, 300, 0);       // thrown right: the number goes over
        var p0 = FeelRules.NumberSpotLaunched(f, null, 600, w, h);
        var other = new FeelRules.Flight(p0.X - 30, p0.Y + 40, p0.X + 30, p0.Y + 140, 0, -120);   // flies up into that spot
        var p = FeelRules.NumberSpotLaunched(f, new[] { other }, 600, w, h, 1, 30);
        Assert.True(FeelRules.CrossesFlight(p0.X - w / 2, p0.Y - h / 2, p0.X + w / 2, p0.Y + h / 2, other));
        Assert.True(Clear(p, w, h, f) && Clear(p, w, h, other));
        Assert.True(Clear((p.X, p.Y - 30), w, h, f));                   // risen 30 px, still clear
        // the same at 4K: twice the px
        var f4 = new FeelRules.Flight(1800, 1000, 1920, 1200, 520, -440);
        var p4 = FeelRules.NumberSpotLaunched(f4, null, 1200, 2 * w, 2 * h, 2);
        Assert.True(Clear(p4, 2 * w, 2 * h, f4));
    }

    [Fact]
    public void ALaunchedNumberIsPlacedOffHerSoBesideHerLeavesItOverNoFlight()
    {
        // F1 lead 29, m4b: the spot clear of the flights lay on her body; BesideHer then pushed "432" ~90 px sideways,
        // blind to the flights, back over a rising body. Her rects go into the placement: BesideHer has nothing to move.
        const float w = 120, h = 60, rise = 30;
        var f = new FeelRules.Flight(900, 500, 960, 600, 260, -220);
        var p0 = FeelRules.NumberSpotLaunched(f, null, 600, w, h, 1, rise);
        var her = new HitsPlace.Box(p0.X - 70, p0.Y - 120, p0.X + 40, p0.Y + 260);
        float herX = (her.X0 + her.X1) / 2;
        Assert.NotEqual(0f, Nudge(p0, w, h, rise, herX, her));                 // lead 28's spot: on her, so nudged
        var keep = new[] { (her.X0 - HitsPlace.BodyGap, her.Y0 - HitsPlace.BodyGap, her.X1 + HitsPlace.BodyGap, her.Y1 + HitsPlace.BodyGap) };
        var p = FeelRules.NumberSpotLaunched(f, null, herX, w, h, 1, rise, keep);
        Assert.True(Clear(p, w, h, f) && Clear((p.X, p.Y - rise), w, h, f));
        Assert.Equal(0f, Nudge(p, w, h, rise, herX, her));                     // BesideHer leaves it where it is
    }

    [Fact]
    public void ALaunchedNumberTakesTheOtherSideWhenHerSideIsAllHer()
    {
        const float w = 120, h = 60;
        var f = new FeelRules.Flight(900, 500, 960, 600, 260, -220);          // the upper side is up and left
        var wall = new[] { (0f, 0f, 935f, 2000f) };                            // her and the strap fill all of it
        var p = FeelRules.NumberSpotLaunched(f, null, 600, w, h, 1, 0, wall);
        Assert.True(p.X - w / 2 - FeelRules.FlightGap >= 935);
        Assert.True(Clear(p, w, h, f));
    }

    static float Nudge((float X, float Y) p, float w, float h, float rise, float herX, HitsPlace.Box her) =>
        HitsPlace.HerNudge(new HitsPlace.Box(p.X - w / 2, p.Y - h / 2, p.X + w / 2, p.Y + h / 2), rise, herX, her, null, out _);

    [Fact]
    public void NumbersKeepOffTheHud()
    {
        const float w = 100, h = 60;
        // judge r5 m2b: "315" at (450, 935), its right end over the orb (left 470, top 945)
        var orb = (470f, 945f, 590f);
        float y = FeelRules.HudSafeY(437, 935, w, h, 1, null, orb);
        Assert.True(y + h / 2 <= 945 - FeelRules.HudGap);
        Assert.True(y <= FeelRules.NumberFloor);
        // no HUD part under it: only the floor
        Assert.Equal(FeelRules.NumberFloor, FeelRules.HudSafeY(200, 1000, w, h, 1));
        // over the hair's river (880): its box's bottom 8 over it
        Assert.Equal(880 - 8 - h / 2, FeelRules.HudSafeY(700, 870, w, h, 1, 880));
        // clear of it all: unchanged; scaled with the screen (1440: k 4/3)
        Assert.Equal(500f, FeelRules.HudSafeY(437, 500, w, h, 1, 880, orb));
        Assert.Equal(880 * 4f / 3, FeelRules.HudSafeY(200, 1400, w, h, 4f / 3), 0.01f);
        // beside the orb (past its gap): the orb does not lift it
        Assert.Equal(FeelRules.NumberFloor, FeelRules.HudSafeY(300, 900, w, h, 1, null, orb));
    }

    [Fact]
    public void AKillWindowClearsTheOlderNumbersNearItByNPlusThree()
    {
        Assert.True(FeelRules.KillClears(1100, 400, 960, 540));            // 198 px off
        Assert.False(FeelRules.KillClears(1300, 300, 960, 540));           // 416 px off
        Assert.True(FeelRules.KillClears(1300, 300, 960, 540, 2));         // the same at 4K is in reach
        Assert.Equal(1f, FeelRules.KillClear(-1));
        Assert.True(FeelRules.KillClear(0) < 0.6f);
        Assert.True(FeelRules.KillClear(1) < FeelRules.KillClear(0));
        Assert.True(FeelRules.KillClear(2) < FeelRules.KillClear(1));
        Assert.Equal(0f, FeelRules.KillClear(3));
        Assert.Equal(0f, FeelRules.KillClear(9));
    }

    [Fact]
    public void AKillWindowNeverClearsTheTotalOfTheKillThatOpensIt()
    {
        // F1 lead 30 (judge n fix 1): only numbers of earlier frames clear; the new total is born on the opening frame
        Assert.False(FeelRules.ClearsAtOpen(500, 500, 960, 500, 960, 540));     // the new total, right over the kill
        Assert.True(FeelRules.ClearsAtOpen(499, 500, 960, 500, 960, 540));      // an earlier step's number there
        Assert.False(FeelRules.ClearsAtOpen(499, 500, 1300, 300, 960, 540));    // an earlier one out of reach
    }

    static float GapToFelled((float X, float Y) p, float w, float h, (float X0, float Y0, float X1, float Y1) f) =>
        FeelRules.BoxGap(p.X - w / 2, p.Y - h / 2, p.X + w / 2, p.Y + h / 2, f.X0, f.Y0, f.X1, f.Y1);

    [Fact]
    public void AMassTotalStandsOverItsFelledWhenNothingIsInTheWay()
    {
        const float w = 130, h = 60;
        var felled = (530f, 160f, 830f, 400f);                                  // judge n m4: the five felled
        var bodies = new[] { new FeelRules.Flight(530, 160, 640, 300, 0, 0), new FeelRules.Flight(700, 250, 830, 400, 0, 0) };
        var p = FeelRules.MassTotalSpot(felled, bodies, 1100, w, h, 1, 30);
        Assert.Equal(FeelRules.NumberSpot(530, 160, 830, 400, 1100, w, h), p);   // NumberOver over the box, away from her
        Assert.Equal(FeelRules.NumberOver, GapToFelled(p, w, h, felled), 0.01f);
        Assert.Equal(0, FeelRules.FlightsCrossed(p.X, p.Y, w, h, bodies, 1, 30));
    }

    [Fact]
    public void AMassTotalIsNotCarriedOffItsKillByAFanOfThrows()
    {
        // judge n m5b: eight felled thrown up-left in a fan; the across-the-throw search took "501" ~250 px up the frame
        const float w = 110, h = 50, rise = 30;
        var felled = (600f, 380f, 900f, 580f);
        var fan = new FeelRules.Flight[8];
        for (int i = 0; i < 8; i++)
        {
            float x = 600 + i * 37, y = 380 + (i % 3) * 60;
            fan[i] = new FeelRules.Flight(x, y, x + 60, y + 110, -140 - i * 15, -150 + i * 10);
        }
        var p = FeelRules.MassTotalSpot(felled, fan, 1200, w, h, 1, rise);
        Assert.True(GapToFelled(p, w, h, felled) <= FeelRules.MassReach);
        // the fewest crossed of every spot in reach on its 10 px grid (laid from the preferred spot)
        var pref = FeelRules.NumberSpot(600, 380, 900, 580, 1200, w, h);
        int got = FeelRules.FlightsCrossed(p.X, p.Y, w, h, fan, 1, rise);
        for (int iy = -40; iy <= 40; iy++)
            for (int ix = -40; ix <= 40; ix++)
            {
                float x = pref.X + ix * 10, y = pref.Y + iy * 10;
                if (GapToFelled((x, y), w, h, felled) <= FeelRules.MassReach)
                    Assert.True(got <= FeelRules.FlightsCrossed(x, y, w, h, fan, 1, rise));
            }
    }

    [Fact]
    public void AMassTotalKeepsOffHerAndInsideTheScreenStillByItsKill()
    {
        const float w = 120, h = 60;
        var felled = (900f, 300f, 1100f, 450f);
        var pref = FeelRules.NumberSpot(900, 300, 1100, 450, 700, w, h);
        var her = new[] { (pref.X - 120, pref.Y - 80, pref.X + 80, 1000f) };    // her body over the preferred spot
        var p = FeelRules.MassTotalSpot(felled, null, 700, w, h, 1, 20, her);
        Assert.True(GapToFelled(p, w, h, felled) <= FeelRules.MassReach);
        Assert.True(p.X - w / 2 - FeelRules.FlightGap >= her[0].Item3 || p.Y + h / 2 + FeelRules.FlightGap <= her[0].Item2
            || p.X + w / 2 + FeelRules.FlightGap <= her[0].Item1);
        // felled at the top of the screen: the total stays under the top band, beside its kill, not lifted off it
        var high = (900f, 90f, 1100f, 250f);
        var q = FeelRules.MassTotalSpot(high, null, 700, w, h, 1, 20, null, (0f, 118f, 1920f, 1000f));
        Assert.True(q.Y - h / 2 - 20 >= 118);
        Assert.True(GapToFelled(q, w, h, high) <= FeelRules.MassReach);
        // at 4K the reach doubles with the px
        var f4 = (1800f, 600f, 2200f, 900f);
        var p4 = FeelRules.MassTotalSpot(f4, null, 1400, 2 * w, 2 * h, 2);
        Assert.Equal(2 * FeelRules.NumberOver, GapToFelled(p4, 2 * w, 2 * h, f4), 0.01f);
    }
}
