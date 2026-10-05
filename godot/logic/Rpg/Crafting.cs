using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Rpg;

/* What the Waystation's hands make of what the night leaves (docs/CRAFTING_DESIGN.md).
 *
 * Three things go into anything made here: iron (old iron, from breaking down
 * what is not kept) for a piece's body, the world's own (pelts, hide, cloth,
 * dust, ember, herbs) for its kind, and fire (ember shards carried out of the
 * night) for the ember's shape and the heat to work it again. Every piece has
 * a life, its heat: each craft spends some, shown before the hammer falls, and
 * at none the piece is set. Nothing is ever broken by a craft.
 *
 * Every craft is quoted first (what it takes, the heat it may cost, the line
 * before and after) and only then done, so the screen and the tests read the
 * same numbers. The numbers are data (data/content/crafting.json). */

public enum Verb { Temper, WorkIn, Cage, Remake, Rekindle, BreakDown, Brew, Buy, Commission, Set, Bind, Steep, Mark, Ink, Burn, Pin, Scrape, Annotate }

public sealed class CraftStep { public int Iron, Gold, GoldPerRarity; public int[] Heat = { 0, 0 }; }
public sealed class CageRules { public int Shards = 4, Gold = 30, Redraw = 1, Offered = 3, MinRarity = 2; public int[] Heat = { 5, 7 }; }
public sealed class RekindleRules { public int Shards = 3, Gold = 20, GoldStep = 20; }
/// <summary>What a material is worked into, how many it takes, who works it, and what the world can tell.</summary>
public sealed class MaterialRule { public int Qty = 1; public List<string> Into = new(); public string Crafter = "brannoc"; public string? Marks; }
/// <summary>A crafter's better terms, while the condition holds. Needs says the standing in
/// words where the condition is more than one ("trust or affection 30").</summary>
public sealed class Easier { public Cond? When; public int HeatTop, TemperIron, EntryGrade, Gold; public string? Line, Needs; }
/// <summary>The binder's terms: a shard and gold a grade bound, and the heat it costs the piece that takes it.</summary>
public sealed class BindRules { public int ShardsPerGrade = 1, GoldPerGrade = 40; public int[] Heat = { 5, 7 }; public string Crafter = "vonnra"; }
/// <summary>What a map's ruler leaves (its people's thing, carrying its Mark at a grade), and what
/// inscribing one costs at Vonnra's table (design 20.3).</summary>
public sealed class MarkRules
{
    public string Crafter = "vonnra";
    public int Gold = 60, GoldPerGrade = 30, Shards = 2, Worn = 3;
    public int[] Heat = { 5, 7 };
    /// <summary>A ruler's chance to leave it, and the grade it comes at: a grade every few tiers, sometimes one more.</summary>
    public double Chance = 0.5, Finer = 0.3;
    public int TiersPerGrade = 3;
    /// <summary>By people: the thing its ruler leaves, and the Mark in it.</summary>
    public Dictionary<string, MarkDrop> Drops = new();
}
public sealed class MarkDrop { public string Item = "", Mark = ""; }
/// <summary>Rook's shelves (the storeroom grows by shelves of 24): the price of each after the first, then
/// of every one beyond those, and the most there can be.</summary>
public sealed class RookLines { public string? Shelf, ShelfMore; }
public sealed class ShelfRules { public string Seller = "rook"; public List<int> Prices = new() { 300, 1000, 2500 }; public int Then = 5000, Most = 8; }
/// <summary>The one gamble (design 9): jars sold while the pump runs, and what steeping does, by weight.</summary>
public sealed class SlurryRules
{
    public string Jar = "slurry_jar", Crafter = "snib", Mark = "slurried";
    public int Gold = 30, PerDay = 3;
    public Cond? Sold;
    public Dictionary<string, int> Odds = new() { ["up"] = 25, ["affix"] = 25, ["nothing"] = 30, ["down"] = 20 };
    public List<string> Affixes = new();
}
/// <summary>Where one of a crafter's verbs opens later than the crafter does (Wenna's
/// tinctures, after the stream's cure), and what they say until it does.</summary>
public sealed class Gate { public Cond? When; public string? Line; }
/// <summary>A draught brewed: what it takes, the gold, who brews it, and the crafter's lines for it
/// (Say: its own lines in turn, "brew.antidote"; Moment: a line said the first time, "brew.moonpetal").</summary>
public sealed class BrewRule { public string Draught = ""; public Dictionary<string, int> Takes = new(); public int Gold; public string Crafter = "wenna"; public string? Say, Moment; }
/// <summary>Wenna's flask: bought once at her still-room; the inn tops the survivor's draughts up to
/// a number while they sleep, a material a draught (The Witcher's refill: no brewing chore).</summary>
public sealed class FlaskRules { public string Item = "wennas_flask", Draught = "health_draught", Material = "bitterroot", Crafter = "wenna"; public int Per = 1, Upto = 3, Gold = 120; }
/// <summary>A base the smith can make from nothing, and the standing it asks (Calling: the
/// weapons of the survivor's calling).</summary>
public sealed class Pattern { public string? Id; public bool Calling; public Cond? When; public string? Needs; }
/// <summary>"Make me one": a new piece, ready the next morning.</summary>
public sealed class CommissionRules { public string Crafter = "brannoc"; public int Iron = 2, Rarity = 1, Days = 1; public List<Pattern> Patterns = new(); }
/// <summary>A trophy set into a piece: a power of its own, outside the seams (Greymuzzle's
/// fang), and what the world can tell of it. Moment keys its lines ("fang.set", "history.fang").</summary>
public sealed class SettingRule { public string Affix = "", Crafter = "brannoc", Moment = "fang"; public string? Mark; public List<ItemKind> Kinds = new(); public int Gold; }
public sealed class CrafterDef
{
    public string Name = "", Place = "";
    public List<string> Verbs = new();
    /// <summary>When they will work for the survivor at all; when not right now (the forge banked).</summary>
    public Cond? When, Closed;
    public string? ClosedLine;
    /// <summary>Their regard rises with work brought, a little a craft, to a limit (the smith's
    /// respect; the herbalist's affection).</summary>
    public int RespectPerCraft, RespectFromCraft;
    public Axis Grows = Axis.Respect;
    public List<Easier> Easier = new();
    /// <summary>Verbs that open later than the crafter does, by the verb's key.</summary>
    public Dictionary<string, Gate> Gates = new();
    /// <summary>For a crafter who is not one of the town's people (no person to draw): the creature
    /// they are drawn as at their bench (Snib, a lampling).</summary>
    public string? Visual;
    /// <summary>What they say (the story lead's words, in data): "greet" on sitting down at
    /// their bench; a verb's key ("temper") after that craft, in turn; "first.VERB" the first
    /// time, with "first.VERB.before" and ".after" as narration round it; "history.VERB" the
    /// line a craft writes on the piece ({who}, {day}, {night}).</summary>
    public Dictionary<string, List<string>> Lines = new();
}

/// <summary>What a crafter said over a craft: narration before, their words, narration after.</summary>
public sealed record Said(string? Before, string? Line, string? After);
public sealed class NightPeople { public string Family = "", Material = ""; public int Per = 150; }
public sealed class NightRules
{
    public int EmberFrom = 10, EmberPer = 8, MinutesPer = 2, StoryBonus = 2, Cap = 8, Miniboss = 2;
    /// <summary>The scars' depth (design 20.5): past this many minutes beyond the win, a shard a minute; past
    /// GlassFrom, once the stream is cured, scar-glass, one and another each GlassEvery minutes more.</summary>
    public int DeepFrom = 30, GlassFrom = 60, GlassEvery = 60;
    public string Glass = "scar_glass";
    /// <summary>Said at the night's end the first time scar-glass is carried out (the story lead's).</summary>
    public string? GlassFirst;
    public double FellKeeps = 0.5;
    public Dictionary<string, List<NightPeople>> Peoples = new();
}

public sealed class CraftingRules
{
    public List<int> Heat = new();
    public double HeatSpread = 0.2;
    public List<int> BreakDown = new();
    public List<CraftStep> Temper = new();
    public CraftStep WorkIn = new();
    public CageRules Cage = new();
    public List<CraftStep> Remake = new();
    public int RemakeCap = 3, RemakeHeat = 4;
    public RekindleRules Rekindle = new();
    public List<BrewRule> Brews = new();
    public FlaskRules Flask = new();
    public CommissionRules Commission = new();
    /// <summary>Trophies that can be set into a piece, by the trophy's item id.</summary>
    public Dictionary<string, SettingRule> Settings = new();
    public BindRules Bind = new();
    public MarkRules Mark = new();
    public ChartRules Charts = new();
    public ShelfRules Shelves = new();
    /// <summary>Rook's words over a shelf sold: the first, then any after (the story lead's).</summary>
    public RookLines Rook = new();
    public SlurryRules Slurry = new();
    public Dictionary<string, MaterialRule> Materials = new();
    public Dictionary<string, CrafterDef> Crafters = new();
    public NightRules Night = new();
}

/// <summary>A craft as it would be done: what it takes, the heat it may cost, what the piece
/// will read after, and why it cannot be done now (null if it can).</summary>
public sealed class Quote
{
    public Verb Verb;
    public string Crafter = "";
    public string Title = "";
    public Dictionary<string, int> Takes = new();
    public int Gold, HeatLo, HeatHi;
    public string? Blocked;
    /// <summary>The affix line before and after (null where there is none).</summary>
    public string? Before, After;
    /// <summary>The affix place it works on (-1: an open seam).</summary>
    public int Index = -1;
    /// <summary>The affix that goes in (work in, a coal).</summary>
    public string? Affix;
    public string? Material;
    /// <summary>The piece a binding unmakes for its power.</summary>
    public string? Donor;
    /// <summary>What a gamble came to, once done ("up", "affix", "nothing", "down").</summary>
    public string? Outcome;
    /// <summary>What is made (a draught brewed, a base commissioned, a trophy set) and how many.</summary>
    public string? Def;
    public int Count = 1;
    /// <summary>The grade an affix goes in at (work in), when the crafter's standing lifts it.</summary>
    public int Grade = -1;
    /// <summary>Old iron and shards it gives back (breaking down).</summary>
    public Dictionary<string, int> Gives = new();
    public bool Ok => Blocked == null;
}

/// <summary>Where a craft is done: the world and the survivor, and the prices the crafter
/// asks of them (a smith who distrusts you charges more).</summary>
public sealed class CraftCtx
{
    public Ctx Ctx;
    public Func<string, double> PriceMod;
    public CraftCtx(Ctx ctx, Func<string, double>? priceMod = null) { Ctx = ctx; PriceMod = priceMod ?? (_ => 1); }
    public CharacterData Ch => Ctx.Ch;
    public WorldState World => Ctx.World;
}

public static partial class Crafting
{
    public const string Iron = "old_iron", Shard = "ember_shard";

    static CraftingRules? rules;
    public static CraftingRules Rules => rules ??= Json.Parse<CraftingRules>(Json.ReadContent("crafting.json"));

    /* ------------------------------------------------------------ pieces -- */

    /// <summary>Plain bases and weapons can be worked; a named piece only if it is one of
    /// the Waystation's own (the wolfhide cloak). Somebody else's work is left be.</summary>
    public static bool Workable(ItemDef def) =>
        def.Kind is ItemKind.Weapon or ItemKind.Offhand or ItemKind.Head or ItemKind.Body or ItemKind.Cloak or ItemKind.Amulet or ItemKind.Ring or ItemKind.Relic
        && (def.Base || def.Weapon != null || def.Workable)
        // A Legendary or a set piece is somebody's work, never the forge's (docs/design/LOOT_DESIGN.md §9).
        && def.Rarity < 4 && def.Set == null;

    public static bool Workable(ItemInstance it) => Items.Find(it.Def) is { } d && Workable(d) && it.Heat != null;

    static int RarityIx(int rarity) => Math.Clamp(rarity, 0, Rules.Heat.Count - 1);

    /// <summary>The heat a piece is made with: its rarity's figure, or within a fifth of it
    /// either way where it fell in the world.</summary>
    public static int HeatAtMaking(int rarity, Rng? roll = null)
    {
        int h = Rules.Heat[RarityIx(rarity)];
        if (roll == null) return h;
        return Math.Max(1, (int)Math.Round(h * (1 - Rules.HeatSpread + roll.Next() * 2 * Rules.HeatSpread)));
    }

    /// <summary>Affix places: as many as a drop of its rarity rolls.</summary>
    public static int Seams(ItemInstance it) => Math.Min(3, Math.Max(0, it.Rarity));
    public static int OpenSeams(ItemInstance it) => Math.Max(0, Seams(it) - it.Affixes.Count);
    /// <summary>The highest grade the forge raises an affix to here: what the best drop of its rarity rolls.</summary>
    public static int Cap(ItemInstance it) => Math.Clamp(it.Rarity, 0, 3);
    /// <summary>The grade a worked-in affix enters at: the piece's own quality lifts it.</summary>
    public static int EntryGrade(ItemInstance it) => Math.Clamp(it.Rarity - 2, 0, 3);
    public static string Grade(int tier) => tier switch { 0 => "I", 1 => "II", 2 => "III", 3 => "IV", _ => "V" };
    /// <summary>The bright grade (V): past every forge, given only by the slurry (design 5.1, 9).</summary>
    public const int Bright = 4;

    static string Line(string affix, int tier) => Items.Affix(affix)?.Text(tier) ?? affix;

    /// <summary>"an epic", "a rare".</summary>
    public static string Article(string word) => (word.Length > 0 && "aeiou".Contains(char.ToLowerInvariant(word[0])) ? "an " : "a ") + word;

    static bool Fits(ItemDef def, string affix) => Items.Affix(affix) is { } a && a.Slots.Contains(def.Kind);

    /* ---------------------------------------------------------- crafters -- */

    public static CrafterDef? Crafter(string id) => Rules.Crafters.GetValueOrDefault(id);

    /// <summary>Why a crafter will not work for the survivor now, or not at that verb yet (null: they will).</summary>
    public static string? Closed(string crafter, Ctx c, Verb? v = null)
    {
        var d = Crafter(crafter);
        if (d == null) return "Nobody here does that.";
        if (!World.Rules.Test(d.When, c)) return d.ClosedLine ?? $"{d.Name} will not work for you yet.";
        if (d.Closed != null && World.Rules.Test(d.Closed, c)) return d.ClosedLine ?? $"{d.Name} is not working now.";
        if (v is Verb verb && d.Gates.TryGetValue(verb.Key(), out var g) && !World.Rules.Test(g.When, c)) return g.Line ?? $"{d.Name} will not do that yet.";
        return null;
    }

    public static bool Does(string crafter, Verb v) => Crafter(crafter)?.Verbs.Contains(v.Key()) == true;

    /// <summary>One of a crafter's lines for a moment, the pick-th in turn (null if none written).</summary>
    public static string? Line(string crafter, string key, int pick = 0) =>
        Crafter(crafter)?.Lines.GetValueOrDefault(key) is { Count: > 0 } l ? l[Math.Abs(pick) % l.Count] : null;

    /// <summary>What the crafter says over a craft just done: the first time each verb is done for
    /// the survivor, its own line (and narration); after, the verb's lines in turn.</summary>
    public static Said? Speak(CraftCtx x, string crafter, Verb v, string? moment = null, string? say = null)
    {
        if (Crafter(crafter) is null) return null;
        string key = v.Key();
        var n = x.World.Npc(crafter);
        // A moment of its own, said once ("brew.moonpetal": the first moonpetal draught).
        if (moment != null && !n.Flag($"said.{moment}").Truthy && Line(crafter, moment) is { } once)
        {
            n.Flags[$"said.{moment}"] = true;
            n.Flags[$"first.{key}"] = true;
            return new Said(Line(crafter, $"{moment}.before"), once, Line(crafter, $"{moment}.after"));
        }
        string flag = $"first.{key}";
        if (!n.Flag(flag).Truthy && Line(crafter, flag) is { } first)
        {
            n.Flags[flag] = true;
            return new Said(Line(crafter, $"{flag}.before"), first, Line(crafter, $"{flag}.after"));
        }
        n.Flags[flag] = true;
        return Line(crafter, say != null && Line(crafter, say) != null ? say : key, (int)n.Flag("crafted").Number) is { } l ? new Said(null, l, null) : null;
    }

    /// <summary>The line a craft writes on a piece, in the crafter's hand if they have one.</summary>
    static string History(CraftCtx x, string crafter, string key, string fallback) => History(x.World, crafter, key, fallback);

    /// <summary>The same, for a piece made in a conversation (Maeca's braid: a "made" give).</summary>
    public static string History(WorldState w, string crafter, string key, string fallback = "Made by {who}, day {day}")
    {
        string who = Crafter(crafter)?.Name ?? crafter;
        // The night the coal came out of: what lets Act 3 name it.
        string night = w.Fact("shards.from").Str is { Length: > 0 } s ? (s.StartsWith("The ") ? "the " + s[4..] : s) : "the night";
        return (Line(crafter, $"history.{key}") ?? fallback).Replace("{who}", who).Replace("{day}", $"{w.Day}").Replace("{night}", night);
    }

    static (int HeatTop, int TemperIron, int EntryGrade) Terms(string crafter, Ctx c)
    {
        int h = 0, i = 0, g = 0;
        foreach (var e in Crafter(crafter)?.Easier ?? new())
            if (World.Rules.Test(e.When, c)) { h += e.HeatTop; i += e.TemperIron; g += e.EntryGrade; }
        return (h, i, g);
    }

    /// <summary>What the crafter's terms take off their prices, as a share (-0.1: a tenth less).</summary>
    static double GoldTerms(string crafter, Ctx c) =>
        (Crafter(crafter)?.Easier ?? new()).Where(e => e.Gold != 0 && World.Rules.Test(e.When, c)).Sum(e => e.Gold) / 100.0;

    /// <summary>A crafter's terms, those given now and those still to earn: each with what it
    /// does and the standing it asks ("respect 20"), so the forge can show the way up.</summary>
    public static List<(string Line, string Effect, string? Needs, bool Met)> TermLadder(string crafter, Ctx c)
    {
        var o = new List<(string, string, string?, bool)>();
        foreach (var e in Crafter(crafter)?.Easier ?? new())
        {
            var fx = new List<string>();
            if (e.HeatTop < 0) fx.Add($"his crafts cost up to {-e.HeatTop} heat less");
            if (e.TemperIron < 0) fx.Add($"tempering takes {Items.Several(Iron, -e.TemperIron)} less");
            if (e.EntryGrade > 0) fx.Add($"what is worked in goes in {e.EntryGrade} grade{(e.EntryGrade > 1 ? "s" : "")} finer");
            if (e.Gold < 0) fx.Add(e.Gold == -10 ? "a tenth off every price" : $"{-e.Gold}% off every price");
            string? needs = e.Needs ?? (e.When?.Rel is { Gte: double g } r ? $"{r.Axis.ToString().ToLowerInvariant()} {g:0}" : null);
            o.Add((e.Line ?? "", string.Join("; ", fx), needs, World.Rules.Test(e.When, c)));
        }
        return o;
    }

    /// <summary>What the crafter's terms are now, in words.</summary>
    public static List<string> TermLines(string crafter, Ctx c) =>
        (Crafter(crafter)?.Easier ?? new()).Where(e => e.Line != null && World.Rules.Test(e.When, c)).Select(e => e.Line!).ToList();

    static int Price(CraftCtx x, string crafter, int gold) =>
        gold <= 0 ? 0 : Math.Max(1, (int)Math.Ceiling(gold * x.PriceMod(crafter) * (1 + GoldTerms(crafter, x.Ctx))));

    /* ----------------------------------------------------------- quotes -- */

    static Quote Begin(Verb v, string crafter, string title) => new() { Verb = v, Crafter = crafter, Title = title };

    /// <summary>Takes and gold the survivor lacks, and the piece's own limits, as the reason it cannot be done.</summary>
    static void Afford(CraftCtx x, Quote q)
    {
        if (q.Blocked != null) return;
        // A banked forge quotes, so the survivor can plan by night, but does nothing.
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is { } shut) { q.Blocked = shut; return; }
        foreach (var (m, n) in q.Takes)
            if (Inventory.Count(x.Ch, m) < n) { q.Blocked = $"Needs {Items.Several(m, n)}; you have {Inventory.Count(x.Ch, m)}."; return; }
        if (x.Ch.Gold < q.Gold) q.Blocked = $"{q.Gold} gold; you have {Math.Floor(x.Ch.Gold)}.";
    }

    static void Hot(ItemInstance it, Quote q)
    {
        if (q.Blocked != null) return;
        if (it.Heat is not int h) q.Blocked = "That's somebody's work. Leave it be.";
        else if (h <= 0) q.Blocked = "It's set. Nothing more can be worked into it.";
    }

    static (int Lo, int Hi) HeatRange(int[] r, int top) => (r[0], Math.Max(r[0], r[1] + top));

    /// <summary>Temper: one affix up a grade, to the piece's cap.</summary>
    public static Quote Temper(CraftCtx x, ItemInstance it, int index, string crafter = "brannoc")
    {
        var q = Begin(Verb.Temper, crafter, "Temper");
        q.Index = index;
        var (top, less, _) = Terms(crafter, x.Ctx);
        if (index < 0 || index >= it.Affixes.Count) { q.Blocked = "Choose what to temper."; return q; }
        var a = it.Affixes[index];
        var def = Items.Affix(a.Id);
        q.Affix = a.Id;
        q.Before = Line(a.Id, a.Tier);
        Hot(it, q);
        if (q.Blocked != null) return q;
        if (def?.Kindled != null || def?.Grants != null) { q.Blocked = "A coal or a worn skill has no grades."; return q; }
        if (def?.Mark == true) { q.Blocked = "A mark is as fine as what it came from. A finer one comes from a harder map."; return q; }
        if (a.Tier >= Cap(it)) { q.Blocked = $"Grade {Grade(a.Tier)} is as high as {Article(Inventory.RarityName(it).ToLowerInvariant())} piece goes."; return q; }
        var step = Rules.Temper[Math.Clamp(a.Tier, 0, Rules.Temper.Count - 1)];
        q.After = Line(a.Id, a.Tier + 1);
        q.Title = $"Temper to grade {Grade(a.Tier + 1)}";
        q.Takes[Iron] = Math.Max(1, step.Iron + less);
        q.Gold = Price(x, crafter, step.Gold);
        (q.HeatLo, q.HeatHi) = HeatRange(step.Heat, top);
        Hot(it, q);
        Afford(x, q);
        return q;
    }

    /// <summary>The materials this piece could have worked in, with what each would make of it.</summary>
    public static List<(string Material, string Affix)> WorkInChoices(ItemInstance it, string crafter = "brannoc")
    {
        var def = Items.Get(it.Def);
        var o = new List<(string, string)>();
        foreach (var (m, r) in Rules.Materials)
            if (r.Crafter == crafter)
                foreach (var a in r.Into)
                    if (Fits(def, a)) o.Add((m, a));
        return o;
    }

    /// <summary>Work in: a material becomes its answer, in an open seam or in place of an affix (lost).</summary>
    public static Quote WorkIn(CraftCtx x, ItemInstance it, string material, string affix, int replace = -1, string crafter = "brannoc")
    {
        var q = Begin(Verb.WorkIn, crafter, "Work in");
        q.Material = material;
        q.Affix = affix;
        q.Index = replace;
        var def = Items.Get(it.Def);
        if (!Rules.Materials.TryGetValue(material, out var r) || !r.Into.Contains(affix) || r.Crafter != crafter) { q.Blocked = "That doesn't go in that way."; return q; }
        if (!Fits(def, affix)) { q.Blocked = "It doesn't take to that kind of piece."; return q; }
        var (top, _, finer) = Terms(crafter, x.Ctx);
        int tier = q.Grade = Math.Min(Math.Max(Cap(it), EntryGrade(it)), EntryGrade(it) + finer);
        q.Title = $"Work in {Items.Find(material)?.Name ?? material}";
        q.After = Line(affix, tier);
        if (replace >= 0)
        {
            if (replace >= it.Affixes.Count) { q.Blocked = "Choose what to work it in over."; return q; }
            q.Before = Line(it.Affixes[replace].Id, it.Affixes[replace].Tier);
        }
        else if (OpenSeams(it) == 0) q.Blocked = Seams(it) == 0 ? "No seam to work it into: have it remade first." : "No open seam: choose what it goes in over.";
        if (it.Affixes.Where((a, i) => i != replace).Any(a => a.Id == affix)) q.Blocked ??= "It already has that.";
        q.Takes[material] = r.Qty;
        q.Gold = Price(x, crafter, Rules.WorkIn.Gold + Rules.WorkIn.GoldPerRarity * Math.Max(0, it.Rarity));
        (q.HeatLo, q.HeatHi) = HeatRange(Rules.WorkIn.Heat, top);
        Hot(it, q);
        Afford(x, q);
        return q;
    }

    static uint Hash(string s)
    {
        uint h = 2166136261;
        foreach (char ch in s) { h ^= ch; h *= 16777619; }
        return h;
    }

    /// <summary>The stand-ins the survivor's skills evolve with: the skills carried by day and
    /// the gear's own weapons (a coal for their recipe comes twice as often).</summary>
    public static HashSet<string> Wanted(CharacterData ch)
    {
        var ids = SkillBook.Carried(ch).Select(w => w.Id).ToList();
        foreach (var s in Items.EquipSlots)
            if (ch.Equipment[s] is { } it && Items.Find(it.Def)?.Weapon is { } w) ids.Add(w.Id);
        return ids.SelectMany(id => Sim.LevelUp.EvolvesWith(id).SelectMany(e => e.Passives)).Select(p => $"stand:{p}").ToHashSet();
    }

    /// <summary>The coals offered for this piece today: three kindled affixes that fit it (not
    /// the one it holds), drawn afresh each day or for a shard.</summary>
    public static List<string> Coals(CharacterData ch, ItemInstance it, int day)
    {
        var def = Items.Get(it.Def);
        var held = it.Affixes.Select(a => a.Id).ToHashSet();
        var pool = Items.Affixes.Where(a => a.Kindled != null && a.Slots.Contains(def.Kind) && !held.Contains(a.Id)).ToList();
        var wanted = Wanted(ch);
        var rng = new Rng(Hash(it.Uid) ^ (uint)(day * 7919) ^ (uint)((it.Draw ?? 0) * 104729 + 17));
        var o = new List<string>();
        while (o.Count < Rules.Cage.Offered && pool.Count > 0)
        {
            var a = rng.Weighted(pool, x => wanted.Contains(x.Kindled!) ? 2 : 1);
            pool.Remove(a);
            o.Add(a.Id);
        }
        return o;
    }

    /// <summary>Where a coal goes: the seam its old coal held, else an open seam, else the place chosen.</summary>
    public static int CoalPlace(ItemInstance it, int replace) =>
        it.Affixes.FindIndex(a => Items.Affix(a.Id)?.Kindled != null) is int k && k >= 0 ? k : OpenSeams(it) > 0 ? -1 : replace;

    /// <summary>Cage a coal: a kindled affix that shapes the night's draft (docs/SKILLS_DESIGN.md 10.1).</summary>
    public static Quote Cage(CraftCtx x, ItemInstance it, string affix, int replace = -1, string crafter = "brannoc")
    {
        var q = Begin(Verb.Cage, crafter, "Cage a coal");
        q.Affix = affix;
        var def = Items.Get(it.Def);
        var a = Items.Affix(affix);
        if (it.Rarity < Rules.Cage.MinRarity) q.Blocked = "Too plain a piece to hold a coal: rare and up.";
        else if (a?.Kindled == null || !Fits(def, affix)) q.Blocked = "That coal won't sit in this piece.";
        else if (!Coals(x.Ch, it, x.World.Day).Contains(affix)) q.Blocked = "That coal isn't one of the three on offer.";
        int at = CoalPlace(it, replace);
        q.Index = at;
        if (q.Blocked == null && at < 0 && OpenSeams(it) == 0) q.Blocked = "Choose what the coal goes in over.";
        if (q.Blocked == null && at >= it.Affixes.Count) q.Blocked = "Choose what the coal goes in over.";
        if (at >= 0 && at < it.Affixes.Count) q.Before = Line(it.Affixes[at].Id, it.Affixes[at].Tier);
        q.After = a?.Text(0);
        var (top, _, _) = Terms(crafter, x.Ctx);
        q.Takes[Shard] = Rules.Cage.Shards;
        q.Gold = Price(x, crafter, Rules.Cage.Gold);
        (q.HeatLo, q.HeatHi) = HeatRange(Rules.Cage.Heat, top);
        Hot(it, q);
        Afford(x, q);
        return q;
    }

    /// <summary>Three more coals to choose from, for a shard.</summary>
    public static Quote Redraw(CraftCtx x, ItemInstance it, string crafter = "brannoc")
    {
        var q = Begin(Verb.Cage, crafter, "Three more coals");
        q.Takes[Shard] = Rules.Cage.Redraw;
        if (it.Rarity < Rules.Cage.MinRarity) q.Blocked = "Too plain a piece to hold a coal: rare and up.";
        Hot(it, q);
        Afford(x, q);
        return q;
    }

    /// <summary>Remake: the piece made again on a better pattern; a seam opens, the heat rises.</summary>
    public static Quote Remake(CraftCtx x, ItemInstance it, string crafter = "brannoc")
    {
        var q = Begin(Verb.Remake, crafter, "Remake");
        int to = it.Rarity + 1;
        if (it.Heat == null) { q.Blocked = "That's somebody's work. Leave it be."; return q; }
        // A remake brings heat back: a steeped piece stays as the slurry set it.
        if (Slurried(it)) { q.Blocked = SetForGood; return q; }
        if (to > Rules.RemakeCap) { q.Blocked = "There's no better pattern he knows. Not yet."; return q; }
        // Remade iron cools overnight: one remake a piece a day (it also spreads a weapon's climb over days).
        bool cooling = it.Remade == x.World.Day;
        var step = Rules.Remake[Math.Clamp(to - 1, 0, Rules.Remake.Count - 1)];
        q.Title = $"Remake as {Items.RarityNames[to].ToLowerInvariant()}";
        q.Takes[Iron] = step.Iron;
        q.Gold = Price(x, crafter, step.Gold);
        q.HeatLo = q.HeatHi = -(Rules.Heat[RarityIx(to)] - Rules.Heat[RarityIx(it.Rarity)]);
        var def = Items.Get(it.Def);
        q.After = def.Weapon != null && def.Weapon.Rank + (to - def.Rarity) <= Inventory.GearRankCap
            ? $"A seam opens; it comes into the night a rank higher" : "A seam opens";
        if (cooling) q.Blocked = "Remade this morning. Iron wants a night to cool. Tomorrow.";
        Afford(x, q);
        return q;
    }

    /// <summary>Rekindle: heat back, half the piece's full heat; each time dearer.</summary>
    public static Quote Rekindle(CraftCtx x, ItemInstance it, string crafter = "brannoc")
    {
        var q = Begin(Verb.Rekindle, crafter, "Rekindle");
        if (it.Heat is not int h || it.HeatFull is not int full) { q.Blocked = "That's somebody's work. Leave it be."; return q; }
        if (Slurried(it)) { q.Blocked = SetForGood; return q; }
        int n = it.Rekindled ?? 0;
        int add = (full + 1) / 2;
        q.Takes[Shard] = Rules.Rekindle.Shards << Math.Min(n, 8);
        q.Gold = Price(x, crafter, Rules.Rekindle.Gold + Rules.Rekindle.GoldStep * n);
        q.HeatLo = q.HeatHi = -add;
        q.After = $"Heat {h} to {Math.Min(full, h + add)} of {full}";
        if (h >= full) q.Blocked = "It's as hot as it gets.";
        Afford(x, q);
        return q;
    }

    /// <summary>Break down: old iron for a piece not kept (and a shard back for a coal in it).</summary>
    public static Quote BreakDown(CraftCtx x, ItemInstance it, string crafter = "")
    {
        var q = Begin(Verb.BreakDown, crafter, "Break down");
        var def = Items.Get(it.Def);
        bool gear = Items.SlotFor(def) != null;
        int iron = Rules.BreakDown[RarityIx(it.Rarity)];
        if (!gear) q.Blocked = "Only gear breaks down.";
        else if (def.Unique || it.Rarity >= 5) q.Blocked = "You can't bring yourself to.";
        else if (iron <= 0) q.Blocked = "Nothing in it worth the breaking.";
        else if (Inventory.Find(x.Ch, it.Uid) is not { InPack: true }) q.Blocked = "Take it off first.";
        q.Gives[Iron] = iron;
        int coals = it.Affixes.Count(a => Items.Affix(a.Id)?.Kindled != null);
        if (coals > 0) q.Gives[Shard] = coals;
        return q;
    }

    /* --------------------------------------------------- the still-room -- */

    public static BrewRule? BrewOf(string draught) => Rules.Brews.FirstOrDefault(b => b.Draught == draught);

    /// <summary>The draughts a crafter brews, in the order they are shown.</summary>
    public static IEnumerable<BrewRule> Brews(string crafter) => Rules.Brews.Where(b => b.Crafter == crafter);

    /// <summary>Brew: draughts from what the survivor brings, cheaper than the shop's, never
    /// stronger (design 12.1: brewing makes them cheaper, not better).</summary>
    public static Quote Brew(CraftCtx x, string draught, int count = 1)
    {
        var r = BrewOf(draught);
        var q = Begin(Verb.Brew, r?.Crafter ?? "", "Brew");
        q.Def = draught;
        q.Count = count = Math.Max(1, count);
        if (r == null) { q.Blocked = "Nobody here brews that."; return q; }
        foreach (var (m, n) in r.Takes) q.Takes[m] = n * count;
        q.Gold = Price(x, r.Crafter, r.Gold) * count;
        q.Gives[draught] = count;
        q.After = Items.Get(draught).Description;
        if (Inventory.Room(x.Ch, draught) < count) q.Blocked = "No room in your pack for it.";
        Afford(x, q);
        return q;
    }

    /// <summary>How many of a draught could be brewed now, up to a limit (for "brew five").</summary>
    public static int CanBrew(CraftCtx x, string draught, int most)
    {
        int n = 0;
        while (n < most && Brew(x, draught, n + 1).Ok) n++;
        return n;
    }

    public static bool HasFlask(CharacterData ch) => Inventory.Count(ch, Rules.Flask.Item) > 0;

    /// <summary>Wenna's flask: bought once; from then on the inn keeps the survivor's draughts topped up.</summary>
    public static Quote BuyFlask(CraftCtx x)
    {
        var f = Rules.Flask;
        var q = Begin(Verb.Buy, f.Crafter, "Her flask");
        q.Def = f.Item;
        q.Gold = Price(x, f.Crafter, f.Gold);
        q.Gives[f.Item] = 1;
        if (HasFlask(x.Ch)) q.Blocked = "You have it.";
        else if (Inventory.Room(x.Ch, f.Item) < 1) q.Blocked = "No room in your pack for it.";
        Afford(x, q);
        return q;
    }

    /// <summary>A night at the inn with the flask: the draughts topped up to the flask's number, a
    /// material each. How many were filled, and whether it ran dry (some were wanted, none filled).</summary>
    public static (int Filled, bool Dry) Refill(CharacterData ch)
    {
        var f = Rules.Flask;
        if (!HasFlask(ch)) return (0, false);
        int want = Math.Max(0, f.Upto - Inventory.Count(ch, f.Draught)), n = 0;
        while (n < want && Inventory.Count(ch, f.Material) >= f.Per && Inventory.Room(ch, f.Draught) > 0)
        {
            Inventory.Take(ch, f.Material, f.Per);
            Inventory.AddToPack(ch, Inventory.Make(ch, f.Draught));
            n++;
        }
        return (n, want > 0 && n == 0);
    }

    /* ------------------------------------------------------- commissions -- */

    /// <summary>The bases the smith can make, each with whether his respect opens it yet and what it asks.</summary>
    public static List<(string Def, bool Open, string? Needs)> Patterns(CraftCtx x)
    {
        var o = new List<(string Def, bool Open, string? Needs)>();
        foreach (var p in Rules.Commission.Patterns)
        {
            bool open = World.Rules.Test(p.When, x.Ctx);
            var ids = p.Calling ? Callings.Archetype(x.Ch.Archetype).Weapons : p.Id != null ? new List<string> { p.Id } : new();
            foreach (var id in ids)
                if (Items.Find(id) != null && o.All(e => e.Def != id)) o.Add((id, open, open ? null : p.Needs));
        }
        return o;
    }

    /// <summary>What a commission makes, before it is made: the piece as it will come off the anvil.</summary>
    public static ItemInstance Pattern(string def, string affix) =>
        new() { Def = def, Rarity = Rules.Commission.Rarity, Affixes = new() { new AffixRoll { Id = affix, Tier = 0 } } };

    /// <summary>What is on the smith's bench for the survivor, and the day it is ready (null: nothing).</summary>
    public static (string Def, string Affix, string Material, int Ready)? Ordered(WorldState w) =>
        w.Fact("commission.def").Str is { Length: > 0 } d
            ? (d, w.Fact("commission.affix").Str ?? "", w.Fact("commission.material").Str ?? "", (int)w.Fact("commission.ready").Number)
            : null;

    /// <summary>"Make me one": a base the smith knows and a material's answer in it, Uncommon, its
    /// affix at grade I and its heat full, ready the next morning (C20: the wait is part of it).</summary>
    public static Quote Commission(CraftCtx x, string def, string material, string affix)
    {
        var c = Rules.Commission;
        var q = Begin(Verb.Commission, c.Crafter, "Make it");
        q.Def = def;
        q.Material = material;
        q.Affix = affix;
        var d = Items.Find(def);
        var pat = Patterns(x).FirstOrDefault(p => p.Def == def);
        if (d == null || pat.Def == null) { q.Blocked = "He doesn't know that pattern."; return q; }
        if (!Rules.Materials.TryGetValue(material, out var r) || r.Crafter != c.Crafter || !r.Into.Contains(affix) || !Fits(d, affix)) { q.Blocked = "That doesn't go in that way."; return q; }
        var made = Pattern(def, affix);
        q.After = $"{Inventory.Name(made)}: {Line(affix, 0)}";
        q.Takes[material] = r.Qty;
        q.Takes[Iron] = c.Iron;
        // What the finished piece would fetch at the shop (Journey.Value's rule): the work is the price.
        q.Gold = Price(x, c.Crafter, (int)Math.Round(d.Value * (1 + 0.6 * Math.Max(0, c.Rarity - d.Rarity)) * 1.15));
        if (!pat.Open) q.Blocked = $"He'll make that at {pat.Needs}.";
        else if (Ordered(x.World) != null) q.Blocked = "He has one on his bench for you already.";
        Afford(x, q);
        return q;
    }

    /// <summary>A new morning: a commission due today is done, and shows over the smith's head.</summary>
    public static void Morning(WorldState w)
    {
        if (Ordered(w) is { } o && w.Day >= o.Ready) w.Facts["commission.done"] = true;
    }

    /// <summary>The morning after: what was ordered, handed over (null if nothing is ready, or the pack
    /// is full and it waits on the bench).</summary>
    public static ItemInstance? Collect(CraftCtx x)
    {
        if (Ordered(x.World) is not { } o || x.World.Day < o.Ready || Items.Find(o.Def) == null) return null;
        var c = Rules.Commission;
        var it = Inventory.Make(x.Ch, o.Def, rarity: c.Rarity, affixes: new() { new AffixRoll { Id = o.Affix, Tier = 0 } });
        if (!Inventory.AddToPack(x.Ch, it)) return null;
        if (Rules.Materials.GetValueOrDefault(o.Material)?.Marks is { } mark) (it.Marks ??= new()).Add(mark);
        (it.History ??= new()).Add(History(x, c.Crafter, "commission", "Made for you by {who}, day {day}"));
        foreach (var k in new[] { "commission.def", "commission.affix", "commission.material", "commission.ready", "commission.done" }) x.World.Facts.Remove(k);
        return it;
    }

    /* ---------------------------------------------------------- settings -- */

    /// <summary>The trophies the survivor carries that this crafter could set into this piece.</summary>
    public static List<string> Settable(CharacterData ch, ItemInstance it, string crafter = "brannoc") =>
        Rules.Settings.Where(kv => kv.Value.Crafter == crafter && Inventory.Count(ch, kv.Key) > 0 && kv.Value.Kinds.Contains(Items.Get(it.Def).Kind))
            .Select(kv => kv.Key).ToList();

    /// <summary>Set a trophy into a piece: its power goes in outside the seams, spends no heat, and the
    /// world can tell (Greymuzzle's fang: the Pack knows it by sight).</summary>
    public static Quote Set(CraftCtx x, ItemInstance it, string trophy, string crafter = "brannoc")
    {
        var q = Begin(Verb.Set, crafter, "Set it");
        q.Def = trophy;
        if (!Rules.Settings.TryGetValue(trophy, out var s) || s.Crafter != crafter) { q.Blocked = "Nobody here sets that."; return q; }
        q.Affix = s.Affix;
        q.After = Line(s.Affix, 0);
        if (!s.Kinds.Contains(Items.Get(it.Def).Kind)) q.Blocked = "It won't sit in this kind of piece.";
        else if (!Workable(it)) q.Blocked = "That's somebody's work. Leave it be.";
        else if (it.Setting != null) q.Blocked = "Something is set in it already.";
        q.Takes[trophy] = 1;
        q.Gold = Price(x, crafter, s.Gold);
        Afford(x, q);
        return q;
    }

    /* ----------------------------------------------------------- binding -- */

    /// <summary>A power that can be lifted out of one piece into another: a plain affix. Coals are
    /// the forge's, a worn skill is its piece's, a trophy's power and the slurry's will not let go.</summary>
    public static bool Bindable(AffixDef? d) => d != null && d.Kindled == null && d.Grants == null && !d.Unique;

    /// <summary>What the survivor carries that could give this piece a power: each piece in the pack and
    /// the place of a bindable affix in it that this kind of piece takes.</summary>
    public static List<(ItemInstance Donor, int Index)> Donors(CharacterData ch, ItemInstance it)
    {
        var kind = Items.Get(it.Def).Kind;
        var o = new List<(ItemInstance, int)>();
        foreach (var d in ch.Pack)
        {
            if (d == null || d.Uid == it.Uid || Items.SlotFor(Items.Get(d.Def)) == null) continue;
            for (int k = 0; k < d.Affixes.Count; k++)
                if (Items.Affix(d.Affixes[k].Id) is { } a && Bindable(a) && a.Slots.Contains(kind)) o.Add((d, k));
        }
        return o;
    }

    /// <summary>Bind: one power lifted out of a donor and set in this piece at the donor's grade (to this
    /// piece's cap), in an open seam or in place of a chosen affix. The donor is unmade (design 7.3).</summary>
    public static Quote Bind(CraftCtx x, ItemInstance it, ItemInstance donor, int donorIndex, int replace = -1, string? crafter = null)
    {
        var r = Rules.Bind;
        crafter ??= r.Crafter;
        var q = Begin(Verb.Bind, crafter, "Bind");
        q.Donor = donor.Uid;
        q.Index = replace;
        if (donorIndex < 0 || donorIndex >= donor.Affixes.Count) { q.Blocked = "Choose what to lift out of it."; return q; }
        var roll = donor.Affixes[donorIndex];
        var a = Items.Affix(roll.Id);
        q.Affix = roll.Id;
        q.Grade = Math.Min(roll.Tier, Math.Max(Cap(it), 0));
        q.After = Line(roll.Id, q.Grade);
        if (a?.Kindled != null) { q.Blocked = Line(crafter, "bind.caged") ?? "That one is caged. It will not come out."; return q; }
        if (!Bindable(a)) { q.Blocked = "That will not let go of what holds it."; return q; }
        if (!Fits(Items.Get(it.Def), roll.Id)) { q.Blocked = "It doesn't take to that kind of piece."; return q; }
        if (replace >= 0)
        {
            if (replace >= it.Affixes.Count) { q.Blocked = "Choose what it goes in over."; return q; }
            q.Before = Line(it.Affixes[replace].Id, it.Affixes[replace].Tier);
        }
        else if (OpenSeams(it) == 0) q.Blocked = Seams(it) == 0 ? "No seam to hold it: have it remade first." : "No open seam: choose what it goes in over.";
        if (it.Affixes.Where((b, i) => i != replace).Any(b => b.Id == roll.Id)) q.Blocked ??= "It already has that.";
        if (Inventory.Find(x.Ch, donor.Uid) is not { InPack: true }) q.Blocked ??= "Take it off first: what gives its power is unmade.";
        var (top, _, _) = Terms(crafter, x.Ctx);
        q.Takes[Shard] = r.ShardsPerGrade * (q.Grade + 1);
        q.Gold = Price(x, crafter, r.GoldPerGrade * (q.Grade + 1));
        (q.HeatLo, q.HeatHi) = HeatRange(r.Heat, top);
        Hot(it, q);
        Afford(x, q);
        return q;
    }

    /* ------------------------------------------------------- item level -- */

    /// <summary>The chance a piece made at this level rolls the finer of its rarity's two grades: an even
    /// coin at a first map's level (10, as by day), rising a fortieth a level to nine in ten (design 20.3).</summary>
    public static double FinerGrade(int level) => Math.Clamp(0.5 + (level - 10) * 0.025, 0.5, 0.9);

    /* ---------------------------------------------------------- shelves -- */

    /// <summary>What Rook asks for the storeroom's next shelf (her prices follow how she feels about you),
    /// or null if it has as many as it can hold. Priced against the economy: the second is about a
    /// Kerchief night's gold, the third and fourth the atlas's, the rest a long sink.</summary>
    public static int? ShelfPrice(CraftCtx x)
    {
        var r = Rules.Shelves;
        int have = x.World.Shelves;
        if (have >= r.Most) return null;
        int k = have - 1;
        return Price(x, r.Seller, k < r.Prices.Count ? r.Prices[k] : r.Then);
    }

    /// <summary>The next shelf bought, paid for and empty (false if it cannot be).</summary>
    public static bool BuyShelf(CraftCtx x)
    {
        if (ShelfPrice(x) is not int gold || x.Ch.Gold < gold) return false;
        x.Ch.Gold -= gold;
        for (int i = 0; i < World.WorldState.Shelf; i++) x.World.Stash.Add(null);
        return true;
    }

    /// <summary>What Rook says over the shelf just sold: the second shelf's line, then the later ones'.</summary>
    public static string? ShelfSaid(WorldState w) => w.Shelves <= 2 ? Rules.Rook.Shelf : Rules.Rook.ShelfMore ?? Rules.Rook.Shelf;

    /* ------------------------------------------------------------- marks -- */

    /// <summary>The Mark a ruler's thing carries, or null if it holds none.</summary>
    public static AffixRoll? MarkIn(ItemInstance it) =>
        Items.Get(it.Def).Kind == ItemKind.Trophy ? it.Affixes.FirstOrDefault(a => Items.Affix(a.Id)?.Mark == true) : null;

    /// <summary>The Mark a ruler's thing is made with (by its item id), or null.</summary>
    public static string? MarkOf(string item) => Rules.Mark.Drops.Values.FirstOrDefault(d => d.Item == item)?.Mark;

    /// <summary>The things carried that hold a Mark, finest first.</summary>
    public static List<ItemInstance> MarksCarried(CharacterData ch) =>
        ch.Satchel.Concat(ch.Pack.Where(p => p != null).Select(p => p!)).Where(p => MarkIn(p) != null).OrderByDescending(p => MarkIn(p)!.Tier).ToList();

    /// <summary>What a map's ruler leaves of its own (null: nothing this time): its people's thing, at a
    /// grade by the map's tier (a grade every few tiers, now and then one finer), to VI.</summary>
    public static (string Item, int Grade)? RulerMark(string people, int tier, Rng rng)
    {
        var r = Rules.Mark;
        if (!r.Drops.TryGetValue(people, out var d) || rng.Next() >= r.Chance) return null;
        int g = Math.Clamp((tier - 1) / Math.Max(1, r.TiersPerGrade) + (rng.Next() < r.Finer ? 1 : 0), 0, 5);
        return (d.Item, g);
    }

    /// <summary>Inscribe: the Mark in a ruler's thing written into the chosen piece at that thing's grade,
    /// in an open seam or in place of a chosen power; one Mark to a piece, so a second goes where the
    /// first was. The thing is used up. Vonnra's, from the binders' book (design 20.3).</summary>
    public static Quote Inscribe(CraftCtx x, ItemInstance it, ItemInstance from, int replace = -1, string? crafter = null)
    {
        var r = Rules.Mark;
        crafter ??= r.Crafter;
        var q = Begin(Verb.Mark, crafter, "Inscribe");
        q.Donor = from.Uid;
        if (MarkIn(from) is not { } m) { q.Blocked = "There is no mark in that."; return q; }
        (q.Affix, q.Grade, q.After) = (m.Id, m.Tier, Line(m.Id, m.Tier));
        if (!Fits(Items.Get(it.Def), m.Id)) { q.Blocked = "It doesn't take to that kind of piece."; return q; }
        int held = it.Affixes.FindIndex(a => Items.Affix(a.Id)?.Mark == true);
        q.Index = held >= 0 ? held : replace;
        if (q.Index >= it.Affixes.Count) q.Blocked = "Choose what it goes in over.";
        else if (q.Index >= 0) q.Before = Line(it.Affixes[q.Index].Id, it.Affixes[q.Index].Tier);
        else if (OpenSeams(it) == 0) q.Blocked = Seams(it) == 0 ? "No seam to hold it: have it remade first." : "No open seam: choose what it goes in over.";
        if (!Inventory.Holds(x.Ch, from.Uid)) q.Blocked ??= "Carry it with you.";
        var (top, _, _) = Terms(crafter, x.Ctx);
        q.Takes[Shard] = r.Shards;
        q.Gold = Price(x, crafter, r.Gold + r.GoldPerGrade * m.Tier);
        (q.HeatLo, q.HeatHi) = HeatRange(r.Heat, top);
        Hot(it, q);
        Afford(x, q);
        return q;
    }

    /* ----------------------------------------------------------- the slurry -- */

    public static bool Slurried(ItemInstance it) => it.Marks?.Contains(Rules.Slurry.Mark) == true;

    /// <summary>What a steeping is done with: a jar of Snib's while one is carried, else the scars' glass.</summary>
    public static string SteepWith(CharacterData ch) =>
        Inventory.Count(ch, Rules.Slurry.Jar) > 0 || Inventory.Count(ch, Rules.Night.Glass) == 0 ? Rules.Slurry.Jar : Rules.Night.Glass;

    /// <summary>Something carried to steep with by hand (a jar, or scar-glass).</summary>
    public static bool CanSteep(CharacterData ch) => Inventory.Count(ch, Rules.Slurry.Jar) + Inventory.Count(ch, Rules.Night.Glass) > 0;

    /// <summary>Why a steeped piece takes no more heat: the slurry's setting is for good (design 9), or
    /// a rekindle or a remake would open it again for the forge.</summary>
    public const string SetForGood = "Steeped: the slurry set it for good. No heat will open it again.";

    /// <summary>Snib sells jars while the pump runs and he has been met: three a day.</summary>
    public static Quote BuyJar(CraftCtx x)
    {
        var s = Rules.Slurry;
        var q = Begin(Verb.Buy, s.Crafter, "A jar");
        q.Def = s.Jar;
        q.Gold = Price(x, s.Crafter, s.Gold);
        q.Gives[s.Jar] = 1;
        var w = x.World;
        int sold = (int)w.Fact("slurry.day").Number == w.Day ? (int)w.Fact("slurry.sold").Number : 0;
        if (!World.Rules.Test(s.Sold, x.Ctx)) q.Blocked = "Nobody is selling it.";
        else if (sold >= s.PerDay) q.Blocked = Line(s.Crafter, "jar.none") ?? "No more today.";
        if (q.Blocked == null && x.Ch.Gold < q.Gold) q.Blocked = $"{q.Gold} gold; you have {Math.Floor(x.Ch.Gold)}.";
        return q;
    }

    /// <summary>How many jars Snib will still sell today.</summary>
    public static int JarsLeft(WorldState w) =>
        Math.Max(0, Rules.Slurry.PerDay - ((int)w.Fact("slurry.day").Number == w.Day ? (int)w.Fact("slurry.sold").Number : 0));

    /// <summary>A jar bought: paid, in the pouch, and counted against the day's three.</summary>
    public static bool Buy(CraftCtx x, Quote q)
    {
        if (!q.Ok || q.Def != Rules.Slurry.Jar || x.Ch.Gold < q.Gold) return false;
        var w = x.World;
        int sold = (int)w.Fact("slurry.day").Number == w.Day ? (int)w.Fact("slurry.sold").Number : 0;
        x.Ch.Gold -= q.Gold;
        Inventory.AddToPack(x.Ch, Inventory.Make(x.Ch, q.Def, 1));
        w.Facts["slurry.day"] = w.Day;
        w.Facts["slurry.sold"] = sold + 1;
        return true;
    }

    /// <summary>Steep: a piece in a jar of the Dig's slurry, by the survivor's own hand. One affix past the
    /// forge's cap (to the bright grade), a slurry affix past the seams, only the veins, or a grade lost;
    /// then it is set for good (design 9). Said in full before the jar is opened.</summary>
    public static Quote Steep(CraftCtx x, ItemInstance it, string crafter = "")
    {
        var s = Rules.Slurry;
        // At Snib's bench he does it, in his words; from the pack, by the survivor's own hand (a jar
        // kept past the cure still steeps).
        var q = Begin(Verb.Steep, crafter, "Steep in slurry");
        q.Takes[SteepWith(x.Ch)] = 1;
        if (!Workable(it)) q.Blocked = "That's somebody's work. Leave it be.";
        else if (Slurried(it)) q.Blocked = "It has been steeped. Once is all it takes.";
        else if (Seams(it) == 0) q.Blocked = "Too plain a piece: there is nothing in it for the slurry to take.";
        else if (Inventory.Count(x.Ch, SteepWith(x.Ch)) < 1) q.Blocked = "You have no slurry.";
        q.HeatLo = q.HeatHi = it.Heat ?? 0;
        q.After = "It is set for good after, whatever it comes to.";
        if (q.Blocked == null && crafter != "" && Closed(crafter, x.Ctx, Verb.Steep) is { } shut) q.Blocked = shut;
        return q;
    }

    /// <summary>What a steeping came to, said plainly (the story's narration says how it looked):
    /// which power moved and to what, the power it gained, or nothing but the veins; and how it
    /// went (1 a gain, -1 a loss, 0 nothing), for the colour it is said in.</summary>
    public static (string Text, int Mood) Outcome(ItemInstance it, Quote q)
    {
        string name = q.Affix != null ? Items.Affix(q.Affix)?.Name ?? q.Affix : "";
        return q.Outcome switch
        {
            "up" when q.Grade >= Bright => ($"{name} rose to the bright grade, past every forge: {q.After}", 1),
            "up" => ($"{name} rose past what the forge can do: grade {Grade(q.Grade)}, {q.After}", 1),
            "down" => ($"{name} gave a grade: {q.Before} to {q.After}", -1),
            "affix" => ($"{name}, past its seams: {q.After}", 1),
            _ => ("Only the veins: nothing else in it changed.", 0),
        };
    }

    /// <summary>What each outcome means, in a few words, for the card that offers the jar.</summary>
    public static string OddsWords(string outcome) => outcome switch
    {
        "up" => "one power past what the forge can do",
        "affix" => "a slurry power past its seams, strong, with a price",
        "nothing" => "only the veins",
        _ => "one power a grade lower",
    };

    /// <summary>The chances of each outcome, as shares of one (for the card that says them).</summary>
    public static IEnumerable<(string Outcome, double Chance)> Odds()
    {
        double total = Math.Max(1, Rules.Slurry.Odds.Values.Sum());
        return Rules.Slurry.Odds.Select(kv => (kv.Key, kv.Value / total));
    }

    static void Steeped(CraftCtx x, ItemInstance it, Quote q, Rng rng)
    {
        var s = Rules.Slurry;
        string pick = rng.Weighted(s.Odds.Keys.ToList(), k => s.Odds[k]);
        var plain = it.Affixes.Select((a, i) => (a, i)).Where(p => Bindable(Items.Affix(p.a.Id))).ToList();
        // Nothing in it to raise or lower: what would have happened to an affix happens past the seams.
        if (pick is "up" or "down" && plain.Count == 0) pick = pick == "up" ? "affix" : "nothing";
        // What it came to is kept on the quote (which power, and its line before and after), so the
        // bench and the pack can say it plainly and ring the seam it touched.
        q.Index = -1;
        q.Before = q.After = null;
        switch (pick)
        {
            case "up":
            {
                // Past what the forge can do (design 9): one power to a grade above the piece's cap, or a
                // grade finer if it was there already; the bright grade is the last. The lowest-raised
                // first would be kind; the slurry is not: any of them that can still rise.
                var rising = plain.Where(p => p.a.Tier < Bright).ToList();
                if (rising.Count == 0) { pick = "nothing"; break; }
                var (a, i) = rising[rng.Int(0, rising.Count - 1)];
                q.Before = Line(a.Id, a.Tier);
                a.Tier = Math.Min(Bright, Math.Max(a.Tier + 1, Cap(it) + 1));
                (q.Affix, q.Index, q.Grade, q.After) = (a.Id, i, a.Tier, Line(a.Id, a.Tier));
                break;
            }
            case "down":
            {
                var (a, i) = plain[rng.Int(0, plain.Count - 1)];
                if (a.Tier <= 0) { pick = "nothing"; break; }
                q.Before = Line(a.Id, a.Tier);
                a.Tier--;
                (q.Affix, q.Index, q.Grade, q.After) = (a.Id, i, a.Tier, Line(a.Id, a.Tier));
                break;
            }
            case "affix":
            {
                var pool = s.Affixes.Where(id => Items.Affix(id) is { } d && d.Slots.Contains(Items.Get(it.Def).Kind) && it.Affixes.All(b => b.Id != id)).ToList();
                if (pool.Count == 0) { pick = "nothing"; break; }
                var id = pool[rng.Int(0, pool.Count - 1)];
                it.Affixes.Add(new AffixRoll { Id = id, Tier = 0 });
                (q.Affix, q.Index, q.Grade, q.After) = (id, it.Affixes.Count - 1, 0, Line(id, 0));
                break;
            }
        }
        q.Outcome = pick;
        it.Heat = 0;
        (it.Marks ??= new()).Add(s.Mark);
        (it.History ??= new()).Add(History(x, s.Crafter, "steep", "Steeped in the Dig's slurry, day {day}"));
    }

    /* ------------------------------------------------------------- doing -- */

    /// <summary>Do a quoted craft that makes something new rather than working a piece: a brew, the
    /// flask, a commission put on the bench. False if it could not be done.</summary>
    public static bool Make(CraftCtx x, Quote q)
    {
        if (!q.Ok || q.Verb is not (Verb.Brew or Verb.Buy or Verb.Commission)) return false;
        if (q.Verb == Verb.Buy && q.Def == Rules.Slurry.Jar) return Buy(x, q);
        var ch = x.Ch;
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;
        foreach (var (m, n) in q.Takes) if (Inventory.Count(ch, m) < n) return false;
        foreach (var (m, n) in q.Gives) if (Inventory.Room(ch, m) < n) return false;
        if (ch.Gold < q.Gold || q.Verb == Verb.Commission && Ordered(x.World) != null) return false;
        foreach (var (m, n) in q.Takes) Inventory.Take(ch, m, n);
        ch.Gold -= q.Gold;
        foreach (var (m, n) in q.Gives)
            for (int k = 0; k < n; k++) Inventory.AddToPack(ch, Inventory.Make(ch, m));
        if (q.Verb == Verb.Commission)
        {
            var w = x.World;
            int ready = w.Day + Rules.Commission.Days;
            w.Facts["commission.def"] = q.Def;
            w.Facts["commission.affix"] = q.Affix;
            w.Facts["commission.material"] = q.Material;
            w.Facts["commission.ready"] = ready;
        }
        if (q.Verb != Verb.Buy) Worked(x, q.Crafter);
        return true;
    }

    /// <summary>Do what was quoted (quoted afresh, so the numbers are the ones the survivor
    /// saw). The heat spent is rolled in the quoted range; at none the piece is set. False if
    /// it could not be done.</summary>
    public static bool Do(CraftCtx x, ItemInstance it, Quote q, Rng rng)
    {
        if (!q.Ok) return false;
        var ch = x.Ch;
        if (q.Verb == Verb.BreakDown)
        {
            if (Inventory.Find(ch, it.Uid) is not { InPack: true } loc) return false;
            ch.Pack[loc.Index] = null;
            foreach (var (m, n) in q.Gives) Inventory.AddToPack(ch, Inventory.Make(ch, m, n));
            return true;
        }
        if (q.Verb is Verb.Brew or Verb.Buy or Verb.Commission) return Make(x, q);
        if (q.Verb == Verb.Steep)
        {
            string with = q.Takes.Keys.FirstOrDefault() ?? Rules.Slurry.Jar;
            if (Inventory.Count(ch, with) < 1 || Slurried(it) || q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;
            Inventory.Take(ch, with, 1);
            Steeped(x, it, q, rng);
            return true;
        }
        if (q.Verb is Verb.Bind && (q.Donor == null || Inventory.Find(ch, q.Donor) is not { InPack: true })) return false;
        if (q.Verb is Verb.Mark or Verb.Annotate && (q.Donor == null || !Inventory.Holds(ch, q.Donor))) return false;
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;
        foreach (var (m, n) in q.Takes) if (Inventory.Count(ch, m) < n) return false;
        if (ch.Gold < q.Gold) return false;
        foreach (var (m, n) in q.Takes) Inventory.Take(ch, m, n);
        ch.Gold -= q.Gold;
        // A chart is worked on its own terms (CraftingCharts.cs): its mods, not seams.
        if (q.Verb is Verb.Ink or Verb.Burn or Verb.Pin or Verb.Scrape or Verb.Annotate)
        {
            if (it.Chart == null) return false;
            int spent = ChartDone(it, q, rng, ch);
            it.Heat = Math.Max(0, (it.Heat ?? 0) - spent);
            Worked(x, q.Crafter);
            return true;
        }
        int cost = q.HeatLo == q.HeatHi ? q.HeatLo : rng.Int(q.HeatLo, q.HeatHi);
        switch (q.Verb)
        {
            case Verb.Temper:
                it.Affixes[q.Index].Tier++;
                break;
            case Verb.WorkIn:
            {
                var roll = new AffixRoll { Id = q.Affix!, Tier = q.Grade >= 0 ? q.Grade : EntryGrade(it) };
                if (q.Index >= 0) it.Affixes[q.Index] = roll; else it.Affixes.Add(roll);
                if (q.Material != null && Rules.Materials.GetValueOrDefault(q.Material)?.Marks is { } mark && !(it.Marks?.Contains(mark) ?? false))
                    (it.Marks ??= new()).Add(mark);
                break;
            }
            case Verb.Cage when q.Affix == null:
                it.Draw = (it.Draw ?? 0) + 1;
                return true;
            case Verb.Cage:
            {
                var roll = new AffixRoll { Id = q.Affix, Tier = 0 };
                if (q.Index >= 0) it.Affixes[q.Index] = roll; else it.Affixes.Add(roll);
                it.Draw = 0;
                (it.History ??= new()).Add(History(x, q.Crafter, "cage", "A coal from {night}, caged by {who}, day {day}"));
                break;
            }
            case Verb.Remake:
            {
                int add = -cost;
                it.Rarity++;
                it.Remade = x.World.Day;
                it.Heat = (it.Heat ?? 0) + add;
                it.HeatFull = (it.HeatFull ?? 0) + add;
                (it.History ??= new()).Add(History(x, q.Crafter, "remake", "Remade by {who}, day {day}"));
                cost = 0;
                break;
            }
            case Verb.Rekindle:
                it.Heat = Math.Min(it.HeatFull ?? 0, (it.Heat ?? 0) - cost);
                it.Rekindled = (it.Rekindled ?? 0) + 1;
                cost = 0;
                break;
            case Verb.Bind:
            {
                var roll = new AffixRoll { Id = q.Affix!, Tier = q.Grade };
                if (q.Index >= 0) it.Affixes[q.Index] = roll; else it.Affixes.Add(roll);
                // The donor is unmade: held over the lamp until it lets go.
                var d = Inventory.Find(ch, q.Donor!)!;
                ch.Pack[d.Index] = null;
                (it.History ??= new()).Add(History(x, q.Crafter, "bind", "Bound by {who}, day {day}"));
                break;
            }
            case Verb.Mark:
            {
                var roll = new AffixRoll { Id = q.Affix!, Tier = q.Grade };
                if (q.Index >= 0) it.Affixes[q.Index] = roll; else it.Affixes.Add(roll);
                // The ruler's thing is used up: what it held is written into the piece.
                Inventory.Remove(ch, q.Donor!);
                (it.History ??= new()).Add(History(x, q.Crafter, "mark", "Marked by {who}, day {day}"));
                break;
            }
            case Verb.Set:
            {
                var s = Rules.Settings[q.Def!];
                it.Setting = s.Affix;
                if (s.Mark != null && !(it.Marks?.Contains(s.Mark) ?? false)) (it.Marks ??= new()).Add(s.Mark);
                (it.History ??= new()).Add(History(x, q.Crafter, s.Moment, "Set by {who}, day {day}"));
                cost = 0;
                break;
            }
        }
        if (cost > 0) it.Heat = Math.Max(0, (it.Heat ?? 0) - cost);
        Worked(x, q.Crafter);
        return true;
    }

    /// <summary>A crafter likes being brought work: a little respect a craft, to a limit.</summary>
    static void Worked(CraftCtx x, string crafter)
    {
        if (Crafter(crafter) is not { RespectPerCraft: > 0 } d) return;
        var n = x.World.Npc(crafter);
        double done = n.Flag("crafted").Number;
        n.Flags["crafted"] = done + 1;
        if (done * d.RespectPerCraft < d.RespectFromCraft) n[d.Grows] = Math.Min(100, n[d.Grows] + d.RespectPerCraft);
    }

    /* ---------------------------------------------------------- the night -- */

    /// <summary>What a survivor carries out of an arena, and what they spilled falling.</summary>
    public sealed record NightYield(Dictionary<string, int> Kept, Dictionary<string, int> Spilled);

    /// <summary>What a night among a people can leave in the fist (Night's materials), in the
    /// order a table says them: ember shards, then the people's own.</summary>
    public static List<string> NightMaterials(string people) =>
        new[] { Shard }.Concat((Rules.Night.Peoples.GetValueOrDefault(people) ?? new()).Select(p => p.Material)).Distinct().ToList();

    /// <summary>Ember shards for the ember reached, the tier, the minutes stayed past the half
    /// hour and a story fight won; the people's own for their champions slain. A fall keeps half.</summary>
    public static NightYield Night(string people, int tier, bool story, int ember, double minutesPast, bool won, bool fell,
        IReadOnlyDictionary<Family, int> champions, IReadOnlyDictionary<Family, int>? minibosses = null, bool cured = false)
    {
        var r = Rules.Night;
        var all = new Dictionary<string, int>();
        void Add(string m, int n) { if (n > 0) all[m] = all.GetValueOrDefault(m) + n; }
        // Past the win the scar keeps paying: a shard every two minutes, then from its deep a shard a minute.
        double past = Math.Max(0, minutesPast);
        int deep = won ? (int)Math.Floor(Math.Min(past, r.DeepFrom) / Math.Max(1, r.MinutesPer)) + (int)Math.Floor(Math.Max(0, past - r.DeepFrom)) : 0;
        Add(Shard, Math.Max(0, ember - r.EmberFrom) / Math.Max(1, r.EmberPer) + Math.Max(0, tier - 1) + deep + (won && story ? r.StoryBonus : 0));
        // The slurry's heir: with the stream cured the jars are gone, but a scar stayed in past the hour
        // gives glass with the same gamble in it (earned by staying, not bought).
        if (won && cured && past >= r.GlassFrom) Add(r.Glass, 1 + (int)((past - r.GlassFrom) / Math.Max(1, r.GlassEvery)));
        foreach (var p in r.Peoples.GetValueOrDefault(people) ?? new())
            if (EnumKey<Family>.TryParse(p.Family, out var fam))
                // The champions' tally, to the cap; a miniboss of the people carries out two more besides.
                Add(p.Material, Math.Min(r.Cap, champions.GetValueOrDefault(fam) / Math.Max(1, p.Per)) + r.Miniboss * (minibosses?.GetValueOrDefault(fam) ?? 0));
        var kept = new Dictionary<string, int>();
        var spilled = new Dictionary<string, int>();
        foreach (var (m, n) in all)
        {
            int k = fell ? (int)Math.Floor(n * r.FellKeeps) : n;
            if (k > 0) kept[m] = k;
            if (n - k > 0) spilled[m] = n - k;
        }
        return new NightYield(kept, spilled);
    }
}
