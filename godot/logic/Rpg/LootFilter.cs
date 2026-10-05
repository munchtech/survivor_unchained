using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/* The item filter (docs/design/LOOT_DESIGN.md §7): what is shown on the ground,
 * what is hidden, what is shouted. A preset, five plain toggles, and a list of
 * rules read top to bottom, the first that matches deciding (Path of Exile's
 * rule). Whatever the rules say, the jackpots (Legendary, Set, Storied, quest
 * things) and a first sighting are never hidden. Hidden things are not taken
 * underfoot, and at a fight's end they are broken down for old iron. */

public enum FilterPreset { Everything, Default, Strict, Best }

public enum FilterAction { Show, Hide, Emphasise }

/// <summary>One rule: an action, and conditions that must all hold (null: any).</summary>
public sealed class FilterRule
{
    public FilterAction Action = FilterAction.Show;
    public List<LootTier>? Tiers;
    public List<ItemKind>? Kinds;
    public int? MinLevel, MaxLevel;
    /// <summary>Within this many levels below the survivor's own.</summary>
    public int? Near;
    public Make? MinMake;
    /// <summary>Any of these affixes, at this grade or better (0 is grade I).</summary>
    public List<string>? Affixes;
    public int? MinGrade;
    /// <summary>Better than what is worn where it would go.</summary>
    public bool? Upgrade;
    /// <summary>A weapon of the survivor's calling.</summary>
    public bool? Calling;
}

public sealed class LootFilter
{
    public FilterPreset Preset = FilterPreset.Default;
    public bool Upgrades = true, CallingWeapons = true, BetterMakes = true, BreakHidden = true;
    /// <summary>Drop sounds from this tier up (Rare by default).</summary>
    public LootTier SoundsFrom = LootTier.Rare;
    /// <summary>The player's own rules, read before the preset.</summary>
    public List<FilterRule> Rules = new();

    /// <summary>The filter's word on a piece where it falls. A first sighting (a base at a make
    /// never seen before) always shows: nobody learns what a Wrought helm is from a hidden one.</summary>
    public Verdict Judge(ItemInstance it, CharacterData? ch, bool firstSighting = false)
    {
        var tier = Drops.TierOf(it);
        if (tier is LootTier.Legendary or LootTier.Storied or LootTier.Set) return Verdict.Emphasised;
        if (Drops.Jackpot(tier) || firstSighting) return Verdict.Shown;
        // The toggles first: they are promises the player was made in plain words.
        bool gear = Items.SlotFor(Items.Get(it.Def)) != null;
        if (gear && ch != null)
        {
            if (Upgrades && Drops.IsUpgrade(ch, it)) return Verdict.Emphasised;
            if (CallingWeapons && Calling(ch, it)) return tier >= LootTier.Epic ? Verdict.Emphasised : Verdict.Shown;
            if (BetterMakes && tier == LootTier.Common && Drops.BetterMake(ch, it)) return Verdict.Shown;
        }
        foreach (var r in Rules)
            if (Matches(r, it, tier, ch))
                return r.Action switch { FilterAction.Hide => Verdict.Hidden, FilterAction.Emphasise => Verdict.Emphasised, _ => Verdict.Shown };
        return ByPreset(tier, gear);
    }

    Verdict ByPreset(LootTier tier, bool gear)
    {
        if (!gear) return Verdict.Shown;
        return Preset switch
        {
            FilterPreset.Everything => tier >= LootTier.Epic ? Verdict.Emphasised : Verdict.Shown,
            FilterPreset.Default => tier == LootTier.Common ? Verdict.Hidden : tier >= LootTier.Epic ? Verdict.Emphasised : Verdict.Shown,
            FilterPreset.Strict => tier <= LootTier.Uncommon ? Verdict.Hidden : tier >= LootTier.Epic ? Verdict.Emphasised : Verdict.Shown,
            _ => tier < LootTier.Epic ? Verdict.Hidden : Verdict.Emphasised,
        };
    }

    static bool Calling(CharacterData ch, ItemInstance it) =>
        Items.Get(it.Def) is { Kind: ItemKind.Weapon } d && Callings.Archetypes.TryGetValue(ch.Archetype, out var a)
        && (a.Weapons.Contains(d.Id) || d.Of != null && a.Weapons.Contains(d.Of));

    public static bool Matches(FilterRule r, ItemInstance it, LootTier tier, CharacterData? ch)
    {
        var def = Items.Get(it.Def);
        int level = Drops.LevelOf(it);
        if (r.Tiers != null && !r.Tiers.Contains(tier)) return false;
        if (r.Kinds != null && !r.Kinds.Contains(def.Kind)) return false;
        if (r.MinLevel is int lo && level < lo) return false;
        if (r.MaxLevel is int hi && level > hi) return false;
        if (r.Near is int near && (ch == null || level < ch.Level - near)) return false;
        if (r.MinMake is Make mk && Drops.MakeOf(level) < mk) return false;
        if (r.Affixes != null && !it.Affixes.Any(a => r.Affixes.Contains(a.Id) && a.Tier >= (r.MinGrade ?? 0))) return false;
        if (r.Affixes == null && r.MinGrade is int g && !it.Affixes.Any(a => a.Tier >= g)) return false;
        if (r.Upgrade is bool up && (ch == null || Drops.IsUpgrade(ch, it) != up)) return false;
        if (r.Calling is bool cl && (ch == null || Calling(ch, it) != cl)) return false;
        return true;
    }

    /// <summary>Whether a tier's landing is heard (the jackpots always are).</summary>
    public bool Heard(LootTier tier) => Drops.Jackpot(tier) || tier >= SoundsFrom && tier <= LootTier.Storied;
}
