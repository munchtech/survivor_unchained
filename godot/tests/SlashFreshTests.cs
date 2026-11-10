using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(P7 lead 9) A cut's struck are its DISTINCT bodies: Ev.Slash.Fresh is how many of an arc's Struck no earlier
/// arc of the same swing had struck, so Fresh summed over a swing's arcs is the bodies the swing hit.</summary>
public sealed class SlashFreshTests
{
    static StatBlock Stats()
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 1e6, [Stat.Regen] = 0, [Stat.Armor] = 2, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4,
            [Stat.CritChance] = 0.05, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        return s;
    }

    /// <summary>Her first swing through a crowd standing close in front of her: its Slash events and the distinct creatures hit in that tick.</summary>
    static (List<Ev.Slash> Slashes, int Bodies) Swing(int extraArcs)
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 1, Collision = new CollisionWorld(120), Combat = true, Stats = Stats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
        });
        b.Weapons[0].Mods.Projectiles += extraArcs;
        double x = b.Player.X, z = b.Player.Z;
        for (int i = 0; i < 24; i++)
        {
            double a = 6.2832 * i / 24, r = 0.9 + 0.5 * (i % 3);
            var e = b.SpawnEnemy("risen", x + r * System.Math.Cos(a), z + r * System.Math.Sin(a))!;
            e.MaxHp = e.Hp = 1e9; e.Speed = 0;
        }
        for (int t = 0; t < 400; t++)
        {
            b.Tick(0.02, 0, 0);
            var evs = b.Events.Drain().ToList();
            var slashes = evs.OfType<Ev.Slash>().ToList();
            if (slashes.Count > 0) return (slashes, evs.OfType<Ev.Hit>().Where(h => !h.Dot).Select(h => h.Target).Distinct().Count());
        }
        throw new Xunit.Sdk.XunitException("she never swung");
    }

    [Fact]
    public void A_swing_of_three_arcs_counts_its_distinct_bodies_in_Fresh()
    {
        var (slashes, bodies) = Swing(2);
        Assert.Equal(3, slashes.Count);
        Assert.True(bodies > 0);
        Assert.All(slashes, s => Assert.InRange(s.Fresh, 0, s.Struck));
        Assert.Equal(slashes[0].Struck, slashes[0].Fresh);
        Assert.Equal(bodies, slashes.Sum(s => s.Fresh));
        // (the arcs overlap, so the old sum overcounted)
        Assert.True(slashes.Sum(s => s.Struck) > bodies);
    }

    [Fact]
    public void A_single_arc_swing_has_Fresh_equal_to_Struck()
    {
        var (slashes, bodies) = Swing(0);
        var s = Assert.Single(slashes);
        Assert.True(s.Struck > 0);
        Assert.Equal(s.Struck, s.Fresh);
        Assert.Equal(bodies, s.Fresh);
    }
}
