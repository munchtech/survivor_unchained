using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 b5) The tail of Battle.HitEnemy on a chained cut: the board's statuses (BoardOnHit) and the Flare's
/// run inside the weighted window on the BLOW's damage, blue.poachers_mercy doubles as a blow's share, and a strike a
/// cut schedules carries the cut's weight to where it lands (StrikeSpec.W). The harness is ProcWeightTests': the SAME
/// skill held 63.9 s, chained (period 0.70, on a copy of its record) against unchained, on a foe that does not die.</summary>
public sealed class TailWeightTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public TailWeightTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;
    const int Steps = 3834;

    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        public int Cuts;

        /// <param name="crit">Her chance to strike true (0: off, as ProcWeightTests).</param>
        public Rig(string id, bool chained, int seed = 5, double crit = 0, string? also = null)
        {
            B = new Battle(new BattleSetup
            {
                Seed = (uint)seed, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = also == null ? [(id, 1)] : [(id, 1), (also, 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Calling = "warden";
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, crit - B.Stats.Get(Stat.CritChance), "test"));
            W = B.Weapons[0];
            W.Timer = 0;
            if (chained)
            {
                W.Press = W.Press!.WithChain(new ChainDef { Grace = 0.40, Recover = 18, Period = 0.70 });
                Assert.NotSame(W.Def.Press!.Chain, W.Press.Chain);
            }
            // (the switch: the shipped record carries a chain; the unchained run takes it off its own copy)
            else W.Press = W.Press?.WithChain(null);
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = 1e9;
            E.AttackT = E.RangedT = 999;
        }

        /// <summary>The board lit with one rule (Lamps v2: BoardOnHit wakes).</summary>
        public Rig Lit(params LampEffect[] rules)
        {
            B.Lamps = new LampLoadout();
            foreach (var r in rules) B.Lamps.Add(r);
            Assert.True(B.Lamps.Board);
            return this;
        }

        public double Dealt => B.DamageBy.Values.Sum();

        /// <summary>Where the foe is held (x; z 0). 2: inside the swing. T3 holds it where only the strike reaches.</summary>
        public double At = 2;
        /// <summary>The strikes scheduled (Ev.Strike) and the last one's circle; the ticks the foe lost life on, what it
        /// has lost in all, and what the last such tick took.</summary>
        public int Strikes, Hits;
        public double StrikeX = double.NaN, StrikeR = double.NaN, Lost, LastHit;

        public void Step(bool held)
        {
            B.HoldSkill(W.Slot, held, At, 0);
            E.X = At; E.Z = 0; E.Vx = E.Vz = 0;
            double hp = E.Hp;
            B.Tick(Dt, 0, 0);
            foreach (var ev in B.Events.Drain())
            {
                if (ev is Ev.Slash) Cuts++;
                if (ev is Ev.Strike st) { Strikes++; StrikeX = st.X; StrikeR = st.Radius; }
            }
            if (E.Hp < hp) { Hits++; LastHit = hp - E.Hp; Lost += LastHit; }
        }

        public Rig Hold(Action? each = null)
        {
            for (int i = 0; i < Steps; i++)
            {
                Step(true);
                each?.Invoke();
            }
            return this;
        }
    }

    static LampEffect Rule(string rule, Tag[]? tags = null, Dictionary<string, double>? args = null, Dictionary<string, string>? words = null) =>
        new() { Do = LampDo.Rule, Rule = rule, Args = args ?? new(), Words = words, Lamp = "", Tags = tags };

    /// <summary>The bleed rite over her melee skills: every blow bleeds for 30% of the blow over 3 s (the worst kept).</summary>
    static LampEffect BleedRite() => Rule("rite", [Tag.Melee], new() { ["share"] = 0.3 }, new() { ["mech"] = "bleed" });

    /// <summary>What the foe's bleed paid over the hold: its rate summed over the time it ran.</summary>
    static double Bled(Rig r)
    {
        double sum = 0;
        r.Hold(() => { if (r.E.Status[StatusKind.Bleed] is { T: > 0 } s) sum += s.Power * Dt; });
        return sum;
    }

    [Theory]
    [InlineData("sunder")]
    [InlineData("oathblade")]
    public void The_rites_bleed_under_a_chain_builds_at_the_blows_rate(string id)
    {
        var plain = new Rig(id, false).Lit(BleedRite());
        var chain = new Rig(id, true).Lit(BleedRite());
        double a = Bled(plain), c = Bled(chain);
        output.WriteLine($"{id} rite bleed paid over 63.9 s: chained {c:0.##} ({chain.Cuts} cuts), unchained {a:0.##} ({plain.Cuts} blows), ratio {c / a:0.0000}");
        Assert.True(chain.Cuts > plain.Cuts * 1.4, "the chain did not swing");
        Assert.True(a > 0);
        // (before: the bleed was sized on the cut's share and kept by its worst rate: 0.44x / 0.67x)
        Assert.InRange(c / a, 0.97, 1.03);
    }

    [Fact]
    public void Poachers_mercy_doubles_as_often_as_the_blows_did()
    {
        // she strikes true half the time, so the count is worth reading; the rite's bleed is what the lamp doubles
        const double crit = 0.5;
        const int seeds = 40;
        int Doubled(bool chained, int seed, out int cuts)
        {
            var r = new Rig("sunder", chained, seed, crit).Lit(BleedRite(), Rule("blue.poachers_mercy"));
            int n = 0;
            double last = r.E.PoachedAt;
            r.Hold(() => { if (r.E.PoachedAt != last) { n++; last = r.E.PoachedAt; } });
            cuts = r.Cuts;
            return n;
        }
        var a = new double[seeds];
        var c = new double[seeds];
        int blows = 0, cuts = 0;
        for (int s = 1; s <= seeds; s++)
        {
            a[s - 1] = Doubled(false, s, out int nb); blows += nb;
            c[s - 1] = Doubled(true, s, out int nc); cuts += nc;
        }
        // the spread is measured, not assumed: each record's mean a seed with its standard error, and the standard
        // error of the difference from the per-seed differences (seed s chained less seed s unchained)
        static (double Mean, double Se) Of(double[] v)
        {
            double m = v.Average();
            return (m, Math.Sqrt(v.Sum(x => (x - m) * (x - m)) / (v.Length - 1) / v.Length));
        }
        var (ma, sa) = Of(a);
        var (mc, sc) = Of(c);
        var (md, sd) = Of(c.Zip(a, (x, y) => x - y).ToArray());
        double off = md / sd;
        output.WriteLine($"sunder poachers_mercy doublings over {seeds} x 63.9 s, true strikes at {crit}: chained {c.Sum():0} ({cuts} cuts; a seed {mc:0.000}, se {sc:0.000}), "
            + $"unchained {a.Sum():0} ({blows} blows; a seed {ma:0.000}, se {sa:0.000}), ratio {mc / ma:0.0000}, difference a seed {md:+0.000;-0.000} (se {sd:0.000}): {off:+0.00;-0.00} SE");
        Assert.True(a.Sum() > 400);
        // enough seeds that the line can see the old fault: three standard errors are under 15% of the blows' count
        Assert.True(3 * sd <= 0.15 * ma, $"too few seeds: 3 SE {3 * sd:0.000} against a mean of {ma:0.000}");
        // (before the gate took the weight: chained 175 / unchained 219 = 0.799 at 10 seeds. The thinning was right per
        // cut, but the once-a-second gate ate the cut after each doubling: cuts are 0.70 s apart, blows 1.6 s. A cut's
        // gate now runs 1 s x its weight, 0.4375 s, so it passes the next cut as 1 s passes the next blow.)
        Assert.InRange(off, -3, 3);
    }

    // (M3 MR 3 t3) Why b5's rig read 62 hits with the strike and 62 without: the strike lands AHEAD of the swing, a
    // 1.8 m circle 1.4 reaches out (Weapons.cs FireSlash), and Bonesplitter's own area (x1.25) lengthens the reach it is
    // measured from: its near edge is past a foe held at 2 m. So the foe is held at the circle's middle, where the
    // swing does not reach and every hit on it is a strike: its damage is the strike's alone.
    [Fact]
    public void A_strike_scheduled_by_a_cut_lands_at_the_cuts_weight()
    {
        // Bonesplitter (the Cleaver's evolution: every swing schedules a strike 0.12 s on) lent to Oathblade, whose swing
        // is the same function. The strike lands after the cast, when WeaponInst.CutW reads 1 again (StrikeSpec.W).
        const double cw = 0.70 / 1.05;   // the chain's period over Oathblade's written wait
        Rig Make(bool chained, bool evolved, double at)
        {
            var r = new Rig("oathblade", chained, also: "cleaver") { At = at };
            r.E.X = at;
            if (evolved) r.W.Evolution = r.B.Weapons[1].Def.Evolutions.First(e => e.Id == "bonesplitter");
            return r;
        }
        void Step(Rig r, bool held) { r.B.Weapons[1].Timer = 999; r.Step(held); }

        // where the strike falls: read off the first one scheduled, the foe where b5 held it
        var probe = Make(false, true, 2);
        for (int i = 0; i < 120 && probe.Strikes == 0; i++) Step(probe, true);
        Assert.True(probe.Strikes > 0, "the swing scheduled no strike: W.Evolution did not reach FireSlash");
        double far = probe.StrikeX, edge = probe.StrikeX - probe.StrikeR - probe.E.Radius;
        output.WriteLine($"the strike: centre x {far:0.###}, radius {probe.StrikeR:0.##}, its near edge on a footpad (radius {probe.E.Radius:0.##}) at x {edge:0.###}; b5 held the foe at 2");
        Assert.True(edge > 2, "the strike reaches a foe at 2 m: b5's miss has another cause");

        // (1) one cut's strike against one written blow's: a press each, to the first hit
        var one = new[] { Make(true, true, far), Make(false, true, far) };
        // (M3 MR 3 landed rule) the battle's first cut is whole (the bank starts full): it would weigh 1 (ratio 1.5 over cw).
        // The chained grip's bank is spent first (PaidTo = now), so the cut weighs its share, as a held cut does.
        one[0].W.PaidTo = one[0].B.Time;
        foreach (var r in one)
        {
            Assert.True(r.B.PressSkill(r.W.Slot, far, 0));
            for (int i = 0; i < 180 && r.Hits == 0; i++) Step(r, false);
            Assert.True(r.Strikes > 0 && r.Hits == 1, $"the strike did not land ({r.Strikes} scheduled, {r.Hits} hits)");
            Assert.Equal(1.0, r.W.CutW);
        }
        double cut = one[0].LastHit, written = one[1].LastHit;
        output.WriteLine($"one strike: a cut's {cut:0.####}, a written blow's {written:0.####}, ratio {cut / written:0.00000} (cw {cw:0.00000})");
        Assert.True(written > 0);
        Assert.InRange(cut / written / cw, 0.995, 1.005);

        // (2) held 63.9 s: the cuts' strikes give what the blows' strikes gave. What is scheduled at the close is counted
        // (run out with the hold let go: landed + pending, as LateWeightTests T2 counts what is in the air).
        var bare = Make(false, false, far);
        var plain = Make(false, true, far);
        var chain = Make(true, true, far);
        var late = new Dictionary<Rig, (int Pending, int New, double Landed)>();
        foreach (var r in new[] { bare, plain, chain })
        {
            for (int i = 0; i < Steps; i++) Step(r, true);
            int at = r.Strikes, pending = r.Strikes - r.Hits; double landed = r.Lost;
            for (int i = 0; i < 60 && r.Hits < r.Strikes; i++) Step(r, false);
            late[r] = (pending, r.Strikes - at, landed);
        }
        output.WriteLine($"oathblade + bonesplitter over 63.9 s, the foe at the strike: chained {chain.Lost:0.#} ({chain.Cuts} cuts, {chain.Strikes} strikes, {chain.Hits} landed; at the close {late[chain].Landed:0.#} landed, {late[chain].Pending} pending, {late[chain].New} scheduled after), "
            + $"unchained {plain.Lost:0.#} ({plain.Cuts} blows, {plain.Strikes} strikes, {plain.Hits} landed; at the close {late[plain].Landed:0.#} landed, {late[plain].Pending} pending, {late[plain].New} scheduled after), "
            + $"ratio {chain.Lost / plain.Lost:0.0000} (as landed at the close {late[chain].Landed / late[plain].Landed:0.0000}); with no strike {bare.Lost:0.#} ({bare.Cuts} blows)");
        // the swing does not reach her there: every hit is a strike, and every strike scheduled landed
        Assert.Equal(0.0, bare.Lost);
        Assert.True(bare.Cuts > 50 && bare.Strikes == 0);
        Assert.True(chain.Cuts > plain.Cuts * 1.4, "the chain did not swing");
        Assert.Equal(plain.Cuts, plain.Strikes);
        Assert.Equal(chain.Cuts, chain.Strikes);
        Assert.Equal(plain.Strikes, plain.Hits);
        Assert.Equal(chain.Strikes, chain.Hits);
        // nothing new is cast once the hold is let go: the run-out only lands what the window scheduled
        Assert.Equal(0, late[plain].New + late[chain].New);
        // (before StrikeSpec.W: every strike landed at weight 1, 1.5x as many as the blows': 1.5x the damage)
        Assert.InRange(chain.Lost / plain.Lost, 0.98, 1.02);
    }
}
