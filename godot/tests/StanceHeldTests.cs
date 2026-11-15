using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her off-hand follows the stance (stances.json "held", view only): the map parses and resolves per slot, and the
/// world's forearm shield follows the off-hand slot (Loadouts.Of).</summary>
public sealed class StanceHeldTests
{
    [Fact]
    public void Carry_l_parses_for_the_mace_and_not_for_the_shield_or_twin_blades()
    {
        Assert.Null(Stances.Find("shield")!.CarryL);
        Assert.Null(Stances.Find("twin_blades")!.CarryL);   // (r3: its forward guard read as reaching out; dropped)
        var mc = Stances.Find("mace")!.CarryL!;
        Assert.True(mc.Out > 0 && mc.Elbow > 0);
        Assert.Equal("dagger_b", Stances.Find("twin_blades")!.Piece("handslot.l", null));   // carry_l is no piece id
    }

    [Fact]
    public void Grip_l_turns_the_twin_fangs_dagger_into_a_reverse_grip_and_nothing_else()
    {
        var g = Stances.Find("twin_blades")!.GripL!;
        Assert.Equal(3, g.Length);
        Assert.InRange(g[0], 150, 250);   // flipped about the hand's across axis: the blade back toward the elbow
        Assert.NotEqual(0, g[2]);         // the tip turned out clear of the forearm
        Assert.Null(Stances.Find("mace")!.GripL);
        Assert.Null(Stances.Find("shield")!.GripL);
        Assert.Equal("dagger_b", Stances.Find("twin_blades")!.Piece("handslot.l", null));   // grip_l is no piece id
    }

    [Fact]
    public void Held_map_parses_and_resolves_per_slot()
    {
        var shield = Stances.Find("shield")!;
        Assert.Equal("shield_round", shield.Piece("forearm.l", "shield_round"));
        Assert.Equal("x", shield.Piece("handslot.l", "x"));            // not named: as the loadout has it
        var twin = Stances.Find("twin_blades")!;
        Assert.Null(twin.Piece("forearm.l", "shield_round"));          // "" = empty
        Assert.Equal("dagger_b", twin.Piece("handslot.l", null));
        var mace = Stances.Find("mace")!;
        Assert.Null(mace.Piece("forearm.l", "shield_round"));
        Assert.Equal("mace", mace.Piece("handslot.l", null));
        Assert.Equal("shield_round", Stances.Piece(null, "forearm.l", "shield_round"));   // set A: the loadout's own
    }

    [Fact]
    public void Set_a_shield_is_the_callings_whatever_the_offhand_slot_holds()
    {
        // A new Warden starts with an empty off-hand slot (her second set) and must still carry her calling's shield.
        var a = Callings.Archetype("warden");
        foreach (var bg in new[] { "hunter", "scholar", "outcast", "devout" })
        {
            var ch = Character.Create(new CreationChoice { Name = "T", Archetype = "warden", Background = bg, Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 1);
            Assert.Null(ch.Equipment[EquipSlot.Offhand]);
            Assert.Equal("shield_round", Loadouts.Of(ch).Arms.Forearm);
            ch.Equipment[EquipSlot.Offhand] = Inventory.Make(ch, "watch_buckler");
            Assert.Equal("shield_round", Loadouts.Of(ch).Arms.Forearm);
        }
    }
}
