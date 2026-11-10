using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Pilots;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 lead 4/5) The campaign fighter's feet (Pilot.StepsAndStands, Pilot's Feet.Plant, Pilot.Meter): she plants
/// and swings, takes one step across her foe, and plants again, under the story stand clock's own count; the arena's
/// hands are what they were. The campaign route: a veteran warden's campaign Battle (MapSim.Survivor, her taught build)
/// stepped here under Pilot.Steer / Pilot.Act with its own `new PackKit(b)` and the world tier's stand row from the data
/// (no zone); two footpads that fight back and never fall are the woken pack.</summary>
[Collection("PilotFeet")]
public sealed class FighterFeetTests
{
    const double Dt = 1 / 60.0;

    /* ------------------------------------------------------------- arena -- */

    /// <summary>A seeded arena fight under the Pilot: a footpad from the ring each half second, every draft's first card.
    /// What came of it, step by step.</summary>
    static string ArenaRun(bool feet, double seconds)
    {
        bool was = Pilot.StepsAndStands;
        Pilot.StepsAndStands = feet;
        try
        {
            var j = MapSim.Survivor("warden", 30, 2, 5);
            var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 11, arena: true);
            Assert.False(b.Campaign);
            var h = new HashCode();
            int n = 0, fallen = 0;
            double hurt = 0;
            for (int i = 0; i * Dt < seconds; i++)
            {
                if (i % 30 == 0) { double a = n++ * 2.4; b.SpawnEnemy("footpad", b.Player.X + Math.Cos(a) * 9, b.Player.Z + Math.Sin(a) * 9); }
                var (mx, mz) = Pilot.Steer(b, deft: i % 2 == 0);
                Pilot.Act(b, j, mx, mz);
                double hp = b.Player.Hp;
                b.Tick(Dt, mx, mz);
                hurt += Math.Max(0, hp - b.Player.Hp);
                while (b.DraftOwed) LevelUp.Choose(b, LevelUp.Draft(b, 3)[0]);
                foreach (var ev in b.Events.Drain()) if (ev is Ev.Kill) fallen++;
                h.Add(b.Player.X); h.Add(b.Player.Z); h.Add(b.Player.Hp); h.Add(b.Rng.State); h.Add(mx); h.Add(mz);
                foreach (var e in b.Enemies.Items) if (e.Alive) { h.Add(e.X); h.Add(e.Z); h.Add(e.Hp); }
                if (b.Over != null) break;
            }
            Assert.True(fallen > 5, $"{fallen} fell: no fight to compare");
            // (the feet's meter is the campaign's: nothing measured here)
            Assert.Equal(0, Pilot.Meter(b).InReach);
            Assert.Equal(0, Pilot.Meter(b).Plants);
            return FormattableString.Invariant(
                $"t {b.Time:R} at ({b.Player.X:R}, {b.Player.Z:R}) hp {b.Player.Hp:R} fell {fallen} kills {b.Weapons.Sum(w => w.Kills)} hurt {hurt:R} level {b.EmberLevel} rng {b.Rng.State} over {b.Over} hash {h.ToHashCode()}");
        }
        finally { Pilot.StepsAndStands = was; }
    }

    [Fact]
    public void The_arena_is_the_same_with_the_feet_on_or_off()
    {
        string on = ArenaRun(true, 25), off = ArenaRun(false, 25);
        Assert.Equal(on, off);
        // (and the run is seeded: itself again)
        Assert.Equal(on, ArenaRun(true, 25));
    }

    /* ---------------------------------------------------------- campaign -- */

    /// <summary>A campaign fight under the Pilot and the stand clock: what her feet did.</summary>
    internal sealed class Fight
    {
        public readonly Battle B;
        public readonly PackKit Kit;
        public readonly Teeth.Director Clock;
        public double Landed => B.SwingLanded;
        /// <summary>Each plant: where and when it began, when its step began (null: none yet, or she walked on), the farthest
        /// she came from the spot within StepMax x 2 of the step's start.</summary>
        public readonly List<(double X, double Z, double At, double? StepAt, double Far)> Plants = new();
        /// <summary>The longest she stood in one place (her feet's hands at rest), by the fight's clock.</summary>
        public double LongestStill;

        /// <summary>(M3 MR 3, the feet) The stand clock's steps: when, and the chained cut's beats then (NaN: none live);
        /// cuts dropped (each once); dashes begun; her place each half second (the trace two runs are compared on).</summary>
        public readonly List<(double At, double Stood, double Start, double Cancel, double End)> Steps = new();
        public int Dropped, Dashes, ChainedTicks;
        public readonly System.Text.StringBuilder Trace = new();

        /// <summary>dummy: the foes never attack (no telegraph, no lunge: nothing to dodge). unchained: her grips' chain
        /// blocks stripped off the weapons' own copies (the swing of Sim/Contact.cs).</summary>
        public Fight(double seconds, int foes = 2, bool dummy = false, bool unchained = false)
        {
            var j = MapSim.Survivor("warden", 30, 2, 5);
            B = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
            Assert.True(B.Campaign);
            // The world tier's stand row, as the story fights carry it (Journey.StartBattle with the tier on).
            Clock = WorldTiers.Get(WorldTiers.Default).Stand!;
            Assert.True(Clock is { Stand: true, StandSwing: > 0 }, "the default tier's stand row has no standSwing");
            B.StoryStand = Clock;
            Kit = new PackKit(B);
            Assert.False(Pilot.Wall(B));
            var pack = new HashSet<Enemy>();
            for (int i = 0; i < foes; i++)
            {
                var e = B.SpawnEnemy("footpad", 5 + i * 0.4, i * 1.6 - 0.8)!;
                e.Hp = e.MaxHp = 1e7;
                pack.Add(e);
            }
            if (unchained) foreach (var w in B.Weapons) if (w.Press?.Chain != null) w.Press = w.Press.WithChain(null);
            int plants = 0, steps = 0;
            double stillSince = 0, droppedAt = double.NaN;
            bool dashing = false;
            for (int i = 0; i * Dt < seconds; i++)
            {
                var p = B.Player;
                var (mx, mz) = Pilot.Steer(B);
                var m = Pilot.Meter(B);
                if (m.Plants > plants) { plants = m.Plants; Plants.Add((p.X, p.Z, B.Time, null, 0)); }
                if (Plants.Count > 0)
                {
                    var (px, pz, at, stepAt, far) = Plants[^1];
                    if (stepAt == null && m.Last.EndsWith("step")) stepAt = B.Time;
                    if (stepAt != null && B.Time <= stepAt + Pilot.StepMax * 2) far = Math.Max(far, Math.Sqrt((p.X - px) * (p.X - px) + (p.Z - pz) * (p.Z - pz)));
                    Plants[^1] = (px, pz, at, stepAt, far);
                }
                if (mx != 0 || mz != 0) stillSince = B.Time;
                LongestStill = Math.Max(LongestStill, B.Time - stillSince);
                if (dummy) foreach (var e in pack) { e.AttackT = e.RangedT = 999; }
                if (m.Steps > steps) { steps = m.Steps; Steps.Add((m.StepAt, m.StepStood, m.StepCutStart, m.StepCancel, m.StepEnd)); }
                Pilot.Act(B, j, mx, mz, drinks: false);
                B.Tick(Dt, mx, mz);
                B.Events.Drain();
                if (B.Swing is { } sw)
                {
                    ChainedTicks++;
                    if (sw.Dropped && sw.StartAt != droppedAt) { Dropped++; droppedAt = sw.StartAt; }
                }
                if (p.DashT > 0 && !dashing) Dashes++;
                dashing = p.DashT > 0;
                if (i % 30 == 0) Trace.Append($"{B.Time:0.000}:{p.X:0.0000},{p.Z:0.0000};");
                // (the fight is her feet's, not her life's: she is kept whole, so no branch turns on her health)
                p.Hp = B.MaxHp;
                Kit.Stand(Dt, null, () => pack);
            }
        }
    }

    /// <summary>The fight, for the feet-on-cuts tests.</summary>
    internal static Fight FightFor(double seconds, int foes = 2, bool dummy = false, bool unchained = false) => new(seconds, foes, dummy, unchained);

    [Fact]
    public void In_a_campaign_fight_she_plants_and_swings_and_the_clock_leaves_her_be()
    {
        var f = new Fight(30);
        var m = Pilot.Meter(f.B);
        string saw = $"{m}; stand charges {f.Kit.StandCharges}; landed {f.Landed:0.0} s of cuts; longest still {f.LongestStill:0.00} s";
        Assert.True(m.InReach > 20, "the pack was not in her reach: " + saw);
        Assert.True(f.Landed > 10, "her cuts did not land: " + saw);
        Assert.True(m.Plants >= 4, "she did not plant and step: " + saw);
        Assert.True(m.StoodShare >= 0.5, "she stood under half the fight: " + saw);
        Assert.True(Math.Abs(m.NetPer10) < 0.3, "she circles her foe: " + saw);
        Assert.True(f.Kit.StandCharges == 0, "the stand clock charged a fighter whose cuts land: " + saw);
    }

    [Fact]
    public void With_the_feet_off_she_circles_as_she_did()
    {
        bool was = Pilot.StepsAndStands;
        Pilot.StepsAndStands = false;
        try
        {
            var f = new Fight(30);
            var m = Pilot.Meter(f.B);
            // (the meter still reads the campaign's fight: the strafe, a turn and more each ten seconds, never a plant)
            Assert.True(m.InReach > 10, m.ToString());
            Assert.Equal(0, m.Plants);
            Assert.True(m.StoodShare < 0.2 && m.TurnsPer10 > 1, m.ToString());
        }
        finally { Pilot.StepsAndStands = was; }
    }

    [Fact]
    public void Each_step_carries_her_clear_of_where_she_planted()
    {
        var f = new Fight(30);
        var stepped = f.Plants.Where(pl => pl.StepAt != null && pl.StepAt + Pilot.StepMax * 2 < f.B.Time).ToList();
        Assert.True(stepped.Count >= 4, $"{stepped.Count} plants ended in a step");
        var shy = stepped.Where(pl => pl.Far < f.Clock.StandMoved).ToList();
        Assert.True(shy.Count == 0, $"{shy.Count} of {stepped.Count} steps left her within {f.Clock.StandMoved} m of her plant after {Pilot.StepMax * 2:0.00} s: "
            + string.Join(", ", shy.Take(6).Select(pl => $"planted at {pl.At:0.00} s, stepped at {pl.StepAt:0.00} s, came {pl.Far:0.00} m")));
        // And a plant is never stood past the clock's own time (the step comes first).
        Assert.True(f.LongestStill < Pilot.PlantMost + 0.1, $"she stood {f.LongestStill:0.00} s in one plant");
    }
}

/// <summary>(M3 MR 3, the feet) Under a chained grip the stand clock's step goes in a cut's dead part (Pilot.StepsOnCuts): from
/// its cancel beat to its period's end, never before its contact; the hands' dodges are never held; an unchained grip's
/// steps are what they were.</summary>
[Collection("PilotFeet")]
public sealed class FeetOnCutsTests
{
    [Fact]
    public void A_held_chained_grip_steps_in_the_cuts_dead_part_and_drops_nothing()
    {
        var f = FighterFeetTests.FightFor(60, dummy: true);
        string saw = $"{f.Steps.Count} steps, {f.Dropped} cuts dropped, {f.Dashes} dashes, {f.ChainedTicks} ticks chained; stand charges {f.Kit.StandCharges}; "
            + string.Join(" ", f.Steps.Take(8).Select(s => $"[{s.At:0.000} in {s.Start:0.000}/{s.Cancel:0.000}/{s.End:0.000}]"));
        Assert.True(f.ChainedTicks > 60 * 60 / 2, "her grip was not chained most of the fight: " + saw);
        var chained = f.Steps.Where(s => !double.IsNaN(s.Cancel)).ToList();
        Assert.True(chained.Count >= 8, "too few steps under a live chain: " + saw);
        // (a step due with the cut before its cancel beat is held to it unless the wait would leave the clock under
        // StepHoldLeft s: the opening cut, begun with the clock already counting, may be one)
        var late = chained.Where(s => s.At >= s.End).ToList();
        Assert.True(late.Count == 0, $"{late.Count} steps past their cut's period: " + saw);
        var early = chained.Where(s => s.At < s.Cancel - 1e-9).ToList();
        Assert.True(early.All(s => s.Stood + (s.Cancel - s.At) > f.Clock.StandFor - Pilot.StepHoldLeft), "a step before its cut's cancel beat that could have waited: " + saw);
        var off = early.Where(s => s.At > 1).ToList();
        Assert.True(off.Count == 0, $"{off.Count} of {chained.Count} chained steps outside the cut's dead part: " + string.Join(" ", off.Take(6).Select(s => $"[{s.At:0.000} in {s.Start:0.000}/{s.Cancel:0.000}/{s.End:0.000}]")) + "; " + saw);
        Assert.Equal(0, f.Dashes);
        Assert.True(f.Dropped == 0, "cuts dropped: " + saw);
        Assert.True(f.Kit.StandCharges == 0, "the clock charged her: " + saw);
    }

    [Fact]
    public void A_danger_dodge_is_not_held_for_a_pending_cut()
    {
        var j = MapSim.Survivor("warden", 30, 2, 5);
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        b.StoryStand = WorldTiers.Get(WorldTiers.Default).Stand!;
        var foe = b.SpawnEnemy("footpad", 1.8, 0)!;
        foe.Hp = foe.MaxHp = 1e7;
        foe.AttackT = foe.RangedT = 999;
        // Her chain started, a cut before its contact beat: a champion close by winds up its lunge.
        bool armed = false;
        for (int i = 0; i < 600 && !armed; i++)
        {
            var (mx, mz) = Pilot.Steer(b);
            Pilot.Act(b, j, mx, mz, drinks: false);
            b.Tick(1 / 60.0, mx, mz);
            b.Events.Drain();
            foe.AttackT = foe.RangedT = 999;
            armed = b.Swing is { } c && b.Time < c.ContactAt && c.StartAt > 0.5 && b.Player.DashCharges > 0 && b.Player.DashT <= 0;
        }
        Assert.True(armed, "no chained cut before its contact beat in 10 s");
        var cut = b.Swing!;
        double start = cut.StartAt;
        foe.Elite = true;
        foe.State = EnemyState.Windup;
        foe.StateT = 0;
        var (x, z) = Pilot.Steer(b);
        Pilot.Act(b, j, x, z, drinks: false);
        Assert.True(b.Player.DashT > 0, "the dodge waited for her cut");
        Assert.True(b.Swing is { } c2 && c2.StartAt == start && c2.Dropped, "the dodge did not drop the pending cut (the accepted cost)");
    }

    [Fact]
    public void An_unchained_grip_steps_as_before()
    {
        bool was = Pilot.StepsOnCuts;
        try
        {
            Pilot.StepsOnCuts = false;
            var before = FighterFeetTests.FightFor(30, unchained: true);
            Pilot.StepsOnCuts = true;
            var now = FighterFeetTests.FightFor(30, unchained: true);
            Assert.Equal(0, now.ChainedTicks);
            Assert.True(now.Steps.Count >= 4, $"{now.Steps.Count} steps");
            Assert.Equal(string.Join(" ", before.Steps.Select(s => s.At.ToString("R"))), string.Join(" ", now.Steps.Select(s => s.At.ToString("R"))));
            Assert.Equal(before.Trace.ToString(), now.Trace.ToString());
        }
        finally { Pilot.StepsOnCuts = was; }
    }
}

/// <summary>Pilot.StepsAndStands is a static the feet's tests turn: they run one at a time (the arena's other tests never read it).</summary>
[CollectionDefinition("PilotFeet", DisableParallelization = true)]
public sealed class PilotFeetCollection { }
