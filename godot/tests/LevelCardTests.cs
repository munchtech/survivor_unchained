using System;
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
    public void The_keys_open_at_4_5_and_9_and_the_autos_at_7_and_10_say_so()
    {
        static int SlotOf(string id) => id switch { "heroic_leap" => 1, "bladestorm" => 2, "shield_charge" => 3, "iron_vow" => 5, "watch_bell" => 6, _ => -1 };
        foreach (var l in new[] { 4, 5, 9 }) Assert.Equal(LevelCardKind.NewKey, LevelCards.ForCampaignLevel(l, Warden, SlotOf, 0).Kind);
        var auto = LevelCards.ForCampaignLevel(7, Warden, SlotOf, 0);
        Assert.Equal((LevelCardKind.NewAuto, "iron_vow", 5), (auto.Kind, auto.Skill, auto.Slot));
        Assert.Equal("LEVEL 7 · AN AUTO SKILL", LevelCards.Header(auto));
        Assert.Equal(LevelCardKind.NewAuto, LevelCards.ForCampaignLevel(10, Warden, SlotOf, 0).Kind);
    }

    [Fact]
    public void Level_8_is_the_second_weapon_with_the_swap_key()
    {
        var s = LevelCards.ForCampaignLevel(8, Warden, _ => -1, 0);
        Assert.Equal(LevelCardKind.NewStance, s.Kind);
        Assert.Equal("LEVEL 8 · A SECOND WEAPON", LevelCards.Header(s));
        Assert.Equal("Bulwark", s.Skill);
        Assert.False(string.IsNullOrEmpty(s.Line));
        Assert.Equal(Act.Character, s.PromptKey);
        // the dev specs: slot:ID:LEVEL:SLOT with SLOT 4+ is an auto card, "stance" is the second weapon's
        Assert.Equal(LevelCardKind.NewAuto, LevelCards.Parse("slot:iron_vow:7:5@1.5")!.Value.Spec.Kind);
        Assert.Equal(LevelCardKind.NewKey, LevelCards.Parse("slot:heroic_leap:4:1")!.Value.Spec.Kind);
        var st = LevelCards.Parse("stance@1.5")!.Value;
        Assert.Equal((LevelCardKind.NewStance, 1.5), (st.Spec.Kind, st.At));
        Assert.Null(LevelCards.Parse("stance:nope"));
    }

    [Fact]
    public void A_level_without_a_new_key_or_with_it_not_carried_is_plain()
    {
        var none = LevelCards.ForCampaignLevel(3, Warden, _ => 1, 1);
        Assert.Equal(LevelCardKind.Plain, none.Kind);
        Assert.Equal("LEVEL 3", LevelCards.Header(none));
        Assert.Equal("Choose a new trait", none.PromptText);
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
        // (bd-keys; bd-sockets) the ninth level opens the fourth key, Shield Charge's (taught_builds.json)
        var card = LevelCards.ForCampaignLevel(9, Warden, id => id == "shield_charge" ? 3 : -1, 0);
        Assert.Equal(LevelCardKind.NewKey, card.Kind);
        var second = LevelCards.WithCalling(card, "judgement_disc");
        // the key card shows as it did
        Assert.Equal((LevelCardKind.NewKey, "shield_charge", 3), (card.Kind, card.Skill, card.Slot));
        Assert.Equal("LEVEL 9 · A NEW KEY", LevelCards.Header(card));
        Assert.Equal(Act.Character, card.PromptKey);
        // and the new skill's own card follows it
        Assert.NotNull(second);
        Assert.Equal((LevelCardKind.NewSkill, "judgement_disc", -1), (second!.Kind, second.Skill, second.Slot));
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

/// <summary>bd-ui W6: the card's placement over the tile row, its tail on what opened, and its chip matching the bar's seat.</summary>
public sealed class LevelCardPlaceTests
{
    [Fact]
    public void The_card_stays_eight_above_the_status_shelf_in_the_campaign_and_is_unchanged_in_the_arena()
    {
        var camp = LevelCardPlace.Compute(247, 86, 978, 959, null);
        Assert.True(camp.Y + 86 <= 959 - 8);
        var arena = LevelCardPlace.Compute(247, 86, 978, null, null);
        Assert.Equal(978.0 - 86, arena.Y);
        Assert.InRange(arena.X, 836f, 837f);
    }

    [Theory]
    [InlineData(760f)] [InlineData(820f)] [InlineData(960f)] [InlineData(1100f)] [InlineData(1200f)]
    public void The_tail_is_vertical_inside_the_card_with_24_to_spare_and_the_card_stays_in_696_to_1244(float tx)
    {
        var p = LevelCardPlace.Compute(247, 86, 978, 959, (tx, 1010f));
        Assert.InRange(p.X, 696, 1244 - 247);
        Assert.InRange(tx - p.X, p.TailX - 0.6f, p.TailX + 0.6f);
        Assert.InRange(p.TailX, 24, 247 - 24);
        Assert.Equal(1010.0 - (p.Y + 86), p.Stem, 1);
    }

    [Fact]
    public void A_target_by_the_left_statue_pins_the_card_at_696()
    {
        var p = LevelCardPlace.Compute(470, 86, 978, 959, (700f, 1010f));
        Assert.Equal(696, p.X);
        Assert.Equal(24, p.TailX);
        Assert.Equal(470f, LevelCardPlace.MaxW);
        Assert.Equal(Math.Round(960 - 235f), LevelCardPlace.Compute(470, 86, 978, 959, null).X);
    }

    [Fact]
    public void The_stance_card_goes_to_set_II_and_wears_the_new_words()
    {
        Assert.Equal(1, AutoRowModel.CardSet);
        Assert.Equal(AutoRowModel.CardSet, 1);
        // set II stands behind set I while set I is up, in front once it is
        var front = (1000f, 500f);
        Assert.NotEqual(front, AutoRowModel.DiscCentre(front, 1, 0));
        Assert.Equal(front, AutoRowModel.DiscCentre(front, 1, 1));
        Assert.Equal("Choose a new trait", LevelCards.PromptFor(2));
        var c = LevelCards.StanceCard(8, "shield")!;
        Assert.StartsWith("Your blows", c.Line);
        Assert.EndsWith(", and each swap strikes", c.Line);
    }

    [Fact]
    public void A_target_inside_the_span_keeps_the_card_centred()
    {
        var p = LevelCardPlace.Compute(247, 86, 978, 959, (960f, 1000f));
        Assert.Equal(Math.Round(960 - 247 / 2f), p.X);
    }

    [Fact]
    public void The_cards_chip_is_the_seats_chip_for_every_slot()
    {
        for (int slot = 0; slot < 4; slot++)
            Assert.Equal(KeyMap.Skills[KeyMap.SeatSlot[KeyMap.SeatOf(slot)]], LevelCardPlace.CapAct(slot));
        Assert.Equal(Act.Skill4, LevelCardPlace.CapAct(3));
        Assert.Equal(Act.Skill3, LevelCardPlace.CapAct(2));
    }

    [Fact]
    public void The_tail_breaks_3_px_clear_around_a_tile_it_would_cross()
    {
        var tile = (L: 860f, T: 100f, R: 894f, B: 134f);
        var spans = LevelCardPlace.StemSpans(875, 40, 200, new[] { tile });
        Assert.Equal(2, spans.Count);
        Assert.Equal((40f, 97f), spans[0]);
        Assert.Equal((137f, 200f), spans[1]);
        // beside it (more than 3 + the tail's half width away) it runs whole
        Assert.Single(LevelCardPlace.StemSpans(900, 40, 200, new[] { tile }));
        // the target the tail only reaches is not avoided
        Assert.Equal((40f, 100f), Assert.Single(LevelCardPlace.StemSpans(875, 40, 100, new[] { tile })));
    }

    [Fact]
    public void An_auto_tile_opens_at_1_7_and_10() => Assert.Equal(new[] { 1, 7, 10 }, new[] { AutoRowModel.OpensAt(0), AutoRowModel.OpensAt(1), AutoRowModel.OpensAt(2) });
}
