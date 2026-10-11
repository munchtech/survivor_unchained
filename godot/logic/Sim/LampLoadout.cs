using System.Collections.Generic;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/// <summary>A reflex (docs/design/CLASSES.md §0): a calling's art that fires itself when its
/// moment comes (Trigger), at most once a Wait.</summary>
public sealed record ReflexDef(string Art, string Trigger, double Wait, Dictionary<string, double>? Args);

/// <summary>What the lit lamps bring one fight (Rpg/LampBook.Loadout): numbers, rules, the dash
/// form's facets, the reflexes, the Flare and its lamps, and the road whose cards lean.</summary>
public sealed class LampLoadout
{
    /// <summary>By night: sizes run at a quarter (rules read their numbers through Size).</summary>
    public bool Night;
    /// <summary>The type: the road chosen.</summary>
    public string Type = "";
    public readonly List<StatMod> Mods = new();
    /// <summary>Attribute points from the attribute lamps (by day and in maps).</summary>
    public readonly Dictionary<string, int> Attributes = new();
    /// <summary>The rules lit, by id, with their numbers.</summary>
    public readonly Dictionary<string, LampEffect> Rules = new();
    /// <summary>Facets the lamps give the calling's own arts: its dash form's and its reflexes'.</summary>
    public readonly HashSet<string> Facets = new();
    /// <summary>The calling's own dash form (the Kin, given by the hearth) and its wait.</summary>
    public string? Kin;
    public double KinWait;
    public readonly List<ReflexDef> Reflexes = new();
    /// <summary>The Flare carried ("" for none) and its lamps (their rule ids).</summary>
    public string Flare = "";
    public readonly HashSet<string> FlareMods = new();
    /// <summary>The road lit deepest: by night its cards lean (Lamps.RoadLean).</summary>
    public string Lean = "";

    public bool Has(string rule) => Rules.ContainsKey(rule);

    /// <summary>A rule's size, at a quarter by night.</summary>
    public double Size(string rule, string arg, double fallback = 0) =>
        Rules.TryGetValue(rule, out var e) ? e.Arg(arg, fallback) * (Night ? Lamps.NightSize : 1) : 0;

    /// <summary>A rule's number that is not a size (a price, a duration, a threshold): kept in full.</summary>
    public double Full(string rule, string arg, double fallback = 0) =>
        Rules.TryGetValue(rule, out var e) ? e.Arg(arg, fallback) : 0;

    public static readonly LampLoadout None = new();
}
