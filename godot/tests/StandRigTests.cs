using System.IO;
using SurvivorUnchained.Look;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 lead 14, S1; docs/design/NIGHT_KIT.md K1) The standing material's levels (rigs.json "stand") are
/// arena_night's alone: every other rig is untouched (its arenas keep the kit's flora, its stone the old code).</summary>
public class StandRigTests
{
    [Fact]
    public void OnlyArenaNightCarriesStand()
    {
        var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
        while (dir != null && !File.Exists(Path.Combine(dir.FullName, "data", "look", "rigs.json"))) dir = dir.Parent;
        Assert.NotNull(dir);
        var s = RigSet.Parse(File.ReadAllText(Path.Combine(dir!.FullName, "data", "look", "rigs.json")));
        foreach (var (id, r) in s.Rigs)
            if (id == "arena_night")
            {
                Assert.True(r.Stands, "arena_night carries stand");
                Assert.Equal(LightRig.StandLength, r.Stand!.Length);
            }
            else Assert.True(r.Stand == null && !r.Stands, id);
    }
}
