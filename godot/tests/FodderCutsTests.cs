using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 m2) The harness's cuts per fodder (RunMeter's FodderCuts): the grip's cuts landed on a body before
/// it died, read from Ev.Hit.Weapon (the skill that landed the hit, set where the hit is made).</summary>
public sealed class FodderCutsTests
{
    const double Dt = 1 / 60.0;

    static Battle Fight()
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = [("sunder", 1)], Ability = AbilityKind.ShieldBash,
        });
        b.Calling = "warden";
        b.Weapons[0].Timer = 0;
        return b;
    }

    static Enemy Foe(Battle b)
    {
        var e = b.SpawnEnemy("footpad", b.Player.X + 2, b.Player.Z)!;
        e.Hp = e.MaxHp = 1e9;
        e.AttackT = e.RangedT = 999;
        return e;
    }

    /// <summary>A fodder body takes three of the held Sunder's cuts, then a hit from another skill kills it: it counts
    /// three. A second body killed by the other skill alone is fodder no cut touched. The run line says both.</summary>
    [Fact]
    public void A_fodder_killed_by_three_cuts_and_a_stray_hit_counts_three()
    {
        var b = Fight();
        Assert.True(b.Campaign);
        var w = b.Weapons[0];
        Assert.True(w.Hold && w.Chained);
        var other = new WeaponInst("groundbreaker", 1, 1);
        var meter = new RunMeter();
        var p = b.Player;
        var foe = Foe(b);
        Assert.False(foe.Elite || foe.Boss);
        int id = foe.Id, cutsSeen = 0;
        double t = 0;
        void Read()
        {
            var evs = b.Events.Drain().ToList();
            // (the field is set where the hit is made: the grip's own hits say "sunder")
            cutsSeen += evs.Count(e => e is Ev.Hit { Weapon: "sunder", Dot: false } h && h.Target == id);
            meter.Step(b, t, Dt, evs, true);
        }
        for (int i = 0; i < 600 && cutsSeen < 3; i++)
        {
            foe.X = p.X + 2; foe.Z = p.Z; foe.Vx = foe.Vz = 0;
            b.HoldSkill(w.Slot, true, foe.X, foe.Z);
            b.Tick(Dt, 0, 0);
            t += Dt;
            Read();
        }
        Assert.Equal(3, cutsSeen);
        Assert.True(foe.Alive && foe.State != EnemyState.Dying);
        b.HoldSkill(w.Slot, false);
        // the stray hit, by another skill, is the one that kills it
        foe.Hp = 1;
        b.HitEnemy(foe, 1e6, School.Physical, [Tag.Physical], new HitOpts { Weapon = other, NoCrit = true });
        var last = b.Events.Drain().ToList();
        var hit = Assert.Single(last.OfType<Ev.Hit>(), h => h.Target == id);
        Assert.Equal("groundbreaker", hit.Weapon);
        var kill = Assert.Single(last.OfType<Ev.Kill>(), k => k.Enemy == id);
        Assert.True(kill.ByPlayer && !kill.Elite && !kill.Boss);
        meter.Step(b, t, Dt, last, true);
        // a second body, never cut: the other skill alone; and a hit with no weapon carries none
        var two = Foe(b);
        two.Hp = 1;
        b.HitEnemy(two, 1e6, School.Physical, [Tag.Physical], new HitOpts { Weapon = other, NoCrit = true });
        var three = Foe(b);
        b.HitEnemy(three, 5, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        last = b.Events.Drain().ToList();
        Assert.Null(Assert.Single(last.OfType<Ev.Hit>(), h => h.Target == three.Id).Weapon);
        meter.Step(b, t, Dt, last, true);
        var m = new RunMeasures();
        meter.Finish(b, t, m);
        Assert.EndsWith(" cuts/fodder mean 3.00 med 3 n 1 uncut 1", m.Grip);
        // (b6: the harness-only source split follows the grip's column, and is the run line's last)
        Assert.EndsWith(m.Grip + " " + m.Src, m.Line());
        Assert.Matches(@"^src sunder n [\d.]+ sh [\d.]+ hx [-\d.]+ rest [-\d.]+ ans [\d.]+ unb [\d.]+ unpaid [-\d.]+ whiff [\d.]+ inv [\d.]+ reachw [\d.]+$", m.Src);
        // (the grip's column still leads it, its two counts before this one)
        Assert.Matches(@"^grip holds .* gaps \d+ whiff \d+ opens \d+ drop \d+ cutw [\d.]+ bank [\d.]+ fmin [\d.]+ cuts/fodder ", m.Grip);
    }

    /// <summary>The count by its parts: a status tick, a Flare's hit and another skill's are no cuts; an elite's death and
    /// a death not the survivor's are not told; a body spawned into a dead one's slot starts at none.</summary>
    [Fact]
    public void Only_the_grips_own_hits_on_fodder_the_survivor_killed_are_counted()
    {
        var c = new FodderCuts();
        static Ev.Hit Hit(int on, string? by, bool dot = false, bool flare = false) => new() { Target = on, Amount = 5, Weapon = by, Dot = dot, ByFlare = flare };
        Assert.True(FodderCuts.IsCut(Hit(1, "sunder")) && FodderCuts.IsCut(Hit(1, "oathblade")));
        Assert.False(FodderCuts.IsCut(Hit(1, "groundbreaker")) || FodderCuts.IsCut(Hit(1, null)) || FodderCuts.IsCut(Hit(1, "sunder", dot: true)) || FodderCuts.IsCut(Hit(1, "sunder", flare: true)));
        // body 1: two cuts (one of each grip), a tick, a Flare's hit: two
        foreach (var ev in new CombatEvent[] { Hit(1, "sunder"), Hit(1, "sunder", dot: true), Hit(1, "oathblade"), Hit(1, null, flare: true), new Ev.Kill { Enemy = 1, ByPlayer = true } }) c.Read(ev);
        Assert.Equal([2], c.Counts);
        // an elite, a boss, a death not hers: cut, not told; their counts are cleared
        c.Read(Hit(2, "sunder")); c.Read(new Ev.Kill { Enemy = 2, ByPlayer = true, Elite = true });
        c.Read(Hit(3, "sunder")); c.Read(new Ev.Kill { Enemy = 3, ByPlayer = true, Boss = true });
        c.Read(Hit(4, "sunder")); c.Read(new Ev.Kill { Enemy = 4, ByPlayer = false });
        Assert.Equal([2], c.Counts);
        Assert.Equal(0, c.Uncut);
        // a body cut once that left without a death, then a new body in its slot, cut four times
        c.Read(Hit(5, "sunder")); c.Read(new Ev.Spawn { Enemy = 5 });
        for (int i = 0; i < 4; i++) c.Read(Hit(5, "sunder"));
        c.Read(new Ev.Kill { Enemy = 5, ByPlayer = true });
        // the Flare's kill of a cut body is left out; of an uncut one, it is fodder no cut touched
        c.Read(Hit(6, "sunder")); c.Read(new Ev.Kill { Enemy = 6, ByPlayer = true, ByFlare = true });
        c.Read(new Ev.Kill { Enemy = 7, ByPlayer = true });
        Assert.Equal([2, 4], c.Counts);
        Assert.Equal(1, c.Uncut);
        Assert.Equal("cuts/fodder mean 3.00 med 4 n 2 uncut 1", c.Line());
        Assert.Equal("cuts/fodder mean - med - n 0 uncut 0", new FodderCuts().Line());
    }
}
