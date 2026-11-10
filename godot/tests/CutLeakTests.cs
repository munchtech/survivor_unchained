using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 l1) The callings' hooks that counted per hit, on a chained cut: Frenzy's stack (butcher.red_hands),
/// the Long Chain's pull (HookLast), the stalker's true-strike poison (StalkerOnHit) and the arcanist's Frostfire
/// (ArcanistOnHit) hold per second. The harness is TailWeightTests': the SAME skill held 63.9 s, chained (period 0.70,
/// on a copy of its record) against unchained, on a foe that does not die and is held where it stands.</summary>
public sealed class CutLeakTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public CutLeakTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;
    const int Steps = 3834;

    sealed class Rig
    {
        public readonly Battle B;
        public readonly WeaponInst W;
        public readonly Enemy E;
        public int Cuts;
        /// <summary>The knockback the foe was given, summed along x (away from her is +; the rig clears it before each
        /// tick, so what a tick leaves is that tick's own, at most one decay step old on both records alike).</summary>
        public double Kb;

        public Rig(string id, bool chained, int seed = 5, double crit = 0)
        {
            B = new Battle(new BattleSetup
            {
                Seed = (uint)seed, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [(id, 1)], Ability = AbilityKind.ShieldBash,
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

        public Rig Lit(params LampEffect[] rules)
        {
            B.Lamps = new LampLoadout();
            foreach (var r in rules) B.Lamps.Add(r);
            return this;
        }

        public void Step()
        {
            B.HoldSkill(W.Slot, true, 2, 0);
            E.X = 2; E.Z = 0; E.Vx = E.Vz = 0; E.Kbx = E.Kbz = 0;
            B.Tick(Dt, 0, 0);
            foreach (var ev in B.Events.Drain()) if (ev is Ev.Slash) Cuts++;
            Kb += E.Kbx;
        }

        public Rig Hold(Action<int>? each = null, int steps = Steps)
        {
            for (int i = 0; i < steps; i++)
            {
                Step();
                each?.Invoke(i);
            }
            return this;
        }
    }

    static LampEffect Rule(string rule, Dictionary<string, double>? args = null) =>
        new() { Do = LampDo.Rule, Rule = rule, Args = args ?? new(), Lamp = "" };

    static double Wait(string id) => id == "sunder" ? 1.6 : 1.05;

    // (a) butcher.red_hands: a stack is a blow's. Before: one per cut, the cap at 14 s against 21 s (Oathblade).
    [Theory]
    [InlineData("oathblade")]
    [InlineData("sunder")]
    public void Frenzy_ramps_as_fast_under_a_chain_as_under_the_blows(string id)
    {
        const double cap = 20;
        static LampEffect Frenzy() => Rule("frenzy", new() { ["per"] = 0.01, ["cap"] = cap, ["fade"] = 3 });
        var plain = new Rig(id, false).Lit(Frenzy());
        var chain = new Rig(id, true).Lit(Frenzy());
        var a = new double[Steps]; var c = new double[Steps];
        plain.Hold(i => a[i] = plain.B.Frenzy);
        chain.Hold(i => c[i] = chain.B.Frenzy);
        Assert.True(chain.Cuts > plain.Cuts * 1.4, "the chain did not swing");
        double At(double[] f, double stacks) { int i = Array.FindIndex(f, v => v >= stacks - 1e-9); return i < 0 ? double.NaN : (i + 1) * Dt; }
        double wait = Wait(id), cw = 0.70 / wait;
        // the ramp: while the unchained record is still under the cap
        int ramp = Array.FindIndex(a, v => v >= cap - 1e-9);
        Assert.True(ramp > 0, "the unchained record never filled Frenzy");
        double worst = 0; int worstAt = 0;
        for (int i = 0; i < ramp; i++) if (Math.Abs(c[i] - a[i]) > worst) { worst = Math.Abs(c[i] - a[i]); worstAt = i; }
        output.WriteLine($"{id} frenzy: stacks at 5 s chained {c[299]:0.###} / unchained {a[299]:0.###}, at 10 s {c[599]:0.###} / {a[599]:0.###}; "
            + $"to 5 / 10 / 15 / cap chained {At(c, 5):0.00} / {At(c, 10):0.00} / {At(c, 15):0.00} / {At(c, cap):0.00} s, unchained {At(a, 5):0.00} / {At(a, 10):0.00} / {At(a, 15):0.00} / {At(a, cap):0.00} s; "
            + $"widest gap on the ramp {worst:0.###} stacks at {(worstAt + 1) * Dt:0.00} s (a cut weighs {cw:0.####}); {chain.Cuts} cuts, {plain.Cuts} blows");
        // the cap is reached at the same time, within one written blow (the blow's wait shrinks as Frenzy fills)
        foreach (double s in new[] { 5.0, 10, 15, cap })
            Assert.InRange(At(c, s) - At(a, s), -wait, wait);
        // and on the way the stacks held are a blow's worth apart at most (the blows step by 1, the cuts by their weight)
        Assert.True(worst <= 1 + cw + 1e-6, $"the stacks drift apart on the ramp: {worst:0.###} at {(worstAt + 1) * Dt:0.00} s");
        // filled, both hold the cap
        Assert.Equal(cap, a[Steps - 1], 6);
        Assert.Equal(cap, c[Steps - 1], 6);
    }

    // (b) chainbound.the_long_chain: the pull a second holds. Before: a whole blow's pull per cut (1.5x / 2.29x).
    [Theory]
    [InlineData("oathblade")]
    [InlineData("sunder")]
    public void The_long_chain_pulls_as_much_a_second_under_a_chain(string id)
    {
        static LampEffect Chain() => Rule("long_chain", new() { ["reach"] = 3, ["weaker"] = 0.2 });
        // the pull alone: what the lamp takes off the skill's own push (the same casts, lit and unlit)
        double Pull(bool chained, out int cuts, out double push)
        {
            var bare = new Rig(id, chained).Hold();
            var lit = new Rig(id, chained).Lit(Chain()).Hold();
            Assert.Equal(bare.Cuts, lit.Cuts);
            cuts = lit.Cuts; push = bare.Kb;
            return bare.Kb - lit.Kb;
        }
        double a = Pull(false, out int blows, out double pushA), c = Pull(true, out int cuts, out double pushC);
        output.WriteLine($"{id} long_chain pull summed over 63.9 s: chained {c:0.###} ({cuts} cuts), unchained {a:0.###} ({blows} blows), ratio {c / a:0.0000}; the skill's own push {pushC:0.###} / {pushA:0.###}, ratio {pushC / pushA:0.0000}");
        Assert.True(cuts > blows * 1.4, "the chain did not swing");
        Assert.True(a > 0, "the lamp pulled nothing");
        Assert.InRange(c / a, 0.98, 1.02);
    }

    /// <summary>What the foe's poison paid over the hold (its rate x its stacks, summed over the time it ran), and when
    /// it first held the cap.</summary>
    static (double Paid, double Capped, double RampStacks) Poisoned(Rig r)
    {
        double paid = 0, capped = double.NaN, ramp = 0;
        r.Hold(i =>
        {
            if (r.E.Status[StatusKind.Poison] is not { T: > 0 } s) return;
            paid += s.Power * s.Stacks * Dt;
            if (i < 540) ramp += s.Stacks * Dt;
            if (double.IsNaN(capped) && s.Stacks >= 10 - 1e-9) capped = (i + 1) * Dt;
        });
        return (paid, capped, ramp);
    }

    // (c) roadknife's true-strike poison: stacks build by the cut's weight, sized on the blow. Before: a whole stack
    // per cut (the cap at 6.3 s against 9.45 s) at the cut's size (0.67x the rate once capped).
    [Theory]
    [InlineData("oathblade", 1)]
    [InlineData("oathblade", 3)]
    [InlineData("sunder", 1)]
    public void A_true_strikes_poison_builds_and_pays_as_the_blows_did(string id, int stacks)
    {
        LampEffect[] Lamps() => stacks == 1
            ? [Rule("true.poison", new() { ["stacks"] = 1 })]
            : [Rule("true.poison", new() { ["stacks"] = 1 }), Rule("venom_edge", new() { ["stacks"] = stacks - 1 })];
        // every blow strikes true
        var plain = new Rig(id, false, crit: 1).Lit(Lamps());
        var chain = new Rig(id, true, crit: 1).Lit(Lamps());
        var a = Poisoned(plain); var c = Poisoned(chain);
        output.WriteLine($"{id} true-strike poison ({stacks} a strike) over 63.9 s: paid chained {c.Paid:0.##} ({chain.Cuts} cuts), unchained {a.Paid:0.##} ({plain.Cuts} blows), ratio {c.Paid / a.Paid:0.0000}; "
            + $"the cap of 10 at {c.Capped:0.00} s chained, {a.Capped:0.00} s unchained; stack-seconds in the first 9 s {c.RampStacks:0.##} / {a.RampStacks:0.##}, ratio {c.RampStacks / a.RampStacks:0.000}");
        Assert.True(chain.Cuts > plain.Cuts * 1.4, "the chain did not swing");
        Assert.True(a.Paid > 0, "no poison was laid");
        Assert.InRange(c.Paid / a.Paid, 0.97, 1.03);
        Assert.InRange(c.Capped - a.Capped, -Wait(id), Wait(id));
    }

    // (d) kindler.frostfire on a cut turned to frost (a Wick's or an evolution's school): the burn it lays is sized on
    // the blow. Before: sized on the cut's share and kept by its worst rate (0.67x).
    [Fact]
    public void Frostfires_burn_under_a_chain_pays_as_the_blows_did()
    {
        Rig Make(bool chained)
        {
            var r = new Rig("oathblade", chained).Lit(Rule("frostfire", new() { ["weaker"] = 0.3 }));
            r.W.Evolution = new Evolution { Id = "test_frost", School = School.Frost };
            Assert.Equal(School.Frost, r.W.School);
            return r;
        }
        double Burned(Rig r)
        {
            double sum = 0;
            r.Hold(_ => { if (r.E.Status[StatusKind.Burn] is { T: > 0 } s) sum += s.Power * s.Stacks * Dt; });
            return sum;
        }
        var plain = Make(false); var chain = Make(true);
        double a = Burned(plain), c = Burned(chain);
        output.WriteLine($"oathblade (frost) frostfire burn paid over 63.9 s: chained {c:0.##} ({chain.Cuts} cuts), unchained {a:0.##} ({plain.Cuts} blows), ratio {c / a:0.0000}");
        Assert.True(chain.Cuts > plain.Cuts * 1.4, "the chain did not swing");
        Assert.True(a > 0, "no burn was laid");
        Assert.InRange(c / a, 0.97, 1.03);
    }

    // (e, l2) The Barrow Lord, down: a holy hit opens a 0.5 s window in which standing over him lays him down twice as
    // fast. A cut opens its weight's share of it (Battle.HitW), so the window is open as much of a second under the
    // chain. Before: a whole window per cut (the laying 1.16x on Oathblade's wait, 1.31x on Sunder's). The arena's
    // script, held down by the test (its clocks put back each tick), struck holy at the blows' pace and at the cuts'.
    [Theory]
    [InlineData(1.05)]
    [InlineData(1.6)]
    public void The_barrow_lords_holy_window_is_open_as_much_of_a_second_under_a_chain(double wait)
    {
        (double Open, double Laid) Down(double every, double? w)
        {
            // BossTests.At30("dead")
            var a = Callings.Archetype("warden");
            var j = Journey.Begin(new CreationChoice { Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 3);
            var spec = new ArenaSpec { Id = "table:test", Name = "Test", Seed = 3, Tier = 1, People = "dead" };
            Arenas.Begin(j.World, spec);
            var map = MapGen.Generate(spec.Map);
            var host = new HeadlessHost(j, 3);
            var zone = new ArenaRun(host, map, spec);
            var at = zone.ArrivalFrom(null);
            var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 3, arena: true);
            b.Hooks = zone.Hooks;
            host.Battle = b;
            zone.Begin(b);
            b.GreatOwed = 0;
            b.Time = 30 * 60 - 0.05;
            void Tick()
            {
                zone.Step(Dt); zone.Frame(Dt); b.Tick(Dt, 0, 0); b.Events.Drain(); host.Pass(Dt);
                b.PendingLevels = 0; b.PendingBlessings.Clear(); b.GreatOwed = 0; b.Player.Hp = b.MaxHp;
            }
            for (int i = 0; i < 12; i++) Tick();
            var boss = b.Enemies.Items.First(e => e.Alive && e.Boss);
            var s = Assert.IsType<BarrowLord>(zone.BossScript);
            bool IsDown() => boss.Alive && boss.TakenMul == 0 && s.Channel?.StartsWith("He will not lie down") == true;
            // down to nothing, the survivor kept away from him
            for (int i = 0; i < 200 * 60 && !IsDown(); i++)
            {
                Tick();
                if (boss.Alive && boss.TakenMul > 0) b.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
                if (s.Channel != null) { b.Player.X = boss.X + 20; b.Player.Z = boss.Z; }
            }
            Assert.True(IsDown(), "he never went down");
            var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;
            var layT = typeof(BarrowLord).GetField("layT", flags)!; var layHeld = typeof(BarrowLord).GetField("layHeld", flags)!;
            double open = 0, laid = 0, next = 0;
            for (int i = 0; i < 3600; i++)
            {
                // held down: he neither rises nor is laid; what a tick adds to the laying is that tick's own
                layT.SetValue(s, 0.0); layHeld.SetValue(s, 0.0);
                b.Player.X = boss.X + 1; b.Player.Z = boss.Z;
                if (i * Dt >= next - 1e-9) { next += every; b.HitEnemy(boss, 1, School.Holy, [Tag.Holy], new HitOpts { NoCrit = true, W = w }); }
                Assert.Equal(1.0, b.HitW);
                Tick();
                Assert.True(IsDown(), $"he did not stay down (tick {i})");
                double held = (double)layHeld.GetValue(s)!;
                laid += held;
                if (held > Dt * 1.5) open += Dt;
            }
            return (open, laid);
        }
        var plain = Down(wait, null);
        var chain = Down(0.70, 0.70 / wait);
        output.WriteLine($"holy window, blows every {wait} s against cuts every 0.70 s of weight {0.70 / wait:0.####}, 60 s down: open chained {chain.Open:0.###} s, unchained {plain.Open:0.###} s, ratio {chain.Open / plain.Open:0.0000}; "
            + $"the laying it grants {chain.Laid:0.###} / {plain.Laid:0.###}, ratio {chain.Laid / plain.Laid:0.0000}");
        Assert.True(plain.Open > 10, "the holy hits opened no window");
        // the laying a second holds
        Assert.InRange(chain.Laid / plain.Laid, 0.97, 1.03);
        // and the window's open time (a window is open a whole number of ticks: up to one tick over per hit on both
        // records, and the cuts are more hits)
        Assert.InRange(chain.Open / plain.Open, 0.97, 1.03);
    }
}
