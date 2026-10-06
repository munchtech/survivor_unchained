using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>What a whole Wayfinder's map pays crafting (docs/CRAFTING_DESIGN.md 20.1): iron and bases,
/// the people's own from what carries it, and never the scars' fire in bulk; and nothing the ruler
/// leaves is lost with the map.</summary>
[Collection("Balance")]
public class AtlasPayTests
{
    static (Journey J, HeadlessHost Host, MapRun Zone, Battle B) Cleared(string people, int tier = 4)
    {
        var j = MapSim.Survivor("warden", 16, 2, 3);
        var chart = new Chart { Tier = tier, People = people, Seed = 1234, Name = "The Test Map" };
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
        Step(zone, b, host, 0.5);
        zone.ClearNow();
        // (she stands still: only the gold comes to her; the rest lies where it fell)
        Step(zone, b, host, 2);
        zone.Leave();
        return (j, host, zone, b);
    }

    static void Step(MapRun zone, Battle b, HeadlessHost host, double seconds)
    {
        for (double t = 0; t < seconds && !zone.Over; t += 1 / 60.0)
        {
            zone.Step(1 / 60.0);
            zone.Frame(1 / 60.0);
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            host.Pass(1 / 60.0);
        }
    }

    [Theory]
    [InlineData("pack")]
    [InlineData("dead")]
    [InlineData("kerchiefs")]
    public void A_map_pays_its_peoples_own_from_what_carries_it_not_from_every_kill(string people)
    {
        var (j, _, zone, _) = Cleared(people);
        Assert.True(zone.Cleared && zone.Over);
        int own = Crafting.NightMaterials(people).Where(m => m != Crafting.Shard).Sum(m => Inventory.Count(j.Ch, m));
        // A quarter of every kill paid 75-100 a map; from its carriers it is a pin's or a few work-ins' worth.
        Assert.InRange(own, 5, 40);
        Assert.True(zone.Kills > 100, $"only {zone.Kills} slain");
    }

    [Fact]
    public void The_Digs_lamplings_pay_their_iron_in_the_atlas_and_leave_the_fire_to_the_scars()
    {
        var (j, _, _, _) = Cleared("lamplings");
        // (a trickle from the carriers' rolls that are not gear, never the 73 a map the kills paid)
        Assert.InRange(Inventory.Count(j.Ch, Crafting.Shard), 0, 4);
        Assert.True(Inventory.Count(j.Ch, Crafting.Iron) >= 5, $"{Inventory.Count(j.Ch, Crafting.Iron)} old iron");
    }

    [Fact]
    public void What_the_ruler_leaves_comes_home_though_she_never_walked_over_it()
    {
        // The ruler's charts fell where it died, across the map from her; left lying, they were lost.
        var (j, _, _, _) = Cleared("pack", tier: 7);
        Assert.Contains(j.Ch.Satchel, i => i.Chart != null);
    }
}
