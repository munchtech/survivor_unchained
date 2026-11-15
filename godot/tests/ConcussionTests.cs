using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Shield Bash's Concussion facet (Content/Abilities.cs: "Stuns last a second longer"), held in the real fight:
/// the bash fires as a calling's reflex (the only way it fires), once with the facet and once without, on the same seed,
/// so the two fights differ by the facet alone.</summary>
public sealed class ConcussionTests
{
    const double Frame = 1 / 60.0;

    static Battle Arena(params string[] facets)
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 200, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4, [Stat.CritChance] = 0, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        return new Battle(new BattleSetup { Seed = 5, Collision = new CollisionWorld(120), Combat = true, Stats = s, Weapons = [], Ability = AbilityKind.ShieldBash, Facets = facets.ToList() });
    }

    /// <summary>A creature that stands and takes it, with no blow of its own in the test, too tough to fall to the bash.</summary>
    static Enemy Foe(Battle b, double x, double z, bool boss = false)
    {
        var e = b.SpawnEnemy("risen", x, z)!;
        e.MaxHp = e.Hp = 1e6;
        e.AttackT = e.RangedT = 99;
        e.Boss = boss;
        return e;
    }

    /// <summary>The bash wired as a reflex: it goes on the next sense tick, once (its lamp's wait outlasts the test).</summary>
    static void Bash(Battle b)
    {
        var l = new LampLoadout();
        l.Reflexes.Add(new ReflexDef("shield_bash", "every", 99, null));
        b.SetLamps(l);
        b.Tick(Frame, 0, 0);
        b.Events.Drain();
        Assert.Equal(1, b.Reflexes.Single().Fired);
    }

    static void Tick(Battle b, double seconds)
    {
        for (double t = 0; t < seconds - 1e-9; t += Frame) { b.Tick(Frame, 0, 0); b.Events.Drain(); }
    }

    static double StunLeft(Enemy e) => e.Status[StatusKind.Stun]?.T ?? 0;

    [Fact]
    public void Concussion_holds_the_stun_a_second_longer()
    {
        var plain = Arena();
        var conc = Arena("concussion");
        var a = Foe(plain, 2, 0);
        var c = Foe(conc, 2, 0);
        Bash(plain);
        Bash(conc);
        // The bash's own stun is 1.5 s; with Concussion it is a second more, on the same frame of the same fight.
        Assert.InRange(StunLeft(a), 1.5 - 2 * Frame, 1.5);
        Assert.Equal(StunLeft(a) + 1.0, StunLeft(c), 6);

        // And the creature is held by it: at 2 s the plain stun is over, the concussed one still holds.
        Tick(plain, 2.0);
        Tick(conc, 2.0);
        Assert.False(a.Status.Has(StatusKind.Stun));
        Assert.True(c.Status.Has(StatusKind.Stun), $"stun left {StunLeft(c):0.000} s");
        // By 2.6 s the concussed one is free again (a second more, not more than that).
        Tick(conc, 0.6);
        Assert.False(c.Status.Has(StatusKind.Stun));
    }

    [Fact]
    public void Concussion_adds_its_second_to_the_stagger_a_boss_takes_from_the_bash()
    {
        // A boss is not locked: the bash's stun (0.6 s for a boss) fills its stagger bar (0.06 + 0.12 a second of stun).
        // Concussion's second is the bar's 0.12 more, the rest of the two fights alike.
        var plain = Arena();
        var conc = Arena("concussion");
        var a = Foe(plain, 2, 0, boss: true);
        var c = Foe(conc, 2, 0, boss: true);
        Bash(plain);
        Bash(conc);
        Assert.False(a.Status.Has(StatusKind.Stun));
        Assert.False(c.Status.Has(StatusKind.Stun));
        Assert.True(a.Stagger > 0);
        Assert.Equal(a.Stagger + 0.12 * 1.0 * plain.Rules.StaggerTaken, c.Stagger, 6);
    }
}
