using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 b4) A hit that lands AFTER its cast carries the cast's weight: a projectile is stamped at the
/// launch (Projectile.W) and Battle.HitEnemy reads the stamp before the weapon's live CutW (1 again by then). The live
/// case is Oathkeeper's crescent. An On-kill echo is per kill, so it is a whole blow wherever it is fired from.</summary>
public sealed class LateWeightTests
{
    const double Dt = 1.0 / 60, Far = 7;

    /// <summary>Oathkeeper (or the plain Oathblade), chained on the test-only block or as written, and one foe held
    /// where only the crescent reaches: past the slash, on its line.</summary>
    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        public double Damage, Shove, Stagger, StampW = double.NaN;
        public int Hits, LaunchTick = -1, HitTick = -1, Ticks;
        public double CutWAtHit = double.NaN;
        double hp = 1e9;

        public Rig(bool chain, bool boss = false, bool evolve = true)
        {
            B = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Calling = "warden";
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -B.Stats.Get(Stat.CritChance), "test"));
            if (evolve) B.Evolve("oathblade", "oathkeeper");
            W = B.Weapons[0];
            if (evolve) Assert.Equal("oathkeeper", W.Evolution?.Id);
            W.Timer = 0;
            if (chain) W.Press = W.Press!.WithChain(new ChainDef { Grace = 0.40, Recover = 18, Period = 0.70 });
            E = B.SpawnEnemy("footpad", Far, 0)!;
            E.Hp = E.MaxHp = 1e9;
            E.AttackT = E.RangedT = 999;
            E.Boss = boss;
        }

        public void Tick(bool held)
        {
            E.X = Far; E.Z = 0; E.Vx = E.Vz = 0; E.Kbx = E.Kbz = 0; E.Stagger = 0;
            B.HoldSkill(W.Slot, held, E.X, E.Z);
            B.Tick(Dt, 0, 0);
            B.Events.Drain();
            Ticks++;
            if (LaunchTick < 0)
                foreach (var pr in B.Projectiles.Items)
                    if (pr.Alive && pr.Weapon == W.Id) { LaunchTick = Ticks; StampW = pr.W; break; }
            if (E.Hp < hp)
            {
                Damage += hp - E.Hp; hp = E.Hp; Hits++;
                Shove += Math.Abs(E.Kbx); Stagger += E.Stagger;
                if (HitTick < 0) { HitTick = Ticks; CutWAtHit = W.CutW; }
            }
        }

        /// <summary>The crescents launched and not yet landed: their weights summed, and how many are a heavy's.</summary>
        public (double W, int Heavies) Flying()
        {
            double w = 0; int heavies = 0;
            foreach (var pr in B.Projectiles.Items)
                if (pr.Alive && pr.Weapon == W.Id) { w += pr.W; if (pr.HeavyId != null) heavies++; }
            return (w, heavies);
        }
    }

    [Fact]
    public void A_crescent_that_lands_after_its_cast_carries_its_cuts_weight()
    {
        var c = new Rig(true); var u = new Rig(false);
        foreach (var r in new[] { c, u })
        {
            Assert.True(r.B.PressSkill(r.W.Slot, Far, 0));
            for (int i = 0; i < 180 && r.Hits == 0; i++) r.Tick(false);
            Assert.True(r.LaunchTick > 0, "no crescent was launched");
            Assert.True(r.HitTick > r.LaunchTick, $"the hit (tick {r.HitTick}) must land after the launch (tick {r.LaunchTick}): the foe is in the slash's reach");
            Assert.Equal(1.0, r.CutWAtHit);
        }
        const double cw = 0.70 / 1.05;   // the chain's period over Oathblade's written wait
        string n = $"stamp {c.StampW:F4} (period / wait {cw:F4}), unchained stamp {u.StampW:F4}; shove {c.Shove:F5} / {u.Shove:F5} = {c.Shove / u.Shove:F4}; damage {c.Damage:F3} / {u.Damage:F3} = {c.Damage / u.Damage:F4}";
        Assert.Equal(1.0, u.StampW);
        Assert.True(Math.Abs(c.StampW - cw) < 1e-9, n);
        Assert.True(u.Shove > 0, n);
        Assert.True(Math.Abs(c.Shove / u.Shove - cw) < 1e-6, n);
        Assert.True(Math.Abs(c.Damage / u.Damage - cw) < 1e-6, n);
    }

    [Fact]
    public void Held_a_minute_the_crescents_give_what_the_blows_crescents_gave()
    {
        int steps = (int)Math.Round(63.9 / Dt);
        foreach (bool boss in new[] { false, true })
        {
            var c = new Rig(true, boss); var u = new Rig(false, boss);
            for (int i = 0; i < steps; i++) { c.Tick(true); u.Tick(true); }
            double cv = boss ? c.Stagger : c.Shove, uv = boss ? u.Stagger : u.Shove;
            string n = $"{(boss ? "boss" : "non-boss")}: crescents {c.Hits} chained / {u.Hits} unchained; damage {c.Damage:F1} / {u.Damage:F1} = {c.Damage / u.Damage:F4}; "
                + $"{(boss ? "stagger added" : "shove added")} {cv:F4} / {uv:F4} = {cv / uv:F4}";
            Assert.True(u.Hits > 50 && c.Hits > u.Hits, n);
            Assert.True(uv > 0, n);
            Assert.True(Math.Abs(c.Damage / u.Damage - 1) < 0.02, n);
            if (!boss) { Assert.True(Math.Abs(cv / uv - 1) < 0.02, n); continue; }
            Assert.Equal(0.0, c.Shove + u.Shove);
            // (M3 MR 3 s1, the cause of the 0.9294 once pinned RED here) A boss's stagger is two things. The ROW
            // (Battle.HitEnemy, 0.004 x knockback x the cut's weight) is a fifth of it and follows the weights as damage
            // does. The other four fifths are the Hand's heavies (Battle.HandHeavy: 0.1 of the bar each, WHOLE, one per 6
            // blows' worth on both records): 12 a minute, so ONE heavy is 7% of the minute's stagger. At 63.9 s both
            // records have CAST 12; the unchained 12th landed at 63.33 s, the chained 12th (cast 63.62 s) is still in
            // the air. As landed: 1.3562 / 1.4592 = 0.9294 = (11 x 0.1 + row) / (12 x 0.1 + row). Not a rate: the window's
            // edge on a whole event (held 60 s 0.9978, 126 s 0.9981, 630 s 0.9912). So the row is held to the damage,
            // the heavies are counted as cast, and the whole is measured with what is in the air added.
            double hs = Hands.Warden.Stagger; int every = Hands.Warden.Every;
            var (cf, uf) = (c.Flying(), u.Flying());
            double cRow = c.Stagger - hs * c.B.HandHeavies, uRow = u.Stagger - hs * u.B.HandHeavies, per = uRow / u.Hits;
            double cAll = c.Stagger + hs * cf.Heavies + per * cf.W, uAll = u.Stagger + hs * uf.Heavies + per * uf.W;
            n += $"; the row {cRow:F5} / {uRow:F5} = {cRow / uRow:F4}; heavies landed {c.B.HandHeavies} / {u.B.HandHeavies}, in the air {cf.Heavies} / {uf.Heavies}, "
                + $"cast {c.W.HandBlows / every} / {u.W.HandBlows / every}; with the air {cAll:F4} / {uAll:F4} = {cAll / uAll:F4}";
            Assert.True(uRow > 0 && u.B.HandHeavies >= 10, n);
            // the row: the cuts' weights, as the damage is (both 0.9884)
            Assert.True(Math.Abs(cRow / uRow - c.Damage / u.Damage) < 0.001, n);
            // the heavies: one per `every` blows' worth on both records, none lost (landed + in the air = cast), as many cast
            Assert.Equal(c.W.HandBlows / every, c.B.HandHeavies + cf.Heavies);
            Assert.Equal(u.W.HandBlows / every, u.B.HandHeavies + uf.Heavies);
            Assert.Equal(u.W.HandBlows / every, c.W.HandBlows / every);
            // the whole, landed and in the air: within 1% (measured 0.9975)
            Assert.True(Math.Abs(cAll / uAll - 1) < 0.01, n);
            // as landed, at most the one heavy in the air apart (11 v 12 here: the 0.9294)
            Assert.True(u.B.HandHeavies - c.B.HandHeavies is 0 or 1, n);
        }
    }

    /// <summary>The echo's caller (Battle.RunOnKills, at the top of the next tick) never runs inside a cast today; the
    /// guard is for a caller that would. So the cut is opened by hand round the echo, as Firing does round a cut's cast.</summary>
    [Fact]
    public void A_kill_echo_inside_a_cut_is_a_whole_blow()
    {
        const double Cw = 0.70 / 1.05;
        static (WeaponInst W, double Dealt, int BlowN, int OwnBlows, int Casts, double After) Echo(double open)
        {
            var r = new Rig(true, evolve: false);
            var (b, w) = (r.B, r.W);
            w.Wick = Turns.Build(w, [(Wicks.Strand("oathblade", "onkill")!, Wicks.PerStrand)]);
            Assert.True(w.Wick is { OnKill: true });
            r.Tick(false);   // (the spatial grid built) the corpse one short of the second foe
            var (n, own, casts) = (w.BlowN, w.OwnBlows, w.Casts);
            w.CutW = open;
            Assert.True(Firing.OnKillEcho(b, w, Far - 1, 0));
            double after = w.CutW;
            w.CutW = 1;
            return (w, 1e9 - r.E.Hp, w.BlowN - n, w.OwnBlows - own, w.Casts - casts, after);
        }
        var cut = Echo(Cw); var whole = Echo(1);
        string n = $"echo inside a cut {cut.Dealt:F4}, outside {whole.Dealt:F4} (a cut's share would be {whole.Dealt * Cw:F4}); blows counted {cut.BlowN} / own {cut.OwnBlows} / casts {cut.Casts}; CutW after {cut.After:F4}";
        Assert.True(whole.Dealt > 0, n);
        Assert.True(Math.Abs(cut.Dealt - whole.Dealt) < 1e-9, n);
        Assert.True(cut.BlowN == 0 && cut.OwnBlows == 0 && cut.Casts == 0, n);
        Assert.Equal(Cw, cut.After);
    }
}
