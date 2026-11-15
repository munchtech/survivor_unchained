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
    public void World_shield_follows_the_offhand_slot()
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 1);
        ch.Equipment[EquipSlot.Offhand] = Inventory.Make(ch, "watch_buckler");
        Assert.Equal("shield_round", Loadouts.Of(ch).Arms.Forearm);
        ch.Equipment[EquipSlot.Offhand] = null;
        Assert.Null(Loadouts.Of(ch).Arms.Forearm);
    }
}
