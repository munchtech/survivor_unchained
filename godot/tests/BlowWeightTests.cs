using System;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 b2) Battle.HitEnemy's flat per-hit rows take a chained cut's weight; the per-blow events keep the
/// blow. Each row is read straight off one hit: a cut (the weapon's CutW at Sunder's 0.4375, its damage the share) beside
/// the whole blow on a twin foe, so a blow's worth of cuts (1 / weight of them) gives what the blow gave.</summary>
public sealed class BlowWeightTests
{
    const double Cw = 0.4375, Blow = 100;
    static readonly Tag[] Tags = [Tag.Physical, Tag.Melee];

    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        readonly double w;

        public Rig(bool cut, Action<Battle>? prep = null)
        {
            B = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [("sunder", 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -B.Stats.Get(Stat.CritChance), "test"));
            prep?.Invoke(B);
            W = B.Weapons[0];
            w = cut ? Cw : 1;
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = 1e6;
            E.AttackT = E.RangedT = 999;
        }

        /// <summary>One hit of the weapon: a cut's share of the blow when chained, as inside its cast.</summary>
        public double Hit(double blow = Blow, StatusPayload? status = null, double knock = 0)
        {
            W.CutW = w;
            try { return B.HitEnemy(E, blow * w, School.Physical, Tags, new HitOpts { Weapon = W, Status = status, Knockback = knock, DirX = 1, NoProcs = true }); }
            finally { W.CutW = 1; }
        }
    }

    [Fact]
    public void The_shove_and_a_boss_stagger_are_the_cuts_share()
    {
        var c = new Rig(true); var u = new Rig(false);
        c.Hit(knock: 1); u.Hit(knock: 1);
        Assert.True(u.E.Kbx > 0);
        Assert.Equal(Cw, c.E.Kbx / u.E.Kbx, 12);

        var cb = new Rig(true); var ub = new Rig(false);
        cb.E.Boss = ub.E.Boss = true;
        cb.Hit(knock: 1); ub.Hit(knock: 1);
        Assert.True(ub.E.Stagger > 0);
        Assert.Equal(Cw, cb.E.Stagger / ub.E.Stagger, 12);
        Assert.Equal(0.0, cb.E.Kbx);
    }

    [Fact]
    public void The_floor_is_the_cuts_share_of_the_blows_floor()
    {
        var c = new Rig(true); var u = new Rig(false);
        c.E.TakenMul = u.E.TakenMul = 0.03;
        double cd = c.Hit(10), ud = u.Hit(10);
        Assert.Equal(0.5, ud, 12);
        Assert.Equal(0.5 * Cw, cd, 12);
    }

    [Fact]
    public void A_shock_is_eaten_by_one_blows_worth_of_cuts()
    {
        var c = new Rig(true); var u = new Rig(false);
        var shock = new StatusPayload(StatusKind.Shock, 1, 1, 30);
        double plainU = u.Hit(), plainC = c.Hit();
        u.B.ApplyStatus(u.E, shock, 0); c.B.ApplyStatus(c.E, shock, 0);
        double bonusU = u.Hit() - plainU;
        Assert.True(bonusU > 1);
        Assert.False(u.E.Status.Has(StatusKind.Shock));
        double bonusC = 0; int cuts = 0;
        while (c.E.Status.Has(StatusKind.Shock)) { bonusC += c.Hit() - plainC; cuts++; }
        Assert.Equal(3, cuts);
        Assert.Equal(bonusU, bonusC, 9);
        Assert.Equal(plainC, c.Hit(), 12);
        // a fresh Shock is a whole one again
        c.B.ApplyStatus(c.E, shock, 0);
        Assert.Equal(0.0, c.E.ShockEaten);
        Assert.Equal(bonusU * Cw, c.Hit() - plainC, 9);
        Assert.Equal(Cw, c.E.ShockEaten, 12);
    }

    [Fact]
    public void A_cut_is_judged_for_the_burst_as_the_blow_it_is_a_share_of()
    {
        var c = new Rig(true); var u = new Rig(false);
        c.E.Hp = u.E.Hp = 40;
        c.E.MaxHp = u.E.MaxHp = 1e6;
        c.Hit(); u.Hit();
        Assert.True(u.E.LastBlow >= 2);
        Assert.Equal(1.0, c.E.LastBlow / u.E.LastBlow, 9);
    }

    [Fact]
    public void The_opener_lands_whole_on_the_first_cut()
    {
        Action<Battle> blind = b => { b.AddBoon("hunters_blind"); b.AddBoon("hunters_blind"); };
        var c = new Rig(true, blind); var u = new Rig(false, blind);
        var plain = new Rig(false);
        double blow = plain.Hit(), critMul = u.B.Stats.Get(Stat.CritDamage);
        double opened = u.Hit();
        Assert.Equal(blow * critMul, opened, 9);
        double first = c.Hit();
        Assert.True(c.E.LastCrit);
        Assert.Equal(blow * Cw + blow * (critMul - 1), first, 9);
        // the blow as judged for the burst is the whole opener
        Assert.Equal(u.E.LastBlow, c.E.LastBlow, 9);
        double second = c.Hit();
        Assert.False(c.E.LastCrit);
        Assert.Equal(blow * Cw, second, 9);
        // a blow's worth of cuts: the first, and (1 - weight) / weight more plain ones
        Assert.Equal(opened, first + second * (1 - Cw) / Cw, 9);
    }

    [Fact]
    public void A_bleed_riding_a_cut_is_sized_on_the_blow()
    {
        var c = new Rig(true); var u = new Rig(false);
        var bleed = new StatusPayload(StatusKind.Bleed, 1, 1, 3);
        c.Hit(status: bleed); u.Hit(status: bleed);
        var cs = c.E.Status[StatusKind.Bleed]; var us = u.E.Status[StatusKind.Bleed];
        Assert.NotNull(cs); Assert.NotNull(us);
        Assert.True(us!.Power > 0);
        Assert.Equal(us.Power, cs!.Power, 9);
        Assert.Equal(us.Stacks, cs.Stacks, 9);
        Assert.Equal(us.T, cs.T, 9);
    }
}
