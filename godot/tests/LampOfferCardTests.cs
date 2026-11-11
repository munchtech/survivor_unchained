using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M7a section D: the level-up card offers the lamp (live wick text, the blow before and after), lights, and clears.</summary>
public class LampOfferCardTests
{
    static Journey Warden()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 7);
    }

    [Fact]
    public void A_held_sunder_point_makes_an_offer_with_the_live_lamp_text_and_the_blow()
    {
        var j = Warden();
        var card = LevelCards.ForCampaignLevel(2, null, _ => -1, 0, j.Ch);
        var m = WickBook.LampMeasure(j.Ch, "sunder", "sunder.stroke.1");
        Assert.Equal(LevelCardKind.LampLit, card.Kind);
        Assert.True(card.Offer);
        Assert.Equal("sunder", card.Skill);
        Assert.Equal("LEVEL 2 · A LAMP TO LIGHT", LevelCards.Header(card));
        Assert.Equal(Act.Lamps, card.PromptKey);
        Assert.Equal("Light: " + Wicks.Text("sunder", "sunder.stroke.1"), card.PromptText);
        Assert.DoesNotContain("Third Blow", card.PromptText);
        Assert.Equal((m.Measure, m.Before, m.After), (card.Measure, card.Before, card.After));
        Assert.Equal("a blow", card.Measure);
    }

    [Fact]
    public void A_new_key_card_stays_and_a_level_with_nothing_held_makes_no_offer()
    {
        var j = Warden();
        foreach (var (id, _) in SkillBook.Carried(j.Ch).ToList()) WickBook.Light(j.Ch, id);
        var plain = LevelCards.ForCampaignLevel(2, null, _ => -1, 1, j.Ch);
        Assert.Equal(LevelCardKind.Plain, plain.Kind);
        Assert.False(plain.Offer);
        Assert.Equal(Act.Character, plain.PromptKey);
        Assert.Null(LevelCards.LampOffer(j.Ch, 2));
    }

    [Fact]
    public void Lighting_turns_the_offer_lit_and_clears_the_prompt()
    {
        var j = Warden();
        var card = LevelCards.LampOffer(j.Ch, 2)!;
        Assert.Equal("sunder.stroke.1", WickBook.Light(j.Ch, "sunder"));
        LevelCards.Lit(card);
        Assert.False(card.Offer);
        Assert.False(card.HasPrompt);
        Assert.Equal("LEVEL 2 · A LAMP LIT", LevelCards.Header(card));
    }

    [Fact]
    public void The_flag_parses_an_offer()
    {
        var (s, _) = LevelCards.Parse("offer:sunder:2:40:44@1")!.Value;
        Assert.True(s.Offer);
        Assert.Equal((LevelCardKind.LampLit, "sunder", 2, 40.0, 44.0), (s.Kind, s.Skill, s.Level, s.Before, s.After));
        Assert.Equal(Act.Lamps, s.PromptKey);
    }
}
