using System.Reflection;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Play.Zones;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(P9 set) The handles on a story arena's own pieces: the "shift" cue, StoryFight.Opened, IStoryArena.Shift, ArenaShape.Level.</summary>
public class P9HandleTests
{
    [Fact]
    public void ShiftCueIsKnownAndLasting()
    {
        Assert.Contains("shift", CineCue.Kinds);
        Assert.True(new CineCue { Do = "shift" }.Lasting);
    }

    [Fact]
    public void OpenedIsAVirtualNoOp_AndArenaShiftHasADefault()
    {
        var opened = typeof(StoryFight).GetMethod("Opened")!;
        Assert.True(opened.IsVirtual && !opened.IsAbstract);
        var shift = typeof(IStoryArena).GetMethod("Shift")!;
        Assert.False(shift.IsAbstract);   // a default body: test fakes compile without it
        Assert.NotNull(typeof(StoryNight).GetMethod("Shift", new[] { typeof(string), typeof(double) }));
    }

    [Fact]
    public void ShapeLevelKeepsTheHeightByDefault()
    {
        var level = typeof(ArenaShape).GetMethod("Level")!;
        Assert.True(level.IsVirtual);
    }
}
