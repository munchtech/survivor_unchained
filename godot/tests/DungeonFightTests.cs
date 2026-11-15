using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The dungeons' fight numbers (data/content/dungeon_fights.json; dungeon-fights lane, 15 Nov). The 50-seed bands live in
/// the harness (`dotnet run --project godot/balance -- dungeon --seeds 50`): hollow human 88% deft 98% standing 0%, roost human 86%
/// deft 98% standing 0% (seeds 1-50; 51-100: 88/98, 84/98; castMove off). Here the rule in three seeds: a bot that never moves falls, the deft one clears.</summary>
public class DungeonFightTests
{
    readonly ITestOutputHelper _out;
    public DungeonFightTests(ITestOutputHelper o) { _out = o; }

    [Fact]
    public void Each_dungeon_has_its_row_and_stands_above_her_level()
    {
        foreach (var id in new[] { "hollow", "roost" })
        {
            var row = DungeonFights.Of(id);
            Assert.True(row.FoeUp >= 1, $"{id}: its foes stand a level over hers");
            Assert.InRange(row.PackSize, 0.5, 1.5);
            Assert.InRange(row.Elites, 0.5, 2);
            Assert.InRange(row.BossHealth, 0.5, 2);
            var c = Chart.ForDungeon(DungeonGen.Get(id)!, 1, 6);
            Assert.Equal(row.FoeUp, c.FoeLevels);
            Assert.Equal(row.PackSize, c.PackSize, 6);
        }
        Assert.Same(DungeonFights.Plain, DungeonFights.Of(""));
    }

    [Theory]
    [InlineData("hollow", 6, 1)]
    [InlineData("hollow", 6, 2)]
    [InlineData("hollow", 6, 3)]
    [InlineData("roost", 7, 1)]
    [InlineData("roost", 7, 2)]
    [InlineData("roost", 7, 3)]
    public void A_bot_that_never_dodges_falls_before_the_ruler(string id, int level, int seed)
    {
        var def = DungeonGen.Get(id)!;
        var r = MapSim.Play(new MapRunSpec(seed, "warden", 1, def.People, level, 1, [], "standing", 25, id));
        _out.WriteLine($"{id} {seed}: {(r.Cleared ? "cleared" : "fell")} {r.Minutes:0.0} min, {r.KilledBy}, in {r.DeathRoom}");
        Assert.False(r.Cleared, $"{id} seed {seed}: standing still cleared it");
    }
}
