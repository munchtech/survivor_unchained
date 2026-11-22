using System.Linq;
using System.Text.Json.Nodes;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The auto slots and the kindled option are gone (docs/design/SKILL_KINDS.md, 22 Nov): the old counts stay pinned
/// for the harness, an old save still loads, and its bar is re-cut to the five taught keys (BUILD_DIRECTION.md Round 10, 22 Nov: five keys, opening at 1, 4, 5, 7 and 9).</summary>
public sealed class FiveKeyBarTests
{
    [Theory]
    [InlineData(1, 2)]
    [InlineData(2, 2)]
    [InlineData(3, 2)]
    [InlineData(4, 3)]
    [InlineData(5, 4)]
    [InlineData(6, 4)]
    [InlineData(7, 5)]
    [InlineData(8, 5)]
    [InlineData(9, 6)]
    [InlineData(10, 7)]
    [InlineData(11, 7)]
    [InlineData(12, 7)]
    [InlineData(13, 7)]
    [InlineData(14, 7)]
    [InlineData(15, 7)]
    public void The_old_keys_plus_autos_ladder_stays_pinned_for_the_harness(int level, int slots) =>
        Assert.Equal(slots, SkillBook.OldBarSlotsAt(level));

    [Theory]
    [InlineData(1, 1)]
    [InlineData(3, 1)]
    [InlineData(4, 2)]
    [InlineData(5, 3)]
    [InlineData(6, 3)]
    [InlineData(7, 4)]
    [InlineData(8, 4)]
    [InlineData(9, 5)]
    [InlineData(15, 5)]
    public void The_keys_open_at_levels_1_4_5_7_and_9(int level, int keys) => Assert.Equal(keys, SkillBook.KeysAt(level));

    [Fact]
    public void The_campaign_has_five_keys() => Assert.Equal(5, Weapons.MaxKeys);

    /// <summary>A save holding an old seven-slot bar (an "autoForm" field, Bar 2) at level 10.</summary>
    static SaveData OldSave()
    {
        var j = KeyBarTests.New(10);
        var node = JsonNode.Parse(Json.Write(j.ToSave(new SaveLocation { Zone = "waystation" })))!;
        var c = node["character"]!.AsObject();
        c["autoForm"] = new JsonArray("groundbreaker");
        c["bar"] = 2;
        c["taughtUpTo"] = 10;
        var old = new[] { "sunder", "groundbreaker", "heroic_leap", "iron_vow", "bladestorm", "shield_charge", "watch_bell" };
        c["skills"] = new JsonArray(old.Select(s => (JsonNode)JsonValue.Create(s)!).ToArray());
        c["slotted"] = new JsonArray(old.Select(s => (JsonNode)JsonValue.Create(s)!).ToArray());
        return Saves.Parse(node.ToJsonString())!;
    }

    [Fact]
    public void An_old_save_with_an_autoForm_field_loads_without_an_exception()
    {
        var d = OldSave();
        Assert.Equal(10, d.Character.Level);
        Assert.Equal(2, d.Character.Bar);
        Assert.Contains("groundbreaker", d.Character.Slotted);
        var j = Journey.From(d, 1);
        Assert.Equal(10, j.Ch.Level);
    }

    [Fact]
    public void After_its_re_cut_the_old_save_carries_exactly_the_five_taught_keys_in_key_order()
    {
        var j = Journey.From(OldSave(), 1);
        KeyBarTests.Fight(j);
        Assert.Equal(TaughtBuilds.BarShape, j.Ch.Bar);
        Assert.Equal(["sunder", "heroic_leap", "bladestorm", "iron_vow", "shield_charge"], SkillBook.Carried(j.Ch).Select(c => c.Id).ToArray());
    }

    /// <summary>A save from the four-pressed-keys bar (Bar 3: Iron Vow on key 4 at level 9).</summary>
    [Fact]
    public void A_four_pressed_key_save_is_re_cut_into_the_five_keys()
    {
        var j = KeyBarTests.New(9);
        var node = JsonNode.Parse(Json.Write(j.ToSave(new SaveLocation { Zone = "waystation" })))!;
        var c = node["character"]!.AsObject();
        c["bar"] = 3;
        c["taughtUpTo"] = 9;
        var four = new[] { "sunder", "heroic_leap", "bladestorm", "iron_vow" };
        c["skills"] = new JsonArray(four.Select(s => (JsonNode)JsonValue.Create(s)!).ToArray());
        c["slotted"] = new JsonArray(four.Select(s => (JsonNode)JsonValue.Create(s)!).ToArray());
        var d = Saves.Parse(node.ToJsonString())!;
        Assert.Equal(3, d.Character.Bar);
        var j2 = Journey.From(d, 1);
        KeyBarTests.Fight(j2);
        Assert.Equal(TaughtBuilds.BarShape, j2.Ch.Bar);
        Assert.Equal(["sunder", "heroic_leap", "bladestorm", "iron_vow", "shield_charge"], SkillBook.Carried(j2.Ch).Select(x => x.Id).ToArray());
    }
}
