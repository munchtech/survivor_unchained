using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L3, found fixing SU-056) Her missiles home on a lifetime everywhere, not only on reflections: a target whose
/// slot is reused in flight does not draw the missile to the newcomer; it picks its own (here the nearer foe).</summary>
public sealed class HomingLifetimeTests
{
    [Fact]
    public void A_slot_reused_in_flight_does_not_draw_her_missile()
    {
        var b = BattleTests.Arena(4);
        double px = b.Player.X, pz = b.Player.Z;
        var target = b.SpawnEnemy("risen", px, pz + 8)!;
        var pr = b.SpawnProjectile(Side.Player, px, pz, 10, School.Physical)!;
        pr.Speed = 10; pr.Vx = 10; pr.Vz = 0; pr.Homing = 3; pr.Life = 2;
        pr.Home(target);
        b.Enemies.Release(target);
        var newcomer = b.SpawnEnemy("risen", px, pz + 8)!;
        Assert.Equal(target.Id, newcomer.Id);
        var nearer = b.SpawnEnemy("risen", px + 4, pz - 3)!;
        Assert.NotEqual(newcomer.Id, nearer.Id);
        b.Tick(1 / 60.0, 0, 0);
        // old: Enemies.Items[Target] was the newcomer, so it turned up toward it; now it re-picks the nearer foe
        Assert.True(pr.Vz < 0, $"Vz {pr.Vz}");
        Assert.Equal(nearer.Id, pr.Target);
    }
}
