from ed import sub
NEW = '''
    /* ---------------------------------------------------------- Vonnra -- */

    static ItemInstance Carry(Route p, string def, int rarity, params (string Id, int Tier)[] affixes)
    {
        var it = Inventory.Make(p.J.Ch, def, rarity: rarity, affixes: affixes.Select(a => new AffixRoll { Id = a.Id, Tier = a.Tier }).ToList());
        Assert.True(Inventory.AddToPack(p.J.Ch, it));
        return it;
    }

    [Fact]
    public void Vonnra_binds_a_power_from_one_piece_into_another_and_the_donor_is_unmade()
    {
        var p = Town();
        p.W.Npc("vonnra").Flags["met"] = true;
        var keep = Carry(p, "bone_amulet", 2, ("hale", 1));
        var give = Carry(p, "silver_ring", 3, ("searing", 3), ("keen", 1), ("of_refusal", 0));
        p.Give("ember_shard", 10);
        // The toll first (the story lead's condition).
        var q = Crafting.Bind(p.J.Craft, keep, give, 0);
        Assert.Equal(Crafting.Crafter("vonnra")!.ClosedLine, q.Blocked);
        p.W.Facts["toll.paid"] = true;
        // What can give: the plain powers of what is carried that this piece takes; never a coal.
        var donors = Crafting.Donors(p.J.Ch, keep);
        Assert.Contains(donors, d => d.Donor == give && d.Index == 0);
        Assert.DoesNotContain(donors, d => d.Donor == give && d.Index == 2);
        Assert.Equal(Crafting.Line("vonnra", "bind.caged"), Crafting.Bind(p.J.Craft, keep, give, 2).Blocked);
        // At the donor's grade, to this piece's cap: an epic's IV comes into a rare at III.
        q = Crafting.Bind(p.J.Craft, keep, give, 0);
        Assert.True(q.Ok, q.Blocked);
        Assert.Equal(2, q.Grade);
        Assert.Equal(3, q.Takes[Crafting.Shard]);
        Assert.Equal(120, q.Gold);
        Assert.Equal(5, q.HeatLo);
        int heat = keep.Heat!.Value;
        Assert.True(p.J.Work(keep.Uid, q, null));
        Assert.Contains(keep.Affixes, a => a.Id == "searing" && a.Tier == 2);
        Assert.Null(Inventory.Find(p.J.Ch, give.Uid));
        Assert.InRange(keep.Heat!.Value, heat - 7, heat - 5);
        Assert.Contains(keep.History!, h => h.StartsWith("Bound over Vonnra's lamp"));
        Assert.Equal(Crafting.Line("vonnra", "first.bind"), p.J.CraftSaid?.Line);
        Assert.Equal(Crafting.Line("vonnra", "first.bind.before"), p.J.CraftSaid?.Before);
        // A piece worn cannot give (it would be unmade off her back); an accusation buys a tenth off.
        var worn = Carry(p, "silver_ring", 2, ("keen", 1));
        Inventory.Equip(p.J.Ch, worn, EquipSlot.Ring1);
        var amulet = Carry(p, "bone_amulet", 2);
        Assert.NotNull(Crafting.Bind(p.J.Craft, amulet, worn, 0).Blocked);
        var spare = Carry(p, "silver_ring", 2, ("keen", 2));
        int full = Crafting.Bind(p.J.Craft, amulet, spare, 0).Gold;
        p.W.Facts["vonnra.accused"] = true;
        Assert.Equal((int)Math.Ceiling(full * 0.9), Crafting.Bind(p.J.Craft, amulet, spare, 0).Gold);
    }

    /* ------------------------------------------------------------ Snib -- */

    [Fact]
    public void Snib_sells_three_jars_a_day_while_the_pump_runs()
    {
        var p = Town();
        Assert.False(Crafting.BuyJar(p.J.Craft).Ok);
        p.W.Npc("snib").Flags["met"] = true;
        for (int k = 0; k < 3; k++) Assert.True(p.J.Make(Crafting.BuyJar(p.J.Craft)));
        Assert.Equal(3, p.Count("slurry_jar"));
        Assert.Equal(Crafting.Line("snib", "jar.sale"), p.J.CraftSaid?.Line);
        Assert.Equal(Crafting.Line("snib", "jar.none"), Crafting.BuyJar(p.J.Craft).Blocked);
        p.Sleep();
        Assert.True(Crafting.BuyJar(p.J.Craft).Ok);
        p.W.Facts["dig.pump"] = "broken";
        Assert.False(Crafting.BuyJar(p.J.Craft).Ok);
        // The cure closes the sale; the jars bought keep, and still steep by the survivor's own hand.
        var it = Carry(p, "iron_helm", 2, ("hale", 1), ("of_the_wolf", 0));
        Assert.NotNull(Crafting.Steep(p.J.Craft, it, "snib").Blocked);
        Assert.True(Crafting.Steep(p.J.Craft, it).Ok);
    }

    [Fact]
    public void Steeping_is_the_one_gamble_past_the_forges_cap_and_it_sets_the_piece()
    {
        var p = Town();
        var seen = new System.Collections.Generic.Dictionary<string, int>();
        for (uint s = 1; s <= 400; s++)
        {
            p.Give("slurry_jar");
            var it = Carry(p, "iron_helm", 3, ("hale", 3), ("of_the_wolf", 1), ("keen", 0));
            var before = it.Affixes.Select(a => (a.Id, a.Tier)).ToList();
            var q = Crafting.Steep(p.J.Craft, it);
            Assert.True(q.Ok, q.Blocked);
            Assert.True(Crafting.Do(p.J.Craft, it, q, new Rng(s * 7919)));
            seen[q.Outcome!] = seen.GetValueOrDefault(q.Outcome!) + 1;
            Assert.Equal(0, it.Heat);
            Assert.True(Crafting.Slurried(it));
            Assert.Equal("It has been steeped. Once is all it takes.", Crafting.Steep(p.J.Craft, it).Blocked);
            var after = it.Affixes.Select(a => (a.Id, a.Tier)).ToList();
            switch (q.Outcome)
            {
                case "up": Assert.Equal(before.Sum(a => a.Tier) + 1, after.Sum(a => a.Tier)); break;
                case "down": Assert.Equal(before.Sum(a => a.Tier) - 1, after.Sum(a => a.Tier)); break;
                case "nothing": Assert.Equal(before, after); break;
                case "affix":
                    // Past the seams: a fourth power, the slurry's, strong with a price.
                    Assert.Equal(4, it.Affixes.Count);
                    Assert.True(Items.Affix(it.Affixes[3].Id)!.Slurry);
                    break;
            }
            p.J.Ch.Pack[p.J.Ch.Pack.IndexOf(it)] = null;
        }
        // The weights, near enough: a quarter up, a quarter a slurry power, the rest veins or a grade lost.
        Assert.InRange(seen["up"], 70, 130);
        Assert.InRange(seen["affix"], 70, 130);
        Assert.InRange(seen["nothing"], 90, 150);
        Assert.InRange(seen["down"], 50, 110);
        // A grade IV taken up becomes the bright grade, V.
        Assert.Equal("V", Crafting.Grade(4));
    }

    [Fact]
    public void At_Snibs_bench_he_does_it_in_his_words_and_what_is_seen_is_said()
    {
        var p = Town();
        p.W.Npc("snib").Flags["met"] = true;
        p.Give("slurry_jar", 2);
        var it = Carry(p, "iron_helm", 2, ("hale", 1), ("of_the_wolf", 0));
        Assert.True(p.J.Work(it.Uid, Crafting.Steep(p.J.Craft, it, "snib"), null));
        Assert.Equal(Crafting.Line("snib", "first.steep.before"), p.J.CraftSaid?.Before);
        Assert.Equal(Crafting.Line("snib", "first.steep"), p.J.CraftSaid?.Line);
        Assert.Contains(p.J.CraftSaid?.After, new[] { "up", "affix", "nothing", "down" }.Select(o => Crafting.Line("snib", $"steep.{o}")));
        Assert.Contains(it.History!, h => h.StartsWith("Steeped in one of Snib's jars"));
    }
}
'''
sub('tests/CraftersTests.cs', [
("""        p.Greet("maeca");
        Assert.Equal(1, p.Count("shed_fur_braid"));
    }
}
""",
"""        p.Greet("maeca");
        Assert.Equal(1, p.Count("shed_fur_braid"));
    }
""" + NEW),
])
