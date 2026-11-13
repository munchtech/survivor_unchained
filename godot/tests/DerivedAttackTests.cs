using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-066) An attack made from another (a split missile, the ground a missile leaves, its
/// splash) takes its parent's context whole: the champion multiplier, the credit, the weapon. And ground or a missile
/// that names a weapon and sets no multiplier of its own strikes a champion with the weapon's.</summary>
public sealed class DerivedAttackTests
{
    [Fact]
    public void A_split_and_its_ground_keep_the_parents_multiplier_and_credit()
    {
        // old: the split children were reset to 1 and no credit; the ground took neither
        var b = BattleTests.Arena(4);
        var e = b.SpawnEnemy("risen", b.Player.X + 8, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e6;
        var pr = b.SpawnProjectile(Side.Player, e.X, e.Z, 10, School.Fire)!;
        pr.Weapon = "cleaver"; pr.BossDamage = 1.3; pr.Credit = "test_credit"; pr.Radius = 0.6; pr.Life = 2;
        pr.SplitOnHit = 2; pr.GroundOnHit = new GroundSpec(2, 2, 0.2);
        b.Tick(1 / 60.0, 0, 0);
        var kids = b.Projectiles.Living().Where(c => c.Depth == 1).ToList();
        Assert.Equal(2, kids.Count);
        Assert.All(kids, c => { Assert.Equal(1.3, c.BossDamage); Assert.Equal("test_credit", c.Credit); Assert.Equal("cleaver", c.Weapon); });
        var zn = b.Zones.Living().Single(z => z.Weapon == "cleaver");
        Assert.Equal(1.3, zn.BossDamage);
        Assert.Equal("test_credit", zn.Credit);
    }

    [Fact]
    public void Ground_naming_a_weapon_strikes_a_champion_with_the_weapons_multiplier()
    {
        // old: GroundZone.BossDamage defaulted to 1 and was passed explicitly, so the weapon's 1.3 never applied
        var b = BattleTests.Arena(4);
        b.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -b.Stats.Get(Stat.CritChance), "test"));
        b.AddWeapon("cleaver", 1);
        Enemy Champ(double dx)
        {
            var c = b.SpawnEnemy("wolf", b.Player.X + dx, b.Player.Z + 20, new Battle.SpawnOpts { Elite = true, Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
            c.MaxHp = c.Hp = 1e6;
            return c;
        }
        var a = Champ(-15); var c1 = Champ(15);
        var za = b.SpawnZone(Side.Player, a.X, a.Z, 3, 5, 20, School.Physical)!; za.Weapon = "cleaver";
        var zc = b.SpawnZone(Side.Player, c1.X, c1.Z, 3, 5, 20, School.Physical)!; zc.Weapon = "cleaver"; zc.BossDamage = 1;
        for (int i = 0; i < 30; i++) { a.X = za.X; a.Z = za.Z; c1.X = zc.X; c1.Z = zc.Z; b.Tick(1 / 60.0, 0, 0); }
        double ta = 1e6 - a.Hp, tc = 1e6 - c1.Hp;
        Assert.True(tc > 0);
        Assert.Equal(Weapons.All["cleaver"].BossDamage ?? 1, ta / tc, 3);
    }
}
