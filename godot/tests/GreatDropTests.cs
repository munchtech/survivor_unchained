using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-gear) The great drops: uniques that rewrite a skill, enable a build, or grant an auto skill the Warden
/// can get no other way; the gift's own drop event; and the gear rules around them (granting affixes, sets).</summary>
public class GreatDropTests
{
    static Journey Warden(int level = 20) => Balance.MapSim.Survivor("warden", level, 1, 5);
    static Func<double> Seq(int seed) { var r = new Random(seed); return r.NextDouble; }
    static IEnumerable<ItemDef> Defs => Items.All.Values;

    static List<ItemDef> Rewriters => Defs.Where(d => d.Rewrites is { Count: > 0 }).ToList();
    static List<ItemDef> Builders => Defs.Where(d => !string.IsNullOrEmpty(d.Build)).ToList();
    static List<ItemDef> Givers => Defs.Where(d => d.Auto is { Count: > 0 }).ToList();

    [Fact]
    public void At_least_three_of_each_kind_are_there_for_the_Warden()
    {
        Assert.True(Rewriters.Count >= 3, "rewrite a skill");
        Assert.True(Builders.Count >= 3, "enable a build");
        Assert.True(Givers.Count >= 3, "grant an auto skill");
        foreach (var d in Rewriters.Concat(Builders).Concat(Givers))
        {
            Assert.Equal(4, d.Rarity);
            Assert.Null(d.Set);
        }
    }

    [Fact]
    public void A_rewrite_is_a_trigger_keyed_to_a_skill_the_Warden_carries()
    {
        foreach (var d in Rewriters)
            foreach (var skill in d.Rewrites!)
            {
                Assert.True(Weapons.All.ContainsKey(skill), $"{d.Id}: {skill} is a skill");
                Assert.True(Weapons.CanCarry("warden", skill), $"{d.Id}: the Warden carries {skill}");
                Assert.Contains(d.Triggers ?? new(), t => t.When?.Weapon == skill);
            }
    }

    [Fact]
    public void A_build_piece_has_a_rule_to_build_on()
    {
        foreach (var d in Builders)
            Assert.True(d.Triggers is { Count: > 0 }, $"{d.Id} enables {d.Build} with a trigger");
    }

    [Fact]
    public void An_auto_gift_is_a_skill_the_Warden_cannot_get_any_other_way()
    {
        foreach (var d in Givers)
        {
            foreach (var skill in d.Auto!.Keys) Assert.True(Weapons.All.ContainsKey(skill), $"{d.Id}: {skill}");
            var gift = Drops.GiftOf(d, "warden");
            Assert.NotNull(gift);
            Assert.False(Weapons.CanCarry("warden", gift!));
        }
        // A piece that gives nothing she lacks is no gift, and no calling is no gift either.
        Assert.Null(Drops.GiftOf(Items.Get("iron_helm"), "warden"));
        Assert.Null(Drops.GiftOf(Givers[0], null));
    }

    [Fact]
    public void Worn_an_auto_piece_adds_its_skill_to_the_kit_stacked_and_uncapped()
    {
        var j = Warden();
        foreach (var d in Givers)
        {
            var it = Inventory.Make(j.Ch, d.Id);
            Inventory.Equip(j.Ch, it, d.Kind == ItemKind.Ring ? EquipSlot.Ring1 : d.Kind == ItemKind.Amulet ? EquipSlot.Amulet : d.Kind == ItemKind.Head ? EquipSlot.Head : EquipSlot.Body);
        }
        var kit = Character.Kit(j.Ch);
        foreach (var d in Givers)
            foreach (var (skill, rank) in d.Auto!)
                Assert.Contains((skill, rank), kit.AutoSkills);
        Assert.True(kit.AutoSkills.Count >= Givers.Count, "every one worn, no limit of the auto slots");
    }

    [Fact]
    public void A_gift_drop_has_its_own_event_and_announcement_the_ordinary_Legendary_does_not()
    {
        var j = Warden(12);
        var gifts = new List<GiftDrop>();
        var said = new List<Announcement>();
        j.OnGift = gifts.Add;
        j.OnAnnounce = said.Add;
        var horn = Givers.First(d => d.Auto!.ContainsKey("spirit_herd"));
        j.Drops(new DropCtx { Source = DropSource.Boss, Level = 12, People = "dead", Floor = (int)LootTier.Legendary, Grant = horn.Id, R = Seq(3) });
        var g = Assert.Single(gifts);
        Assert.Equal("spirit_herd", g.Skill);
        Assert.Equal(horn.Id, g.Item.Def);
        Assert.Contains(said, a => a.Kicker == Drops.GiftFalls && a.Through);
        Assert.DoesNotContain(said, a => a.Title == Drops.NamedFalls);

        // An ordinary Legendary (one that grants nothing new) keeps the old line, and raises no gift.
        var plain = Warden(12);
        var g2 = new List<GiftDrop>();
        var said2 = new List<Announcement>();
        plain.OnGift = g2.Add;
        plain.OnAnnounce = said2.Add;
        plain.Drops(new DropCtx { Source = DropSource.Boss, Level = 12, People = "dead", Floor = (int)LootTier.Legendary, Grant = Rewriters[0].Id, R = Seq(4) });
        Assert.Empty(g2);
        Assert.Contains(said2, a => a.Title == Drops.NamedFalls);
    }

    [Fact]
    public void Granting_affixes_roll_on_amulets_and_rings_only()
    {
        var granting = Items.Affixes.Where(a => a.Grants != null).ToList();
        Assert.NotEmpty(granting);
        foreach (var a in granting)
            Assert.All(a.Slots, s => Assert.True(s is ItemKind.Amulet or ItemKind.Ring, $"{a.Id} rolls on {s}"));
        // ... and in the drops: none found worn on any other kind over many rolls.
        for (int s = 0; s < 120; s++)
        {
            var j = Warden(30);
            foreach (var d in Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 30 + s % 40, People = "dead", Floor = (int)LootTier.Legendary, R = Seq(s) }))
                if (d.Item != null && Items.Get(d.Item.Def).Kind is not (ItemKind.Amulet or ItemKind.Ring))
                    Assert.DoesNotContain(d.Item.Affixes, a => Items.Affix(a.Id)?.Grants != null);
        }
    }

    [Fact]
    public void Sets_are_two_or_three_pieces_on_live_slots_with_minor_perks()
    {
        Assert.NotEmpty(Drops.Rules.Sets);
        foreach (var set in Drops.Rules.Sets.Values)
        {
            Assert.InRange(set.Pieces.Count, 2, 3);
            Assert.Equal(set.Pieces.Count, set.Pieces.Distinct().Count());
            foreach (var id in set.Pieces)
            {
                var d = Items.Get(id);
                Assert.Equal(set.Id, d.Set);
                Assert.Contains(d.Kind, Enum.GetValues<ItemKind>());
                Assert.True(string.IsNullOrEmpty(d.Build) && d.Auto == null && d.Rewrites == null, $"{id}: a set is never the build");
            }
            Assert.All(set.Bonuses, b => Assert.InRange(b.Worn, 2, set.Pieces.Count));
            // Minor perks: the rule is small (a few mods and at most a trigger each), never a rewrite.
            Assert.All(set.Bonuses, b => Assert.True((b.Mods?.Count ?? 0) <= 3 && (b.Triggers?.Count ?? 0) <= 1));
        }
    }
}
