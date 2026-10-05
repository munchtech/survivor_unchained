using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Crafting's second phase (docs/CRAFTING_DESIGN.md 7.2, 7.5, 10.1): Wenna's still-room
/// and flask, Brannoc's commissions, Greymuzzle's fang set, and Maeca's braid of shed fur.</summary>
public class CraftersTests
{
    static Route Town()
    {
        var p = Route.New();
        foreach (var n in new[] { "brannoc", "wenna", "maeca" }) p.W.Npc(n).Flags["met"] = true;
        p.W.Time = TimeOfDay.Day;
        p.J.Ch.Gold = 1000;
        return p;
    }

    /* ------------------------------------------------------------ Wenna -- */

    [Fact]
    public void Wenna_brews_a_draught_cheaper_than_the_shop_from_what_is_brought()
    {
        var p = Town();
        int before = p.Count("health_draught");
        Assert.False(Crafting.Brew(p.J.Craft, "health_draught").Ok);
        p.Give("bitterroot", 5);
        var q = Crafting.Brew(p.J.Craft, "health_draught");
        Assert.True(q.Ok, q.Blocked);
        Assert.Equal(2, q.Takes["bitterroot"]);
        Assert.True(q.Gold < Items.Get("health_draught").Value);
        double gold = p.J.Ch.Gold;
        Assert.True(p.J.Make(q));
        Assert.Equal(before + 1, p.Count("health_draught"));
        Assert.Equal(3, p.Count("bitterroot"));
        Assert.Equal(gold - q.Gold, p.J.Ch.Gold);
        // Her first brew says its own line; after, a brew's lines in turn.
        Assert.Equal(Crafting.Line("wenna", "first.brew"), p.J.CraftSaid?.Line);
        // As many as the bitterroot allows, in one press.
        Assert.Equal(1, Crafting.CanBrew(p.J.Craft, "health_draught", 5));
        Assert.Equal(3, Crafting.CanBrew(p.J.Craft, "antidote", 5));
        Assert.True(p.J.Make(Crafting.Brew(p.J.Craft, "antidote", 3)));
        Assert.Equal(Crafting.Line("wenna", "brew.antidote"), p.J.CraftSaid?.Line);
    }

    [Fact]
    public void The_first_moonpetal_draught_has_its_own_words_and_the_draught_key_keeps_it_for_a_deep_wound()
    {
        var p = Town();
        p.Give("moonpetal", 2);
        Assert.True(p.J.Make(Crafting.Brew(p.J.Craft, "moonpetal_draught")));
        Assert.Equal(Crafting.Line("wenna", "brew.moonpetal"), p.J.CraftSaid?.Line);
        Assert.True(p.J.Make(Crafting.Brew(p.J.Craft, "moonpetal_draught")));
        Assert.NotEqual(Crafting.Line("wenna", "brew.moonpetal"), p.J.CraftSaid?.Line);

        p.Enter("verge");
        var b = p.B!;
        int plain = p.Count("health_draught"), moon = p.Count("moonpetal_draught");
        Assert.True(plain > 0);
        // A scratch: the plain draught.
        b.Player.Hp = b.MaxHp * 0.7;
        p.J.Quaff(b);
        Assert.Equal(plain - 1, p.Count("health_draught"));
        Assert.Equal(moon, p.Count("moonpetal_draught"));
        // Most of it gone: the moonpetal, and it heals 60%.
        b.Player.Hp = b.MaxHp * 0.3;
        p.J.Quaff(b);
        Assert.Equal(moon - 1, p.Count("moonpetal_draught"));
        Assert.True(b.Player.Hp >= b.MaxHp * 0.85);
    }

    [Fact]
    public void Her_flask_is_filled_at_the_inn_overnight_a_bitterroot_a_draught_to_three()
    {
        var p = Town();
        foreach (var it in p.J.Ch.Pack.Where(x => x?.Def == "health_draught").ToList()) p.J.Ch.Pack[p.J.Ch.Pack.IndexOf(it)] = null;
        Assert.Equal(0, p.Count("health_draught"));
        var buy = Crafting.BuyFlask(p.J.Craft);
        Assert.True(buy.Ok, buy.Blocked);
        Assert.Equal(120, buy.Gold);
        Assert.True(p.J.Make(buy));
        Assert.False(Crafting.BuyFlask(p.J.Craft).Ok);
        // No bitterroot: dry, said once.
        Assert.Contains(Crafting.Line("wenna", "flask.dry"), p.Sleep());
        Assert.DoesNotContain(Crafting.Line("wenna", "flask.dry"), p.Sleep());
        // Two bitterroot: two draughts.
        p.Give("bitterroot", 2);
        var morning = p.Sleep();
        Assert.Contains(morning, l => l.Contains("two draughts"));
        Assert.Equal(2, p.Count("health_draught"));
        Assert.Equal(0, p.Count("bitterroot"));
        // Topped up to three, never past it.
        p.Give("bitterroot", 5);
        p.Sleep();
        Assert.Equal(3, p.Count("health_draught"));
        Assert.Equal(4, p.Count("bitterroot"));
        p.Sleep();
        Assert.Equal(3, p.Count("health_draught"));
    }

    [Fact]
    public void Her_bench_opens_with_the_clean_stream_and_her_standing_lifts_what_she_works_in()
    {
        var p = Town();
        Assert.Contains("Brew me something.", p.Offered("wenna"));
        var it = Inventory.Make(p.J.Ch, "bone_amulet", rarity: 2, affixes: new() { new AffixRoll { Id = "of_reach", Tier = 1 } });
        Inventory.AddToPack(p.J.Ch, it);
        p.Give("bitterroot", 6);
        Assert.NotNull(Crafting.WorkIn(p.J.Craft, it, "bitterroot", "of_the_physician", crafter: "wenna").Blocked);
        p.W.Facts["stream.clear"] = true;
        var q = Crafting.WorkIn(p.J.Craft, it, "bitterroot", "of_the_physician", crafter: "wenna");
        Assert.True(q.Ok, q.Blocked);
        Assert.Equal(0, q.Grade);
        p.W.Npc("wenna").Trust = 30;
        q = Crafting.WorkIn(p.J.Craft, it, "bitterroot", "of_the_physician", crafter: "wenna");
        Assert.Equal(1, q.Grade);
        Assert.True(p.J.Work(it.Uid, q, null));
        Assert.Equal(1, it.Affixes.Single(a => a.Id == "of_the_physician").Tier);
        Assert.Equal(Crafting.Line("wenna", "first.workIn"), p.J.CraftSaid?.Line);
    }

    /* -------------------------------------------------------- Brannoc -- */

    [Fact]
    public void A_commission_is_ready_the_next_morning_uncommon_hot_and_his()
    {
        var p = Town();
        p.Give("wolf_pelt", 3);
        p.Give("old_iron", 2);
        var pats = Crafting.Patterns(p.J.Craft);
        Assert.Contains(pats, x => x.Def == "iron_helm" && x.Open);
        Assert.Contains(pats, x => x.Def == "chain_shirt" && !x.Open && x.Needs == "respect 20");
        Assert.Contains(pats, x => x.Def == Callings.Archetype("warden").Weapons[0] && x.Open);
        Assert.NotNull(Crafting.Commission(p.J.Craft, "chain_shirt", "wolf_pelt", "of_the_wolf").Blocked);

        var q = Crafting.Commission(p.J.Craft, "iron_helm", "wolf_pelt", "of_the_wolf");
        Assert.True(q.Ok, q.Blocked);
        Assert.True(p.J.Make(q));
        Assert.Equal(Crafting.Line("brannoc", "commission.take"), p.J.CraftSaid?.Line);
        Assert.Equal(0, p.Count("wolf_pelt"));
        // One on his bench at a time; not before morning.
        p.Give("wolf_pelt", 3);
        p.Give("old_iron", 2);
        Assert.NotNull(Crafting.Commission(p.J.Craft, "leather_cap", "wolf_pelt", "of_the_wolf").Blocked);
        Assert.Null(p.J.CollectCommission());
        Assert.Null(p.Marker("brannoc"));

        p.Sleep();
        Assert.Equal("!", p.Marker("brannoc"));
        var it = p.J.CollectCommission();
        Assert.NotNull(it);
        Assert.Equal("iron_helm", it!.Def);
        Assert.Equal(1, it.Rarity);
        Assert.Equal(0, it.Affixes.Single(a => a.Id == "of_the_wolf").Tier);
        Assert.Equal(it.HeatFull, it.Heat);
        Assert.Equal(Crafting.Rules.Heat[1], it.Heat);
        Assert.Contains("wolf_pelts", it.Marks!);
        Assert.Contains(it.History!, h => h.StartsWith("Made for you on Brannoc's anvil"));
        Assert.Equal(Crafting.Line("brannoc", "commission.ready"), p.J.CraftSaid?.Line);
        Assert.Null(p.Marker("brannoc"));
        Assert.Null(Crafting.Ordered(p.W));
    }

    [Fact]
    public void Greymuzzles_fang_is_set_in_a_weapon_or_amulet_outside_its_seams_and_the_Pack_knows_it()
    {
        var p = Town();
        p.Give("greymuzzle_fang");
        Assert.Contains("Greymuzzle's fang. Will you set it?", p.Offered("brannoc"));
        var weapon = p.J.Ch.Equipment.Weapon!;
        var helm = Inventory.Make(p.J.Ch, "iron_helm", rarity: 1);
        Inventory.AddToPack(p.J.Ch, helm);
        Assert.Empty(Crafting.Settable(p.J.Ch, helm));
        Assert.Equal(["greymuzzle_fang"], Crafting.Settable(p.J.Ch, weapon));
        int heat = weapon.Heat ?? 0, seams = Crafting.OpenSeams(weapon);
        var q = Crafting.Set(p.J.Craft, weapon, "greymuzzle_fang");
        Assert.True(q.Ok, q.Blocked);
        Assert.True(p.J.Work(weapon.Uid, q, null));
        Assert.Equal("greymuzzles", weapon.Setting);
        Assert.Equal(heat, weapon.Heat);
        Assert.Equal(seams, Crafting.OpenSeams(weapon));
        Assert.StartsWith("Greymuzzle's ", Inventory.Name(weapon));
        Assert.Contains(Inventory.Mods(weapon), m => m.Stat == Stat.VsOf(Family.Wolf) && m.Value >= 0.3);
        Assert.Equal(0, p.Count("greymuzzle_fang"));
        Assert.Contains("greymuzzle_fang", Inventory.WorldTags(p.J.Ch));
        Assert.Equal(Crafting.Line("brannoc", "fang.set"), p.J.CraftSaid?.Line);
        Assert.Contains(weapon.History!, h => h.StartsWith("Set with Greymuzzle's fang"));
        Assert.DoesNotContain("Greymuzzle's fang. Will you set it?", p.Offered("brannoc"));
        // It never rolls on a drop.
        Assert.DoesNotContain(Enumerable.Range(0, 300).Select(s => Inventory.Make(null, "bone_amulet", rarity: 3, seed: (uint)s + 1)),
            it => it.Affixes.Any(a => a.Id == "greymuzzles"));
    }

    [Fact]
    public void Maeca_sees_the_fang_worn_once_and_thinks_less_of_you()
    {
        var p = Town();
        p.Give("greymuzzle_fang");
        var weapon = p.J.Ch.Equipment.Weapon!;
        Assert.True(p.J.Work(weapon.Uid, Crafting.Set(p.J.Craft, weapon, "greymuzzle_fang"), null));
        p.Enter("waystation");
        var maeca = p.Zone!.Actors["maeca"];
        double before = p.W.Npc("maeca").Affection;
        Assert.Equal("That's his. Wear it where I can't see it.", maeca.Urgent!());
        maeca.Spoken!("That's his. Wear it where I can't see it.");
        Assert.Equal(before - 10, p.W.Npc("maeca").Affection);
        Assert.Null(maeca.Urgent!());
        maeca.Spoken!("That's his. Wear it where I can't see it.");
        Assert.Equal(before - 10, p.W.Npc("maeca").Affection);
    }

    /* ----------------------------------------------------------- Maeca -- */

    [Fact]
    public void With_the_Pack_allied_Maeca_braids_what_they_shed_by_the_next_day()
    {
        var p = Town();
        p.W.Facts["pack.allied"] = true;
        var (said, _) = p.Greet("maeca");
        Assert.Contains("leaving fur on the thorn", said);
        Assert.Equal(0, p.Count("shed_fur_braid"));
        // Not the same day.
        Assert.DoesNotContain("bites the end off", p.Greet("maeca").Said);
        p.Sleep();
        Assert.Contains("bites the end off", p.Greet("maeca").Said);
        Assert.Equal(1, p.Count("shed_fur_braid"));
        var braid = p.J.Ch.Pack.First(x => x?.Def == "shed_fur_braid")!;
        Assert.Contains(braid.History!, h => h.StartsWith("Braided by Maeca from what the Pack shed"));
        Assert.Contains(Inventory.Mods(braid), m => m.Stat == Stat.FromOf(Family.Wolf) && m.Value >= 0.3);
        // Once.
        p.Sleep();
        p.Greet("maeca");
        Assert.Equal(1, p.Count("shed_fur_braid"));
    }

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
            // What it came to is kept on the quote, said plainly, and names the power it touched.
            var (said, mood) = Crafting.Outcome(it, q);
            switch (q.Outcome)
            {
                case "up":
                    Assert.Equal(before.Sum(a => a.Tier) + 1, after.Sum(a => a.Tier));
                    Assert.Equal(q.Grade, it.Affixes[q.Index].Tier);
                    Assert.Equal(before[q.Index].Tier + 1, q.Grade);
                    Assert.StartsWith(Items.Affix(q.Affix!)!.Name, said);
                    Assert.Equal(1, mood);
                    break;
                case "down":
                    Assert.Equal(before.Sum(a => a.Tier) - 1, after.Sum(a => a.Tier));
                    Assert.Equal(before[q.Index].Tier - 1, it.Affixes[q.Index].Tier);
                    Assert.Equal(-1, mood);
                    break;
                case "nothing": Assert.Equal(before, after); Assert.Equal(-1, q.Index); Assert.Equal(0, mood); break;
                case "affix":
                    // Past the seams: a fourth power, the slurry's, strong with a price.
                    Assert.Equal(4, it.Affixes.Count);
                    Assert.True(Items.Affix(it.Affixes[3].Id)!.Slurry);
                    Assert.Equal(3, q.Index);
                    Assert.Contains(Items.Affix(it.Affixes[3].Id)!.Text(0), said);
                    break;
            }
            // Set for good: no heat comes back to open it for the forge again.
            Assert.Equal(Crafting.SetForGood, Crafting.Rekindle(p.J.Craft, it).Blocked);
            Assert.Equal(Crafting.SetForGood, Crafting.Remake(p.J.Craft, it).Blocked);
            p.J.Ch.Pack[p.J.Ch.Pack.IndexOf(it)] = null;
        }
        // The weights, near enough: a quarter up, a quarter a slurry power, the rest veins or a grade lost.
        Assert.InRange(seen["up"], 70, 130);
        Assert.InRange(seen["affix"], 70, 130);
        Assert.InRange(seen["nothing"], 90, 150);
        Assert.InRange(seen["down"], 50, 110);
        // A grade IV taken up becomes the bright grade, V; nothing goes past it.
        Assert.Equal("V", Crafting.Grade(Crafting.Bright));
        for (uint s = 1; s <= 60; s++)
        {
            p.Give("slurry_jar");
            var it = Carry(p, "iron_helm", 3, ("hale", Crafting.Bright));
            var q = Crafting.Steep(p.J.Craft, it);
            Assert.True(Crafting.Do(p.J.Craft, it, q, new Rng(s * 104729)));
            Assert.True(it.Affixes[0].Tier <= Crafting.Bright);
            if (q.Outcome == "up") Assert.Fail("A bright grade cannot rise further: that is only the veins.");
            p.J.Ch.Pack[p.J.Ch.Pack.IndexOf(it)] = null;
        }
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
