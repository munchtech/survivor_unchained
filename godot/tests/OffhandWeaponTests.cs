using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-wire, level 8) The off-hand weapons: a short sword, a flanged mace and a smith's hammer join the shield as plain
/// off-hand bases, so a piece that falls can pick each stance her second set offers (Items.OffhandWeapons, Items.DropBase).
/// Everything here goes through the real roll (Drops.Roll, seeded) and the real equip (Inventory.Equip).</summary>
public class OffhandWeaponTests(ITestOutputHelper log)
{
    static Journey Warden(int level) => MapSim.Survivor("warden", level, 1, 5);
    static Func<double> Seq(int seed) { var r = new Random(seed); return r.NextDouble; }
    static readonly string[] Peoples = ["pack", "dead", "lamplings", "kerchiefs"];

    /// <summary>The off-hand kinds the shares are read by: a piece by its base (a named shield is a shield).</summary>
    static string KindOf(ItemDef def) => Drops.BaseOf(def)?.Id switch
    {
        "watch_buckler" => "shield", "short_sword" => "blade", "flanged_mace" => "mace", "smiths_hammer" => "hammer", _ => "other",
    };

    [Theory]
    [InlineData("short_sword", "twin_blades")]
    [InlineData("flanged_mace", "mace")]
    [InlineData("smiths_hammer", "mace")]
    [InlineData("watch_buckler", "shield")]
    public void Each_off_hand_base_drops_equips_to_the_off_hand_and_sets_its_stance(string id, string stance)
    {
        var j = Warden(12);
        var ch = j.Ch;
        ItemInstance? got = null;
        for (int s = 0; s < 4000 && got == null; s++)
            got = Drops.Roll(new DropCtx { Ch = ch, World = j.World, Source = DropSource.Champion, Level = 10, People = Peoples[s % 4], R = Seq(s) })
                .Select(d => d.Item).FirstOrDefault(it => it?.Def == id);
        Assert.NotNull(got);
        var def = Items.Get(id);
        Assert.Equal(ItemKind.Offhand, def.Kind);
        Assert.True(def.Base);
        Assert.Equal(10, got!.Level);
        // It rolls only what an off-hand may (the kind's affix table).
        Assert.All(got.Affixes, a => Assert.Contains(ItemKind.Offhand, Items.Affix(a.Id)!.Slots));

        Assert.True(Inventory.AddToPack(ch, got));
        // Her own choice is another stance: the piece she wears decides.
        ch.Stance = TaughtBuilds.Of("warden")!.Stance!.Offers.First(o => o != stance);
        Assert.True(Inventory.Equip(ch, got, EquipSlot.Offhand));
        Assert.Same(got, ch.Equipment[EquipSlot.Offhand]);
        Assert.Equal(stance, SkillBook.WornStance(ch));
        Assert.Equal(stance, SkillBook.StanceOf(ch));
        Assert.DoesNotContain(ch.Pack, p => p?.Uid == got.Uid);
    }

    [Fact]
    public void The_off_hand_weapons_fall_only_from_the_level_the_stance_opens()
    {
        int from = TaughtBuilds.Of("warden")!.Stance!.Level;
        string[] weapons = ["short_sword", "flanged_mace", "smiths_hammer"];
        Assert.All(weapons, id => Assert.Equal(from, Items.Get(id).DropsFrom));
        var j = Warden(from - 1);
        var defs = Enumerable.Range(0, 3000).SelectMany(s => Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Champion,
            Level = from - 1, People = Peoples[s % 4], R = Seq(s) })).Where(d => d.Item != null).Select(d => d.Item!.Def).ToList();
        Assert.DoesNotContain(defs, weapons.Contains);
        Assert.Contains("watch_buckler", defs);
    }

    [Theory]
    [InlineData(10)]
    [InlineData(20)]
    [InlineData(30)]
    public void Over_ten_thousand_drops_each_off_hand_kind_keeps_its_share(int level)
    {
        var j = Warden(level);
        var R = Seq(7000 + level);
        var count = new Dictionary<string, int> { ["shield"] = 0, ["blade"] = 0, ["mace"] = 0, ["hammer"] = 0, ["other"] = 0 };
        int gear = 0, offhand = 0;
        for (int k = 0; gear < 10_000; k++)
            foreach (var d in Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Champion, Level = level, People = Peoples[k % 4], R = R }))
            {
                if (d.Item is not { } it || gear >= 10_000) continue;
                var def = Items.Get(it.Def);
                if (Items.SlotFor(def) == null) continue;
                gear++;
                if (def.Kind != ItemKind.Offhand) continue;
                offhand++;
                count[KindOf(def)]++;
            }
        double Share(string kind) => (double)count[kind] / offhand;
        log.WriteLine($"level {level}: {gear} gear drops, {offhand} off-hands ({100.0 * offhand / gear:0.0}%): " +
            string.Join(", ", count.Select(c => $"{c.Key} {c.Value} ({100 * Share(c.Key):0.0}%)")));
        foreach (var kind in new[] { "blade", "mace", "hammer" }) Assert.InRange(Share(kind), 0.10, 0.30);
        Assert.True(Share("shield") >= 0.25, $"shields {Share("shield"):P1}");
        Assert.Equal(0, count["other"]);
    }
}
