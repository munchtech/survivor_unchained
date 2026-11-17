using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sound;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner's gear sounds by slot (src/Audio/EquipCue.cs, 16 Nov 2026): plate on the body, helm-and-boots on the head and
/// feet, the interface's own for the rest; every chain ends at ui.equip so an unbanked slot sound still plays something.</summary>
public class EquipCueTests
{
    [Theory]
    [InlineData(EquipSlot.Body, "equip.plate")]
    [InlineData(EquipSlot.Head, "equip.helm_boots")]
    [InlineData(EquipSlot.Feet, "equip.helm_boots")]
    [InlineData(EquipSlot.Weapon, "ui.equip")]
    [InlineData(EquipSlot.Offhand, "ui.equip")]
    [InlineData(EquipSlot.Ring2, "ui.equip")]
    [InlineData(EquipSlot.Amulet, "ui.equip")]
    public void SlotChoosesFirstLink(EquipSlot slot, string first)
    {
        var c = EquipCue.Chain(slot);
        Assert.Equal(first, c[0]);
        Assert.Equal("ui.equip", c[^1]);
    }

    [Fact]
    public void NoSlotAndLookSlots()
    {
        Assert.Equal(["ui.equip"], EquipCue.Chain(null));
        Assert.Equal(EquipSlot.Feet, EquipCue.OfLook("feet"));
        Assert.Null(EquipCue.OfLook("hands"));
    }
}
