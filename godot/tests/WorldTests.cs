using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

/// <summary>The character, the world's language, dialogue and saves: the web
/// game's world tests, ported.</summary>
public class CharacterTests
{
    [Fact]
    public void Starts_with_its_calling_weapon_and_background_kit()
    {
        var ch = Survivor("hunter");
        Assert.Equal("worn_oathblade", ch.Equipment.Weapon?.Def);
        Assert.Equal("old_hunters_cloak", ch.Equipment.Cloak?.Def);
        Assert.Contains("beastlore", ch.Knowledge);
        var kit = Character.Kit(ch);
        Assert.Equal(new[] { ("oathblade", 1) }, kit.Weapons);
        // The cloak's beast protection reaches the stat block.
        Assert.Equal(0.25, kit.Stats.GetRaw(Stat.FromOf(Family.Wolf)), 6);
        Assert.Contains("beastscent", Inventory.WorldTags(ch));
    }

    [Fact]
    public void Equipping_swaps_the_old_item_back_into_the_pack()
    {
        var ch = Survivor();
        var staff = Inventory.Make(ch, "ember_staff");
        Inventory.AddToPack(ch, staff);
        Assert.True(Inventory.Equip(ch, staff, EquipSlot.Weapon));
        Assert.Equal("ember_staff", ch.Equipment.Weapon?.Def);
        Assert.Contains(ch.Pack, p => p?.Def == "worn_oathblade");
        Assert.Equal("cinderfall", Character.Kit(ch).Weapons[0].Id);
    }

    [Fact]
    public void Plain_gear_rolls_affixes_and_compare_reports_differences()
    {
        var ch = Survivor();
        var ring = Inventory.Make(ch, "silver_ring", rarity: 3, seed: 7);
        Assert.True(ring.Affixes.Count > 1);
        Assert.NotEqual("Silver Ring", Inventory.Name(ring));
        Assert.NotEmpty(Character.Compare(ch, ring, EquipSlot.Ring1));
    }

    [Fact]
    public void Levels_grant_points_and_trait_picks()
    {
        var ch = Survivor();
        int gained = Character.GainXp(ch, 5000);
        Assert.True(gained > 2);
        Assert.Equal(gained * 2, ch.Points);
        Assert.True(ch.TraitPicks > 0);
    }

    [Fact]
    public void Stacks_materials()
    {
        var ch = Survivor();
        Inventory.AddToPack(ch, Inventory.Make(ch, "wolf_pelt", qty: 3));
        Inventory.AddToPack(ch, Inventory.Make(ch, "wolf_pelt", qty: 4));
        Assert.Equal(7, Inventory.Count(ch, "wolf_pelt"));
        Assert.Single(ch.Pack.Where(p => p?.Def == "wolf_pelt"));
    }

    [Fact]
    public void Item_triggers_from_content_reach_the_fight()
    {
        // The Wolf-Fang Necklace's rule is data; worn, it is in the kit.
        var ch = Survivor();
        Inventory.Equip(ch, Inventory.Make(ch, "wolf_fang_necklace"), EquipSlot.Amulet);
        var kit = Character.Kit(ch);
        var t = Assert.Single(kit.Triggers);
        Assert.Equal(TriggerEvent.Hit, t.Def.On);
        var apply = Assert.IsType<Effect.Apply>(Assert.Single(t.Def.Effects));
        Assert.Equal(StatusKind.Bleed, apply.Payload.Kind);
        Assert.Contains(StatusKind.Bleed, kit.GearStatuses);
    }
}

public class WorldLogicTests
{
    [Fact]
    public void Conditions_over_facts_knowledge_items_relations_background()
    {
        var s = Make("outcast");
        s.World.Facts["beasts.population"] = 70;
        Assert.True(Rules.Test(C("{ fact: 'beasts.population', gte: 50 }"), s.C));
        Assert.True(Rules.Test(C("{ bg: 'outcast' }"), s.C));
        Assert.True(Rules.Test(C("{ hasTag: 'kerchief_colors' }"), s.C));
        Assert.True(Rules.Test(C("{ hasItem: 'lockpicks' }"), s.C));
        Assert.True(Rules.Test(C("{ all: [{ knows: 'underworld' }, { not: { knows: 'beastlore' } }] }"), s.C));
        Rules.Apply(E("{ rel: { npc: 'rav', trust: 30 } }"), s.C);
        Assert.True(Rules.Test(C("{ rel: { npc: 'rav', axis: 'trust', gte: 30 } }"), s.C));
    }

    [Fact]
    public void Changes_give_items_gold_entries_traits_with_notices()
    {
        var s = Make();
        Rules.Apply(Es("[{ give: 'wolf_pelt', qty: 2 }, { gold: 30 }, { quest: { id: 'beasts', entry: 'rumour' } }, { trait: 'wolf_friend' }]"), s.C);
        Assert.Equal(2, Inventory.Count(s.Ch, "wolf_pelt"));
        Assert.Equal(55, s.Ch.Gold);
        Assert.Equal(QuestStatus.Active, s.World.Quests["beasts"].Status);
        Assert.Contains("wolf_friend", s.Ch.Traits);
        Assert.True(s.Notices.Count >= 4);
    }

    [Fact]
    public void History_reaches_witnesses_at_once_and_everyone_else_through_gossip()
    {
        var s = Make();
        Rules.Apply(E("{ history: { id: 'stole_cargo', text: 'kept the Coyle cargo', tags: ['theft'], spread: 2, sentiment: { trust: -20 }, reactions: { harlan: { trust: -60, affection: -40 } } }, witnesses: ['jory'] }"), s.C);
        Assert.Contains("stole_cargo", s.World.Npc("jory").Memories);
        Assert.Equal(0, s.World.Npc("harlan").Trust);
        var social = new Dictionary<string, List<string>> { ["harlan"] = ["jory", "rook"], ["rook"] = ["harlan", "holloway"], ["holloway"] = ["rook"] };
        var rng = Lcg(0.1);
        for (int d = 0; d < 6; d++) Simulation.AdvanceDay(s.C, rng, new(), social);
        Assert.Contains("stole_cargo", s.World.Npc("harlan").Memories);
        Assert.Equal(-60, s.World.Npc("harlan").Trust);
        Assert.Contains("distrusts", Rules.Attitude(s.World.Npc("harlan")));
    }

    [Fact]
    public void Scheduled_consequences_and_daily_rules_fire_on_the_day()
    {
        var s = Make();
        Rules.Apply(E("{ later: { days: 2, id: 'survivors_die', effect: { set: { 'caravan.survivors': 'dead' } } } }"), s.C);
        var rules = new List<DailyRule> { Rule("{ id: 'escalate', when: { fact: 'beasts.outcome', exists: false }, effect: { add: { 'beasts.severity': 1 } } }") };
        var none = new Dictionary<string, List<string>>();
        Simulation.AdvanceDay(s.C, () => 0.5, rules, none);
        Assert.False(s.World.Facts.ContainsKey("caravan.survivors"));
        Simulation.AdvanceDay(s.C, () => 0.5, rules, none);
        Assert.Equal("dead", s.World.Fact("caravan.survivors").Str);
        Assert.Equal(2, s.World.Fact("beasts.severity").Number);
    }

    [Fact]
    public void A_settled_quest_is_never_reopened_by_a_late_active()
    {
        var s = Make(seed: 3);
        Rules.Apply(E("{ quest: { id: 'beasts', status: 'resolved', outcome: 'cured' } }"), s.C);
        Rules.Apply(E("{ quest: { id: 'beasts', status: 'active', entry: 'holloway_bounty' } }"), s.C);
        Assert.Equal(QuestStatus.Resolved, s.World.Quests["beasts"].Status);
        Assert.Contains("holloway_bounty", s.World.Quests["beasts"].Entries);
    }

    [Fact]
    public void Grades_how_people_feel_loudest_first()
    {
        var s = Make();
        var n = s.World.Npc("maeca");
        n.Flags["met"] = true;
        Assert.Equal("unsure of you", Rules.Attitude(n));
        n.Affection = 20; n.Respect = 45;
        Assert.Equal("respects you, likes you", Rules.Attitude(n));
        n.Fear = 25; n.Trust = -50;
        Assert.Equal("distrusts you, respects you", Rules.Attitude(n));
    }

    [Fact]
    public void Reads_the_powers_of_the_Verge_from_what_the_world_holds()
    {
        var s = Make("hunter");
        StandingEntry? Find(string id) => Standings.Of(s.C).Find(x => x.Id == id);
        Assert.Null(Find("pack"));
        Rules.Apply(Es("[{ quest: { id: 'beasts', entry: 'rumour', status: 'active' } }, { quest: { id: 'caravan', entry: 'wreck', status: 'active' } }]"), s.C);
        Assert.Equal(StandingTone.Hostile, Find("pack")?.Tone);
        Assert.Equal("Hostile", Find("kerchief")?.Word);
        Assert.False(Standings.WolvesFriendly(s.C));
        Rules.Apply(E("{ set: { 'hollow.peace': true } }"), s.C);
        Assert.True(Standings.WolvesFriendly(s.C));
        Assert.Equal("Let you pass", Find("pack")?.Word);
        Rules.Apply(E("{ set: { 'pack.allied': true } }"), s.C);
        Assert.Equal(StandingTone.Ally, Find("pack")?.Tone);
        Rules.Apply(E("{ set: { redcowl: 'bargained' } }"), s.C);
        Assert.True(Standings.KerchiefsFriendly(s.C));
        Assert.Equal("Tolerated", Find("kerchief")?.Word);
        Rules.Apply(E("{ set: { 'be.crates': 'redcowl' } }"), s.C);
        Assert.Equal("Redcowl keeps the Coyle crates from the Dig, on your word.", Find("kerchief")?.Why);
        Rules.Apply(E("{ set: { 'roost.hostile': true } }"), s.C);
        Assert.False(Standings.KerchiefsFriendly(s.C));
        Assert.Equal("At war", Find("kerchief")?.Word);
        Rules.Apply(E("{ set: { 'caravan.survivors': 'rescued', 'caravan.cargo': 'kept' } }"), s.C);
        Assert.Equal("Cheated", Find("coyle")?.Word);
    }
}

public class DialogueTests
{
    static readonly Conversation Convo = Json.Parse<Conversation>(Js(@"{
      npc: 'maeca',
      entry: [{ when: { met: 'maeca' }, node: 'again' }, { node: 'hello' }],
      nodes: {
        hello: { id: 'hello', text: 'Who are you, {name}?', choices: [
          { text: 'I read the tracks. Something drove them out.', when: { knows: 'beastlore' }, badge: 'Beastlore', effects: [{ rel: { npc: 'maeca', respect: 15 } }], goto: 'agree' },
          { text: 'Tell me about the old empire.', when: { knows: 'arcana' }, locked: 'Requires: Arcana' },
          { text: 'Goodbye.', end: true },
        ] },
        agree: { id: 'agree', text: 'Then you see it too.', choices: [{ text: 'I do.', end: true }] },
        again: { id: 'again', text: 'Back again.', choices: [{ text: 'Bye.', end: true }] },
      },
    }"));

    [Fact]
    public void Background_choices_carry_badges_others_lock_with_reasons_meeting_is_remembered()
    {
        var s = Make("hunter");
        var run = new DialogueRunner(Convo, s.C);
        var p = run.Start()!;
        Assert.Equal("Who are you, Ashe?", p.Text);
        var beast = p.Choices.First(x => x.Badge == "Beastlore");
        Assert.True(beast.Enabled);
        var arcana = p.Choices.First(x => x.Locked != null);
        Assert.False(arcana.Enabled);
        var next = run.Choose(beast.Index).Next!;
        Assert.Equal("Then you see it too.", next.Text);
        Assert.Equal(15, s.World.Npc("maeca").Respect);
        Assert.Equal("Back again.", new DialogueRunner(Convo, s.C).Start()!.Text);
    }
}

public class SaveTests
{
    [Fact]
    public void Round_trips_character_world_and_location()
    {
        var s = Make();
        Rules.Apply(Es("[{ set: { 'caravan.cargo': 'kept' } }, { give: 'wolf_fang_necklace' }, { rel: { npc: 'harlan', trust: -40 } }]"), s.C);
        s.World.Day = 4;
        var dir = Path.Combine(Path.GetTempPath(), "su-saves-" + Guid.NewGuid().ToString("N"));
        try
        {
            var saves = new Saves(dir);
            Assert.True(saves.Write(1, new SaveData { Playtime = 123, Character = s.Ch, World = s.World, Location = new SaveLocation { Zone = "thornhollow", X = 3, Z = -7, Facing = 1 } }));
            var back = saves.Read(1)!;
            Assert.Equal("Ashe", back.Character.Name);
            Assert.Equal(4, back.World.Day);
            Assert.Equal("kept", back.World.Fact("caravan.cargo").Str);
            Assert.Equal(-40, back.World.Npcs["harlan"].Trust);
            Assert.Contains(back.Character.Pack, p => p?.Def == "wolf_fang_necklace");
            Assert.Equal(("thornhollow", 3.0, -7.0, 1.0), (back.Location.Zone, back.Location.X, back.Location.Z, back.Location.Facing));
            Assert.Equal(1, saves.LastSlot());
            Assert.Single(saves.Slots());
            // A code carries a save to another machine.
            var code = saves.ExportCode(1)!;
            Assert.True(saves.ImportCode(2, code));
            Assert.Equal("Ashe", saves.Read(2)!.Character.Name);
        }
        finally { Directory.Delete(dir, true); }
    }

    [Fact]
    public void A_shop_saved_before_it_kept_its_offered_lines_still_opens()
    {
        var s = Make();
        s.World.Shops["pell"] = new ShopState { RestockDay = 4 };
        var raw = Json.Write(new SaveData { Character = s.Ch, World = s.World })
            .Replace("\"offered\":[]", "\"offered\":null");
        Assert.Contains("\"offered\":null", raw);
        Assert.NotNull(Saves.Parse(raw)!.World.Shops["pell"].Offered);
    }

    [Fact]
    public void A_broken_save_is_set_aside_not_overwritten()
    {
        var dir = Path.Combine(Path.GetTempPath(), "su-saves-" + Guid.NewGuid().ToString("N"));
        try
        {
            var saves = new Saves(dir);
            File.WriteAllText(Path.Combine(dir, "slot0.json"), "{ not json");
            Assert.Null(saves.Read(0));
            Assert.Single(Directory.GetFiles(dir, "slot0.json.broken.*"));
        }
        finally { Directory.Delete(dir, true); }
    }
}
