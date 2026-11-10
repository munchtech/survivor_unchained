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
        // The grip: held at the nearest foe in its reach.
        foreach (var w in b.Weapons)
        {
            if (!w.Hold) continue;
            double reach = (w.Num(s => s.Reach) ?? 2.6) + d.GripPad;
            var near = b.NearestHostile(p.X, p.Z, reach);
            if (near == null || !h.GripHeld(b.Time)) b.HoldSkill(w.Slot, false);
            else b.HoldSkill(w.Slot, true, near.X, near.Z);
        }
        // A union that took the grip's key (Bladestorm: Sunder's is its break): out of a storm that key still swings Sunder,
        // and a grip-only hand holds it as it held the grip.
        if (h.GripOnly)
        {
            foreach (var w in b.Weapons)
                if (w.Slot2 >= 0 && !w.Channeling && d.For(w.Id).Aim == "storm" && !Firing.InStorm(b, w)
                    && b.NearestHostile(p.X, p.Z, (w.Num(s => s.Reach) ?? 2.6) + d.GripPad) is { } nf && h.GripHeld(b.Time))
                { h.HalfGrip = Firing.HalfOf(w)?.Id; b.PressSkill(w.Slot2, nf.X, nf.Z); }
            return;
        }
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

    /// <summary>Bladestorm: held while its crowd stands (or Resolve is full and a foe is near), broken on its lines.</summary>
    static bool Storm(Battle b, PressHands h, WeaponInst w, PlanRule r, bool full, bool ignore)
    {
        var p = b.Player;
        int n = b.HostilesInRadius(p.X, p.Z, 3.5).Count, start = r.When?.Count ?? 4, thin = r.ThinBelow ?? 4;
        if (w.Channeling)
        {
            bool late = w.ChannelMax - w.ChannelT <= (r.BreakLate ?? 0.5);
            if (w.Slot2 >= 0 && (w.Lines.Count >= (r.BreakLines ?? 2) || late || (n < thin && w.Lines.Count > 0)))
            { b.HoldSkill(w.Slot, false); b.PressSkill(w.Slot2, p.X, p.Z); return true; }
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
        // Out of a storm, Sunder's key swings Sunder at what is near.
        if (w.Slot2 >= 0 && !Firing.InStorm(b, w) && n > 0) { h.HalfGrip = Firing.HalfOf(w)?.Id; b.PressSkill(w.Slot2, p.X, p.Z); }
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
