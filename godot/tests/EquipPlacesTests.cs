using System;
using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>SU-040: every equipment slot has one name and glyph (Items.Places), read by the Pack's doll and the
/// forge's worn row, so a slot added to EquipSlot shows everywhere or this fails (the forge threw at Shoulders
/// from 18 October, when the six armor slots came in and the screens' own table kept nine).</summary>
public class EquipPlacesTests
{
    [Fact]
    public void Every_slot_has_a_name_and_a_glyph_the_icon_set_has()
    {
        foreach (var s in Enum.GetValues<EquipSlot>())
        {
            Assert.True(Items.Places.TryGetValue(s, out var p), $"{s} has no place");
            Assert.False(string.IsNullOrWhiteSpace(p.Name), $"{s} has no name");
            Assert.True(GlyphPaths.Own(p.Glyph), $"{s}'s glyph '{p.Glyph}' is not in glyphs.json");
        }
        Assert.Equal(Enum.GetValues<EquipSlot>().Length, Items.Places.Count);
        Assert.Equal(Items.EquipSlots.OrderBy(s => s), Items.Places.Keys.OrderBy(s => s));
    }
}
