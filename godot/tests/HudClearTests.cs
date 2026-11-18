using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class HudClearTests
{
    static HudClear.Box B(float x0, float y0, float x1, float y1) => new(x0, y0, x1, y1);

    [Fact]
    public void ClearNumberIsNotMoved()
    {
        var (dx, dy) = HudClear.Shift(B(0, 0, 50, 30), [B(200, 200, 300, 260)]);
        Assert.Equal(0, dx); Assert.Equal(0, dy);
    }

    [Fact]
    public void NumberOnTextEndsTwelveClear()
    {
        var card = B(860, 190, 925, 215);
        var num = B(870, 195, 930, 225);
        var (dx, dy) = HudClear.Shift(num, [card]);
        var m = num.Moved(dx, dy);
        Assert.False(m.Hits(card, HudClear.Gap - 0.01f));
        Assert.True(dy <= 0);
    }

    [Fact]
    public void ShiftsUpWhenThatIsShortest()
    {
        var (dx, dy) = HudClear.Shift(B(100, 100, 200, 130), [B(0, 110, 1000, 140)]);
        Assert.Equal(0, dx);
        Assert.Equal(-(130 - (110 - 12)), dy, 0.01f);
    }

    [Fact]
    public void ShiftsSidewaysWhenThatIsShorter()
    {
        var (dx, dy) = HudClear.Shift(B(990, 100, 1040, 400), [B(0, 0, 1000, 500)]);
        Assert.Equal(0, dy);
        Assert.Equal(1012 - 990, dx, 0.01f);
    }

    [Fact]
    public void TwoCardsBothCleared()
    {
        var cards = new[] { B(100, 100, 300, 140), B(100, 40, 300, 80) };
        var num = B(150, 105, 200, 135);
        var (dx, dy) = HudClear.Shift(num, cards);
        var m = num.Moved(dx, dy);
        foreach (var c in cards) Assert.False(m.Hits(c, 11.99f));
    }

    [Fact]
    public void TipWaitsTwoSecondsOfQuiet()
    {
        Assert.True(HudClear.TipWaits(10, 9, false));
        Assert.True(HudClear.TipWaits(11.9, 10, false));
        Assert.False(HudClear.TipWaits(12, 10, false));
        Assert.False(HudClear.TipWaits(5, double.NegativeInfinity, false));
    }

    [Fact]
    public void TipAlreadyShowingStays()
    {
        Assert.False(HudClear.TipWaits(10, 9.9, true));
    }
}
