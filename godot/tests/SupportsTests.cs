using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Support gems (BUILD_DIRECTION "Supports", BUILD_UNLOCKS): sockets open with a skill's rank (3, 6), a gem takes
/// only the skills its tags fit, a copy sits in one socket, owning a gem lowers its own drop weight, and a socket closed by
/// rank keeps its gem but adds nothing. data/content/supports.json, Rpg/Supports.cs.</summary>
public sealed class SupportsTests
{
    [Fact]
    public void Gems_are_unique_and_fit_real_tags()
    {
        Assert.NotEmpty(Supports.All);
        Assert.Equal(Supports.All.Count, Supports.All.Select(g => g.Id).Distinct().Count());
        foreach (var g in Supports.All)
        {
            Assert.All(g.Fits, f => Assert.True(Enum.TryParse<Tag>(f, true, out _), $"{g.Id} fits unknown tag {f}"));
            Assert.NotEmpty(g.Effects);
            Assert.True(g.Weight > 0);
        }
    }

    [Theory]
    [InlineData(1, 0), InlineData(2, 0), InlineData(3, 1), InlineData(5, 1), InlineData(6, 2), InlineData(8, 2)]
    public void Sockets_open_with_rank(int rank, int open) => Assert.Equal(open, Supports.SocketsAt(rank));

    [Fact]
    public void The_warden_basic_attack_takes_melee_gems_and_any_gems()
    {
        Assert.True(Supports.Fits(Supports.Find("brutality")!, "sunder"));
        Assert.True(Supports.Fits(Supports.Find("haste")!, "sunder"));
        var spell = Weapons.All.Values.FirstOrDefault(w => w.Tags.Contains(Tag.Spell) && !w.Tags.Contains(Tag.Melee));
        if (spell != null) Assert.False(Supports.Fits(Supports.Find("brutality")!, spell.Id));
    }

    [Fact]
    public void A_socket_needs_rank_fit_and_a_free_copy()
    {
        var s = new SupportState();
        s.Owned["brutality"] = 1;
        Assert.False(Supports.Socket(s, "sunder", 2, 0, "brutality"));      // no socket at rank 2
        Assert.True(Supports.Socket(s, "sunder", 3, 0, "brutality"));
        Assert.False(Supports.Socket(s, "sunder", 3, 1, "brutality"));      // socket 2 opens at 6
        Assert.False(Supports.Socket(s, "heroic_leap", 6, 0, "brutality")); // the one copy is in sunder
        Assert.True(Supports.Socket(s, "sunder", 3, 0, "brutality"));       // re-setting its own socket is fine
        Assert.False(Supports.Socket(s, "sunder", 6, 1, "nonesuch"));
        s.Owned["brutality"] = 2;
        Assert.True(Supports.Socket(s, "sunder", 6, 1, "brutality"));
    }

    [Fact]
    public void A_closed_socket_keeps_its_gem_but_adds_nothing()
    {
        var s = new SupportState();
        s.Owned["brutality"] = 1; s.Owned["haste"] = 1;
        Assert.True(Supports.Socket(s, "sunder", 6, 0, "brutality"));
        Assert.True(Supports.Socket(s, "sunder", 6, 1, "haste"));
        Assert.Equal(0.15, Supports.EffectsFor(s, "sunder", 6)["speed"], 6);
        var low = Supports.EffectsFor(s, "sunder", 4);
        Assert.False(low.ContainsKey("speed"));
        Assert.Equal(0.25, low["damage"], 6);
        Assert.Equal("haste", s.Sockets["sunder"][1]);
    }

    [Fact]
    public void Owning_a_gem_makes_it_drop_less_so_the_others_come()
    {
        var g = Supports.Find("brutality")!;
        Assert.Equal(g.Weight * 0.5, Supports.DropWeight(g, 1), 9);
        var fresh = new SupportState();
        var owned = new SupportState();
        owned.Owned["brutality"] = 3;
        var rng = new Random(7);
        int a = 0, b = 0;
        for (int i = 0; i < 20000; i++)
        {
            double r = rng.NextDouble();
            if (Supports.Roll(fresh, r).Id == "brutality") a++;
            if (Supports.Roll(owned, r).Id == "brutality") b++;
        }
        Assert.True(b * 4 < a, $"owned 3: {b} drops against {a} fresh");
    }

    [Fact]
    public void Every_gem_has_a_registered_gem_item()
    {
        foreach (var g in Supports.All)
        {
            var d = Items.Get(Supports.ItemId(g.Id));
            Assert.Equal(ItemKind.Gem, d.Kind);
            Assert.Equal(g.Id, Supports.OfItem(d.Id)!.Id);
            Assert.Equal(Store.Gems, Drops.StoreOf(d, null));
        }
    }

    [Fact]
    public void Gems_survive_a_save_round_trip()
    {
        var ch = new CharacterData { Ability = Content.Abilities.All.Values.First().Id };
        ch.Gems.Owned["haste"] = 2;
        ch.Gems.Sockets["sunder"] = new() { "haste", null };
        var back = Core.Json.Parse<CharacterData>(Core.Json.Write(ch));
        Assert.Equal(2, back.Gems.Owned["haste"]);
        Assert.Equal(new string?[] { "haste", null }, back.Gems.Sockets["sunder"].ToArray());
    }

    [Fact]
    public void A_gem_item_goes_to_the_gem_store_not_the_pack()
    {
        var ch = new CharacterData();
        var it = Inventory.Make(ch, Supports.ItemId("haste"), dropped: true);
        Assert.True(Inventory.AddToPack(ch, it));
        Assert.Equal(1, ch.Gems.Owned["haste"]);
        Assert.All(ch.Pack, p => Assert.Null(p));
        Assert.Equal(1, Inventory.Count(ch, Supports.ItemId("haste")));
    }

    [Fact]
    public void A_boss_drops_one_gem_from_level_12_and_none_before()
    {
        int Gems(int level)
        {
            var ch = new CharacterData { Level = level };
            var x = new DropCtx { Ch = ch, Source = DropSource.Boss, Level = level, R = () => 0.5 };
            return Drops.Roll(x).Count(d => d.Tier == LootTier.Gem);
        }
        Assert.Equal(1, Gems(12));
        Assert.Equal(0, Gems(11));
        Assert.True(Drops.Jackpot(LootTier.Gem));
    }
}
