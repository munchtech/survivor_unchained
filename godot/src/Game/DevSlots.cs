using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>
/// M4 (docs/design/M4_HUD.md §1, the judge's build): --slots "sunder:hold,cleaver:channel,heroic_leap:press,..." puts
/// those skills on the slots in that order (slot 1 = LMB, 2 = RMB, 3-6 = the keys 1-4) in the form each names, through
/// the sim's public API (RemoveWeapon, AddWeapon, SetForm), once in each campaign fight. With --grant-union U it then
/// makes the union from its carried parts (Battle.GrantUnion: Bladestorm takes the Cleaver's key and the Sunder's), so
/// the union sits on the keys --slots gave its parts whichever of the two runs first. GameHud.Frame ticks it.
/// </summary>
public static class DevSlots
{
    static readonly string? Spec = Args.Get("slots");
    static Battle? done;

    /// <summary>--resolve-at T:V[,T:V...] (pictures): her Resolve set to V once the fight's clock passes T s (a storm's
    /// fuel, a spender short of its cost), each once.</summary>
    static readonly (double T, double V)[] ResolveAt = (Args.Get("resolve-at") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries)
        .Select(x => x.Split(':')).Where(x => x.Length == 2)
        .Select(x => (double.Parse(x[0], System.Globalization.CultureInfo.InvariantCulture), double.Parse(x[1], System.Globalization.CultureInfo.InvariantCulture))).ToArray();
    static int resolveNext;
    static double traceAt;
    static Battle? resolveFor;

    /// <summary>--step-won ID[@T] (pictures, M4 §3): the dash step ID granted (no banner) once the campaign fight's clock
    /// passes T s (default 2), and the HUD's step-won motion fired for it directly (GameHud.StepWon).</summary>
    static readonly string? StepSpec = Args.Get("step-won");
    static readonly string StepId = StepSpec?.Split('@')[0].Trim() ?? "";
    static readonly double StepAt = StepSpec?.Split('@') is { Length: > 1 } sp
        && double.TryParse(sp[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var st) ? st : 2;
    static Battle? stepFor;

    /// <summary>The step due now (once a fight), or null.</summary>
    public static Content.DashStepDef? StepDue(Battle b)
    {
        if (StepSpec == null || ReferenceEquals(stepFor, b) || !b.Campaign || !b.Combat) return null;
        if (b.Time < StepAt) return null;
        stepFor = b;
        var step = Content.DashSteps.Find(StepId);
        if (step == null) { GD.Print($"step-won: {StepId} unknown"); return null; }
        GD.Print($"step-won: {step.Id} granted {(b.GrantDashStep(step.Id, announce: false) ? "yes" : "no (taken already)")} at {b.Time:0.00}");
        return step;
    }

    public static void Tick(Battle b)
    {
        if (ResolveAt.Length > 0 && b.Campaign && b.Combat)
        {
            if (!ReferenceEquals(resolveFor, b)) { resolveFor = b; resolveNext = 0; }
            while (resolveNext < ResolveAt.Length && b.Time >= ResolveAt[resolveNext].T)
            {
                b.Resolve.Set(ResolveAt[resolveNext].V);
                GD.Print($"slots: resolve set to {ResolveAt[resolveNext].V} at {b.Time:0.00}");
                resolveNext++;
            }
        }
        if (Args.Has("slots-trace") && b.Campaign && b.Combat && b.Time >= traceAt)
        {
            traceAt = b.Time + 0.25;
            var sb = new System.Text.StringBuilder($"slots-trace t {b.Time:0.00} resolve {b.Resolve.Value:0}");
            foreach (var w in b.Weapons) sb.Append($" | {w.Id}@{w.Slot + 1}/{w.Slot2 + 1} {w.Cast} held {w.Held} ch {w.Channeling} t {w.Timer:0.0} brk {w.BreakUntil:0.0}");
            GD.Print(sb.ToString());
        }
        if (Spec == null || ReferenceEquals(done, b) || !b.Combat || !b.Campaign) return;
        done = b;
        foreach (var line in Apply(b, Spec, Args.Get("grant-union"))) GD.Print(line);
    }

    /// <summary>What it did, a line each, for the log.</summary>
    public static List<string> Apply(Battle b, string spec, string? union)
    {
        var said = new List<string>();
        var ranks = b.Weapons.ToDictionary(w => w.Id, w => w.Rank);
        int top = ranks.Count > 0 ? ranks.Values.Max() : 1;
        foreach (var id in b.Weapons.Select(w => w.Id).ToList()) b.RemoveWeapon(id);
        foreach (var raw in spec.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var parts = raw.Split(':');
            string id = parts[0], cast = parts.Length > 1 ? parts[1] : "";
            var w = b.AddWeapon(id, Math.Min(Content.Weapons.MaxRank, ranks.TryGetValue(id, out var r) ? r : top));
            if (w == null) { said.Add($"slots: {id} not added (unknown, or no slot free)"); continue; }
            bool formed = cast == "" || b.SetForm(id, cast);
            said.Add($"slots: {id} on slot {w.Slot + 1}{(cast == "" ? "" : formed ? $" as {cast}" : $" ({cast} refused by its record)")}");
        }
        if (!string.IsNullOrWhiteSpace(union))
        {
            var u = b.GrantUnion(union.Trim());
            said.Add(u != null ? $"slots: union {union} on slots {u.Slot + 1} and {u.Slot2 + 1}" : $"slots: union {union} not made");
        }
        return said;
    }
}
