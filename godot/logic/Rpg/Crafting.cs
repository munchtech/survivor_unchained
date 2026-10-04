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

public enum Verb { Temper, WorkIn, Cage, Remake, Rekindle, BreakDown }

public sealed class CraftStep { public int Iron, Gold, GoldPerRarity; public int[] Heat = { 0, 0 }; }
public sealed class CageRules { public int Shards = 4, Gold = 30, Redraw = 1, Offered = 3, MinRarity = 2; public int[] Heat = { 5, 7 }; }
public sealed class RekindleRules { public int Shards = 3, Gold = 20, GoldStep = 20; }
/// <summary>What a material is worked into, how many it takes, who works it, and what the world can tell.</summary>
public sealed class MaterialRule { public int Qty = 1; public List<string> Into = new(); public string Crafter = "brannoc"; public string? Marks; }
/// <summary>A crafter's better terms, while the condition holds.</summary>
public sealed class Easier { public Cond? When; public int HeatTop, TemperIron; public string? Line; }
public sealed class CrafterDef
{
    public string Name = "", Place = "";
    public List<string> Verbs = new();
    /// <summary>When they will work for the survivor at all; when not right now (the forge banked).</summary>
    public Cond? When, Closed;
    public string? ClosedLine;
    /// <summary>Their respect rises with work brought, a little a craft, to a limit.</summary>
    public int RespectPerCraft, RespectFromCraft;
    public List<Easier> Easier = new();
}
public sealed class NightPeople { public string Family = "", Material = ""; public int Per = 150; }
public sealed class NightRules
{
    public int EmberFrom = 10, EmberPer = 8, MinutesPer = 2, StoryBonus = 2, Cap = 8;
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

public static class Crafting
{
    public const string Iron = "old_iron", Shard = "ember_shard";

    static CraftingRules? rules;
    public static CraftingRules Rules => rules ??= Json.Parse<CraftingRules>(Json.ReadContent("crafting.json"));

    /* ------------------------------------------------------------ pieces -- */

    /// <summary>Plain bases and weapons can be worked; a named piece only if it is one of
    /// the Waystation's own (the wolfhide cloak). Somebody else's work is left be.</summary>
    public static bool Workable(ItemDef def) =>
        def.Kind is ItemKind.Weapon or ItemKind.Offhand or ItemKind.Head or ItemKind.Body or ItemKind.Cloak or ItemKind.Amulet or ItemKind.Ring or ItemKind.Relic
        && (def.Base || def.Weapon != null || def.Workable);

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

    static string Line(string affix, int tier) => Items.Affix(affix)?.Text(tier) ?? affix;

    static bool Fits(ItemDef def, string affix) => Items.Affix(affix) is { } a && a.Slots.Contains(def.Kind);

    /* ---------------------------------------------------------- crafters -- */

    public static CrafterDef? Crafter(string id) => Rules.Crafters.GetValueOrDefault(id);

    /// <summary>Why a crafter will not work for the survivor now (null: they will).</summary>
    public static string? Closed(string crafter, Ctx c)
    {
        var d = Crafter(crafter);
        if (d == null) return "Nobody here does that.";
        if (!World.Rules.Test(d.When, c)) return d.ClosedLine ?? $"{d.Name} will not work for you yet.";
        if (d.Closed != null && World.Rules.Test(d.Closed, c)) return d.ClosedLine ?? $"{d.Name} is not working now.";
        return null;
    }

    public static bool Does(string crafter, Verb v) => Crafter(crafter)?.Verbs.Contains(v.Key()) == true;

    static (int HeatTop, int TemperIron) Terms(string crafter, Ctx c)
    {
        int h = 0, i = 0;
        foreach (var e in Crafter(crafter)?.Easier ?? new())
            if (World.Rules.Test(e.When, c)) { h += e.HeatTop; i += e.TemperIron; }
        return (h, i);
    }

    /// <summary>What the crafter's terms are now, in words.</summary>
    public static List<string> TermLines(string crafter, Ctx c) =>
        (Crafter(crafter)?.Easier ?? new()).Where(e => e.Line != null && World.Rules.Test(e.When, c)).Select(e => e.Line!).ToList();

    static int Price(CraftCtx x, string crafter, int gold) => gold <= 0 ? 0 : Math.Max(1, (int)Math.Ceiling(gold * x.PriceMod(crafter)));

    /* ----------------------------------------------------------- quotes -- */

    static Quote Begin(Verb v, string crafter, string title) => new() { Verb = v, Crafter = crafter, Title = title };

    /// <summary>Takes and gold the survivor lacks, and the piece's own limits, as the reason it cannot be done.</summary>
    static void Afford(CraftCtx x, Quote q)
    {
        if (q.Blocked != null) return;
        foreach (var (m, n) in q.Takes)
            if (Inventory.Count(x.Ch, m) < n) { q.Blocked = $"Needs {n} {(Items.Find(m)?.Name ?? m).ToLowerInvariant()}; you have {Inventory.Count(x.Ch, m)}."; return; }
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
        var (top, less) = Terms(crafter, x.Ctx);
        if (index < 0 || index >= it.Affixes.Count) { q.Blocked = "Choose what to temper."; return q; }
        var a = it.Affixes[index];
        var def = Items.Affix(a.Id);
        q.Affix = a.Id;
        q.Before = Line(a.Id, a.Tier);
        Hot(it, q);
        if (q.Blocked != null) return q;
        if (def?.Kindled != null || def?.Grants != null) { q.Blocked = "A coal or a worn skill has no grades."; return q; }
        if (a.Tier >= Cap(it)) { q.Blocked = $"Grade {Grade(a.Tier)} is as high as a {Inventory.RarityName(it).ToLowerInvariant()} piece goes."; return q; }
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
        int tier = EntryGrade(it);
        q.Title = $"Work in {Items.Find(material)?.Name ?? material}";
        q.After = Line(affix, tier);
        if (replace >= 0)
        {
            if (replace >= it.Affixes.Count) { q.Blocked = "Choose what to work it in over."; return q; }
            q.Before = Line(it.Affixes[replace].Id, it.Affixes[replace].Tier);
        }
        else if (OpenSeams(it) == 0) q.Blocked = Seams(it) == 0 ? "No seam to work it into: have it remade first." : "No open seam: choose what it goes in over.";
        if (it.Affixes.Where((a, i) => i != replace).Any(a => a.Id == affix)) q.Blocked ??= "It already has that.";
        var (top, _) = Terms(crafter, x.Ctx);
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
        var (top, _) = Terms(crafter, x.Ctx);
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
        if (to > Rules.RemakeCap) { q.Blocked = "There's no better pattern he knows. Not yet."; return q; }
        var step = Rules.Remake[Math.Clamp(to - 1, 0, Rules.Remake.Count - 1)];
        q.Title = $"Remake as {Items.RarityNames[to].ToLowerInvariant()}";
        q.Takes[Iron] = step.Iron;
        q.Gold = Price(x, crafter, step.Gold);
        q.HeatLo = q.HeatHi = -(Rules.Heat[RarityIx(to)] - Rules.Heat[RarityIx(it.Rarity)]);
        var def = Items.Get(it.Def);
        q.After = def.Weapon != null && def.Weapon.Rank + (to - def.Rarity) <= Inventory.GearRankCap
            ? $"A seam opens; it comes into the night a rank higher" : "A seam opens";
        Afford(x, q);
        return q;
    }

    /// <summary>Rekindle: heat back, half the piece's full heat; each time dearer.</summary>
    public static Quote Rekindle(CraftCtx x, ItemInstance it, string crafter = "brannoc")
    {
        var q = Begin(Verb.Rekindle, crafter, "Rekindle");
        if (it.Heat is not int h || it.HeatFull is not int full) { q.Blocked = "That's somebody's work. Leave it be."; return q; }
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
    public static Quote BreakDown(CraftCtx x, ItemInstance it)
    {
        var q = Begin(Verb.BreakDown, "", "Break down");
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

    /* ------------------------------------------------------------- doing -- */

    /// <summary>Do what was quoted (quoted afresh, so the numbers are the ones the survivor
    /// saw). The heat spent is rolled in the quoted range; at none the piece is set. False if
    /// it could not be done.</summary>
    public static bool Do(CraftCtx x, ItemInstance it, Quote q, Rng rng)
    {
        if (!q.Ok) return false;
        var ch = x.Ch;
        var w = x.World;
        if (q.Verb == Verb.BreakDown)
        {
            if (Inventory.Find(ch, it.Uid) is not { InPack: true } loc) return false;
            ch.Pack[loc.Index] = null;
            foreach (var (m, n) in q.Gives) Inventory.AddToPack(ch, Inventory.Make(ch, m, n));
            return true;
        }
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx) is not null) return false;
        foreach (var (m, n) in q.Takes) if (Inventory.Count(ch, m) < n) return false;
        if (ch.Gold < q.Gold) return false;
        foreach (var (m, n) in q.Takes) Inventory.Take(ch, m, n);
        ch.Gold -= q.Gold;
        int cost = q.HeatLo == q.HeatHi ? q.HeatLo : rng.Int(q.HeatLo, q.HeatHi);
        string who = Crafter(q.Crafter)?.Name ?? q.Crafter;
        switch (q.Verb)
        {
            case Verb.Temper:
                it.Affixes[q.Index].Tier++;
                break;
            case Verb.WorkIn:
            {
                var roll = new AffixRoll { Id = q.Affix!, Tier = EntryGrade(it) };
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
                (it.History ??= new()).Add($"A coal from the night caged in it by {who}, day {w.Day}");
                break;
            }
            case Verb.Remake:
            {
                int add = -cost;
                it.Rarity++;
                it.Heat = (it.Heat ?? 0) + add;
                it.HeatFull = (it.HeatFull ?? 0) + add;
                (it.History ??= new()).Add($"Remade by {who}, day {w.Day}");
                cost = 0;
                break;
            }
            case Verb.Rekindle:
                it.Heat = Math.Min(it.HeatFull ?? 0, (it.Heat ?? 0) - cost);
                it.Rekindled = (it.Rekindled ?? 0) + 1;
                cost = 0;
                break;
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
        if (done * d.RespectPerCraft < d.RespectFromCraft) n.Respect = Math.Min(100, n.Respect + d.RespectPerCraft);
    }

    /* ---------------------------------------------------------- the night -- */

    /// <summary>What a survivor carries out of an arena, and what they spilled falling.</summary>
    public sealed record NightYield(Dictionary<string, int> Kept, Dictionary<string, int> Spilled);

    /// <summary>Ember shards for the ember reached, the tier, the minutes stayed past the half
    /// hour and a story fight won; the people's own for their champions slain. A fall keeps half.</summary>
    public static NightYield Night(string people, int tier, bool story, int ember, double minutesPast, bool won, bool fell,
        IReadOnlyDictionary<Family, int> champions)
    {
        var r = Rules.Night;
        var all = new Dictionary<string, int>();
        void Add(string m, int n) { if (n > 0) all[m] = all.GetValueOrDefault(m) + n; }
        Add(Shard, Math.Max(0, ember - r.EmberFrom) / Math.Max(1, r.EmberPer) + Math.Max(0, tier - 1)
            + (won ? (int)Math.Floor(Math.Max(0, minutesPast) / Math.Max(1, r.MinutesPer)) : 0) + (won && story ? r.StoryBonus : 0));
        foreach (var p in r.Peoples.GetValueOrDefault(people) ?? new())
            if (EnumKey<Family>.TryParse(p.Family, out var fam))
                Add(p.Material, Math.Min(r.Cap, champions.GetValueOrDefault(fam) / Math.Max(1, p.Per)));
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
