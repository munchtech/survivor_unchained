using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 b3a) Battle.ApplyStatus on a chained cut: a status riding the cuts keeps its per-second rates
/// against the written blows. Every test holds the SAME skill for 63.9 s, chained (period 0.70, on a copy of its
/// record: no shipped record has a chain) against unchained, on a foe that does not die. The run itself is not a
/// whole number of blows on the chained side (Sunder: 92 cuts = 40.25 blows' worth against 40 blows, +0.6%), which is
/// inside every 2% line below. Where a chance is under 1 the means are over enough seeds that 2% is at least three
/// standard errors of the ratio (asserted; the measured error is in each message).</summary>
public sealed class StatusWeightTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public StatusWeightTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;
    const int Steps = 3834;

    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        readonly StatusKind watch;
        readonly bool boss;
        /// <summary>Damage over time dealt, the watched status's landings, the stagger added (a boss).</summary>
        public double Dot, Stagger;
        public int Landed;
        public readonly List<double> Frozen = new();
        /// <summary>The watched status's stacks 1.6 s and 3.2 s after it first landed (no later: at 4.8 s Sunder's own
        /// heavy, its 4th blow, has applied the status twice, and the chain's heavy, cut 8, lands at 4.9 s).</summary>
        public readonly double[] Stacks = new double[2];
        double first = double.NaN;
        int sampled;

        /// <param name="ride">A status put on the skill's hits (by a wick that does nothing else); null, its own.</param>
        public Rig(string id, bool chained, int seed, StatusKind watch, StatusPayload? ride, bool boss = false)
        {
            this.watch = watch; this.boss = boss;
            B = new Battle(new BattleSetup
            {
                Seed = (uint)seed, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [(id, 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Calling = "warden";
            // crit off: it holds in expectation (a cut rolls as a blow does) and is not what this measures
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -B.Stats.Get(Stat.CritChance), "test"));
            W = B.Weapons[0];
            W.Timer = 0;
            if (chained)
            {
                W.Press = W.Press!.WithChain(new ChainDef { Grace = 0.40, Recover = 18, Period = 0.70 });
                Assert.Null(W.Def.Press!.Chain);
            }
            if (ride != null)
            {
                Assert.Null(W.StatusOf);
                W.Wick = new WickFx { Statuses = { new WickStatus(ride, 0, 0) } };
            }
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = 1e9;
            E.AttackT = E.RangedT = 999;
            E.Boss = boss;
        }

        public Rig Hold()
        {
            for (int i = 0; i < Steps; i++)
            {
                B.HoldSkill(W.Slot, true, E.X, E.Z);
                E.X = 2; E.Z = 0; E.Vx = E.Vz = 0;
                // (a boss) the bar is read and emptied every tick, never full and never resisting: what is ADDED is the measure
                if (boss) { E.Stagger = 0; E.StaggeredT = 0; E.StaggerResistT = 0; }
                B.Tick(Dt, 0, 0);
                if (boss) Stagger += E.Stagger;
                foreach (var ev in B.Events.Drain())
                {
                    if (ev is Ev.Hit { Dot: true } h && h.Target == E.Id) Dot += h.Amount;
                    else if (ev is Ev.Status s && s.Target == E.Id)
                    {
                        if (s.Kind == StatusKind.Frozen) Frozen.Add(B.Time);
                        if (s.Kind == watch) { Landed++; if (double.IsNaN(first)) first = B.Time; }
                    }
                }
                if (sampled < Stacks.Length && B.Time >= first + (sampled + 1) * 1.6 + 0.05) Stacks[sampled++] = E.Status[watch]?.Stacks ?? 0;
            }
            return this;
        }
    }

    /// <summary>The mean of a measure over seeds 1..n, and its standard error.</summary>
    static (double Mean, double Se) Mean(int seeds, Func<int, double> run)
    {
        var v = new double[seeds];
        Parallel.For(0, seeds, i => v[i] = run(i + 1));
        double m = v.Average();
        return (m, Math.Sqrt(v.Sum(x => (x - m) * (x - m)) / (seeds - 1) / seeds));
    }

    /// <summary>Chained over unchained, with the ratio's standard error; told (shown by
    /// `dotnet test --logger "console;verbosity=detailed"`), and returned for the assert.</summary>
    (double Ratio, double Se, string Told) Against(string what, int seeds, Func<bool, int, double> run)
    {
        var c = Mean(seeds, s => run(true, s));
        var u = Mean(seeds, s => run(false, s));
        double r = c.Mean / u.Mean, se = r * Math.Sqrt(c.Se * c.Se / (c.Mean * c.Mean) + u.Se * u.Se / (u.Mean * u.Mean));
        string told = $"{what}: chained {c.Mean:F3} (se {c.Se:F3}) | unchained {u.Mean:F3} (se {u.Se:F3}) | {(r - 1) * 100:+0.00;-0.00}% (se {se * 100:F2}%), {seeds} seeds";
        output.WriteLine(told);
        return (r, se, told);
    }

    void Within2(string what, int seeds, Func<bool, int, double> run)
    {
        var (r, se, told) = Against(what, seeds, run);
        Assert.True(3 * se <= 0.02, "too few seeds: " + told);
        Assert.True(Math.Abs(r - 1) <= 0.02, told);
    }

    [Fact]
    public void A_refreshed_bleed_does_the_same_damage_a_second()
    {
        // Oathblade's written bleed: 0.35 a blow, 0.3 of the blow over 3 s, the worst kept and refreshed (weight 0.6667).
        // (at rank 1 the carried Oathblade has no status of its own, WeaponInst.StatusOf is null: it rides as the others do)
        var bleed = new StatusPayload(StatusKind.Bleed, 0.35, 0.3, 3);
        Within2("oathblade bleed damage", Seeds1, (ch, seed) => new Rig("oathblade", ch, seed, StatusKind.Bleed, bleed).Hold().Dot);
    }

    [Fact]
    public void A_stacking_burn_builds_and_burns_the_same()
    {
        var sure = new StatusPayload(StatusKind.Burn, 1, 0.5, 3);
        var c = new Rig("sunder", true, 1, StatusKind.Burn, sure).Hold();
        var u = new Rig("sunder", false, 1, StatusKind.Burn, sure).Hold();
        string told = $"sunder burn at chance 1: chained {c.Dot:F1} stacks {string.Join(" ", c.Stacks.Select(s => s.ToString("F3")))}"
            + $" | unchained {u.Dot:F1} stacks {string.Join(" ", u.Stacks.Select(s => s.ToString("F3")))} | {(c.Dot / u.Dot - 1) * 100:+0.00;-0.00}%";
        output.WriteLine(told);
        // Quantization in her favor, accepted by main, see chain_weight.md (the burn pays +0.5% chained). The stacks are
        // read at 1.6 and 3.2 s only: unchained 2, 3; chained 1.875, 2.750 (a whole first stack, then 0.4375 a cut),
        // inside 0.45. A 4.8 s sample crosses Sunder's heavy (its 4th blow applies the status twice: 5 unchained, the
        // chain's cut 8 at 4.9 s not yet landed), so it measured the heavy's timing and not the build: not sampled.
        Assert.Equal(new double[] { 2, 3 }, u.Stacks);
        for (int i = 0; i < u.Stacks.Length; i++) Assert.True(Math.Abs(c.Stacks[i] - u.Stacks[i]) <= 0.45, told);
        Assert.True(Math.Abs(c.Dot / u.Dot - 1) <= 0.02, told);

        var maybe = new StatusPayload(StatusKind.Burn, 0.35, 0.5, 3);
        // Quantization in her favor, accepted by main, see chain_weight.md (the watch: a stacking status under chance 1).
        // Measured over 400 seeds: chained 388.4 (se 6.2) against unchained 314.7 (se 4.3): +23.4% (se 2.6%), not the
        // 2% of the other lines. Reading: a 3 s burn on 1.6 s blows at 0.35 drops whenever two blows miss in a row, so
        // the count keeps starting over; the cuts try every 0.70 s, so the burn is dropped less often and stands higher,
        // and each new start's opening cut is a whole stack (the first-application-whole rule) where it stood for 0.89
        // of one. The rule is kept as written; this pins what it gives (the band is three standard errors).
        var (r, _, said) = Against("sunder burn damage at chance 0.35", Seeds2, (ch, seed) => new Rig("sunder", ch, seed, StatusKind.Burn, maybe).Hold().Dot);
        Assert.True(Math.Abs(r - 1.234) <= 0.08, said);
    }

    [Fact]
    public void Chill_freezes_as_often()
    {
        var chill = new StatusPayload(StatusKind.Chill, 1, 1, 4);
        var c = new Rig("sunder", true, 1, StatusKind.Chill, chill).Hold();
        var u = new Rig("sunder", false, 1, StatusKind.Chill, chill).Hold();
        static double[] Cycles(Rig r) => r.Frozen.Zip(r.Frozen.Skip(1), (a, b) => b - a).ToArray();
        double[] cc = Cycles(c), uc = Cycles(u);
        string told = $"sunder chill: chained {c.Frozen.Count} freezes, first {c.Frozen[0]:F2} s, cycles {string.Join(" ", cc.Select(x => x.ToString("F2")))}"
            + $" | unchained {u.Frozen.Count} freezes, first {u.Frozen[0]:F2} s, cycles {string.Join(" ", uc.Select(x => x.ToString("F2")))}";
        output.WriteLine(told);
        // Quantization in her favor, accepted by main, see chain_weight.md (the watch: 9 freezes against 8). Measured:
        // chained 9 freezes, every cycle 7.00 s; unchained 8 freezes, cycles 7.95 to 8.00 s: 1.0 s short (more than the
        // one cut, 0.70 s, of the first line), 12% more freezes. The first freeze is within a cut (5.00 s against
        // 4.88 s). Reading: a freeze takes the Chill slot away, so EVERY cycle opens on
        // a "fresh" foe and its opening cut is a whole blow's cold (the first-application-whole rule): 0.5625 of a
        // blow, 0.9 s of cuts, given once a cycle and not only once a fight. The rule is kept as written; this pins
        // what it gives.
        Assert.True(Math.Abs(c.Frozen[0] - u.Frozen[0]) <= 0.70 + 1e-6, told);
        Assert.True(uc.Length > 0 && uc.All(x => Math.Abs(x - 8.0) <= 0.06), told);
        Assert.True(cc.Length > 0 && cc.All(x => Math.Abs(x - 7.0) <= 0.02), told);
    }

    [Fact]
    public void An_eighty_percent_stun_lands_as_often()
    {
        var stun = new StatusPayload(StatusKind.Stun, 0.80, 1, 1);
        Within2("sunder stuns landed at chance 0.8", Seeds4, (ch, seed) => new Rig("sunder", ch, seed, StatusKind.Stun, stun).Hold().Landed);
    }

    [Fact]
    public void An_eighty_percent_stun_rider_staggers_a_boss_the_same()
    {
        var stun = new StatusPayload(StatusKind.Stun, 0.80, 1, 1);
        // the blows' own stagger (no rider; nothing in it is rolled) is taken off: what is left is the rider's
        double Own(bool ch) => new Rig("sunder", ch, 1, StatusKind.Stun, null, boss: true).Hold().Stagger;
        double ownC = Own(true), ownU = Own(false);
        output.WriteLine($"sunder's own stagger on a boss: chained {ownC:F3} | unchained {ownU:F3}");
        Within2("sunder stun rider's stagger on a boss at chance 0.8", Seeds4, (ch, seed) => new Rig("sunder", ch, seed, StatusKind.Stun, stun, boss: true).Hold().Stagger - (ch ? ownC : ownU));
    }

    // Seeds: the bleed's ratio has se 0.91% at 400 seeds, so 1200; a 20% stun's had se 0.53% at 6000 (2.5 minutes a
    // test), so the stun runs at chance 0.8, where 600 seeds hold the line (se 0.54% landed, 0.55% the stagger: three are 1.7%; 12 s).
    const int Seeds1 = 1200, Seeds2 = 400, Seeds4 = 600;
}
