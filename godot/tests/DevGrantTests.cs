using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3) A dev grant on a campaign survivor whose taught build fills the six keys (Sim/DevGrants.cs): the union is
/// carried on two keys, the grip stays on the first.</summary>
public class DevGrantTests
{
    [Fact]
    public void A_union_granted_on_six_full_keys_takes_two_and_the_grip_stays()
    {
        var j = MapSim.Survivor("warden", 30, 2, 5);
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        Assert.True(b.Campaign);
        var taught = TaughtBuilds.Of("warden")!;
        Assert.Equal(Weapons.MaxWeapons, b.SlotsUsed);
        var grip = b.Weapons.Single(w => w.Id == taught.Grip);
        Assert.Equal(0, grip.Slot);
        // (the bare grant is refused: no two keys free)
        Assert.Null(b.GrantUnion("bladestorm"));

        var said = DevGrants.Apply(b, null, "bladestorm", null);

        var u = Unions.Find("bladestorm")!;
        var storm = b.Weapons.Single(w => w.Id == u.Into);
        Assert.True(storm.Slot >= 0 && storm.Slot2 >= 0 && storm.Slot != storm.Slot2);
        Assert.Contains(said, l => l.StartsWith("grant-union: bladestorm on slots"));
        Assert.True(b.SlotsUsed <= Weapons.MaxWeapons);
        // The grip is still carried on the first key, or is the union's own part (then the union answers its key).
        var gripNow = b.Weapons.Find(w => w.Id == taught.Grip);
        if (taught.Grip == u.A || taught.Grip == u.B) Assert.True(storm.Slot == 0 || storm.Slot2 == 0);
        else { Assert.NotNull(gripNow); Assert.Equal(0, gripNow!.Slot); }
        // A second ask changes nothing more.
        int carried = b.Weapons.Count;
        Assert.Contains(DevGrants.Apply(b, null, "bladestorm", null), l => l.StartsWith("grant-union: bladestorm already carried on slots"));
        Assert.Equal(carried, b.Weapons.Count);
        Assert.Contains(DevGrants.Apply(b, "no_such_skill", "no_such_union", null), l => l == "grant: no_such_skill not added (no such skill)");
    }
}
