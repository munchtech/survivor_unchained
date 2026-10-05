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

    /// <summary>A cinematic's other ending, played by its own hook: C11's spared part
    /// (Redcowl let up off his knee, the owner's 4 October decision).</summary>
    static readonly Dictionary<string, Action<Setup>> OtherEnding = new()
    {
        ["cin_raid_on_the_roost"] = s => s.World.Facts["redcowl"] = "spared",
    };

    [Fact]
    public void Every_cinematic_reads_from_its_first_line_to_its_last()
    {
        foreach (var id in Cinematics)
        {
            var lines = Lines(id, Q());
            if (OtherEnding.TryGetValue(id, out var other))
            {
                var s = Q();
                other(s);
                lines.AddRange(Lines(id, s));
            }
            Assert.NotEmpty(lines);
            Assert.All(lines, l => Assert.NotEqual("", l.Speaker));
            Assert.Equal(Convo(id).Nodes.Count, lines.Select(l => l.Id).Distinct().Count());
        }
        Assert.Equal(["cin_drowned_fire.bedroll", "cin_drowned_fire.prints", "cin_drowned_fire.lamp", "cin_drowned_fire.call", "cin_drowned_fire.frost"], Lines("cin_drowned_fire", Q()).Select(l => l.Id));
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
    public void Redcowl_spared_owes_her_the_rest_of_him_and_never_says_the_name()
    {
        // The owner, 4 October: spared, his words at the knee, then he gets up and strikes the camp.
        var s = Q("outcast");
        s.Ch.Sex = Sex.Female;
        s.World.Facts["redcowl"] = "spared";
        var lines = Lines("cin_raid_on_the_roost", s);
        Assert.Equal(["cin_raid_on_the_roost.spared", "cin_raid_on_the_roost.flit"], lines.Select(l => l.Id));
        Assert.Contains("the rest of me", lines[0].Text);
        Assert.Contains("lass", lines[0].Text);
        Assert.Contains("We're flitting!", lines[1].Text);
        Assert.True(s.World.Fact("redcowl.last_words").IsNull);
        // Told "Ashford" once in his camp, he squares it, and still does not say it: that is spent dying.
        var k = Q();
        k.World.Facts["redcowl"] = "spared";
        k.World.Facts["redcowl.ashford_said"] = true;
        var said = Lines("cin_raid_on_the_roost", k)[0].Text;
        Assert.Contains("square, lad", said);
        Assert.DoesNotContain("Ashford", said);
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
    public void Wenna_gives_her_mask_to_whoever_cleaned_her_stream()
    {
        var s = Q();
        Talk(Convo("wenna"), s.C, "goodbye");
        var mask = () => Greet(Convo("wenna"), s.C).Choices.Single(c => c.Text.Contains("beaked mask"));
        Assert.False(mask().Enabled);
        Rules.Apply(E("{ history: { id: 'stream_cleared', text: 'stopped the poison in the Thornhollow stream', tags: ['deed'], spread: 2 } }"), s.C);
        s.World.Facts["beasts.outcome"] = "cured";
        Assert.True(mask().Enabled);
        Assert.Contains("You cleaned my stream", Talk(Convo("wenna"), s.C, "beaked mask")!.Text);
        // Sold to Pell, it is not cleaned; it is bought.
        var p = Q();
        Talk(Convo("wenna"), p.C, "goodbye");
        Rules.Apply(E("{ history: { id: 'stream_cleared', text: 'stopped the poison in the Thornhollow stream', tags: ['deed'], spread: 2 } }"), p.C);
        p.World.Facts["beasts.outcome"] = "exploited";
        Assert.False(Greet(Convo("wenna"), p.C).Choices.Single(c => c.Text.Contains("beaked mask")).Enabled);
    }

    [Fact]
    public void Keegan_sups_with_whoever_listened_to_her()
    {
        // The road (WRITING_PASS.md): the Warden's lore told her (+15 respect),
        // Ashe asked after (+10), and one dinner eaten with her (+10 affection).
        var s = Q("scholar");
        Talk(Convo("keegan"), s.C, "bye");
        s.Ch.Knowledge.Add("lore.warden");
        s.Ch.Knowledge.Add("lore.ashe");
        Talk(Convo("keegan"), s.C, "ford-warden");
        var k = s.World.Npc("keegan");
        Talk(Convo("keegan"), s.C, "ashe");
        Talk(Convo("keegan"), s.C, "dinner");
        s.World.Time = TimeOfDay.Night;
        var supper = Greet(Convo("keegan"), s.C).Choices.Single(c => c.Text.Contains("Have you eaten"));
        Assert.True(supper.Enabled, $"respect {k.Respect}, affection {k.Affection}");
    }

    [Fact]
    public void The_pump_runs_until_someone_stops_it_and_the_burial_is_one_morning()
    {
        var s = Q();
        Simulation.AdvanceDay(s.C, () => 0.5);
        Assert.Equal("running", s.World.Fact("dig.pump").Str);
        s.World.Facts["nell.told"] = "gone";
        Simulation.AdvanceDay(s.C, () => 0.5);
        Assert.True(s.World.Fact("nell.burying").Truthy);
        Simulation.AdvanceDay(s.C, () => 0.5);
        Assert.False(s.World.Fact("nell.burying").Truthy);
        Assert.True(s.World.Fact("nell.buried").Truthy);
    }

    [Fact]
    public void The_voices_keep_their_rules_once_heard_aloud()
    {
        // VOICES.md: Jory has the cage in everything he says, and never says "cage".
        foreach (var n in Convo("jory").Nodes.Values.Where(n => (n.Speaker ?? "jory") == "jory"))
            foreach (var v in n.Text) Assert.DoesNotContain("cage", v.Text, StringComparison.OrdinalIgnoreCase);
        Assert.All(Lore.Person("jory")!.Barks, b => Assert.DoesNotContain("cage", b, StringComparison.OrdinalIgnoreCase));
        // Vonnra never answers yes or no.
        Assert.DoesNotContain("It is.", Convo("vonnra").Nodes["cb_vault3"].Text[0].Text);
        // The curfew is heard only after dark.
        var curfew = Lore.FolkLines.Where(l => l.Text.Contains("curfew") || l.Text.Contains("shut till dawn")).ToList();
        Assert.Equal(2, curfew.Count);
        Assert.All(curfew, l => Assert.True(l.Night));
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

    [Fact]
    public void Chid_never_tells_a_mourner_what_she_saw()
    {
        // The burial morning: nothing from Chid about it until she has stood at
        // the grave, and then not what she saw there.
        var s = Q();
        Talk(Convo("chid"), s.C, "goodbye");
        s.World.Facts["nell.told"] = "gone";
        Simulation.AdvanceDay(s.C, () => 0.5);
        Assert.True(s.World.Fact("nell.burying").Truthy);
        Assert.NotEqual("cb_nell", new DialogueRunner(Convo("chid"), s.C).Start()!.Node.Id);
        Rules.Apply(E("{ zone: { id: 'waystation', key: 'burial', value: true } }"), s.C);
        var at = new DialogueRunner(Convo("chid"), s.C).Start()!;
        Assert.Equal("cb_nell", at.Node.Id);
        Assert.StartsWith("I sang it flat.", at.Text);
        // Kept away, she hears it from him the next day.
        var away = Q();
        Talk(Convo("chid"), away.C, "goodbye");
        away.World.Facts["nell.told"] = "gone";
        Simulation.AdvanceDay(away.C, () => 0.5);
        Simulation.AdvanceDay(away.C, () => 0.5);
        Assert.StartsWith("We buried Nell", new DialogueRunner(Convo("chid"), away.C).Start()!.Text);
    }

    [Fact]
    public void The_carter_wears_thinner_with_every_death()
    {
        // LINE_NOTES 4.1: the same white lie, until it can be asked about.
        var s = Q();
        Talk(Convo("chid"), s.C, "goodbye");
        string Woke(int deaths)
        {
            s.World.Facts["player.deaths"] = deaths;
            s.World.Facts["player.just_died"] = true;
            var p = new DialogueRunner(Convo("chid"), s.C).Start()!;
            Assert.Equal("woke", p.Node.Id);
            return p.Text;
        }
        var said = Enumerable.Range(1, 4).Select(Woke).ToList();
        Assert.Equal(4, said.Distinct().Count());
        Assert.Contains("A carter found you on the Old Road", said[0]);
        Assert.Contains("...Well. Someone did.", said[2]);
        Assert.Contains("The carter sends his regards.", said[3]);
        // "Someone always does" is Vonnra's, in the fortune (C09 shot 7), and nobody else's.
        foreach (var (_, c) in Dialogue.All.Where(kv => kv.Key != "vonnra"))
            foreach (var n in c.Nodes.Values)
                foreach (var v in n.Text) Assert.DoesNotContain("Someone always does", v.Text);
        // The other signatures (VOICES.md) are their owners' too, in conversation and in passing.
        var signatures = new Dictionary<string, string> { ["before you ask"] = "maeca", ["Not there"] = "keegan", ["Payment, always"] = "vonnra" };
        foreach (var (phrase, owner) in signatures)
        {
            foreach (var (_, c) in Dialogue.All)
                foreach (var n in c.Nodes.Values.Where(n => (n.Speaker ?? c.Npc) != owner))
                    foreach (var v in n.Text) Assert.DoesNotContain(phrase, System.Text.RegularExpressions.Regex.Replace(v.Text, @"\([A-Z][^)]*\)", ""));
            foreach (var p in Lore.Npcs.Values.Concat(Lore.Outsiders.Values).Where(p => p.Id != owner))
                foreach (var b in p.Barks.Concat(p.NightBarks ?? new()).Concat((p.Said ?? new()).Select(l => l.Text))) Assert.DoesNotContain(phrase, b);
        }
        s.World.Facts["player.just_died"] = true;
        Assert.Contains("I never asked his name", Talk(Convo("chid"), s.C, "Which carter")!.Text);
        // And somebody in the street notices there are no carts.
        Assert.Contains(Lore.FolkLines, l => l.Text.Contains("who keeps bringing that one in") && l.When != null);
    }

    static List<string> Said(string npc, Setup s, bool dark) =>
        Lore.Person(npc)!.Said!.Where(l => (l.Night == null || l.Night == dark) && Rules.Test(l.When, s.C)).Select(l => l.Text).ToList();

    [Fact]
    public void The_town_stops_saying_what_has_stopped_being_true()
    {
        // LINE_NOTES 10: a person's barks follow what the survivor settled.
        var s = Q();
        Assert.Contains("Late. Jory's never late.", Said("harlan", s, false));
        Assert.DoesNotContain(Lore.Person("harlan")!.Barks, b => b.Contains("Jory"));
        s.World.Facts["caravan.survivors"] = "rescued";
        Assert.DoesNotContain("Late. Jory's never late.", Said("harlan", s, false));
        Assert.Contains("He sleeps with the lamp lit. So do I, now.", Said("harlan", s, true));
        Assert.DoesNotContain(Said("harlan", s, true), l => l.Contains("hated the dark"));
        // The Pack: loud while it lives, and a Hollow with nothing in it after.
        Assert.Contains("The Pack's loud tonight.", Said("maeca", s, true));
        s.World.Facts["beasts.outcome"] = "slaughtered";
        Assert.DoesNotContain("The Pack's loud tonight.", Said("maeca", s, true));
        Assert.Contains("Nothing calls in the Hollow now.", Said("maeca", s, true));
        Assert.DoesNotContain("They drank from the stream and fell down.", Said("tam", s, false));
        // Brannoc lied to still thinks she is on the road.
        s.World.Facts["nell.told"] = "lie";
        Assert.Contains("Low Kiln's three days. She'll be there by now.", Said("brannoc", s, false));
    }

    /// <summary>A night as Arenas.Finish leaves it in the world.</summary>
    static void Night(Setup s, string people, bool won, bool fell, bool story, double past = 0, bool longest = false)
    {
        var f = s.World.Facts;
        // The Pack as a new journey has it (Journey.New), or the dawn's rules count it gone.
        if (s.World.Fact("beasts.population").IsNull) f["beasts.population"] = 60;
        f["arena.last.people"] = people; f["arena.last.won"] = won; f["arena.last.fell"] = fell; f["arena.last.story"] = story;
        f["arena.last.past"] = past; f["arena.last.longest"] = longest; f["arena.last.ago"] = 0;
        f["arena.nights"] = s.World.Fact("arena.nights").Number + 1;
        if (fell) f["arena.fell"] = s.World.Fact("arena.fell").Number + 1;
        s.World.Time = TimeOfDay.Night;
    }

    /// <summary>Everything the town says about the last night that holds now.</summary>
    static List<string> NightTalk(Setup s, bool dark) =>
        Lore.Npcs.Values.Concat(Lore.Outsiders.Values).SelectMany(p => p.Said ?? new())
            .Where(l => SurvivorUnchained.Core.Json.Write(l.When).Contains("arena.last.ago"))
            .Where(l => (l.Night == null || l.Night == dark) && Rules.Test(l.When, s.C)).Select(l => l.Text).ToList();

    [Fact]
    public void The_town_talks_about_the_night_just_past_and_then_lets_it_go()
    {
        // The experience audit's finding 5: after any night, someone says something, that
        // night and the morning after; by the next night it is old news.
        foreach (var people in new[] { "pack", "dead", "lamplings", "kerchiefs" })
            foreach (var won in new[] { true, false })
                foreach (var fell in new[] { true, false })
                    foreach (var story in new[] { true, false })
                    {
                        var s = Q();
                        Night(s, people, won, fell, story);
                        Assert.NotEmpty(NightTalk(s, true));
                        Simulation.AdvanceDay(s.C, () => 0.99);
                        Assert.NotEmpty(NightTalk(s, false));
                        s.World.Time = TimeOfDay.Night;
                        Assert.Empty(NightTalk(s, true));
                        Simulation.AdvanceDay(s.C, () => 0.99);
                        Assert.Empty(NightTalk(s, false));
                    }
        // Who says what: the count on the wall, the lamp on the slate, the dark like moths.
        var t = Q();
        Night(t, "pack", won: true, fell: false, story: false, past: 16, longest: true);
        var tonight = NightTalk(t, true);
        Assert.Contains("One in. Count's right, for once.", tonight);
        Assert.Contains("Lamp burned all night for you, pet. A night's ember. It's on your slate.", tonight);
        Assert.Contains(tonight, l => l.Contains("like moths round a candle"));
        Assert.Contains(tonight, l => l.StartsWith("Your longest yet."));
        Simulation.AdvanceDay(t.C, () => 0.99);
        // A Pack night: Maeca hears it, and once the Pack is gone she asks what is still out there.
        Assert.Contains("Heard you out by the Hollow last night. From the Blind. How many?", Said("maeca", t, false));
        t.World.Facts["beasts.outcome"] = "slaughtered";
        Assert.Contains("There's no Pack left. I counted the pelts. So what were you killing?", Said("maeca", t, false));
        // Chid's first fall gives away that the survivor is always cold at night; his "again" waits for a second.
        var c = Q();
        Night(c, "dead", won: false, fell: true, story: true);
        Assert.Contains(NightTalk(c, true), l => l.Contains("Colder than usual"));
        Assert.DoesNotContain(NightTalk(c, true), l => l.StartsWith("Back again!"));
    }

    [Fact]
    public void Nobody_says_an_answer_before_its_act()
    {
        // The bible's first rule holds for the interface too (LINE_NOTES 4.4), and
        // the nemesis never wears a name the story has spent (4.2).
        var risen = Callings.Trait("risen_once")!.Text;
        Assert.DoesNotContain("died", risen);
        Assert.StartsWith("You fell, and got up again.", risen);
        // Maeca keeps Ashford until it is earned: not on meeting, not on her plate.
        foreach (var v in Convo("maeca").Nodes["first"].Text) Assert.DoesNotContain("Ashford", v.Text);
        Assert.DoesNotContain("Ashford", Lore.Person("maeca")!.Title);
        Assert.Contains("Ashford was.", Convo("rook").Nodes["valley"].Text[0].Text);
        // "Comes back" is the ledger's word; the Wayfinder does not spend it on meeting.
        Assert.DoesNotContain("comes back", Convo("wayfinder").Nodes["first"].Text[0].Text);
    }

    [Fact]
    public void The_voice_that_calls_her_up_the_road_opens_the_fortune()
    {
        // Bible, "Who tells it": Vonnra calls the survivor up the road at the waking,
        // unnamed, and opens the fortune with the same words.
        var call = Convo("cin_drowned_fire").Nodes["call"];
        Assert.Equal("far_voice", call.Speaker);
        Assert.DoesNotContain("Vonnra", Lore.Speakers["far_voice"].Name);
        Assert.Contains("No charge, this once.", call.Text[0].Text);
        foreach (var v in Convo("vonnra").Nodes["fortune"].Text) Assert.Contains("No charge, this once.", v.Text);
    }

    [Fact]
    public void Grimtunnel_never_finishes_surface_meat_at_her_after_the_ford()
    {
        // C03: he smells downstairs on her and cannot finish the word. From then on
        // he never does (C12 and every arena); Snib, who has not smelled her, does.
        foreach (var n in Convo("cin_dig_boils_over").Nodes.Values)
            foreach (var v in n.Text) Assert.DoesNotContain("surface-meat", v.Text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("surface-m—", Convo("cin_heart_goes_down").Nodes.Values.SelectMany(n => n.Text).Select(v => v.Text).Single(t => t.StartsWith("Finders keepers")));
    }

    [Fact]
    public void Brannoc_says_twelve_once_in_a_playthrough()
    {
        // Twelve irons, and a girl of twelve he made: said the first time she passes
        // the forge after the truth, and never again.
        var p = Route.New();
        p.W.Facts["nell.told"] = "gone";
        p.Enter("waystation");
        var smith = p.Zone!.Actors["brannoc"];
        Assert.Equal("Twelve, I made.", smith.Urgent!());
        Assert.DoesNotContain("Twelve, I made.", smith.Said!());
        smith.Spoken!("Twelve, I made.");
        Assert.Null(smith.Urgent!());
        p.Leave();
        p.Enter("waystation");
        Assert.Null(p.Zone!.Actors["brannoc"].Urgent!());
    }
}
