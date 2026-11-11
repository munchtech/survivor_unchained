using System;
using System.Collections.Generic;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;

namespace SurvivorUnchained.Look;

/// <summary>One hold asked of one body: seconds, how long after the blow it lands (her Oathblade's hits wait for
/// their sweep), and the blow's direction (the victim's shake).</summary>
public readonly record struct StopAsk(int Body, double Seconds, double Delay, double Dx, double Dz);

/// <summary>Local hit-stop's classes: from one sim step's events, which bodies hold and for how long. Her heavy hit is
/// LeadRule.Heavy, the one definition the sound's lead uses. Plain C#; the one piece of state is the charge's "first
/// impact only". Each body gets the longest class that applies to it this step.</summary>
public sealed class HitStopClassifier
{
    readonly HitStopTable t;
    bool chargeStopped;
    readonly Dictionary<int, StopAsk> best = new();
    readonly List<Ev.Hit> struck = new();
    public HitStopClassifier(HitStopTable? table = null) { t = table ?? HitStopTable.Load; }

    /// <summary>The Oathblade and its evolutions (skills.json oathblade: slash_steel, slash_holy, slash_blood).</summary>
    public static bool IsOath(string? art) => art is "slash_steel" or "slash_holy" or "slash_blood";

    static bool Qualifies(Ev.Hit h) => h.Weapon != null && !h.ByFlare && !h.Dot && !h.Blocked;

    void Put(int body, double ms, double delay, double dx, double dz)
    {
        if (ms <= 0) return;
        if (best.TryGetValue(body, out var o) && o.Seconds >= ms / 1000) return;
        best[body] = new StopAsk(body, ms / 1000, delay, dx, dz);
    }

    readonly List<Ev.Kill> kills = new();
    readonly HashSet<int> touched = new();
    readonly HashSet<int> hitIds = new();

    /// <summary>The asks of one step. maxHp: hers (a hurt is over 12% of it). herX, herZ: where she stands (NaN: unknown,
    /// every blow counts as her contact): she holds only for a blow that lands within her_reach_m of her, so a wave or a
    /// thrown edge landing late, or a wound's kill, holds the struck body alone and never stops her mid wind-up.</summary>
    public List<StopAsk> Of(IReadOnlyList<CombatEvent> evs, double maxHp, double herX = double.NaN, double herZ = double.NaN)
    {
        best.Clear(); struck.Clear(); kills.Clear(); touched.Clear(); hitIds.Clear();
        int mass = 0;
        double art = 0;
        bool Near(double x, double z) => double.IsNaN(herX) || (x - herX) * (x - herX) + (z - herZ) * (z - herZ) <= t.HerReachM * t.HerReachM;
        foreach (var e in evs)
        {
            switch (e)
            {
                case Ev.Hit h when Qualifies(h):
                    struck.Add(h);
                    hitIds.Add(h.Target);
                    // Her own blade's swing is her contact at any reach her gear gives it; other weapons count only within her_reach_m.
                    bool near = IsOath(h.Art) || Near(h.X, h.Z);
                    if (near) touched.Add(h.Target);
                    double ms = LeadRule.Heavy(h) ? (h.Crit ? t.CritMs : t.HeavyMs) : t.TrashMs;
                    if (ms > 0)
                    {
                        double d = IsOath(h.Art) ? t.FirstHitDelayMs / 1000 : 0;
                        Put(h.Target, ms, d, h.Dx, h.Dz);
                        if (near) Put(HitStops.Her, ms, d, 0, 0);
                    }
                    break;
                case Ev.Kill k when k.ByPlayer && !k.ByFlare:
                    kills.Add(k);
                    break;
                case Ev.PlayerHit ph when !ph.Dodged && !ph.Blocked && !ph.Dot && maxHp > 0 && ph.Amount > maxHp * 0.12:
                    Put(HitStops.Her, t.HurtMs, 0, 0, 0);
                    break;
                case Ev.Ability { Id: "shield_bash" or "bull_rush" or "leap" }:
                case Ev.Leap { Phase: LeapPhase.Land }:
                case Ev.Charge { Phase: ChargePhase.Stop or ChargePhase.Slam }:
                case Ev.Spin { Phase: SpinPhase.Break }:
                case Ev.Brace { Phase: BracePhase.Burst }:
                    art = t.ArtMs;
                    break;
                case Ev.Charge { Phase: ChargePhase.Impact } when !chargeStopped:
                    chargeStopped = true; art = t.ArtMs;
                    break;
                case Ev.Charge { Phase: ChargePhase.Start }:
                    chargeStopped = false;
                    break;
            }
        }
        // A mass kill (one blow felling mass_kill_n or more: kills this step by a blow that landed this step) holds every
        // body it felled like an elite kill. An elite or boss kill holds the body; either holds her too only when her
        // own blow landed on it, near, this step.
        foreach (var k in kills) if (hitIds.Contains(k.Enemy)) mass++;
        bool massKill = t.MassKillN > 0 && mass >= t.MassKillN;
        foreach (var k in kills)
        {
            bool big = k.Elite || k.Boss;
            if (!big && !(massKill && hitIds.Contains(k.Enemy))) continue;
            double km = k.Boss ? t.BossKillMs : t.EliteKillMs;
            Put(k.Enemy, km, 0, k.Dx, k.Dz);
            if (touched.Contains(k.Enemy)) Put(HitStops.Her, km, 0, 0, 0);
        }
        if (art > 0)
        {
            Put(HitStops.Her, art, 0, 0, 0);
            foreach (var h in struck) Put(h.Target, art, 0, h.Dx, h.Dz);
        }
        return new List<StopAsk>(best.Values);
    }
}
