using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>bd-ui W7: the key seats' pure rules.</summary>
public class SeatLookTests
{
    [Theory]
    [InlineData(0, 1)]
    [InlineData(1, 4)]
    [InlineData(2, 5)]
    [InlineData(3, 9)]
    public void A_locked_key_opens_at_the_first_level_that_has_it(int slot, int level) => Assert.Equal(level, SeatLook.OpensAt(slot, 4));

    [Theory]
    [InlineData(1.0, 0f)]
    [InlineData(0.75, 0.25f)]
    [InlineData(0.0, 1f)]
    [InlineData(-1.0, 1f)]
    [InlineData(2.0, 0f)]
    public void The_wipe_covers_the_share_not_ready(double ready, float share) => Assert.Equal((double)share, (double)SeatLook.WipeShare(ready), 4);

    [Fact]
    public void Desaturate_keeps_luma_and_pulls_chroma()
    {
        var (r, g, b) = SeatLook.Desaturate(1f, 0f, 0f, 0.6f);
        Assert.Equal((double)(0.2126f + 0.7874f * 0.6f), (double)r, 4);
        Assert.Equal((double)(0.2126f * 0.4f), (double)g, 4);
        var (r1, g1, b1) = SeatLook.Desaturate(0.3f, 0.5f, 0.7f, 1f);
        Assert.Equal((0.3f, 0.5f, 0.7f), (r1, g1, b1));
        var (r0, g0, b0) = SeatLook.Desaturate(0.3f, 0.5f, 0.7f, 0f);
        Assert.Equal((double)r0, (double)g0, 4); Assert.Equal((double)g0, (double)b0, 4);
    }
}
