using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;

namespace SurvivorUnchained.Rpg;

/// <summary>What working a chart costs at the Wayfinder's table (docs/CRAFTING_DESIGN.md 20.4).</summary>
public sealed class ChartRules
{
    public string Crafter = "wayfinder";
    /// <summary>A chart's heat at drop, plain, fine and rare: its budget, as a piece's is.</summary>
    public List<int> Heat = new() { 4, 6, 8 };
    public ChartStep Ink = new() { Shards = 1, Gold = 10, GoldPerTier = 5, Heat = new[] { 2, 3 } };
    public ChartStep Burn = new() { Shards = 2, Heat = new[] { 2, 3 } };
    public ChartStep Pin = new() { Material = 2, Heat = new[] { 1, 1 } };
    public ChartStep Scrape = new() { Iron = 3, Heat = new[] { 1, 2 } };
    public ChartStep Annotate = new() { Gold = 20, GoldPerTier = 10 };
    public int QualityStep = 5, QualityMax = 20, PerSide = 3;
}

public sealed class ChartStep { public int Shards, Iron, Material, Gold, GoldPerTier; public int[] Heat = { 0, 0 }; }

/* Working charts (docs/CRAFTING_DESIGN.md 20.4): Path of Exile's map crafting kept for its choices,
 * its slot machine dropped. Each verb is chosen and costed before it is done, a chart has heat as a
 * piece has, and the materials are the two arenas' own: shards from the scars, the people's material
 * and iron from the atlas. Ysolde does it at her table, in her words. */
public static partial class Crafting
{
    /// <summary>A chart's heat as it drops, by its rarity (plain, fine, rare).</summary>
    public static int ChartHeat(Chart c) => Rules.Charts.Heat[Math.Clamp(c.Rarity, 0, Rules.Charts.Heat.Count - 1)];

    /// <summary>The heat a chart has left (one from before charts had heat is full).</summary>
    public static int ChartHeatLeft(ItemInstance it) => it.Heat ?? (it.Chart is { } c ? ChartHeat(c) : 0);

    /// <summary>"the Pack's ground", "the Lamplings' ground".</summary>
    public static string Ground(string people) => MapOffers.People(people).Name is var n && n.EndsWith("s") ? $"{n}' ground" : $"{n}'s ground";

    /// <summary>The material a people's ground pays, which pins a mod on its chart (a Pack chart: wolf pelts).</summary>
    public static string PeoplesMaterial(string people) =>
        Rules.Night.Peoples.GetValueOrDefault(people)?.FirstOrDefault()?.Material ?? Shard;

    static Quote ChartQuote(Verb v, ItemInstance it, string title, string? crafter, ChartStep step, CraftCtx x)
    {
        var q = Begin(v, crafter ?? Rules.Charts.Crafter, title);
        if (it.Chart is not { } c) { q.Blocked = "That is not a chart."; return q; }
        if (step.Shards > 0) q.Takes[Shard] = step.Shards;
        if (step.Iron > 0) q.Takes[Iron] = step.Iron;
        if (step.Material > 0) q.Takes[PeoplesMaterial(c.People)] = step.Material;
        if (step.Gold > 0 || step.GoldPerTier > 0) q.Gold = Price(x, q.Crafter, step.Gold + step.GoldPerTier * c.Tier);
        (q.HeatLo, q.HeatHi) = (step.Heat[0], step.Heat[1]);
        return q;
    }

    /// <summary>Its ink set: nothing more is worked on it; it can only be run.</summary>
    static void ChartHot(ItemInstance it, Quote q)
    {
        if (q.Blocked == null && q.HeatHi > 0 && ChartHeatLeft(it) <= 0) q.Blocked = "Its ink has set. Nothing more can be worked on it; it can only be run.";
    }

    /// <summary>Ink: a mod added at random on the side chosen, the foe's (what strengthens them) or the
    /// survivor's (what weakens you); each pays in what is found.</summary>
    public static Quote Ink(CraftCtx x, ItemInstance it, bool foe, string? crafter = null)
    {
        var q = ChartQuote(Verb.Ink, it, foe ? "Ink the foe's side" : "Ink your side", crafter, Rules.Charts.Ink, x);
        if (it.Chart is not { } c) return q;
        q.Affix = foe ? "foe" : "you";
        q.After = foe ? "a mod at random that strengthens them" : "a mod at random that weakens you";
        if (c.Rolled.Count(m => m.Prefix == foe) >= Rules.Charts.PerSide)
            q.Blocked = $"Three on {(foe ? "the foe's" : "your")} side already: scrape one first.";
        else if (!Charts.All.Any(m => m.Prefix == foe && Charts.Fits(c, m))) q.Blocked = "Nothing more fits that side.";
        ChartHot(it, q);
        Afford(x, q);
        return q;
    }

    /// <summary>Burn and redraw: every mod but the pinned one rerolled, as many on each side as before.</summary>
    public static Quote Burn(CraftCtx x, ItemInstance it, string? crafter = null)
    {
        var q = ChartQuote(Verb.Burn, it, "Burn and redraw", crafter, Rules.Charts.Burn, x);
        if (it.Chart is not { } c) return q;
        q.After = c.Pinned != null ? $"every mod but “{Charts.Mod(c.Pinned).Name}” drawn again" : "every mod drawn again";
        if (c.Mods.All(m => m == c.Pinned)) q.Blocked = c.Mods.Count == 0 ? "A plain chart: nothing on it to burn. Ink it first." : "Only the pinned mod is on it.";
        ChartHot(it, q);
        Afford(x, q);
        return q;
    }

    /// <summary>Pin: one mod held through a redraw (one pin a chart: a new pin moves it).</summary>
    public static Quote Pin(CraftCtx x, ItemInstance it, string mod, string? crafter = null)
    {
        var q = ChartQuote(Verb.Pin, it, "Pin it", crafter, Rules.Charts.Pin, x);
        if (it.Chart is not { } c) return q;
        q.Affix = mod;
        q.After = c.Pinned is { } was && was != mod ? $"held through a redraw; the pin on “{Charts.Mod(was).Name}” comes out" : "held through a redraw";
        if (!c.Mods.Contains(mod)) q.Blocked = "That is not on the chart.";
        else if (c.Pinned == mod) q.Blocked = "It is pinned already.";
        ChartHot(it, q);
        Afford(x, q);
        return q;
    }

    /// <summary>Scrape: one chosen mod taken off with a blade's edge.</summary>
    public static Quote Scrape(CraftCtx x, ItemInstance it, string mod, string? crafter = null)
    {
        var q = ChartQuote(Verb.Scrape, it, "Scrape it off", crafter, Rules.Charts.Scrape, x);
        if (it.Chart is not { } c) return q;
        q.Affix = mod;
        q.Before = c.Mods.Contains(mod) ? Charts.Mod(mod).Says : null;
        q.After = "gone from the chart, and what it paid with it";
        if (!c.Mods.Contains(mod)) q.Blocked = "That is not on the chart.";
        ChartHot(it, q);
        Afford(x, q);
        return q;
    }

    /// <summary>Annotate: a fifth more found, to a fifth in all; written in from another chart of the same
    /// people's ground, which is given up. Spends no heat.</summary>
    public static Quote Annotate(CraftCtx x, ItemInstance it, ItemInstance? from, string? crafter = null)
    {
        var r = Rules.Charts;
        var q = ChartQuote(Verb.Annotate, it, "Annotate", crafter, r.Annotate, x);
        if (it.Chart is not { } c) return q;
        q.Donor = from?.Uid;
        q.After = $"{Math.Min(r.QualityMax, c.Quality + r.QualityStep)}% more found";
        if (c.Quality >= r.QualityMax) q.Blocked = $"As full of notes as a chart gets: {r.QualityMax}% more found.";
        else if (from?.Chart is not { } f || from.Uid == it.Uid || f.People != c.People) q.Blocked = $"Another chart of {Ground(c.People)} to write from.";
        else if (!Inventory.Holds(x.Ch, from.Uid)) q.Blocked = "Carry it with you.";
        Afford(x, q);
        return q;
    }

    /// <summary>Another chart of the same people's ground, carried, to annotate from (the plainest first).</summary>
    public static ItemInstance? AnnotateFrom(CharacterData ch, ItemInstance it) =>
        it.Chart is { } c ? ch.Satchel.Where(p => p.Chart is { } f && p.Uid != it.Uid && f.People == c.People).OrderBy(p => p.Chart!.Rarity).ThenBy(p => p.Chart!.Tier).FirstOrDefault() : null;

    /// <summary>A chart's rarity follows what is written on it: plain, fine to two mods, rare from three.</summary>
    static void Rerate(ItemInstance it, Chart c)
    {
        c.Rarity = c.Mods.Count == 0 ? 0 : c.Mods.Count <= 2 ? 1 : 2;
        it.Rarity = c.Rarity;
    }

    static void AddSide(Chart c, Rng rng, bool foe)
    {
        var pool = Charts.All.Where(m => m.Prefix == foe && Charts.Fits(c, m)).ToList();
        if (pool.Count > 0) c.Mods.Add(pool[rng.Int(0, pool.Count - 1)].Id);
    }

    /// <summary>A chart verb done (from Do, after the takes and gold are paid): what it spends of the heat.</summary>
    static int ChartDone(ItemInstance it, Quote q, Rng rng, CharacterData ch)
    {
        var c = it.Chart!;
        it.Heat ??= ChartHeat(c);
        it.HeatFull ??= ChartHeat(c);
        switch (q.Verb)
        {
            case Verb.Ink:
                AddSide(c, rng, q.Affix == "foe");
                break;
            case Verb.Burn:
            {
                int pre = c.Rolled.Count(m => m.Prefix && m.Id != c.Pinned), suf = c.Rolled.Count(m => !m.Prefix && m.Id != c.Pinned);
                c.Mods.RemoveAll(m => m != c.Pinned);
                for (int k = 0; k < pre; k++) AddSide(c, rng, true);
                for (int k = 0; k < suf; k++) AddSide(c, rng, false);
                break;
            }
            case Verb.Pin:
                c.Pinned = q.Affix;
                break;
            case Verb.Scrape:
                c.Mods.Remove(q.Affix!);
                if (c.Pinned == q.Affix) c.Pinned = null;
                break;
            case Verb.Annotate:
                c.Quality = Math.Min(Rules.Charts.QualityMax, c.Quality + Rules.Charts.QualityStep);
                Inventory.Remove(ch, q.Donor!);
                return 0;
        }
        Rerate(it, c);
        return q.HeatLo == q.HeatHi ? q.HeatLo : rng.Int(q.HeatLo, q.HeatHi);
    }
}
