using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The dash's growth in a fight (Content/DashSteps.cs): the steps she has taken, read where the dash is run. Nothing
 * here grows by use: the dash form gains no rank by being pressed (Forms.cs), only by these. */
public sealed partial class Battle
{
    /// <summary>The dash's steps taken (ids, a repeatable one once per time taken).</summary>
    public readonly List<string> DashSteps = new();

    static readonly Tag[] LandingTags = [Tag.Physical, Tag.Area];

    double StepSum(DashStepKind kind)
    {
        double s = 0;
        foreach (var id in DashSteps) if (Content.DashSteps.Find(id) is { } d && d.Kind == kind) s += d.Amount;
        return s;
    }

    /// <summary>Dash charges the steps add (Another Breath), at most DashSteps.MaxPips.</summary>
    public int DashPips => Math.Min(Content.DashSteps.MaxPips, RoundInt(StepSum(DashStepKind.Charge)));

    /// <summary>Her dash charges at most: the stat's, and the steps' pips (the HUD's pips read this).</summary>
    public int MaxDashCharges => RoundInt(Stats.Get(Stat.DashCharges)) + DashPips;

    /// <summary>Long Stride: how much farther the dash (and the form riding it) carries her.</summary>
    public double DashStride => 1 + StepSum(DashStepKind.Length);

    /// <summary>Quick Breath: how much faster charges come back (25% sooner: the wait times 0.75).</summary>
    double DashBreath => 1 / Math.Max(0.1, 1 - StepSum(DashStepKind.Recharge));

    /// <summary>A step taken: kept for the fight, its facet opened on the form, a new pip filled at once. Announce
    /// (Ev.DashStep) when granted in play; the steps a fight starts with come in silently. False when it is unknown
    /// or taken as often as it may be.</summary>
    public bool GrantDashStep(string id, bool announce = true)
    {
        if (!Content.DashSteps.CanTake(DashSteps, id)) return false;
        var d = Content.DashSteps.Find(id)!;
        int pips = DashPips;
        DashSteps.Add(id);
        if (Player != null && DashPips > pips) Player.DashCharges = Math.Min(MaxDashCharges, Player.DashCharges + DashPips - pips);
        if (announce) Events.Emit(new Ev.DashStep { Id = id });
        return true;
    }

    /// <summary>A dash (or the form that carried her in its place) has ended: Hard Landing shoves the lesser things
    /// round her aside.</summary>
    void DashLanded()
    {
        if (!Combat) return;
        DashStepDef? hard = null;
        foreach (var id in DashSteps) if (Content.DashSteps.Find(id) is { Kind: DashStepKind.Landing } d) { hard = d; break; }
        if (hard is not { } hd) return;
        var p = Player;
        double r = hd.Radius > 0 ? hd.Radius : 2;
        var was = credit;
        credit = "dash";
        ForEachHostileInRadius(p.X, p.Z, r, (e, dist) =>
        {
            if (e.Elite || e.Boss || e.Decoy) return;
            double dd = dist == 0 ? 1 : dist;
            HitEnemy(e, hd.Damage, School.Physical, LandingTags, new HitOpts { Knockback = hd.Knockback, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, NoProcs = true, Credit = "dash" });
        });
        credit = was;
        Events.Emit(new Ev.HardLanding { X = p.X, Z = p.Z, Radius = r });
    }
}
