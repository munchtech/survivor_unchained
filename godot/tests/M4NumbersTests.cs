using SurvivorUnchained.Ui;
using SurvivorUnchained.View;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M4 lead 6: where a damage number may start (clear of the strap under her for its first 0.3 s), and the
/// level card's dev spec taking a key card and the new skill's card that follows it.</summary>
public class M4NumbersTests
{
    // the strap under her: 96 x 28 at (912, 560)
    const float Sx0 = 912, Sy0 = 560, Sx1 = 1008, Sy1 = 588;

    static float Nudge(float x0, float y0, float x1, float y1, float rise = 30) =>
        HitsPlace.StrapNudge(x0, y0, x1, y1, rise, Sx0, Sy0, Sx1, Sy1);

    [Fact]
    public void A_number_clear_of_the_strap_stays()
    {
        Assert.Equal(0, Nudge(700, 550, 780, 590));          // well to its left
        Assert.Equal(0, Nudge(1020, 550, 1100, 590));        // to its right, past the gap
        Assert.Equal(0, Nudge(930, 480, 990, 520));          // above it, lifting away
        Assert.Equal(0, Nudge(930, 640, 990, 680, rise: 30)); // under it, and 0.3 s of lift does not reach it
    }

    [Fact]
    public void A_number_on_the_strap_starts_beside_it_on_its_own_side()
    {
        float dx = Nudge(880, 555, 960, 595);                 // its middle (920) left of the strap's (960)
        Assert.True(dx < 0);
        Assert.Equal((double)(Sx0 - HitsPlace.StrapGap), 960 + dx, 3);  // its right edge a gap short of the strap
        dx = Nudge(970, 555, 1050, 595);
        Assert.True(dx > 0);
        Assert.Equal((double)(Sx1 + HitsPlace.StrapGap), 970 + dx, 3);
        Assert.True(Nudge(920, 555, 1000, 595) > 0);          // dead centre: to the right, where numbers are lifted
        Assert.Equal(0, Nudge(880 + Nudge(880, 555, 960, 595), 555, 960 + Nudge(880, 555, 960, 595), 595)); // and then it is clear
    }

    [Fact]
    public void A_number_that_would_lift_into_the_strap_in_its_first_third_of_a_second_is_moved_too()
    {
        Assert.Equal(0, Nudge(930, 610, 990, 650, rise: 10));
        Assert.NotEqual(0, Nudge(930, 610, 990, 650, rise: 30));
        // the lift itself: nothing at birth, 0.336 m at 0.3 s, all of it (0.525 m) by the end of its life
        Assert.Equal(0, HitsPlace.RiseIn(0), 6);
        Assert.Equal(0.336, HitsPlace.RiseIn(0.3), 6);
        Assert.Equal(0.525, HitsPlace.RiseIn(0.75), 6);
        Assert.Equal(0.525, HitsPlace.RiseIn(5), 6);
    }

    [Fact]
    public void The_level_cards_spec_takes_a_key_card_and_the_skill_card_that_follows()
    {
        var two = LevelCards.ParseAll("slot:heroic_leap:9@1.5+skill:dawnpulse")!;
        Assert.Equal(2, two.Count);
        Assert.Equal("LEVEL 9 · A NEW KEY", LevelCards.Header(two[0].Spec));
        Assert.Equal("A NEW SKILL", LevelCards.Header(two[1].Spec));
        Assert.Equal(0, two[1].Spec.Level);
        Assert.Equal(LevelCards.SkillPrompt, two[1].Spec.PromptText);
        Assert.Equal(1.5, two[1].At);                         // no @T of its own: at the first one's time
        Assert.Equal(2.5, LevelCards.ParseAll("plain:5@1+skill:dawnpulse@2.5")![1].At);
        Assert.Single(LevelCards.ParseAll("skill:dawnpulse:6@1.5")!);
        Assert.Null(LevelCards.ParseAll("slot:heroic_leap:9+nonsense"));
        Assert.Null(LevelCards.ParseAll("skill:dawnpulse"));  // a card with no level follows another, never alone
    }
}
