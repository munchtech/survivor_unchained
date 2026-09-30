using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Oaths as rules of the fight, and the gear that answers them
/// (Maps/MapOffers.cs, MapRules, Items.Affixes).</summary>
public class OathTests
{
    static void Tick(Battle b, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
    }

    static Battle Arena(params string[] oaths)
    {
        var b = BattleTests.Arena(21);
        b.RemoveWeapon("oathblade");
        b.Rules = MapOffers.Rules(new MapSpec { Oaths = oaths.ToList() });
        return b;
    }

    [Fact]
    public void Every_oath_and_people_names_its_answer_and_the_answer_exists()
    {
        foreach (var o in MapOffers.Oaths)
        {
            Assert.False(string.IsNullOrWhiteSpace(o.Answer), o.Id);
            Assert.NotEmpty(o.Lean!);
            Assert.All(o.Lean!, a => Assert.NotNull(Items.Affix(a)));
        }
        foreach (var p in MapOffers.Peoples) Assert.All(p.Lean, a => Assert.NotNull(Items.Affix(a)));
    }

    [Fact]
    public void Under_the_long_winter_their_blows_slow_you_and_sure_footing_answers()
    {
        var b = Arena("winter");
        var r = b.SpawnEnemy("risen", b.Player.X + 1, b.Player.Z)!;
        b.HurtPlayer(5, School.Physical, "risen", r);
        Assert.True(b.Player.SlowF < 0.7);
        double slowed = b.Player.SlowT;
        var sure = Arena("winter");
        sure.Stats.Add(new StatMod(Stat.Tenacity, ModKind.Flat, 0.5, "test"));
        var r2 = sure.SpawnEnemy("risen", sure.Player.X + 1, sure.Player.Z)!;
        sure.HurtPlayer(5, School.Physical, "risen", r2);
        Assert.True(sure.Player.SlowT < slowed);
        Assert.True(sure.Player.SlowF > b.Player.SlowF);
    }

    [Fact]
    public void Under_the_blight_their_blows_poison_and_mending_is_cut()
    {
        var b = Arena("blight");
        var r = b.SpawnEnemy("risen", b.Player.X + 1, b.Player.Z)!;
        b.HurtPlayer(5, School.Physical, "risen", r);
        Assert.True(b.Player.PoisonT > 0);
        b.Player.Hp = 50;
        b.HealPlayer(30, "test");
        Assert.InRange(b.Player.Hp, 69, 71);
    }

    [Fact]
    public void Under_iron_only_criticals_land_whole()
    {
        double Blow(Battle b, bool crit)
        {
            var e = b.SpawnEnemy("risen_warrior", b.Player.X + 3, b.Player.Z)!;
            return b.HitEnemy(e, 100, School.Physical, [Tag.Physical], crit ? new HitOpts { Crit = true } : new HitOpts { NoCrit = true });
        }
        Assert.Equal(Blow(Arena(), false) * 0.67, Blow(Arena("iron"), false), 1);
        Assert.Equal(Blow(Arena(), true), Blow(Arena("iron"), true), 1);
    }

    [Fact]
    public void Under_the_hunt_they_are_faster_and_under_embers_and_ruin_their_dead_are_dangerous()
    {
        var hunt = Arena("hunt");
        var calm = Arena();
        double fast = Enumerable.Range(0, 30).Average(_ => hunt.SpawnEnemy("risen", 5, 5)!.Speed);
        double slow = Enumerable.Range(0, 30).Average(_ => calm.SpawnEnemy("risen", 5, 5)!.Speed);
        Assert.InRange(fast / slow, 1.12, 1.28);

        var b = Arena("embers", "ruin");
        var list = new List<Enemy>();
        for (int i = 0; i < 40; i++) list.Add(b.SpawnEnemy("risen", 8 + i % 8, 8 + i / 8)!);
        foreach (var e in list) b.KillEnemy(e, true, null);
        Assert.Contains(b.Zones.Living(), z => z.Owner == Side.Enemy && z.School == School.Fire);
        Assert.Contains(b.Events.Drain(), ev => ev is Ev.Telegraph);
    }

    [Fact]
    public void A_maps_gear_leans_toward_what_answers_it()
    {
        var lean = MapOffers.Lean(new MapSpec { Oaths = ["winter"] }, "pack");
        Assert.Contains("of_the_hearth", lean);
        Assert.Contains("wolfbane", lean);
        int hits = 0, plain = 0;
        for (uint i = 0; i < 300; i++)
        {
            hits += Inventory.Make(null, "silver_ring", 1, 2, i + 1, lean: lean).Affixes.Count(a => lean.Contains(a.Id));
            plain += Inventory.Make(null, "silver_ring", 1, 2, i + 1).Affixes.Count(a => lean.Contains(a.Id));
        }
        Assert.True(hits > plain * 2, $"{hits} leaning, {plain} without");
    }

    [Fact]
    public void Fine_gear_can_carry_a_skill_and_it_goes_with_the_gear()
    {
        var j = Play.Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id,
            WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = "shield_bash",
        }, 7);
        var ring = Inventory.Make(j.Ch, "silver_ring", 1, 3, affixes: [new AffixRoll { Id = "of_the_gyre", Tier = 2 }]);
        Assert.True(Inventory.AddToPack(j.Ch, ring));
        j.Equip(ring.Uid, EquipSlot.Ring1, null);
        Assert.Contains(Character.Kit(j.Ch).Weapons, w => w.Id == "axe_gyre");
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3);
        Assert.Contains(b.Weapons, w => w.Id == "axe_gyre");
        j.Capture(b);
        j.Unequip(EquipSlot.Ring1, b);
        Assert.DoesNotContain(b.Weapons, w => w.Id == "axe_gyre");
        var next = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 4);
        Assert.DoesNotContain(next.Weapons, w => w.Id == "axe_gyre");
        // Skills come only on fine gear.
        for (uint i = 0; i < 200; i++)
            Assert.DoesNotContain(Inventory.Make(null, "silver_ring", 1, 1, i + 1).Affixes, a => Items.Affix(a.Id)!.Grants != null);
    }

    [Fact]
    public void An_arena_sworn_under_winter_puts_its_rule_on_the_fight()
    {
        var spec = ArenaTests.Spec("pack", false, "winter", "moonless");
        var map = MapGen.Generate(spec.Map);
        var j = Play.Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id,
            WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = "shield_bash",
        }, 42);
        SurvivorUnchained.Arena.Arenas.Begin(j.World, spec);
        var host = new FakeHost(j, map.Meta, map.Ground);
        var zone = new Play.Zones.ArenaRun(host, map, spec);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 11, arena: true);
        zone.Begin(b);
        Assert.True(b.Rules.HitChill);
        // Half the arena's light (which reaches further than the wood's).
        Assert.Equal(0.5 * 1.6, b.Rules.Light, 3);
    }
}
