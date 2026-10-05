using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The two kits (docs/CRAFTING_DESIGN.md 20.2, Rpg/Kits.cs): the night kit holds only what
/// differs from the day's and goes on by itself wherever the ember burns.</summary>
public class KitsTests
{
    static (Route P, ItemInstance Coal, ItemInstance Plain) Dressed()
    {
        var p = Route.New();
        var ch = p.J.Ch;
        // A plain amulet worn by day, and one with a coal caged in it carried.
        var plain = Inventory.Make(ch, "bone_amulet", 1, 2, affixes: new() { new AffixRoll { Id = "hale", Tier = 1 } });
        Assert.True(Inventory.Equip(ch, plain, EquipSlot.Amulet));
        var coal = Inventory.Make(ch, "bone_amulet", 1, 2, affixes: new() { new AffixRoll { Id = "of_the_first_spark", Tier = 1 } });
        Assert.True(Inventory.AddToPack(ch, coal));
        return (p, coal, plain);
    }

    [Fact]
    public void A_new_survivor_wears_the_same_by_night_as_by_day_and_is_not_shown_two_kits()
    {
        var p = Route.New();
        var ch = p.J.Ch;
        Assert.Equal(KitKind.Day, Kits.On(ch));
        foreach (var s in Items.EquipSlots)
        {
            Assert.Same(Kits.Piece(ch, KitKind.Day, s), Kits.Piece(ch, KitKind.Night, s));
            Assert.False(Kits.HasOwn(ch, KitKind.Night, s));
        }
        Assert.False(Kits.Shown(ch));
        // Putting the night's on changes nothing that is worn.
        var before = Items.EquipSlots.Select(s => ch.Equipment[s]?.Uid).ToList();
        Kits.Wear(ch, KitKind.Night);
        Assert.Equal(before, Items.EquipSlots.Select(s => ch.Equipment[s]?.Uid).ToList());
    }

    [Fact]
    public void A_coal_worn_by_night_is_set_aside_by_day_and_goes_on_with_the_night()
    {
        var (p, coal, plain) = Dressed();
        var ch = p.J.Ch;
        Assert.True(Kits.Shown(ch));
        Assert.True(Kits.Put(ch, KitKind.Night, coal, EquipSlot.Amulet));
        // By day the plain one is worn; the coal is set aside, not carried, and not lost.
        Assert.Same(plain, ch.Equipment.Amulet);
        Assert.Same(coal, Kits.Piece(ch, KitKind.Night, EquipSlot.Amulet));
        Assert.Equal(Store.Kit, Inventory.Find(ch, coal.Uid)!.Store);
        Assert.False(Inventory.Holds(ch, coal.Uid));
        Assert.Contains(coal, Inventory.Everything(ch));
        Assert.DoesNotContain(coal, ch.Pack);
        Assert.Empty(Character.Kit(ch).Kindled);
        // By night the coal is worn and kindles the ember; the plain one waits.
        Kits.Wear(ch, KitKind.Night);
        Assert.Same(coal, ch.Equipment.Amulet);
        Assert.Equal(Store.Kit, Inventory.Find(ch, plain.Uid)!.Store);
        Assert.Contains("of_the_first_spark", Character.Kit(ch).Kindled);
        // And by day again.
        Kits.Wear(ch, KitKind.Day);
        Assert.Same(plain, ch.Equipment.Amulet);
        Assert.Same(coal, Kits.Piece(ch, KitKind.Night, EquipSlot.Amulet));
    }

    [Fact]
    public void The_kit_goes_on_with_the_place()
    {
        var (p, coal, plain) = Dressed();
        var ch = p.J.Ch;
        Kits.Put(ch, KitKind.Night, coal, EquipSlot.Amulet);
        p.J.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 3, arena: true);
        Assert.Same(coal, ch.Equipment.Amulet);
        p.J.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 4);
        Assert.Same(plain, ch.Equipment.Amulet);
        // A night on the Verge lights the ember: the night's kit there too.
        p.J.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 5, ember: true);
        Assert.Same(coal, ch.Equipment.Amulet);
    }

    [Fact]
    public void Taken_off_the_night_kit_a_slot_wears_the_days_piece_again_by_day_or_by_night()
    {
        foreach (var night in new[] { false, true })
        {
            var (p, coal, plain) = Dressed();
            var ch = p.J.Ch;
            Kits.Put(ch, KitKind.Night, coal, EquipSlot.Amulet);
            if (night) Kits.Wear(ch, KitKind.Night);
            Assert.True(Kits.Clear(ch, KitKind.Night, EquipSlot.Amulet));
            Assert.Contains(coal, ch.Pack);
            Assert.False(Kits.HasOwn(ch, KitKind.Night, EquipSlot.Amulet));
            Assert.Same(plain, ch.Equipment.Amulet);
            Assert.Same(plain, Kits.Piece(ch, KitKind.Night, EquipSlot.Amulet));
        }
    }

    [Fact]
    public void The_day_kit_can_be_dressed_by_night_and_the_night_kit_by_day()
    {
        var (p, coal, plain) = Dressed();
        var ch = p.J.Ch;
        Kits.Put(ch, KitKind.Night, coal, EquipSlot.Amulet);
        Kits.Wear(ch, KitKind.Night);
        // By night, a new day amulet: the coal stays on, the old plain one goes to the pack.
        var better = Inventory.Make(ch, "bone_amulet", 1, 3);
        Inventory.AddToPack(ch, better);
        Assert.True(Kits.Put(ch, KitKind.Day, better, EquipSlot.Amulet));
        Assert.Same(coal, ch.Equipment.Amulet);
        Assert.Contains(plain, ch.Pack);
        Kits.Wear(ch, KitKind.Day);
        Assert.Same(better, ch.Equipment.Amulet);
        // A slot the night has nothing of its own in wears the day's: a ring put on by night where it
        // had none is the night's own, and the day's ring stays the day's.
        var dayRing = Inventory.Make(ch, "copper_ring", 1, 1);
        Inventory.AddToPack(ch, dayRing);
        Assert.True(Kits.Put(ch, KitKind.Day, dayRing, EquipSlot.Ring1));
        var nightRing = Inventory.Make(ch, "silver_ring", 1, 2);
        Inventory.AddToPack(ch, nightRing);
        Kits.Wear(ch, KitKind.Night);
        Assert.Same(dayRing, ch.Equipment.Ring1);
        Assert.True(Kits.Put(ch, KitKind.Night, nightRing, EquipSlot.Ring1));
        Assert.Same(nightRing, ch.Equipment.Ring1);
        Assert.Same(dayRing, Kits.Piece(ch, KitKind.Day, EquipSlot.Ring1));
        Kits.Wear(ch, KitKind.Day);
        Assert.Same(dayRing, ch.Equipment.Ring1);
    }

    [Fact]
    public void A_screen_that_knows_nothing_of_kits_cannot_lose_a_piece_between_them()
    {
        var (p, coal, plain) = Dressed();
        var ch = p.J.Ch;
        Kits.Put(ch, KitKind.Night, coal, EquipSlot.Amulet);
        // What is set aside cannot be pulled out from under the kits.
        Assert.False(Inventory.Equip(ch, coal, EquipSlot.Amulet));
        Assert.Null(Inventory.Remove(ch, coal.Uid));
        // By night, the night's own piece taken off the plain way: the slot is the day's again.
        Kits.Wear(ch, KitKind.Night);
        Assert.True(Inventory.Unequip(ch, EquipSlot.Amulet));
        Kits.Wear(ch, KitKind.Day);
        Assert.Same(plain, ch.Equipment.Amulet);
        Assert.Contains(coal, ch.Pack);
        Assert.False(Kits.HasOwn(ch, KitKind.Night, EquipSlot.Amulet));
        var all = Inventory.Everything(ch).Select(i => i.Uid).ToList();
        Assert.Equal(all.Count, all.Distinct().Count());
    }

    [Fact]
    public void Both_kits_survive_a_save()
    {
        var (p, coal, plain) = Dressed();
        var ch = p.J.Ch;
        Kits.Put(ch, KitKind.Night, coal, EquipSlot.Amulet);
        Kits.Wear(ch, KitKind.Night);
        var back = Json.Clone(ch);
        Assert.Equal(KitKind.Night, Kits.On(back));
        Assert.Equal(coal.Uid, back.Equipment.Amulet!.Uid);
        Assert.Equal(plain.Uid, Kits.Piece(back, KitKind.Day, EquipSlot.Amulet)!.Uid);
        Kits.Wear(back, KitKind.Day);
        Assert.Equal(plain.Uid, back.Equipment.Amulet!.Uid);
        // A save from before the kits reads as one kit, worn by day and night.
        var old = Json.Parse<CharacterData>(Json.Write(Route.New().J.Ch).Replace("\"nightOn\":false,", ""));
        Assert.Equal(KitKind.Day, Kits.On(old));
        Assert.All(Items.EquipSlots, s => Assert.False(Kits.HasOwn(old, KitKind.Night, s)));
    }
}
