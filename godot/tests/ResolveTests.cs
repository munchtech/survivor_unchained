using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The campaign's press path (ARPG.md 3.1-3.3, M3): Resolve (Sim/Resolve.cs), the press records' holds, aims,
/// costs, waits and poses, the kindled keys, Bladestorm on Resolve; and the arena left as it was.</summary>
public sealed class ResolveTests
{
    const double Dt = 1 / 60.0;
    /// <summary>Long enough for a press's blow to land on its clip's contact (M3, Sim/Contact.cs: at most 0.07 s today).</summary>
    const double Land = 0.12;

    /// <summary>A campaign fight, the warden's calling (Resolve on), every skill ready.</summary>
    static Battle Campaign(string calling = "warden", params (string Id, int Rank)[] skills)
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = skills.ToList(), Ability = AbilityKind.ShieldBash,
        });
        b.Calling = calling;
        foreach (var w in b.Weapons) w.Timer = 0;
        return b;
    }

    static Battle Warden(params (string Id, int Rank)[] skills) => Campaign("warden", skills);

    static Enemy Dummy(Battle b, double x, double z, bool hits = false)
    {
        var e = b.SpawnEnemy("footpad", x, z)!;
        e.Hp = e.MaxHp = 1e7;
        if (!hits) e.AttackT = e.RangedT = 999;
        b.Spatial.Clear();
        foreach (var o in b.Enemies.Items) if (o.Alive && o.State != EnemyState.Dying) b.Spatial.Insert(o.Id, o.X, o.Z);
        return e;
    }

    static void Pin(Battle b, IList<Enemy> es, IList<(double X, double Z)> at)
    {
        for (int i = 0; i < es.Count; i++) { es[i].X = at[i].X; es[i].Z = at[i].Z; es[i].Vx = es[i].Vz = 0; }
        b.Spatial.Clear();
        foreach (var e in b.Enemies.Items) if (e.Alive && e.State != EnemyState.Dying) b.Spatial.Insert(e.Id, e.X, e.Z);
    }

    static List<CombatEvent> Run(Battle b, double seconds, Action? each = null, Func<bool>? until = null, double mx = 0, double mz = 0)
    {
        var evs = new List<CombatEvent>();
        for (double t = 0; t < seconds - 1e-9; t += Dt)
        {
            each?.Invoke();
            b.Tick(Dt, mx, mz);
            evs.AddRange(b.Events.Drain());
            if (until?.Invoke() == true) break;
        }
        return evs;
    }

    /* ------------------------------------------------------------ resolve -- */

    [Fact]
    public void Resolve_fills_on_landed_blows_and_not_on_swings_at_air()
    {
        var b = Warden(("sunder", 1));
        var w = b.Weapons.Single();
        Assert.True(b.Resolve.On);
        Assert.True(w.Hold);
        var at = new List<(double, double)> { (2, 0), (2.3, 0.8), (2.3, -0.8) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        Pin(b, es, at);
        // Held at the pack: one swing, three struck: 12 + 3 + 3 a written blow. (sw1) Sunder is chained: the swing is
        // one cut of the blow, its share 0.70 / 1.6 = 0.4375 of that.
        // (M3 MR 3 landed rule) the battle's first cut is whole (the bank starts full): this one weighs 1, so 18 x 1.
        const double cut = 18 * 1.0;
        Assert.Equal(0.70 / 1.6, w.BlowWeight, 12);
        b.HoldSkill(w.Slot, true, 2, 0);
        var evs = Run(b, Land, () => Pin(b, es, at));
        Assert.Equal(cut, b.Resolve.Value, 6);
        Assert.Equal(ResolveReason.Landed, b.Resolve.LastReason);
        Assert.Contains(evs.OfType<Ev.Resolve>(), e => Math.Abs(e.Value - cut) < 1e-6 && e.Reason == ResolveReason.Landed);
        // Swung at the air behind her: nothing landed, nothing gained.
        b.HoldSkill(w.Slot, false);
        w.Timer = 0;
        b.HoldSkill(w.Slot, true, -2, 0);
        var air = Run(b, Land, () => Pin(b, es, at));
        Assert.Single(air.OfType<Ev.Slash>());
        Assert.Equal(cut, b.Resolve.Value, 6);
    }

    [Fact]
    public void Standing_in_a_crowd_without_swinging_fills_nothing_and_taken_never_passes_a_third()
    {
        var b = Warden(("sunder", 1));
        var w = b.Weapons.Single();
        for (int i = 0; i < 6; i++) Dummy(b, Math.Cos(i) * 1.6, Math.Sin(i) * 1.6, hits: true);
        double hp0 = b.Player.Hp;
        bool hurt = false;
        Run(b, 8, () => { if (b.Player.Hp < hp0) hurt = true; b.Player.Hp = b.MaxHp; });
        Assert.True(hurt, "the crowd struck her");
        Assert.Equal(0, b.Resolve.Value, 9);
        // Swinging in it: the taken fill stays within half the landed (a third of the whole), always.
        b.HoldSkill(w.Slot, true, 1.6, 0);
        bool held = true;
        Run(b, 12, () =>
        {
            b.Player.Hp = b.MaxHp;
            held &= b.Resolve.TakenFill <= 0.5 * b.Resolve.LandedFill + 1e-9;
            var near = b.NearestHostile(b.Player.X, b.Player.Z, 5);
            if (near != null) b.AimSkills(near.X, near.Z);
        });
        Assert.True(held);
        Assert.True(b.Resolve.LandedFill > 0);
        Assert.True(b.Resolve.TakenFill > 0, "blows taken filled some");
        Assert.True(b.Resolve.TakenFill <= (b.Resolve.TakenFill + b.Resolve.LandedFill) / 3 + 1e-9);
    }

    [Fact]
    public void Resolve_fades_out_of_a_fight_and_never_in_one()
    {
        var b = Warden(("sunder", 1));
        var e = Dummy(b, 5, 0);
        var at = new List<(double, double)> { (5, 0) };
        b.Resolve.Set(50);
        Run(b, 4, () => Pin(b, [e], at));
        Assert.Equal(50, b.Resolve.Value, 9);
        // Nothing within 12 m, no blow for 3 s: 10 a second.
        at[0] = (40, 0);
        Run(b, 1, () => Pin(b, [e], at));
        Assert.InRange(b.Resolve.Value, 39.5, 40.5);
        Assert.Equal(ResolveReason.Faded, b.Resolve.LastReason);
        Assert.True(b.Resolve.Rate < -9 && b.Resolve.Rate > -11);
        // A blow just given: no fade for 3 s.
        b.FightAt = b.Time;
        double v = b.Resolve.Value;
        Run(b, 2.9, () => Pin(b, [e], at));
        Assert.Equal(v, b.Resolve.Value, 9);
        Run(b, 1, () => Pin(b, [e], at));
        Assert.True(b.Resolve.Value < v - 5);
    }

    [Fact]
    public void A_spender_will_not_fire_short_and_spends_on_firing()
    {
        var b = Warden(("groundbreaker", 1));
        var w = b.Weapons.Single();
        Assert.Equal(CastMode.Press, w.Cast);
        var e = Dummy(b, 6, 0);
        Pin(b, [e], [(6, 0)]);
        b.Resolve.Set(30);
        Assert.False(b.PressSkill(w.Slot, 6, 0));
        Assert.Equal(30, b.Resolve.Value, 9);
        b.Resolve.Set(50);
        Assert.True(b.PressSkill(w.Slot, 6, 0));
        Assert.Equal(10, b.Resolve.Value, 9);
        Assert.Equal(ResolveReason.Spent, b.Resolve.LastReason);
        // Its campaign wait (0.5 s), not its old 5 s cooldown.
        Assert.InRange(w.Timer, 0.08, 0.5 + 1e-9);
        Run(b, Land, () => Pin(b, [e], [(6, 0)]));
        Assert.True(e.Hp < e.MaxHp);
    }

    [Fact]
    public void A_cost_never_blocks_a_calling_without_a_resource_which_keeps_its_cooldown()
    {
        var b = Campaign("reaver", ("cleaver", 1));
        var w = b.Weapons.Single();
        Assert.False(b.Resolve.On);
        Dummy(b, 2, 0);
        Assert.True(b.PressSkill(w.Slot, 2, 0));
        Assert.Equal(Firing.CooldownOf(b, w), w.Timer, 9);
        Assert.True(w.Timer > 1, "a spender with nothing to pay keeps its base cooldown");
    }

    /* --------------------------------------------------------- bladestorm -- */

    static (Battle B, WeaponInst W) Storm()
    {
        // (13 Nov 2026) Bladestorm is the Warden's own skill: Sunder on key 1 (its break), Bladestorm on key 2.
        var b = Warden(("sunder", 8), ("bladestorm", 8));
        var w = b.Weapons.Single(x => x.Id == "bladestorm");
        w.Timer = 0;
        // Within 12 m (in a fight: no fade), out of the spin's reach.
        var e = Dummy(b, 7, 0);
        return (b, w);
    }

    [Fact]
    public void Bladestorm_drains_resolve_while_held_past_its_old_cap_and_ends_at_zero()
    {
        var (b, w) = Storm();
        Assert.NotNull(w.Press);
        b.Resolve.Set(100);
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, 1, 0));
        double drain = w.Press!.Drain!.Value;
        Run(b, 3.3, () => b.HoldSkill(w.Slot, true));
        Assert.True(w.Channeling, "past the arena's 3 s cap it spins on");
        Assert.InRange(b.Resolve.Value, 100 - drain * 3.3 - 1, 100 - drain * 3.3 + 1);
        Run(b, 100 / drain, () => b.HoldSkill(w.Slot, true), () => !w.Channeling);
        Assert.False(w.Channeling);
        Assert.Equal(0, b.Resolve.Value, 9);
        Assert.InRange(b.Resolve.SpentInStorm, 99.9, 100.0001);
        Assert.True(w.Timer <= 0.1, "no cooldown after it");
        // Empty, it will not start.
        b.HoldSkill(w.Slot, false);
        Run(b, 0.2);
        Assert.False(b.PressSkill(w.Slot, 1, 0));
    }

    /// <summary>(13 Nov 2026) With Sunder swapped out of the keys there is no break key: the storm still spins on its key and
    /// ends when Resolve runs dry, as it does for a hand that never presses the break.</summary>
    [Fact]
    public void With_Sunder_swapped_out_the_storm_spins_and_ends_when_Resolve_runs_dry()
    {
        var b = Warden(("bladestorm", 8));
        var w = b.Weapons.Single();
        w.Timer = 0;
        Assert.Equal(-1, b.BreakSlot(w));
        Dummy(b, 7, 0);
        b.Resolve.Set(100);
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, 1, 0));
        double drain = w.Press!.Drain!.Value;
        Run(b, 0.5 * 100 / drain, () => b.HoldSkill(w.Slot, true));
        Assert.True(w.Channeling, "it spins on with no break key");
        Run(b, 0.6 * 100 / drain, () => b.HoldSkill(w.Slot, true), () => !w.Channeling);
        Assert.False(w.Channeling);
        Assert.Equal(0, b.Resolve.Value, 9);
        Assert.InRange(b.Resolve.SpentInStorm, 99.9, 100.0001);
    }

    [Fact]
    public void The_break_grows_with_the_resolve_the_storm_spent()
    {
        var (b, w) = Storm();
        b.Resolve.Set(100);
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, 1, 0));
        Run(b, 1.8, () => b.HoldSkill(w.Slot, true));
        double spent = b.Resolve.SpentInStorm, drain = w.Press!.Drain!.Value;
        Assert.InRange(spent, 1.8 * drain * 0.9, 1.8 * drain * 1.1);
        b.Events.Drain();
        Assert.True(b.PressSkill(b.BreakSlot(w), 0, 0));
        var brk = b.Events.Drain().OfType<Ev.Spin>().Single(e => e.Phase == SpinPhase.Break);
        // (bd-storm) From BreakFloor at none to BreakGrow at BreakSpent: a tapped spin breaks small, a held one great.
        double floor = w.Def.Base.BreakFloor ?? 1, most = w.Def.Base.BreakGrow ?? 1.6, at = w.Def.Base.BreakSpent ?? 100;
        Assert.True(floor < 1, "a tapped storm's break is less than a full blow");
        Assert.Equal(floor + (most - floor) * Math.Min(1, spent / at), brk.Grow, 6);
        Assert.Equal(most, Firing.BreakGrowthSpent(w, 250), 9);
        Assert.Equal(floor, Firing.BreakGrowthSpent(w, 0), 9);
    }

    [Fact]
    public void Out_of_a_storm_sunders_key_swings_sunder_and_builds_resolve()
    {
        var (b, w) = Storm();
        var e = Dummy(b, 2, 0);
        var at = new List<(double, double)> { (2, 0) };
        Pin(b, [e], at);
        Assert.False(Firing.InStorm(b, w));
        Assert.True(b.PressSkill(b.BreakSlot(w), 2, 0));
        Run(b, Land, () => Pin(b, [e], at));
        // (sw1) the half is Sunder's shipped record, chained: one cut builds its weight's part of the blow's 12.
        // (M3 MR 3 landed rule) the battle's first cut is whole (the bank starts full): weight 1, so 12 x 1.
        Assert.Equal(12 * 1.0, b.Resolve.Value, 6);
        Assert.True(e.Hp < e.MaxHp);
    }

    [Fact]
    public void Bladestorm_beside_Sunder_keeps_each_skills_own_lamps()
    {
        var b = Warden(("sunder", 8), ("bladestorm", 8));
        b.SetWickPath("sunder", Enumerable.Range(1, 4).Select(n => $"sunder.stroke.{n}").ToArray());
        var sunder = b.Weapons.First(x => x.Id == "sunder");
        var storm = b.Weapons.First(x => x.Id == "bladestorm");
        Assert.NotNull(sunder.Wick);
        // Bladestorm is no union: no half, and it carries none of Sunder's lamps.
        Assert.Null(Firing.HalfOf(storm));
        Assert.Null(storm.Wick);
    }

    /* ------------------------------------------------------- hold and aim -- */

    [Fact]
    public void A_hold_repeats_while_held_at_the_moving_aim()
    {
        var b = Warden(("sunder", 1));
        var w = b.Weapons.Single();
        var at = new List<(double, double)> { (2, 0), (-2, 0) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        b.HoldSkill(w.Slot, true, 2, 0);
        var first = Run(b, 0.5, () => Pin(b, es, at)).OfType<Ev.Slash>().ToList();
        Assert.Single(first);
        Assert.Equal(0, first[0].Angle, 6);
        var then = Run(b, 3.4, () => { Pin(b, es, at); b.HoldSkill(w.Slot, true, -2, 0); }).OfType<Ev.Slash>().ToList();
        Assert.True(then.Count >= 2, $"{then.Count} swings held");
        Assert.All(then, s => Assert.Equal(Math.PI, Math.Abs(s.Angle), 6));
        // Let go: no more.
        b.HoldSkill(w.Slot, false);
        Assert.Empty(Run(b, 3, () => Pin(b, es, at)).OfType<Ev.Slash>());
    }

    /// <summary>The view mirrors a cut's arc from the sim's side, never a toggle of its own (Ev.Slash.Side). A blow that
    /// lands on its clip's contact takes the CLIP's side: Sunder held as the grip plays sword_heavy, so every cut is
    /// that clip's side, the same on every run; a cut that kills none says so, and names the in-line body it struck.</summary>
    [Fact]
    public void A_held_cut_takes_its_clips_side()
    {
        List<Ev.Slash> Cuts()
        {
            var b = Warden(("sunder", 1));
            var w = b.Weapons.Single();
            var at = new List<(double, double)> { (2, 0), (2.6, 0.4) };
            var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
            b.HoldSkill(w.Slot, true, 2, 0);
            var cuts = Run(b, 6, () => { Pin(b, es, at); b.HoldSkill(w.Slot, true, 2, 0); }).OfType<Ev.Slash>().ToList();
            Assert.Equal(cuts.Count, w.Cuts);
            return cuts;
        }
        var a = Cuts();
        Assert.True(a.Count >= 3, $"{a.Count} cuts held");
        Assert.Equal(-1, HerEvents.Side("sword_heavy"));
        Assert.All(a, s => Assert.Equal(HerEvents.Side("sword_heavy"), s.Side));
        Assert.Equal(a.Select(s => s.Side), Cuts().Select(s => s.Side));
        Assert.All(a, s => Assert.True(s.Held));
        Assert.All(a, s => Assert.Equal(0, s.Killed));
        Assert.All(a, s => Assert.True(s.Struck > 0 && Math.Abs(s.HitX - 2) < 0.5 && Math.Abs(s.HitZ) < 0.5, $"struck {s.Struck} at {s.HitX:0.00},{s.HitZ:0.00}"));
    }

    /// <summary>WeaponInst.NextSide: a clip's side wins while it is set (the Oathblade's grip plays sword_back then
    /// sword_fore: +1, -1, ...); with none (ClipSide 0) the cut alternates from the weapon's count, the first -1.</summary>
    [Fact]
    public void A_cut_with_no_clip_side_alternates_from_the_weapons_count_and_a_clips_side_wins()
    {
        var w = Warden(("sunder", 1)).Weapons.Single();
        Assert.Equal((0, 0), (w.ClipSide, w.Cuts));
        Assert.Equal(new[] { -1, 1, -1, 1 }, Enumerable.Range(0, 4).Select(_ => w.NextSide()));
        foreach (var clip in new[] { "sword_back", "sword_fore", "sword_back" })
        {
            w.ClipSide = HerEvents.Side(clip)!.Value;
            Assert.Equal(HerEvents.Side(clip), w.NextSide());
        }
        Assert.Equal(7, w.Cuts);
        // The clip's side gone: back to the count (7 cuts made, so the eighth is +1, the ninth -1).
        w.ClipSide = 0;
        Assert.Equal(new[] { 1, -1 }, new[] { w.NextSide(), w.NextSide() });
    }

    /// <summary>The first cut of Sunder held at (2, 0) over these bodies (hp each; pinned every step).</summary>
    static (Ev.Slash Cut, List<Enemy> Es) FirstCut(params (double X, double Z, double Hp)[] bodies)
    {
        var b = Warden(("sunder", 1));
        var w = b.Weapons.Single();
        var at = bodies.Select(o => (o.X, o.Z)).ToList();
        var es = bodies.Select(o => { var e = Dummy(b, o.X, o.Z); e.Hp = e.MaxHp = o.Hp; return e; }).ToList();
        b.HoldSkill(w.Slot, true, 2, 0);
        var cuts = Run(b, 0.5, () => Pin(b, es, at)).OfType<Ev.Slash>().ToList();
        return (Assert.Single(cuts), es);
    }

    /// <summary>Ev.Slash.Killed: how many of the struck the cut killed.</summary>
    [Fact]
    public void A_cut_reports_how_many_of_its_struck_it_killed()
    {
        // Two that die to it and one that does not, all on the cut's line.
        var (cut, es) = FirstCut((2, 0, 1), (1.6, 0.2, 1), (2.2, -0.2, 1e7));
        Assert.Equal(3, cut.Struck);
        Assert.True(cut.Killed == 2, $"killed {cut.Killed} of {cut.Struck} struck; bodies (alive, state, hp): {string.Join(" ", es.Select(e => $"{e.Alive}/{e.State}/{e.Hp:0.#}"))}");
        Assert.Equal(new[] { true, true, false }, es.Select(e => e.State == EnemyState.Dying));
        // None dies: none killed.
        var (dry, _) = FirstCut((2, 0, 1e7), (1.6, 0.2, 1e7));
        Assert.Equal((2, 0), (dry.Struck, dry.Killed));
    }

    /// <summary>Ev.Slash.HitX/HitZ: the struck body nearest the cut's line, not the nearest to her; a body within
    /// 0.7 m of her only when no other was struck.</summary>
    [Fact]
    public void A_cut_names_the_struck_body_nearest_its_line()
    {
        // One nearer her and off the line, one farther and on it: the one on the line.
        var (cut, _) = FirstCut((1.0, 0.3, 1e7), (2, 0, 1e7));
        Assert.Equal(2, cut.Struck);
        Assert.Equal((2.0, 0.0), (cut.HitX, cut.HitZ));
        // One against her (0.5 m, dead on the line) and one farther and a little off it: the farther one.
        (cut, _) = FirstCut((0.5, 0, 1e7), (2, 0.3, 1e7));
        Assert.Equal(2, cut.Struck);
        Assert.Equal((2.0, 0.3), (cut.HitX, cut.HitZ));
        // The one against her alone: it is the contact.
        (cut, _) = FirstCut((0.5, 0, 1e7));
        Assert.Equal(1, cut.Struck);
        Assert.Equal((0.5, 0.0), (cut.HitX, cut.HitZ));
    }

    [Fact]
    public void Hover_aim_picks_the_foe_under_the_point_within_reach()
    {
        var b = Warden(("judgement_disc", 1));
        var w = b.Weapons.Single();
        var a = Dummy(b, 6, 0);
        var c = Dummy(b, 0, 6);
        var far = Dummy(b, 0, -30);
        Pin(b, [a, c, far], [(6, 0), (0, 6), (0, -30)]);
        b.AimSkills(0.9, 6.6);
        Assert.Same(c, b.AimFor(w)!.Value.Foe);
        b.AimSkills(5.2, 0.4);
        Assert.Same(a, b.AimFor(w)!.Value.Foe);
        // Nothing within 1.5 m of the point: the point itself.
        b.AimSkills(3, 3);
        var pt = b.AimFor(w)!.Value;
        Assert.Null(pt.Foe);
        Assert.Equal((3.0, 3.0), (pt.X, pt.Z));
        // A foe under the point but out of reach: the point clamped to reach.
        b.AimSkills(0, -30);
        pt = b.AimFor(w)!.Value;
        Assert.Null(pt.Foe);
        Assert.Equal(w.AimRange, Math.Sqrt(pt.X * pt.X + pt.Z * pt.Z), 6);
        // The disc goes to the hovered foe, not the nearest.
        b.AimSkills(0.9, 6.6);
        b.Resolve.Set(100);
        Assert.True(b.PressSkill(w.Slot, 0.9, 6.6));
        var shot = b.Projectiles.Items.Last(p => p.Alive);
        Assert.Equal(c.Id, shot.Target);
    }

    [Fact]
    public void No_press_roots_her_over_three_tenths_of_a_second()
    {
        foreach (var d in Weapons.All.Values)
            if (d.Press is { } r) Assert.True((r.Plant ?? 0) <= Battle.MaxPlant + 1e-9, d.Id);
        var b = Warden(("groundbreaker", 1));
        var w = b.Weapons.Single();
        Dummy(b, 6, 0);
        b.Resolve.Set(100);
        Assert.True(b.PressSkill(w.Slot, 6, 0));
        Assert.Equal(0.3, b.Player.PlantT, 9);
        int still = 0;
        for (int i = 0; i < 60; i++)
        {
            double z = b.Player.Z;
            b.Tick(Dt, 0, 1);
            if (Math.Abs(b.Player.Z - z) < 1e-9) still++;
        }
        Assert.True(still * Dt <= 0.3 + Dt + 1e-9, $"planted {still * Dt:0.00} s");
        Assert.True(b.Player.Z > 1, "she walks after it");
        // While the cast plays she walks at 70%.
        var c = Warden(("cleaver", 1));
        var ce0 = Dummy(c, 0, 2);
        Pin(c, [ce0], [(0, 2)]);
        c.Resolve.Set(100);
        var cw = c.Weapons.Single();
        Assert.True(c.PressSkill(cw.Slot, 0, 2));
        Assert.Equal(0.7, c.Player.CastWalk, 9);
        Assert.Equal(0, c.Player.PlantT, 9);
    }

    [Fact]
    public void Only_sunders_own_heavy_swing_plants_her()
    {
        var b = Warden(("sunder", 1));
        var w = b.Weapons.Single();
        var e = Dummy(b, 2, 0);
        var at = new List<(double, double)> { (2, 0) };
        var plants = new List<double>();
        // (sw1) Sunder is chained: each press is a cut of weight 0.70 / 1.6 = 0.4375 in the every-4th count, the opening
        // one whole (Blows.CountFirstWhole): 1 + 6 x 0.4375 = 3.625 after seven, and the EIGHTH completes the fourth blow
        // (it was the fourth press of four written blows).
        for (int i = 0; i < 8; i++)
        {
            w.Timer = 0;
            Pin(b, [e], at);
            Assert.True(b.PressSkill(w.Slot, 2, 0));
            plants.Add(b.Events.Drain().OfType<Ev.Cast>().Single().Plant);
            Run(b, 0.4, () => Pin(b, [e], at));
        }
        Assert.Equal([0, 0, 0, 0, 0, 0, 0, 0.3], plants);
    }

    /* ------------------------------------------------------------ kindled -- */

    [Fact]
    public void Rebukes_key_readies_a_riposte_for_two_seconds()
    {
        var b = Warden(("rebuke", 1));
        var w = b.Weapons.Single();
        Assert.False(w.Pressed);
        Assert.True(w.Keyed);
        var e = Dummy(b, 1.5, 0);
        Assert.True(b.PressSkill(w.Slot, 0, 0));
        Assert.Equal(b.Time + 2, b.RiposteUntil, 9);
        Assert.False(b.PressSkill(w.Slot, 0, 0));
        int strikes = b.RebukeStrikes, blocks = b.Blocks;
        Assert.Equal(0, b.HurtPlayer(50, School.Physical, "test", e));
        Assert.Equal(1, b.Ripostes);
        Assert.Equal(blocks + 1, b.Blocks);
        Assert.Equal(strikes + 1, b.RebukeStrikes);
        Assert.True(e.Hp < e.MaxHp);
        // Spent: the next blow is not a riposte.
        b.Player.Iframes = 0;
        b.HurtPlayer(50, School.Physical, "test", e);
        Assert.Equal(1, b.Ripostes);
        // Readied and left: gone after 2 s.
        var c = Warden(("rebuke", 1));
        var ce = Dummy(c, 1.5, 0);
        Assert.True(c.PressSkill(c.Weapons.Single().Slot, 0, 0));
        Run(c, 2.05);
        c.Player.Iframes = 0;
        c.HurtPlayer(50, School.Physical, "test", ce);
        Assert.Equal(0, c.Ripostes);
    }

    [Fact]
    public void An_auras_key_flares_it_for_three_seconds_once_per_its_wait()
    {
        var b = Warden(("hallowed_ring", 1));
        var w = b.Weapons.Single();
        Assert.True(w.KindledNow);
        double dmg = w.Damage, area = Firing.AreaOf(b, w, 3);
        Assert.True(b.PressSkill(w.Slot, 0, 0));
        Assert.Equal(dmg * 1.25, w.Damage, 9);
        Assert.Equal(area * 1.3, Firing.AreaOf(b, w, 3), 9);
        Assert.False(b.PressSkill(w.Slot, 0, 0));
        Run(b, 2.9);
        Assert.Equal(1.25, w.AuraMul, 9);
        Run(b, 0.2);
        Assert.Equal(dmg, w.Damage, 9);
        Assert.Equal(area, Firing.AreaOf(b, w, 3), 9);
        Run(b, 5);
        Assert.True(b.PressSkill(w.Slot, 0, 0));
    }

    [Fact]
    public void A_kindled_spender_fires_itself_only_when_full_taking_all_and_its_key_heaves_from_its_cost()
    {
        var b = Warden(("groundbreaker", 1));
        var w = b.Weapons.Single();
        Assert.True(w.SetForm("kindle"));
        Assert.Equal(CastMode.Auto, w.Cast);
        var at = new List<(double, double)> { (6, 0), (6.5, 0.6), (6.5, -0.6) };
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        // Short of its cost: it waits.
        b.Resolve.Set(30);
        Run(b, 1, () => Pin(b, es, at));
        Assert.Equal(30, b.Resolve.Value, 9);
        // Its key: now, with what she has (30 of 40: three quarters as hard), spending it.
        double hp0 = es[0].Hp;
        Assert.True(b.PressSkill(w.Slot, 6, 0));
        Assert.Equal(0, b.Resolve.Value, 9);
        Run(b, Land, () => Pin(b, es, at));
        Assert.True(es[0].Hp < hp0);
        // Under half its cost the key does nothing.
        w.Timer = 0;
        b.Resolve.Set(19);
        Assert.False(b.PressSkill(w.Slot, 6, 0));
        // (M3) Paid but not full, a crowd in range: it waits for her key (it fires itself only when Resolve is full).
        b.Resolve.Set(60);
        Run(b, 1, () => Pin(b, es, at));
        Assert.Equal(60, b.Resolve.Value, 9);
        // Its key from its whole cost: full strength, the cost spent, and it waits only its record's wait (0.5 s), not its
        // kindled cooldown (5 s): the cost is the gate.
        Assert.True(b.PressSkill(w.Slot, 6, 0));
        Assert.Equal(20, b.Resolve.Value, 9);
        Assert.InRange(w.Timer, 0.01, 0.51);
        // Full with a crowd in range: it fires itself, and the heave takes all of it.
        Run(b, 1, () => Pin(b, es, at));
        b.Resolve.Set(100);
        Run(b, 0.5, () => Pin(b, es, at));
        Assert.Equal(0, b.Resolve.Value, 9);
    }

    /* ---------------------------------------------------------- the arena -- */

    [Fact]
    public void Off_the_campaign_an_auto_sunder_still_fires_itself()
    {
        var b = BattleTests.Arena(4, ("sunder", 1));
        b.Calling = "warden";
        var w = b.Weapons.Single();
        Assert.False(b.Campaign);
        Assert.Null(w.Press);
        Assert.False(w.Pressed);
        Assert.False(b.Resolve.On);
        var e = Dummy(b, 2, 0);
        var at = new List<(double, double)> { (2, 0) };
        var evs = Run(b, 3, () => Pin(b, [e], at));
        Assert.NotEmpty(evs.OfType<Ev.Slash>());
        Assert.Empty(evs.OfType<Ev.Resolve>());
        Assert.Empty(evs.OfType<Ev.Cast>());
        Assert.Equal(0, b.Resolve.Value);
    }
}
