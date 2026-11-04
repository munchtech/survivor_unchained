using System;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A table arena as a board (H1 item 6: data/content/boards.json, Maps/ArenaBoard.cs): the Pack's tier-1
/// Hollow cut to 52 m, a fold round a lamp reached only through its three gaps; other tiers and story nights as
/// they were.</summary>
public class BoardTests
{
    [Fact]
    public void The_boards_load()
    {
        var d = Boards.For("hollow", 1);
        Assert.NotNull(d);
        Assert.Equal(52, d!.Radius);
        Assert.Equal(3, d.Fold.Gaps);
        Assert.Null(Boards.For("hollow", 2));
        Assert.Null(Boards.For("barrow", 1));
    }

    [Theory]
    [InlineData(3)]
    [InlineData(17)]
    [InlineData(311)]
    public void A_tier_one_pack_arena_is_a_board_held_through_its_gaps(int seed)
    {
        var m = MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = "pack", Tier = 1 });
        var b = m.Board;
        Assert.NotNull(b);
        Assert.Same(b, m.Meta.Board);
        Assert.Equal(52, b!.Radius);
        Assert.Equal(3, b.Chokes.Count);
        Assert.Single(b.Lamps);
        Assert.Equal(3, b.Lanes.Count);
        var lamp = b.Lamps[0];
        Assert.InRange(lamp.Light, 0, m.Meta.Lights.Count - 1);
        // Its light hangs at the lantern's flame, off the post by the arm (Head, at its scale), and reaches past the wall.
        var ll = m.Meta.Lights[lamp.Light];
        Assert.InRange(MathX.Dist(ll.X, ll.Z, lamp.X, lamp.Z), 0.5, 1.12 * lamp.Def.Scale + 0.1);
        Assert.True(ll.Distance >= b.Fold.WallR + 1, "the lamp's light falls short of the wall");
        Assert.True(ll.Core > 0);
        // Door lights at both sides of each gap.
        Assert.Equal(2 * b.Chokes.Count, m.Meta.Lights.Count(l => l.Color == Boards.For("hollow", 1)!.Fold.Door.Color && MathX.Dist(l.X, l.Z, b.Fold.X, b.Fold.Z) < b.Fold.OuterR));
        Assert.Contains(m.Pieces, p => p.Id == "halloween/post_lantern" && Math.Abs(p.X - lamp.X) < 0.01);
        var r = BoardCheck.Measure(m);
        Assert.False(r.Leaks, "the fold reaches the outside with its gaps shut");
        Assert.True(r.StartOutside);
        Assert.True(r.FoldReached);
        // The fold fits the play camera (about 28 by 24 m round her): wall 9-11 m out, 2 m through.
        Assert.InRange(b.Fold.OuterR, 9.5, 12.5);
        Assert.InRange(r.FoldInside, 150, 420);
        foreach (var g in r.Gaps)
        {
            Assert.True(g.Passable, $"gap at {g.Bearing:0.00} shut");
            Assert.InRange(g.ClearWidth, 4.9, 6.2);
        }
        // One gap faces the start.
        double toStart = Math.Atan2(-b.Fold.Z, -b.Fold.X);
        Assert.Contains(b.Chokes, c => Math.Abs(MathX.Wrap(c.Bearing - toStart)) < 0.2);
        // The walkable ground about (52/84)^2 of the open bowl's.
        var was = BoardCheck.Measure(MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = "pack", Tier = 1, StoryNight = true }));
        Assert.InRange((double)r.Open / was.Open, 0.3, 0.45);
        // Cover is fewer, and never in the fold.
        Assert.DoesNotContain(m.Meta.Colliders, c => c.Kind == SurvivorUnchained.Sim.ColliderKind.Circle && b.Fold.Contains(c.X, c.Z)
            && Math.Sqrt(Math.Pow(c.X - lamp.X, 2) + Math.Pow(c.Z - lamp.Z, 2)) > 1);
    }

    [Fact]
    public void Other_tiers_and_story_nights_take_no_board()
    {
        Assert.Null(MapGen.Generate(new MapSpec { Seed = 3, Arena = true, People = "pack", Tier = 2 }).Board);
        Assert.Null(MapGen.Generate(new MapSpec { Seed = 3, Arena = true, People = "pack", Tier = 1, StoryNight = true }).Board);
        Assert.Null(MapGen.Generate(new MapSpec { Seed = 311, Arena = true, People = "pack", Tier = 1, Story = "hollow_by_night", StoryNight = true }).Board);
        Assert.Null(MapGen.Generate(new MapSpec { Seed = 3, Arena = true, People = "dead", Tier = 1 }).Board);
        // A story night's spec says so.
        Assert.True(new ArenaSpec { Id = "x", Name = "x", People = "pack", Story = true }.Map.StoryNight);
    }
}
