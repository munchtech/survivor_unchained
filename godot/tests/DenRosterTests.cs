using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(P3, docs/design/DEN_ROSTER.md section 3) The den's roster: its packs are recipes, its foes have one move each,
/// and nowhere else is the table's row changed.</summary>
[Collection("Balance")]
public class DenRosterTests
{
    sealed record Run(MapRun Zone, Battle B);

    static Run Open(Chart chart)
    {
        var j = MapSim.Survivor("warden", 6, 2, 3);
        var map = MapGen.Generate(chart.Map);
        var host = new HeadlessHost(j, 3);
        var zone = new MapRun(host, map, chart);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 3);
        b.Hooks = BattleHooks.Following(zone.Hooks);
        var zh = zone.Hooks;
        b.Hooks.OnPickup = p => (zh.OnPickup == null || zh.OnPickup(p)) && j.PickedUp(p);
        host.Battle = b;
        zone.Begin(b);
        return new Run(zone, b);
    }

    static Run Den(int seed)
    {
        var r = Open(Chart.ForDungeon(DungeonGen.Get("hollow")!, seed, 6));
        r.Zone.PlaceAll();
        return r;
    }

    static readonly string[] Telegraphed = ["boar", "wolf_blighted", "boar_slurry", "boar_ironback", "wolf_howler"];

    [Fact]
    public void The_dens_packs_are_all_recipes_and_at_most_one_foe_in_three_is_telegraphed()
    {
        var ids = DenRoster.Recipes.Select(x => x.Id).ToHashSet();
        int seen = 0;
        for (int seed = 1; seed <= 6; seed++)
            foreach (var (recipe, _, defs) in Den(seed).Zone.PackMakeup)
            {
                seen++;
                Assert.Contains(recipe, ids);
                int tele = defs.Count(d => Telegraphed.Contains(d));
                Assert.True(tele * 3 <= defs.Count, $"seed {seed} {recipe}: {tele} of {defs.Count} telegraphed");
            }
        Assert.True(seen > 0);
    }

    [Fact]
    public void Over_six_dens_every_kind_of_the_roster_is_fielded()
    {
        var seen = new HashSet<string>();
        for (int seed = 1; seed <= 6; seed++)
            foreach (var (_, _, defs) in Den(seed).Zone.PackMakeup) foreach (var d in defs) seen.Add(d);
        foreach (var kind in new[] { "wolf", "wolf_runner", "wolf_blighted", "boar", "boar_slurry", "wolf_howler", "boar_ironback" })
            Assert.Contains(kind, seen);
    }

    [Fact]
    public void The_cut_changes_the_dens_kinds_and_never_the_table()
    {
        var wolfRunner = Enemies.Get("wolf_runner");
        Assert.Equal(Behavior.Orbit, wolfRunner.Behavior);
        Assert.Equal(26, wolfRunner.Health);
        Assert.NotNull(wolfRunner.Lunge);

        var live = new List<Enemy>();
        for (int seed = 1; seed <= 6; seed++) live.AddRange(Den(seed).B.Enemies.Living());
        var runner = live.First(e => e.Def.Id == "wolf_runner").Def;
        Assert.Equal(Behavior.Chase, runner.Behavior);
        Assert.Null(runner.Lunge);
        Assert.Equal(14, runner.Health);
        var sick = live.First(e => e.Def.Id == "wolf_blighted").Def;
        Assert.Equal(Behavior.Ranged, sick.Behavior);
        Assert.True(sick.Ranged!.Lob);
        Assert.Equal(0.6, sick.Ranged.Aim);
        Assert.NotNull(sick.Burst);
        Assert.NotNull(live.First(e => e.Def.Id == "boar").Def.Charge);
        Assert.Equal(2.8, live.First(e => e.Def.Id == "boar_ironback").Def.Slam!.Radius);
    }

    [Fact]
    public void Only_the_den_battle_carries_a_roster()
    {
        var den = Open(Chart.ForDungeon(DungeonGen.Get("hollow")!, 1, 6));
        Assert.NotNull(den.B.Roster);
        var map = Open(new Chart { Tier = 1, People = "pack", Seed = 1234, Mods = new List<string>(), Name = "The Test Map" });
        Assert.Null(map.B.Roster);
    }
}
