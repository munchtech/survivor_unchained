using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her hair's highlights (the owner, 22 Oct): a second colour on some of her locks, off by default,
/// each hair colour's own when turned on, saved with her look.</summary>
public class HairHighlightTests : System.IDisposable
{
    // (parked since face 40: Lore.ShowHighlights off; these tests force them on, as the shot switch does, except
    // Parked_hides_them)
    public HairHighlightTests() => Lore.ForceHighlights = true;
    public void Dispose() => Lore.ForceHighlights = false;

    static CharacterData Her(string? hair, string? highlight)
    {
        var a = Callings.Archetype("reaver");
        return Character.Create(new CreationChoice
        {
            Name = "H", Archetype = "reaver", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
            Sex = Sex.Female, HairStyle = "braid", Hair = hair, HairHighlight = highlight,
        }, 1, 7);
    }

    static string Hex(string id) => Lore.HairHighlights.Single(h => h.Id == id).Color;

    [Fact]
    public void Every_hair_has_a_default_highlight_that_exists()
    {
        Assert.NotEmpty(Lore.HairHighlights);
        foreach (var h in Lore.Hairs)
            Assert.Contains(Lore.HairHighlights, x => x.Id == Lore.DefaultHighlight(h.Id));
        // (the owner's: copper on black, honey on brown, platinum on blonde)
        Assert.Equal("copper", Lore.DefaultHighlight("black"));
        Assert.Equal("honey", Lore.DefaultHighlight("brown"));
        Assert.Equal("platinum", Lore.DefaultHighlight("fair"));
        Assert.Equal("platinum", Lore.DefaultHighlight("honey"));
        // (a colour by its hex, as the shot switch passes it, and one not among the hairs, by how light it is)
        Assert.Equal("copper", Lore.DefaultHighlight("#2a2422"));
        Assert.Equal("copper", Lore.DefaultHighlight("#101010"));
        Assert.Equal("platinum", Lore.DefaultHighlight("#e0d8c8"));
    }

    [Fact]
    public void Off_by_default_and_resolved_when_on()
    {
        Assert.Null(Her("black", null).HairHighlight);
        Assert.Null(Loadouts.Of(Her("black", null)).Person.HairHighlight);
        Assert.Null(Loadouts.Of(Her("black", "off")).Person.HairHighlight);
        Assert.Equal(Hex("copper"), Loadouts.Of(Her("black", Lore.HighlightAuto)).Person.HairHighlight);
        Assert.Equal(Hex("honey"), Loadouts.Of(Her("brown", Lore.HighlightAuto)).Person.HairHighlight);
        Assert.Equal(Hex("platinum"), Loadouts.Of(Her("fair", Lore.HighlightAuto)).Person.HairHighlight);
        // (one picked holds whatever the hair; a hex of its own too)
        Assert.Equal(Hex("auburn"), Loadouts.Of(Her("fair", "auburn")).Person.HairHighlight);
        Assert.Equal("#123456", Loadouts.Of(Her("black", "#123456")).Person.HairHighlight);
        // (an unknown id: none, not a crash)
        Assert.Null(Loadouts.Of(Her("black", "nonesuch")).Person.HairHighlight);
    }

    [Fact]
    public void Saved_with_her_look()
    {
        var ch = Her("black", "honey");
        var back = Json.Parse<CharacterData>(Json.Write(ch));
        Assert.Equal("honey", back.HairHighlight);
        Assert.Equal(Hex("honey"), Loadouts.Of(back).Person.HairHighlight);
        var off = Json.Parse<CharacterData>(Json.Write(Her("black", null)));
        Assert.Null(off.HairHighlight);
        // (and it changes what shows)
        Assert.NotEqual(Loadouts.Look(Loadouts.Of(Her("black", null))), Loadouts.Look(Loadouts.Of(Her("black", Lore.HighlightAuto))));
    }

    [Fact]
    public void Platinum_covers_twice_and_honey_is_stronger()
    {
        // (face 40, the judge: platinum 2x coverage, ash and lighter; honey 1.5x strength, r2 3x; the rest as they were)
        var p = Lore.HairHighlights.Single(h => h.Id == "platinum");
        Assert.Equal(2f, p.Share);
        Assert.Equal(3f, Lore.HairHighlights.Single(h => h.Id == "honey").Strength);
        Assert.Equal(1f, Lore.HairHighlights.Single(h => h.Id == "copper").Share);
        var rgb = Enumerable.Range(0, 3).Select(i => System.Convert.ToInt32(p.Color.Substring(1 + 2 * i, 2), 16) / 255f).ToArray();
        float max = rgb.Max(), min = rgb.Min();
        Assert.True(max > 0.95f && (max - min) / max < 0.04f && rgb[0] - rgb[2] < 0.03f, $"platinum {p.Color}: light ash, not pink");
    }

    [Fact]
    public void Parked_hides_them()
    {
        // (face 40: the highlights failed their judge and are parked: with the switch off a saved look's highlight
        // still loads, but her hair shows none)
        Assert.False(Lore.ShowHighlights);
        Lore.ForceHighlights = false;
        var ch = Json.Parse<CharacterData>(Json.Write(Her("black", Lore.HighlightAuto)));
        Assert.Equal(Lore.HighlightAuto, ch.HairHighlight);
        Assert.Null(Loadouts.Of(ch).Person.HairHighlight);
        Assert.Null(Loadouts.Of(Her("fair", "auburn")).Person.HairHighlight);
        Assert.Equal(Loadouts.Look(Loadouts.Of(Her("black", null))), Loadouts.Look(Loadouts.Of(Her("black", Lore.HighlightAuto))));
        // (forced on, as --hair-highlight does, it shows)
        Lore.ForceHighlights = true;
        Assert.Equal(Hex("copper"), Loadouts.Of(ch).Person.HairHighlight);
    }
}
