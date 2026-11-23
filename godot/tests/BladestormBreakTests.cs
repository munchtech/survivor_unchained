using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>(skills-five, 22 Nov; the owner: "the bladesttorm -> sunder cancel big hit is super strong to just keep bladestorm
/// -> instantly sunder -> repeat ... an easy fix is "if channeling for x time" then it does the big hit") Bladestorm's break
/// (a fresh press of Sunder's key) is the big hit only once the storm has spun breakAfter seconds (skills.json); a shorter
/// storm cancels into a plain Sunder swing. The probe measures three ways of fighting a pack at the ninth level, the
/// --veteran build (MapSim.Survivor, gear rarity 1): Sunder held, Bladestorm held then broken, and the loop "Bladestorm, at
/// once Sunder, repeat"; the loop must be no better than the better of the other two.</summary>
public sealed class BladestormBreakTests
{
    const double Dt = 1 / 60.0;
    readonly ITestOutputHelper _out;
    public BladestormBreakTests(ITestOutputHelper o) => _out = o;

    public enum Way { Sunder, Hold, Loop }

    /// <summary>Six foes round her, pinned where they stand each step (knockback and stun do not change the sum).</summary>
    static readonly (double X, double Z)[] Pack = [(1.6, 0), (1.2, 1.2), (1.2, -1.2), (0, 1.8), (0, -1.8), (2.4, 0.5)];
    static readonly (double X, double Z)[] One = [(1.6, 0)];

    public record Result(double Dps, int Breaks, int Storms, double Resolve);

    /// <summary>secs of fighting from Resolve 50. Hold: spin to holdFor s (or dry), break, swing Sunder until Resolve is 50
    /// again, spin again. Loop: spin tap s, a fresh Sunder press, the key held gap s, again.</summary>
    public static Result Measure(Way way, (double X, double Z)[] at, double tap = 0.1, double gap = 0.15, double holdFor = 4, double secs = 20, int level = 9)
    {
        var j = MapSim.Survivor("warden", level, 1, 5);
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        var storm = b.Weapons.Single(x => x.Id == "bladestorm");
        var sunder = b.Weapons.Single(x => x.Id == "sunder");
        var p = b.Player;
        var foes = at.Select(a =>
        {
            var e = b.SpawnEnemy("footpad", p.X + a.X, p.Z + a.Z)!;
            e.Hp = e.MaxHp = 1e9;
            e.AttackT = e.RangedT = 999;
            return e;
        }).ToList();
        foreach (var w in b.Weapons) w.Timer = 0;
        b.Resolve.Set(50);
        int breaks = 0, storms = 0;
        string phase = "start";
        double phaseT = 0;
        bool sunderDown = false, stormDown = false;
        void Sunder(bool down, bool press = false)
        {
            if (press) { b.HoldSkill(sunder.Slot, false); b.HoldSkill(sunder.Slot, true, p.X + 1.2, p.Z); b.PressSkill(sunder.Slot, p.X + 1.2, p.Z); }
            sunderDown = down;
        }
        void Storm(bool down, bool press = false)
        {
            if (press) { b.HoldSkill(storm.Slot, true, p.X + 1.2, p.Z); if (b.PressSkill(storm.Slot, p.X + 1.2, p.Z)) storms++; }
            stormDown = down;
        }
        void Go(string ph) { phase = ph; phaseT = 0; }
        for (double t = 0; t < secs; t += Dt)
        {
            for (int i = 0; i < foes.Count; i++) { foes[i].X = p.X + at[i].X; foes[i].Z = p.Z + at[i].Z; foes[i].Vx = foes[i].Vz = 0; }
            switch (way)
            {
                case Way.Sunder:
                    if (phase == "start") { Sunder(true, true); Go("swing"); }
                    break;
                case Way.Hold:
                    if (phase == "start" || phase == "build" && b.Resolve.Value >= 50) { Sunder(false); Storm(true, true); Go(storm.Channeling ? "spin" : "build"); if (phase == "build") Sunder(true, true); }
                    else if (phase == "spin" && (!storm.Channeling || phaseT >= holdFor)) { Storm(false); Sunder(true, true); Go("build"); }
                    break;
                case Way.Loop:
                    if (phase == "start" || phase == "after" && phaseT >= gap) { Sunder(false); Storm(true, true); Go("spin"); }
                    else if (phase == "spin" && phaseT >= tap) { Storm(false); Sunder(true, true); Go("after"); }
                    break;
            }
            if (sunderDown) b.HoldSkill(sunder.Slot, true, p.X + 1.2, p.Z); else b.HoldSkill(sunder.Slot, false);
            if (stormDown) b.HoldSkill(storm.Slot, true, p.X + 1.2, p.Z); else b.HoldSkill(storm.Slot, false);
            b.Tick(Dt, 0, 0);
            phaseT += Dt;
            foreach (var ev in b.Events.Drain()) if (ev is Ev.Spin { Phase: SpinPhase.Break }) breaks++;
        }
        double dmg = foes.Sum(e => e.MaxHp - e.Hp);
        return new Result(dmg / secs, breaks, storms, b.Resolve.Value);
    }

    static (Battle B, WeaponInst Storm, WeaponInst Sunder, Enemy Foe) Spun(double secs)
    {
        var j = MapSim.Survivor("warden", 9, 1, 5);
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        var storm = b.Weapons.Single(x => x.Id == "bladestorm");
        var sunder = b.Weapons.Single(x => x.Id == "sunder");
        var p = b.Player;
        var e = b.SpawnEnemy("footpad", p.X + 1.6, p.Z)!;
        e.Hp = e.MaxHp = 1e9;
        e.AttackT = e.RangedT = 999;
        foreach (var w in b.Weapons) w.Timer = 0;
        b.Resolve.Set(100);
        b.HoldSkill(storm.Slot, true);
        Assert.True(b.PressSkill(storm.Slot, e.X, e.Z), "the storm did not start");
        for (double t = 0; t < secs - 1e-9; t += Dt) { e.X = p.X + 1.6; e.Z = p.Z; b.HoldSkill(storm.Slot, true); b.Tick(Dt, 0, 0); }
        Assert.True(storm.Channeling);
        b.Events.Drain();
        return (b, storm, sunder, e);
    }

    static List<CombatEvent> PressSunder(Battle b, WeaponInst sunder, Enemy e, out bool went)
    {
        b.HoldSkill(sunder.Slot, true, e.X, e.Z);
        went = b.PressSkill(sunder.Slot, e.X, e.Z);
        var evs = new List<CombatEvent>();
        for (double t = 0; t < 0.4; t += Dt) { b.HoldSkill(sunder.Slot, false); b.Tick(Dt, 0, 0); evs.AddRange(b.Events.Drain()); }
        return evs;
    }

    [Fact]
    public void A_storm_shorter_than_breakAfter_cancels_into_a_plain_Sunder_swing()
    {
        double after = Content.Weapons.All["bladestorm"].Base.BreakAfter ?? 0;
        Assert.True(after > 0, "skills.json bladestorm has no breakAfter");
        var (b, storm, sunder, e) = Spun(after * 0.5);
        Assert.False(Firing.BreakReady(b, storm));
        Assert.False(b.BreakReadyOn(sunder), "the HUD's ready bond shows before the break is ready");
        b.HoldSkill(storm.Slot, false);   // (her storm key let go: held, the storm starts again, the test below)
        var evs = PressSunder(b, sunder, e, out bool went);
        Assert.True(went);
        Assert.DoesNotContain(evs, x => x is Ev.Spin { Phase: SpinPhase.Break });
        Assert.False(Firing.InStorm(b, storm), "the storm is still on after the cancel");
        Assert.Contains(evs, x => x is Ev.Slash);
    }

    [Fact]
    public void A_storm_of_breakAfter_or_more_breaks_in_the_great_blow()
    {
        double after = Content.Weapons.All["bladestorm"].Base.BreakAfter ?? 0;
        var (b, storm, sunder, e) = Spun(after + 0.1);
        Assert.True(Firing.BreakReady(b, storm));
        Assert.True(b.BreakReadyOn(sunder), "the HUD's ready bond does not show when the break is ready");
        var evs = PressSunder(b, sunder, e, out bool went);
        Assert.True(went);
        Assert.Single(evs.OfType<Ev.Spin>().Where(x => x.Phase == SpinPhase.Break));
    }

    /// <summary>(the owner, 22 Nov: "if we keep holding the bladestorm button it dosn't start again until we press it again")
    /// Sunder's key ends the storm (the break when ready, the cancel when not): with Bladestorm's key still held the storm
    /// starts again once it is ready, with no new press of its key; let go, it does not.</summary>
    [Theory]
    [InlineData(true, true)]
    [InlineData(false, true)]
    [InlineData(true, false)]
    [InlineData(false, false)]
    public void A_storm_Sunders_key_ended_starts_again_only_while_its_own_key_is_held(bool broken, bool held)
    {
        double after = Content.Weapons.All["bladestorm"].Base.BreakAfter ?? 0;
        var (b, storm, sunder, e) = Spun(broken ? after + 0.1 : after * 0.5);
        var p = b.Player;
        if (!held) b.HoldSkill(storm.Slot, false);
        b.HoldSkill(sunder.Slot, true, e.X, e.Z);
        Assert.True(b.PressSkill(sunder.Slot, e.X, e.Z));
        Assert.False(storm.Channeling, "Sunder's key did not end the storm");
        bool again = false;
        for (double t = 0; t < 8 && !again; t += Dt)
        {
            e.X = p.X + 1.6; e.Z = p.Z;
            b.Resolve.Set(100);
            b.HoldSkill(sunder.Slot, false);
            b.HoldSkill(storm.Slot, held);
            b.Tick(Dt, 0, 0);
            again = storm.Channeling;
        }
        Assert.Equal(held, again);
        // The new storm is its own: its break is not ready at once.
        if (again) Assert.False(Firing.BreakReady(b, storm), "the storm that started again can be broken at once");
    }

    /// <summary>The owner's loop, "Bladestorm, at once Sunder, repeat", is no better than holding Bladestorm (held its
    /// breakAfter, then broken: the best hold, since a longer one earns less a second) or holding Sunder, on a pack of six and
    /// on one foe. Before skills-five (no breakAfter): the loop 3039 dps on the pack against 2109 for a 1 s hold and break, 1458
    /// for a 4 s one, 447 for Sunder; on one foe 458 against 312, 195, 58.</summary>
    [Fact]
    public void The_spin_and_at_once_Sunder_loop_is_no_better_than_holding_either()
    {
        double after = Content.Weapons.All["bladestorm"].Base.BreakAfter ?? 0;
        foreach (var at in new[] { Pack, One })
        {
            double loop = Measure(Way.Loop, at, 0.1).Dps, hold = Measure(Way.Hold, at, holdFor: after + 2 * Dt).Dps, sunder = Measure(Way.Sunder, at).Dps;
            _out.WriteLine($"{at.Length} foes: loop {loop:0}, hold {hold:0}, Sunder {sunder:0}");
            Assert.True(loop <= Math.Max(hold, sunder), $"the loop {loop:0} dps beats holding ({hold:0}) and Sunder ({sunder:0})");
        }
    }

    /// <summary>The probe's table (skills.json breakAfter as it stands, or `after` written over it for a sweep).</summary>
    [Fact(Skip = "probe: run by hand (writes Weapons.All's bladestorm breakAfter while it runs)")]
    public void The_probe_table()
    {
        foreach (var after in new double?[] { null, 0, 1.0, 1.5, 2.0, 3.0 })
        {
            var was = Content.Weapons.All["bladestorm"].Base.BreakAfter;
            if (after != null) Content.Weapons.All["bladestorm"].Base.BreakAfter = after;
            try
            {
                _out.WriteLine($"breakAfter {(after ?? was ?? 0):0.0} s{(after == null ? " (data)" : "")}");
                foreach (var (name, at) in new[] { ("pack of 6", Pack), ("one foe", One) })
                {
                    var s = Measure(Way.Sunder, at);
                    var h = Measure(Way.Hold, at);
                    var line = $"  {name}: Sunder {s.Dps:0} | hold 4 s + break {h.Dps:0} ({h.Breaks} breaks) | loop spin+Sunder:";
                    foreach (var tap in new[] { 0.1, 0.5, 1.0, 1.5, 1.8, 2.0, 3.0 })
                    {
                        var l = Measure(Way.Loop, at, tap);
                        line += $" {tap:0.0}s {l.Dps:0} ({l.Breaks}b)";
                    }
                    _out.WriteLine(line);
                }
            }
            finally { Content.Weapons.All["bladestorm"].Base.BreakAfter = was; }
        }
    }
}
