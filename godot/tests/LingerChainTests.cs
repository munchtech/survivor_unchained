using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 J12b) Linger under a chain of weighed cuts: ONE ground per WRITTEN blow at the blow's size
/// (Firing.LaysGround, WeaponInst.GroundKey), so the grounds a minute, their damage a second and the procs their ticks
/// set off are the unchained skill's. An On-kill echo lays its ground as an unchained echo does; a block's answer (a
/// whole blow) lays exactly one; unchained and a chain with no period are as they were. No shipped record has a chain
/// yet: every chained run chains a COPY of the record (period 0.70, grace 0.40, recover 18). Sunder has no Linger
/// strand: its runs (and the hand-built Oathblade ones) put a wick with only the ground on the weapon.</summary>
public sealed class LingerChainTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public LingerChainTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0, Hp0 = 1e9;
    static readonly GroundSpec Spec = new(1.5, 2, 0.25);

    sealed record ZoneRec(double T, double Dps, bool Echo, double X, double Z, double Radius, double Life);
    /// <summary>A cast landed: the written-blow count after it, its weight, the grounds (not an echo's) it laid.</summary>
    sealed record CastRec(int N, double Part, double CastW, int Laid, double Dps);

    sealed class Run
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        public readonly List<ZoneRec> Zones = new();
        public readonly List<CastRec> Landed = new();
        public readonly TriggerInstance Flat;
        public int Cuts, Echoes, Fodder;
        readonly Dictionary<GroundZone, double> seen = new();
        double last = double.NaN, onKillT = double.NegativeInfinity;

        /// <param name="period">0.70: the chain of weighed cuts; 0: a chain with no period; null: unchained.</param>
        /// <param name="shipped">Oathblade at rank 4 with the shipped Linger strand lit, not a hand-built wick.</param>
        public Run(string id, double? period, bool ground = true, bool shipped = false, bool onKill = false, bool answers = false)
        {
            B = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [(id, shipped ? 4 : 1)], Ability = AbilityKind.ShieldBash,
                Wicks = shipped ? new Dictionary<string, string[]> { [id] = WickBook.Path(Enumerable.Range(1, 4).Select(n => $"linger.{n}").ToArray(), id) } : null,
            });
            B.Calling = "warden";
            B.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -B.Stats.Get(Stat.CritChance), "test"));
            W = B.Weapons[0];
            W.Timer = 0;
            if (period is double p)
            {
                W.Press = W.Press!.WithChain(p > 0 ? new ChainDef { Grace = 0.40, Recover = 18, Period = p } : new ChainDef { Grace = 0.40, Recover = 18 });
                Assert.Null(W.Def.Press!.Chain);
            }
            // (the plain run of the shipped strand keeps the strand's other numbers: only its ground is taken off)
            if (shipped) { Assert.Equal(Spec, W.Wick!.Ground); if (!ground) W.Wick.Ground = null; }
            else if (ground || onKill) W.Wick = new WickFx { Ground = ground ? Spec : null, OnKill = onKill, OnKillGap = 0.5, OnKillDamage = 0.6 };
            if (answers)
            {
                B.Lamps = new LampLoadout();
                B.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "oathblade.shield_and_edge", Args = new Dictionary<string, double>() });
                B.AddBoon("warding");
            }
            // a flat rule on every hit that changes nothing in the fight: its firings are the procs a second
            B.AddTrigger(new TriggerDef { On = TriggerEvent.Hit, Effects = [new Effect.Cooldown(0, Effect.CooldownScope.Ability)] }, "test:flat");
            Flat = B.Triggers[^1];
            E = B.SpawnEnemy("footpad", 2, 0)!;
            E.Hp = E.MaxHp = Hp0;
            E.AttackT = E.RangedT = 999;
        }

        public double Damage => Hp0 - E.Hp;
        public IEnumerable<ZoneRec> Own => Zones.Where(z => !z.Echo);

        public void Block()
        {
            int n = B.Blocks;
            B.Player.Iframes = 0; B.Player.BlockT = 0;
            B.HurtPlayer(10, School.Physical, "test", null);
            Assert.Equal(n + 1, B.Blocks);
        }

        /// <param name="fodder">Every this many steps a foe that dies to one cut stands beside the dummy (0: none).</param>
        public Run Hold(int steps, int fodder = 0)
        {
            for (int i = 0; i < steps; i++)
            {
                if (fodder > 0 && i % fodder == 0)
                {
                    var f = B.SpawnEnemy("footpad", 2, 0.5)!;
                    f.Hp = f.MaxHp = 0.01; f.AttackT = f.RangedT = 999;
                    Fodder++;
                }
                B.HoldSkill(W.Slot, true, E.X, E.Z);
                E.X = 2; E.Z = 0; E.Vx = E.Vz = 0;
                B.Tick(Dt, 0, 0);
                int laid = 0; double dps = 0;
                foreach (var z in B.Zones.Items)
                {
                    if (!z.Alive || z.Weapon != W.Id) continue;
                    if (!seen.TryGetValue(z, out double age) || z.Age < age)
                    {
                        Zones.Add(new ZoneRec(B.Time, z.Dps, z.Echo, z.X, z.Z, z.Radius, z.Life));
                        if (!z.Echo) { laid++; dps = z.Dps; }
                    }
                    seen[z] = z.Age;
                }
                // (one cast a step at most; a swing of two arcs tells two slashes)
                bool slash = false;
                foreach (var ev in B.Events.Drain()) slash |= ev is Ev.Slash;
                if (slash && fodder == 0) Landed.Add(new CastRec(W.BlowN, W.BlowPart, W.CastW, laid, dps));
                if (fodder == 0 && laid > 0) Assert.True(Landed.Count > 0 && Landed[^1].Laid == laid, "a ground without a cast");
                if (W.Chain is { Live: true } c && c.StartAt != last) { last = c.StartAt; Cuts++; }
                if (W.OnKillT != onKillT) { onKillT = W.OnKillT; Echoes++; }
            }
            return this;
        }

        /// <summary>Held until cut k (0-based) has started and its blow is still to land.</summary>
        public void HoldToPending(int k)
        {
            while (Cuts < k + 1) Hold(1);
            Assert.Equal(1, B.PendingBlows);
            Assert.Equal(k, Landed.Count);
        }
    }

    static double Pct(double a, double b) => (a / b - 1) * 100;

    // ---- facts 1, 2, 3 and the brief's (1), (2): grounds a minute, their size, their damage and their procs a second ----

    [Theory]
    [InlineData("oathblade", false)]
    [InlineData("sunder", false)]
    [InlineData("oathblade", true)]
    public void A_held_chain_lays_one_ground_a_written_blow_at_the_blows_size(string id, bool shipped)
    {
        const int steps = 37800; // 630 s: a whole number of both waits' blows (1.05 s: 600, 1.6 s: 393.75) to within one
        double min = steps * Dt / 60;
        var c = new Run(id, 0.70, shipped: shipped).Hold(steps);
        var u = new Run(id, null, shipped: shipped).Hold(steps);
        var c0 = new Run(id, 0.70, ground: false, shipped: shipped).Hold(steps);
        var u0 = new Run(id, null, ground: false, shipped: shipped).Hold(steps);
        Assert.NotEqual(1, c.W.BlowWeight);
        Assert.Equal(1, u.W.BlowWeight);

        // the swings themselves are the same with and without the ground (so the difference is the grounds' own)
        Assert.Equal(c0.Landed.Count, c.Landed.Count);
        Assert.Equal(u0.Landed.Count, u.Landed.Count);
        int zc = c.Zones.Count, zu = u.Zones.Count;
        double dc = (c.Damage - c0.Damage) / (steps * Dt), du = (u.Damage - u0.Damage) / (steps * Dt);
        int pc = c.Flat.Count - c0.Flat.Count, pu = u.Flat.Count - u0.Flat.Count;
        output.WriteLine($"{id}{(shipped ? " (shipped Linger strand, rank 4)" : "")}, {steps * Dt:F0} s held, cut weight {c.W.BlowWeight:F4}:");
        output.WriteLine($"  casts: chained {c.Landed.Count} cuts = {c.W.BlowN + c.W.BlowPart:F3} blows | unchained {u.Landed.Count} blows");
        output.WriteLine($"  grounds a minute: chained {zc / min:F3} ({zc}) | unchained {zu / min:F3} ({zu}) | {Pct(zc, zu):+0.00;-0.00}%");
        output.WriteLine($"  ground dps (each): chained {c.Zones.Min(z => z.Dps):F6}..{c.Zones.Max(z => z.Dps):F6} | unchained {u.Zones[0].Dps:F6}");
        output.WriteLine($"  ground damage a second on the dummy: chained {dc:F5} | unchained {du:F5} | {Pct(dc, du):+0.00;-0.00}%");
        output.WriteLine($"  flat procs: all, chained {c.Flat.Count} | unchained {u.Flat.Count} | {Pct(c.Flat.Count, u.Flat.Count):+0.00;-0.00}%; off the grounds' ticks, chained {pc} | unchained {pu} | {Pct(pc, pu):+0.00;-0.00}%");

        // unchained: a ground a swing, as ever
        Assert.Equal(u.Landed.Count, zu);
        Assert.All(u.Landed, l => Assert.Equal(1, l.Laid));
        // chained: one a written blow (not one a cut), within 1%
        Assert.True(zc < c.Landed.Count * 0.8, "one a cut");
        // per WRITTEN BLOW FIRED (every row): grounds, their damage and their procs, chained as unchained
        double bc = c.W.BlowN + c.W.BlowPart, bu = u.W.BlowN + u.W.BlowPart;
        Assert.Equal(u.Landed.Count, bu, 6);
        output.WriteLine($"  a written blow fired: grounds {zc / bc:F4} | {zu / bu:F4}; ground damage {(c.Damage - c0.Damage) / bc:F4} | {(u.Damage - u0.Damage) / bu:F4} ({Pct((c.Damage - c0.Damage) / bc, (u.Damage - u0.Damage) / bu):+0.00;-0.00}%); procs {pc / bc:F4} | {pu / bu:F4} ({Pct(pc / bc, pu / bu):+0.00;-0.00}%); blows a second chained v unchained {Pct(bc, bu):+0.00;-0.00}%");
        Assert.True(Math.Abs(zc - bc) < 1 - 1e-6);
        Assert.True(Math.Abs(Pct(zc / bc, zu / bu)) <= 0.5, $"grounds a blow {zc / bc} v {zu / bu}");
        Assert.True(Math.Abs(Pct((c.Damage - c0.Damage) / bc, (u.Damage - u0.Damage) / bu)) <= 1);
        Assert.True(Math.Abs(Pct(pc / bc, pu / bu)) <= 2);
        // each chained ground is the written blow's, off a light cut and off a heavy one; place, reach and life the same
        var first = u.Zones[0];
        // (Sunder's own heavy falls on a fixed beat of its count and is never the first cut of a blow's worth)
        int heavyLaid = c.Landed.Count(l => l.Laid == 1 && l.CastW > c.W.BlowWeight + 1e-6);
        output.WriteLine($"  grounds laid by a heavy cut: {heavyLaid} of {c.Landed.Count(l => l.CastW > c.W.BlowWeight + 1e-6)} heavy cuts");
        if (id == "oathblade") Assert.True(heavyLaid > 0);
        Assert.Contains(c.Landed, l => l.Laid == 1 && Math.Abs(l.CastW - c.W.BlowWeight) < 1e-9);
        foreach (var z in c.Zones.Concat(u.Zones))
        {
            Assert.Equal(first.Dps, z.Dps, 6);
            Assert.Equal(first.X, z.X, 9); Assert.Equal(first.Z, z.Z, 9);
            Assert.Equal(first.Radius, z.Radius, 9); Assert.Equal(first.Life, z.Life, 9);
        }
        // per SECOND: the rank 1 rows (the written 1.05 s and 1.6 s). The shipped strand at rank 4 runs the chain's own
        // blows 1.7% under the unchained skill's on 60 Hz steps (the cut's wait in whole steps): the chain's pace, not
        // Linger's, told above and not asserted here.
        if (shipped) return;
        Assert.True(Math.Abs(Pct(zc, zu)) <= 1, $"grounds {zc} v {zu}");
        // their damage a second (they stack, each ticks on its own) and the procs their ticks set off: a ground's tick
        // carries no weight (it is a whole hit, outside any cast), and with one ground a written blow that is neutral
        Assert.True(du > 0 && pu > 0);
        Assert.True(Math.Abs(Pct(dc, du)) <= 1, $"ground damage a second {dc} v {du}");
        Assert.True(Math.Abs(Pct(pc, pu)) <= 2, $"procs off the grounds {pc} v {pu}");
        Assert.True(Math.Abs(Pct(c.Flat.Count, u.Flat.Count)) <= 2, $"procs {c.Flat.Count} v {u.Flat.Count}");
    }

    // ---- facts 6: unchained and a chain with no period, as they were ----

    [Theory]
    [InlineData("oathblade")]
    [InlineData("sunder")]
    public void Unchained_and_a_chain_with_no_period_lay_a_ground_a_swing_as_before(string id)
    {
        foreach (double? period in new double?[] { null, 0 })
        {
            var r = new Run(id, period).Hold(3600);
            Assert.Equal(1, r.W.BlowWeight);
            Assert.Equal(-1, r.W.GroundKey);
            Assert.True(r.Landed.Count > 20);
            Assert.Equal(r.Landed.Count, r.Zones.Count);
            // (bit for bit: the swing's own number, read outside a cast, where CutW is 1)
            Assert.All(r.Zones, z => Assert.Equal(r.W.Damage * Spec.DpsPct, z.Dps));
            Assert.All(r.Zones, z => Assert.False(z.Echo));
            output.WriteLine($"{id}, {(period == null ? "unchained" : "chain, no period")}: {r.Landed.Count} swings, {r.Zones.Count} grounds at {r.Zones[0].Dps:R}");
        }
    }

    // ---- facts 4 (as ruled: an echo lays its ground as an unchained echo does) and the brief's (3) ----

    [Theory]
    [InlineData("oathblade")]
    [InlineData("sunder")]
    public void An_on_kill_echo_lays_its_ground_chained_as_unchained_and_takes_no_blows_ground(string id)
    {
        const int steps = 7200;
        var c = new Run(id, 0.70, onKill: true).Hold(steps, fodder: 150);
        var u = new Run(id, null, onKill: true).Hold(steps, fodder: 150);
        var plain = new Run(id, 0.70).Hold(steps);
        int ec = c.Zones.Count(z => z.Echo), eu = u.Zones.Count(z => z.Echo);
        output.WriteLine($"{id}: echoes chained {c.Echoes} -> {ec} echo grounds | unchained {u.Echoes} -> {eu} echo grounds; own grounds chained {c.Own.Count()} (no echoes: {plain.Zones.Count}) | unchained {u.Own.Count()}");
        Assert.True(c.Echoes > 20 && u.Echoes > 20);
        // one ground an echo, on both
        Assert.Equal(u.Echoes, eu);
        Assert.Equal(c.Echoes, ec);
        // at the echo's size on both: the written blow's at the Turn's strength (0.6)
        double own = u.Own.First().Dps;
        Assert.All(u.Zones.Concat(c.Zones).Where(z => z.Echo), z => Assert.Equal(own * 0.6, z.Dps, 6));
        Assert.All(c.Own, z => Assert.Equal(own, z.Dps, 6));
        // the echo took no blow's ground: her own are what they are with no echo in the fight
        Assert.Equal(plain.Zones.Count, c.Own.Count());
    }

    // ---- the brief's (4): a block's answer in a held run lays exactly one, and the count holds ----

    [Fact]
    public void A_blocks_answer_lays_exactly_one_ground_and_the_count_stays_one_a_written_blow()
    {
        double blow = new Run("oathblade", null).Hold(240).Zones[0].Dps;
        int had = 0;
        // (the three phases of a 2/3 cut: the answer reads a blow with no ground yet, or one whose ground is laid)
        foreach (int k in new[] { 1, 2, 3, 4, 5, 6 })
        {
            var r = new Run("oathblade", 0.70, answers: true);
            r.HoldToPending(k);
            r.Block();
            Assert.True(r.W.AnswerDue);
            r.Hold(600);
            int a = r.Landed.FindIndex(l => Math.Abs(l.CastW - 1) < 1e-9);
            Assert.Equal(k + 1, a);
            Assert.Single(r.Landed, l => Math.Abs(l.CastW - 1) < 1e-9);
            // the answer's own cast lays one ground, the written blow's
            Assert.Equal(1, r.Landed[a].Laid);
            Assert.Equal(blow, r.Landed[a].Dps, 6);
            // the blow it read had its ground already (the cut before laid it and completed nothing): the answer's is
            // the NEXT blow's, and the cut after it lays none
            bool hadIt = r.Landed[a - 1].Laid == 1 && r.Landed[a - 1].N == r.Landed[a - 2].N;
            if (hadIt) { had++; Assert.Equal(0, r.Landed[a + 1].Laid); }
            // no double, no lost: the grounds laid stay within one of the written blows fired, after every cast
            int z = 0;
            foreach (var l in r.Landed)
            {
                z += l.Laid;
                Assert.True(Math.Abs(z - (l.N + l.Part)) < 1 - 1e-6, $"k {k}: {z} grounds at {l.N + l.Part:F3} blows");
                if (l.Laid > 0) Assert.Equal(blow, l.Dps, 6);
            }
            Assert.Equal(z, r.Zones.Count);
            output.WriteLine($"block at pending cut {k}: answer = cast {a}, laid {r.Landed[a].Laid} at {r.Landed[a].Dps:F6} (blow {blow:F6}), its blow had a ground: {hadIt}; {z} grounds over {r.Landed[^1].N + r.Landed[^1].Part:F3} blows; grounds by cast: {string.Join("", r.Landed.Take(a + 4).Select(l => l.Laid))}");
        }
        Assert.True(had >= 1, "no run met an answer on a blow whose ground was laid");
        Assert.True(had < 6, "no run met an answer on a blow with no ground yet");
    }
}
