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
    public void A_crit_is_at_least_135_percent_of_the_largest_normal_number_at_every_size()
    {
        Assert.Equal(58, HitsPlace.NormalMost);
        foreach (bool heavy in new[] { false, true })
        {
            Assert.True(HitsPlace.NumberSize(false, heavy) <= HitsPlace.NormalMost);
            foreach (bool critHeavy in new[] { false, true })
                Assert.True(HitsPlace.NumberSize(true, critHeavy) >= HitsPlace.CritOverNormal * HitsPlace.NumberSize(false, heavy));
        }
        Assert.True(HitsPlace.NumberSize(true, false) >= HitsPlace.CritOverNormal * HitsPlace.NormalMost);
    }

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

    // her body at the play camera: 56 x 85 over her feet at (960, 573); the strap under her is wider than she is
    static readonly HitsPlace.Box Body = new(932, 488, 988, 573), Strap = new(Sx0, Sy0, Sx1, Sy1);
    const float HerX = 960;

    static float Her(float x0, float y0, float x1, float y1, out int hit, float rise = 30, bool body = true, bool strap = true) =>
        HitsPlace.HerNudge(new(x0, y0, x1, y1), rise, HerX, body ? Body : null, strap ? Strap : null, out hit);

    /// <summary>The number's box, moved, touches neither her body nor the strap (their gaps and its rise counted).</summary>
    static void AssertClearOfHer(float x0, float y0, float x1, float y1, float dx, float rise = 30)
    {
        Assert.Equal(0, Her(x0 + dx, y0, x1 + dx, y1, out int hit, rise));
        Assert.Equal(0, hit);
        Assert.Equal(0, HitsPlace.StrapNudge(x0 + dx, y0, x1 + dx, y1, rise, Sx0, Sy0, Sx1, Sy1));
        Assert.Equal(0, HitsPlace.StrapNudge(x0 + dx, y0, x1 + dx, y1, rise, Body.X0, Body.Y0, Body.X1, Body.Y1, HitsPlace.BodyGap));
    }

    [Fact]
    public void A_number_dead_centre_on_her_goes_right_and_ends_clear_of_her_body_and_strap()
    {
        float dx = Her(930, 510, 990, 540, out int hit);      // on her torso, its middle on her centre line
        Assert.Equal(HitsPlace.HitBody, hit);
        Assert.Equal((double)(Body.X1 + HitsPlace.BodyGap), 930 + dx, 3);   // its left edge a gap right of her
        AssertClearOfHer(930, 510, 990, 540, dx);
        // on her head and on her legs alike
        Assert.True(Her(940, 490, 980, 505, out _) > 0);
        Assert.True(Her(940, 540, 980, 552, out _, rise: 0) > 0);
    }

    [Fact]
    public void A_number_left_of_her_centre_line_goes_left_one_right_of_it_goes_right()
    {
        float dx = Her(900, 510, 950, 540, out int hit);      // its middle (925) left of her (960)
        Assert.Equal(HitsPlace.HitBody, hit);
        Assert.Equal((double)(Body.X0 - HitsPlace.BodyGap), 950 + dx, 3);
        AssertClearOfHer(900, 510, 950, 540, dx);
        dx = Her(965, 510, 1015, 540, out _);                 // 990: right
        Assert.Equal((double)(Body.X1 + HitsPlace.BodyGap), 965 + dx, 3);
        // the side is told by HER centre line, not the rect's it is on: a wide number over the strap's left end
        // whose middle is right of her goes right, past all of the strap
        dx = Her(905, 565, 1025, 600, out hit);               // middle 965
        Assert.Equal(HitsPlace.HitBody | HitsPlace.HitStrap, hit);
        Assert.Equal((double)(Sx1 + HitsPlace.StrapGap), 905 + dx, 3);
    }

    [Fact]
    public void A_number_already_clear_of_her_is_not_moved()
    {
        Assert.Equal(0, Her(1020, 500, 1080, 530, out int hit));   // beside her, past her gap and the strap's
        Assert.Equal(0, hit);
        Assert.Equal(0, Her(840, 500, 900, 530, out _));           // to her left
        Assert.Equal(0, Her(930, 440, 990, 470, out _));           // over her head, lifting away
        Assert.Equal(0, Her(993, 500, 1053, 530, out _));          // a gap and a px right of her body, above the strap
        Assert.NotEqual(0, Her(990, 500, 1050, 530, out _));       // inside her gap: moved
    }

    [Fact]
    public void A_number_moved_off_her_body_that_would_land_on_the_strap_clears_both()
    {
        // right: off her body alone it would stand at 992..1052, on the strap's right end (to 1008)
        float dx = Her(940, 530, 1000, 570, out int hit);
        Assert.Equal(HitsPlace.HitBody | HitsPlace.HitStrap, hit);
        Assert.Equal((double)(Sx1 + HitsPlace.StrapGap), 940 + dx, 3);
        AssertClearOfHer(940, 530, 1000, 570, dx);
        // left: off her body alone at 868..928, on the strap's left end (from 912)
        dx = Her(920, 530, 980, 570, out hit);
        Assert.Equal(HitsPlace.HitBody | HitsPlace.HitStrap, hit);
        Assert.Equal((double)(Sx0 - HitsPlace.StrapGap), 980 + dx, 3);
        AssertClearOfHer(920, 530, 980, 570, dx);
        // a body wider than the strap (a close camera): past her, which is past the strap too
        var wide = new HitsPlace.Box(880, 300, 1040, 573);
        dx = HitsPlace.HerNudge(new(970, 565, 1030, 600), 0, HerX, wide, Strap, out hit);
        Assert.Equal((double)(wide.X1 + HitsPlace.BodyGap), 970 + dx, 3);
        // and the other way round: on the strap alone, and off it it would land on a body that stands past the strap's end
        var aside = new HitsPlace.Box(1000, 300, 1060, 573);
        dx = HitsPlace.HerNudge(new(920, 565, 980, 600), 0, 940, aside, Strap, out hit);
        Assert.Equal(HitsPlace.HitBody | HitsPlace.HitStrap, hit);
        Assert.Equal((double)(aside.X1 + HitsPlace.BodyGap), 920 + dx, 3);
    }

    [Fact]
    public void A_numbers_rise_into_her_is_counted_and_her_body_is_kept_clear_with_the_strap_hidden()
    {
        // under the strap: 10 px of lift does not reach it, 30 does
        Assert.Equal(0, Her(930, 610, 990, 650, out _, rise: 10));
        Assert.NotEqual(0, Her(930, 610, 990, 650, out int hit, rise: 30));
        Assert.Equal(HitsPlace.HitStrap, hit);
        // the strap hidden: under her feet, 10 px does not reach her body, 30 does; and on her it is moved all the same
        Assert.Equal(0, Her(930, 600, 990, 630, out _, rise: 10, strap: false));
        Assert.NotEqual(0, Her(930, 600, 990, 630, out hit, rise: 30, strap: false));
        Assert.Equal(HitsPlace.HitBody, hit);
        Assert.Equal((double)(Body.X1 + HitsPlace.BodyGap), 930 + Her(930, 510, 990, 540, out _, strap: false), 3);
        // without her (a tool's scene) it is the strap's rule as it was
        Assert.Equal(HitsPlace.StrapNudge(970, 555, 1050, 595, 30, Sx0, Sy0, Sx1, Sy1), Her(970, 555, 1050, 595, out hit, body: false));
        Assert.Equal(HitsPlace.HitStrap, hit);
        Assert.Equal(0, Her(930, 510, 990, 540, out _, body: false, strap: false));
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
