using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 b1/b2, the LANDED rule) A chained grip keeps a time bank (WeaponInst.PaidTo, Battle.BankOf): a
/// cut weighs what the wait has earned since the grip's last cut that LANDED (struck a body), at most one written blow,
/// never under its own share; only a cut that strikes a body pays, once however many bodies; a whiff spends and counts
/// nothing. Held on target every cut weighs its share to the bit. The shipped records, as they ship.</summary>
public sealed class RestedOpeningTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public RestedOpeningTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;

    sealed record Cut(int N, double Start, double End, double Earned, double Weight, double Scale, bool Heavy, bool Whole);

    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        /// <summary>The weapon that swings (the union's half when one is granted).</summary>
        public WeaponInst G;
        public readonly Enemy E;
        public readonly List<Enemy> More = new();
        public readonly List<Cut> Cuts = new();
        /// <summary>What each cut landed (BlowN's growth while it was the chain's cut), by its index in Cuts.</summary>
        public readonly List<double> Paid = new();
        /// <summary>The body is away (40 m behind her) while she still aims where it stood: a gap, nothing in reach.</summary>
        public bool Gap;
        public int Drops, HeavyLanded;
        double last = double.NaN, dropped = double.NaN, landed0;

        public Rig(string id, bool chained = true, bool hand = true, int bodies = 1)
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
            if (!chained) W.Press = W.Press!.WithChain(null);
            Assert.Equal(chained, W.Chained);
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = 1e9;
            E.AttackT = E.RangedT = 999;
            for (int i = 1; i < bodies; i++)
            {
                var f = B.SpawnEnemy("footpad", 2, 0)!;
                f.Hp = f.MaxHp = 1e9; f.AttackT = f.RangedT = 999;
                More.Add(f);
            }
        }

        /// <summary>The written wait now (the period over the cut's share): W of the bank.</summary>
        public double Written => Firing.CooldownOf(B, G) / G.BlowWeight;
        /// <summary>The written blows LANDED (every landed cast's weight, counted; a whiff counts 0).</summary>
        public double Landed => G.BlowN + G.BlowPart;
        (double X, double Z) Aim => (B.Player.X + 2, B.Player.Z);

        void Pin()
        {
            var p = B.Player;
            (E.X, E.Z) = Gap ? (p.X - 40, p.Z) : (p.X + 2, p.Z);
            E.Vx = E.Vz = 0;
            for (int i = 0; i < More.Count; i++) { var f = More[i]; (f.X, f.Z) = Gap ? (p.X - 40, p.Z + 1 + i) : (p.X + 2, p.Z + (i + 1) * 0.3 * (i % 2 == 0 ? 1 : -1)); f.Vx = f.Vz = 0; }
        }

        public void Step(bool held, int steps = 1)
        {
            for (int i = 0; i < steps; i++)
            {
                Pin();
                B.HoldSkill(W.Slot, held, Aim.X, Aim.Z);
                B.Tick(Dt, 0, 0);
                Note();
            }
        }

        public bool Tap(int? slot = null)
        {
            Pin();
            bool ok = B.PressSkill(slot ?? W.Slot, Aim.X, Aim.Z);
            Note();
            return ok;
        }

        public void Until(double time) { while (B.Time < time - 1e-9) Step(false); }

        void Note()
        {
            B.Events.Drain();
            double l = Landed;
            if (l > landed0 + 1e-12)
            {
                if (Paid.Count > 0) Paid[^1] += l - landed0;
                if (G.HeavyCast) HeavyLanded++;
            }
            landed0 = l;
            if (G.Chain is not { } c) return;
            if (c.Dropped && dropped != c.StartAt) { dropped = c.StartAt; Drops++; }
            if (!c.Live || c.StartAt == last) return;
            last = c.StartAt;
            Assert.Equal(GripMeter.WeightOf(G), c.Weight);
            Cuts.Add(new Cut(c.Cut, c.StartAt, c.PeriodEnd, c.Rest, c.Weight, c.PeriodScale, c.Heavy, c.Whole));
            Paid.Add(0);
        }
    }

    /// <summary>(1) THE INVARIANT, as a property: 400 seeded press patterns a record, 60 s each (holds, taps, rests,
    /// flutters, each on target or in a GAP with no body in reach; dashes; the Hand on for half; answers off). At every
    /// step the summed LANDED weight is at most (t + W) / W plus what the cut in hand has paid forward past now
    /// (max(0, PaidTo - t) / W, never more than the time it occupies), and at every cut's period end the plain bound
    /// (t + W) / W. The summed heavy COUNT never runs ahead of holding on target over the same time.</summary>
    [Theory]
    [InlineData("sunder")]
    [InlineData("oathblade")]
    public void No_press_pattern_beats_the_written_wait_or_the_hold(string id)
    {
        const int steps = 3600, seeds = 400;
        var heldL = new double[2][]; var heldH = new int[2][];
        for (int h = 0; h < 2; h++)
        {
            var r = new Rig(id, hand: h == 1);
            heldL[h] = new double[steps]; heldH[h] = new int[steps];
            for (int i = 0; i < steps; i++) { r.Step(true); heldL[h][i] = r.Landed; heldH[h][i] = r.HeavyLanded; }
        }
        double worstStep = double.NegativeInfinity, worstEnd = double.NegativeInfinity, worstHold = double.NegativeInfinity;
        int capped = 0, cappedCuts = 0, cuts = 0, whiffs = 0, drops = 0, heavies = 0, rested = 0, worstHeavy = int.MinValue;
        for (int seed = 1; seed <= seeds; seed++)
        {
            bool hand = seed % 2 == 0;
            int hi = hand ? 1 : 0;
            var r = new Rig(id, hand: hand);
            var rng = new Random(seed);
            int i = 0, ends = 0;
            void Step(bool held)
            {
                r.Step(held);
                double t = r.B.Time, wt = r.Written, l = r.Landed, paid = double.IsNaN(r.G.PaidTo) ? t : r.G.PaidTo;
                double over = l - ((t + wt) / wt + Math.Max(0, paid - t) / wt);
                worstStep = Math.Max(worstStep, over);
                Assert.True(over <= 1e-9, $"{id} seed {seed} t {t:F3}: landed {l:F4} over the bound by {over:F4}");
                // every cut's period end passed: the plain bound
                while (ends < r.Cuts.Count && r.Cuts[ends].End <= t + 1e-9)
                {
                    double o2 = l - (t + wt) / wt;
                    worstEnd = Math.Max(worstEnd, o2);
                    Assert.True(o2 <= 1e-9, $"{id} seed {seed} t {t:F3}: landed {l:F4} over the plain bound at a period end by {o2:F4}");
                    ends++;
                }
                int dh = r.HeavyLanded - heldH[hi][i];
                worstHeavy = Math.Max(worstHeavy, dh);
                // (at most one heavy of phase: a whole opening lands at once where the hold's cut is still before its
                // contact; the count itself is bounded by the landed weight above)
                Assert.True(dh <= 1, $"{id} seed {seed} t {t:F3}: {r.HeavyLanded} heavies landed, held on target {heldH[hi][i]}");
                worstHold = Math.Max(worstHold, l - heldL[hi][i]);
                i++;
            }
            while (i < steps)
            {
                r.Gap = rng.NextDouble() < 0.35;
                if (rng.NextDouble() < 0.2) r.B.Dash(rng.Next(2) == 0 ? 1 : -1, 0);
                switch (rng.Next(4))
                {
                    case 0:
                    {
                        int n = 3 + (int)(rng.NextDouble() * 200), dashAt = rng.NextDouble() < 0.35 ? rng.Next(n) : -1;
                        for (int k = 0; k < n && i < steps; k++) { if (k == dashAt) r.B.Dash(0, -1); Step(true); }
                        break;
                    }
                    case 1:
                    {
                        int every = (int)Math.Round((0.2 + rng.NextDouble() * 2.8) * 60), taps = 1 + rng.Next(5);
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
            cuts += r.Cuts.Count; drops += r.Drops; heavies += r.HeavyLanded;
            whiffs += r.Paid.Count(p => p == 0);
            rested += r.Cuts.Skip(1).Count(c => !c.Whole && c.Weight > r.G.BlowWeight * c.Scale + 1e-12);
            int cap = r.Cuts.Skip(1).Count(c => c.Weight >= 1 - 1e-12 && !c.Whole);
            cappedCuts += cap; if (cap > 0) capped++;
            // a cut that landed paid exactly its weight (once), a whiff nothing
            for (int k = 0; k < r.Cuts.Count; k++) Assert.True(r.Paid[k] == 0 || Math.Abs(r.Paid[k] - r.Cuts[k].Weight) < 1e-9 || r.Cuts[k].Whole, $"{id} seed {seed} cut {k}: paid {r.Paid[k]:F4} of {r.Cuts[k].Weight:F4}");
        }
        Assert.True(whiffs > 500 && drops > 20 && heavies > 200 && rested > 500 && capped > 50, $"whiffs {whiffs} drops {drops} heavies {heavies} rested {rested} capped {capped}");
        output.WriteLine($"{id}: {seeds} patterns x 60 s, {cuts} cuts ({whiffs} whiffed or dropped, {rested} rested, {cappedCuts} capped at a whole blow in {capped} patterns, {heavies} heavies landed, {drops} dropped by a dash)");
        output.WriteLine($"{id}: worst landed - bound (with the cut in hand's paid-forward) {worstStep:+0.0000;-0.0000}; worst at a period end - (t + W) / W {worstEnd:+0.0000;-0.0000}; "
            + $"worst heavies - held's {worstHeavy:+0;-0}; worst landed - held's (same step) {worstHold:+0.0000;-0.0000}; held 60 s = {heldL[0][^1]:F3} (no Hand) / {heldL[1][^1]:F3} (Hand)");
    }

    /// <summary>(2) One cut on three bodies: one weight, one commit (BlowN grows by the cut's weight, PaidTo by its weight
    /// x W), and every body struck.</summary>
    [Theory]
    [InlineData("sunder")]
    [InlineData("oathblade")]
    public void One_cut_on_several_bodies_is_one_weight_and_one_commit(string id)
    {
        var r = new Rig(id, hand: false, bodies: 3);
        while (r.Cuts.Count < 6) r.Step(true);
        r.Until(r.Cuts[^1].Start - Dt);
        for (int k = 0; k < r.Cuts.Count - 1; k++) Assert.Equal(r.Cuts[k].Weight, r.Paid[k], 9);
        Assert.Equal(r.Cuts.Take(r.Cuts.Count - 1).Sum(c => c.Weight), r.Landed, 9);
        // held on target: each landed cut paid its weight x W once, from where the one before paid to: the bank stands
        // at the last landed cut's start (the first, whole, paid from start - W to its start)
        Assert.Equal(r.Cuts[^2].Start, r.G.PaidTo, 9);
        Assert.True(r.E.Hp < 1e9 && r.More.All(f => f.Hp < 1e9));
    }

    /// <summary>(3) Held on target, both records, Hand on and off, a minute: the first cut is a whole blow, every cut
    /// after it weighs its share TO THE BIT (a heavy share x scale) and lands exactly that. (SwingChainTests' held minute
    /// pins the beats, rates and sides, and runs in the same filter, unchanged.)</summary>
    [Theory]
    [InlineData("sunder", false)]
    [InlineData("sunder", true)]
    [InlineData("oathblade", false)]
    [InlineData("oathblade", true)]
    public void Held_on_target_every_cut_but_the_first_weighs_its_share_to_the_bit(string id, bool hand)
    {
        var r = new Rig(id, hand: hand);
        r.Step(true, 3600);
        Assert.True(r.Cuts.Count > 60);
        Assert.Equal(1.0, r.Cuts[0].Weight);
        foreach (var c in r.Cuts.Skip(1)) Assert.Equal(r.G.BlowWeight * c.Scale, c.Weight);
        for (int k = 0; k < r.Cuts.Count - 1; k++) Assert.Equal(r.Cuts[k].Weight, r.Paid[k], 9);
        Assert.True(hand || id == "oathblade" || r.Cuts.Any(c => c.Heavy));
        output.WriteLine($"{id} hand {hand}: {r.Cuts.Count} cuts, {r.Cuts.Count(c => c.Heavy)} heavy, landed {r.Landed:F4}");
    }

    /// <summary>(4) A whiff then a landed cut: the landed one carries the whole rest earned since the last LANDED cut
    /// (capped at 1). Flailing (holding in the gap), tapping in the gap and resting all open on the same weight.</summary>
    [Theory]
    [InlineData("sunder", 0.75)]
    [InlineData("oathblade", 0.75)]
    [InlineData("sunder", 1.3)]
    [InlineData("oathblade", 2.0)]
    public void A_whiff_spends_nothing_and_the_next_landed_cut_carries_the_rest(string id, double gap)
    {
        double? weight = null;
        foreach (var mode in new[] { "flail", "tap", "rest" })
        {
            var r = new Rig(id, hand: false);
            while (r.Cuts.Count < 5) r.Step(true);
            double p = r.Cuts[^1].End, landedAt = 0;
            // release so the 5th is the last cut held on target; it lands
            r.Until(p);
            // (held on target the bank stands at the last landed cut's start)
            Assert.Equal(r.Cuts[^1].Start, r.G.PaidTo, 9);
            double paid = r.G.PaidTo;
            landedAt = r.Landed;
            int n0 = r.Cuts.Count;
            r.Gap = true;
            if (mode == "flail") while (r.B.Time < p + Math.Min(gap, 0.7) - 0.1) r.Step(true);
            if (mode == "tap") Assert.True(r.Tap());
            r.Until(p + gap);
            if (mode != "rest") { Assert.True(r.Cuts.Count > n0); Assert.Equal(landedAt, r.Landed, 12); }
            r.Gap = false;
            while (r.G.Timer > 0) r.Step(false);
            double start = r.B.Time;
            Assert.True(r.Tap());
            var c = r.Cuts[^1];
            double expect = Blows.Rested(r.G.BlowWeight * c.Scale, (c.Start - paid) / r.Written);
            Assert.Equal(expect, c.Weight, 12);
            Assert.Equal(Math.Min(1, (c.Start - paid) / r.Written), c.Earned, 12);
            r.Until(c.End);
            Assert.Equal(landedAt + c.Weight, r.Landed, 9);
            output.WriteLine($"{id} gap {gap:F2} {mode}: opens at +{start - p:F3} s on weight {c.Weight:F4} (share {r.G.BlowWeight:F4})");
            weight ??= c.Weight;
            Assert.Equal(weight.Value, c.Weight, 12);
        }
    }

    /// <summary>(5) The block's answer is one whole blow, against a full bank (after a rest) and an empty one (held on
    /// target), at each block rate and answer wait of lead 14's table: printed, the written blows landed in each 0.85 s
    /// span from an answer's start; asserted, the answer never pays more than one blow's weight in its own wait's span.</summary>
    [Fact]
    public void The_answer_pays_one_blow_in_its_wait_full_bank_or_empty()
    {
        double?[] answers = [null, 0.85, 0.78, 0.70];
        double[] gaps = [3, 7, 10];
        foreach (var answer in answers)
        {
            string line = $"answer wait {(answer is double a0 ? a0.ToString("F2") : "unset (1.05)")}:";
            Rig Make()
            {
                var r = new Rig("oathblade", hand: false);
                // (null: unset, the blow's own wait; the shipped record writes 0.85)
                { var ch = r.W.Press!.Chain!; r.W.Press = r.W.Press.WithChain(new ChainDef { Grace = ch.Grace, Recover = ch.Recover, Period = ch.Period, Answer = answer }); }
                return r;
            }
            double Span(Rig r, Cut c, double len, List<(double T, double L)> trace) =>
                trace.Where(x => x.T >= c.Start - 1e-9 && x.T < c.Start + len - 1e-9).Sum(x => x.L);
            foreach (double g in gaps)
            {
                // empty bank: held on target, a block about every g s when no cut is pending (the answer is the next cut)
                var r = Make();
                var trace = new List<(double T, double L)>();
                var jit = new Random(100 + (int)g);
                double next = g / 2, l0 = 0;
                while (r.B.Time < 240)
                {
                    if (r.B.Time >= next && r.B.PendingBlows == 0 && !r.W.AnswerDue) { r.W.AnswerDue = true; next += g - 1 + 2 * jit.NextDouble(); }
                    r.Step(true);
                    trace.Add((r.B.Time, r.Landed - l0)); l0 = r.Landed;
                }
                var ans = r.Cuts.Where(c => c.Whole).ToList();
                Assert.True(ans.Count > 15);
                double wait = (answer ?? 1.05);
                foreach (var c in ans)
                {
                    Assert.Equal(1.0, c.Weight);
                    Assert.True(Span(r, c, wait, trace) <= 1 + 1e-9, $"answer at {c.Start:F3} pays {Span(r, c, wait, trace):F4} in its wait");
                }
                var spans = ans.Select(c => Span(r, c, 0.85, trace)).ToList();
                line += $" | empty bank, block ~{g} s: {ans.Count} answers, blows per 0.85 s span mean {spans.Average():F4} max {spans.Max():F4}";
            }
            {
                // full bank: rested 3 s, then the answer
                var r = Make();
                while (r.Cuts.Count < 3) r.Step(true);
                r.Until(r.B.Time + 3);
                var trace = new List<(double T, double L)>();
                double l0 = r.Landed;
                r.W.AnswerDue = true;
                Assert.True(r.Tap());
                trace.Add((r.B.Time, r.Landed - l0)); l0 = r.Landed;
                var c = r.Cuts[^1];
                Assert.True(c.Whole);
                Assert.Equal(1.0, c.Weight);
                while (r.B.Time < c.Start + 1.2) { r.Step(true); trace.Add((r.B.Time, r.Landed - l0)); l0 = r.Landed; }
                Assert.True(Span(r, c, answer ?? 1.05, trace) <= 1 + 1e-9);
                line += $" | full bank: {Span(r, c, 0.85, trace):F4} per 0.85 s span";
            }
            output.WriteLine(line);
        }
    }

    /// <summary>(6) Sunder with Bladestorm carried beside it (the Warden's own skill since 13 Nov 2026; once a union's half):
    /// its first cut is whole; after a rest it carries what it earned since its last
    /// landed cut; after more than a written wait it opens whole again.</summary>
    [Fact]
    public void Sunder_beside_Bladestorm_opens_whole_after_a_rest()
    {
        var r = new Rig("sunder");
        var storm = r.B.AddWeapon("bladestorm", Weapons.MaxRank)!;
        var half = r.W;
        Assert.True(half.Chained && !storm.Chained);
        r.G = half;
        double share = half.BlowWeight, written = r.Written;
        Assert.Equal(0.70 / 1.6, share, 12);
        Assert.True(r.Tap(half.Slot));
        Assert.Equal((0, 1.0), (r.Cuts[0].N, r.Cuts[0].Weight));
        r.Until(r.Cuts[0].End + 0.3);
        double paid = half.PaidTo;
        Assert.True(r.Tap(half.Slot));
        Assert.Equal(Blows.Rested(share * r.Cuts[1].Scale, (r.Cuts[1].Start - paid) / written), r.Cuts[1].Weight, 12);
        r.Until(r.Cuts[1].End + 3);
        double landed = r.Landed;
        Assert.Equal(1 + r.Cuts[1].Weight, landed, 9);
        Assert.True(r.Tap(half.Slot));
        Assert.Equal((0, 1.0), (r.Cuts[2].N, r.Cuts[2].Weight));
        r.Until(r.Cuts[2].End);
        Assert.Equal(landed + 1, r.Landed, 9);
    }

    /// <summary>(7) Momentum held (its faster cuts on fodder), then a long rest: the next opening is a whole blow (the
    /// PayTo clamp at the period end keeps the fast cuts from running the bank into the future).</summary>
    [Theory]
    [InlineData("sunder")]
    [InlineData("oathblade")]
    public void A_momentum_hold_then_a_long_rest_opens_whole(string id)
    {
        var r = new Rig(id, hand: false);
        r.B.Lamps = new LampLoadout();
        r.B.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "momentum", Args = new Dictionary<string, double> { ["kills"] = 1, ["sooner"] = 0.3 } });
        var fodder = new List<Enemy>();
        for (int i = 0; i < 600; i++)
        {
            fodder.RemoveAll(f => !f.Alive);
            while (fodder.Count < 3)
            {
                var f = r.B.SpawnEnemy("footpad", r.B.Player.X + 1.5, r.B.Player.Z)!;
                f.Hp = f.MaxHp = 0.01; f.AttackT = f.RangedT = 999;
                fodder.Add(f);
            }
            for (int k = 0; k < fodder.Count; k++) { var f = fodder[k]; f.X = r.B.Player.X + 1.5; f.Z = r.B.Player.Z + (k - 1) * 0.2; f.Vx = f.Vz = 0; }
            r.Step(true);
        }
        Assert.True(r.G.Kills > 10, $"{r.G.Kills} kills");
        double held = r.Landed, t1 = r.B.Time;
        Assert.True(r.G.PaidTo <= r.Cuts[^1].End + 1e-9, $"PaidTo {r.G.PaidTo:F3} past the last period end {r.Cuts[^1].End:F3}");
        r.Until(t1 + 5);
        Assert.True(r.Tap());
        Assert.Equal(1.0, r.Cuts[^1].Weight);
        output.WriteLine($"{id}: momentum held 10 s, {r.G.Kills} kills, landed {held:F3}; after 5 s the opening weighs {r.Cuts[^1].Weight:F4}");
    }
}
