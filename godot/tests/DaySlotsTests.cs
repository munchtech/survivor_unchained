using System;
using System.IO;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Six day slots by level 20, and the type chosen at creation
/// (docs/design/CLASS_IDENTITY_AND_TALENTS.md §3.7; Rpg/SkillBook.cs, Rpg/LampBook.cs).</summary>
public class DaySlotsTests
{
    static CharacterData Make(string calling = "warden", string type = "")
    {
        var a = Callings.Archetype(calling);
        return Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0], Type = type,
        }, seed: 7);
    }

    [Theory]
    [InlineData(1, 2)] [InlineData(3, 2)] [InlineData(4, 3)] [InlineData(7, 3)] [InlineData(8, 4)]
    [InlineData(13, 4)] [InlineData(14, 5)] [InlineData(19, 5)] [InlineData(20, 6)] [InlineData(30, 6)]
    public void Slots_grow_to_six_by_the_twentieth_level(int level, int slots)
    {
        var ch = Make();
        ch.Level = level;
        Assert.Equal(slots, SkillBook.Slots(ch));
    }

    [Fact]
    public void Nothing_carried_past_the_slots()
    {
        var ch = Make();
        // Everything the calling may carry, learned and slotted past the limit by hand (as an old save might).
        var all = Weapons.All.Keys.Where(id => SkillBook.Carries(ch, id)).ToList();
        Assert.True(all.Count > 6);
        foreach (var level in new[] { 1, 4, 8, 14, 20, 30 })
        {
            ch.Level = level;
            ch.Skills = all.ToList();
            ch.Slotted = all.ToList();
            Assert.True(SkillBook.Carried(ch).Count() <= SkillBook.Slots(ch));
        }
    }

    [Theory]
    [InlineData("sunderer")]
    [InlineData("bulwark")]
    public void The_type_chosen_at_creation_is_walked_on_every_layout(string road)
    {
        var ch = Make("warden", road);
        Assert.All(LampBook.State(ch).Layouts, l => Assert.Equal(road, l.Type));
        // Its free lamps are lit and its Strike carried, as a type change would leave them.
        Assert.All(LampBook.State(ch).Layouts, l => Assert.Equal(Lamps.Road(road).Strike, l.Flare));
        Assert.Subset(LampBook.State(ch).Layouts[1].Lit.ToHashSet(), LampBook.Free(ch, LampBook.State(ch).Layouts[1]));
        Assert.True(LampBook.Switch(ch, 1));
        Assert.Equal(road, LampBook.Now(ch).Type);
    }

    [Theory]
    [InlineData("")]
    [InlineData("nonsense")]
    [InlineData("butcher")] // a reaver's road, not hers
    public void A_type_she_cannot_walk_falls_back_to_the_default(string road)
    {
        var ch = Make("warden", road);
        Assert.All(LampBook.State(ch).Layouts, l => Assert.Equal(LampBook.DefaultType("warden"), l.Type));
    }

    [Fact]
    public void The_type_survives_a_save()
    {
        var ch = Make("warden", "bulwark");
        var dir = Path.Combine(Path.GetTempPath(), "su-saves-" + Guid.NewGuid().ToString("N"));
        try
        {
            var saves = new Saves(dir);
            Assert.True(saves.Write(1, new SaveData { Character = ch, World = new WorldState() }));
            var back = saves.Read(1)!;
            Assert.All(LampBook.State(back.Character).Layouts, l => Assert.Equal("bulwark", l.Type));
        }
        finally { Directory.Delete(dir, true); }
    }
}
