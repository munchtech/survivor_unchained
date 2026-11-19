using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play.Zones;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(playtest-bugs-3) A prologue callout that waits on a key must name a key that exists: Groundbreaker is a
/// kindled auto (slot 4 and up), and "Skill5" is unbound, so its Freeze could never be answered and the sim sat dead.</summary>
public class PrologueCalloutKeyTests
{
    [Fact]
    public void KeySlotsMapToTheFourKeysAndAutosToNone()
    {
        for (int s = 0; s < Weapons.MaxKeys; s++) Assert.Equal($"skill{s + 1}", Prologue.KeyActFor(s));
        for (int s = Weapons.MaxKeys; s < Weapons.MaxKeys + Weapons.AutoSlots + 2; s++) Assert.Null(Prologue.KeyActFor(s));
    }

    [Fact]
    public void GroundbreakerIsAnAutoSoItsCalloutNamesNoKey()
    {
        var t = TaughtBuilds.All["warden"];
        int auto = t.Autos.FindIndex(a => a.Skill == "groundbreaker");
        Assert.True(auto >= 0, "groundbreaker is a kindled auto");
        Assert.Null(Prologue.KeyActFor(Weapons.MaxKeys + auto));
    }
}
