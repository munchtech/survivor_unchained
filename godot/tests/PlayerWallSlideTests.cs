using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The player's velocity is what the walls let her do: pressed into one she stands, along one she slides.</summary>
public class PlayerWallSlideTests
{
    static Battle WithWall()
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 140, [Stat.Regen] = 0, [Stat.Armor] = 2, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4,
            [Stat.CritChance] = 0.05, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        var col = new CollisionWorld(120);
        col.AddBox(10, 0, 1, 25); // a wall across x = 9..11
        var b = new Battle(new BattleSetup { Seed = 3, Collision = col, Combat = true, Stats = s, Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash });
        b.Player.X = 5; b.Player.Z = 0;
        return b;
    }

    static void Run(Battle b, double mx, double mz, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0) { b.Tick(1 / 60.0, mx, mz); b.Events.Drain(); b.Player.Hp = b.MaxHp; }
    }

    [Fact]
    public void Straight_into_a_wall_she_stands()
    {
        var b = WithWall();
        Run(b, 1, 0, 3);
        var p = b.Player;
        Assert.True(Math.Abs(p.Vx) < 0.05 && Math.Abs(p.Vz) < 0.05, $"v=({p.Vx},{p.Vz}) x={p.X}");
        Assert.False(p.Moving);
    }

    [Fact]
    public void Diagonal_into_a_wall_she_slides_along_it()
    {
        var b = WithWall();
        Run(b, 1, 1, 3); // reaches the wall, keeps going along it (z)
        var p = b.Player;
        double speed = 5, along = speed * Math.Sin(Math.PI / 4);
        Assert.True(p.X < 9, $"x={p.X}");
        Assert.True(p.Vz > 0.5 * along, $"vz={p.Vz}");
        Assert.True(p.Moving);
    }

    [Fact]
    public void Open_ground_speed_is_unchanged()
    {
        var b = WithWall();
        Run(b, -1, 0, 1.5);
        var p = b.Player;
        Assert.True(Math.Abs(p.Vx) > 4.5, $"vx={p.Vx}");
        Assert.True(p.Moving);
    }
}
