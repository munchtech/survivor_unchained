using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M4 (docs/design/M4_HUD.md §4): the level card's kind, words, flag and clock (src/Ui/LevelCardModel.cs).</summary>
public sealed class LevelCardTests
{
    static TaughtBuild Warden => TaughtBuilds.Of("warden")!;

    [Fact]
    public void A_level_that_teaches_a_carried_skill_is_a_new_key()
    {
        var s = LevelCards.ForCampaignLevel(4, Warden, id => id == "heroic_leap" ? 2 : -1, 0);
        Assert.Equal(LevelCardKind.NewKey, s.Kind);
        Assert.Equal("heroic_leap", s.Skill);
        Assert.Equal(2, s.Slot);
        Assert.Equal("LEVEL 4 · A NEW KEY", LevelCards.Header(s));
        Assert.Equal(Act.Character, s.PromptKey);
        Assert.Equal("Attribute points to spend", s.PromptText);
    }

    [Fact]
    public void A_level_without_a_new_key_or_with_it_not_carried_is_plain()
    {
        var none = LevelCards.ForCampaignLevel(3, Warden, _ => 1, 1);
        Assert.Equal(LevelCardKind.Plain, none.Kind);
        Assert.Equal("LEVEL 3", LevelCards.Header(none));
        Assert.Equal("A new trait can be chosen", none.PromptText);
        var notCarried = LevelCards.ForCampaignLevel(4, Warden, _ => -1, 0);
        Assert.Equal(LevelCardKind.Plain, notCarried.Kind);
        Assert.Equal(LevelCardKind.Plain, LevelCards.ForCampaignLevel(4, null, _ => 0, 0).Kind);
    }

    [Fact]
    public void The_flag_parses_its_three_kinds()
    {
        var k = LevelCards.Parse("slot:heroic_leap:4")!.Value;
        Assert.Equal(LevelCardKind.NewKey, k.Spec.Kind);
        Assert.Equal(1.5, k.At);
        var l = LevelCards.Parse("lamp:sunder:6:42:47@2.5")!.Value;
        Assert.Equal(LevelCardKind.LampLit, l.Spec.Kind);
        Assert.Equal((42.0, 47.0, 6, 2.5), (l.Spec.Before, l.Spec.After, l.Spec.Level, l.At));
        Assert.Equal("LEVEL 6 · A LAMP LIT", LevelCards.Header(l.Spec));
        Assert.Equal(LevelCardKind.Plain, LevelCards.Parse("plain:5")!.Value.Spec.Kind);
        Assert.Null(LevelCards.Parse("slot:x"));
        Assert.Null(LevelCards.Parse("lamp:sunder:6:a:47"));
    }

    [Fact]
    public void The_callings_skill_takes_a_plain_levels_card_and_keeps_its_level()
    {
        var card = LevelCards.ForCampaignLevel(6, Warden, _ => 1, 0);
        Assert.Equal(LevelCardKind.Plain, card.Kind);
        Assert.Null(LevelCards.WithCalling(card, "dawnpulse"));
        Assert.Equal(LevelCardKind.NewSkill, card.Kind);
        Assert.Equal("dawnpulse", card.Skill);
        Assert.Equal(6, card.Level);
        Assert.Equal("LEVEL 6 · A NEW SKILL", LevelCards.Header(card));
        // (it is on no key: no slot to fold to, and its prompt names the skills screen)
        Assert.Equal(-1, card.Slot);
        Assert.Equal(Act.Arts, card.PromptKey);
        Assert.Equal("Put it on a key", card.PromptText);
    }

    [Fact]
    public void The_callings_skill_follows_a_key_levels_card_on_its_own_card_without_the_level()
    {
        var card = LevelCards.ForCampaignLevel(9, Warden, id => id == "watch_bell" ? 5 : -1, 0);
        Assert.Equal(LevelCardKind.NewKey, card.Kind);
        var second = LevelCards.WithCalling(card, "dawnpulse");
        // the key card shows as it did
        Assert.Equal((LevelCardKind.NewKey, "watch_bell", 5), (card.Kind, card.Skill, card.Slot));
        Assert.Equal("LEVEL 9 · A NEW KEY", LevelCards.Header(card));
        Assert.Equal(Act.Character, card.PromptKey);
        // and the new skill's own card follows it
        Assert.NotNull(second);
        Assert.Equal((LevelCardKind.NewSkill, "dawnpulse", -1), (second!.Kind, second.Skill, second.Slot));
        Assert.Equal("A NEW SKILL", LevelCards.Header(second));
        Assert.DoesNotContain("LEVEL", LevelCards.Header(second));
        Assert.Equal(Act.Arts, second.PromptKey);
        Assert.Equal("Put it on a key", second.PromptText);
        // one after the other from the same queue
        var q = new LevelCardQueue();
        q.Add(card); q.Add(second);
        q.Tick(1 / 60.0, false);
        Assert.Same(card, q.Current);
        Run(q, LevelCards.In + LevelCards.HoldPrompt + LevelCards.Out + 0.1);
        Assert.Same(second, q.Current);
    }

    [Fact]
    public void The_flag_parses_a_new_skill()
    {
        var k = LevelCards.Parse("skill:dawnpulse:6@2")!.Value;
        Assert.Equal((LevelCardKind.NewSkill, "dawnpulse", 6, 2.0), (k.Spec.Kind, k.Spec.Skill, k.Spec.Level, k.At));
        Assert.Equal("LEVEL 6 · A NEW SKILL", LevelCards.Header(k.Spec));
        Assert.Equal(Act.Arts, k.Spec.PromptKey);
        Assert.True(k.Spec.HasPrompt);
        Assert.Null(LevelCards.Parse("skill:dawnpulse"));
        Assert.Null(LevelCards.Parse("skill:dawnpulse:x"));
    }

    [Fact]
    public void The_line_is_one_short_clause()
    {
        Assert.Equal("You leap where you aim, untouchable in the air",
            LevelCards.Line("You leap where you aim, untouchable in the air, and come down blade first: everything in the ring is struck."));
        Assert.Equal("A heavy, wide chop that sweeps the whole front of you", LevelCards.Line("A heavy, wide chop that sweeps the whole front of you. Opens wounds."));
        Assert.Equal("You plant your feet and swear it", LevelCards.Line("You plant your feet and swear it: for 2 s every blow on you lands at half."));
        Assert.Equal("42", LevelCards.Num(42.0));
        Assert.Equal("4.5", LevelCards.Num(4.5));
    }

    static void Run(LevelCardQueue q, double secs, bool held = false)
    {
        for (double t = 0; t < secs; t += 1 / 60.0) q.Tick(1 / 60.0, held);
    }

    [Fact]
    public void The_clock_runs_in_hold_out_and_holds_longer_with_a_prompt()
    {
        var q = new LevelCardQueue();
        q.Add(new LevelCardSpec { Level = 2 });
        q.Tick(1 / 60.0, false);
        Assert.True(q.Began);
        Assert.Equal(LevelCardQueue.Phase.In, q.Now);
        Run(q, 0.2);
        Assert.Equal(LevelCardQueue.Phase.Hold, q.Now);
        Run(q, 2.15);
        Assert.Equal(LevelCardQueue.Phase.Out, q.Now);
        Run(q, 0.35);
        Assert.Null(q.Current);

        q.Add(new LevelCardSpec { Level = 3, PromptKey = Act.Character, PromptText = "Attribute points to spend" });
        q.Tick(1 / 60.0, false);
        Run(q, 0.2 + 2.6);
        Assert.Equal(LevelCardQueue.Phase.Hold, q.Now);
        Run(q, 0.5);
        Assert.Equal(LevelCardQueue.Phase.Out, q.Now);
    }

    [Fact]
    public void Cards_wait_while_held_and_show_one_at_a_time()
    {
        var q = new LevelCardQueue();
        q.Add(new LevelCardSpec { Level = 4 });
        q.Add(new LevelCardSpec { Level = 5 });
        Run(q, 5, held: true);
        Assert.Null(q.Current);
        Assert.Equal(2, q.Count);
        Run(q, 1);
        Assert.Equal(4, q.Current!.Level);
        // a hold mid-card pauses it
        double t = q.T;
        Run(q, 3, held: true);
        Assert.Equal(t, q.T);
        Run(q, 2.0);
        Assert.Equal(5, q.Current!.Level);
    }
}
