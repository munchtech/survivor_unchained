using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Ledge kills (the owner, 15 Nov): a normal foe forced over an edge dies of it, a real kill with its loot at the ledge; an elite
/// or a boss is carried to the brink and stops there alive; a foe's own movement never takes it over.</summary>
public class LedgeKillTests
{
    const double Dt = 1.0 / 60;

    /// <summary>Ground west of x = 10; a drop (a dungeon's wall) from 10 to 14; she stands at (0, 0).</summary>
    static Battle Edge(int seed = 3)
    {
        var col = new CollisionWorld(120);
        col.AddBox(12, 0, 2, 30, 0, new ColliderOpts(Tag: "wall", Drop: true));
        var b = new Battle(new BattleSetup { Seed = (uint)seed, Collision = col, Combat = true, Campaign = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash });
        b.Hooks.OnLoot = e => [new Loot(PickupKind.Item, "ember_shard", 1), new Loot(PickupKind.Item, "bone_amulet", 1), new Loot(PickupKind.Material, "wolf_pelt", 2)];
        return b;
    }

    static void Run(Battle b, double secs) { for (int i = 0; i < secs / Dt; i++) b.Tick(Dt, 0, 0); }

    [Fact]
    public void A_normal_foe_knocked_over_an_edge_dies_credited_with_loot_at_the_ledge()
    {
        var b = Edge();
        var e = b.SpawnEnemy("risen", 8.5, 1, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!;
        var kills = new List<Ev.Kill>();
        e.Kbx = 45;
        for (int i = 0; i < 90; i++) { b.Tick(Dt, 0, 0); foreach (var ev in b.Events.Drain()) if (ev is Ev.Kill k) kills.Add(k); }
        Assert.Equal(EnemyState.Dying, e.State);
        Assert.True(e.Fell);
        Assert.Equal(1, b.LedgeKillCount);
        Assert.Equal(1, b.KillCount);
        Assert.Single(kills);
        Assert.True(kills[0].ByPlayer && kills[0].Fell);
        var loot = b.Pickups.Items.Where(p => p.Alive && p.Kind is PickupKind.Item or PickupKind.Material).ToList();
        Assert.Equal(3, loot.Count);
        foreach (var p in b.Pickups.Items.Where(p => p.Alive))
        {
            Assert.True(p.X < 10 - 0.3, $"pickup at {p.X:0.00} is not on the near ground");
            Assert.False(b.Collision.Blocked(p.X, p.Z, 0.2), "a drop lies in solid");
            Assert.True(Math.Abs(p.X - e.FellX) < 4 && Math.Abs(p.Z - e.FellZ) < 4, "within a few metres of the crossing");
        }
    }

    [Fact]
    public void An_elite_and_a_boss_are_carried_to_the_brink_and_stay_alive()
    {
        foreach (var kind in new[] { "elite", "boss" })
        {
            var b = Edge();
            var e = b.SpawnEnemy("risen", 8.5, 1, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Elite = kind == "elite", Boss = kind == "boss" })!;
            var brinks = new List<Ev.Brink>();
            e.Kbx = 90;
            double far = 0;
            for (int i = 0; i < 120; i++) { b.Tick(Dt, 0, 0); far = Math.Max(far, e.X); if (i < 30) e.Kbx = Math.Max(e.Kbx, 20); foreach (var ev in b.Events.Drain()) if (ev is Ev.Brink br) brinks.Add(br); }
            Assert.True(e.Alive && e.State != EnemyState.Dying, kind);
            Assert.Equal(0, b.LedgeKillCount);
            Assert.False(e.Fell);
            Assert.True(e.X < 10.0 && !b.Collision.InDrop(e.X, e.Z), $"{kind} stands on the ground at the brink, x={e.X:0.00}");
            Assert.True(far > 9.0, $"{kind} was carried to the edge, furthest x={far:0.00}");
        }
    }

    [Fact]
    public void A_foes_own_charge_at_an_edge_does_not_kill_it_and_she_never_goes_over()
    {
        var col = new CollisionWorld(120);
        col.AddBox(12, 0, 2, 30, 0, new ColliderOpts(Tag: "wall", Drop: true));
        var b = new Battle(new BattleSetup { Seed = 4, Collision = col, Combat = true, Campaign = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash });
        b.Player.X = 17; b.Player.Z = 0;
        var e = b.SpawnEnemy("boar", 4, 0, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!;
        for (int i = 0; i < 600; i++)
        {
            b.Tick(Dt, i % 120 < 60 ? -1 : 0, 0);   // she presses toward the drop now and then
            Assert.False(col.InDrop(b.Player.X, b.Player.Z));
        }
        Assert.Equal(0, b.LedgeKillCount);
        Assert.False(e.Fell);
    }

    [Fact]
    public void With_the_rule_off_a_foe_stops_at_the_wall()
    {
        var b = Edge();
        var e = b.SpawnEnemy("risen", 8.5, 1, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!;
        b.LedgeKills = false;
        e.Kbx = 45;
        Run(b, 1.5);
        Assert.True(e.Alive && e.State != EnemyState.Dying);
        Assert.False(b.Collision.InDrop(e.X, e.Z));
        Assert.Equal(0, b.LedgeKillCount);
    }

    [Fact]
    public void The_same_seed_falls_the_same_way()
    {
        string One()
        {
            var b = Edge(9);
            for (int k = 0; k < 6; k++) b.SpawnEnemy("risen", 8 + k * 0.3, -2 + k, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!.Kbx = 40 + k * 3;
            Run(b, 2);
            return $"{b.LedgeKillCount}/{b.KillCount}/" + string.Join(",", b.Pickups.Items.Where(p => p.Alive).Select(p => $"{p.X:0.000}:{p.Z:0.000}"));
        }
        Assert.Equal(One(), One());
    }

    [Fact]
    public void A_ledge_kill_is_the_pushing_skills_kill_and_damage()
    {
        var b = Edge();
        var w = b.Weapons.First(x => x.Id == "oathblade");
        var e = b.SpawnEnemy("risen", 8.5, 1, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!;
        int kills0 = w.Kills;
        b.HitEnemy(e, 1, School.Physical, [Tag.Melee], new HitOpts { Weapon = w, Knockback = 3, DirX = 1, NoProcs = true });
        Assert.True(e.Alive && e.State != EnemyState.Dying, "the blow alone does not kill it");
        Assert.Equal("oathblade", e.KbBy);
        double left = e.Hp, dealt = b.DamageBy.GetValueOrDefault("oathblade");
        Run(b, 1.5);
        Assert.True(e.Fell, "the push carried it over");
        Assert.Equal(kills0 + 1, w.Kills);
        Assert.Equal(dealt + left, b.DamageBy.GetValueOrDefault("oathblade"), 3);
        Assert.False(b.DamageBy.ContainsKey("other"), "nothing of the fall is credited to no one");
    }
}

