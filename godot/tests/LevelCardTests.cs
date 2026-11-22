using System;
using System.Linq;
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
    public void The_keys_open_at_4_5_7_and_9_say_so_and_level_10_opens_nothing()
    {
        static int SlotOf(string id) => id switch { "heroic_leap" => 1, "bladestorm" => 2, "iron_vow" => 3, "shield_charge" => 4, _ => -1 };
        foreach (var l in new[] { 4, 5, 7, 9 }) Assert.Equal(LevelCardKind.NewKey, LevelCards.ForCampaignLevel(l, Warden, SlotOf, 0).Kind);
        // (no auto slots since 22 Nov: level 10 is a plain card)
        foreach (var l in new[] { 10 }) Assert.Equal(LevelCardKind.Plain, LevelCards.ForCampaignLevel(l, Warden, SlotOf, 0).Kind);
    }

    [Fact]
    public void Level_8_is_the_second_weapon_with_the_swap_key()
    {
        var s = LevelCards.ForCampaignLevel(8, Warden, _ => -1, 0);
        Assert.Equal(LevelCardKind.NewStance, s.Kind);
        Assert.Equal("LEVEL 8 · A SECOND WEAPON", LevelCards.Header(s));
        Assert.Equal("Shieldwall", s.Skill);
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
    public void The_tail_is_vertical_inside_the_card_with_24_to_spare_and_the_card_stays_in_720_to_1244(float tx)
    {
        var p = LevelCardPlace.Compute(247, 86, 978, 959, (tx, 1010f));
        Assert.InRange(p.X, 720, 1244 - 247);
        Assert.InRange(tx - p.X, p.TailX - 0.6f, p.TailX + 0.6f);
        Assert.InRange(p.TailX, 24, 247 - 24);
        Assert.Equal(1010.0 - LevelCardPlace.Land - (p.Y + 86), p.Stem, 1);
    }

    [Fact]
    public void A_target_by_the_left_statue_pins_the_card_at_720()
    {
        var p = LevelCardPlace.Compute(470, 86, 978, 959, (700f, 1010f));
        Assert.Equal(720, p.X);
        Assert.Equal(24, p.TailX);
        Assert.Equal(524f, LevelCardPlace.MaxW);   // (the whole span between the statues)
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
        Assert.EndsWith(", and every swap lands a strike.", c.Line);
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

    [Theory]
    [InlineData(700f, 1010f)] [InlineData(960f, 969f)] [InlineData(1100f, 960f)] [InlineData(1200f, 1013f)]
    public void The_stem_ends_2_px_above_its_targets_top_rim_for_every_target_kind(float tx, float ty)
    {
        // (road: the coin's arch top; auto: the tile's top; stance: the disc's top. Key cards keep their 10 px stub in LevelCard.)
        var p = LevelCardPlace.Compute(300, 92, 978, 959, (tx, ty));
        Assert.InRange(ty - (p.Y + 92 + p.Stem), 0, 3);
    }

    [Fact]
    public void The_stem_runs_through_a_rect_it_lands_on_but_breaks_for_one_it_crosses()
    {
        // a disc behind the tile whose top is above y1 and whose bottom is below it holds the tail's x: the target, not avoided
        Assert.Equal((40f, 100f), Assert.Single(LevelCardPlace.StemSpans(875, 40, 100, new[] { (L: 860f, T: 90f, R: 894f, B: 134f) })));
        // a rect wholly above y1 still cuts it
        Assert.Equal(2, LevelCardPlace.StemSpans(875, 40, 200, new[] { (L: 860f, T: 100f, R: 894f, B: 134f) }).Count);
    }

    [Fact]
    public void An_auto_tile_opens_at_1_7_and_10() => Assert.Equal(new[] { 1, 7, 10 }, new[] { AutoRowModel.OpensAt(0), AutoRowModel.OpensAt(1), AutoRowModel.OpensAt(2) });

    [Fact]
    public void Hold_is_by_the_words_with_the_prompt_row_on_top()
    {
        Assert.Equal(2.8, LevelCards.HoldSecs(3, false), 6);          // (a short one holds the floor)
        Assert.Equal(1.4 + 0.25 * 10, LevelCards.HoldSecs(10, false), 6);
        Assert.Equal(4.5, LevelCards.HoldSecs(40, false), 6);         // (a long one, the ceiling)
        Assert.Equal(4.5 + 0.8, LevelCards.HoldSecs(40, true), 6);
        Assert.Equal(2.8 + 0.8, LevelCards.HoldSecs(1, true), 6);
        Assert.Equal(6, LevelCards.Words("Heroic Leap  Leap where you → aim"));
        // the queue honours it, In 0.18 and Out 0.3 unchanged
        var q = new LevelCardQueue();
        q.Add(new LevelCardSpec { Level = 2 });
        q.Tick(1 / 60.0, false);
        q.HoldNow = 4;
        for (double x = 0; x < 0.18 + 3.9; x += 1 / 60.0) q.Tick(1 / 60.0, false);
        Assert.Equal(LevelCardQueue.Phase.Hold, q.Now);
        for (double x = 0; x < 0.2; x += 1 / 60.0) q.Tick(1 / 60.0, false);
        Assert.Equal(LevelCardQueue.Phase.Out, q.Now);
        for (double x = 0; x < 0.35; x += 1 / 60.0) q.Tick(1 / 60.0, false);
        Assert.Null(q.Current);
    }

    static readonly (float, float, float, float) Card = (700, 800, 1200, 900);

    [Fact]
    public void The_card_fades_for_anything_within_8_px_and_not_beyond()
    {
        Assert.False(CardFade.Blocked(Card, []));
        Assert.True(CardFade.Blocked(Card, [(800, 880, 820, 960)]));              // her, across it
        Assert.True(CardFade.Blocked(Card, [(1200 + 7, 850, 1300, 860)]));        // 7 px off its right edge: grown 8
        Assert.False(CardFade.Blocked(Card, [(1200 + 9, 850, 1300, 860)]));
        Assert.False(CardFade.Blocked(Card, [(100, 100, 300, 300), (800, 920, 900, 1000)]));
    }

    [Fact]
    public void The_alpha_eases_to_a_quarter_in_012_s_and_back_and_the_hold_waits_3_s_at_most()
    {
        var f = new CardFade();
        float dt = 1 / 60f;
        for (int i = 0; i < 7; i++) f.Step(true, true, dt);          // 0.117 s
        Assert.InRange(f.Alpha, 0.25f, 0.28f);
        for (int i = 0; i < 3; i++) f.Step(true, true, dt);
        Assert.Equal(0.25, f.Alpha, 4);
        float waited = 0;
        for (int i = 0; i < 60 * 5; i++) if (f.Step(true, true, dt)) waited += dt;
        Assert.InRange(waited + 10 * dt, 2.99f, 3.02f);   // (3 s all told) then it leaves anyway
        Assert.False(f.Step(true, true, dt));
        Assert.Equal(0.25, f.Alpha, 4);
        for (int i = 0; i < 8; i++) f.Step(false, true, dt);
        Assert.Equal(1.0, f.Alpha, 4);
        Assert.False(f.Step(false, true, dt));
        f.Reset();
        Assert.True(f.Step(true, true, dt));                          // (a new card gets its own 3 s)
        Assert.False(f.Step(true, false, dt));                        // (not while rising or leaving: only the hold waits)
    }

    [Fact]
    public void Every_unlock_line_is_one_line_of_72_characters_or_less_that_fits_the_card()
    {
        foreach (var row in SurvivorUnchained.Content.UnlockCards.All.Values.SelectMany(l => l))
        {
            Assert.True(row.Line.Length <= LevelCardPlace.LineChars, $"{row.Id}: {row.Line.Length} characters");
            // (UI sans 16 measured at no more than 6.5 px a character over these rows; the room is the card's width less the well's column)
            Assert.True(row.Line.Length * LevelCardPlace.PxPerChar <= LevelCardPlace.LineRoom + 10, $"{row.Id} would wrap");
        }
        Assert.Equal("Brace: for 2 s blows land at half, then burst back in a ring.", SurvivorUnchained.Content.UnlockCards.ForSkill("iron_vow")!.Line);
    }
}
