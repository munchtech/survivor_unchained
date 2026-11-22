using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The unlock cards (data/content/unlock_cards.json, BUILD_UNLOCKS.md): one row per layer on a calling's ladder, the
/// card and the lesson read from it, the calling's skill never on a layer's level, the lesson once.</summary>
public sealed class UnlockCardTests
{
    static TaughtBuild Warden => TaughtBuilds.Of("warden")!;

    /// <summary>Every taught skill on its taught slot: the keys 0-3.</summary>
    static int SlotOf(string id)
    {
        return Warden.Keys.FindIndex(s => s.Skill == id);
    }

    [Fact]
    public void Every_layer_level_has_exactly_one_row_and_no_row_is_extra()
    {
        var want = new List<(int Level, string Id)>();
        foreach (var s in Warden.Keys) want.Add((s.Level, s.Skill));
        want.Add((Warden.Stance!.Level, "stance"));
        want.Add((LampBook.RoadLevel, "road"));
        var have = UnlockCards.Rows("warden").Select(r => (r.Level, r.Id)).ToList();
        Assert.Equal(want.OrderBy(x => x.Level).ThenBy(x => x.Id), have.OrderBy(x => x.Level).ThenBy(x => x.Id));
        foreach (var r in UnlockCards.Rows("warden"))
        {
            Assert.Contains(r.Kind, new[] { "key", "stance", "road" });
            Assert.NotEqual("", r.Line);
            Assert.NotEqual("", r.Title);
            Assert.NotEqual("", r.Lands);
            // (a key row's skill is a key of the build)
            if (r.Kind == "key") Assert.Contains(Warden.Keys, s => s.Skill == r.Id);
            // (a key and a stance lesson teach with a key's name; the road teaches nothing)
            if (r.Kind is "road") Assert.False(r.Teach.NextFight, r.Id);
            if (r.Teach.NextFight) { Assert.NotEqual("", r.Teach.Text); Assert.NotEqual("", r.Teach.Key); }
        }
    }

    [Fact]
    public void No_level_has_two_rows_but_the_starting_kit()
    {
        foreach (var g in UnlockCards.Rows("warden").Where(r => !r.Start).GroupBy(r => r.Level)) Assert.Single(g);
        Assert.All(UnlockCards.Rows("warden").Where(r => r.Start), r => Assert.Equal(1, r.Level));
        Assert.Equal(2, UnlockCards.Rows("warden").Count(r => r.Start));
    }

    [Fact]
    public void Levels_2_to_10_make_one_card_each_of_the_rows_kind_and_line()
    {
        for (int l = 2; l <= 10; l++)
        {
            var cards = LevelCards.CardsFor(l, Warden, SlotOf, 0, null, roadRaised: l == LampBook.RoadLevel);
            var card = Assert.Single(cards);
            Assert.NotEqual(LevelCardKind.NewSkill, card.Kind);
            Assert.Equal(l, card.Level);
            var row = UnlockCards.At("warden", l);
            if (row == null) { Assert.Equal(LevelCardKind.Plain, card.Kind); Assert.Equal($"LEVEL {l}", LevelCards.Header(card)); continue; }
            var kind = row.Kind switch { "key" => LevelCardKind.NewKey, "auto" => LevelCardKind.NewAuto, "stance" => LevelCardKind.NewStance, _ => LevelCardKind.NewRoad };
            Assert.Equal(kind, card.Kind);
            Assert.Equal(row.Line, card.Line);
            Assert.Equal($"LEVEL {l} · {row.Title}", LevelCards.Header(card));
        }
        Assert.Equal("LEVEL 6 · A ROAD TO WALK", LevelCards.Header(LevelCards.CardsFor(6, Warden, SlotOf, 0, null, true)[0]));
        // (the road not raised: level 6 is a plain card)
        Assert.Equal(LevelCardKind.Plain, LevelCards.CardsFor(6, Warden, SlotOf, 0)[0].Kind);
        // (a layer's level never takes the road's card, raised or not)
        Assert.Equal(LevelCardKind.NewKey, LevelCards.CardsFor(9, Warden, SlotOf, 0, null, true)[0].Kind);
        // (the skill's own line is its row's, as the key card draws it)
        Assert.Equal(UnlockCards.Of("warden", "shield_charge")!.Line, LevelCards.Line("shield_charge", Weapons.All["shield_charge"].Description));
    }

    [Fact]
    public void The_callings_skill_never_shares_a_layers_level_and_waits_for_a_quiet_moment()
    {
        // (levels 6 and 9 with a calling skill taught: still one card, and no new skill among it)
        foreach (var l in new[] { 6, 9 })
        {
            var cards = LevelCards.CardsFor(l, Warden, SlotOf, 0, null, roadRaised: l == 6);
            Assert.Single(cards);
            Assert.DoesNotContain(cards, c => c.Kind == LevelCardKind.NewSkill);
        }
        var skill = LevelCards.NewSkill(0, "dawnpulse");
        Assert.Equal("A NEW SKILL", LevelCards.Header(skill));
        Assert.False(LevelCards.CallingDue(true, 10));
        Assert.False(LevelCards.CallingDue(false, 1.9));
        Assert.True(LevelCards.CallingDue(false, LevelCards.QuietFor));
        Assert.True(LevelCards.CallingDue(false, 5));
    }

    [Fact]
    public void The_road_card_says_its_row_with_no_key_and_no_prompt_row()
    {
        var road = LevelCards.RoadCard(6, "warden")!;
        Assert.Equal((LevelCardKind.NewRoad, string.Join(" or ", Lamps.RoadsOf("warden").Select(r => r.Name.Replace("Road of the ", "")))), (road.Kind, road.Skill));
        Assert.Contains(" or ", road.Skill);
        Assert.Equal("Your road", LevelCards.RoadNames("nobody"));
        Assert.Equal(UnlockCards.Of("warden", "road")!.Line, road.Line);
        Assert.False(road.HasPrompt);
        Assert.Equal(-1, road.Slot);
        Assert.Null(LevelCards.RoadCard(6, "nobody"));
        // (its glyph exists)
        Assert.Contains("\"" + road.Icon + "\"", SurvivorUnchained.Core.DataFiles.Text("content/glyphs.json"));
    }

    static UnlockCard Row(string id) => UnlockCards.Of("warden", id)!;

    [Fact]
    public void A_lesson_teaches_once_at_the_next_fight_and_a_press_clears_it()
    {
        var done = new HashSet<string>();
        var lessons = new UnlockLessons(done.Contains, id => done.Add(id));
        lessons.Opened(Row("heroic_leap"));
        Assert.Null(lessons.Tick(true, 0.1));     // (a fight already near, the card just up: not yet)
        Assert.Null(lessons.Tick(false, 0.1));
        var row = lessons.Tick(true, 0.1);        // (a fight near after one that was not)
        Assert.Same(Row("heroic_leap"), row);
        Assert.Null(lessons.Tick(true, 0.1));
        Assert.Contains("heroic_leap", done);
        Assert.False(lessons.Used("bladestorm"));
        Assert.True(lessons.Used("heroic_leap"));  // (its hint was up: taken down)
        Assert.False(lessons.Used("heroic_leap"));
        // (taught once per character: opened again, it stays quiet)
        lessons.Opened(Row("heroic_leap"));
        Assert.Null(lessons.Tick(false)); Assert.Null(lessons.Tick(true));
    }

    [Fact]
    public void A_fight_near_three_seconds_after_the_card_is_the_next_fight_and_the_stance_lesson_ends_on_a_swap()
    {
        var done = new HashSet<string>();
        var lessons = new UnlockLessons(done.Contains, id => done.Add(id));
        lessons.Opened(Row("stance"));
        Assert.Null(lessons.Tick(true, 2.0));
        Assert.Same(Row("stance"), lessons.Tick(true, 1.1));
        Assert.True(lessons.Used("stance"));
        // (used before the fight: owed no more)
        lessons.Opened(Row("shield_charge"));
        Assert.False(lessons.Used("shield_charge"));
        Assert.Null(lessons.Tick(false)); Assert.Null(lessons.Tick(true));
        Assert.Contains("shield_charge", done);
    }

    [Fact]
    public void An_auto_the_road_and_the_starting_kit_never_teach()
    {
        var done = new HashSet<string>();
        var lessons = new UnlockLessons(done.Contains, id => done.Add(id));
        foreach (var id in new[] { "iron_vow", "watch_bell", "road", "sunder", "groundbreaker" })
        {
            lessons.Opened(Row(id));
            Assert.Null(lessons.Tick(false));
            Assert.Null(lessons.Tick(true, 5));
        }
        Assert.Empty(done);
    }

    [Fact]
    public void A_lesson_names_the_key_and_never_says_the_key()
    {
        int shown = 0;
        foreach (var row in UnlockCards.All.Values.SelectMany(l => l).Where(r => r.Teach.NextFight))
        {
            string text = UnlockLessons.TextFor(row, k => "[" + k + "]");
            Assert.DoesNotContain("{key}", text);
            Assert.DoesNotContain("the key", text);
            if (row.Teach.Key != "") Assert.Contains("[" + row.Teach.Key + "]", text);
            shown++;
        }
        Assert.True(shown >= 4);
        Assert.Equal("Press *[Skill4]* to charge behind your shield: what stands in the way is struck and thrown aside.", UnlockLessons.TextFor(UnlockCards.ForSkill("shield_charge")!, k => "[" + k + "]"));
    }
}
