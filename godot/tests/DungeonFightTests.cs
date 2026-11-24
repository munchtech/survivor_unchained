using System;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The dungeons' fight numbers (data/content/dungeon_fights.json; dungeon-fights lane, 15 Nov). The 50-seed bands live in
/// the harness (`dotnet run --project godot/balance -- dungeon --seeds 50`): hollow human 88% deft 98% standing 0%, roost human 86%
/// deft 98% standing 0% (seeds 1-50; 51-100: 88/98, 84/98; castMove off). Here the rule in three seeds: a bot that never moves falls, the deft one clears.
/// (P3, 22 Nov, the den's own roster, DEN_ROSTER.md) hollow seeds 1-50 at den-roster eb0a397c7: human 96% deft 100% standing 2% (the human's
/// 96% predates P3: 96% at 0c62da9bb); its clear feel by `denfeel --seeds 20`: a normal pack p50 11-13 s, the hunting pack 6.4-6.9 s.
/// (P3, 23 Nov, 7a8f97ea3) hollow seeds 1-50 after the ruler's holds read true (ArenaBoss StateT, a4fdfb286) and bossKit 1.4:
/// deft/human/standing L9 gear 2 (the owner's) 90/84/2%, L6 gear 1 90/86/2%; ruler TTK 114-125 s.</summary>
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

    /// <summary>(P3, DEN_ROSTER.md "Clear-feel targets") The den clears as the page asks, in three seeds of the deft bot (the 20-seed
    /// numbers in the class summary): a normal pack goes down within 10 s of her first blow on it (median), most packs drop
    /// 40% of themselves inside one 1.5 s window, and a red lane comes no more than once in 8 s of room fighting.</summary>
    [Fact]
    public void The_den_clears_inside_the_pages_feel_targets()
    {
        var runs = Enumerable.Range(1, 3).Select(seed => DenFeel.Play(new MapRunSpec(seed, "warden", 1, DungeonGen.Get("hollow")!.People, 6, 1, [], "deft", 8, "hollow"))).ToList();
        var packs = runs.SelectMany(r => r.Packs).Where(p => p.Killed && p.FirstHit >= 0).ToList();
        var normal = packs.Where(p => p.Grade == 0).Select(p => p.LastDeath - p.FirstHit).OrderBy(x => x).ToList();
        double ttk = normal[normal.Count / 2], together = packs.Count(p => p.Together >= 0.4) / (double)packs.Count;
        double lanes = runs.Sum(r => r.Lanes) / Math.Max(1, runs.Sum(r => r.RoomFight)) * 8;
        _out.WriteLine($"{packs.Count} packs killed; normal TTK p50 {ttk:0.0} s ({normal.Count}); together >=40% {together:P0}; lanes {lanes:0.00} per 8 s");
        Assert.True(normal.Count >= 20, $"only {normal.Count} normal packs killed");
        Assert.True(ttk <= 10, $"a normal pack takes {ttk:0.0} s");
        Assert.True(together >= 0.7, $"{together:P0} of packs fall together");
        Assert.True(lanes <= 1, $"{lanes:0.00} lanes per 8 s");
    }

    /// <summary>Roost seed 16, deft (15 Nov): the Red Hand jammed in the Boss camp's 2.0 m door (his body is 2.2 m across), nothing
    /// reached him, and the run timed out at 25 minutes with 9054 life left. Foes now squeeze through a door a little narrower than they are.</summary>
    [Fact]
    public void The_ruler_does_not_wedge_in_the_boss_camp_door_roost_seed_16()
    {
        var def = DungeonGen.Get("roost")!;
        var r = MapSim.Play(new MapRunSpec(16, "warden", 1, def.People, 7, 1, [], "deft", 25, "roost"));
        _out.WriteLine($"roost 16: {(r.Cleared ? "cleared" : "not cleared")} {r.Minutes:0.0} min, boss ttk {r.BossTtk}, falls {r.Falls}");
        Assert.True(r.Cleared, $"roost seed 16 not cleared in {r.Minutes:0.0} min (falls {r.Falls}, ruler left {r.BossLeft:0.00})");
    }
}
