using System;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>No foe ends a step inside solid (boss-unwedge, 15 Nov): a knockback, a pull or a script's dash that carries a foe into
/// a wall leaves it against the wall, not in it; a foe pinched between pieces that stand closer than its body squeezes through; one
/// set down inside a thick wall is set on the nearest open ground. Roost seed 16: the Red Hand (radius 1.1) jammed in the Boss
/// camp's 2.0 m door and the run timed out at 25 minutes.</summary>
public class FoeSolidTests
{
    const double Dt = 1.0 / 60;

    /// <summary>A footpad grown to a boss's body, far from her, on a map with a few walls.</summary>
    static (Battle B, Enemy E) Rig(Action<CollisionWorld> walls, double x, double z, double radius = 1.1)
    {
        var col = new CollisionWorld(120);
        walls(col);
        var b = new Battle(new BattleSetup { Seed = 3, Collision = col, Combat = true, Campaign = true, Stats = BattleTests.BaseStats(), Weapons = [("sunder", 1)], Ability = AbilityKind.ShieldBash });
        b.Player.X = 40; b.Player.Z = 40;
        var e = b.SpawnEnemy("footpad", x, z)!;
        e.Radius = radius;
        e.Hp = e.MaxHp = 1e9;
        e.AttackT = e.RangedT = 999;
        return (b, e);
    }

    // A long wall across the origin, a foe three metres off it on each side, thrown at the arm it faces tick after tick.
    [Theory]
    [InlineData(0, 3, 0, -1)]
    [InlineData(0, -3, 0, 1)]
    [InlineData(3, 0, -1, 0)]
    [InlineData(-3, 0, 1, 0)]
    public void A_foe_thrown_at_a_wall_from_each_side_stays_out_of_it(double x, double z, double dx, double dz)
    {
        var (b, e) = Rig(c => c.AddBox(0, 0, x != 0 ? 0.5 : 30, x != 0 ? 30 : 0.5), x, z);
        double side = Math.Sign(x != 0 ? x : z);
        for (int i = 0; i < 240; i++)
        {
            if (i % 20 == 0) { e.Kbx = dx * 40; e.Kbz = dz * 40; }
            b.Tick(Dt, 0, 0);
            double depth = b.Collision.Depth(e.X, e.Z, CollisionWorld.WallRadius(e.Radius), true);
            Assert.True(depth <= CollisionWorld.Slop, $"tick {i}: in the wall at ({e.X:0.00},{e.Z:0.00}), depth {depth:0.000}");
            Assert.True(Math.Sign(x != 0 ? e.X : e.Z) == side, $"tick {i}: through the wall to ({e.X:0.00},{e.Z:0.00})");
        }
    }

    [Fact]
    public void A_foe_dropped_inside_a_thick_wall_is_set_on_open_ground()
    {
        // three pieces laid over one another: nearest-face pushes alone leave it in one of them
        var (b, e) = Rig(c => { c.AddBox(0, 0, 3, 0.5); c.AddBox(0, 0.4, 0.5, 3); c.AddBox(0.3, 0, 2, 2); }, 0.1, 0.1);
        b.Tick(Dt, 0, 0);
        double depth = b.Collision.Depth(e.X, e.Z, CollisionWorld.WallRadius(e.Radius), true);
        Assert.True(depth <= CollisionWorld.Slop, $"still in solid at ({e.X:0.00},{e.Z:0.00}), depth {depth:0.000}");
        Assert.True(Math.Abs(e.X) < 8 && Math.Abs(e.Z) < 8, "set down nearby, not flung");
    }

    // The Roost seed 16 jam: two wall corners 2.0 m apart, a body 2.2 m across, the nav grid calling the way open.
    [Theory]
    [InlineData(1.1)]
    [InlineData(1.25)]
    public void A_body_wider_than_a_door_squeezes_through_it(double radius)
    {
        var col = new CollisionWorld(120);
        col.AddBox(0, 3, 0.5, 2); // z 1..5
        col.AddBox(0, -3, 0.5, 2); // z -5..-1: a door 2.0 wide
        double x = -5, z = 0.2;
        for (int i = 0; i < 400 && x < 5; i++)
        {
            x += 0.05; // a walker's step, toward her on the far side
            col.Resolve(ref x, ref z, radius);
            Assert.True(col.Depth(x, z, CollisionWorld.WallRadius(radius)) <= CollisionWorld.Slop, $"step {i}: wedged at ({x:0.00},{z:0.00})");
        }
        Assert.True(x >= 5, $"stopped at the door, x {x:0.00}");
    }

    [Fact]
    public void A_player_is_not_squeezed()
    {
        var col = new CollisionWorld(120);
        col.AddBox(0, 3, 0.5, 2);
        col.AddBox(0, -3, 0.5, 2);
        double x = 0, z = 0;
        col.Resolve(ref x, ref z, 1.1, isPlayer: true);
        Assert.True(col.Depth(x, z, 1.1) > CollisionWorld.Slop, "her own pinch is left as the old push left it");
    }
}


