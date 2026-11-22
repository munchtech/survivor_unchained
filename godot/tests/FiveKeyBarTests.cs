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
/// for the harness, an old save still loads, and its bar is re-cut to the four taught keys.</summary>
public sealed class FourKeyBarTests
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
    public void After_its_re_cut_the_old_save_carries_exactly_the_four_taught_keys_in_key_order()
    {
        var j = Journey.From(OldSave(), 1);
        KeyBarTests.Fight(j);
        Assert.Equal(TaughtBuilds.BarShape, j.Ch.Bar);
        Assert.Equal(["sunder", "heroic_leap", "bladestorm", "iron_vow"], SkillBook.Carried(j.Ch).Select(c => c.Id).ToArray());
    }
}
