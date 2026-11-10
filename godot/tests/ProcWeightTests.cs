using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 p1) Battle.Fire on a chained cut: a rule a cut sets off keeps its per-second rate against the
/// written blows (Procs.cs ProcClass: a Whole rule fires once per blow's worth of would-fires and sees the blow; a
/// Sized one runs on every cut, share-sized, and a status it applies is weighed by the status step). Every test holds
/// the SAME skill for 63.9 s, chained (period 0.70, on a copy of its record: no shipped record has a chain) against
/// unchained, crit off, on foes that do not die. The chained run is not a whole number of blows (Sunder: 92 cuts =
/// 40.25 blows' worth against 40 blows, +0.6%), which is inside every line below.</summary>
public sealed class ProcWeightTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public ProcWeightTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;
    const int Steps = 3834;

    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        readonly List<(Enemy E, double Z)> more = new();
        public int Cuts, Landed;

        /// <param name="ride">A status put on the skill's hits (by a wick that does nothing else).</param>
        public Rig(string id, bool chained, int seed = 5, int pack = 1, StatusPayload? ride = null)
        {
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
                Assert.NotSame(W.Def.Press!.Chain, W.Press.Chain);
            }
            // (the switch: the shipped record carries a chain; the unchained run takes it off its own copy)
            else W.Press = W.Press?.WithChain(null);
            if (ride != null)
            {
                Assert.Null(W.StatusOf);
                W.Wick = new WickFx { Statuses = { new WickStatus(ride, 0, 0) } };
            }
            E = Foe(0);
            if (pack > 1) { more.Add((Foe(0.7), 0.7)); more.Add((Foe(-0.7), -0.7)); }
        }

        Enemy Foe(double z)
        {
            var e = B.SpawnEnemy("footpad", 2, z)!;
            e.Hp = e.MaxHp = 1e9;
            e.AttackT = e.RangedT = 999;
            return e;
        }

        /// <summary>A rule of the test's own, and its live instance (Count: the times its effects ran).</summary>
        public TriggerInstance Rule(string source, TriggerDef def)
        {
            B.AddTrigger(def, source);
            var t = B.Triggers[^1];
            Assert.Same(def, t.Def);
            return t;
        }

        public double By(string source) => B.DamageBy.GetValueOrDefault(source);

        public Rig Hold(Action? each = null)
        {
            for (int i = 0; i < Steps; i++)
            {
                B.HoldSkill(W.Slot, true, E.X, E.Z);
                E.X = 2; E.Z = 0; E.Vx = E.Vz = 0;
                foreach (var (e, z) in more) { e.X = 2; e.Z = z; e.Vx = e.Vz = 0; }
                B.Tick(Dt, 0, 0);
                foreach (var ev in B.Events.Drain())
                {
                    if (ev is Ev.Slash) Cuts++;
                    else if (ev is Ev.Status st && st.Target == E.Id) Landed++;
                }
                each?.Invoke();
            }
            return this;
        }
    }

    /// <summary>A flat effect that changes nothing in the fight (no seconds off a cooldown): the rule is Whole, and its
    /// firings are read off TriggerInstance.Count (the times its effects ran).</summary>
    static TriggerDef Flat(TriggerEvent on, double? icd = null, TriggerCond? when = null)
    {
        var def = new TriggerDef { On = on, Icd = icd, When = when, Effects = [new Effect.Cooldown(0, Effect.CooldownScope.Ability)] };
        Assert.Equal(ProcClass.Whole, def.Weighs());
        return def;
    }

    (int C, int U, string Told) Firings(string what, double? icd, int pack)
    {
        var c = new Rig("sunder", true, pack: pack);
        var u = new Rig("sunder", false, pack: pack);
        var tc = c.Rule("test:flat", Flat(TriggerEvent.Hit, icd));
        var tu = u.Rule("test:flat", Flat(TriggerEvent.Hit, icd));
        c.Hold(); u.Hold();
        string told = $"{what}: chained {tc.Count} firings ({c.Cuts} cuts, part left {tc.Part:F4}) | unchained {tu.Count} ({u.Cuts} blows) | {((double)tc.Count / tu.Count - 1) * 100:+0.00;-0.00}%";
        output.WriteLine(told);
        return (tc.Count, tu.Count, told);
    }

    [Fact]
    public void A_flat_proc_comes_once_a_blows_worth()
    {
        // no chance, no icd: 92 cuts would fire it 92 times; it runs on the first and then once per 1 / 0.4375 cuts
        var (c, u, told) = Firings("flat on hit", null, 1);
        Assert.True(Math.Abs((double)c / u - 1) <= 0.02, told);
        // icd 4: the blows fire it every third (4.8 s); the cuts' clock is 4 x 0.4375 = 1.75 s, every third cut (2.1 s),
        // and a blow's worth of those is 2.1 / 0.4375 = 4.8 s
        (c, u, told) = Firings("flat on hit, icd 4", 4, 1);
        Assert.True(Math.Abs((double)c / u - 1) <= 0.05, told);
        // three foes in the cut, icd 1: one firing a blow (the icd eats the other two foes' hits) on both sides
        (c, u, told) = Firings("flat on hit, three foes, icd 1", 1, 3);
        Assert.True(Math.Abs((double)c / u - 1) <= 0.05, told);
        // (beside the brief's three) three foes and no icd: every foe's hit counts its share
        (c, u, told) = Firings("flat on hit, three foes", null, 3);
        Assert.True(Math.Abs((double)c / u - 1) <= 0.02, told);
    }

    [Theory]
    [InlineData(null)]
    [InlineData(1.0)]
    public void A_hit_sized_proc_gives_the_same_a_second_under_an_icd(double? icd)
    {
        // the shape of the item at godot/data/content/items.json:1500: a nova of half the hit, no knockback
        TriggerDef Nova() => new() { On = TriggerEvent.Hit, Icd = icd, Effects = [new Effect.Nova(3, 0.5, Basis.Hit, School.Physical)] };
        Assert.Equal(ProcClass.Sized, Nova().Weighs());
        var c = new Rig("sunder", true);
        var u = new Rig("sunder", false);
        var tc = c.Rule("test:nova", Nova());
        var tu = u.Rule("test:nova", Nova());
        c.Hold(); u.Hold();
        double dc = c.By("test:nova"), du = u.By("test:nova");
        string told = $"nova 0.5 x hit, icd {icd?.ToString() ?? "none"}: chained {dc:F1} in {tc.Count} novas ({c.Cuts} cuts) | unchained {du:F1} in {tu.Count} ({u.Cuts} blows) | {(dc / du - 1) * 100:+0.00;-0.00}%";
        output.WriteLine(told);
        Assert.True(du > 0, told);
        Assert.True(Math.Abs(dc / du - 1) <= 0.02, told);
    }

    /// <summary>T3(a)'s run: an on-hit Apply of a sure stacking burn (3 s). Burn caps at 5 stacks, so the stacks ADDED
    /// are read every tick as the rise over the tick before, and the slot is then set back to 1 stack (its time and
    /// power untouched), which the cap can never hide. Beside it, two rules on the Status event the burn raises: a flat
    /// (Whole) one, counted, and a nova of the hit (Sized), summed: what a landed burn's event weighs.</summary>
    (double Added, int Landed, int Lapses, double MinT, int Whole, double Sized) Burn(bool chained)
    {
        var r = new Rig("sunder", chained);
        var apply = new TriggerDef { On = TriggerEvent.Hit, When = new TriggerCond { NotTag = Tag.Nova }, Effects = [new Effect.Apply(new StatusPayload(StatusKind.Burn, 1, 0.5, 3), true)] };
        Assert.Equal(ProcClass.Sized, apply.Weighs());
        r.Rule("test:burn", apply);
        var whole = r.Rule("test:onburn", Flat(TriggerEvent.Status, null, new TriggerCond { Applied = StatusKind.Burn }));
        r.Rule("test:burnnova", new TriggerDef { On = TriggerEvent.Status, When = new TriggerCond { Applied = StatusKind.Burn }, Effects = [new Effect.Nova(3, 1, Basis.Hit, School.Physical)] });
        double added = 0, minT = double.PositiveInfinity;
        int landed = 0, lapses = 0;
        bool had = false;
        r.Hold(() =>
        {
            var s = r.E.Status[StatusKind.Burn];
            if (s == null || s.T <= 0) { if (had) lapses++; had = false; return; }
            double before = had ? 1 : 0;
            if (s.Stacks > before + 1e-12) { added += s.Stacks - before; landed++; }
            else minT = Math.Min(minT, s.T);
            s.Stacks = 1;
            had = true;
        });
        return (added, landed, lapses, minT, whole.Count, r.By("test:burnnova"));
    }

    [Fact]
    public void A_status_from_a_proc_builds_at_the_blows_rate()
    {
        // (a) a sure burn applied by an on-hit rule: every cut lands one, building the share of a blow it stands for
        var c = Burn(true);
        var u = Burn(false);
        string told = $"burn by an on-hit apply: chained {c.Added:F4} stacks added in {c.Landed} landings, lapses {c.Lapses}, least time left {c.MinT:F2} s"
            + $" | unchained {u.Added:F4} in {u.Landed}, lapses {u.Lapses}, least time left {u.MinT:F2} s | {(c.Added / u.Added - 1) * 100:+0.00;-0.00}% ({c.Added - u.Added:+0.000;-0.000} stacks)";
        output.WriteLine(told);
        Assert.Equal(0, c.Lapses);
        Assert.Equal(0, u.Lapses);
        // (both sides also count the burn's own ticks: a tick of damage over time is a hit at weight 1, so the on-hit
        // rule lands a whole stack on each, 127 a side. The cuts against the blows are the +0.813 stacks between them:
        // the first cut's whole stack, 1 - 0.4375, and the run's 0.25 of a blow more.)
        // (the first application is a whole stack by design: one stack's difference allowed, else 2%)
        Assert.True(Math.Abs(c.Added - u.Added) <= 1 || Math.Abs(c.Added / u.Added - 1) <= 0.02, told);
        // the Status event of each landed burn carries W = build, the FIRST one too (which landed a whole stack). A
        // Whole rule on it does not see that (its first firing is whole anyway); a Sized one is paid the first cut's
        // share for it, so what the events weigh is the cuts' shares (the blows' worth of the run), not the stacks.
        string open = $"rules on the burn's Status event: flat (whole) chained {c.Whole} | unchained {u.Whole}; nova of the hit (sized) chained {c.Sized:F1} | unchained {u.Sized:F1} | {(c.Sized / u.Sized - 1) * 100:+0.00;-0.00}%";
        output.WriteLine(open);
        Assert.True(Math.Abs(c.Whole - u.Whole) <= 1, open);
        Assert.True(Math.Abs(c.Sized / u.Sized - 1) <= 0.02, open);

        // (b) a Whole rule on the Status event, under the cut's own bleed (Oathblade's written one riding its hits:
        // 0.35 a blow, weight 0.6667): each landed bleed counts the share of a blow it stands for
        var bleed = new StatusPayload(StatusKind.Bleed, 0.35, 0.3, 3);
        (double Mean, double Se, double Counted, double Landed, double Worth) Mean(bool chained)
        {
            var v = new double[SeedsB];
            var counted = new double[SeedsB];
            var landed = new double[SeedsB];
            var worth = new double[SeedsB];
            Parallel.For(0, SeedsB, i =>
            {
                var r = new Rig("oathblade", chained, seed: i + 1, ride: bleed);
                var t = r.Rule("test:onbleed", Flat(TriggerEvent.Status, null, new TriggerCond { Applied = StatusKind.Bleed }));
                r.Hold();
                v[i] = t.Count;
                counted[i] = t.Count + t.Part;
                landed[i] = r.Landed;
                worth[i] = r.W.BlowN + r.W.BlowPart;
            });
            double m = v.Average();
            return (m, Math.Sqrt(v.Sum(x => (x - m) * (x - m)) / (SeedsB - 1) / SeedsB), counted.Average(), landed.Average(), worth.Average());
        }
        var bc = Mean(true);
        var bu = Mean(false);
        double ratio = bc.Mean / bu.Mean, se = ratio * Math.Sqrt(bc.Se * bc.Se / (bc.Mean * bc.Mean) + bu.Se * bu.Se / (bu.Mean * bu.Mean));
        string toldB = $"flat rule on the bleed's Status event: chained {bc.Mean:F3} firings (se {bc.Se:F3}) | unchained {bu.Mean:F3} (se {bu.Se:F3}) | {(ratio - 1) * 100:+0.00;-0.00}% (se {se * 100:F2}%), {SeedsB} seeds"
            + $"; firings + the part left: chained {bc.Counted:F3} ({(bc.Counted / bu.Mean - 1) * 100:+0.00;-0.00}%); bleeds landed: chained {bc.Landed:F3} | unchained {bu.Landed:F3}";
        output.WriteLine(toldB);
        Assert.True(3 * se <= 0.03, "too few seeds: " + toldB);
        // The measure (main): firings PLUS the part the rule still holds at the close, within 3%. Measured (600 seeds,
        // 63.9 s) -2.86%, and its cause is named (s4, 200 seeds held 630 s; docs/balance/chain_weight.md):
        // (1) -1.61% is blows' worth CAST, 61.000 against 62. The chain keeps the written wait to the instant (600.000
        //     worth in 630 s, 1.0500 s each); the UNCHAINED swing runs a part of a 1/60 s step fast (603 blows, 62.77
        //     steps each where 1.05 s is 63: -0.50% for good), and its 62nd blow lands on step 3833 of this window's
        //     3834 (the edge, -1.1%: the worth ratio is 0.9839 here, 0.9917 at 126 s, 0.9950 at 630 s).
        // (2) the rest is the 0.35 roll's noise (se 0.98% here): per blow's worth cast the rule counts the same on both
        //     records, chained over unchained 1.0132 at 126 s, 0.9996 at 315 s, 0.9998 at 630 s.
        // So the law is held per blow's worth cast (2.5 se of this run), and the whole count to the decided 3%.
        double perWorth = bc.Counted / bc.Worth / (bu.Mean / bu.Worth);
        toldB += $"; blows' worth cast: chained {bc.Worth:F3} | unchained {bu.Worth:F3}; firings + part per blow's worth, chained over unchained {perWorth:F4}";
        output.WriteLine(toldB);
        Assert.True(Math.Abs(bc.Counted / bu.Mean - 1) <= 0.03, toldB);
        Assert.True(Math.Abs(perWorth - 1) <= 2.5 * se, toldB);
    }

    const int SeedsB = 600;
}
