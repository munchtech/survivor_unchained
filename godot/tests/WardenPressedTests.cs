using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The Warden's pressed skills (Sim/PressedWarden.cs): Heroic Leap (marked = hit), Shield Charge (the old Bull
/// Rush's run as a skill, its lamps and its Turn), Bladestorm (the two-key Union: hold spins, the second key breaks).
/// Fights with no calling (the Hand's heavy count stays out, but where a test asks for it).</summary>
public sealed class WardenPressedTests(ITestOutputHelper output)
{
    const double Dt = 1 / 60.0;

    static Battle Fight(params (string Id, int Rank)[] skills)
    {
        var b = BattleTests.Arena(21, skills);
        b.Calling = null;
        foreach (var w in b.Weapons) w.Timer = 0;
        return b;
    }

    /// <summary>A creature that stands and takes it, pinned where it is put (Pin) until let go.</summary>
    static Enemy Dummy(Battle b, double x, double z, string def = "footpad")
    {
        var e = b.SpawnEnemy(def, x, z)!;
        e.Hp = e.MaxHp = 1e7;
        e.AttackT = e.RangedT = 999;
        return e;
    }

    static void Pin(Battle b, IList<Enemy> es, IList<(double X, double Z)> at)
    {
        for (int i = 0; i < es.Count; i++) { es[i].X = at[i].X; es[i].Z = at[i].Z; es[i].Vx = es[i].Vz = 0; }
        b.Spatial.Clear();
        foreach (var e in b.Enemies.Items) if (e.Alive && e.State != EnemyState.Dying) b.Spatial.Insert(e.Id, e.X, e.Z);
    }

    /// <summary>Steps, the events kept; each step's own action first (a key held, the dummies pinned).</summary>
    static List<CombatEvent> Run(Battle b, double seconds, Action? each = null, Func<bool>? until = null)
    {
        var evs = new List<CombatEvent>();
        for (double t = 0; t < seconds - 1e-9; t += Dt)
        {
            each?.Invoke();
            b.Tick(Dt, 0, 0);
            evs.AddRange(b.Events.Drain());
            if (until?.Invoke() == true) break;
        }
        return evs;
    }

    /* -------------------------------------------------------- heroic leap -- */

    [Fact]
    public void Heroic_leap_strikes_exactly_what_its_ring_marked()
    {
        var b = Fight(("heroic_leap", 1));
        var w = b.Weapons.Single();
        var p = b.Player;
        double lx = p.X + 6, lz = p.Z;
        // Inside, on the edge either way, and well outside (one by her feet where she took off).
        var offs = new (double X, double Z)[] { (0, 0), (2, 0), (0, -3), (-2.4, 1.6), (3.3, 0), (0, 3.9), (4.6, 0), (0, -6), (-6, 0), (5, 5) };
        var at = offs.Select(o => (lx + o.X, lz + o.Z)).ToList();
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        Run(b, 1.5, () => Pin(b, es, at));
        b.Events.Drain();
        Assert.True(b.PressSkill(w.Slot, lx, lz));
        var take = b.Events.Drain().OfType<Ev.Leap>().Single();
        Assert.Equal(LeapPhase.Takeoff, take.Phase);
        Assert.Equal(lx, take.X1, 3);
        Assert.Equal(3.5, take.Radius, 3);
        Assert.True(p.Iframes >= take.Dur - 1e-9);
        // Untouchable in the air.
        var hp0 = es.Select(e => e.Hp).ToList();
        var evs = Run(b, 1.0, () => Pin(b, es, at), () => b.Player.Leap == null);
        var land = evs.OfType<Ev.Leap>().Single(e => e.Phase == LeapPhase.Land);
        Assert.Equal((take.X1, take.Z1, take.Radius), (land.X1, land.Z1, land.Radius));
        // Marked = hit: the ring told at takeoff is the set struck at landing, both ways.
        // (Measured where they were pinned as it landed: the blow then throws them.)
        var inRing = es.Where((e, i) => Math.Sqrt((at[i].Item1 - land.X1) * (at[i].Item1 - land.X1) + (at[i].Item2 - land.Z1) * (at[i].Item2 - land.Z1)) <= land.Radius + e.Radius).Select(e => e.Id).ToHashSet();
        Assert.Equal(inRing.OrderBy(x => x), b.LeapStruck.OrderBy(x => x));
        Assert.Equal(inRing.Count, land.Hit);
        for (int i = 0; i < es.Count; i++)
            Assert.Equal(inRing.Contains(es[i].Id), es[i].Hp < hp0[i]);
        Assert.InRange(inRing.Count, 4, 7);
        // Knocked down (stunned) where it stood.
        Assert.All(es.Where(e => inRing.Contains(e.Id)), e => Assert.True(e.Status.Has(StatusKind.Stun)));
        Assert.True(w.Timer > 7, $"timer {w.Timer}");
        Assert.Contains(evs, e => e is Ev.Explosion { Art: "heroic_leap_heave" });
    }

    [Fact]
    public void Heroic_leap_clamps_its_jump_and_stops_short_of_a_wall()
    {
        var b = Fight(("heroic_leap", 1));
        var w = b.Weapons.Single();
        var p = b.Player;
        double x0 = p.X, z0 = p.Z;
        Assert.True(b.PressSkill(w.Slot, x0 + 1, z0));
        Assert.Equal(3, p.Leap!.X1 - x0, 3);
        Run(b, 1, until: () => p.Leap == null);
        w.Timer = 0;
        double x1 = p.X, z1 = p.Z;
        Assert.True(b.PressSkill(w.Slot, x1, z1 + 30));
        Assert.Equal(9, p.Leap!.Z1 - z1, 3);
        Run(b, 1, until: () => p.Leap == null);
        // A wall across the line: she comes down on the near side of it.
        w.Timer = 0;
        double x2 = p.X, z2 = p.Z;
        b.Collision.AddCircle(x2 + 5, z2, 1.0);
        Assert.True(b.PressSkill(w.Slot, x2 + 8, z2));
        Assert.True(p.Leap!.X1 < x2 + 5 - 1.0, $"landed at {p.Leap.X1 - x2:0.00}");
        Assert.True(p.Leap.X1 > x2 + 2.5);
    }

    /* ------------------------------------------------------ shield charge -- */

    [Fact]
    public void Shield_charge_runs_its_line_strikes_what_is_in_the_way_and_gives_a_barrier()
    {
        var b = Fight(("shield_charge", 1));
        var w = b.Weapons.Single();
        var p = b.Player;
        double x0 = p.X, z0 = p.Z;
        var foe = Dummy(b, x0 + 3, z0 + 0.3);
        var aside = Dummy(b, x0 + 3, z0 + 6);
        Run(b, 1, () => Pin(b, [foe, aside], [(x0 + 3, z0 + 0.3), (x0 + 3, z0 + 6)]));
        b.Events.Drain();
        Assert.True(b.PressSkill(w.Slot, x0 + 20, z0));
        Assert.Equal(0.15 * b.MaxHp, p.Shield, 1);
        var evs = Run(b, 0.6);
        Assert.Contains(evs, e => e is Ev.Charge { Phase: ChargePhase.Start });
        Assert.Contains(evs, e => e is Ev.Charge { Phase: ChargePhase.Impact } im && im.Target == foe.Id);
        Assert.Contains(evs, e => e is Ev.Charge { Phase: ChargePhase.End });
        Assert.True(foe.Hp < foe.MaxHp);
        Assert.Equal(aside.MaxHp, aside.Hp);
        Assert.InRange(p.X - x0, 7.5, 9);
        Assert.Null(b.Art.Rush);
        Assert.True(w.Timer > 6, $"timer {w.Timer}");
        Assert.False(b.PressSkill(w.Slot, x0, z0));
    }

    [Fact]
    public void A_champion_stops_the_charge_and_is_stunned()
    {
        var b = Fight(("shield_charge", 1));
        var w = b.Weapons.Single();
        var p = b.Player;
        double x0 = p.X, z0 = p.Z;
        var champ = Dummy(b, x0 + 4, z0);
        champ.Elite = true;
        Run(b, 1, () => Pin(b, [champ], [(x0 + 4, z0)]));
        b.Events.Drain();
        Assert.True(b.PressSkill(w.Slot, x0 + 20, z0));
        var evs = Run(b, 0.6);
        Assert.Contains(evs, e => e is Ev.Charge { Phase: ChargePhase.Stop } st && st.Target == champ.Id);
        Assert.True(p.X - x0 < 4.5, $"ran {p.X - x0:0.0}");
        Assert.True(champ.Status.Has(StatusKind.Stun));
    }

    [Fact]
    public void Shield_charge_lamps_and_its_turn_pile_driver()
    {
        var b = Fight(("shield_charge", 8));
        b.Lamps = new LampLoadout();
        b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "shield_charge.iron_hide", Args = new Dictionary<string, double>() });
        b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "shield_charge.unbroken", Args = new Dictionary<string, double>() });
        b.Evolve("shield_charge", "pile_driver", chest: true);
        var w = b.Weapons.Single();
        var p = b.Player;
        double x0 = p.X, z0 = p.Z;
        var inWay = Dummy(b, x0 + 3, z0);
        var atEnd = Dummy(b, x0 + 9.5, z0 + 1.5);
        Run(b, 1, () => Pin(b, [inWay, atEnd], [(x0 + 3, z0), (x0 + 9.5, z0 + 1.5)]));
        b.Events.Drain();
        w.Timer = 0;
        Assert.True(b.PressSkill(w.Slot, x0 + 20, z0));
        Assert.Equal(0.25 * b.MaxHp, p.Shield, 1);
        var evs = Run(b, 0.6);
        Assert.True(p.Shield > 0.25 * b.MaxHp, "unbroken: a thing struck adds to the barrier");
        Assert.Contains(evs, e => e is Ev.Charge { Phase: ChargePhase.Slam });
        Assert.True(atEnd.Hp < atEnd.MaxHp);
        Assert.True(atEnd.Status.Has(StatusKind.Stun));
    }

    /* --------------------------------------------------------- bladestorm -- */

    /// <summary>Sunder on slot 1, the Cleaver on slot 2, then the union granted: its spin key is the Cleaver's.</summary>
    static (Battle B, WeaponInst W) Storm(bool hand = false)
    {
        var b = Fight(("sunder", 8), ("cleaver", 8));
        if (hand) b.Calling = "warden";
        var w = b.GrantUnion("bladestorm")!;
        w.Timer = 0;
        return (b, w);
    }

    [Fact]
    public void Bladestorm_holds_both_slots_the_cleavers_key_spins_and_the_sunders_breaks()
    {
        var (b, w) = Storm();
        Assert.Equal(["bladestorm"], b.Weapons.Select(x => x.Id).ToArray());
        Assert.Equal(2, b.SlotsUsed);
        Assert.Equal((1, 0), (w.Slot, w.Slot2));
        Assert.Same(w, b.OnSlot(0));
        Assert.Same(w, b.OnSlot(1));
        // The Sunder's key held does not spin it.
        b.HoldSkill(w.Slot2, true);
        Assert.False(w.Held);
        b.HoldSkill(w.Slot2, false);
        b.HoldSkill(w.Slot, true);
        Assert.True(w.Held);
    }

    [Fact]
    public void Bladestorm_held_spins_and_ticks_and_released_ends_with_its_cooldown()
    {
        var (b, w) = Storm();
        var p = b.Player;
        var at = new List<(double, double)> { (p.X + 1.5, p.Z), (p.X - 2.5, p.Z + 1) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        Run(b, 0.5, () => Pin(b, es, at));
        b.Events.Drain();
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
        var evs = b.Events.Drain().ToList();
        evs.AddRange(Run(b, 1.2, () => { b.HoldSkill(w.Slot, true); Pin(b, es, at); }));
        Assert.Contains(evs, e => e is Ev.Spin { Phase: SpinPhase.Start });
        int ticks = evs.Count(e => e is Ev.Spin { Phase: SpinPhase.Tick });
        Assert.InRange(ticks, 4, 5);
        Assert.All(es, e => Assert.True(e.Hp < e.MaxHp));
        Assert.Equal(0, w.Timer);
        b.HoldSkill(w.Slot, false);
        var end = Run(b, Dt * 2);
        Assert.Contains(end, e => e is Ev.Spin { Phase: SpinPhase.End });
        Assert.False(w.Channeling);
        Assert.True(w.Timer > 5.5, $"timer {w.Timer}");
    }

    [Fact]
    public void Bladestorm_moves_at_a_slower_pace_while_it_spins()
    {
        var (b, w) = Storm();
        var p = b.Player;
        double x0 = p.X;
        for (int i = 0; i < 60; i++) { b.Tick(Dt, 1, 0); b.Events.Drain(); }
        double free = p.Vx;
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
        for (int i = 0; i < 60; i++) { b.HoldSkill(w.Slot, true); b.Tick(Dt, 1, 0); b.Events.Drain(); }
        Assert.Equal(0.85, p.Vx / free, 2);
        Assert.True(p.X > x0 + 3);
    }

    [Fact]
    public void Bladestorm_heavy_ticks_throw_lines_and_the_break_splits_every_one()
    {
        var (b, w) = Storm();
        var p = b.Player;
        p.Facing = Math.PI / 2; // along +x
        var at = new List<(double, double)> { (p.X + 1.5, p.Z), (p.X + 6, p.Z), (p.X - 9, p.Z) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        Run(b, 0.5, () => Pin(b, es, at));
        p.Facing = Math.PI / 2;
        b.Events.Drain();
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
        var evs = Run(b, 2.5, () => { b.HoldSkill(w.Slot, true); Pin(b, es, at); });
        var thrown = evs.OfType<Ev.SpinLine>().Where(e => e.Phase == SpinLinePhase.Thrown).ToList();
        Assert.Equal(2, thrown.Count);
        Assert.Equal(evs.OfType<Ev.Spin>().Count(e => e.Phase == SpinPhase.Tick && e.Heavy), thrown.Count);
        // 7 m by 1.2 m, grown with rank as Sunder's line is (rank 8: x1.28).
        double k = Firing.AreaOf(b, w, 1);
        Assert.All(thrown, l => { Assert.Equal(7 * k, Math.Sqrt((l.X1 - l.X0) * (l.X1 - l.X0) + (l.Z1 - l.Z0) * (l.Z1 - l.Z0)), 2); Assert.Equal(1.2 * k, l.Width, 2); });
        Assert.Equal(2, w.Lines.Count);
        // The far one on the lines is struck only by the split; the one behind her never.
        double farHp = es[1].Hp, behindHp = es[2].Hp;
        Assert.Equal(es[1].MaxHp, farHp);
        Assert.True(b.PressSkill(w.Slot2, p.X, p.Z));
        var brk = b.Events.Drain().ToList();
        Assert.Single(brk, e => e is Ev.Spin { Phase: SpinPhase.Break });
        var split = brk.OfType<Ev.SpinLine>().Where(e => e.Phase == SpinLinePhase.Split).Select(e => e.Id).ToList();
        Assert.Equal(thrown.Select(e => e.Id), split);
        Assert.True(es[1].Hp < farHp);
        Assert.Equal(es[2].MaxHp, es[2].Hp);
        Assert.Empty(w.Lines);
        Assert.False(w.Channeling);
        Assert.True(w.Timer > 5.5);
        Assert.True(es[0].Status.Has(StatusKind.Stun));
        // Broken once: the key breaks nothing more (it swings Sunder now).
        b.PressSkill(w.Slot2, p.X, p.Z);
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.Spin { Phase: SpinPhase.Break });
    }

    [Fact]
    public void Bladestorm_breaks_a_breath_after_the_spin_and_unbroken_its_lines_fade()
    {
        var (b, w) = Storm();
        var p = b.Player;
        // Ready, no storm: the Sunder's key breaks nothing (with nothing in reach it doesn't even swing).
        b.PressSkill(w.Slot2, p.X + 2, p.Z);
        Assert.False(w.Channeling);
        Assert.Equal(0, w.Timer);
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.Spin);
        // Spun and let go: within 1 s it still breaks.
        b.HoldSkill(w.Slot, true);
        b.PressSkill(w.Slot, p.X + 2, p.Z);
        Run(b, 1.3, () => b.HoldSkill(w.Slot, true));
        b.HoldSkill(w.Slot, false);
        Run(b, 0.8);
        Assert.False(w.Channeling);
        Assert.Single(w.Lines);
        Assert.True(b.PressSkill(w.Slot2, p.X, p.Z));
        Assert.Contains(b.Events.Drain(), e => e is Ev.SpinLine { Phase: SpinLinePhase.Split });
        // Again, let go and left: the line fades, dealing nothing, and the key is dead.
        w.Timer = 0;
        b.HoldSkill(w.Slot, true);
        b.PressSkill(w.Slot, p.X + 2, p.Z);
        Run(b, 1.3, () => b.HoldSkill(w.Slot, true));
        b.HoldSkill(w.Slot, false);
        var evs = Run(b, 1.1);
        Assert.Contains(evs, e => e is Ev.SpinLine { Phase: SpinLinePhase.Faded });
        Assert.Empty(w.Lines);
        b.PressSkill(w.Slot2, p.X, p.Z);
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.Spin { Phase: SpinPhase.Break });
    }

    [Fact]
    public void Bladestorm_with_the_hand_is_heavy_on_its_count_and_holds_six_lines_at_most()
    {
        var (b, w) = Storm(hand: true);
        b.HoldSkill(w.Slot, true);
        b.PressSkill(w.Slot, b.Player.X + 2, b.Player.Z);
        var evs = Run(b, 4.2, () => b.HoldSkill(w.Slot, true));
        int heavy = evs.Count(e => e is Ev.Spin { Phase: SpinPhase.Tick, Heavy: true });
        Assert.True(heavy >= 3, $"{heavy} heavy ticks");
        Assert.True(w.Lines.Count <= 6);
        Assert.Contains(evs, e => e is Ev.Spin { Phase: SpinPhase.End });
    }

    [Fact]
    public void Bladestorm_sunders_key_out_of_a_storm_swings_sunder_on_its_own_cooldown_and_repeats_held()
    {
        var (b, w) = Storm();
        var p = b.Player;
        p.Facing = Math.PI / 2;
        var at = new List<(double, double)> { (p.X + 1.5, p.Z) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        Run(b, 0.2, () => Pin(b, es, at));
        b.Events.Drain();
        b.HoldSkill(w.Slot2, true);
        Assert.True(b.PressSkill(w.Slot2, p.X + 2, p.Z));
        var evs = b.Events.Drain().ToList();
        evs.AddRange(Run(b, 5.0, () => { b.HoldSkill(w.Slot2, true); Pin(b, es, at); }));
        var h = w.Half!;
        Assert.Equal("sunder", h.Id);
        Assert.Equal(w.Rank, h.Rank);
        // Pressed at 0, then held: 1.6, 3.2, 4.8; its fourth is its own heavy one, with the line.
        Assert.Equal(4, h.OwnBlows);
        Assert.Equal(4 * Firing.CountOf(b, h, 1), evs.Count(e => e is Ev.Slash));
        Assert.DoesNotContain(evs, e => e is Ev.Spin);
        Assert.False(w.Channeling);
        Assert.Equal(0, w.Timer);
        Assert.True(b.DamageBy.GetValueOrDefault("sunder") > 0);
        Assert.Equal(["bladestorm"], b.Weapons.Select(x => x.Id).ToArray());
    }

    [Fact]
    public void Bladestorm_a_grip_held_into_the_storm_never_breaks_it_and_a_fresh_press_does()
    {
        var (b, w) = Storm();
        var p = b.Player;
        var at = new List<(double, double)> { (p.X + 1.5, p.Z) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        Run(b, 0.2, () => Pin(b, es, at));
        // Sunder's key held first (it swings), then the storm.
        b.HoldSkill(w.Slot2, true);
        b.PressSkill(w.Slot2, p.X + 2, p.Z);
        Run(b, 0.3, () => { b.HoldSkill(w.Slot2, true); Pin(b, es, at); });
        int swung = w.Half!.OwnBlows;
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
        // Held on into it, and pressed again each step as a buffer would: no break, no Sunder swing, still spinning.
        var evs = Run(b, 2.0, () => { b.HoldSkill(w.Slot, true); b.HoldSkill(w.Slot2, true); b.PressSkill(w.Slot2, p.X, p.Z); Pin(b, es, at); });
        Assert.True(w.Channeling);
        Assert.DoesNotContain(evs, e => e is Ev.Spin { Phase: SpinPhase.Break });
        Assert.Equal(swung, w.Half.OwnBlows);
        // Let go and pressed fresh: it breaks.
        b.HoldSkill(w.Slot2, false);
        Run(b, Dt, () => { b.HoldSkill(w.Slot, true); Pin(b, es, at); });
        b.HoldSkill(w.Slot2, true);
        Assert.True(b.PressSkill(w.Slot2, p.X, p.Z));
        Assert.Contains(b.Events.Drain(), e => e is Ev.Spin { Phase: SpinPhase.Break });
        Assert.False(w.Channeling);
    }

    [Fact]
    public void Bladestorm_break_grows_with_the_storm_spent_from_half_a_second_to_its_cap()
    {
        Ev.Spin BreakAfter(double seconds)
        {
            var (b, w) = Storm();
            var p = b.Player;
            b.HoldSkill(w.Slot, true);
            Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
            Run(b, seconds, () => b.HoldSkill(w.Slot, true), () => !w.Channeling);
            b.Events.Drain();
            Assert.True(b.PressSkill(w.Slot2, p.X, p.Z));
            return b.Events.Drain().OfType<Ev.Spin>().Single(e => e.Phase == SpinPhase.Break);
        }
        var (b0, w0) = Storm();
        double r = Firing.AreaOf(b0, w0, 4);
        Assert.Equal(3, w0.ChannelMax);
        var quick = BreakAfter(0.3);
        var mid = BreakAfter(1.75);
        var full = BreakAfter(3.5);
        Assert.Equal(1, quick.Grow, 6);
        Assert.Equal(1.3, mid.Grow, 1);
        Assert.Equal(1.6, full.Grow, 6);
        Assert.Equal(r, quick.Radius, 6);
        Assert.Equal(r * 1.6, full.Radius, 6);
    }

    /* ----------------------------------------------------------- iron vow -- */

    [Fact]
    public void Iron_vow_plants_then_braces_halving_blows_and_storing_a_fifth()
    {
        var b = Fight(("iron_vow", 1));
        var w = b.Weapons.Single(x => x.Id == "iron_vow");
        w.CastSet = CastMode.Press;
        var p = b.Player;
        Assert.Equal(CastMode.Press, w.Cast);
        Assert.Equal(WeaponBehavior.Brace, w.Behavior);
        Run(b, 0.2);
        p.Hp = 1e6;
        double Blow() { p.Iframes = 0; double h0 = p.Hp; b.HurtPlayer(100, School.Physical, "test", null); return h0 - p.Hp; }
        double free = Blow();
        Assert.True(free > 0);
        b.Events.Drain();
        Assert.True(b.PressSkill(w.Slot, p.X, p.Z));
        Assert.Contains(b.Events.Drain(), e => e is Ev.Brace { Phase: BracePhase.Start, Radius: > 4.9 });
        Assert.True(w.Timer > 9.5);
        // The plant: her walk held for 0.3 s, then she walks while it braces.
        double x0 = p.X;
        for (int i = 0; i < 15; i++) { b.Tick(Dt, 1, 0); b.Events.Drain(); }
        Assert.Equal(x0, p.X, 6);
        for (int i = 0; i < 30; i++) { b.Tick(Dt, 1, 0); b.Events.Drain(); }
        Assert.True(p.X > x0 + 0.5);
        Assert.True(b.Bracing);
        double braced = Blow();
        Assert.Equal(free * 0.5, braced, 6);
        Assert.Equal(free * 0.2, b.VowStored, 6);
        Assert.Contains(b.Events.Drain(), e => e is Ev.Brace { Phase: BracePhase.Store });
        // Store events are throttled: a second blow at once stores but says nothing.
        Blow();
        Assert.Equal(free * 0.4, b.VowStored, 6);
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.Brace);
    }

    [Fact]
    public void Iron_vow_burst_strikes_exactly_what_its_ring_marked_for_its_store_times_three()
    {
        var b = Fight(("iron_vow", 1));
        var w = b.Weapons.Single(x => x.Id == "iron_vow");
        w.CastSet = CastMode.Press;
        var p = b.Player;
        var at = new List<(double, double)> { (p.X + 1, p.Z), (p.X, p.Z - 4.5), (p.X - 3, p.Z + 3), (p.X + 6, p.Z), (p.X, p.Z + 8) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        Run(b, 0.2, () => Pin(b, es, at));
        p.Hp = 1e6;
        b.Events.Drain();
        Assert.True(b.PressSkill(w.Slot, p.X, p.Z));
        Run(b, 1.0, () => Pin(b, es, at));
        p.Iframes = 0;
        b.HurtPlayer(200, School.Physical, "test", null);
        double stored = b.VowStored;
        Assert.True(stored > 0);
        var hp0 = es.Select(e => e.Hp).ToList();
        var evs = Run(b, 1.5, () => Pin(b, es, at), () => !b.Bracing);
        var burst = evs.OfType<Ev.Brace>().Single(e => e.Phase == BracePhase.Burst);
        Assert.Equal(stored, burst.Stored, 6);
        double r = burst.Radius;
        Assert.Equal(Firing.AreaOf(b, w, 5), r, 6);
        var inside = es.Where(e => Math.Sqrt((e.X - burst.X) * (e.X - burst.X) + (e.Z - burst.Z) * (e.Z - burst.Z)) <= r).Select(e => e.Id).ToHashSet();
        Assert.Equal(3, inside.Count);
        Assert.Equal(inside, b.VowStruck.ToHashSet());
        Assert.Equal(inside.Count, burst.Hit);
        for (int i = 0; i < es.Count; i++)
        {
            if (inside.Contains(es[i].Id)) { Assert.True(es[i].Hp < hp0[i]); Assert.True(es[i].Status.Has(StatusKind.Stun)); }
            else Assert.Equal(hp0[i], es[i].Hp);
        }
        double dealt = hp0[0] - es[0].Hp;
        Assert.InRange(dealt, (w.Damage + stored * 3) * 0.99, (w.Damage + stored * 3) * 2.01);
        output.WriteLine($"stored {stored:0.0}, burst {dealt:0.0} on one (base {w.Damage:0.0})");
    }

    /// <summary>The first DPS check (the P7 brief): per target in the radius, Bladestorm while it spins (a 3 s spin and
    /// its break) against Cleaver and Sunder together on one target, the same rank, no Hand.</summary>
    [Fact]
    public void Bladestorm_out_damages_cleaver_and_sunder_by_a_third_to_a_half_per_target_while_it_spins()
    {
        double offLine = 0;
        double PartsDps()
        {
            var b = Fight(("cleaver", 8), ("sunder", 8));
            var p = b.Player;
            var at = new List<(double, double)> { (p.X + 1.5, p.Z) };
            var e = Dummy(b, p.X + 1.5, p.Z);
            Run(b, 64, () => Pin(b, [e], at));
            return (e.MaxHp - e.Hp) / 64;
        }
        (double Spin, double Cycle) StormDps()
        {
            var (b, w) = Storm();
            var p = b.Player;
            p.Facing = Math.PI / 2;
            // One on the lines (ahead, along her facing), one beside her, off them.
            var at = new List<(double, double)> { (p.X + 1.5, p.Z), (p.X, p.Z + 1.8) };
            var e = Dummy(b, p.X + 1.5, p.Z);
            var off = Dummy(b, p.X, p.Z + 1.8);
            Run(b, 0.2, () => Pin(b, [e, off], at));
            double hp0 = e.Hp, off0 = off.Hp;
            int spins = 0;
            for (; spins < 6; spins++)
            {
                w.Timer = 0;
                b.HoldSkill(w.Slot, true);
                Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
                Run(b, 3.1, () => { b.HoldSkill(w.Slot, true); Pin(b, [e, off], at); }, () => !w.Channeling);
                b.HoldSkill(w.Slot, false);
                Assert.True(b.PressSkill(w.Slot2, p.X, p.Z));
                b.Events.Drain();
            }
            double spin = (hp0 - e.Hp) / (3.0 * spins);
            offLine = (off0 - off.Hp) / (3.0 * spins);
            return (spin, spin * 3 / (3 + w.Timer));
        }
        double parts = PartsDps();
        var (storm, cycle) = StormDps();
        output.WriteLine($"cleaver+sunder {parts:0.0}/s on one target; bladestorm {storm:0.0}/s while it spins on its lines (x{storm / parts:0.00}), {offLine:0.0}/s off them (x{offLine / parts:0.00}), {cycle:0.0}/s over spin+cooldown (x{cycle / parts:0.00})");
        // Per target in the radius (the ticks and the break; the brief's measure): a third to a half more. A target on
        // the lines takes their splits on top (about twice the parts', as Sunder's own line is counted in theirs).
        Assert.InRange(offLine / parts, 1.3, 1.5);
        Assert.True(storm > offLine * 1.3);
    }
}
