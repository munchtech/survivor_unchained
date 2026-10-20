using System.Linq;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The armed townsfolk's stands (logic/Play/TownStands.cs): only the town's own names map; each
/// townsperson's loop starts at its own place, the same every build.</summary>
public class TownStandsTests
{
    [Fact]
    public void ArmedStandsMapOnlyTheTownsOwnNames()
    {
        Assert.Equal("idle_armed", TownStands.Armed("Idle_Armed"));
        Assert.Equal("idle_2h", TownStands.Armed("Idle_2H_Rest"));
        // The bosses' and the fights' armed idles keep the library's.
        foreach (var n in new[] { "Idle", "Idle_Shield_Loop", "2H_Melee_Idle", "Idle_Loop", "" })
            Assert.Null(TownStands.Armed(n));
    }

    [Fact]
    public void PhaseIsStableAndSpreadsNeighbours()
    {
        Assert.Equal(TownStands.Phase("guard0@1.0,2.0"), TownStands.Phase("guard0@1.0,2.0"));
        var ph = Enumerable.Range(0, 6).Select(i => TownStands.Phase($"guard{i}@{i}.0,3.0")).ToList();
        Assert.All(ph, p => Assert.InRange(p, 0, 1));
        Assert.Equal(ph.Count, ph.Distinct().Count());
        // Spread over the loop, not bunched.
        Assert.True(ph.Max() - ph.Min() > 0.3);
    }
}
