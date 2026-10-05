using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Marks: what gear inscribes on one skill or one verb (docs/items/CATALOGUE.md §4), worn
/// in the Wayfinder's maps. The first four prove each kind of hook once: a behaviour read by id
/// (the Ravine), a ground on a skill's blast (the Falling Star), a verb's own effect (the Open
/// Gate), a count that grows with the crowd (the Gyre); and numbers on one skill (SkillMods).</summary>
public class MarkTests
{
    static int Launched(Battle b, string weapon, double seconds)
    {
        int n = 0;
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            foreach (var ev in b.Events.Drain()) { }
            n = System.Math.Max(n, b.Projectiles.Living().Count(p => p.Weapon == weapon && p.Owner == Side.Player));
        }
        return n;
    }

    static void Foes(Battle b, params (double X, double Z)[] at)
    {
        foreach (var (x, z) in at)
        {
            var e = b.SpawnEnemy("risen_warrior", b.Player.X + x, b.Player.Z + z, new Battle.SpawnOpts { Level = 1 })!;
            e.MaxHp = e.Hp = 1e6;
            e.Speed = 0;
        }
    }

    [Fact]
    public void The_ravine_looses_a_second_volley_at_the_farthest()
    {
        var plain = BattleTests.Arena(5, ("volley", 1));
        Foes(plain, (3, 0), (12, 2));
        int without = Launched(plain, "volley", 0.6);
        var marked = BattleTests.Arena(5, ("volley", 1));
        marked.Wear(new Dictionary<string, double> { [Marks.Ravine] = 1 }, new Dictionary<string, WeaponMods>());
        Foes(marked, (3, 0), (12, 2));
        int with = Launched(marked, "volley", 0.6);
        Assert.Equal(2 * without, with);
    }

    [Fact]
    public void The_falling_star_leaves_the_cinders_ground_burning()
    {
        var b = BattleTests.Arena(5, ("cinderfall", 1));
        b.Wear(new Dictionary<string, double> { [Marks.FallingStar] = 0 }, new Dictionary<string, WeaponMods>());
        Foes(b, (6, 0));
        bool burning = false;
        for (double t = 0; t < 4 && !burning; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            burning = b.Zones.Living().Any(z => z.Owner == Side.Player && z.School == School.Fire);
        }
        Assert.True(burning);
        var z0 = b.Zones.Living().First(z => z.Owner == Side.Player && z.School == School.Fire);
        // Grade I: two seconds of it.
        Assert.InRange(z0.Life, 1.0, 2.01);
    }

    [Fact]
    public void The_open_gate_leaves_holy_fire_where_the_dash_began()
    {
        var b = BattleTests.Arena(5, ("oathblade", 3));
        Assert.True(b.Dash(1, 0));
        Assert.Empty(b.Zones.Living().Where(z => z.School == School.Holy));
        var m = BattleTests.Arena(5, ("oathblade", 3));
        m.Wear(new Dictionary<string, double> { [Marks.OpenGate] = 1 }, new Dictionary<string, WeaponMods>());
        double x0 = m.Player.X;
        Assert.True(m.Dash(1, 0));
        var ring = m.Zones.Living().Single(z => z.School == School.Holy && z.Owner == Side.Player);
        Assert.Equal(x0, ring.X, 3);
        Assert.Equal(m.Weapons.Max(w => w.Damage) * 0.9, ring.Dps, 3);
    }

    [Fact]
    public void The_gyre_gains_axes_from_the_press_round_it()
    {
        var plain = BattleTests.Arena(5, ("axe_gyre", 1));
        var ring = Enumerable.Range(0, 12).Select(i => (3.5 * System.Math.Cos(i * 0.52), 3.5 * System.Math.Sin(i * 0.52))).ToArray();
        Foes(plain, ring);
        int without = Launched(plain, "axe_gyre", 0.5);
        var marked = BattleTests.Arena(5, ("axe_gyre", 1));
        marked.Wear(new Dictionary<string, double> { [Marks.Gyre] = 1 }, new Dictionary<string, WeaponMods>());
        Foes(marked, ring);
        // Twelve close by at its best (one for every three): three more, its cap.
        Assert.Equal(without + 3, Launched(marked, "axe_gyre", 0.5));
    }

    [Fact]
    public void A_skills_own_numbers_from_gear_come_with_it_into_the_hand()
    {
        var b = BattleTests.Arena(5, ("oathblade", 1));
        double before = b.Weapons[0].Damage;
        var mods = new Dictionary<string, WeaponMods> { ["oathblade"] = new() { Damage = 1.5 }, ["cleaver"] = new() { Projectiles = 1 } };
        b.Wear(new Dictionary<string, double>(), mods);
        Assert.Equal(before * 1.5, b.Weapons[0].Damage, 6);
        // One taken up later carries its own too.
        var c = b.AddWeapon("cleaver")!;
        Assert.Equal(1, c.Mods.Projectiles);
    }
}
