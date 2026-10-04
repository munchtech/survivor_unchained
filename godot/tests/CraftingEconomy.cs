using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>
/// Act 1's crafting economy played forward day by day (docs/CRAFTING_DESIGN.md 13.3–13.4):
/// the measured faucets, a survivor who crafts on what they wear with the real forge (quotes,
/// heat, terms), and the design's targets. The faucets, per won night, are the combat lead's
/// sweep at 71608a4 (deft bot, fodder gold at 2%, gear only from carriers): ember at the end,
/// champions, gold by people; the gear is the arena's own drop rule (ArenaRun.OnLoot, about 20
/// carriers at 60% and the boss's 2 + tier / 2). By day: the Verge's rates for a few beasts,
/// and Act 1's quest gold (about 800) and story prices (about 500) spread over its days.
/// </summary>
public class CraftingEconomy(ITestOutputHelper log)
{
    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];
    static readonly string[] Peoples = ["pack", "dead", "lamplings", "kerchiefs"];
    // Per tier 1..3: ember at the end (median), champions, the Kerchiefs' gold and the others'.
    static readonly int[] Ember = [57, 62, 67], Champs = [864, 1052, 1079], KerchiefGold = [2570, 3320, 2796], OtherGold = [11, 22, 16];

    sealed class Tally
    {
        public double Earned, Spent;
        public int Crafts, FirstCraftDay = -1, WeaponRare = -1, WeaponEpic = -1;
        public readonly List<int> CraftsByDay = new();
        public readonly List<int> ShardsByNight = new();
        public int Worked;
        public readonly Dictionary<string, int> ByPiece = new();
        public string Log = "";
    }

    /// <summary>One Act 1, <paramref name="days"/> long, a night every day; <paramref name="championGold"/>
    /// scales the gold arena champions drop (1: today).</summary>
    static Tally Play(int days, double championGold, uint seed, bool stay)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, seed);
        j.World.Npc("brannoc").Flags["met"] = true;
        var rng = new Rng(seed * 2654435761u + 1);
        var t = new Tally();
        j.Ch.Gold = 0;
        for (int day = 1; day <= days; day++)
        {
            j.World.Day = day;
            int tier = day <= days * 3 / 10 ? 1 : day <= days * 7 / 10 ? 2 : 3;
            string people = Peoples[(day - 1) % Peoples.Length];
            bool story = day % 3 == 0;
            double gold = 0;
            // The night: shards and the people's own, by the real rule; gold; the carriers' gear.
            var champs = people switch
            {
                "pack" => new Dictionary<Family, int> { [Family.Wolf] = Champs[tier - 1] * 6 / 10, [Family.Boar] = Champs[tier - 1] * 4 / 10 },
                "dead" => new Dictionary<Family, int> { [Family.Undead] = Champs[tier - 1] },
                "lamplings" => new Dictionary<Family, int> { [Family.Lampling] = Champs[tier - 1] },
                _ => new Dictionary<Family, int> { [Family.Kerchief] = Champs[tier - 1] },
            };
            var y = Crafting.Night(people, tier, story, Ember[tier - 1], stay ? 4 : 0, true, false, champs);
            j.Carry(y, "The night");
            t.ShardsByNight.Add(y.Kept.GetValueOrDefault(Crafting.Shard));
            gold += people == "kerchiefs" ? KerchiefGold[tier - 1] * championGold : OtherGold[tier - 1];
            var drops = new List<ItemInstance>();
            int carriers = 20;
            for (int k = 0; k < carriers; k++)
                if (rng.Next() < 0.6) drops.Add(Inventory.Make(j.Ch, PlainGear[rng.Int(0, PlainGear.Length - 1)], rarity: Rarity(rng, tier, 1), seed: (uint)rng.Int(1, int.MaxValue - 1), dropped: true));
            for (int k = 0; k < 2 + tier / 2; k++)
                drops.Add(Inventory.Make(j.Ch, PlainGear[rng.Int(0, PlainGear.Length - 1)], rarity: Math.Max(1, Rarity(rng, tier, 1.5)), seed: (uint)rng.Int(1, int.MaxValue - 1), dropped: true));
            // By day: a few of the Verge's beasts, the quests' gold, the story's prices.
            if (rng.Next() < 0.55) Give(j, "wolf_pelt", 1 + rng.Int(0, 1));
            if (rng.Next() < 0.5) Give(j, "boar_hide", 1);
            gold += 800.0 / days;
            j.Ch.Gold += gold;
            t.Earned += gold;
            j.Ch.Gold = Math.Max(0, j.Ch.Gold - 500.0 / days);

            // What is kept: a finer piece than the one worn is worn; everything else is broken down.
            j.World.Time = TimeOfDay.Day;
            foreach (var it in drops)
            {
                var slot = Items.SlotFor(Items.Get(it.Def))!.Value;
                if (slot == EquipSlot.Ring1 && j.Ch.Equipment.Ring1 != null && (j.Ch.Equipment.Ring2 == null || j.Ch.Equipment.Ring2.Rarity < j.Ch.Equipment.Ring1.Rarity)) slot = EquipSlot.Ring2;
                var worn = j.Ch.Equipment[slot];
                Inventory.AddToPack(j.Ch, it);
                if (worn == null || Better(it, worn))
                {
                    Inventory.Equip(j.Ch, it, slot);
                    if (worn != null && Inventory.Find(j.Ch, worn.Uid) is { InPack: true }) Break(j, worn);
                }
                else Break(j, it);
            }

            // The forge: the spender works what it wears while it can pay.
            double before = j.Ch.Gold;
            int crafts = 0;
            for (int guard = 0; guard < 60 && Next(j) is { } job; guard++)
            {
                if (!j.Work(job.Uid, job.Q, null)) break;
                t.ByPiece[job.Uid] = t.ByPiece.GetValueOrDefault(job.Uid) + 1;
                crafts++;
            }
            t.Spent += before - j.Ch.Gold;
            t.Crafts += crafts;
            t.CraftsByDay.Add(crafts);
            if (crafts > 0 && t.FirstCraftDay < 0) t.FirstCraftDay = day;
            int wr = j.Ch.Equipment.Weapon!.Rarity;
            if (wr >= 2 && t.WeaponRare < 0) t.WeaponRare = day;
            if (wr >= 3 && t.WeaponEpic < 0) t.WeaponEpic = day;
            t.Log += $"day {day,2} t{tier} {people,-9} gold +{gold,6:0} have {j.Ch.Gold,6:0}  iron {Inventory.Count(j.Ch, Crafting.Iron),3}  shards {Inventory.Count(j.Ch, Crafting.Shard),3}  crafts {crafts,2}  weapon {Items.RarityNames[wr]}\n";
        }
        // Fully worked by the forge: worked three times or more, every seam filled and at the piece's cap
        // (a lucky drop already at its cap is the world's doing, not the forge's).
        t.Worked = Items.EquipSlots.Select(s => j.Ch.Equipment[s]).Count(it => it != null && Crafting.Seams(it) > 0 && t.ByPiece.GetValueOrDefault(it.Uid) >= 3 && Crafting.OpenSeams(it) == 0
            && it.Affixes.All(x => Items.Affix(x.Id) is { } d && (d.Kindled != null || d.Grants != null || x.Tier >= Crafting.Cap(it))));
        return t;
    }

    static int Rarity(Rng r, int tier, double luck)
    {
        double roll = r.Next() / luck;
        return roll < 0.04 + tier * 0.01 ? 3 : roll < 0.2 + tier * 0.02 ? 2 : roll < 0.65 ? 1 : 0;
    }

    static bool Better(ItemInstance it, ItemInstance worn) =>
        it.Rarity > worn.Rarity || it.Rarity == worn.Rarity && it.Affixes.Sum(x => x.Tier + 1) > worn.Affixes.Sum(x => x.Tier + 1) + 1;

    static void Give(Journey j, string m, int n) => Inventory.AddToPack(j.Ch, Inventory.Make(j.Ch, m, n));

    static void Break(Journey j, ItemInstance it)
    {
        var q = Crafting.BreakDown(j.Craft, it);
        if (q.Ok) Crafting.Do(j.Craft, it, q, new Rng(1));
    }

    /// <summary>The next craft worth doing on what is worn, cheapest answer first: remake the
    /// weapon; temper the lowest grade; fill an open seam; cage a coal; rekindle a piece that
    /// still has tempering to take.</summary>
    static (string Uid, Quote Q)? Next(Journey j)
    {
        var x = j.Craft;
        var worn = Items.EquipSlots.Select(s => j.Ch.Equipment[s]).Where(it => it != null && Crafting.Workable(it)).Select(it => it!).ToList();
        var w = j.Ch.Equipment.Weapon!;
        if (Crafting.Remake(x, w) is { Ok: true } rq) return (w.Uid, rq);
        var tempers = worn.SelectMany(it => it.Affixes.Select((a, k) => (it, k, a.Tier))).OrderBy(p => p.Tier)
            .Select(p => (p.it.Uid, Q: Crafting.Temper(x, p.it, p.k))).Where(p => p.Q.Ok).ToList();
        if (tempers.Count > 0) return tempers[0];
        foreach (var it in worn.Where(it => Crafting.OpenSeams(it) > 0))
            foreach (var (m, a) in Crafting.WorkInChoices(it).OrderByDescending(c => Inventory.Count(j.Ch, c.Material)))
                if (Crafting.WorkIn(x, it, m, a) is { Ok: true } wq) return (it.Uid, wq);
        int kindled = worn.Sum(it => it.Affixes.Count(a => Items.Affix(a.Id)?.Kindled != null));
        if (kindled < 2)
            foreach (var it in worn.Where(it => it.Rarity >= 2 && it.Affixes.All(a => Items.Affix(a.Id)?.Kindled == null)))
                foreach (var c in Crafting.Coals(j.Ch, it, j.World.Day))
                {
                    // Over the lowest plain affix when no seam is open.
                    int over = Crafting.OpenSeams(it) > 0 ? -1 : it.Affixes.Select((a, k) => (a.Tier, k)).OrderBy(p => p.Tier).First().k;
                    if (Crafting.Cage(x, it, c, over) is { Ok: true } cq) return (it.Uid, cq);
                }
        foreach (var it in worn.Where(it => it.Heat < 4 && it.Affixes.Any(a => a.Tier < Crafting.Cap(it))))
            if (Crafting.Rekindle(x, it) is { Ok: true } kq) return (it.Uid, kq);
        return null;
    }

    [Fact]
    public void Act_one_crafting_meets_its_targets()
    {
        const int days = 10;
        var runs = Enumerable.Range(0, 8).Select(s => Play(days, 1, (uint)(101 + s * 7), s % 2 == 0)).ToList();
        var cut = Enumerable.Range(0, 8).Select(s => Play(days, 0.1, (uint)(101 + s * 7), s % 2 == 0)).ToList();
        log.WriteLine(runs[0].Log);
        void Report(string name, List<Tally> rs) => log.WriteLine(
            $"{name}: first craft day {Med(rs.Select(r => r.FirstCraftDay))}, crafts a day {Med(rs.SelectMany(r => r.CraftsByDay)):0.0} (max {rs.SelectMany(r => r.CraftsByDay).Max()}), " +
            $"weapon rare day {Med(rs.Select(r => r.WeaponRare))}, epic day {Med(rs.Select(r => r.WeaponEpic))}, fully worked {Med(rs.Select(r => r.Worked))}, " +
            $"gold spent {Med(rs.Select(r => r.Spent / Math.Max(1, r.Earned))):0%} of {Med(rs.Select(r => r.Earned)):0} earned, shards a night {Med(rs.SelectMany(r => r.ShardsByNight))}");
        Report("today's gold", runs);
        Report("champion gold at a tenth", cut);
        log.WriteLine(cut[0].Log);

        // The targets (design 13.3), held on the economy crafting asks for: arena champions paying a
        // tenth of the day's gold (combat's one line; today's Kerchief nights pay 2.5k-3.3k, which
        // buys the whole forge in a night). The first craft on day 1 or 2; the starting weapon rare
        // by day 4 and epic by day 5 to 8; the forge finishes at most two pieces in an act; a won
        // night's shards pay for a cage or a rekindle; crafting takes 30-70% of the gold.
        Assert.InRange(Med(cut.Select(r => r.FirstCraftDay)), 1, 2);
        Assert.InRange(Med(cut.Select(r => r.WeaponRare)), 1, 4);
        Assert.InRange(Med(cut.Select(r => r.WeaponEpic)), 5, 8);
        Assert.InRange(Med(cut.Select(r => r.Worked)), 0, 2);
        Assert.InRange(Med(cut.SelectMany(r => r.ShardsByNight)), 4, 8);
        Assert.InRange(Med(cut.Select(r => r.Spent / Math.Max(1, r.Earned))), 0.3, 0.7);
    }

    static double Med(IEnumerable<double> xs)
    {
        var s = xs.OrderBy(v => v).ToList();
        return s.Count == 0 ? double.NaN : s[s.Count / 2];
    }

    static int Med(IEnumerable<int> xs) => (int)Med(xs.Select(v => (double)v));
}
