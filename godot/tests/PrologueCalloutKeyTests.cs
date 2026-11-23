using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play.Zones;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(playtest-bugs-3) A prologue callout that waits on a key must name a key that exists: a skill beyond the four
/// keys has no key, and "Skill5" is unbound, so its Freeze could never be answered and the sim sat dead.</summary>
public class PrologueCalloutKeyTests
{
    [Fact]
    public void KeySlotsMapToTheFourKeysAndNoneBeyond()
    {
        for (int s = 0; s < Weapons.MaxKeys; s++) Assert.Equal($"skill{s + 1}", Prologue.KeyActFor(s));
        for (int s = Weapons.MaxKeys; s < Weapons.MaxKeys + 5; s++) Assert.Null(Prologue.KeyActFor(s));
    }
}
