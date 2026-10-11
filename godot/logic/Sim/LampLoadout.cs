using System;
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
    /// <summary>How many lamps are lit (the Flare burns as bright as the board: Flare.LampGlow).</summary>
    public int Lit;
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

    /// <summary>Every lamp effect lit under a rule id: skill lamps share ids across skills ("skill.area" on
    /// Dawnpulse and on Axe Gyre), small lamps across tags, and two lamps may light the same rule.</summary>
    public readonly Dictionary<string, List<LampEffect>> Each = new();

    public bool Has(string rule) => Rules.ContainsKey(rule);

    /// <summary>Debug switch for bisecting: LAMPS_OFF=id1,id2 leaves those rule ids unlit (read once).</summary>
    static readonly HashSet<string> Off = new((Environment.GetEnvironmentVariable("LAMPS_OFF") ?? "")
        .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));

    public void Add(LampEffect e)
    {
        if (e.Rule == null || Off.Contains(e.Rule)) return;
        Rules.TryAdd(e.Rule, e);
        if (!Each.TryGetValue(e.Rule, out var l)) Each[e.Rule] = l = new();
        l.Add(e);
    }

    /// <summary>A rule's size, at a quarter by night: summed over every lamp lighting it.</summary>
    public double Size(string rule, string arg, double fallback = 0) =>
        Sum(rule, arg, fallback, null) * (Night ? Lamps.NightSize : 1);

    /// <summary>A rule's size for one skill: the lamps on that skill, and those on any of its tags.</summary>
    public double SizeOn(string rule, string arg, string skill, Tag[]? tags, double fallback = 0) =>
        Sum(rule, arg, fallback, e => On(e, skill, tags)) * (Night ? Lamps.NightSize : 1);

    /// <summary>The rule is lit for this skill (a skill lamp on it, or a lamp on one of its tags).</summary>
    public bool HasOn(string rule, string skill, Tag[]? tags) =>
        Each.TryGetValue(rule, out var l) && l.Exists(e => On(e, skill, tags));

    static bool On(LampEffect e, string skill, Tag[]? tags) =>
        (e.Skill == null && e.Tags == null) || e.Skill == skill || (e.Tags != null && tags != null && Array.Exists(e.Tags, t => Array.IndexOf(tags, t) >= 0));

    double Sum(string rule, string arg, double fallback, Func<LampEffect, bool>? where)
    {
        if (!Each.TryGetValue(rule, out var l)) return 0;
        double v = 0;
        foreach (var e in l) if (where == null || where(e)) v += e.Arg(arg, fallback);
        return v;
    }

    /// <summary>A rule's number that is not a size (a price, a duration, a threshold): kept in full.</summary>
    public double Full(string rule, string arg, double fallback = 0) =>
        Rules.TryGetValue(rule, out var e) ? e.Arg(arg, fallback) : 0;

    public static readonly LampLoadout None = new();
}
