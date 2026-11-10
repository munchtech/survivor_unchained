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
        public Run(double? period = 0.70, bool lamp = true, uint seed = 5, double? answer = null)
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
                W.Press = W.Press!.WithChain(p > 0 ? new ChainDef { Grace = 0.40, Recover = 18, Period = p, Answer = answer } : new ChainDef { Grace = 0.40, Recover = 18 });
                Assert.NotSame(W.Def.Press!.Chain, W.Press.Chain);
            }
            // (the switch: the shipped record carries a chain; the unchained run takes it off its own copy)
            else W.Press = W.Press?.WithChain(null);
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

        /// <summary>Held until a cut has landed that leaves the Hand's count one whole blow short of its heavy, with less than a
        /// cut's share to spare: a cut's share does not complete the heavy, a whole blow does. The index of the next cut.</summary>
        public int HoldToOneShort()
        {
            int every = Hands.Warden.Every;
            while (!(Cuts.Count > 0 && Landed.Count == Cuts.Count && W.HandBlows % every == every - 1 && W.HandPart + W.BlowWeight < 1 - 1e-6)) Step(true);
            return Cuts.Count;
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
        int every = Hands.Warden.Every;
        while (u.Landed.Count < every) u.Step(true);
        // (unchained: the Hand's every-th blow is the heavy; hands.json, 6 today)
        Assert.Equal(Enumerable.Range(1, every).Select(i => i == every), u.Landed.Select(l => l.Heavy));
        double blow = u.Landed[0].Dmg, heavy = u.Landed[every - 1].Dmg;
        // (the Hand's heavy is a stun and a shove; on this dummy its damage need not be more than the blow's)
        Assert.True(heavy >= blow - 1e-9);
        output.WriteLine($"unchained blow {blow:F4}, heavy blow {heavy:F4}");

        var c = new Run();
        c.HoldToPending(1);
        c.Block();
        c.HoldToCuts(3);
        Assert.True(c.Cuts[2].Whole);
        Assert.False(c.Landed[2].Heavy);
        Assert.Equal(blow, c.Landed[2].Dmg, 6);
        Assert.Equal(blow * c.W.BlowWeight, c.Landed[1].Dmg, 6);

        // The lost heavy (lead 13's finding): the Hand's count stands one whole blow short of its heavy. A cut's share
        // (0.667) does not complete it, the answer's whole blow does: the answer IS the heavy, at its press (the
        // heavy clip) and at its contact (the heavy blow), and it weighs the written heavy.
        var h = new Run();
        int k = h.HoldToOneShort();
        Assert.Equal(0, h.B.HandHeavies);
        h.Block();
        h.HoldToCuts(k + 2);
        var a = h.Cuts[k];
        Assert.True(a.Whole);
        Assert.True(a.Heavy);
        Assert.Equal(h.W.Press!.ClipHeavy, a.Clip);
        Assert.True(h.Landed[k].Heavy);
        Assert.Equal(heavy, h.Landed[k].Dmg, 6);
        Assert.Equal(1, h.B.HandHeavies);
        // a heavy answer is a whole blow too: its wait is the written wait, not the heavy cut's longer share of it
        Assert.Equal(1 / h.W.BlowWeight, a.Scale, 12);
        Assert.Equal(h.Wait / h.W.BlowWeight, h.Cuts[k + 1].Start - a.Start, 9);
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
        r.HoldToCuts(6);
        Assert.Equal(a.Clip, r.Cuts[4].Clip);
        Assert.Equal(r.Cuts[4].Contact - r.Cuts[4].Start, a.Contact - a.Start, 9);
        // the blow lands on the contact (the first step at or past it)
        Assert.InRange(r.Landed[2].T - a.Contact, -1e-9, Dt + 1e-9);
        output.WriteLine($"answer (light, clip {a.Clip}), in 1/60 s frames from its start: contact {F(a.Contact - a.Start):F2}, cancel beat {F(a.Cancel - a.Start):F2}, clip end {F(beats.Len / a.Rate):F2}, next cut starts {F(next.Start - a.Start):F2}"
            + $" | a plain cut: contact {F(r.Cuts[4].Contact - r.Cuts[4].Start):F2}, cancel {F(r.Cuts[4].Cancel - r.Cuts[4].Start):F2}, next {F(r.Cuts[5].Start - r.Cuts[4].Start):F2}");
        var h = new Run();
        int k = h.HoldToOneShort();
        h.Block();
        h.HoldToCuts(k + 14);
        var ha = h.Cuts[k];
        Assert.True(ha.Whole && ha.Heavy);
        Assert.Equal(h.W.Press!.ClipHeavy, ha.Clip);
        var hb = HerEvents.ChainBeats(ha.Clip, true);
        output.WriteLine($"answer (heavy, clip {ha.Clip}): contact {F(ha.Contact - ha.Start):F2}, cancel beat {F(ha.Cancel - ha.Start):F2}, clip end {F(hb.Len / ha.Rate):F2}, next cut starts {F(h.Cuts[k + 1].Start - ha.Start):F2}");
        // (a plain heavy cut of the same run: the same clip at the same beats, its own longer period after it)
        int p = h.Cuts.FindIndex(k + 1, c => c.Heavy && !c.Whole);
        Assert.True(p > 0 && p + 1 < h.Cuts.Count);
        Assert.Equal(h.Cuts[p].Rate, ha.Rate, 9);
        Assert.Equal(h.Cuts[p].Contact - h.Cuts[p].Start, ha.Contact - ha.Start, 9);
        Assert.Equal(h.Cuts[p].Cancel - h.Cuts[p].Start, ha.Cancel - ha.Start, 9);
        output.WriteLine($"a plain heavy cut: contact {F(h.Cuts[p].Contact - h.Cuts[p].Start):F2}, cancel {F(h.Cuts[p].Cancel - h.Cuts[p].Start):F2}, next {F(h.Cuts[p + 1].Start - h.Cuts[p].Start):F2}");
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

    // ---- 6: the measurement (main's): damage per second, chained v unchained, by block period and by answer wait ----

    /// <summary>Held on a dummy for `secs`, a block about every `gap` s (0: none; each gap drawn evenly from gap - 1 to
    /// gap + 1: exactly periodic blocks lock to the swing's clock and measure one phase only): damage per second, the
    /// answers a minute (unchained: the blocks that cut a wait short) and the unchained blocks lost a minute (a block
    /// between a press and its contact: the contact's rearm overwrites the zeroed wait).</summary>
    static (double Dps, double Answers, double Holed) Held(bool chained, double gap, double secs, Random? jitter, double? answer = null)
    {
        var r = new Run(chained ? 0.70 : null, answer: answer);
        double next = gap > 0 ? gap / 2 : double.PositiveInfinity;
        int steps = (int)Math.Round(secs * 60);
        for (int i = 0; i < steps; i++)
        {
            r.Step(true);
            if (r.B.Time >= next - 1e-9) { r.Block(); next += gap - 1 + 2 * jitter!.NextDouble(); }
        }
        double mins = secs / 60;
        return (r.Damage / secs, (chained ? r.Cuts.Count(c => c.Whole) : r.Answered) / mins, r.Holed / mins);
    }

    [Fact]
    public void Measured_held_ten_minutes_with_blocks_the_chain_against_the_written_blows()
    {
        const double secs = 600;
        const int seeds = 8;
        var none = (C: Held(true, 0, secs, null), U: Held(false, 0, secs, null));
        output.WriteLine($"no blocks: chained {none.C.Dps:F3} dps, unchained {none.U.Dps:F3} dps, ratio {none.C.Dps / none.U.Dps:F4}");
        double[] gaps = [3, 7, 10];
        double?[] answers = [null, 0.85, 0.78, 0.70];
        // (the same block times on both sides: seed by seed)
        var un = gaps.ToDictionary(g => g, g => Enumerable.Range(0, seeds).Select(j => Held(false, g, secs, new Random(100 + j))).ToList());
        var def = new Dictionary<double, double>();
        foreach (var answer in answers)
        {
            var f = new Run(answer: answer);
            f.HoldToPending(1);
            f.Block();
            f.HoldToCuts(4);
            string line = $"answer wait {(answer is double a ? a.ToString("F2") : "unset (the blow's, 1.05)")}: next cut {F(f.Cuts[3].Start - f.Cuts[2].Start):F1} frames after the answer's start (cancel beat {F(f.Cuts[2].Cancel - f.Cuts[2].Start):F1}, clip end 42.0)";
            foreach (double g in gaps)
            {
                var ch = Enumerable.Range(0, seeds).Select(j => Held(true, g, secs, new Random(100 + j), answer)).ToList();
                var by = ch.Select((c, j) => c.Dps / un[g][j].Dps).ToList();
                double ratio = ch.Average(c => c.Dps) / un[g].Average(u => u.Dps);
                line += $" | block ~{g} s: ratio {ratio:F4} (by seed {by.Min():F4} to {by.Max():F4}), answers/min chained {ch.Average(c => c.Answers):F2} unchained {un[g].Average(u => u.Answers):F2} (+{un[g].Average(u => u.Holed):F2} lost)";
                if (answer == null) def[g] = ratio;
            }
            output.WriteLine(line);
        }
        // Pinned: with no blocks the chain gives what the written blows give. With blocks, the DEFAULT answer (a whole
        // blow for a whole wait) leaves the chain low, about 0.19 of a blow per block: these bounds are the measured
        // state (10 Nov), not a target; the "answer" wait is the option that closes it (main's pick).
        Assert.InRange(none.C.Dps / none.U.Dps, 0.98, 1.02);
        Assert.InRange(def[3], 0.92, 0.95);
        Assert.InRange(def[7], 0.96, 0.985);
        Assert.InRange(def[10], 0.97, 0.99);
    }

    [Fact]
    public void An_answer_wait_written_on_the_chain_is_the_wait_after_the_answer_and_nothing_else()
    {
        Assert.Equal(0.85, SurvivorUnchained.Core.Json.Parse<ChainDef>("{\"period\": 0.7, \"answer\": 0.85}").Answer);
        Assert.Null(SurvivorUnchained.Core.Json.Parse<ChainDef>("{\"period\": 0.7}").Answer);
        var d = new Run(); var w = new Run(answer: 0.85);
        foreach (var r in new[] { d, w }) { r.HoldToPending(1); r.Block(); r.HoldToCuts(5); }
        Assert.Equal(1.05, d.Cuts[3].Start - d.Cuts[2].Start, 9);
        Assert.Equal(0.85, w.Cuts[3].Start - w.Cuts[2].Start, 9);
        // the blow, its clip and its beats are the same; the cuts after it are cuts
        Assert.True(w.Cuts[2].Whole);
        Assert.Equal(d.Landed[2].Dmg, w.Landed[2].Dmg, 9);
        Assert.Equal(d.Landed[2].N, w.Landed[2].N);
        Assert.Equal((d.Cuts[2].Rate, d.Cuts[2].Contact - d.Cuts[2].Start, d.Cuts[2].Cancel - d.Cuts[2].Start), (w.Cuts[2].Rate, w.Cuts[2].Contact - w.Cuts[2].Start, w.Cuts[2].Cancel - w.Cuts[2].Start));
        Assert.Equal(w.Wait, w.Cuts[4].Start - w.Cuts[3].Start, 9);
        // a chain with no period never reads it
        var n = new Run(0, answer: 0.85);
        n.HoldToPending(1); n.Block(); n.HoldToCuts(4);
        Assert.All(n.Cuts, c => { Assert.False(c.Whole); Assert.Equal(1.0, c.Scale); });
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
        Assert.Equal(0.0, n.W.Timer);
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
