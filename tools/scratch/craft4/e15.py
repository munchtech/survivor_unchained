from ed import sub

sub("tests/CraftingTests.cs", [
("""        Assert.False(Crafting.BreakDown(j.Craft, j.Ch.Equipment.Weapon!).Ok);
        Assert.False(Crafting.BreakDown(j.Craft, Piece(j, "wardens_lampiron", 3)).Ok);
    }
""",
"""        Assert.False(Crafting.BreakDown(j.Craft, j.Ch.Equipment.Weapon!).Ok);
        Assert.False(Crafting.BreakDown(j.Craft, Piece(j, "wardens_lampiron", 3)).Ok);
    }

    [Fact]
    public void A_Legendary_breaks_down_for_five_old_iron_and_three_shards_wherever_it_is_broken()
    {
        var j = Make();
        var legendary = Items.All.Values.First(d => d.Rarity == 4 && !d.Unique && Items.SlotFor(d) != null);
        var it = Piece(j, legendary.Id, 4);
        Assert.Equal(LootTier.Legendary, Drops.TierOf(it));
        var q = Crafting.BreakDown(j.Craft, it);
        Assert.True(q.Ok, q.Blocked);
        Assert.Equal(5, q.Gives[Crafting.Iron]);
        Assert.Equal(3, q.Gives[Crafting.Shard]);
        // A fight's end breaks down what it hid or could not carry by the same yield.
        Assert.Equal(q.Gives, Crafting.Yield(it));
        Assert.True(j.Work(it.Uid, q, null));
        Assert.Equal(3, Inventory.Count(j.Ch, Crafting.Shard));
    }
"""),
])
