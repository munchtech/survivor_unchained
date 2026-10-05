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
        p.J.Ch.Belt.Remove("health_draught");
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
                    // One power past what the forge can do: above the piece's cap (an epic's IV), to the bright V.
                    Assert.Equal(q.Grade, it.Affixes[q.Index].Tier);
                    Assert.Equal(Crafting.Bright, q.Grade);
                    Assert.True(q.Grade > Crafting.Cap(it));
                    Assert.Equal(before.Where((a, i) => i != q.Index), after.Where((a, i) => i != q.Index));
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

    /* ------------------------------------------------------------- Marks -- */

    static Route Table()
    {
        var p = Town();
        p.W.Npc("vonnra").Flags["met"] = true;
        p.W.Facts["toll.paid"] = true;
        p.Give("ember_shard", 20);
        return p;
    }

    /// <summary>A ruler's thing as it falls: made at its grade, the Mark in it at the same grade.</summary>
    static ItemInstance RulerThing(Route p, string people, int grade)
    {
        var d = Crafting.Rules.Mark.Drops[people];
        var it = Inventory.Make(p.J.Ch, d.Item, rarity: grade);
        Assert.True(Inventory.AddToPack(p.J.Ch, it));
        return it;
    }

    [Fact]
    public void Each_peoples_ruler_leaves_its_own_mark_finer_the_harder_the_map()
    {
        // The four Marks combat proved, one to each people, each a thing of theirs.
        Assert.Equal(new[] { "dead", "kerchiefs", "lamplings", "pack" }, Crafting.Rules.Mark.Drops.Keys.OrderBy(k => k));
        Assert.Equal(Marks.All.OrderBy(m => m), Crafting.Rules.Mark.Drops.Values.Select(d => d.Mark).OrderBy(m => m));
        foreach (var d in Crafting.Rules.Mark.Drops.Values)
        {
            Assert.Equal(ItemKind.Trophy, Items.Get(d.Item).Kind);
            Assert.True(Items.Affix(d.Mark)!.Mark);
            Assert.False(Crafting.Bindable(Items.Affix(d.Mark)));
        }
        var rng = new Rng(11);
        var low = Enumerable.Range(0, 400).Select(_ => Crafting.RulerMark("pack", 1, rng)).Where(m => m != null).Select(m => m!.Value.Grade).ToList();
        var high = Enumerable.Range(0, 400).Select(_ => Crafting.RulerMark("pack", 16, rng)).Where(m => m != null).Select(m => m!.Value.Grade).ToList();
        // About half the rulers leave one; tier 1's are grade I or II, tier 16's the last, VI.
        Assert.InRange(low.Count, 160, 240);
        Assert.All(low, g => Assert.InRange(g, 0, 1));
        Assert.All(high, g => Assert.Equal(5, g));
        // Fallen at grade III, the thing carries its Mark at III.
        var p = Table();
        var thing = RulerThing(p, "lamplings", 2);
        Assert.Equal((Marks.FallingStar, 2), (Crafting.MarkIn(thing)!.Id, Crafting.MarkIn(thing)!.Tier));
    }

    [Fact]
    public void Vonnra_writes_a_mark_into_a_seam_and_the_maps_wear_it()
    {
        var p = Table();
        var helm = Inventory.Make(p.J.Ch, "iron_helm", rarity: 2, affixes: new() { new AffixRoll { Id = "hale", Tier = 1 } });
        p.J.Ch.Equipment[EquipSlot.Head] = helm;
        var bone = RulerThing(p, "pack", 3);
        var q = Crafting.Inscribe(p.J.Craft, helm, bone);
        Assert.True(q.Ok, q.Blocked);
        Assert.True(p.J.Work(helm.Uid, q, null));
        // In the open seam, at the thing's grade; the thing is used up; her words, and the history.
        Assert.Equal((Marks.Ravine, 3), (helm.Affixes[1].Id, helm.Affixes[1].Tier));
        Assert.Null(Inventory.Find(p.J.Ch, bone.Uid));
        Assert.Equal(Crafting.Line("vonnra", "first.mark"), p.J.CraftSaid?.Line);
        Assert.Contains(helm.History!, h => h.StartsWith("Marked at Vonnra's table"));
        // Worn, the kit carries it at its strength (grade IV of VI: 0.6) for the maps to wear.
        Assert.Equal(0.6, Character.Kit(p.J.Ch).Marks[Marks.Ravine], 3);
        // A mark has the grade it came with: no forge tempers it.
        Assert.NotNull(Crafting.Temper(p.J.Craft, helm, 1).Blocked);
        // One mark to a piece: a second goes where the first was.
        var glass = RulerThing(p, "lamplings", 0);
        var again = Crafting.Inscribe(p.J.Craft, helm, glass);
        Assert.Equal(1, again.Index);
        Assert.True(p.J.Work(helm.Uid, again, null));
        Assert.Equal(2, helm.Affixes.Count);
        Assert.Equal(Marks.FallingStar, helm.Affixes[1].Id);
        Assert.False(Character.Kit(p.J.Ch).Marks.ContainsKey(Marks.Ravine));
    }

    [Fact]
    public void Three_marks_are_worn_at_once_and_the_same_mark_twice_is_the_finer()
    {
        var p = Table();
        var slots = new[] { EquipSlot.Head, EquipSlot.Body, EquipSlot.Amulet, EquipSlot.Ring1, EquipSlot.Ring2 };
        var defs = new[] { "iron_helm", "chain_shirt", "bone_amulet", "silver_ring", "copper_ring" };
        var marks = new[] { (Marks.Ravine, 1), (Marks.FallingStar, 2), (Marks.Ravine, 4), (Marks.OpenGate, 0), (Marks.Gyre, 5) };
        for (int i = 0; i < slots.Length; i++)
            p.J.Ch.Equipment[slots[i]] = Inventory.Make(p.J.Ch, defs[i], rarity: 2, affixes: new() { new AffixRoll { Id = marks[i].Item1, Tier = marks[i].Item2 } });
        var worn = Character.Kit(p.J.Ch).Marks;
        Assert.Equal(Crafting.Rules.Mark.Worn, worn.Count);
        Assert.Equal(0.8, worn[Marks.Ravine], 3);
        Assert.Equal(0.4, worn[Marks.FallingStar], 3);
        Assert.Contains(Marks.OpenGate, worn.Keys);
        Assert.DoesNotContain(Marks.Gyre, worn.Keys);
    }

    /* ---------------------------------------------------- the scars' depth -- */

    [Fact]
    public void A_scar_pays_deeper_the_longer_one_stays_and_glass_once_the_stream_is_clean()
    {
        var none = new Dictionary<Family, int>();
        int Shards(double past, bool won = true) => Crafting.Night("pack", 1, false, 10, past, won, false, none).Kept.GetValueOrDefault(Crafting.Shard);
        // A shard every two minutes past the win, to thirty; then a shard a minute: truly endless.
        Assert.Equal(5, Shards(10));
        Assert.Equal(15, Shards(30));
        Assert.Equal(25, Shards(40));
        Assert.Equal(105, Shards(120));
        Assert.Equal(0, Shards(40, won: false));
        // While the stream is sick, Snib sells the gamble; once it is clean, a scar stayed in past the hour gives it.
        Assert.Equal(0, Crafting.Night("pack", 1, false, 10, 90, true, false, none).Kept.GetValueOrDefault("scar_glass"));
        Assert.Equal(0, Crafting.Night("pack", 1, false, 10, 59, true, false, none, cured: true).Kept.GetValueOrDefault("scar_glass"));
        Assert.Equal(1, Crafting.Night("pack", 1, false, 10, 60, true, false, none, cured: true).Kept["scar_glass"]);
        Assert.Equal(2, Crafting.Night("pack", 1, false, 10, 125, true, false, none, cured: true).Kept["scar_glass"]);
        // A miniboss carries out two of its people's material.
        Assert.Equal(2, Crafting.Night("dead", 1, false, 10, 0, true, false, none, new Dictionary<Family, int> { [Family.Undead] = 1 }).Kept["bone_dust"]);
        // The glass steeps by hand as a jar does, after the jars are gone.
        var p = Town();
        p.Give("scar_glass");
        var it = Carry(p, "iron_helm", 2, ("hale", 1));
        var q = Crafting.Steep(p.J.Craft, it);
        Assert.True(q.Ok, q.Blocked);
        Assert.Equal(1, q.Takes["scar_glass"]);
        Assert.True(Crafting.Do(p.J.Craft, it, q, new Rng(4)));
        Assert.Equal(0, p.Count("scar_glass"));
        Assert.True(Crafting.Slurried(it));
    }

    /* --------------------------------------------------------- item level -- */

    [Fact]
    public void Gear_from_a_harder_map_rolls_the_finer_grade_more_often()
    {
        var p = Town();
        double Finer(int? level)
        {
            int finer = 0, all = 0;
            for (uint s = 1; s <= 600; s++)
            {
                var it = Inventory.Make(p.J.Ch, "iron_helm", rarity: 2, seed: s * 7919, dropped: true, level: level);
                Assert.Equal(level ?? p.J.Ch.Level, it.Level);
                // Past level 25 the grades rise (loot's rule, docs/design/LOOT_DESIGN.md §4.3): read within the band.
                foreach (var a in it.Affixes) { all++; if (a.Tier - Drops.GradeShift(it.Level) == 2) finer++; }
            }
            return finer / (double)all;
        }
        // By day a coin; a first map's level the same; a tier-11 map's (level 30) nine in ten.
        Assert.InRange(Finer(null), 0.43, 0.57);
        Assert.InRange(Finer(10), 0.43, 0.57);
        Assert.InRange(Finer(30), 0.84, 0.95);
        Assert.Equal(0.7, Crafting.FinerGrade(18), 6);
        // Never past the rarity's own finer grade, but for the grades depth adds past level 25 (loot's §4.3).
        Assert.All(Enumerable.Range(1, 200).Select(s => Inventory.Make(p.J.Ch, "iron_helm", rarity: 2, seed: (uint)s, level: 40)),
            it => Assert.All(it.Affixes, a => Assert.True(a.Tier <= Crafting.Cap(it) + Drops.GradeShift(it.Level))));
        // Only gear carries a level.
        Assert.Null(Inventory.Make(p.J.Ch, "wolf_pelt", level: 30).Level);
    }

    /* ----------------------------------------------------- Rook's shelves -- */

    [Fact]
    public void Rooks_storeroom_grows_by_shelves_bought_dearer_each_time()
    {
        var p = Town();
        // The room comes with one shelf of 24.
        Assert.Equal(WorldState.Shelf, p.W.Stash.Count);
        Assert.Equal(1, p.W.Shelves);
        p.J.Ch.Gold = 100_000;
        var paid = new List<int>();
        while (Crafting.ShelfPrice(p.J.Craft) is int price)
        {
            double gold = p.J.Ch.Gold;
            Assert.True(Crafting.BuyShelf(p.J.Craft));
            Assert.Equal(gold - price, p.J.Ch.Gold);
            // Rook's words over it: the second shelf's, then the later ones' (the story lead's).
            Assert.Equal(paid.Count == 0 ? Crafting.Rules.Rook.Shelf : Crafting.Rules.Rook.ShelfMore, Crafting.ShelfSaid(p.W));
            paid.Add(price);
        }
        Assert.NotNull(Crafting.Rules.Rook.Shelf);
        Assert.NotNull(Crafting.Rules.Night.GlassFirst);
        // To the most there can be, each dearer than the last or as dear; the second is about a Kerchief night's gold.
        Assert.Equal(Crafting.Rules.Shelves.Most, p.W.Shelves);
        Assert.Equal(Crafting.Rules.Shelves.Most * WorldState.Shelf, p.W.Stash.Count);
        Assert.InRange(paid[0], 250, 400);
        Assert.Equal(paid.OrderBy(x => x), paid);
        Assert.False(Crafting.BuyShelf(p.J.Craft));
        // Not without the gold.
        var q = Town();
        q.J.Ch.Gold = 10;
        Assert.False(Crafting.BuyShelf(q.J.Craft));
        Assert.Equal(1, q.W.Shelves);
    }

    [Fact]
    public void A_storeroom_from_before_shelves_keeps_its_two_and_a_short_one_is_made_whole()
    {
        var p = Town();
        var d = Json.Parse<SaveData>(Json.Write(p.J.ToSave(new SaveLocation { Zone = "waystation" })));
        d.World.Stash = Enumerable.Repeat<ItemInstance?>(null, 48).ToList();
        d.World.Stash[40] = new ItemInstance { Uid = "kept", Def = "iron_helm", Rarity = 1 };
        var back = Saves.Migrate(Json.Parse<SaveData>(Json.Write(d)));
        Assert.Equal(2, back.World.Shelves);
        Assert.Equal("kept", back.World.Stash[40]!.Uid);
        d.World.Stash = Enumerable.Repeat<ItemInstance?>(null, 30).ToList();
        Assert.Equal(48, Saves.Migrate(Json.Parse<SaveData>(Json.Write(d))).World.Stash.Count);
    }

    /* ------------------------------------------------------------ Charts -- */

    static ItemInstance ChartOf(Route p, string people, int rarity, params string[] mods)
    {
        var c = new Maps.Chart { Tier = 2, People = people, Seed = 7, Rarity = rarity, Mods = mods.ToList(), Name = "The Test Ground" };
        Assert.True(p.J.GiveChart(c));
        return p.J.Ch.Satchel.First(i => i.Chart == c);
    }

    [Fact]
    public void A_chart_has_heat_and_ink_adds_a_mod_on_the_side_chosen()
    {
        var p = Table();
        p.W.Npc("wayfinder").Flags["met"] = true;
        var it = ChartOf(p, "pack", 0);
        Assert.Equal(Crafting.Rules.Charts.Heat[0], it.Heat);
        var rng = new Rng(5);
        // The foe's side: a prefix; it is a fine chart now, and the ink cost heat, a shard and gold.
        var q = Crafting.Ink(p.J.Craft, it, foe: true);
        Assert.True(q.Ok, q.Blocked);
        double gold = p.J.Ch.Gold;
        int shards = p.Count("ember_shard");
        Assert.True(Crafting.Do(p.J.Craft, it, q, rng));
        Assert.Single(it.Chart!.Mods);
        Assert.True(Maps.Charts.Mod(it.Chart.Mods[0]).Prefix);
        Assert.Equal(1, it.Chart.Rarity);
        Assert.Equal(1, it.Rarity);
        Assert.Equal(shards - 1, p.Count("ember_shard"));
        Assert.Equal(gold - q.Gold, p.J.Ch.Gold);
        Assert.InRange(it.Heat!.Value, 1, 2);
        // Three to a side at most.
        var full = ChartOf(p, "pack", 2, "signed", "twin", "restless");
        Assert.Contains("Three on the foe's side", Crafting.Ink(p.J.Craft, full, foe: true).Blocked);
        Assert.True(Crafting.Ink(p.J.Craft, full, foe: false).Ok);
        // Its ink set at no heat: nothing more is worked on it.
        full.Heat = 0;
        Assert.Contains("ink has set", Crafting.Ink(p.J.Craft, full, foe: false).Blocked);
        Assert.Contains("ink has set", Crafting.Scrape(p.J.Craft, full, "signed").Blocked);
    }

    [Fact]
    public void A_pinned_mod_holds_through_a_burn_and_scraping_takes_one_off()
    {
        var p = Table();
        p.W.Npc("wayfinder").Flags["met"] = true;
        p.Give("wolf_pelt", 4);
        p.Give("old_iron", 6);
        var it = ChartOf(p, "pack", 2, "signed", "twin", "thin_blood");
        it.Heat = it.HeatFull = 20;
        // Pinned with the Pack's own material.
        var pin = Crafting.Pin(p.J.Craft, it, "twin");
        Assert.Equal(2, pin.Takes["wolf_pelt"]);
        Assert.True(Crafting.Do(p.J.Craft, it, pin, new Rng(1)));
        Assert.Equal("twin", it.Chart!.Pinned);
        for (uint s = 1; s <= 30; s++)
        {
            var burn = Crafting.Burn(p.J.Craft, it);
            Assert.True(burn.Ok, burn.Blocked);
            it.Heat = 20;
            p.Give("ember_shard", 2);
            Assert.True(Crafting.Do(p.J.Craft, it, burn, new Rng(s)));
            // The pin holds; as many of each side as before.
            Assert.Contains("twin", it.Chart.Mods);
            Assert.Equal(2, it.Chart.Rolled.Count(m => m.Prefix));
            Assert.Equal(1, it.Chart.Rolled.Count(m => !m.Prefix));
            Assert.Equal(it.Chart.Mods.Count, it.Chart.Mods.Distinct().Count());
        }
        // Scraped, the pinned mod is gone and so is the pin; the chart is fine now, not rare.
        var scrape = Crafting.Scrape(p.J.Craft, it, "twin");
        Assert.Equal(3, scrape.Takes["old_iron"]);
        Assert.True(Crafting.Do(p.J.Craft, it, scrape, new Rng(2)));
        Assert.DoesNotContain("twin", it.Chart.Mods);
        Assert.Null(it.Chart.Pinned);
        Assert.Equal(1, it.Chart.Rarity);
    }

    [Fact]
    public void Annotating_writes_from_another_chart_of_the_same_ground_to_a_fifth_more_found()
    {
        var p = Table();
        p.W.Npc("wayfinder").Flags["met"] = true;
        var it = ChartOf(p, "dead", 1, "sleepless");
        Assert.Null(Crafting.AnnotateFrom(p.J.Ch, it));
        Assert.NotNull(Crafting.Annotate(p.J.Craft, it, null).Blocked);
        ChartOf(p, "pack", 0);
        Assert.Null(Crafting.AnnotateFrom(p.J.Ch, it));
        for (int k = 0; k < 4; k++)
        {
            var from = ChartOf(p, "dead", 0);
            Assert.Equal(from, Crafting.AnnotateFrom(p.J.Ch, it));
            var q = Crafting.Annotate(p.J.Craft, it, from);
            Assert.True(q.Ok, q.Blocked);
            int heat = it.Heat!.Value;
            Assert.True(Crafting.Do(p.J.Craft, it, q, new Rng(3)));
            Assert.Null(Inventory.Find(p.J.Ch, from.Uid));
            Assert.Equal(heat, it.Heat);
        }
        Assert.Equal(20, it.Chart!.Quality);
        Assert.Contains("As full of notes", Crafting.Annotate(p.J.Craft, it, ChartOf(p, "dead", 0)).Blocked);
    }
}
