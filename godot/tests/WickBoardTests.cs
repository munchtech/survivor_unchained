using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

public sealed class WickBoardTests
{
    static CharacterData Warden(int level)
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = level;
        ch.Equipment = new Equipment();
        return ch;
    }

    [Fact]
    public void Held_points_do_not_light_the_wick_board()
    {
        var ch = Warden(9);
        LampBook.Now(ch).Held["sunder"] = SkillBook.Rank(ch);
        var stats = WickBook.Weapon(ch, "sunder", WickBook.RankIn(ch, "sunder", false));
        Assert.Empty(stats.Wick!.Lit);
        var board = WickBoardModel.Read(ch, "sunder");
        Assert.Equal(stats.Wick.Lit, board.Lit);
    }

    public static IEnumerable<object[]> Skills() => Wicks.Skills.SelectMany(skill =>
        (Items.Affix(Items.PlusId(skill))?.Plus == skill ? new[] { false, true } : new[] { false })
            .Select(plus => new object[] { skill, plus }));

    [Theory]
    [MemberData(nameof(Skills))]
    public void Every_held_and_lit_count_agrees_with_stats_and_tooltip(string skill, bool plus)
    {
        var ch = Warden(1);
        if (plus)
            ch.Equipment.Ring1 = Inventory.Make(null, "copper_ring", rarity: 2, seed: 3,
                affixes: new List<AffixRoll> { new() { Id = Items.PlusId(skill), Tier = 0 } });
        var strands = Wicks.StrandsOf(skill).ToArray();
        var all = strands.SelectMany(s => Enumerable.Range(1, Wicks.PerStrand).Select(s.LampId)).ToArray();
        var plans = new[] { Array.Empty<string>() }.Concat(strands.Select(s => Enumerable.Range(1, Wicks.PerStrand).Select(s.LampId).ToArray()));
        foreach (var plan in plans)
        {
            LampBook.Now(ch).Wicks[skill] = plan.ToList();
            for (int points = 1; points <= Weapons.MaxRank; points++)
            {
                ch.Level = 2 * points - 1;
                for (int held = 0; held <= points + 1; held++)
                {
                    LampBook.Now(ch).Held[skill] = held;
                    int burning = held > 0 ? Math.Max(0, points - held) : Math.Min(Weapons.MaxRank, points + (plus ? 1 : 0));
                    var expected = WickBook.Path(ch, skill).Take(burning).ToArray();
                    var stats = WickBook.Weapon(ch, skill, WickBook.RankIn(ch, skill, false));
                    var board = WickBoardModel.Read(ch, skill);
                    var tip = SkillTipModel.Build(ch, null, skill, "press");
                    Assert.True(expected.SequenceEqual(board.Lit), $"{skill}: {points} points, {held} held, plus {plus}, plan {string.Join(",", plan)}");
                    Assert.Equal(expected, stats.Wick!.Lit);
                    Assert.Equal(expected, tip.LitLamps.ToArray());
                    Assert.Equal(expected.Length, all.Count(id => board.StateOf(id) == WickLampState.Lit));
                    foreach (var id in all)
                    {
                        var state = expected.Contains(id) ? WickLampState.Lit : plan.Contains(id) ? WickLampState.Planned : WickLampState.Unlit;
                        Assert.Equal(state, board.StateOf(id));
                    }
                    if (WickBook.Sum(ch, skill, false) is { } sum) Assert.Equal(stats.Damage, sum.Total);
                }
            }
        }
    }

    [Fact]
    public void Lighting_a_held_point_uses_the_existing_planned_and_unlit_states()
    {
        var ch = Warden(1);
        var id = WickBook.Path(ch, "sunder")[0];
        WickBook.Hold(ch, "sunder", 1);
        Assert.Equal(WickLampState.Unlit, WickBoardModel.Read(ch, "sunder").StateOf(id));
        Assert.Equal(WickNo.None, WickBook.Plan(ch, "sunder", id));
        Assert.Equal(WickLampState.Planned, WickBoardModel.Read(ch, "sunder").StateOf(id));
        Assert.Equal(id, WickBook.Light(ch, "sunder"));
        Assert.Equal(WickLampState.Lit, WickBoardModel.Read(ch, "sunder").StateOf(id));
        Assert.Equal(new[] { id }, SkillTipModel.Build(ch, null, "sunder", "hold").LitLamps.ToArray());
    }

    [Fact]
    public void Each_layout_reads_its_own_held_points_and_plan()
    {
        var ch = Warden(5);
        var book = LampBook.State(ch);
        var strands = Wicks.StrandsOf("sunder").ToArray();
        for (int i = 0; i < book.Layouts.Count; i++)
        {
            book.Layouts[i].Held["sunder"] = i;
            book.Layouts[i].Wicks["sunder"] = Enumerable.Range(1, Wicks.PerStrand).Select(strands[i].LampId).ToList();
        }
        for (int i = book.Layouts.Count - 1; i >= 0; i--)
        {
            book.Active = i;
            var board = WickBoardModel.Read(ch, "sunder");
            Assert.Equal(SkillBook.Rank(ch) - i, board.Lit.Length);
            Assert.Equal(WickBook.Weapon(ch, "sunder", WickBook.RankIn(ch, "sunder", false)).Wick!.Lit, board.Lit);
            Assert.Equal(board.Lit, SkillTipModel.Build(ch, null, "sunder", "hold").LitLamps.ToArray());
        }
    }

    [Fact]
    public void An_unplanned_turn_is_crossed_only_when_another_turn_is_lit()
    {
        var ch = Warden(9);
        var path = WickBook.Path(ch, "sunder");
        var turn = path.First(id => Wicks.IsTurn("sunder", id));
        var other = Wicks.StrandsOf("sunder").Select(s => s.LampId(Wicks.PerStrand)).First(id => id != turn);
        LampBook.Now(ch).Held["sunder"] = 2;
        var board = WickBoardModel.Read(ch, "sunder");
        Assert.False(board.TurnTaken);
        Assert.False(board.Crossed(other));
        Assert.Equal(WickLampState.Unlit, board.StateOf(turn));
        WickBook.Light(ch, "sunder");
        board = WickBoardModel.Read(ch, "sunder");
        Assert.True(board.TurnTaken);
        Assert.True(board.Crossed(other));
        Assert.Equal(WickLampState.Lit, board.StateOf(turn));
    }

    [Fact]
    public void A_live_tooltip_reads_the_same_lit_lamps_as_the_board()
    {
        var ch = Warden(5);
        for (int held = 0; held <= SkillBook.Rank(ch); held++)
        {
            LampBook.Now(ch).Held["sunder"] = held;
            var battle = BattleTests.Arena(7, ("sunder", WickBook.RankIn(ch, "sunder", false)));
            battle.SetWickPath("sunder", WickBook.DayPath(ch, "sunder"));
            var board = WickBoardModel.Read(ch, "sunder");
            var tip = SkillTipModel.Build(ch, battle, "sunder", "hold");
            Assert.Equal(board.Lit, tip.LitLamps.ToArray());
            Assert.Equal(board.Lit, battle.Weapons.Single(w => w.Id == "sunder").Wick!.Lit);
        }
    }

    [Theory]
    [MemberData(nameof(Skills))]
    public void Arena_board_ignores_held_points_like_its_stats_and_tooltip(string skill, bool plus)
    {
        var ch = Warden(2 * Weapons.MaxRank - 1);
        if (plus)
            ch.Equipment.Ring1 = Inventory.Make(null, "copper_ring", rarity: 2, seed: 3,
                affixes: new List<AffixRoll> { new() { Id = Items.PlusId(skill), Tier = 0 } });
        int rank = WickBook.RankIn(ch, skill, true);
        for (int held = 0; held <= SkillBook.Rank(ch) + 1; held++)
        {
            LampBook.Now(ch).Held[skill] = held;
            var board = WickBoardModel.Read(ch, skill, night: true);
            var stats = WickBook.Weapon(ch, skill, rank, night: true);
            var battle = BattleTests.Arena(7, (skill, rank));
            battle.SetWickPath(skill, WickBook.Path(ch, skill));
            var tip = SkillTipModel.Build(ch, battle, skill, "press");
            Assert.Equal(WickBook.Path(ch, skill).Take(rank), board.Lit);
            Assert.Equal(stats.Wick!.Lit, board.Lit);
            Assert.Equal(tip.LitLamps, board.Lit);
            Assert.Empty(board.Held);
            Assert.Equal(rank, board.Rank);
        }
    }
}
