using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The skills a survivor learns for the day from what burned in the arenas (Rpg/SkillBook.cs).</summary>
public class SkillTests
{
    static Journey Make(string calling = "warden")
    {
        var a = Callings.Archetype(calling);
        return Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
    }

    static Battle Day(Journey j) => j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3);

    [Fact]
    public void A_tome_teaches_only_what_has_been_seen_burning()
    {
        var j = Make("arcanist");
        j.GiveItem(SkillBook.Tome("seeking_motes"));
        var tome = j.Ch.Satchel.First(p => p.Def == SkillBook.Tome("seeking_motes"));
        // Never seen in an arena: the words mean nothing yet.
        j.Use(tome.Uid, null);
        Assert.False(SkillBook.Knows(j.Ch, "seeking_motes"));
        j.Ch.Discovered.Add("seeking_motes");
        j.Use(tome.Uid, null);
        Assert.True(SkillBook.Knows(j.Ch, "seeking_motes"));
        // A free slot takes it into hand, and by day it is in the fight.
        Assert.Contains("seeking_motes", j.Ch.Slotted);
        Assert.Contains(Day(j).Weapons, w => w.Id == "seeking_motes" && w.Rank == SkillBook.Rank(j.Ch));
        Assert.DoesNotContain(j.Ch.Satchel, p => p.Def == SkillBook.Tome("seeking_motes"));
    }

    [Fact]
    public void A_skill_asks_something_of_you_and_lies_idle_until_you_measure_up()
    {
        var j = Make("warden");
        j.Ch.Discovered.Add("seeking_motes");
        Assert.Equal("Wits", SkillBook.Attribute("seeking_motes"));
        Assert.Equal("Might", SkillBook.Attribute("cleaver"));
        Assert.Equal("Finesse", SkillBook.Attribute("volley"));
        Assert.Equal("Resolve", SkillBook.Attribute("hallowed_ring"));
        Assert.True(SkillBook.Learn(j.Ch, "seeking_motes"));
        // A warden's wits are not up to it: learned and carried, but idle.
        Assert.False(SkillBook.Meets(j.Ch, "seeking_motes"));
        Assert.DoesNotContain(Day(j).Weapons, w => w.Id == "seeking_motes");
        j.Ch.Attributes.Wits = SkillBook.Need;
        Assert.Contains(Day(j).Weapons, w => w.Id == "seeking_motes");
    }

    [Fact]
    public void Skills_learned_for_the_day_stay_out_of_the_nights_arenas()
    {
        var j = Make("arcanist");
        j.Ch.Discovered.Add("rimeshard");
        SkillBook.Learn(j.Ch, "rimeshard");
        Assert.Contains(Day(j).Weapons, w => w.Id == "rimeshard");
        var night = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        Assert.DoesNotContain(night.Weapons, w => w.Id == "rimeshard");
    }

    [Fact]
    public void Slots_and_ranks_grow_with_the_survivor_and_the_calling_teaches_its_own()
    {
        var j = Make("stalker");
        Assert.Equal(2, SkillBook.Slots(j.Ch));
        Assert.Equal(1, SkillBook.Rank(j.Ch));
        foreach (var id in new[] { "volley", "knifestorm", "rimeshard" }) j.Ch.Discovered.Add(id);
        while (j.Ch.Level < 3) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        // The third level: the calling teaches a thing of its own kind it has seen.
        var taught = j.Grew();
        Assert.NotNull(taught);
        Assert.True(SkillBook.Knows(j.Ch, taught!));
        Assert.Contains(Weapons.All[taught!].Tags, Callings.Archetype("stalker").Favours.Contains);
        while (j.Ch.Level < 8) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        Assert.Equal(5, SkillBook.Slots(j.Ch));
        Assert.Equal(3, SkillBook.Rank(j.Ch));
    }

    /// <summary>A stalker at the third level with skills of its kind seen: the calling teaches one when Grew is called.</summary>
    static Journey AtThird(List<Announcement> said)
    {
        var j = Make("stalker");
        j.OnAnnounce = said.Add;
        // (everything seen: the calling has one of its kind to teach at the third level and again at the sixth)
        foreach (var id in Weapons.All.Keys) j.Ch.Discovered.Add(id);
        return j;
    }

    static void GrowTo(Journey j, int level)
    {
        while (j.Ch.Level < level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
    }

    [Fact]
    public void Out_of_a_campaign_fight_the_calling_announces_its_skill()
    {
        var said = new List<Announcement>();
        var j = AtThird(said);
        GrowTo(j, 3);
        var taught = j.Grew();
        Assert.NotNull(taught);
        var a = Assert.Single(said, x => x.Kicker == "A new skill");
        Assert.Equal(Weapons.All[taught!].Name, a.Title);
        Assert.Equal("Your calling teaches it to you. Put it on a key (K)", a.Sub);
        Assert.Null(j.CallingTaught);

        // an arena's fight is not the campaign's: the banner still
        said.Clear();
        var k = AtThird(said);
        k.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        GrowTo(k, 3);
        Assert.NotNull(k.Grew());
        Assert.Single(said, x => x.Kicker == "A new skill");
        Assert.Null(k.CallingTaught);
    }

    [Fact]
    public void In_a_campaign_fight_the_callings_skill_goes_to_the_level_card_without_a_banner()
    {
        var said = new List<Announcement>();
        var j = AtThird(said);
        var b = Day(j);
        Assert.True(b.Campaign);
        GrowTo(j, 3);
        var taught = j.Grew();
        Assert.NotNull(taught);
        Assert.DoesNotContain(said, x => x.Kicker == "A new skill");
        Assert.Equal((3, taught!), j.CallingTaught);

        // the fight after it is an arena's: the campaign's is no longer running, and the banner is back
        j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        GrowTo(j, 6);
        var next = j.Grew();
        Assert.NotNull(next);
        Assert.Single(said, x => x.Kicker == "A new skill" && x.Title == Weapons.All[next!].Name);
        Assert.Equal((3, taught), j.CallingTaught);
    }

    [Fact]
    public void Every_skill_the_ember_gives_has_a_tome_and_the_curiosities_sell_them()
    {
        foreach (var id in Weapons.Pool) Assert.NotNull(Items.Find(SkillBook.Tome(id))?.Consumable?.Skill);
        var j = Make();
        j.Ch.Discovered.AddRange(["volley", "knifestorm", "rimeshard"]);
        var stock = j.OpenShop("vonnra", new System.Random(3))!.Stock;
        Assert.Equal(2, stock.Count(i => i.Def.StartsWith("tome_")));
    }
}
