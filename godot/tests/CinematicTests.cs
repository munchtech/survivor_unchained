using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

/// <summary>The cinematics' lines as the data holds them (docs/cinematics):
/// each cinematic's conversation walks from its first line to its last, every
/// line a VO id; the lines that vary by the survivor vary; and what a
/// cinematic leaves in the world is read where the scripts say it is.</summary>
public class CinematicTests
{
    static Setup Q(string bg = "hunter")
    {
        var s = Make(bg, "Wren", 5);
        s.World.Facts["prologue.done"] = true;
        return s;
    }

    static Conversation Convo(string id) => Dialogue.Find(id) ?? throw new KeyNotFoundException(id);

    /// <summary>A cinematic's lines in order, as its player reads them.</summary>
    static List<(string Id, string Speaker, string Text)> Lines(string id, Setup s)
    {
        var r = new DialogueRunner(Convo(id), s.C);
        var p = r.Start();
        var o = new List<(string, string, string)>();
        while (p != null)
        {
            o.Add(($"{id}.{p.Node.Id}", p.Speaker, p.Text));
            if (p.Choices.Count > 0) { Assert.Equal("(Continue.)", Assert.Single(p.Choices).Text); break; }
            p = r.Advance();
        }
        return o;
    }

    static readonly string[] Cinematics =
    [
        "cin_drowned_fire", "cin_none_cross", "cin_heart_goes_down", "cin_first_light", "cin_forty_one_mouths",
        "cin_iron_marker", "cin_raid_on_the_roost", "cin_dig_boils_over", "cin_behind_the_door",
    ];

    [Fact]
    public void Every_cinematic_reads_from_its_first_line_to_its_last()
    {
        foreach (var id in Cinematics)
        {
            var lines = Lines(id, Q());
            Assert.NotEmpty(lines);
            Assert.All(lines, l => Assert.NotEqual("", l.Speaker));
            Assert.Equal(Convo(id).Nodes.Count, lines.Count);
        }
        Assert.Equal(["cin_drowned_fire.bedroll", "cin_drowned_fire.prints", "cin_drowned_fire.frost"], Lines("cin_drowned_fire", Q()).Select(l => l.Id));
    }

    [Fact]
    public void The_dying_Warden_asks_one_thing_and_Grimtunnel_cannot_finish_his_insult()
    {
        var lines = Lines("cin_heart_goes_down", Q());
        Assert.Equal("Is it morning?", lines.First().Text);
        Assert.Equal("ford_warden", lines.First().Speaker);
        Assert.Contains("ever so grateful", lines.Last().Text);
    }

    [Fact]
    public void Redcowls_last_words_are_the_name_if_you_said_it_and_a_message_for_his_brother_if_not()
    {
        var s = Q("outcast");
        var last = Lines("cin_raid_on_the_roost", s).Last();
        Assert.Contains("the leg held", last.Text);
        Assert.Equal("leg", s.World.Fact("redcowl.last_words").Str);
        // Rav, told.
        Rules.Apply(E("{ history: { id: 'killed_redcowl', text: 'took the Roost by night', tags: ['kerchief'], spread: 2 } }"), s.C);
        s.World.Npc("rav").Flags["met"] = true;
        var p = Talk(Convo("rav"), s.C, "the leg held");
        Assert.Contains("Course it held", p!.Text);

        var k = Q("outcast");
        k.World.Facts["redcowl.ashford_said"] = true;
        Assert.StartsWith("...Ashford.", Lines("cin_raid_on_the_roost", k).Last().Text);
        Assert.Equal("ashford", k.World.Fact("redcowl.last_words").Str);
    }

    [Fact]
    public void Lines_said_to_a_woman_are_said_to_a_woman()
    {
        var s = Q();
        s.Ch.Sex = Sex.Female;
        Assert.Contains("lass", Lines("cin_raid_on_the_roost", s).First().Text);
        Assert.Contains("lad", Lines("cin_raid_on_the_roost", Q()).First().Text);
    }

    [Fact]
    public void The_Latin_is_read_only_by_a_reader()
    {
        Assert.Equal("Nondum. (Not yet.)", Lines("cin_behind_the_door", Q("scholar")).First().Text);
        Assert.Equal("Nondum.", Lines("cin_behind_the_door", Q("hunter")).First().Text);
    }

    [Fact]
    public void Vonnra_reads_only_after_dark_and_asks_for_the_hand_you_fight_with()
    {
        var s = Q();
        s.World.Time = TimeOfDay.Day;
        // Before the chapter is ready there is no fortune to refuse: the reason
        // "after dark" is never given for the wrong cause.
        Assert.DoesNotContain(Greet(Convo("vonnra"), s.C).Choices, c => c.Text.Contains("fortune"));
        s.World.Facts["chapter.ready"] = true;
        var fortune = Greet(Convo("vonnra"), s.C).Choices.Single(c => c.Text.Contains("fortune"));
        Assert.False(fortune.Enabled);
        Assert.Equal("She reads only after dark", fortune.Locked);
        s.World.Time = TimeOfDay.Night;
        Assert.Contains("the one you hold the blade with", Talk(Convo("vonnra"), s.C, "fortune")!.Text);
        // Read once: when the book is closed it is gone, by day or night.
        s.World.Facts["chapter.done"] = true;
        Assert.DoesNotContain(Greet(Convo("vonnra"), s.C).Choices, c => c.Text.Contains("fortune"));
        s.World.Time = TimeOfDay.Day;
        Assert.DoesNotContain(Greet(Convo("vonnra"), s.C).Choices, c => c.Text.Contains("fortune"));
        // An arcanist is asked for the hand she burns with.
        var a = Make("hunter", "Wren", 5);
        a.Ch.Archetype = "arcanist";
        a.World.Facts["chapter.ready"] = true;
        a.World.Time = TimeOfDay.Night;
        Assert.Contains("the one you burn with", Talk(Convo("vonnra"), a.C, "fortune")!.Text);
    }

    [Fact]
    public void The_old_wolf_smells_Maeca_on_her_lover()
    {
        var s = Q();
        var p = Talk(Convo("greymuzzle"), s.C, "kneel");
        Assert.Contains("his lip lifts off his teeth", p!.Text);
        Assert.DoesNotContain("tail moves", p.Text);
        var m = Q();
        m.World.Facts["maeca.lover"] = true;
        Assert.Contains("his tail moves, once", Talk(Convo("greymuzzle"), m.C, "kneel")!.Text);
    }

    [Fact]
    public void The_burial_is_this_morning_so_she_can_go()
    {
        var s = Q();
        s.World.Facts["nell.told"] = "gone";
        var heard = string.Join(" ", Simulation.AdvanceDay(s.C, () => 0.5).Lines);
        Assert.Contains("They are burying her this morning", heard);
        Assert.Contains("Lie down, lie down", Lines("cin_iron_marker", s).First().Text);
    }

    [Fact]
    public void The_ground_stops_Vonnra_in_the_middle_of_the_last_reading()
    {
        var s = Q("hunter");
        s.World.Facts["chapter.ready"] = true;
        s.World.Time = TimeOfDay.Night;
        var r = new DialogueRunner(Convo("vonnra"), s.C);
        var p = r.Start();
        while (p!.Choices.Count == 0) p = r.Advance();
        p = r.Choose(p.Choices.First(c => c.Text.Contains("fortune")).Index).Next;
        while (p!.Choices.Count == 0) p = r.Advance();
        Assert.Equal("f_below", p.Node.Id);
        Assert.Contains("And the door in the hillside...", p.Text);
        Assert.EndsWith("She looks east, into the dark, and does not finish.)", p.Text);
    }

    [Fact]
    public void Keegan_says_oil_keeps_it_sleeping_and_the_book_says_not_oil()
    {
        var s = Q("scholar");
        Talk(Convo("keegan"), s.C, "bye");
        s.Ch.Knowledge.Add("lore.warden");
        Assert.Contains("Ember wakes it.", Talk(Convo("keegan"), s.C, "ford-warden")!.Text);
        Assert.Contains("Not oil. Wrong colour.", Lore.Quests["lamps"].Entries["book"]);
    }

    [Fact]
    public void Every_survivor_is_cold_by_night_and_Sella_says_so_by_the_third_morning()
    {
        // The body's hours (STORY_BIBLE section 1): cold as the river all night, warm
        // by breakfast. Every survivor is Unchained from the ford, died since or not.
        var s = Q("hunter");
        s.Ch.Gold = 60;
        Talk(Convo("sella"), s.C, "how much", "15 gold, then", "kiss her", "until next time");
        Assert.False(s.World.Fact("sella.felt_cold").Truthy);
        Talk(Convo("sella"), s.C, "how much", "15 gold, then", "kiss her", "until next time");
        Assert.False(s.World.Fact("sella.felt_cold").Truthy);
        Assert.True(s.World.Npc("sella").Flag("say:cold_bath").Truthy);
        var r = new DialogueRunner(Convo("sella"), s.C);
        var p = r.Start();
        while (p!.Choices.Count == 0) p = r.Advance();
        p = r.Choose(p.Choices.First(c => c.Text.Contains("how much", StringComparison.OrdinalIgnoreCase)).Index).Next;
        while (p!.Choices.Count == 0) p = r.Advance();
        p = r.Choose(p.Choices.First(c => c.Text.Contains("15 gold, then")).Index).Next;
        while (p!.Choices.Count == 0) p = r.Advance();
        p = r.Choose(p.Choices.First(c => c.Text.Contains("kiss her", StringComparison.OrdinalIgnoreCase)).Index).Next;
        while (p!.Choices.Count == 0) p = r.Advance();
        Assert.Contains("cold as the river all night", p.Text);
        Assert.Contains("warm as toast", p.Text);
        r.Choose(p.Choices.First(c => c.Text.Contains("until next time", StringComparison.OrdinalIgnoreCase)).Index);
        Assert.True(s.World.Fact("sella.felt_cold").Truthy);
        Assert.True(s.World.Fact("sella.cold_sold").Truthy);
    }
}
