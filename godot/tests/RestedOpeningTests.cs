using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 o2) The rested opening (Battle.RestOf, Sim.Blows.Rested): a chained cut that starts on a press
/// carries the rest its grip had. Every cut pays forward its own share (the time until the grip is free again, over
/// the written wait); a press adds the idle time since the grip was last free; at most one whole blow. The held
/// chain's cut on its beat keeps its share to the bit. The shipped records, as they ship.</summary>
public sealed class RestedOpeningTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public RestedOpeningTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;

    sealed record Cut(int N, double Start, double End, double Rest, double Weight, double Scale, bool Heavy, bool Whole, double Wait);

    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        /// <summary>The weapon that swings (the union's half when one is granted).</summary>
        public WeaponInst G;
        public readonly Enemy E;
        public readonly List<Cut> Cuts = new();
        /// <summary>The summed weight of the cuts started, and what the cap (one whole blow) cut off them.</summary>
        public double Sum, CapLoss;
        public int Drops;
        double last = double.NaN, dropped = double.NaN;

        public Rig(string id, bool chained = true, bool hand = true)
        {
            B = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [(id, 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Calling = "warden";
            B.HandsOn = hand;
            // crit off: a cut rolls as a blow does; these tests read one cut against another
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -B.Stats.Get(Stat.CritChance), "test"));
            G = W = B.Weapons[0];
            W.Timer = 0;
            Assert.Same(W.Def.Press, W.Press);
            if (!chained) W.Press = W.Press!.WithChain(null);
            Assert.Equal(chained, W.Chained);
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = 1e9;
            E.AttackT = E.RangedT = 999;
        }

        /// <summary>The written wait now: the unchained record's (the period over the cut's share).</summary>
        public double Written => Firing.CooldownOf(B, G) / G.BlowWeight;
        /// <summary>The written blows landed (every cast's weight, counted).</summary>
        public double Landed => G.BlowN + G.BlowPart;
        public double Damage => 1e9 - E.Hp;

        void Pin() { var p = B.Player; E.X = p.X + 2; E.Z = p.Z; E.Vx = E.Vz = 0; }

        public void Step(bool held, int steps = 1)
        {
            for (int i = 0; i < steps; i++)
            {
                Pin();
                B.HoldSkill(W.Slot, held, E.X, E.Z);
                B.Tick(Dt, 0, 0);
                Note();
            }
        }

        public bool Tap(int? slot = null)
        {
            Pin();
            bool ok = B.PressSkill(slot ?? W.Slot, E.X, E.Z);
            Note();
            return ok;
        }

        public void Until(double time) { while (B.Time < time - 1e-9) Step(false); }

        void Note()
        {
            B.Events.Drain();
            if (G.Chain is not { } c) return;
            if (c.Dropped && dropped != c.StartAt) { dropped = c.StartAt; Drops++; }
            if (!c.Live || c.StartAt == last) return;
            last = c.StartAt;
            double own = G.BlowWeight * (c.Whole ? 1 : c.PeriodScale);
            Assert.Equal(GripMeter.WeightOf(G), c.Weight);
            Cuts.Add(new Cut(c.Cut, c.StartAt, c.PeriodEnd, c.Rest, c.Weight, c.PeriodScale, c.Heavy, c.Whole, Written));
            Sum += c.Weight;
            if (!c.Whole && Cuts.Count > 1) CapLoss += own + c.Rest - c.Weight;
        }
    }

    /// <summary>(1) Held steady, both shipped records, a minute: the first cut of the battle is a whole blow; every cut
    /// after it is the chain's next cut on its beat, carries no rest and weighs its own share TO THE BIT (the cut's
    /// share times a heavy's longer period: the tip's weight), starting on the instant the cut before's period ended.
    /// (SwingChainTests' held minute pins the beats, rates and sides, and stands untouched.)</summary>
    [Theory]
    [InlineData("sunder", true)]
    [InlineData("sunder", false)]
    [InlineData("oathblade", true)]
    [InlineData("oathblade", false)]
    public void Held_steady_every_cut_but_the_first_weighs_its_share_to_the_bit(string id, bool hand)
    {
        var r = new Rig(id, hand: hand);
        r.Step(true, 3600);
        Assert.True(r.Cuts.Count > 60, $"{r.Cuts.Count} cuts");
        Assert.Equal((0, 1.0, 1.0), (r.Cuts[0].N, r.Cuts[0].Rest, r.Cuts[0].Weight));
        double share = r.W.BlowWeight, sum = 1;
        Assert.Equal(id == "sunder" ? 0.70 / 1.6 : 0.70 / 1.05, share);
        for (int k = 1; k < r.Cuts.Count; k++)
        {
            var c = r.Cuts[k];
            Assert.Equal(k, c.N);
            Assert.Equal(0.0, c.Rest);
            // (exact: the same product the tip's cast took)
            Assert.Equal(share * c.Scale, c.Weight);
            Assert.Equal(r.Cuts[k - 1].End, c.Start, 9);
            if (k < r.Cuts.Count - 1) sum += c.Weight;
        }
        if (id == "sunder" || hand) Assert.Contains(r.Cuts, c => c.Heavy);
        Assert.Equal(0.0, r.CapLoss);
        // the counted blows are the cuts' weights: all but the last cut, whose blow may not have landed yet
        Assert.InRange(r.Landed - sum, -1e-9, r.Cuts[^1].Weight + 1e-9);
    }

    /// <summary>(2) The opening after a rest: its weight is its share plus the idle time since the grip was free over the
    /// written wait, at most 1; the battle's first cut is 1. Damage, Resolve, the written-blow count and the heavy's
    /// count (Sunder's own, the Hand's for Oathblade) all move by that same weight, and the wait after it is the period.</summary>
    [Theory]
    [InlineData("sunder", 0.2)]
    [InlineData("sunder", 0.9)]
    [InlineData("sunder", 1.6)]
    [InlineData("sunder", 5.0)]
    [InlineData("oathblade", 0.2)]
    [InlineData("oathblade", 0.9)]
    [InlineData("oathblade", 1.05)]
    [InlineData("oathblade", 5.0)]
    public void An_opening_after_a_rest_weighs_its_share_plus_the_rest(string id, double rest)
    {
        var r = new Rig(id);
        var w = r.W;
        double share = w.BlowWeight, period = Firing.CooldownOf(r.B, w), written = r.Written;
        Assert.Equal(0.70, period, 12);
        double Count() => id == "sunder" ? w.OwnBlows + w.OwnPart : w.HandBlows + w.HandPart;
        Assert.True(r.Tap());
        var first = r.Cuts.Single();
        Assert.Equal((0, 1.0), (first.N, first.Weight));
        Assert.Equal(first.Start + period, first.End, 9);
        r.Until(first.End - 0.1);
        // the first blow landed whole: every count took 1
        var (d1, f1) = (r.Damage, r.B.Resolve.LandedFill);
        Assert.True(d1 > 0 && f1 > 0);
        Assert.Equal((1.0, 1.0), (r.Landed, Count()));
        r.Until(first.End + rest);
        double idle = r.B.Time - w.Chain!.PeriodEnd, want = Math.Min(1, share + idle / written);
        Assert.InRange(idle, rest - 1e-9, rest + Dt);
        Assert.True(r.Tap());
        var c = r.Cuts[1];
        // (past the grace: a new chain's opening, cut 0)
        Assert.Equal(0, c.N);
        Assert.False(c.Heavy);
        Assert.Equal(want, c.Weight, 12);
        Assert.InRange(c.Weight, share, 1);
        if (rest >= written) Assert.Equal(1.0, c.Weight);
        // the wait after it is the cut's own period
        Assert.Equal(c.Start + period, c.End, 9);
        Assert.False(r.Tap());
        r.Until(c.End - 0.1);
        // (the foe's 1e9 life: a blow's damage is read off it to about 1e-7)
        Assert.Equal(want, (r.Damage - d1) / d1, 6);
        Assert.Equal(want, (r.B.Resolve.LandedFill - f1) / f1, 9);
        Assert.Equal(1 + want, r.Landed, 9);
        Assert.Equal(1 + want, Count(), 9);
        Assert.Equal(c.End, w.Chain.PeriodEnd, 9);
        // (ready on the step its period ends, or the one after: the step clock's residue)
        r.Until(c.End);
        if (!r.Tap()) { r.Step(false); Assert.True(r.Tap()); }
        output.WriteLine($"{id}: rest {rest:F2} s (idle {idle:F4}) -> weight {c.Weight:F4} (share {share:F4}, written wait {written:F3})");
    }

    /// <summary>One seeded press pattern, 120 s: holds, taps at a rhythm (buffered or not), gaps inside and outside the
    /// grace, flutters, and dashes (which drop a pending cut and bar the next). Checked at every step.</summary>
    static Rig Pattern(string id, int seed, bool hand, double[] worst)
    {
        var r = new Rig(id, hand: hand);
        var rng = new Random(seed);
        double share = r.W.BlowWeight, written = r.Written, heavyMost = share * (54.0 / 42 - 1);
        int steps = 7200, i = 0;
        void Step(bool held)
        {
            r.Step(held); i++;
            if (r.Cuts.Count == 0) return;
            var (c0, cn) = (r.Cuts[0], r.Cuts[^1]);
            // THE INVARIANT: the summed weight of the cuts started never exceeds elapsed / the written wait + 1 (the first
            // cut's whole blow); a heavy in hand pays forward its longer period, its extra share and no more
            double over = r.Sum - ((r.B.Time - c0.Start) / written + 1);
            worst[0] = Math.Max(worst[0], over);
            Assert.True(over <= (cn.Heavy ? heavyMost : 0) + 1e-6, $"{id} seed {seed} t {r.B.Time:F3}: sum {r.Sum:F4} over the bound by {over:F4}");
            // the account, exact: one whole blow, then every second from the first cut's period end to the last one's,
            // less only what the cap cut off (a grip left idle past a full written wait)
            double id2 = r.Sum - (1 + (cn.End - c0.End) / written - r.CapLoss);
            worst[1] = Math.Max(worst[1], Math.Abs(id2));
            Assert.True(Math.Abs(id2) <= 1e-6, $"{id} seed {seed} t {r.B.Time:F3}: the account is off by {id2:E3}");
            Assert.True(r.Landed <= r.Sum + 1e-9);
        }
        while (i < steps)
        {
            if (rng.NextDouble() < 0.2) r.B.Dash(rng.Next(2) == 0 ? 1 : -1, 0);
            switch (rng.Next(4))
            {
                case 0:
                {
                    int n = 3 + (int)(rng.NextDouble() * 240), dashAt = rng.NextDouble() < 0.35 ? rng.Next(n) : -1;
                    for (int k = 0; k < n && i < steps; k++) { if (k == dashAt) r.B.Dash(0, -1); Step(true); }
                    break;
                }
                case 1:
                {
                    int every = (int)Math.Round((0.2 + rng.NextDouble() * 2.8) * 60), taps = 1 + rng.Next(6);
                    bool buffered = rng.Next(2) == 0, want = false;
                    for (int k = 0; k < taps * every && i < steps; k++)
                    {
                        if (k % every == 0) want = true;
                        if (want && r.Tap() || !buffered) want = false;
                        Step(false);
                    }
                    break;
                }
                case 2:
                    for (int k = 0, n = 3 + (int)(rng.NextDouble() * 150); k < n && i < steps; k++) Step(false);
                    break;
                default:
                    for (int f = 0, fs = 1 + rng.Next(5); f < fs; f++)
                    {
                        for (int k = 0, n = 6 + rng.Next(25); k < n && i < steps; k++) Step(true);
                        for (int k = 0, n = 3 + rng.Next(28); k < n && i < steps; k++) Step(false);
                    }
                    break;
            }
        }
        return r;
    }

    /// <summary>(3) THE INVARIANT, as a property: over 200 seeded press patterns a record (half with the Hand's heavy on),
    /// at every step the summed weight is at most elapsed / the written wait + 1; it IS one whole blow plus the time from
    /// the first cut's period end to the last one's over the written wait, less only the cap's loss (so a pattern that
    /// never rests the grip past a full wait is within one cut's share of the bound); and no pattern beats holding by
    /// more than one whole blow.</summary>
    [Theory]
    [InlineData("sunder")]
    [InlineData("oathblade")]
    public void No_press_pattern_beats_the_written_wait_or_the_hold(string id)
    {
        var held = new double[2];
        for (int h = 0; h < 2; h++) { var r = new Rig(id, hand: h == 1); r.Step(true, 7200); held[h] = r.Sum; }
        double worstHold = double.NegativeInfinity, least = double.PositiveInfinity;
        var worst = new[] { double.NegativeInfinity, 0.0 };
        int cuts = 0, rested = 0, capped = 0, drops = 0, heavies = 0, tight = 0;
        for (int seed = 1; seed <= 200; seed++)
        {
            bool hand = seed % 2 == 0;
            var r = Pattern(id, seed, hand, worst);
            worstHold = Math.Max(worstHold, r.Sum - held[hand ? 1 : 0]);
            least = Math.Min(least, r.Sum);
            Assert.True(r.Sum <= held[hand ? 1 : 0] + 1, $"{id} seed {seed}: {r.Sum:F3} beats the hold's {held[hand ? 1 : 0]:F3}");
            cuts += r.Cuts.Count; drops += r.Drops; heavies += r.Cuts.Count(c => c.Heavy);
            rested += r.Cuts.Count(c => c.Rest > 0); capped += r.Cuts.Skip(1).Count(c => c.Weight >= 1 - 1e-12 && !c.Whole);
            Assert.All(r.Cuts, c => Assert.True(c.Rest > 0 || c.Weight == r.W.BlowWeight * c.Scale));
            if (r.CapLoss == 0)
            {
                // no waste: at the last cut's start the sum is within that cut's share of the bound
                tight++;
                var (c0, cn) = (r.Cuts[0], r.Cuts[^1]);
                Assert.InRange(r.Sum - ((cn.Start - c0.Start) / r.Written + 1), -1e-6 - r.W.BlowWeight * 54.0 / 42, r.W.BlowWeight * (54.0 / 42 - 1) + 1e-6);
            }
        }
        Assert.True(rested > 1000 && drops > 20 && heavies > 200 && capped > 100, $"rested {rested} drops {drops} heavies {heavies} capped {capped}");
        output.WriteLine($"{id}: 200 patterns x 120 s, {cuts} cuts ({rested} rested, {capped} capped at a whole blow, {heavies} heavy, {drops} dropped by a dash), {tight} with no cap loss; "
            + $"worst sum - (elapsed / wait + 1) = {worst[0]:+0.0000;-0.0000} (a heavy in hand may add {r0(id):F4}); the account's worst error {worst[1]:E2}; "
            + $"held 120 s = {held[0]:F3} (no Hand) / {held[1]:F3} (Hand); best pattern - hold = {worstHold:+0.000;-0.000}; least pattern {least:F3}");
        static double r0(string id) => (id == "sunder" ? 0.70 / 1.6 : 0.70 / 1.05) * (54.0 / 42 - 1);
    }

    /// <summary>Written blows landed in `secs` by a press plan: `press(step)` says tap (retried each step until it fires:
    /// the buffer) or hold.</summary>
    static double Landed(string id, bool chained, double secs, Func<int, (bool Held, bool Tap)> plan, bool hand = false)
    {
        var r = new Rig(id, chained, hand);
        bool want = false;
        for (int i = 0, n = (int)Math.Round(secs / Dt); i < n; i++)
        {
            var (held, tap) = plan(i);
            want |= tap;
            if (want && r.Tap()) want = false;
            r.Step(held);
        }
        return r.Landed;
    }

    /// <summary>(4) Against the unchained record, the same hands: tapped once a written wait for a minute, the landed
    /// weight is the unchained blows' within one; short holds (1.0 s on, 0.6 s off) land Sunder's within 3%. Oathblade's
    /// unchained record wastes 0.55 s of each such cycle (ready at 1.05 s, its key up until 1.6 s) where the chain's
    /// second cut uses it, so there the chain lands MORE (as it did before this rule), and never more than the wait
    /// allows; its lifts short enough to waste nothing (0.9 s on, 0.15 s off) land the unchained record's within 3%.</summary>
    [Fact]
    public void The_same_presses_land_what_the_unchained_record_lands()
    {
        foreach (var (id, written) in new[] { ("sunder", 1.6), ("oathblade", 1.05) })
        {
            int every = (int)Math.Round(written / Dt);
            double c = Landed(id, true, 60, i => (false, i % every == 0)), u = Landed(id, false, 60, i => (false, i % every == 0));
            output.WriteLine($"{id} tapped once per {written} s for 60 s: chained {c:F3} | unchained {u:F3}");
            Assert.InRange(c - u, -1, 1);
            Assert.InRange(c, 60 / written - 1, 60 / written + 1);
            // With the Hand's heavy on: a heavy cut pays forward its longer period (its share 54/42 of a cut's), and a
            // rested heavy is still capped at one whole blow, so a hand that taps once a written wait loses the heavy's
            // extra share each time one comes round (Oathblade: 0.19 of a blow every sixth blow). Never more.
            double ch = Landed(id, true, 60, i => (false, i % every == 0), hand: true), uh = Landed(id, false, 60, i => (false, i % every == 0), hand: true);
            output.WriteLine($"{id} tapped once per {written} s for 60 s, the Hand on: chained {ch:F3} | unchained {uh:F3}");
            Assert.InRange(ch - uh, -(uh / 6 + 1) * (0.70 / written) * (54.0 / 42 - 1) - 1e-6, 1);
            double hc = Landed(id, true, 60, i => (i % 96 < 60, false)), hu = Landed(id, false, 60, i => (i % 96 < 60, false));
            output.WriteLine($"{id} held 1.0 s on, 0.6 s off for 60 s: chained {hc:F3} | unchained {hu:F3} | {(hc / hu - 1) * 100:+0.0;-0.0}% (the wait allows {60 / written + 1:F2})");
            Assert.True(hc <= 60 / written + 1 + 1e-6);
            if (id == "sunder") Assert.InRange(hc / hu, 0.97, 1.03);
            else Assert.True(hc >= hu);
            double sc = Landed(id, true, 60, i => (i % 63 < 54, false)), su = Landed(id, false, 60, i => (i % 63 < 54, false));
            output.WriteLine($"{id} held 0.9 s on, 0.15 s off for 60 s: chained {sc:F3} | unchained {su:F3} | {(sc / su - 1) * 100:+0.0;-0.0}%");
            Assert.InRange(sc / su, 0.97, 1.03);
        }
    }

    /// <summary>(5) A press buffered through the cut starts the chain's next cut on its beat: no idle, the share to the
    /// bit. A press again inside the grace, after the grip stood free a while, is the chain's next cut too (not an
    /// opening) and carries that idle.</summary>
    [Theory]
    [InlineData("sunder")]
    [InlineData("oathblade")]
    public void A_buffered_press_on_the_beat_carries_nothing_and_a_press_inside_the_grace_carries_its_idle(string id)
    {
        var r = new Rig(id);
        double share = r.W.BlowWeight, written = r.Written;
        r.Step(true, 30);
        var c0 = r.Cuts.Single();
        // let go at 0.5 s and press every step: the buffer
        while (r.Cuts.Count < 2) { r.Tap(); r.Step(false); Assert.True(r.B.Time < c0.End + 0.1); }
        var c1 = r.Cuts[1];
        Assert.Equal((1, 0.0, share), (c1.N, c1.Rest, c1.Weight));
        Assert.Equal(c0.End, c1.Start, 9);
        // held through the second cut and let go just before its period ends: the grace runs from there
        while (r.B.Time < c1.End - 0.1) r.Step(true);
        r.Until(c1.End + 0.15);
        Assert.True(r.W.Chain!.Live);
        double idle = r.B.Time - r.W.Chain.PeriodEnd;
        Assert.InRange(idle, 0.15 - 1e-9, 0.15 + Dt);
        Assert.True(r.Tap());
        var c2 = r.Cuts[2];
        Assert.Equal(2, c2.N);
        Assert.Equal(share + idle / written, c2.Weight, 12);
        Assert.Equal(idle / written, c2.Rest, 12);
    }

    /// <summary>(6) The union's half (Bladestorm's Sunder, on the union's second key) keeps its own rest: its first cut
    /// is a whole blow, a press after a full written wait is whole again, and a shorter rest is its share plus the idle.</summary>
    [Fact]
    public void The_unions_half_opens_whole_after_a_rest()
    {
        var r = new Rig("sunder");
        DevGrants.Apply(r.B, null, "bladestorm", null);
        var storm = r.B.Weapons.Single(x => x.Id == Unions.Find("bladestorm")!.Into);
        var half = Firing.HalfOf(storm)!;
        Assert.True(half.Chained && !storm.Chained);
        r.G = half;
        double share = half.BlowWeight, written = r.Written;
        Assert.Equal(0.70 / 1.6, share, 12);
        Assert.True(r.Tap(storm.Slot2));
        Assert.Equal((0, 1.0), (r.Cuts[0].N, r.Cuts[0].Weight));
        r.Until(r.Cuts[0].End + 0.3);
        double idle = r.B.Time - half.Chain!.PeriodEnd;
        Assert.True(r.Tap(storm.Slot2));
        Assert.Equal(share + idle / written, r.Cuts[1].Weight, 12);
        r.Until(r.Cuts[1].End + 3);
        double landed = r.Landed;
        Assert.Equal(1 + r.Cuts[1].Weight, landed, 9);
        Assert.True(r.Tap(storm.Slot2));
        Assert.Equal((0, 1.0), (r.Cuts[2].N, r.Cuts[2].Weight));
        r.Until(r.Cuts[2].End);
        Assert.Equal(landed + 1, r.Landed, 9);
    }

    /// <summary>(7) An answer mid-chain is still exactly one whole blow (no rest on it), and the cut after it follows the
    /// record's "answer" wait and weighs its share.</summary>
    [Theory]
    [InlineData("sunder")]
    [InlineData("oathblade")]
    public void An_answer_mid_chain_is_one_whole_blow_and_the_next_cut_follows_its_wait(string id)
    {
        var r = new Rig(id, hand: false);
        var ch = r.W.Press!.Chain!;
        Assert.Equal((0.70, 0.85), (ch.Period, ch.Answer));
        while (r.Cuts.Count < 3) r.Step(true);
        r.W.AnswerDue = true;
        while (r.Cuts.Count < 5) r.Step(true);
        var (a, next) = (r.Cuts[3], r.Cuts[4]);
        Assert.True(a.Whole);
        Assert.Equal((0.0, 1.0), (a.Rest, a.Weight));
        Assert.Equal(0.85 / 0.70, a.Scale, 12);
        Assert.Equal(a.Start + 0.85, next.Start, 9);
        Assert.False(next.Whole);
        Assert.Equal((0.0, r.W.BlowWeight), (next.Rest, next.Weight));
        // an answer owed at an opening after a rest: one whole blow, not more
        r.Until(next.End + 2);
        double landed = r.Landed;
        r.W.AnswerDue = true;
        Assert.True(r.Tap());
        Assert.True(r.Cuts[5].Whole);
        Assert.Equal(1.0, r.Cuts[5].Weight);
        r.Until(r.Cuts[5].End - 0.05);
        Assert.Equal(landed + 1, r.Landed, 9);
    }
}
