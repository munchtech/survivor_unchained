using SurvivorUnchained.View;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A1: a released cut that ends off the stance fades to the idle over the sim's Recover (PlayerView.OnSwingRelease).</summary>
public class SwingRecoverTests
{
    const double Recover = 18 / 60.0 / 1.0;   // Sunder's recover at rate 1: 0.30 s

    [Fact]
    public void A_released_cut_A_reaches_the_idle_within_the_recover_and_a_frame()
    {
        Assert.Equal(Recover, SwingRecover.Fade("sunder_cut_a", Recover));
        Assert.Equal(1.0, SwingRecover.IdleWeight(Recover + 1 / 60.0, Recover));
        Assert.InRange(SwingRecover.IdleWeight(Recover / 2, Recover), 0.49, 0.51);
        Assert.Equal(0.0, SwingRecover.IdleWeight(0, Recover));
    }

    [Fact]
    public void A_released_cut_B_keeps_the_usual_fade()
    {
        Assert.Null(SwingRecover.Fade("sunder_cut_b", Recover));
        Assert.Null(SwingRecover.Fade("sword_heavy", Recover));
        Assert.Null(SwingRecover.Fade(null, Recover));
    }

    [Fact]
    public void Sunder_cycles_cut_A_then_B_and_a_held_chain_tells_no_release()
    {
        // (a held chain tells no Ev.SwingRelease, asserted in SwingChainTests' held test: the view fades only in OnSwingRelease)
        var press = SurvivorUnchained.Content.Weapons.All["sunder"].Press!;
        Assert.Equal(new[] { "sunder_cut_a", "sunder_cut_b" }, press.Clip);
        Assert.False(SwingRecover.EndsOnStance(press.Clip![0]));
        Assert.True(SwingRecover.EndsOnStance(press.Clip[1]));
    }
}
