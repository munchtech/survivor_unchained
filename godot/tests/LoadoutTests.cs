using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>What the survivor looks like and carries (Play/Loadout.cs).</summary>
public class LoadoutTests
{
    [Theory]
    [InlineData("warden")]
    [InlineData("reaver")]
    [InlineData("arcanist")]
    [InlineData("stalker")]
    public void Every_calling_is_dressed_and_armed(string archetype)
    {
        var a = Callings.Archetype(archetype);
        foreach (var weapon in a.Weapons)
        {
            var ch = Character.Create(new CreationChoice
            {
                Name = "Ashe", Archetype = archetype, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = weapon,
                Ability = a.Abilities[0],
            }, 1, 7);
            var lo = Loadouts.Of(ch);
            Assert.NotEmpty(lo.Person.Outfit!);
            Assert.False(string.IsNullOrEmpty(lo.Arms.Right));
            Assert.NotEmpty(lo.Arms.Attack);
            // The calling's colours dye the cloth (the first colours are the clothes' own).
            Assert.Equal(a.Palettes[0].Paint.ContainsKey("cloth"), lo.Person.Dye != null);
        }
    }

    [Fact]
    public void A_reaver_goes_bare_and_a_hood_hides_the_hair()
    {
        var a = Callings.Archetype("reaver");
        var ch = Character.Create(new CreationChoice { Name = "B", Archetype = "reaver", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 1, 7);
        Assert.DoesNotContain(Loadouts.Of(ch).Person.Outfit!, p => p.Contains("Body"));
        var s = Callings.Archetype("stalker");
        var hooded = Character.Create(new CreationChoice { Name = "C", Archetype = "stalker", Background = "hunter", Palette = s.Palettes[0].Id, WeaponItem = s.Weapons[0], Ability = s.Abilities[0], Model = "rogue_hooded" }, 1, 7);
        Assert.Null(Loadouts.Of(hooded).Person.Hair);
    }

    [Theory]
    [InlineData("warden")]
    [InlineData("reaver")]
    [InlineData("stalker")]
    public void A_woman_goes_in_her_own_body_with_her_own_hair(string archetype)
    {
        var a = Callings.Archetype(archetype);
        var ch = Character.Create(new CreationChoice
        {
            Name = "D", Archetype = archetype, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
            Sex = Sex.Female, HairStyle = "Hair_Buns", Figure = 1.2, Model = "rogue_hooded",
        }, 1, 7);
        var p = Loadouts.Of(ch).Person;
        Assert.Equal(Loadouts.HerBody, p.Body);
        // Her own outfit for her calling, not the Quaternius clothes.
        Assert.Equal(new[] { Loadouts.HerOutfit(archetype) }, p.Outfit!);
        // Her hair is her own: no hairstyle goes over it (its colour still dyes it).
        Assert.Null(p.Hair);
        // The calling's first colours are its own, undyed: her suit as it was made.
        Assert.Null(p.Dye);
        Assert.False(p.Beard);
        Assert.Equal(1.2, p.Figure);
        Assert.False(string.IsNullOrEmpty(Loadouts.Of(ch).Arms.Right));
    }
}
