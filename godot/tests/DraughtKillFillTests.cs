using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner, 19 Nov: "we need ways to get health, our vial should refill on kills like in poe". 10 charge points make
/// a draught (normal 1, elite 3, boss 10), capped at the flask's number; the rest are lost.</summary>
public class DraughtKillFillTests
{
    static Journey Make()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 42);
        var f = Crafting.Rules.Flask;
        Inventory.Take(j.Ch, f.Draught, Inventory.Count(j.Ch, f.Draught));
        return j;
    }

    static int Count(Journey j) => Inventory.Count(j.Ch, Crafting.Rules.Flask.Draught);

    static Enemy Foe(Battle b, bool elite = false, bool boss = false)
    {
        var e = b.SpawnEnemy("wolf", 3, 3)!;
        e.Elite = elite; e.Boss = boss;
        return e;
    }

    [Fact]
    public void Ten_normal_kills_make_a_draught()
    {
        var j = Make();
        var b = j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 7);
        for (int i = 0; i < 9; i++) j.Killed(Foe(b), true);
        Assert.Equal(0, Count(j));
        j.Killed(Foe(b), true);
        Assert.Equal(1, Count(j));
    }

    [Fact]
    public void An_elite_is_three_and_a_boss_is_a_whole_charge_and_it_caps()
    {
        var j = Make();
        var b = j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 7);
        j.Killed(Foe(b, boss: true), true);
        Assert.Equal(1, Count(j));
        for (int i = 0; i < 3; i++) j.Killed(Foe(b, elite: true), true);
        Assert.Equal(1, Count(j));
        j.Killed(Foe(b), true);
        Assert.Equal(2, Count(j));
        for (int i = 0; i < 5; i++) j.Killed(Foe(b, boss: true), true);
        Assert.Equal(Crafting.Rules.Flask.Upto, Count(j));
    }
}
