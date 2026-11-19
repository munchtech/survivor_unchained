using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The demo flavor's cut lists (data/content/demo.json, Core.Demo): off, nothing is cut; on, the arena, the story and
/// the roost are cut and the den's way stays; the demo's goals point at the town's east gate and the den's mouth.</summary>
public class DemoTests
{
    [Fact]
    public void Off_cuts_nothing()
    {
        Assert.False(Demo.On);
        Assert.False(Demo.HidesInteractable("maps"));
        Assert.False(Demo.HidesTalk("rook"));
        Assert.False(Demo.HidesCinematic("c02"));
        Assert.False(Demo.NoArenas);
        Assert.False(Demo.FreezeClock);
        Assert.False(Demo.HidesDungeon("roost"));
    }

    [Fact]
    public void The_lists_cut_the_arena_the_story_and_the_roost_but_keep_the_way_to_the_den()
    {
        // (read through the lists, never by switching Demo.On: other tests read goals and zones in parallel)
        var c = Demo.Data;
        foreach (var id in new[] { "maps", "talk:rook", "door:smithy", "board", "scar:2:hollow", "night:hollow", "enter_roost", "cage1", "petal0", "vaultdoor", "greymuzzle", "gate:south" })
            Assert.True(Demo.Listed(c.Interactables, id), id);
        foreach (var id in new[] { "enter_hollow", "exit", "gate:east", "postfire", "postrest", "lamppost:verge.post", "well" })
            Assert.False(Demo.Listed(c.Interactables, id), id);
        Assert.True(Demo.Listed(c.Talks, "cin_iron_marker"));
        Assert.True(Demo.Listed(c.Cinematics, "c04b"));
        Assert.True(Demo.Listed(c.Storybooks, "sb00"));
        Assert.True(c.NoArenas && c.NoMapTable && c.FreezeClock && c.HideMale && c.NoDevKeys && c.NoOpeningStory);
        Assert.Equal(["hollow"], c.Dungeons);
        Assert.Contains("table", c.HideGoals);
    }

    [Fact]
    public void Listed_matches_exact_star_and_prefix()
    {
        Assert.True(Demo.Listed(["a", "b*"], "a"));
        Assert.True(Demo.Listed(["b*"], "bee"));
        Assert.False(Demo.Listed(["b*"], "ab"));
        Assert.True(Demo.Listed(["*"], "anything"));
        Assert.False(Demo.Listed([], "a"));
    }

    [Fact]
    public void The_demo_goals_parse_and_pin_the_east_gate_and_the_den()
    {
        var g = Demo.Data.Goals;
        Assert.NotNull(g);
        var defs = Json.Parse<System.Collections.Generic.List<GoalDef>>(g!.Value.GetRawText());
        Assert.Contains(defs, d => d.Zone == "waystation" && d.Pin == "gate:east");
        Assert.Contains(defs, d => d.Zone == "verge" && d.Pin == "enter_hollow");
        Assert.All(defs, d => Assert.NotEmpty(d.Steps));
    }
}
