using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Who may carry a skill (docs/design/CLASS_IDENTITY_AND_TALENTS.md 2.1, 6.1 "Access"):
/// the kindred pairs, the valley's for everyone, a union its parts' in common, and every
/// way a skill reaches her (the draft, the calling's lessons, tomes, gear) asking Weapons.CanCarry.</summary>
public class AccessTests
{
    static readonly string[] Four = ["warden", "reaver", "arcanist", "stalker"];

    static readonly Dictionary<string, string[]> Pairs = new()
    {
        ["cleaver"] = ["warden", "reaver"], ["iron_palms"] = ["warden", "reaver"],
        ["arcweb"] = ["reaver", "arcanist"], ["umbral_bolt"] = ["reaver", "arcanist"],
        ["firepot"] = ["arcanist", "stalker"], ["thornbloom"] = ["arcanist", "stalker"],
        ["judgement_disc"] = ["stalker", "warden"], ["gale_chakram"] = ["stalker", "warden"],
        ["dawnpulse"] = ["warden", "arcanist"], ["hallowed_ring"] = ["warden", "arcanist"],
        ["spirit_herd"] = ["reaver", "stalker"], ["blightfield"] = ["reaver", "stalker"],
    };

    static Journey Survivor(string calling, uint seed = 7)
    {
        var a = Callings.Archetype(calling);
        return Journey.Begin(new CreationChoice { Name = "T", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, seed);
    }

    [Fact]
    public void The_kindred_pairs_and_the_valleys_are_as_designed()
    {
        foreach (var id in Weapons.Pool)
        {
            var want = Pairs.GetValueOrDefault(id) ?? Four;
            foreach (var c in Four) Assert.Equal(want.Contains(c), Weapons.CanCarry(c, id));
            // An evolution is carried by whoever carries its skill.
            foreach (var e in Weapons.All[id].Evolutions)
                foreach (var c in Four) Assert.Equal(want.Contains(c), Weapons.CanCarry(c, e.Id));
        }
        Assert.Equal(14, Weapons.Pool.Count(id => Weapons.AccessOf(id) == null));
        // A union's access is computed, never stored.
        foreach (var u in Unions.All) Assert.Null(Weapons.All[u.Into].Access);
    }

    [Theory]
    [InlineData("dawns_judgement", "warden")]
    [InlineData("rotwood", "stalker")]
    [InlineData("the_tempest", "reaver,arcanist")]
    [InlineData("butchers_wheel", "warden,reaver")]
    [InlineData("barrow_host", "reaver,stalker")]
    [InlineData("soul_lantern", "reaver,arcanist")]
    [InlineData("frostfire_comet", "warden,reaver,arcanist,stalker")]
    public void A_union_is_for_the_callings_both_its_halves_allow(string union, string who)
    {
        var want = who.Split(',');
        foreach (var c in Four) Assert.Equal(want.Contains(c), Weapons.CanCarry(c, union));
    }

    /// <summary>A whole arena of drafts, taken at random, for each calling: nothing it may not
    /// carry is ever offered, nor held.</summary>
    [Fact]
    public void Each_calling_never_drafts_what_it_cannot_carry()
    {
        foreach (var calling in Four)
        {
            var rng = new Random(11);
            var seen = new HashSet<string>();
            for (uint seed = 1; seed <= 10; seed++)
            {
                var b = BattleTests.Arena(seed);
                b.Calling = calling;
                for (int level = 0; level < 60; level++)
                {
                    b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
                    while (b.DraftOwed)
                    {
                        var offers = LevelUp.Draft(b);
                        foreach (var o in offers.Where(o => o.Kind is OfferKind.Weapon or OfferKind.Rank or OfferKind.Evolve or OfferKind.Union or OfferKind.Hone))
                        {
                            Assert.True(Weapons.CanCarry(calling, o.Id), $"{calling} offered {o.Kind} {o.Id}");
                            if (o.Branch != null) Assert.True(Weapons.CanCarry(calling, o.Branch), $"{calling} offered {o.Branch}");
                            seen.Add(o.Id);
                        }
                        // Evolutions and unions first, as a player takes them; else at random.
                        var take = offers.FirstOrDefault(o => o.Kind is OfferKind.Evolve or OfferKind.Union) ?? offers[rng.Next(offers.Count)];
                        LevelUp.Choose(b, take);
                    }
                }
                Assert.All(b.Weapons, w => Assert.True(Weapons.CanCarry(calling, w.Id), $"{calling} holds {w.Id}"));
            }
            // It still sees the rest: its pairs' and the valley's.
            Assert.True(seen.Count >= 15, $"{calling} saw only {seen.Count}");
        }
    }

    [Fact]
    public void A_warden_never_sees_the_six_kindred_skills_she_is_not_in()
    {
        string[] never = ["arcweb", "umbral_bolt", "firepot", "thornbloom", "spirit_herd", "blightfield"];
        var banned = never.Concat(never.SelectMany(id => Weapons.All[id].Evolutions.Select(e => e.Id)))
            .Concat(Unions.All.Where(u => never.Contains(u.A) || never.Contains(u.B)).Select(u => u.Id)).ToHashSet();
        var rng = new Random(3);
        for (uint seed = 1; seed <= 40; seed++)
        {
            var b = BattleTests.Arena(seed);
            b.Calling = "warden";
            for (int level = 0; level < 40; level++)
            {
                b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
                while (b.DraftOwed)
                {
                    var offers = LevelUp.Draft(b);
                    Assert.DoesNotContain(offers, o => banned.Contains(o.Id) || (o.Branch != null && banned.Contains(o.Branch)));
                    LevelUp.Choose(b, offers[rng.Next(offers.Count)]);
                }
            }
        }
    }

    [Fact]
    public void A_union_is_offered_only_where_both_halves_allow_it()
    {
        foreach (var calling in new[] { "warden", "arcanist" })
        {
            var b = BattleTests.Arena(1, ("dawnpulse", Weapons.MaxRank), ("judgement_disc", Weapons.MaxRank));
            b.Calling = calling;
            foreach (var id in new[] { "dawnpulse", "judgement_disc" }) b.Evolve(id, Weapons.All[id].Evolutions[0].Id);
            Assert.Equal(calling == "warden", LevelUp.ReadyUnions(b).Any(u => u.Id == "dawns_judgement"));
        }
    }

    [Fact]
    public void The_calling_never_teaches_what_it_cannot_carry()
    {
        foreach (var calling in Four)
        {
            var j = Survivor(calling);
            var ch = j.Ch;
            ch.Discovered.AddRange(Weapons.Pool.Where(id => !ch.Discovered.Contains(id)));
            ch.Attributes.Might = ch.Attributes.Finesse = ch.Attributes.Wits = ch.Attributes.Resolve = 20;
            for (int level = 3; level <= 60; level += 3)
            {
                ch.Level = level;
                if (SkillBook.Calling(ch) is { } taught) Assert.True(Weapons.CanCarry(calling, taught), $"{calling} taught {taught}");
            }
            Assert.All(ch.Skills.Where(Weapons.All.ContainsKey), id => Assert.True(Weapons.CanCarry(calling, id)));
        }
    }

    [Fact]
    public void A_tome_she_cannot_carry_is_refused_and_one_slotted_lies_idle()
    {
        var ch = Survivor("warden").Ch;
        ch.Discovered.Add("firepot");
        ch.Attributes.Might = ch.Attributes.Finesse = ch.Attributes.Wits = ch.Attributes.Resolve = 20;
        Assert.False(SkillBook.CanLearn(ch, "firepot"));
        Assert.False(SkillBook.Learn(ch, "firepot"));
        // An old save that knows and carries it: it lies idle, and no slot takes it.
        ch.Skills.Add("firepot");
        ch.Slotted.Clear();
        ch.Slotted.Add("firepot");
        Assert.DoesNotContain(SkillBook.Carried(ch), c => c.Id == "firepot");
        Assert.DoesNotContain(Character.Kit(ch).Learned, c => c.Id == "firepot");
        ch.Slotted.Clear();
        Assert.False(SkillBook.Slot(ch, "firepot"));
        // Hers to carry: learned and carried.
        ch.Discovered.Add("gale_chakram");
        Assert.True(SkillBook.Learn(ch, "gale_chakram"));
        Assert.Contains(SkillBook.Carried(ch), c => c.Id == "gale_chakram");
    }

    [Fact]
    public void A_worn_skill_she_cannot_carry_rerolls_and_a_worn_weapon_keeps_only_its_numbers()
    {
        var amulet = Items.All.Values.First(d => d.Base && d.Kind == ItemKind.Amulet && Items.Affixes.Any(a => a.Id == "of_dawn" && a.Slots.Contains(d.Kind))).Id;
        int Dawns(string calling)
        {
            var ch = Survivor(calling).Ch;
            int n = 0;
            for (uint s = 1; s <= 600; s++)
                if (Inventory.Make(ch, amulet, rarity: 4, seed: s).Affixes.Any(a => a.Id == "of_dawn")) n++;
            return n;
        }
        Assert.True(Dawns("warden") > 0);
        Assert.Equal(0, Dawns("reaver"));
        Assert.Equal(0, Dawns("stalker"));

        // A reaver wearing a disc (a stalker's and a warden's): worn, its skill idle.
        var r = Survivor("reaver").Ch;
        var disc = Inventory.Make(r, "judgement_disc_item");
        Assert.True(Inventory.Equip(r, disc, EquipSlot.Weapon));
        Assert.DoesNotContain(Character.Kit(r).Weapons, w => w.Id == "judgement_disc");
        var given = Inventory.Make(null, amulet, rarity: 4, affixes: [new AffixRoll { Id = "of_dawn", Tier = 2 }]);
        Assert.True(Inventory.Equip(r, given, EquipSlot.Amulet));
        Assert.DoesNotContain(Character.Kit(r).Weapons, w => w.Id == "dawnpulse");
    }

    [Fact]
    public void Loot_for_a_survivor_never_rolls_a_weapon_her_calling_cannot_carry()
    {
        foreach (var calling in Four)
        {
            var j = Survivor(calling);
            var rnd = new Random(9);
            var x = new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Champion, Level = 30, People = "dead", R = rnd.NextDouble };
            for (int i = 0; i < 400; i++)
                foreach (var tier in new[] { LootTier.Rare, LootTier.Epic, LootTier.Set, LootTier.Legendary })
                {
                    var it = Drops.Piece(x, tier, rnd.NextDouble);
                    if (Items.Get(it.Def).Weapon is { } w) Assert.True(Weapons.CanCarry(calling, w.Id), $"{calling} got {it.Def}");
                }
        }
    }

    [Fact]
    public void Every_calling_starts_with_weapons_it_can_carry()
    {
        foreach (var calling in Four)
            foreach (var item in Callings.Archetype(calling).Weapons)
                if (Items.Get(item).Weapon is { } w) Assert.True(Weapons.CanCarry(calling, w.Id), $"{calling} starts with {item} ({w.Id})");
    }
}
