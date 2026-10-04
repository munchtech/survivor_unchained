using System.Linq;
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
        // Her hair is one of her own cuts: an older save's cut becomes the nearest of hers.
        Assert.Equal("bob", p.Hair);
        // The calling's first colours are its own, undyed: her suit as it was made.
        Assert.Null(p.Dye);
        Assert.False(p.Beard);
        Assert.Equal(1.2, p.Figure);
        Assert.False(string.IsNullOrEmpty(Loadouts.Of(ch).Arms.Right));
    }

    [Fact]
    public void Her_cut_face_eyes_and_paint_are_kept_and_worn()
    {
        var a = Callings.Archetype("warden");
        var face = new System.Collections.Generic.Dictionary<string, double> { ["eyes_tilt"] = 0.6, ["jaw"] = 0, ["lips_lower"] = 2 };
        var ch = Character.Create(new CreationChoice
        {
            Name = "E", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
            Sex = Sex.Female, HairStyle = "braid", Eyes = "cornflower", Paint = "woad", Face = face,
        }, 1, 7);
        // Saved: only what moved from her own face, each within its range.
        Assert.Equal(2, ch.Face!.Count);
        Assert.Equal(1, ch.Face["lips_lower"]);
        Assert.Equal("cornflower", ch.Eyes);
        Assert.Equal("woad", ch.Paint);
        var p = Loadouts.Of(ch).Person;
        Assert.Equal("braid", p.Hair);
        Assert.Equal(0.6, p.Face!["eyes_tilt"]);
        Assert.Equal(World.Lore.Her.Eyes.First(e => e.Id == "cornflower").Color, p.Eyes);
        Assert.Equal("woad", p.Paint);
        // Her own eyes (as painted) and bare skin carry nothing.
        ch.Eyes = "moss"; ch.Paint = null;
        Assert.Null(Loadouts.Of(ch).Person.Eyes);
        Assert.Null(Loadouts.Of(ch).Person.Paint);
        // A man has none of hers.
        var him = Character.Create(new CreationChoice { Name = "F", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0], Sex = Sex.Male, Eyes = "cornflower", Face = face }, 1, 7);
        Assert.Null(Loadouts.Of(him).Person.Face);
        Assert.Null(Loadouts.Of(him).Person.Eyes);
    }

    [Fact]
    public void Her_looks_are_whole()
    {
        // Every slider has its words and a range about her own face; every face starts from known sliders.
        var her = World.Lore.Her;
        var ids = her.Sliders.Select(s => s.Id).ToHashSet();
        // (tools/assets/face_shapes.py's SLIDERS, written by face_looks.py: every part of her face, her ears and her neck)
        Assert.Equal(47, ids.Count);
        // (eight groups of at most eight: creation's Shape part shows a group whole, unscrolled)
        var groups = her.Sliders.GroupBy(s => s.Group).ToList();
        Assert.Equal(new[] { "Head", "Brows", "Eyes", "Nose", "Cheeks", "Mouth", "Jaw", "Ears and neck" }, groups.Select(g => g.Key));
        Assert.All(groups, g => Assert.InRange(g.Count(), 1, 8));
        Assert.Contains("forehead_height", ids);
        Assert.Contains("chin_width", ids);
        Assert.All(her.Sliders, s => Assert.True(s.Min <= 0 && s.Max > 0 && s.Low != "" && s.High != ""));
        Assert.All(her.Faces, f => Assert.All(f.Shape, kv =>
        {
            var s = her.Sliders.First(x => x.Id == kv.Key);
            Assert.InRange(kv.Value, s.Min, s.Max);
        }));
        Assert.Equal(new[] { "long", "ponytail", "braid", "bob", "pixie" }, her.Cuts.Select(h => h.Id));
        Assert.Contains(her.Paints, p => p.Id == "none");
        // A man (a kit body until the male hero's is worn) is shaped without one.
        Assert.Null(Loadouts.HeroKit(Sex.Male));
    }
}
