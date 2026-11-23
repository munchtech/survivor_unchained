using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(the owner, 22 Nov: "the ironhide mobs are still stupidly strong. it seemingly is a bad mechanic"; asked what should
/// happen to the den's iron-skinned champions: "Keep, no blocking") In the den no champion turns or cuts a blow: the Ironbound
/// sign is never worn there. The mechanic itself stays where it is taught or ruled (prologue, Oath of Iron, IronboundTests).</summary>
[Collection("Balance")]
public class DenNoIronTests
{
    static (MapRun Zone, Battle B) Den(int seed)
    {
        var chart = Chart.ForDungeon(DungeonGen.Get("hollow")!, seed, 6);
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
        zone.PlaceAll();
        return (zone, b);
    }

    [Fact]
    public void No_champion_the_den_spawns_has_a_blow_turned_or_cut_by_iron()
    {
        int signed = 0, champions = 0;
        for (int seed = 1; seed <= 40; seed++)
        {
            var (_, b) = Den(seed);
            foreach (var e in b.Enemies.Living())
            {
                if (e.Def.Signs.Length > 0) signed++;
                if (e.Def.Signs.Length > 0 || e.Elite) champions++;
                Assert.DoesNotContain("ironbound", e.Def.Signs);
                Assert.True(e.Def.IronSkin <= 0, $"seed {seed}: {e.Def.Id} ({e.Def.Name}) has IronSkin {e.Def.IronSkin}");
            }
        }
        Assert.True(signed > 0 && champions > 0, "no signed champion met: the test saw nothing");
    }
}
