using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 J12c) sunderer.momentum under a chain of weighed cuts: kills are counted per WRITTEN blow (the cuts
/// that share BlowN before their cast), and a blow that reaches the count pays the NEXT written blow: every cut of it
/// waits x (1 - sooner), once, on its period at its start (so the clip's rate and beats follow) and again at its
/// contact. Unchained (BlowWeight 1): the old rule (the reaching swing's own wait). No shipped record has a chain yet:
/// every chained run chains a COPY of Oathblade's record (period 0.70, grace 0.40, recover 18; its written wait 1.05).</summary>
public sealed class MomentumChainTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public MomentumChainTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0, Fast = 0.75;

    sealed class Cut
    {
        public int I, Key, Kills; public bool Landed; public string? Clip;
        /// <summary>P0: the period at the cut's start (PeriodEnd - StartAt); P1: the same after its contact.</summary>
        public double Start, Contact, Cancel, Rate, Scale, Cd, P0, P1 = double.NaN, AnimRate, LandT;
    }

    sealed class Run
    {
        public readonly Battle B; public readonly WeaponInst W; public readonly Enemy E;
        public readonly List<Cut> Cuts = new();
        /// <summary>Every blow landed (Ev.Slash): when its swing was pressed, the kills inside its cast.</summary>
        public readonly List<(double T, int Kills)> Casts = new();
        /// <summary>Fodder to stand in the arc when cut I starts (they die to its blow).</summary>
        public Dictionary<int, int> Feed = new();
        readonly List<Enemy> fodder = new();
        readonly int need;
        double last = double.NaN;

        /// <param name="period">0.70: the chain of weighed cuts; null: unchained.</param>
        public Run(double? period = 0.70, bool lit = true, int need = 3, bool hand = false, bool answer = false)
        {
            this.need = need;
            B = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
            });
            if (hand) B.Calling = "warden";
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -B.Stats.Get(Stat.CritChance), "test"));
            W = B.Weapons[0];
            W.Timer = 0;
            Assert.True(W.Tags.Has(Tag.Melee));
            // (the switch: the shipped record carries a chain; the unchained run takes it off its own copy)
            W.Press = W.Press!.WithChain(period is double p ? new ChainDef { Grace = 0.40, Recover = 18, Period = p } : null);
            B.Lamps = new LampLoadout();
            if (lit) B.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "momentum", Args = new Dictionary<string, double> { ["kills"] = need, ["sooner"] = 1 - Fast } });
            if (answer) { B.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "oathblade.shield_and_edge", Args = new Dictionary<string, double>() }); B.AddBoon("warding"); }
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = 1e9;
            E.AttackT = E.RangedT = 999;
        }

        public double Wait => Firing.CooldownOf(B, W);
        public double Worth => (W.BlowN + W.BlowPart) / B.Time;

        public void Spawn(int n)
        {
            for (int i = 0; i < n; i++)
            {
                var f = B.SpawnEnemy("footpad", B.Player.X + 1.5, B.Player.Z)!;
                f.Hp = f.MaxHp = 0.01; f.AttackT = f.RangedT = 999;
                fodder.Add(f);
            }
        }

        public void Block()
        {
            int n = B.Blocks;
            B.Player.Iframes = 0; B.Player.BlockT = 0;
            B.HurtPlayer(10, School.Physical, "test", null);
            Assert.Equal(n + 1, B.Blocks);
        }

        public Run Step(int steps = 1)
        {
            for (int s = 0; s < steps; s++)
            {
                var p = B.Player;
                E.X = p.X + 2; E.Z = p.Z; E.Vx = E.Vz = 0;
                fodder.RemoveAll(f => !f.Alive || f.Hp > 0.01);
                for (int i = 0; i < fodder.Count; i++) { var f = fodder[i]; f.X = p.X + 1.5; f.Z = p.Z + (i % 7 - 3) * 0.2; f.Vx = f.Vz = 0; }
                B.HoldSkill(W.Slot, true, E.X, E.Z);
                int k0 = W.Kills;
                B.Tick(Dt, 0, 0);
                foreach (var ev in B.Events.Drain()) if (ev is Ev.Slash) Casts.Add((B.Player.AttackAnim?.T ?? B.Time, W.Kills - k0));
                if (W.Chain is not { Live: true } c) continue;
                if (c.StartAt != last)
                {
                    last = c.StartAt;
                    Cuts.Add(new Cut { I = Cuts.Count, Key = W.BlowN, Clip = c.Clip, Start = c.StartAt, Contact = c.ContactAt, Cancel = c.CancelAt, Rate = c.Rate, Scale = c.PeriodScale,
                        Cd = Wait, P0 = c.PeriodEnd - c.StartAt, AnimRate = B.Player.AttackAnim!.Rate });
                    if (Feed.TryGetValue(Cuts.Count - 1, out int n)) Spawn(n);
                }
                var cur = Cuts[^1];
                if (!cur.Landed && c.Landed) { cur.Landed = true; cur.Kills = W.Kills - k0; cur.P1 = c.PeriodEnd - c.StartAt; cur.LandT = B.Time; }
            }
            return this;
        }

        /// <summary>Held until n cuts have started and the last has landed.</summary>
        public Run ToCuts(int n) { while (Cuts.Count < n || !Cuts[^1].Landed) Step(); return this; }

        /// <summary>The rule, cut by cut: a cut is paid when the cuts of the written blow before its own made the count.</summary>
        public bool Paid(Cut c) => Cuts.Where(x => x.Landed && x.Key == c.Key - 1).Sum(x => x.Kills) >= need && Cuts.Any(x => x.Landed && x.Key == c.Key - 1);

        /// <summary>Every cut's period at its start and after its contact is its wait x its share x (0.75 when paid), exactly once.</summary>
        public void Check(bool lit = true)
        {
            foreach (var c in Cuts)
            {
                double want = c.Cd * c.Scale * (lit && Paid(c) ? Fast : 1);
                Assert.True(Math.Abs(want - c.P0) < 1e-9, $"cut {c.I} (blow {c.Key}) start: period {c.P0:R}, want {want:R}");
                if (c.Landed) Assert.True(Math.Abs(want - c.P1) < 1e-9, $"cut {c.I} (blow {c.Key}) after contact: period {c.P1:R}, want {want:R}");
            }
        }

        public int[] PaidCuts => Cuts.Where(c => Math.Abs(c.P0 - c.Cd * c.Scale * Fast) < 1e-9).Select(c => c.I).ToArray();
        public int[] PaidAfter => Cuts.Where(c => c.Landed && Math.Abs(c.P1 - c.Cd * c.Scale * Fast) < 1e-9).Select(c => c.I).ToArray();
    }

    static Run Fed(params (int Cut, int N)[] feed)
    {
        var r = new Run();
        foreach (var (c, n) in feed) r.Feed[c] = n;
        r.ToCuts(9);
        // (no Hand: plain cuts at 2/3 of a blow, so the written blows are two cuts, one cut, two, one ...)
        Assert.Equal(new[] { 0, 0, 1, 2, 2, 3, 4, 4, 5 }, r.Cuts.Select(c => c.Key).ToArray());
        foreach (var (c, n) in feed) Assert.Equal(n, r.Cuts[c].Kills);
        r.Check();
        return r;
    }

    [Fact] // T1
    public void Kills_count_over_all_the_cuts_of_one_written_blow_and_pay_every_cut_of_the_next()
    {
        // 2 + 1 over the two cuts of blow 2: blow 3 (cut 5) is paid, at its start and after its contact; nothing else
        var r = Fed((3, 2), (4, 1));
        Assert.Equal(new[] { 5 }, r.PaidCuts);
        Assert.Equal(new[] { 5 }, r.PaidAfter);
        Assert.Equal(r.Wait * Fast, r.Cuts[5].P0, 9);
        // 3 in the one cut of blow 1: both cuts of blow 2 are paid, and only they
        r = Fed((2, 3));
        Assert.Equal(new[] { 3, 4 }, r.PaidCuts);
        Assert.Equal(new[] { 3, 4 }, r.PaidAfter);
    }

    [Fact] // T2
    public void Three_kills_in_one_cut_pay_nothing_inside_its_own_blow()
    {
        var r = Fed((3, 3));
        // the reaching cut's own wait is whole, and so is its blow's second cut; the next blow's is paid
        Assert.Equal(r.Wait, r.Cuts[3].P1, 9);
        Assert.Equal(r.Wait, r.Cuts[4].P0, 9);
        Assert.Equal(new[] { 5 }, r.PaidCuts);
        Assert.Equal(new[] { 5 }, r.PaidAfter);
    }

    [Fact] // T3
    public void Below_the_count_in_each_blow_pays_nothing_the_count_starts_again_with_the_blow()
    {
        var r = Fed((3, 1), (4, 1), (5, 2), (6, 2));
        Assert.Empty(r.PaidCuts);
        Assert.Empty(r.PaidAfter);
    }

    [Fact] // T4
    public void Blows_that_reach_back_to_back_are_each_paid_once()
    {
        // blow 1 reaches (cut 2); blow 2 reaches on its first cut (3); blow 3 reaches (5); blow 4 (6, 7) does not
        var r = Fed((2, 3), (3, 3), (5, 3));
        Assert.Equal(new[] { 3, 4, 5, 6, 7 }, r.PaidCuts);
        Assert.Equal(new[] { 3, 4, 5, 6, 7 }, r.PaidAfter);
        foreach (int i in new[] { 3, 4, 5, 6, 7 }) { Assert.Equal(r.Wait * Fast, r.Cuts[i].P0, 9); Assert.Equal(r.Wait * Fast, r.Cuts[i].P1, 9); }
        Assert.Equal(r.Wait, r.Cuts[8].P0, 9);
    }

    [Fact] // T5
    public void A_paid_cuts_clip_runs_faster_by_the_same_factor_and_its_beats_with_it()
    {
        var r = Fed((2, 3));
        var paid = r.Cuts[3];
        var plain = r.Cuts.First(c => c.I > 4 && c.Clip == paid.Clip);
        output.WriteLine($"clip {paid.Clip}: plain rate {plain.Rate:R} contact +{plain.Contact - plain.Start:R} cancel +{plain.Cancel - plain.Start:R} | paid rate {paid.Rate:R} contact +{paid.Contact - paid.Start:R} cancel +{paid.Cancel - paid.Start:R} | AttackAnim rate {paid.AnimRate:R}");
        Assert.Equal(plain.Rate / Fast, paid.Rate, 9);
        Assert.Equal(HerEvents.ChainBeats(paid.Clip, false).Len / (r.Wait * Fast), paid.Rate, 9);
        Assert.Equal(paid.Rate, paid.AnimRate);
        Assert.Equal(plain.Rate, plain.AnimRate);
        Assert.Equal((plain.Contact - plain.Start) * Fast, paid.Contact - paid.Start, 9);
        Assert.Equal((plain.Cancel - plain.Start) * Fast, paid.Cancel - paid.Start, 9);
        // the blow lands on the step its (earlier) contact falls in
        Assert.InRange(paid.LandT, paid.Contact - 1e-9, paid.Contact + Dt);
    }

    [Fact] // T6
    public void Always_on_the_chain_fires_as_many_blows_worth_a_second_as_the_unchained_skill()
    {
        var c = new Run(need: 0).Step(3600);
        var u = new Run(null, need: 0).Step(3600);
        double law = 1 / (u.Wait * Fast);
        output.WriteLine($"always on: blows' worth per second chained {c.Worth:0.0000} | unchained {u.Worth:0.0000} | written wait x 0.75 gives {law:0.0000}");
        c.Check();
        Assert.InRange(c.Worth / u.Worth, 0.98, 1.02);
        Assert.InRange(c.Worth / law, 0.98, 1.02);
        Assert.InRange(u.Worth / law, 0.98, 1.02);
    }

    /// <summary>T7, a MEASUREMENT (nothing pinned but that both sides earn payouts): kills that come thinly. Fodder walks
    /// into the arc one at a time at a seeded rate (the same arrivals both sides), each dying to the next blow.</summary>
    [Fact]
    public void Scarce_kills_measured_chained_against_unchained()
    {
        foreach (double rate in new[] { 1.5, 2.55, 4.0 })
        {
            var (cs, us, cw, uw, cb, ub) = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
            const int seeds = 4, steps = 7200;
            for (int seed = 1; seed <= seeds; seed++)
                foreach (bool chained in new[] { true, false })
                {
                    var r = new Run(chained ? 0.70 : null);
                    var rng = new Random(seed);
                    for (int i = 0; i < steps; i++) { if (rng.NextDouble() < rate * Dt) r.Spawn(1); r.Step(); }
                    if (chained)
                    {
                        r.Check();
                        var blows = r.Cuts.Where(c => c.Landed).GroupBy(c => c.Key).Select(g => g.Sum(c => c.Kills)).ToList();
                        cs += blows.Count(k => k >= 3) / (double)blows.Count / seeds; cw += r.Worth / seeds; cb += 1 / (r.Wait / r.W.BlowWeight) / seeds;
                    }
                    else { us += r.Casts.Count(k => k.Kills >= 3) / (double)r.Casts.Count / seeds; uw += r.Worth / seeds; ub += 1 / r.Wait / seeds; }
                }
            output.WriteLine($"T7 kills {rate:0.00}/s, {seeds} seeds x {steps / 60} s: written blows that earn the payout chained {cs:P1} | unchained {us:P1}; " +
                $"blows' worth per second chained {cw:0.0000} | unchained {uw:0.0000} (chained/unchained {cw / uw:0.0000}; no momentum {cb:0.0000} | {ub:0.0000}; " +
                $"gain chained {cw / cb - 1:P1} | unchained {uw / ub - 1:P1})");
            Assert.True(cs > 0 && us > 0);
        }
    }

    [Fact] // T8
    public void A_heavy_cut_of_a_paid_blow_waits_its_longer_period_less_the_same_share()
    {
        var r = new Run(hand: true);
        for (int i = 0; i < 20; i++) r.Feed[i] = 3;
        r.ToCuts(20).Check();
        var heavy = r.Cuts.Where(c => c.I >= 2 && c.Scale > 1 + 1e-6).ToList();
        Assert.NotEmpty(heavy);
        foreach (var h in heavy)
        {
            output.WriteLine($"heavy cut {h.I} (blow {h.Key}): wait {h.Cd:R} x scale {h.Scale:R} x {Fast} = {h.P0:R} at its start, {h.P1:R} after its contact");
            Assert.Equal(h.Cd * h.Scale * Fast, h.P0, 9);
            Assert.Equal(h.Cd * h.Scale * Fast, h.P1, 9);
        }
    }

    [Fact] // T9
    public void A_cut_of_a_paid_blow_dropped_by_a_dash_leaves_the_rest_of_that_blow_paid()
    {
        var r = new Run();
        r.Feed[2] = 3;
        while (r.Cuts.Count < 4) r.Step();
        Assert.Equal(1, r.B.PendingBlows);
        int key = r.W.BlowN;
        Assert.True(r.B.Dash(0, -1));
        Assert.Equal(0, r.B.PendingBlows);
        r.ToCuts(8);
        Assert.False(r.Cuts[3].Landed);
        // the dropped cut never cast: the blow it was part of is still the one being made, by the next two cuts
        Assert.Equal(new[] { key, key, key, key + 1 }, r.Cuts.Skip(3).Take(4).Select(c => c.Key).ToArray());
        Assert.Equal(new[] { 3, 4, 5 }, r.PaidCuts);
        Assert.Equal(new[] { 4, 5 }, r.PaidAfter);
        Assert.Equal(r.Wait, r.Cuts[6].P0, 9);
    }

    [Fact] // T10
    public void Unchained_lit_but_never_earning_is_the_unlit_run_step_for_step_and_a_paid_swing_is_the_old_rule()
    {
        // lit, no kills v not lit: the same press on the same step, every swing (the unchained rule is untouched)
        var lit = new Run(null).Step(1500);
        var unlit = new Run(null, lit: false).Step(1500);
        Assert.True(lit.Casts.Count > 20);
        Assert.Equal(unlit.Casts.Select(k => k.T).ToArray(), lit.Casts.Select(k => k.T).ToArray());
        Assert.Equal(unlit.W.Timer, lit.W.Timer);
        var r = new Run(null);
        for (int i = 0; i < 1500; i++) { if (i % 100 == 20) r.Spawn(i / 100 % 3 == 0 ? 2 : 3 + i / 100 % 2); r.Step(); }
        Assert.Equal(1, r.W.BlowWeight);
        Assert.Equal((int.MinValue, 0, false), (r.W.MomKey, r.W.MomKills, r.W.MomFast));
        Assert.Contains(r.Casts, k => k.Kills == 2);
        // the old rule: the swing that killed three has its OWN wait x 0.75 (press to press), every other the whole wait.
        // (tighten to the written wait after the clock commit: today's unchained deferred swing runs a step short on some blows)
        int paid = 0;
        for (int i = 0; i + 1 < r.Casts.Count; i++)
        {
            bool p = r.Casts[i].Kills >= 3;
            double want = r.Wait * (p ? Fast : 1), got = r.Casts[i + 1].T - r.Casts[i].T;
            Assert.True(Math.Abs(got - want) < Dt + 1e-9, $"swing {i} ({r.Casts[i].Kills} kills): next after {got:R}, want {want:R}");
            if (p) paid++;
        }
        output.WriteLine($"unchained: {r.Casts.Count} swings, {paid} paid");
        Assert.True(paid >= 3);
    }

    [Fact] // T11
    public void Not_lit_or_no_kills_a_chains_cuts_keep_their_periods()
    {
        var r = new Run(lit: false);
        foreach (var (c, n) in new[] { (2, 3), (3, 3), (5, 3) }) r.Feed[c] = n;
        r.ToCuts(9).Check(lit: false);
        Assert.Empty(r.PaidCuts);
        Assert.Equal((int.MinValue, 0, false), (r.W.MomKey, r.W.MomKills, r.W.MomFast));
        var q = new Run().ToCuts(9);
        Assert.Empty(q.PaidCuts);
        for (int i = 0; i < 9; i++) Assert.Equal(r.Cuts[i].Start, q.Cuts[i].Start);
    }

    [Fact] // (J12a's answer under J12c)
    public void A_blocks_answer_in_a_paid_blow_waits_the_blows_wait_less_the_share_and_its_kills_are_its_blows()
    {
        var r = new Run(answer: true);
        r.Feed[2] = 3;
        while (r.Cuts.Count < 4) r.Step();
        r.Block();
        while (r.Cuts.Count < 5) r.Step();
        r.Spawn(3);
        r.ToCuts(8);
        // (the cut the block fell in: paid at its start; the answer follows from its cancel beat, J12a, at the paid rate)
        Assert.Equal(r.Wait * Fast, r.Cuts[3].P0, 9);
        Assert.Equal(r.Cuts[3].Cancel - r.Cuts[3].Start, r.Cuts[3].P1, 9);
        var a = r.Cuts[4];
        Assert.Equal(1 / r.W.BlowWeight, a.Scale, 9);
        Assert.Equal(r.Cuts[3].Key, a.Key);
        Assert.Equal(r.Wait / r.W.BlowWeight * Fast, a.P0, 9);
        Assert.Equal(r.Wait / r.W.BlowWeight * Fast, a.P1, 9);
        Assert.Equal(r.Cuts[3].Rate, a.Rate * (HerEvents.ChainBeats(r.Cuts[3].Clip, false).Len / HerEvents.ChainBeats(a.Clip, false).Len), 9);
        Assert.Equal(3, a.Kills);
        // its three kills are blow 2's: the blow after (cut 5) is paid, the one after that is not
        Assert.Equal(new[] { 3, 4, 5 }, r.PaidCuts);
    }
}
