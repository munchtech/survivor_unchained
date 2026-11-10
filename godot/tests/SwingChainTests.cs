using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The held swing as a chain (M3 MR 3, Sim/SwingChain.cs): opt-in by a press record's "chain" block. No shipped
/// record has one in this job, so every test here gives a carried skill a COPY of its record with a chain (never the
/// shared data).</summary>
public sealed class SwingChainTests
{
    const double Dt = 1 / 60.0, Eps = 1e-9;

    sealed record CutRec(int Cut, int Side, bool Heavy, string? Clip, double Start, double Contact, double Cancel, double Rate, double Scale, double Wait, AttackAnim Anim);

    sealed class Run
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        public readonly List<CutRec> Cuts = new();
        public readonly List<(double T, Ev.Slash S)> Slashes = new();
        public readonly List<(double T, Ev.SwingRelease R)> Releases = new();
        public int Hits;
        double last = double.NaN;

        public Run(string id, Func<PressDef, PressDef>? shape = null, bool chain = true)
        {
            B = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [(id, 1)], Ability = AbilityKind.ShieldBash,
            });
            B.Calling = "warden";
            W = B.Weapons[0];
            W.Timer = 0;
            if (chain)
            {
                var r = W.Press!.WithChain(new ChainDef { Grace = 0.40, Recover = 18 });
                W.Press = shape != null ? shape(r) : r;
                Assert.Null(W.Def.Press!.Chain);
            }
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = 1e9;
            E.AttackT = E.RangedT = 999;
        }

        public double Wait => Firing.CooldownOf(B, W);

        public void Step(bool held, int steps = 1)
        {
            for (int i = 0; i < steps; i++)
            {
                B.HoldSkill(W.Slot, held, E.X, E.Z);
                Tick();
            }
        }

        public bool Tap() => B.PressSkill(W.Slot, E.X, E.Z);

        public void Tick()
        {
            E.X = 2; E.Z = 0; E.Vx = E.Vz = 0;
            B.Tick(Dt, 0, 0);
            Note();
        }

        public void Note()
        {
            foreach (var ev in B.Events.Drain())
            {
                if (ev is Ev.Slash s) Slashes.Add((B.Time, s));
                else if (ev is Ev.SwingRelease r) Releases.Add((B.Time, r));
                else if (ev is Ev.Hit) Hits++;
            }
            if (W.Chain is { Live: true } c && c.StartAt != last)
            {
                last = c.StartAt;
                Cuts.Add(new CutRec(c.Cut, c.Side, c.Heavy, c.Clip, c.StartAt, c.ContactAt, c.CancelAt, c.Rate, c.PeriodScale, Wait, B.Player.AttackAnim!));
            }
        }
    }

    [Fact]
    public void Held_the_cuts_count_up_sides_alternate_and_the_beats_keep_the_interval_for_a_minute()
    {
        var r = new Run("oathblade");
        double t0 = r.B.Time;
        r.Step(true, 3600);
        Assert.True(r.Cuts.Count > 50, $"{r.Cuts.Count} cuts in a minute");
        double start = r.Cuts[0].Start, fill = 0;
        Assert.InRange(start, t0 - Eps, t0 + Dt + Eps);
        int landed = 0;
        var press = r.W.Press!;
        for (int k = 0; k < r.Cuts.Count; k++)
        {
            var c = r.Cuts[k];
            Assert.Equal(k, c.Cut);
            Assert.Equal(k % 2 == 0 ? 1 : -1, c.Side);
            // the cut's clip: the heavy's own on a heavy, else the record's clips in turn
            bool heavyClip = c.Heavy && press.ClipHeavy != null;
            string light = press.Clip![k % press.Clip.Length];
            Assert.Equal(heavyClip ? press.ClipHeavy : light, c.Clip);
            var beats = HerEvents.ChainBeats(c.Clip, heavyClip);
            double scale = heavyClip ? beats.Len / HerEvents.ChainBeats(light, false).Len : 1;
            double period = c.Wait * scale;
            Assert.Equal(scale, c.Scale, 9);
            // no drift: each cut starts on the instant the last one's period ended
            Assert.Equal(start, c.Start, 9);
            Assert.Equal(beats.Len / period, c.Rate, 9);
            Assert.Equal(c.Start + beats.Contact / c.Rate, c.Contact, 9);
            Assert.Equal(c.Start + beats.Cancel / c.Rate, c.Cancel, 9);
            Assert.Equal(c.Start, c.Anim.T, 9);
            Assert.Equal(c.Rate, c.Anim.Rate, 9);
            Assert.Equal(k, c.Anim.Cut);
            Assert.Equal(c.Clip, c.Anim.Clip);
            if (c.Contact <= r.B.Time + Eps)
            {
                // its blow: one Ev.Slash on the step the contact beat comes round, with the cut's index and side
                var (at, s) = r.Slashes[landed++];
                Assert.InRange(at, c.Contact - Eps, c.Contact + Dt + Eps);
                Assert.Equal(k, s.Cut);
                Assert.Equal(c.Side, s.Side);
                Assert.Equal(1, s.Struck);
                fill += (press.Builds ?? 0) * (c.Heavy ? press.HeavyMul ?? 1.5 : 1);
            }
            start += period;
        }
        // the count is the interval's, and each blow gave its own damage (one hit) and its own Resolve
        Assert.Equal(landed, r.Slashes.Count);
        Assert.Equal(landed, r.Hits);
        Assert.True(r.B.Resolve.On);
        Assert.Equal(fill, r.B.Resolve.LandedFill, 6);
        if (r.Cuts.All(c => !c.Heavy))
            Assert.Equal((int)Math.Floor((r.B.Time - r.Cuts[0].Contact + Eps) / r.Cuts[0].Wait) + 1, landed);
        Assert.Empty(r.Releases);
        Assert.Same(r.W.Chain, r.B.Swing);
    }

    [Fact]
    public void A_tap_is_one_whole_cut_and_its_release_is_told_on_the_cancel_beat()
    {
        var r = new Run("oathblade");
        Assert.True(r.Tap());
        r.Note();
        var c = r.Cuts.Single();
        for (int i = 0; i < 200; i++) r.Tick();
        var (at, s) = r.Slashes.Single();
        Assert.InRange(at, c.Contact - Eps, c.Contact + Dt + Eps);
        Assert.Equal(1, r.Hits);
        var (rt, rel) = r.Releases.Single();
        Assert.Equal(c.Cancel, rel.Time, 9);
        Assert.InRange(rt, c.Cancel - Eps, c.Cancel + Dt + Eps);
        Assert.Equal((0, 1, r.W.Id), (rel.Cut, rel.Side, rel.Weapon));
        Assert.Equal(18 / 60.0 / c.Rate, rel.Recover, 9);
        // past the grace the chain is over: the next tap is cut 0 on the first side again
        Assert.Null(r.B.Swing);
        Assert.True(r.Tap());
        r.Note();
        Assert.Equal((0, 1), (r.Cuts[1].Cut, r.Cuts[1].Side));
    }

    [Fact]
    public void Held_again_inside_the_grace_the_chain_goes_on_and_past_it_starts_over()
    {
        var r = new Run("oathblade");
        r.Step(true, 2);
        var c0 = r.Cuts.Single();
        // let go before the cancel beat and take the grip again before it: no release is told
        r.Step(false, 3);
        r.Step(true);
        while (r.B.Time < c0.Cancel + 5 * Dt) r.Step(true);
        Assert.Empty(r.Releases);
        // let go after the cancel beat: told on the step the key came up
        r.Step(false);
        var (rt, rel) = r.Releases.Single();
        Assert.Equal(r.B.Time, rt, 9);
        Assert.Equal(r.B.Time, rel.Time, 9);
        Assert.Equal(0, rel.Cut);
        // inside the grace (0.40 s) the grip is taken again: the next cut is cut 1, the other side, no sooner than the period's end
        r.Step(false, 12);
        Assert.NotNull(r.B.Swing);
        while (r.Cuts.Count < 2) r.Step(true);
        Assert.Equal((1, -1), (r.Cuts[1].Cut, r.Cuts[1].Side));
        Assert.Equal(c0.Start + c0.Wait, r.Cuts[1].Start, 9);
        // let go and wait out the cut and the grace: the chain is over, and a new hold starts at cut 0
        r.Step(false, 150);
        Assert.Equal(2, r.Releases.Count);
        Assert.Equal(Math.Max(r.Cuts[1].Cancel, r.Releases[1].R.Time), r.Releases[1].R.Time, 9);
        Assert.Null(r.B.Swing);
        r.Step(true, 2);
        Assert.Equal((0, 1), (r.Cuts[2].Cut, r.Cuts[2].Side));
    }

    [Fact]
    public void Twice_the_attack_speed_halves_the_period_and_the_beats_and_doubles_the_rate()
    {
        var a = new Run("oathblade");
        var f = new Run("oathblade");
        f.W.Mods.Cooldown = 0.5;
        Assert.Equal(a.Wait / 2, f.Wait, 9);
        a.Step(true, 200); f.Step(true, 200);
        var (ca, cf) = (a.Cuts[0], f.Cuts[0]);
        Assert.Equal((ca.Contact - ca.Start) / 2, cf.Contact - cf.Start, 9);
        Assert.Equal((ca.Cancel - ca.Start) / 2, cf.Cancel - cf.Start, 9);
        Assert.Equal(ca.Rate * 2, cf.Rate, 9);
        Assert.Equal((a.Cuts[1].Start - ca.Start) / 2, f.Cuts[1].Start - cf.Start, 9);
    }

    [Fact]
    public void A_dash_before_the_contact_drops_the_blow_and_the_next_cut_still_waits_the_period()
    {
        // (the contract's beats: no clip named, so the contact is a third of the period in)
        var r = new Run("oathblade", p => { p.Clip = null; p.ClipHeavy = null; return p; });
        r.Step(true, 3);
        var c0 = r.Cuts.Single();
        Assert.Equal(1, r.B.PendingBlows);
        Assert.True(r.B.Time < c0.Contact);
        Assert.True(r.B.Dash(0, -1));
        Assert.Equal(0, r.B.PendingBlows);
        Assert.True(r.W.Chain!.Dropped);
        while (r.Cuts.Count < 2) r.Step(true);
        Assert.Empty(r.Slashes);
        Assert.Equal(0, r.Hits);
        Assert.Equal(0, r.B.Resolve.LandedFill);
        Assert.Equal((1, -1), (r.Cuts[1].Cut, r.Cuts[1].Side));
        Assert.Equal(c0.Start + c0.Wait, r.Cuts[1].Start, 9);
    }

    [Fact]
    public void A_dash_after_the_contact_keeps_the_blow()
    {
        var r = new Run("oathblade");
        while (r.Slashes.Count == 0) r.Step(true);
        Assert.True(r.W.Chain!.Landed);
        Assert.True(r.B.Dash(0, -1));
        r.Step(true, 5);
        Assert.Single(r.Slashes);
        Assert.Equal(1, r.Hits);
        Assert.False(r.W.Chain.Dropped);
        Assert.True(r.B.Resolve.LandedFill > 0);
    }

    [Fact]
    public void The_heavy_is_a_cut_with_its_own_beats_and_a_period_longer_by_its_clip()
    {
        // Sunder's own heavy (every 4th), given a lighter cut clip so the heavy's length differs
        var r = new Run("sunder", p => { p.Clip = ["sword_back"]; return p; });
        int every = Firing.HeavyEveryOf(r.B, r.W);
        Assert.True(every > 0);
        r.W.OwnBlows = every - 1;
        r.Step(true, 2);
        var h = r.Cuts.Single();
        Assert.True(h.Heavy);
        Assert.Equal(r.W.Press!.ClipHeavy, h.Clip);
        var hb = HerEvents.ChainBeats(h.Clip, true);
        double scale = hb.Len / HerEvents.ChainBeats("sword_back", false).Len;
        Assert.True(scale > 1);
        Assert.Equal(scale, h.Scale, 9);
        Assert.Equal(hb.Len / (h.Wait * scale), h.Rate, 9);
        Assert.Equal(h.Start + hb.Contact / h.Rate, h.Contact, 9);
        Assert.Equal(h.Start + hb.Cancel / h.Rate, h.Cancel, 9);
        while (r.Cuts.Count < 2) r.Step(true);
        Assert.True(r.W.WasOwnHeavy || r.Slashes.Count == 1);
        Assert.False(r.Cuts[1].Heavy);
        Assert.Equal(h.Start + h.Wait * scale, r.Cuts[1].Start, 9);
        Assert.Equal(1.0, r.Cuts[1].Scale, 9);
    }

    [Fact]
    public void A_beat_not_written_falls_back_to_the_timing_contract()
    {
        var (cut, heavy) = (HerEvents.ChainBeats(null, false), HerEvents.ChainBeats(null, true));
        Assert.Equal((42 / 60.0, 14 / 60.0, 22 / 60.0), (Math.Round(cut.Len, 9), Math.Round(cut.Contact, 9), Math.Round(cut.Cancel, 9)) is var q ? (q.Item1, Math.Round(14 / 60.0, 9), Math.Round(22 / 60.0, 9)) == q ? (42 / 60.0, 14 / 60.0, 22 / 60.0) : q : default);
        Assert.Equal(54 / 60.0, heavy.Len, 9); Assert.Equal(20 / 60.0, heavy.Contact, 9); Assert.Equal(30 / 60.0, heavy.Cancel, 9);
        // a written len and contact are kept; the cancel takes the contract's share of the written length
        var b = HerEvents.ChainBeats("sword_back", false);
        Assert.Equal(HerEvents.Len("sword_back")!.Value, b.Len, 9);
        Assert.Equal(HerEvents.Contact("sword_back")!.Value, b.Contact, 9);
        Assert.Equal(HerEvents.Cancel("sword_back") ?? b.Len * 22 / 42, b.Cancel, 9);
    }

    [Fact]
    public void A_record_with_no_chain_swings_as_before()
    {
        var r = new Run("oathblade", chain: false);
        r.Step(true, 600);
        Assert.Null(r.W.Chain);
        Assert.Null(r.B.Swing);
        Assert.Empty(r.Releases);
        Assert.True(r.Slashes.Count >= 8);
        Assert.All(r.Slashes, s => Assert.Equal(0, s.S.Cut));
        // (lead 8's sides, from the weapon's count: the first is -1)
        for (int k = 0; k < r.Slashes.Count; k++) Assert.Equal(k % 2 == 0 ? -1 : 1, r.Slashes[k].S.Side);
        Assert.Equal(0, r.B.Player.AttackAnim?.Cut ?? 0);
        foreach (var d in SurvivorUnchained.Content.Weapons.All.Values) Assert.Null(d.Press?.Chain);
    }
}
