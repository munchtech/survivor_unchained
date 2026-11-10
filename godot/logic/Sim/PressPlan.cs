using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Sim;

/* The one press plan (M3; data/content/press_plan.json): what a pressing hand presses in a campaign fight. The harness's
 * bots and the game's autopilot run it through PressHands (how late, how often missed, how often the grip is let go,
 * how often a condition is ignored, whether marks are read). One press a step; the grip every step. */
public sealed class PlanRule
{
    public int Priority = 9;
    public KindleDef? When;
    public string Aim = "hover";
    public double? Reach, PackRadius, Line, LineHalf, BreakLate;
    public int? PackMin, LineMin, BreakLines, ThinBelow;
}

public sealed class PressPlanDef
{
    public double SpendFullAt = 0.9, GripPad = 1.5;
    public PlanRule Default = new();
    public Dictionary<string, PlanRule> Skills = new();
    public PlanRule For(string id) => Skills.TryGetValue(id, out var r) ? r : Default;
}

/// <summary>The hands' gap rule (M3 MR 3 h1): a model of the BOT'S HANDS, no rule of the game. A CHAINED grip's key
/// stays down for up to the chain's grace (ChainDef.Grace, else Battle.ChainGrace) after the last step a foe stood in its
/// reach and a step, as a player's would between two foes: the chain is then never released over a short gap. It only
/// STAYS down: a key that came up (the grace ran out, the hand's lapse, another battle) goes down again only at a foe.
/// The hand's lapse (PressHands.GripHeld) is not bridged: it lifts the key in a gap as it does at a foe. An unchained
/// grip has no grace: bit for bit the old line (a foe in reach, and the hand holding). One memory per key, by slot.</summary>
public sealed class GripGaps
{
    readonly Dictionary<int, (double At, double X, double Z)> seen = new();
    /// <summary>(tests) The grace of a grip in place of its record's: a union's half takes its record from its def each
    /// step (Firing.HalfOf), so no test-only chain stays on it.</summary>
    internal Func<WeaponInst, double>? GraceOf;

    /// <summary>How long the hand holds a grip's key through a gap: its chain's grace; 0 unchained (or kindled).</summary>
    public static double Grace(WeaponInst? grip) => grip is { Chained: true } ? grip.Press?.Chain?.Grace ?? Battle.ChainGrace : 0;

    /// <summary>Whether the key on `slot` is down this step, and its aim. `foe`: a foe stands in the grip's reach and a
    /// step (at x, z: the aim, and remembered). `down`: the key is down now (it stays down, it is never pressed, in a
    /// gap). `h`: the hand whose lapse lifts it (null: none). The same answer however often it is asked in a step.</summary>
    internal bool Down(Battle b, int slot, WeaponInst? grip, bool foe, double x, double z, bool down, PressHands? h, out (double X, double Z) aim)
    {
        aim = (x, z);
        if (foe)
        {
            if (h != null && !h.GripHeld(b.Time)) { seen.Remove(slot); return false; }
            seen[slot] = (b.Time, x, z);
            return true;
        }
        double grace = grip == null ? 0 : GraceOf?.Invoke(grip) ?? Grace(grip);
        if (grace > 0 && down && seen.TryGetValue(slot, out var m) && b.Time >= m.At && b.Time - m.At <= grace && (h == null || h.GripHeld(b.Time)))
        {
            aim = (m.X, m.Z);
            return true;
        }
        seen.Remove(slot);
        return false;
    }
}

/// <summary>A hand on the plan: deft (no delay, nothing missed), human (React s late, a share missed, the grip let go a
/// share of the time), careless (conditions ignored half the time, marks unread), grip-only (standing, idler).</summary>
public sealed class PressHands
{
    public double React, Miss, GripShare = 1, Ignore;
    public bool GripOnly, Reads = true;
    readonly Rng rng;
    readonly Dictionary<WeaponInst, (double Since, bool Missed)> due = new(ReferenceEqualityComparer.Instance);
    double gripRollAt = double.NegativeInfinity, ignoreRollAt = double.NegativeInfinity;
    bool gripOn = true, ignoring;
    /// <summary>A union's second key held as the grip this step (Bladestorm on Sunder's key, out of a storm with a foe in
    /// reach: the key is pressed every step, a hold): the half's id, else null. What the game's --clip prints as the grip's hold.</summary>
    public string? HalfGrip;
    /// <summary>The held keys' memory of the last foe in reach (the gap rule: GripGaps).</summary>
    public readonly GripGaps Gaps = new();
    /// <summary>Presses that went off, by skill id (the harness's presses per minute).</summary>
    public readonly Dictionary<string, int> Presses = new();

    public PressHands(uint seed) { rng = new Rng(seed * 2654435761u + 91); }
    public static PressHands Deft(uint seed) => new(seed);
    public static PressHands Human(uint seed, double react)
    {
        var h = new PressHands(seed) { React = react, GripShare = 0.85 };
        h.Miss = 0.10 + 0.05 * h.rng.Next();
        return h;
    }
    public static PressHands Careless(uint seed, double react) => new(seed) { React = react, Miss = 0.15, GripShare = 0.85, Ignore = 0.5, Reads = false };
    public static PressHands Grip(uint seed) => new(seed) { GripOnly = true };

    internal bool GripHeld(double now)
    {
        if (GripShare >= 1) return true;
        if (now - gripRollAt >= 0.5) { gripRollAt = now; gripOn = rng.Next() < GripShare; }
        return gripOn;
    }

    internal bool Ignoring(double now)
    {
        if (Ignore <= 0) return false;
        if (now - ignoreRollAt >= 2) { ignoreRollAt = now; ignoring = rng.Next() < Ignore; }
        return ignoring;
    }

    /// <summary>The press is wanted now: true once it has been wanted React s and was not missed.</summary>
    internal bool Due(WeaponInst w, double now)
    {
        if (!due.TryGetValue(w, out var d)) due[w] = d = (now, Miss > 0 && rng.Next() < Miss);
        if (d.Missed) { if (now - d.Since > 1.5) due.Remove(w); return false; }
        return now - d.Since >= React;
    }
    internal void Clear(WeaponInst w) => due.Remove(w);
    internal void Went(WeaponInst w) { due.Remove(w); Presses[w.Id] = Presses.GetValueOrDefault(w.Id) + 1; }
}

public static class PressPlan
{
    static PressPlanDef? def;
    public static PressPlanDef Def => def ??= JsonSerializer.Deserialize<PressPlanDef>(Json.ReadContent("press_plan.json"), Json.Options)!;

    /// <summary>One step of the plan (campaign only). `sees`: the hand reads the marks this step (Human's awareness).</summary>
    public static void Run(Battle b, PressHands h, bool sees = true)
    {
        var p = b.Player;
        if (!b.Campaign || !p.Alive) return;
        var d = Def;
        h.HalfGrip = null;
        // The grip: held at the nearest foe in its reach; a chained grip held on through a gap of up to its chain's
        // grace, at the last foe's place (GripGaps: the hands' gap rule).
        foreach (var w in b.Weapons)
        {
            if (!w.Hold) continue;
            double reach = (w.Num(s => s.Reach) ?? 2.6) + d.GripPad;
            var near = b.NearestHostile(p.X, p.Z, reach);
            if (h.Gaps.Down(b, w.Slot, w, near != null, near?.X ?? 0, near?.Z ?? 0, w.Held, h, out var at)) b.HoldSkill(w.Slot, true, at.X, at.Z);
            else b.HoldSkill(w.Slot, false);
        }
        // A union that took the grip's key (Bladestorm: Sunder's is its break): out of a storm that key still swings Sunder,
        // and the hand HOLDS it as it held the grip, every step, before any return below (a dash, a leap, a rush, another
        // press going off or the storm's press waiting never lets it go), and through the storm's spin, as a player's would.
        foreach (var w in b.Weapons)
        {
            if (w.Slot2 < 0 || w.Behavior != WeaponBehavior.Spin || d.For(w.Id).Aim != "storm") continue;
            if (!HalfGrip(b, h, w, out var at)) { b.HoldSkill(w.Slot2, false); continue; }
            if (h.GripOnly) b.HoldSkill(w.Slot2, true, at.X, at.Z); else b.HoldSkill(w.Slot2, true, p.X, p.Z);
            if (!Firing.InStorm(b, w)) h.HalfGrip = Firing.HalfOf(w)?.Id;
        }
        if (h.GripOnly) return;
        if (p.Leap != null || b.Art.Rush != null || p.DashT > 0) return;
        bool reads = sees && h.Reads, ignore = h.Ignoring(b.Time);
        bool full = b.Resolve.On && b.Resolve.Value >= d.SpendFullAt * b.Resolve.Max;
        foreach (var w in b.Weapons.Where(w => w.Keyed && !w.Hold && w.DisabledT <= 0).OrderBy(w => d.For(w.Id).Priority).ToList())
        {
            var rule = d.For(w.Id);
            if (rule.Aim == "storm") { if (Storm(b, h, w, rule, full, ignore)) return; continue; }
            double cost = b.CostOf(w);
            bool ready = w.KindledNow
                ? w.KindleKey == KindlePress.Now ? (w.Timer <= 0 || w.Relooking) && !b.BlowPending(w) && (cost <= 0 || b.Resolve.Value >= cost / 2) : w.PressWait <= 0
                : w.Timer <= 0 && !w.Channeling && !b.BlowPending(w) && (cost <= 0 || b.Resolve.Value >= cost);
            if (!ready) { h.Clear(w); continue; }
            var when = rule.When ?? (w.KindledNow ? w.Kindle : null);
            bool cond = ignore || when == null || (reads || !NeedsReading(when)) && b.Kindled(when);
            // A kindled "now" spender fires itself only when Resolve is full (and takes all of it): the plan heaves it
            // from its whole cost as soon as its condition holds, and always before Resolve would cap.
            if (w.KindledNow && w.KindleKey == KindlePress.Now && cost > 0 && !ignore) cond = full || cond && b.Resolve.Value >= cost;
            else if (cost > 0 && full) cond = true;
            // Full: the spender goes at what there is (a pack if one stands in reach, else the nearest foe), never wasted.
            if (!cond || (AimOf(b, w, rule) ?? (cost > 0 && full ? AimOf(b, w, d.Default) : null)) is not var (ax, az)) { h.Clear(w); continue; }
            if (!h.Due(w, b.Time)) continue;
            if (b.PressSkill(w.Slot, ax, az)) { h.Went(w); return; }
        }
    }

    static bool NeedsReading(KindleDef k) => k.When == "windup" || k.Any?.Any(NeedsReading) == true;

    /// <summary>The union's grip this step (its other half held on its second key): whether the key is down, and the
    /// aim: the nearest foe in the half's reach and the pad while the hand holds (PressHands.GripHeld: one roll each half
    /// second, the same answer all step); a chained half's key held on through a gap of up to its chain's grace at the
    /// last foe's place (GripGaps: the hands' gap rule; the same answer all step, so the storm's break may ask again).</summary>
    static bool HalfGrip(Battle b, PressHands h, WeaponInst w, out (double X, double Z) at)
    {
        var half = Firing.HalfOf(w);
        double reach = (half?.Num(s => s.Reach) ?? 2.6) + Def.GripPad;
        var near = b.NearestHostile(b.Player.X, b.Player.Z, reach);
        return h.Gaps.Down(b, w.Slot2, half, near != null, near?.X ?? 0, near?.Z ?? 0, w.Held2, h, out at);
    }

    /// <summary>Bladestorm: held while its crowd stands (or Resolve is full and a foe is near), broken on its lines.</summary>
    static bool Storm(Battle b, PressHands h, WeaponInst w, PlanRule r, bool full, bool ignore)
    {
        var p = b.Player;
        int n = b.HostilesInRadius(p.X, p.Z, 3.5).Count, start = r.When?.Count ?? 4, thin = r.ThinBelow ?? 4;
        if (w.Channeling)
        {
            bool late = w.ChannelMax - w.ChannelT <= (r.BreakLate ?? 0.5);
            if (w.Slot2 >= 0 && (w.Lines.Count >= (r.BreakLines ?? 2) || late || (n < thin && w.Lines.Count > 0)))
            {
                // The break is a FRESH press of the second key (a grip held from before the storm never breaks it): the
                // held key comes up and goes down again, and stays down after if the hand is holding the grip this step.
                b.HoldSkill(w.Slot, false);
                b.HoldSkill(w.Slot2, false);
                b.HoldSkill(w.Slot2, true);
                b.PressSkill(w.Slot2, p.X, p.Z);
                if (!HalfGrip(b, h, w, out _)) b.HoldSkill(w.Slot2, false);
                return true;
            }
            b.HoldSkill(w.Slot, n >= thin || full && n > 0);
            return false;
        }
        if (w.Timer <= 0 && (n >= start || (full || ignore) && n > 0))
        {
            if (!h.Due(w, b.Time)) return false;
            b.HoldSkill(w.Slot, true);
            if (b.PressSkill(w.Slot, p.X + Math.Sin(p.Facing) * 2, p.Z + Math.Cos(p.Facing) * 2)) { h.Went(w); return true; }
            return false;
        }
        h.Clear(w);
        b.HoldSkill(w.Slot, false);
        // (Out of a storm, Sunder's key swings Sunder at what is near: held in Run, before every return.)
        return false;
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    static (double X, double Z)? AimOf(Battle b, WeaponInst w, PlanRule r)
    {
        var p = b.Player;
        if (r.Aim == "self" || w.Press?.Aim == PressAim.Self)
            return b.NearestHostile(p.X, p.Z, Math.Max(3.5, w.Num(s => s.Radius) ?? 3.5)) != null || r.When != null ? (p.X, p.Z) : null;
        double reach = r.Reach ?? w.Press?.Reach ?? w.AimRange;
        var near = b.HostilesInRadius(p.X, p.Z, reach);
        if (near.Count == 0) return null;
        if (r.Aim == "pack")
        {
            double pr = r.PackRadius ?? 3.5; Enemy? best = null; int most = 0;
            foreach (var e in near) { int c = near.Count(o => Dist(o.X, o.Z, e.X, e.Z) <= pr); if (c > most) { most = c; best = e; } }
            if (best == null || most < (r.PackMin ?? 1)) return null;
            var pack = near.Where(o => Dist(o.X, o.Z, best.X, best.Z) <= pr).ToList();
            return (pack.Average(o => o.X), pack.Average(o => o.Z));
        }
        if (r.Aim == "line")
        {
            double len = r.Line ?? reach, half = r.LineHalf ?? 1.2; (double, double)? at = null; int most = 0;
            foreach (var t in near)
            {
                double l = Math.Max(0.1, Dist(t.X, t.Z, p.X, p.Z)), dx = (t.X - p.X) / l, dz = (t.Z - p.Z) / l; int c = 0;
                foreach (var o in near)
                {
                    double rx = o.X - p.X, rz = o.Z - p.Z, along = rx * dx + rz * dz;
                    if (along > 0 && along <= len && Math.Abs(rx * dz - rz * dx) <= half + o.Radius) c++;
                }
                if (c > most) { most = c; at = (p.X + dx * len, p.Z + dz * len); }
            }
            return most >= (r.LineMin ?? 1) ? at : null;
        }
        var n = b.NearestHostile(p.X, p.Z, reach);
        return n == null ? null : (n.X, n.Z);
    }
}
