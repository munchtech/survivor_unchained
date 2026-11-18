using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The one prompt that the Lamps tree exists: at the first held point, once per save, never in the arena or over a choice.</summary>
public sealed class LampsTeachTests
{
    static CharacterData Warden(int level)
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = level;
        return ch;
    }

    [Fact]
    public void Fires_once_at_the_first_held_point()
    {
        var ch = Warden(6);
        var w = new WorldState { Time = TimeOfDay.Day };
        Assert.True(LampBook.Spare(ch, w) > 0);
        Assert.True(LampsTeach.Take(ch, w, false));
        Assert.False(LampsTeach.Take(ch, w, false));
        ch.Level = 7;
        Assert.False(LampsTeach.Take(ch, w, false));
        Assert.Equal("Press *L* to open your Lamps and spend the point you hold.", LampsTeach.TextFor(_ => "L"));
    }

    [Fact]
    public void Waits_for_the_arena_and_a_choice_to_clear_and_for_a_point()
    {
        var ch = Warden(6);
        var w = new WorldState { Time = TimeOfDay.Day, Arena = new Arena.ArenaSpec() };
        Assert.False(LampsTeach.Take(ch, w, false));
        w.Arena = null;
        Assert.False(LampsTeach.Take(ch, w, true));
        Assert.True(LampsTeach.Take(ch, w, false));
        var none = Warden(1);
        var w2 = new WorldState();
        Assert.False(LampsTeach.Take(none, w2, false));
        Assert.False(w2.Fact(LampsTeach.Fact).Truthy);
    }

    [Fact]
    public void Opening_the_Lamps_settles_it()
    {
        var ch = Warden(6);
        var w = new WorldState();
        LampsTeach.Used(w);
        Assert.False(LampsTeach.Take(ch, w, false));
    }

    [Fact]
    public void ThePromptCountsThePointsSheHolds()
    {
        Assert.Equal("Press *L* to open your Lamps and spend the point you hold.", LampsTeach.TextFor(_ => "L", 1));
        Assert.Equal("Press *L* to open your Lamps and spend the point you hold.", LampsTeach.TextFor(_ => "L", 0));
        Assert.Equal("Press *L* to open your Lamps and spend the 6 points you hold.", LampsTeach.TextFor(_ => "L", 6));
    }
}
