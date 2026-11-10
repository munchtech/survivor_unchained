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
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public SwingChainTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

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
        // (the blow's weight) more foes held in place, the own-heavy lines thrown, each hit's damage on E, and the
        // weapon's own-heavy flag as read at each cut's press and at each blow's contact
        public readonly List<(Enemy E, double X, double Z)> More = new();
        public readonly List<double> Dealt = new();
        public readonly List<bool> OwnAtPress = new(), OwnAtContact = new();
        public int Lines;
        double last = double.NaN, hp = 1e9;

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

        public void Add(double x, double z)
        {
            var e = B.SpawnEnemy("footpad", x, z)!;
            e.Hp = e.MaxHp = 1e9;
            e.AttackT = e.RangedT = 999;
            More.Add((e, x, z));
        }

        public double Damage => 1e9 - E.Hp + More.Sum(m => 1e9 - m.E.Hp);

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
            foreach (var (e, x, z) in More) { e.X = x; e.Z = z; e.Vx = e.Vz = 0; }
            B.Tick(Dt, 0, 0);
            Note();
        }

        public void Note()
        {
            foreach (var ev in B.Events.Drain())
            {
                if (ev is Ev.Slash s) { Slashes.Add((B.Time, s)); OwnAtContact.Add(W.WasOwnHeavy); }
                else if (ev is Ev.SwingRelease r) Releases.Add((B.Time, r));
                else if (ev is Ev.Hit) Hits++;
                else if (ev is Ev.Beam { Art: { } art } && art.EndsWith("_line")) Lines++;
            }
            if (E.Hp < hp) { Dealt.Add(hp - E.Hp); hp = E.Hp; }
            if (W.Chain is { Live: true } c && c.StartAt != last)
            {
                last = c.StartAt;
                OwnAtPress.Add(W.WasOwnHeavy);
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

    // ---- the cut's weight (M3 MR 3): a chain with a period makes each cut a share of the written blow ----

    static PressDef P70(PressDef p) { p.Chain = new ChainDef { Grace = 0.40, Recover = 18, Period = 0.70 }; return p; }

    [Fact]
    public void A_cut_with_a_period_weighs_its_share_of_the_blow_and_only_inside_its_cast()
    {
        var c = new Run("sunder", P70);
        var u = new Run("sunder", chain: false);
        Assert.Equal(0.4375, c.W.BlowWeight, 12);
        Assert.Equal(1.0, u.W.BlowWeight);
        Assert.Equal(1.0, new Run("sunder").W.BlowWeight);
        Assert.Equal(u.W.Damage, c.W.Damage);
        Assert.Equal(u.Wait * 0.4375, c.Wait, 12);
        while (c.Dealt.Count == 0) c.Step(true);
        while (u.Dealt.Count == 0) u.Step(true);
        Assert.False(c.Cuts[0].Heavy);
        Assert.Equal(0.4375, c.Dealt[0] / u.Dealt[0], 6);
        // outside the cast the weight is 1 again, and the count carries the part
        Assert.Equal(1.0, c.W.CutW);
        Assert.Equal(u.W.Damage, c.W.Damage);
        // (the opening cut counts whole in an every-N count, Blows.CountFirstWhole; the written-blow count takes its share)
        Assert.Equal((1, 0), (c.W.OwnBlows, c.W.BlowN));
        Assert.Equal(0.0, c.W.OwnPart, 12);
        Assert.Equal((1, 0.0), (c.W.HandBlows, c.W.HandPart));
        Assert.Equal(0.4375, c.W.BlowPart, 12);
        Assert.Equal(0.4375 * (c.W.Press!.Builds ?? 0), c.B.Resolve.LandedFill, 9);
    }

    /// <summary>Held for 63.9 s: whole written blows on both sides (the unchained Sunder's 41st lands at 64.0 s exactly).
    /// Lines: its own heavies; Hand: the Hand's count's heavies (every Hands.Warden.Every-th blow); Heavy: the heavy
    /// blows fired for either reason (Battle.HandHeavies is per foe struck).</summary>
    static (double Dmg, double Fill, int Lines, int Hand, int Heavy, int Blows, double Whole) Hold(string id, bool chained, int pack)
    {
        var r = new Run(id, chained ? P70 : null, chain: chained);
        // crit off: it holds in expectation (a cut rolls as a blow does) and is not what this measures
        r.B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -r.B.Stats.Get(Stat.CritChance), "test"));
        if (pack > 1) { r.Add(2, 0.7); r.Add(2, -0.7); }
        r.Step(true, 3834);
        if (pack > 1) Assert.All(r.Slashes, s => Assert.Equal(pack, s.S.Struck));
        int hand = r.W.HandBlows / Math.Max(1, SurvivorUnchained.Content.Hands.Warden.Every);
        return (r.Damage, r.B.Resolve.LandedFill, r.Lines, hand, r.B.HandHeavies / pack, r.Slashes.Count, r.W.BlowN + r.W.BlowPart);
    }

    [Theory]
    [InlineData("sunder", 1)]
    [InlineData("oathblade", 1)]
    [InlineData("sunder", 3)]
    public void Held_a_minute_the_chain_of_cuts_gives_what_the_written_blows_gave(string id, int pack)
    {
        var c = Hold(id, true, pack);
        var u = Hold(id, false, pack);
        string told = $"{id} x{pack}: chained dmg {c.Dmg:F1} fill {c.Fill:F2} own heavies {c.Lines} hand heavies {c.Hand} heavy blows {c.Heavy} cuts {c.Blows} blows {c.Whole:F3}"
            + $" | unchained dmg {u.Dmg:F1} fill {u.Fill:F2} own heavies {u.Lines} hand heavies {u.Hand} heavy blows {u.Heavy} blows {u.Blows}"
            + $" | dmg {(c.Dmg / u.Dmg - 1) * 100:+0.00;-0.00}% fill {(c.Fill / u.Fill - 1) * 100:+0.00;-0.00}%";
        // (told on a pass too: `dotnet test --logger "console;verbosity=detailed"` shows it)
        output.WriteLine(told);
        Assert.True(Math.Abs(c.Whole - u.Blows) <= 1, told);
        Assert.True(Math.Abs(c.Lines - u.Lines) <= 1, told);
        Assert.True(Math.Abs(c.Hand - u.Hand) <= 1, told);
        Assert.True(Math.Abs(c.Fill / u.Fill - 1) <= 0.02, told);
        Assert.True(Math.Abs(c.Dmg / u.Dmg - 1) <= 0.02, told);
    }

    [Fact]
    public void The_opening_cut_counts_whole_so_the_first_own_heavy_is_cut_eight()
    {
        // Sunder's own every 4th, unchained: the 4th blow, at 3 x 1.6 = 4.8 s. Chained at 0.70 s (weight 0.4375) the
        // opening cut counts 1, so cut k finds 1 + (k - 2) x 0.4375 counted: 1 + 6 x 0.4375 + 0.4375 = 4.0625 >= 4 at
        // k = 8, which starts 7 x 0.70 = 4.9 s after the first (were the opening cut a share, it would be cut 10 at 6.3 s).
        var r = new Run("sunder", P70);
        int every = Firing.HeavyEveryOf(r.B, r.W);
        Assert.Equal(4, every);
        // read ahead on the fresh count: the opening firing completes nothing at either weight
        Assert.False(Blows.Completes(0, 0, every, r.W.BlowWeight));
        Assert.False(Blows.Completes(0, 0, every, 1));
        while (r.Slashes.Count < 60) r.Step(true);
        var own = Enumerable.Range(0, 60).Where(k => r.OwnAtContact[k]).Select(k => k + 1).ToList();
        output.WriteLine("sunder chained, own heavy cuts: " + string.Join(", ", own));
        Assert.Equal(8, own[0]);
        Assert.True(r.Cuts[7].Heavy);
        Assert.Equal(r.Cuts[0].Start + 4.9, r.Cuts[7].Start, 6);
        // the cycle after it is the weighed one: 4 blows of cuts (a heavy cut counts its longer share)
        for (int k = 1; k < own.Count; k++) Assert.InRange(own[k] - own[k - 1], 9, 10);
        Assert.Equal(r.OwnAtPress.Take(60), r.OwnAtContact.Take(60));
    }

    [Fact]
    public void A_dashed_off_heavy_comes_on_the_next_cut_and_press_and_contact_agree()
    {
        var r = new Run("sunder", p => { p = P70(p); p.Clip = null; p.ClipHeavy = null; return p; });
        (r.W.OwnBlows, r.W.OwnPart) = (3, 0.6);
        r.Step(true, 3);
        Assert.True(r.OwnAtPress.Single());
        Assert.True(r.B.Time < r.Cuts[0].Contact);
        Assert.True(r.B.Dash(0, -1));
        Assert.True(r.W.Chain!.Dropped);
        while (r.Cuts.Count < 2) r.Step(true);
        Assert.Empty(r.Slashes);
        Assert.Equal((3, 0.6), (r.W.OwnBlows, r.W.OwnPart));
        Assert.True(r.OwnAtPress[1]);

        // held for 100 cuts: what the press read ahead is what the contact decided, every cut
        var h = new Run("sunder", P70);
        while (h.Slashes.Count < 100) h.Step(true);
        Assert.Equal(h.OwnAtPress.Take(100), h.OwnAtContact.Take(100));
        Assert.InRange(h.OwnAtContact.Take(100).Count(x => x), 10, 11);
        Assert.Equal(h.OwnAtContact.Count(x => x), h.Lines);
    }
}
