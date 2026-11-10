using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 J12a) The block answer of a chained Oathblade (bulwark.oathblade.shield_and_edge) is one WHOLE written
/// blow, latched (WeaponInst.AnswerDue): the next cut to start after a block weighs 1 and waits the blow's wait, on the
/// cut's own clip at the cut's rate; it never starts before the running cut's cancel beat; the heavy counts ask at weight 1
/// at its press and at its contact. No shipped record has a chain yet: every run here chains a COPY of Oathblade's
/// record (period 0.70, grace 0.40, recover 18; its written wait 1.05).</summary>
public sealed class BlockAnswerTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public BlockAnswerTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0, Hp0 = 1e7;

    sealed class CutRec
    {
        public int Cut; public bool Heavy, Whole; public string? Clip;
        public double Start, Contact, Cancel, Rate, Scale;
    }

    sealed class Run
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        public readonly bool Chained;
        public readonly List<CutRec> Cuts = new();
        /// <summary>Each blow landed, in order: its damage on the dummy, whether it was heavy, the written-blow count after it.</summary>
        public readonly List<(double T, double Dmg, bool Heavy, int N, double Part)> Landed = new();
        public int Answered, Holed;
        double last = double.NaN, hp = Hp0;

        /// <param name="period">0.70: the chain of weighed cuts; 0: a chain with no period; null: unchained.</param>
        public Run(double? period = 0.70, bool lamp = true, uint seed = 5)
        {
            B = new Battle(new BattleSetup
            {
                Seed = seed, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Calling = "warden";
            // crit off: the weights are read off single blows
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -B.Stats.Get(Stat.CritChance), "test"));
            W = B.Weapons[0];
            W.Timer = 0;
            Chained = period != null;
            if (period is double p)
            {
                W.Press = W.Press!.WithChain(p > 0 ? new ChainDef { Grace = 0.40, Recover = 18, Period = p } : new ChainDef { Grace = 0.40, Recover = 18 });
                Assert.Null(W.Def.Press!.Chain);
            }
            if (lamp)
            {
                B.Lamps = new LampLoadout();
                B.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "oathblade.shield_and_edge", Args = new Dictionary<string, double>() });
            }
            // (Warding light: a blow is turned whenever BlockT is 0)
            B.AddBoon("warding");
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = Hp0;
            E.AttackT = E.RangedT = 999;
        }

        public double Wait => Firing.CooldownOf(B, W);
        public double Damage => Landed.Sum(l => l.Dmg);

        /// <summary>A blow turned now (between two steps: after the step's swings, as HurtPlayer runs in a step).</summary>
        public void Block()
        {
            int n = B.Blocks;
            if (W.Timer > 0) { if (B.PendingBlows == 0) Answered++; else Holed++; }
            B.Player.Iframes = 0; B.Player.BlockT = 0;
            B.HurtPlayer(10, School.Physical, "test", null);
            Assert.Equal(n + 1, B.Blocks);
        }

        public void Step(bool held, int steps = 1)
        {
            for (int i = 0; i < steps; i++)
            {
                B.HoldSkill(W.Slot, held, E.X, E.Z);
                E.X = 2; E.Z = 0; E.Vx = E.Vz = 0;
                B.Tick(Dt, 0, 0);
                foreach (var ev in B.Events.Drain())
                    if (ev is Ev.Slash) { Landed.Add((B.Time, hp - E.Hp, W.HeavyCast, W.BlowN, W.BlowPart)); hp = E.Hp; }
                if (W.Chain is { Live: true } c && c.StartAt != last)
                {
                    last = c.StartAt;
                    Cuts.Add(new CutRec { Cut = c.Cut, Heavy = c.Heavy, Whole = c.Whole, Clip = c.Clip, Start = c.StartAt, Contact = c.ContactAt, Cancel = c.CancelAt, Rate = c.Rate, Scale = c.PeriodScale });
                }
            }
        }

        /// <summary>Held until cut k (0-based) has started and its blow is still to land.</summary>
        public void HoldToPending(int k)
        {
            while (Cuts.Count < k + 1) Step(true);
            Assert.Equal(1, B.PendingBlows);
            Assert.Equal(k, Landed.Count);
        }

        public void HoldToCuts(int n) { while (Cuts.Count < n || B.PendingBlows > 0) Step(true); }
    }

    static double F(double seconds) => seconds * 60;

    // ---- 1: the latch through a pending cut's landing ----

    [Fact]
    public void A_block_while_a_cut_is_pending_makes_the_next_cut_the_whole_blow_from_that_cuts_cancel_beat()
    {
        var r = new Run();
        Assert.Equal(0.70 / 1.05, r.W.BlowWeight, 12);
        r.HoldToPending(1);
        r.Block();
        Assert.True(r.W.AnswerDue);
        r.HoldToCuts(4);
        var (pending, answer, after) = (r.Cuts[1], r.Cuts[2], r.Cuts[3]);
        // the pending cut landed at its own weight: the latch was not taken by its landing
        Assert.False(pending.Whole);
        Assert.Equal(r.Landed[0].Dmg, r.Landed[1].Dmg, 6);
        // the answer: the next cut, from the pending cut's cancel beat, one whole blow
        Assert.True(answer.Whole);
        Assert.False(answer.Heavy);
        Assert.Equal(pending.Cancel, answer.Start, 9);
        Assert.Equal(r.Landed[0].Dmg / r.W.BlowWeight, r.Landed[2].Dmg, 6);
        Assert.False(r.W.AnswerDue);
        Assert.False(r.W.WholeCast);
        Assert.False(after.Whole);
    }

    // ---- 2: its damage is the written blow's, light and heavy ----

    [Fact]
    public void The_answers_damage_is_the_written_blows_light_and_heavy()
    {
        var u = new Run(null);
        while (u.Landed.Count < 4) u.Step(true);
        // (unchained: the Hand's every 4th blow is the heavy)
        Assert.Equal(new[] { false, false, false, true }, u.Landed.Select(l => l.Heavy));
        double blow = u.Landed[0].Dmg, heavy = u.Landed[3].Dmg;
        Assert.True(heavy > blow * 1.2);

        var c = new Run();
        c.HoldToPending(1);
        c.Block();
        c.HoldToCuts(3);
        Assert.True(c.Cuts[2].Whole);
        Assert.False(c.Landed[2].Heavy);
        Assert.Equal(blow, c.Landed[2].Dmg, 6);
        Assert.Equal(blow * c.W.BlowWeight, c.Landed[1].Dmg, 6);

        // The lost heavy (lead 13's finding): after four cuts the Hand's count stands at 3 whole blows. A cut's share
        // (0.667) does not complete the 4th, the answer's whole blow does: the answer IS the heavy, at its press (the
        // heavy clip) and at its contact (the heavy blow), and it weighs the written heavy.
        var h = new Run();
        h.HoldToPending(3);
        h.Block();
        while (h.Landed.Count < 4) h.Step(true);
        Assert.Equal(3, h.W.HandBlows);
        Assert.Equal(0.0, h.W.HandPart, 9);
        h.HoldToCuts(6);
        var a = h.Cuts[4];
        Assert.True(a.Whole);
        Assert.True(a.Heavy);
        Assert.Equal(h.W.Press!.ClipHeavy, a.Clip);
        Assert.True(h.Landed[4].Heavy);
        Assert.Equal(heavy, h.Landed[4].Dmg, 6);
        Assert.Equal(1, h.B.HandHeavies);
        // a heavy answer is a whole blow too: its wait is the written wait, not the heavy cut's longer share of it
        Assert.Equal(1 / h.W.BlowWeight, a.Scale, 12);
        Assert.Equal(h.Wait / h.W.BlowWeight, h.Cuts[5].Start - a.Start, 9);
    }

    // ---- 3: the wait after it; the clip is not stretched ----

    [Fact]
    public void The_wait_after_the_answer_is_the_blows_and_its_clip_keeps_the_cuts_rate_and_beats()
    {
        var r = new Run();
        r.HoldToPending(1);
        r.Block();
        r.HoldToCuts(4);
        var (a, next) = (r.Cuts[2], r.Cuts[3]);
        Assert.True(a.Whole);
        Assert.Equal(1.05, r.Wait / r.W.BlowWeight, 9);
        Assert.Equal(r.Wait / r.W.BlowWeight, next.Start - a.Start, 9);
        // the clip: the chain's next by index, at the cut's rate (its length over the CUT's period), beats where a cut has them
        Assert.Equal(r.W.Press!.Clip![2 % r.W.Press.Clip.Length], a.Clip);
        var beats = HerEvents.ChainBeats(a.Clip, false);
        Assert.Equal(beats.Len / r.Wait, a.Rate, 9);
        Assert.Equal(beats.Contact / a.Rate, a.Contact - a.Start, 9);
        Assert.Equal(beats.Cancel / a.Rate, a.Cancel - a.Start, 9);
        // (the same clip two cuts on, a plain cut: the same beats)
        r.HoldToCuts(5);
        Assert.Equal(a.Clip, r.Cuts[4].Clip);
        Assert.Equal(r.Cuts[4].Contact - r.Cuts[4].Start, a.Contact - a.Start, 9);
        // the blow lands on the contact (the first step at or past it)
        Assert.InRange(r.Landed[2].T - a.Contact, -1e-9, Dt + 1e-9);
        output.WriteLine($"answer (light, clip {a.Clip}), in 1/60 s frames from its start: contact {F(a.Contact - a.Start):F2}, cancel beat {F(a.Cancel - a.Start):F2}, clip end {F(beats.Len / a.Rate):F2}, next cut starts {F(next.Start - a.Start):F2}"
            + $" | a plain cut: contact {F(r.Cuts[4].Contact - r.Cuts[4].Start):F2}, cancel {F(r.Cuts[4].Cancel - r.Cuts[4].Start):F2}, next {F(r.Cuts[5 < r.Cuts.Count ? 5 : 4].Start - r.Cuts[4].Start):F2}");
        var h = new Run();
        h.HoldToPending(3);
        h.Block();
        h.HoldToCuts(6);
        var ha = h.Cuts[4];
        var hb = HerEvents.ChainBeats(ha.Clip, true);
        output.WriteLine($"answer (heavy, clip {ha.Clip}): contact {F(ha.Contact - ha.Start):F2}, cancel beat {F(ha.Cancel - ha.Start):F2}, clip end {F(hb.Len / ha.Rate):F2}, next cut starts {F(h.Cuts[5].Start - ha.Start):F2}");
    }

    // ---- 4: one block, one answer ----

    [Fact]
    public void One_block_is_one_answer_and_two_blocks_before_it_starts_are_still_one()
    {
        foreach (int blocks in new[] { 1, 2 })
        {
            var r = new Run();
            r.HoldToPending(1);
            r.Block();
            if (blocks == 2) { r.Step(true); Assert.Equal(1, r.B.PendingBlows); r.Block(); }
            r.HoldToCuts(8);
            Assert.Equal(1, r.Cuts.Count(c => c.Whole));
            Assert.True(r.Cuts[2].Whole);
            // the cut after it is a cut again: its share, its period
            Assert.Equal(1.0, r.Cuts[3].Scale);
            Assert.Equal(r.Landed[1].Dmg, r.Landed[3].Dmg, 6);
            Assert.Equal(r.Wait, r.Cuts[4].Start - r.Cuts[3].Start, 9);
        }
        // a block with no cut pending, between a cut's contact and its cancel beat: the answer waits for that beat
        var m = new Run();
        m.HoldToCuts(2);
        Assert.True(m.B.Time < m.Cuts[1].Cancel - Dt);
        m.Block();
        m.HoldToCuts(3);
        Assert.True(m.Cuts[2].Whole);
        Assert.Equal(m.Cuts[1].Cancel, m.Cuts[2].Start, 9);
        // and past the cancel beat it starts on the next step
        var p = new Run();
        p.HoldToCuts(2);
        while (p.B.Time < p.Cuts[1].Cancel + 2 * Dt) p.Step(true);
        Assert.Equal(2, p.Cuts.Count);
        double at = p.B.Time;
        p.Block();
        p.Step(true);
        Assert.Equal(3, p.Cuts.Count);
        Assert.True(p.Cuts[2].Whole);
        Assert.Equal(at + Dt, p.Cuts[2].Start, 9);
    }

    // ---- 5: the counts ----

    [Fact]
    public void An_answer_counts_one_whole_blow_and_no_heavy_is_lost_to_it()
    {
        var r = new Run();
        r.HoldToPending(1);
        r.Block();
        r.HoldToCuts(3);
        Assert.Equal(r.Landed[1].N + 1, r.Landed[2].N);
        Assert.Equal(r.Landed[1].Part, r.Landed[2].Part, 12);

        // Held four minutes with blocks at awkward phases (the gaps walk through the cut's period): every time the
        // Hand's count passes a 4th blow, that firing was the heavy one, and the press's read agreed with the contact's.
        var h = new Run();
        int k = 0;
        double next = 1.3;
        for (int i = 0; i < 4 * 3600; i++)
        {
            h.Step(true);
            if (h.B.Time >= next) { h.Block(); next += 1.9 + 0.37 * (k++ % 7); }
        }
        int answers = h.Cuts.Count(c => c.Whole);
        Assert.True(answers > 60, $"{answers} answers");
        int heavies = h.Landed.Count(l => l.Heavy);
        Assert.Equal(h.W.HandBlows / Hands.Warden.Every, heavies);
        Assert.Equal(heavies, h.B.HandHeavies);
        for (int i = 0; i < h.Landed.Count; i++) Assert.Equal(h.Cuts[i].Heavy, h.Landed[i].Heavy);
        // (answers that were heavies: the case that was lost)
        Assert.True(h.Cuts.Count(c => c.Whole && c.Heavy) > 5);
        output.WriteLine($"held 240 s, {k} blocks: {answers} answers ({h.Cuts.Count(c => c.Whole && c.Heavy)} of them heavy), {heavies} heavies in {h.W.HandBlows} counted blows, written blows {h.W.BlowN + h.W.BlowPart:F3}");
    }

    // ---- 6: the measurement (main's): damage per second, chained v unchained, by block period ----

    /// <summary>Held on a dummy for `secs`, a block every `gap` s (0: none; jitter: each gap drawn evenly from gap - 1 to
    /// gap + 1, so the blocks do not lock to the swing's clock): damage per second, answers and holed blocks per minute.</summary>
    static (double Dps, double Answers, double Holed) Held(bool chained, double gap, double secs, double first, Random? jitter)
    {
        var r = new Run(chained ? 0.70 : null);
        double next = gap > 0 ? first : double.PositiveInfinity;
        int steps = (int)Math.Round(secs * 60);
        for (int i = 0; i < steps; i++)
        {
            r.Step(true);
            if (r.B.Time >= next - 1e-9) { r.Block(); next += jitter != null ? gap - 1 + 2 * jitter.NextDouble() : gap; }
        }
        double mins = secs / 60;
        return (r.Damage / secs, (chained ? r.Cuts.Count(c => c.Whole) : r.Answered) / mins, r.Holed / mins);
    }

    [Fact]
    public void Measured_held_ten_minutes_with_blocks_the_chain_against_the_written_blows()
    {
        const double secs = 600;
        var ratio = new Dictionary<double, double>();
        foreach (double gap in new[] { 0.0, 3, 7, 10 })
        {
            // exactly periodic (as asked): six first-block times across the gap
            var exact = Enumerable.Range(0, gap > 0 ? 6 : 1).Select(j => (C: Held(true, gap, secs, gap * (j + 1) / 6, null), U: Held(false, gap, secs, gap * (j + 1) / 6, null))).ToList();
            double ec = exact.Average(x => x.C.Dps), eu = exact.Average(x => x.U.Dps);
            string line = $"block every {gap,2} s  EXACT: chained {ec:F3} dps, unchained {eu:F3} dps, ratio {ec / eu:F4} (by first block {string.Join(" ", exact.Select(x => (x.C.Dps / x.U.Dps).ToString("F4")))});"
                + $" answers/min chained {exact.Average(x => x.C.Answers):F2} unchained {exact.Average(x => x.U.Answers):F2} (holed {exact.Average(x => x.U.Holed):F2})";
            if (gap > 0)
            {
                var jit = Enumerable.Range(0, 6).Select(j => (C: Held(true, gap, secs, gap / 2, new Random(100 + j)), U: Held(false, gap, secs, gap / 2, new Random(100 + j)))).ToList();
                double jc = jit.Average(x => x.C.Dps), ju = jit.Average(x => x.U.Dps);
                line += $" | JITTERED +-1 s, 6 seeds x 600 s: ratio {jc / ju:F4} (by seed {string.Join(" ", jit.Select(x => (x.C.Dps / x.U.Dps).ToString("F4")))});"
                    + $" answers/min chained {jit.Average(x => x.C.Answers):F2} unchained {jit.Average(x => x.U.Answers):F2} (holed {jit.Average(x => x.U.Holed):F2})";
                ratio[gap] = jc / ju;
            }
            else ratio[gap] = ec / eu;
            output.WriteLine(line);
        }
        // pinned: only what the measurement shows to hold
        Assert.InRange(ratio[0], 0.98, 1.02);
        Assert.InRange(ratio[10], 0.98, 1.02);
    }

    [Fact]
    public void With_no_blocks_the_lamp_changes_nothing()
    {
        foreach (double? period in new double?[] { 0.70, 0, null })
        {
            var a = new Run(period, lamp: true); var b = new Run(period, lamp: false);
            a.Step(true, 3600); b.Step(true, 3600);
            Assert.Equal(b.Landed, a.Landed);
            Assert.Equal(b.Cuts.Select(c => (c.Start, c.Contact, c.Cancel, c.Rate, c.Scale, c.Whole)), a.Cuts.Select(c => (c.Start, c.Contact, c.Cancel, c.Rate, c.Scale, c.Whole)));
            Assert.All(a.Cuts, c => Assert.False(c.Whole));
        }
    }

    // ---- 7: unchained and a chain with no period ----

    [Fact]
    public void Unchained_and_a_chain_with_no_period_are_never_owed_a_blow()
    {
        // unchained: the wait is zeroed and it swings on the next step, as it always did
        var u = new Run(null);
        while (u.Landed.Count < 2) u.Step(true);
        u.Step(true, 6);
        Assert.Equal(0, u.B.PendingBlows);
        Assert.True(u.W.Timer > 0.3);
        u.Block();
        Assert.Equal(0.0, u.W.Timer);
        Assert.False(u.W.AnswerDue);
        Assert.Equal(1.0, u.W.NextW);
        u.Step(true);
        Assert.Equal(1, u.B.PendingBlows);
        while (u.Landed.Count < 3) u.Step(true);
        Assert.Equal(u.Landed[0].Dmg, u.Landed[2].Dmg, 6);
        Assert.Null(u.W.Chain);

        // a chain with no period: every cut is a whole blow already; nothing is latched, no cut is marked, the waits are the cut's
        var n = new Run(0);
        Assert.Equal(1.0, n.W.BlowWeight);
        n.HoldToPending(1);
        n.Block();
        Assert.False(n.W.AnswerDue);
        n.HoldToCuts(2);
        n.Step(true, 4);
        n.Block();
        Assert.False(n.W.AnswerDue);
        n.HoldToCuts(5);
        Assert.All(n.Cuts, c => { Assert.False(c.Whole); Assert.Equal(1.0, c.Scale); });
        Assert.All(n.Landed.Where(l => !l.Heavy), l => Assert.Equal(n.Landed[0].Dmg, l.Dmg, 6));
        Assert.Equal(u.Landed[0].Dmg, n.Landed[0].Dmg, 6);
    }

    // ---- 8: key up at the block ----

    [Fact]
    public void Key_up_at_the_block_swings_nothing_and_the_next_press_is_the_whole_blow()
    {
        var r = new Run();
        r.HoldToCuts(2);
        r.Step(false, 30);
        r.Block();
        Assert.True(r.W.AnswerDue);
        r.Step(false, 240);
        Assert.Equal(2, r.Cuts.Count);
        Assert.Equal(2, r.Landed.Count);
        // (the latch does not expire: per second it is neutral, a whole blow for a whole wait)
        Assert.True(r.W.AnswerDue);
        r.HoldToCuts(4);
        Assert.True(r.Cuts[2].Whole);
        Assert.Equal(r.Landed[1].Dmg / r.W.BlowWeight, r.Landed[2].Dmg, 6);
        Assert.Equal(r.Wait / r.W.BlowWeight, r.Cuts[3].Start - r.Cuts[2].Start, 9);
        Assert.False(r.Cuts[3].Whole);
    }
}
