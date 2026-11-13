using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The 13 November 2026 cut (15 gear places to 8): "her total power at a level is unchanged". Power is the loot score
/// (Drops.Power: the stats and rules a piece brings, at its make) summed over what she wears, a plain Rare of each place's
/// bases at the same expected affix roll. The old numbers are frozen from the build before the cut (head, body, cloak, amulet,
/// two rings and the off-hand: the places with bases); the cloak's is now the boots', the relic's affixes went to the jewellery.
/// The item levels run to 75 now (they ran to 40), so a level here is the old one stretched by 75/40.</summary>
public class GearBudgetTests
{
    /// <summary>The old level 5, 10 and 20 on the stretched curve.</summary>
    static int Stretch(int old) => (int)Math.Ceiling(old * Drops.Rules.MaxLevel / 40.0);

    /// <summary>The expected power of one worn place at a level and rarity: the mean base's implicit numbers at its make, and the
    /// expected power of what it rolls (the mean affix of its pool at the grade the rarity rolls).</summary>
    public static double SlotBudget(ItemKind kind, int level, int rarity = 2)
    {
        var bases = Items.All.Values.Where(d => d.Base && d.Kind == kind && d.Id.IndexOf("zz_", StringComparison.Ordinal) < 0).ToList();
        if (bases.Count == 0) return 0;
        double total = 0;
        foreach (var b in bases)
        {
            var bare = new ItemInstance { Uid = "x", Def = b.Id, Rarity = rarity, Level = level };
            double implicitPower = Drops.Power(bare);
            var pool = Items.Affixes.Where(a => a.Slots.Contains(kind) && rarity >= a.MinRarity && !a.Unique).ToList();
            double affix = 0;
            if (pool.Count > 0)
            {
                foreach (var a in pool)
                    foreach (int tier in new[] { Math.Max(0, rarity - 1), Math.Max(0, Math.Min(3, rarity)) })
                    {
                        var with = new ItemInstance { Uid = "x", Def = b.Id, Rarity = rarity, Level = level, Affixes = [new AffixRoll { Id = a.Id, Tier = tier }] };
                        affix += (Drops.Power(with) - implicitPower) / 2;
                    }
                affix = affix / pool.Count * Math.Min(3, rarity);
            }
            total += implicitPower + affix;
        }
        return total / bases.Count;
    }

    /// <summary>Everything worn that has a base: the head, the body, the boots, the amulet, both rings and the off-hand.</summary>
    static double Total(int level) =>
        new[] { ItemKind.Head, ItemKind.Body, ItemKind.Feet, ItemKind.Amulet, ItemKind.Ring, ItemKind.Ring, ItemKind.Offhand }.Sum(k => SlotBudget(k, level));

    [Theory]
    [InlineData(5, 75.323)]
    [InlineData(10, 90.651)]
    [InlineData(20, 109.811)]
    public void Her_power_at_a_level_is_within_three_percent_of_before_the_cut(int oldLevel, double before)
    {
        double now = Total(Stretch(oldLevel));
        Assert.InRange(now / before, 0.97, 1.03);
    }

    [Theory]
    [InlineData(5, "reaver_harness", "reaver_furboots")]
    [InlineData(14, "ranger_corset", "ranger_boots")]
    [InlineData(24, "warden_plate", "warden_sabatons")]
    [InlineData(5, "forged_cuirass")]
    public void A_named_kit_folded_into_its_body_piece_keeps_its_armor(int before, params string[] pieces)
    {
        double armor = pieces.Sum(id => Items.Get(id).Mods!.Where(m => m.Stat == Stat.Armor).Sum(m => m.Value));
        Assert.Equal(before, armor, 6);
    }

    [Fact]
    public void The_folded_body_pieces_wear_every_piece_of_the_kit()
    {
        // (the body covers everything from the neck down but the boots, so a kit's belt, legs, shoulders, arms and hands hang from it)
        var look = Wear.Of(new Equipment { Body = new ItemInstance { Uid = "b", Def = "warden_plate" } });
        foreach (var vs in new[] { "top", "belt", "skirt", "bottom", "greaves", "pauldrons", "bracers" }) Assert.True(look.ContainsKey(vs), vs);
        look = Wear.Of(new Equipment { Body = new ItemInstance { Uid = "b", Def = "ranger_corset" } });
        foreach (var vs in new[] { "top", "belt", "bottom", "pauldrons", "bracers", "gloves" }) Assert.True(look.ContainsKey(vs), vs);
    }

    [Fact]
    public void The_cut_places_are_gone_and_there_are_exactly_eight()
    {
        Assert.Equal(8, Enum.GetValues<EquipSlot>().Length);
        Assert.Equal(["Weapon", "Offhand", "Head", "Body", "Feet", "Amulet", "Ring1", "Ring2"], Enum.GetNames<EquipSlot>());
        string[] cut = ["belt", "legs", "cloak", "bracers", "shoulders", "hands", "relic"];
        Assert.DoesNotContain(Enum.GetNames<ItemKind>(), n => cut.Contains(n, StringComparer.OrdinalIgnoreCase));
        Assert.DoesNotContain(Items.All.Values, d => cut.Contains(d.Kind.ToString(), StringComparer.OrdinalIgnoreCase));
        Assert.DoesNotContain(Items.Affixes, a => a.Slots.Any(k => cut.Contains(k.ToString(), StringComparer.OrdinalIgnoreCase)));
        Assert.Equal(Items.EquipSlots.Count(), Items.Places.Count);
    }
}
