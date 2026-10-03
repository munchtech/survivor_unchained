using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

/// <summary>The Act 1 writing pass, played: things found before anyone asked
/// for them start their story instead of finishing it, people react to a
/// survivor who arrives already knowing, and the choices that only pay off
/// in later acts leave their mark on the world now (docs/WRITING_PASS.md).</summary>
public class BreadcrumbTests
{
    static Setup Q(string bg = "hunter")
    {
        var s = Make(bg, "Wren", 5);
        s.World.Facts["prologue.done"] = true;
        s.World.Facts["beasts.population"] = 60;
        return s;
    }

    static Conversation Convo(string id) => Dialogue.Find(id) ?? throw new KeyNotFoundException(id);
    static List<string> Day(Setup s) => Simulation.AdvanceDay(s.C, () => 0.5).Lines;
    static void Give(Setup s, string id, int qty = 1) => Inventory.AddToPack(s.Ch, Inventory.Make(s.Ch, id, qty: qty));
    static void Entries(Setup s, string quest, params string[] entries)
    {
        foreach (var e in entries) Rules.Apply(E($"{{ quest: {{ id: '{quest}', status: 'active', entry: '{e}' }} }}"), s.C);
    }
    static bool Has(Setup s, string quest, string entry) => s.World.Quests.TryGetValue(quest, out var q) && q.Entries.Contains(entry);
    static List<string> Offered(Setup s, string id) => Greet(Convo(id), s.C).Choices.Select(c => c.Text).ToList();
    static void Meet(Setup s, string id) => s.World.Npc(id).Flags["met"] = true;

    /// <summary>Vonnra's fortune, read through to its last question.</summary>
    static (DialogueRunner R, Presented P, string Read) Fortune(Setup s)
    {
        var r = new DialogueRunner(Convo("vonnra"), s.C);
        var p = r.Start()!;
        p = r.Choose(p.Choices.First(c => c.Text.Contains("fortune", StringComparison.OrdinalIgnoreCase)).Index).Next!;
        var read = new List<string>();
        while (p.Choices.Count == 0) { read.Add(p.Text); p = r.Advance()!; }
        read.Add(p.Text);
        return (r, p, string.Join(" ", read));
    }

    /* ---------------------------------------------- found before it was asked for -- */

    [Fact]
    public void A_ledger_burgled_on_the_first_night_starts_the_caravan_instead_of_ending_it()
    {
        var s = Q("outcast");
        Give(s, "pell_ledger");
        // Nothing to expose yet: the survivor cannot know what "R." was paid for.
        var offered = Offered(s, "holloway");
        Assert.DoesNotContain(offered, t => t.Contains("Here's his ledger"));
        Assert.Contains(offered, t => t.Contains("I found this book"));
        var p = Talk(Convo("holloway"), s.C, "found this book");
        Assert.Contains("Jessop", p!.Text);
        Assert.True(Has(s, "caravan", "ledger_read"));
        Assert.Equal(QuestStatus.Active, s.World.Quests["caravan"].Status);
        // Who "R." is, is the next thing to find: until then, still nothing to expose.
        Assert.DoesNotContain(Offered(s, "holloway"), t => t.Contains("Here's his ledger"));
        Entries(s, "caravan", "wreck");
        Talk(Convo("holloway"), s.C, "his ledger");
        Assert.Equal("exposed", s.World.Fact("caravan.pell").Str);
    }

    [Fact]
    public void Harlan_reads_the_ledger_too_and_sends_you_to_find_who_R_is()
    {
        var s = Q();
        Give(s, "pell_ledger");
        Talk(Convo("harlan"), s.C, "found this book");
        Assert.True(Has(s, "caravan", "ledger_read"));
        Assert.Equal(1, Inventory.Count(s.Ch, "pell_ledger"));
        Assert.DoesNotContain(Offered(s, "harlan"), t => t.Contains("Pell Varrow paid the Kerchiefs"));
    }

    [Fact]
    public void Pell_is_glad_of_a_thief_who_does_not_know_what_he_stole()
    {
        var s = Q("outcast");
        Give(s, "pell_ledger");
        Assert.Contains("don't know what you're holding", Talk(Convo("pell"), s.C, "read your ledger")!.Text);
        var k = Q("outcast");
        Give(k, "pell_ledger");
        Entries(k, "caravan", "harlan_plea", "wreck");
        Assert.DoesNotContain("don't know what you're holding", Talk(Convo("pell"), k.C, "read your ledger")!.Text);
    }

    [Fact]
    public void Jory_home_before_his_uncle_ever_met_you_is_met_as_news_not_a_plea()
    {
        var s = Q();
        s.World.Facts["caravan.survivors"] = "rescued";
        var r = new DialogueRunner(Convo("harlan"), s.C);
        var p = r.Start()!;
        Assert.Contains("bar in your hands", p.Text);
        Assert.DoesNotContain("days late", p.Text);
        Assert.False(Has(s, "caravan", "harlan_plea"));
        double gold = s.Ch.Gold;
        r.Choose(p.Choices.First(c => c.Text.Contains("Jory's alive")).Index);
        Assert.Equal(gold + 100, s.Ch.Gold);
    }

    [Fact]
    public void A_strongbox_carried_in_cold_is_met_with_the_seal_and_the_boy()
    {
        var s = Q();
        Give(s, "coyle_strongbox");
        Assert.Contains("That's my seal", new DialogueRunner(Convo("harlan"), s.C).Start()!.Text);
    }

    [Fact]
    public void Harlan_counts_the_days_his_nephew_has_been_gone()
    {
        var s = Q();
        Assert.Contains("Four days", new DialogueRunner(Convo("harlan"), s.C).Start()!.Text);
        var w = Q();
        w.World.Facts["caravan.days"] = 3;
        Assert.Contains("A week", new DialogueRunner(Convo("harlan"), w.C).Start()!.Text);
    }

    [Fact]
    public void A_survivor_who_found_the_Roost_first_can_tell_Harlan_where_his_wagons_are()
    {
        var s = Q();
        Entries(s, "caravan", "roost_found");
        var p = Talk(Convo("harlan"), s.C, "seen your wagons");
        Assert.Contains("pay it twice", p!.Text);
        Assert.True(Has(s, "caravan", "roost_told"));
    }

    [Fact]
    public void Redcowl_tells_a_stranger_whose_wagons_they_are()
    {
        var s = Q("outcast");
        Talk(Convo("redcowl"), s.C, "whose wagons");
        Assert.True(Has(s, "caravan", "redcowl_wagons"));
        var k = Q("outcast");
        Entries(k, "caravan", "harlan_plea");
        Assert.DoesNotContain(Offered(k, "redcowl"), t => t.Contains("Whose wagons"));
    }

    [Fact]
    public void Snib_explains_his_pump_to_someone_who_does_not_yet_know_the_water_matters()
    {
        var s = Q("scholar");
        var offered = Offered(s, "snib");
        Assert.Contains(offered, t => t.Contains("What are you pumping"));
        Assert.DoesNotContain(offered, t => t.Contains("sinkhole") || t.Contains("poisoning"));
        Talk(Convo("snib"), s.C, "what are you pumping");
        Assert.Contains("clue.pipe", s.Ch.Knowledge);
        Assert.True(Has(s, "beasts", "snib_slurry"));
        Assert.DoesNotContain("root_cause", s.Ch.Knowledge);
        // The stream is the reason to ask him to move it; a sick wolf is the reason to care.
        Assert.DoesNotContain(Offered(s, "snib"), t => t.Contains("sinkhole"));
        s.Ch.Knowledge.Add("clue.sick_wolf");
        Assert.Contains(Offered(s, "snib"), t => t.Contains("sinkhole"));
    }

    [Fact]
    public void Harlan_pays_for_the_boy_even_after_you_sold_his_box()
    {
        var s = Q();
        Talk(Convo("harlan"), s.C, "goodbye");
        s.World.Facts["caravan.survivors"] = "rescued";
        s.World.Facts["caravan.cargo"] = "sold";
        double gold = s.Ch.Gold;
        var p = new DialogueRunner(Convo("harlan"), s.C);
        var first = p.Start()!;
        Assert.Contains("For the boy", first.Text);
        p.Choose(first.Choices.First(c => c.Text == "Take it.").Index);
        Assert.Equal(gold + 100, s.Ch.Gold);
        // Once paid, it is the plain refusal from then on.
        Assert.DoesNotContain("For the boy", new DialogueRunner(Convo("harlan"), s.C).Start()!.Text);
    }

    /* ------------------------------------------------------------- the lamps -- */

    [Fact]
    public void Brannoc_asks_after_his_daughter_and_the_truth_buries_her()
    {
        var s = Q();
        Talk(Convo("brannoc"), s.C, "goodbye");
        Day(s);
        var p = new DialogueRunner(Convo("brannoc"), s.C).Start()!;
        Assert.Equal("nell", p.Node.Id);
        Talk(Convo("brannoc"), s.C, "wagon on its side", "put her down", "quick");
        Assert.Equal("risen", s.World.Fact("nell.told").Str);
        Assert.True(Has(s, "lamps", "nell"));
        Assert.Contains(s.World.History, h => h.Id == "told_brannoc");
        Assert.Contains("Brannoc banked his forge", string.Join(" ", Day(s)));
        Assert.True(s.World.Fact("nell.buried").Truthy);
        Meet(s, "chid");
        Assert.Contains("We buried Nell", new DialogueRunner(Convo("chid"), s.C).Start()!.Text);
        // He asks once.
        Assert.NotEqual("nell", new DialogueRunner(Convo("brannoc"), s.C).Start()!.Node.Id);
    }

    [Fact]
    public void Brannoc_does_not_ask_on_the_day_you_arrive_nor_at_a_banked_forge()
    {
        var s = Q();
        Talk(Convo("brannoc"), s.C, "goodbye");
        Assert.NotEqual("nell", new DialogueRunner(Convo("brannoc"), s.C).Start()!.Node.Id);
        Day(s);
        s.World.Time = TimeOfDay.Night;
        Assert.NotEqual("nell", new DialogueRunner(Convo("brannoc"), s.C).Start()!.Node.Id);
        s.World.Time = TimeOfDay.Day;
        // Walking away from the question leaves it to be asked again.
        Assert.Equal("nell", new DialogueRunner(Convo("brannoc"), s.C).Start()!.Node.Id);
        Assert.Equal("nell", new DialogueRunner(Convo("brannoc"), s.C).Start()!.Node.Id);
    }

    [Fact]
    public void Holloway_turns_a_letter_face_down_at_night_from_the_third_day()
    {
        var s = Q();
        Talk(Convo("holloway"), s.C, "that's all");
        Assert.DoesNotContain(Offered(s, "holloway"), t => t.Contains("silver seal"));
        s.World.Day = 3;
        s.World.Time = TimeOfDay.Night;
        Assert.Contains("silver seal", Greet(Convo("holloway"), s.C).Text);
        Talk(Convo("holloway"), s.C, "silver seal");
        Assert.True(s.World.Fact("holloway.letter_seen").Truthy);
    }

    [Fact]
    public void A_lie_to_Brannoc_sends_him_to_the_gate_to_ask_strangers()
    {
        var s = Q();
        Talk(Convo("brannoc"), s.C, "goodbye");
        Day(s);
        Talk(Convo("brannoc"), s.C, "passed nobody");
        Assert.Equal("lie", s.World.Fact("nell.told").Str);
        Assert.False(s.World.Fact("nell.buried").Truthy);
        Day(s);
        Assert.Contains("Brannoc stopped a pedlar", string.Join(" ", Day(s)));
        Assert.Contains(Lore.FolkLines, l => l.Text.Contains("red-haired girl") && Rules.Test(l.When, s.C));
        Assert.Equal("Waiting for word from Low Kiln that his girl got there.", Lore.ConcernOf("brannoc", s.C));
    }

    [Fact]
    public void Brannoc_knows_his_own_mark_on_the_Wardens_lamp_iron()
    {
        var s = Q();
        Give(s, "wardens_lampiron");
        var p = Talk(Convo("brannoc"), s.C, "warden's fist");
        Assert.Contains("Mine", p!.Text);
        Assert.True(Has(s, "lamps", "mark"));
        Assert.True(Has(s, "lamps", "irons"));
    }

    [Fact]
    public void Holloway_learns_his_deserter_died_at_his_post()
    {
        var s = Q();
        s.Ch.Knowledge.Add("lore.warden");
        Talk(Convo("holloway"), s.C, "watch-post", "lit again");
        Assert.True(Has(s, "lamps", "book"));
        Assert.True(Has(s, "lamps", "post"));
        Assert.Contains("handcart and a spade", string.Join(" ", Day(s)));
    }

    [Fact]
    public void The_board_asks_for_carters_and_a_reader_of_the_watchmans_book_notices()
    {
        var s = Q();
        Assert.Matches("CARTERS WANTED", new DialogueRunner(Convo("board"), s.C).Start()!.Text);
        Assert.False(Has(s, "lamps", "notice"));
        s.Ch.Knowledge.Add("lore.warden");
        new DialogueRunner(Convo("board"), s.C).Start();
        Assert.True(Has(s, "lamps", "notice"));
    }

    [Fact]
    public void Vonnra_can_be_told_to_her_face_only_by_someone_who_has_the_pieces()
    {
        var s = Q("scholar");
        s.World.Facts["beasts.outcome"] = "cured";
        s.World.Facts["caravan.survivors"] = "rescued";
        s.World.Facts["chapter.ready"] = true;
        Assert.DoesNotContain(Fortune(s).P.Choices, c => c.Text.Contains("You lit the lamps"));

        var k = Q("scholar");
        k.World.Facts["beasts.outcome"] = "cured";
        k.World.Facts["caravan.survivors"] = "rescued";
        k.World.Facts["chapter.ready"] = true;
        Entries(k, "lamps", "irons", "coin");
        var (r, p, _) = Fortune(k);
        p = r.Choose(p.Choices.First(c => c.Text.Contains("You lit the lamps")).Index).Next!;
        Assert.Contains("Sit down, Wren", p.Text);
        p = r.Advance()!;
        Assert.Contains("Wren", p.Text);
        Assert.Equal("fortune", r.Choose(p.Choices[0].Index).Action);
        Assert.True(k.World.Fact("vonnra.accused").Truthy);
        Assert.True(Has(k, "lamps", "accused"));
        Assert.Contains("Wren", Greet(Convo("vonnra"), k.C).Text);
    }

    [Fact]
    public void What_is_said_in_the_blue_room_comes_back_in_the_fortune()
    {
        var s = Q("hunter");
        s.Ch.Gold = 20;
        Talk(Convo("sella"), s.C, "how much", "15 gold", "where you come from");
        Assert.True(s.World.Fact("sella.heard_past").Truthy);
        s.World.Facts["beasts.outcome"] = "cured";
        s.World.Facts["caravan.survivors"] = "rescued";
        s.World.Facts["chapter.ready"] = true;
        Assert.Contains("bow too big", Fortune(s).Read);
        var k = Q("hunter");
        k.World.Facts["beasts.outcome"] = "cured";
        k.World.Facts["caravan.survivors"] = "rescued";
        k.World.Facts["chapter.ready"] = true;
        Assert.Contains("far bank", Fortune(k).Read);
    }

    /* ------------------------------------------------------- the six crates -- */

    [Fact]
    public void Told_what_the_crates_are_for_Redcowl_keeps_them_from_the_hill_and_arms_you_against_it()
    {
        var s = Q("outcast");
        s.Ch.Knowledge.Add("clue.blasting_ember");
        Talk(Convo("redcowl"), s.C, "six crates", "blasting ember", "deep enough", "give me one");
        Assert.Equal("redcowl", s.World.Fact("be.crates").Str);
        Assert.Equal(1, Inventory.Count(s.Ch, "blasting_ember"));
        Assert.True(Has(s, "beasts", "redcowl_charge"));
        Entries(s, "caravan", "roost_found");
        Assert.DoesNotContain(Offered(s, "harlan"), t => t.Contains("six crates"));
        s.World.Facts["beasts.outcome"] = "cured";
        s.World.Facts["caravan.survivors"] = "rescued";
        s.World.Facts["chapter.ready"] = true;
        Assert.Contains("bandit's tent", Fortune(s).Read);
    }

    [Fact]
    public void Told_where_his_crates_are_Harlan_sends_for_them()
    {
        var s = Q();
        s.Ch.Knowledge.Add("clue.blasting_ember");
        Entries(s, "caravan", "roost_found");
        Talk(Convo("harlan"), s.C, "six crates");
        Assert.Equal("harlan", s.World.Fact("be.crates").Str);
        Assert.Contains("Two of Harlan's teamsters", string.Join(" ", Day(s)));
    }

    [Fact]
    public void Jory_told_the_truth_has_it_out_with_his_uncle()
    {
        var s = Q();
        Talk(Convo("harlan"), s.C, "goodbye");
        s.World.Facts["caravan.survivors"] = "rescued";
        s.Ch.Knowledge.Add("clue.blasting_ember");
        Talk(Convo("jory"), s.C, "what was in the crates", "blasting ember", "he knew");
        Assert.True(s.World.Fact("jory.knows_be").Truthy);
        Assert.True(Has(s, "caravan", "jory_told"));
        Assert.Contains("Jory did the shouting", string.Join(" ", Day(s)));
        Assert.Contains("He knows", new DialogueRunner(Convo("harlan"), s.C).Start()!.Text);
        // A boy who has his answer stops asking.
        Assert.DoesNotContain(Offered(s, "jory"), t => t.Contains("What was in the crates"));
    }

    [Fact]
    public void Jory_told_salt_believes_it()
    {
        var s = Q();
        s.World.Facts["caravan.survivors"] = "rescued";
        Talk(Convo("jory"), s.C, "what was in the crates", "salt");
        Assert.True(s.World.Fact("jory.lied_to").Truthy);
        Assert.False(s.World.Fact("jory.knows_be").Truthy);
        Assert.Empty(Day(s).Where(l => l.Contains("Jory did the shouting")));
    }

    [Fact]
    public void Who_tells_Redcowl_where_Pell_sleeps_decides_how_Pell_leaves()
    {
        var s = Q("outcast");
        Give(s, "pell_ledger");
        Talk(Convo("redcowl"), s.C, "sold you out", "in the loft");
        Assert.Equal("taken", s.World.Fact("pell.fate").Str);
        Assert.Equal("fled", s.World.Fact("caravan.pell").Str);
        Assert.Contains("red thread", string.Join(" ", Day(s)));

        var k = Q("outcast");
        Give(k, "pell_ledger");
        Talk(Convo("redcowl"), k.C, "sold you out", "find him yourself");
        Assert.Equal("ran", k.World.Fact("pell.fate").Str);
        Assert.Contains("fast horse", string.Join(" ", Day(k)));
    }

    [Fact]
    public void When_the_chapter_closes_the_crates_go_wherever_nobody_stopped_them()
    {
        string Settled(Action<Setup> before)
        {
            var s = Q();
            before(s);
            s.World.Facts["chapter.done"] = true;
            Day(s);
            return s.World.Fact("be.crates").Str!;
        }
        Assert.Equal("dig", Settled(_ => { }));
        Assert.Equal("dig", Settled(s => s.World.Facts["redcowl"] = "tricked"));
        Assert.Equal("watch", Settled(s => s.World.Facts["roost.cleared"] = true));
        Assert.Equal("burned", Settled(s => Rules.Apply(E("{ history: { id: 'burned_roost', text: 'set the Roost burning', tags: ['caravan'], spread: 2 } }"), s.C)));
        Assert.Equal("redcowl", Settled(s => s.World.Facts["be.crates"] = "redcowl"));
    }

    /* ------------------------------------------------- seeds for the later acts -- */

    [Fact]
    public void Seeds_are_planted_where_the_story_will_come_back_for_them()
    {
        var s = Q();
        Talk(Convo("tam"), s.C, "listening", "did right", "anything else strange");
        Assert.True(Has(s, "below", "tock"));
        Assert.True(s.World.Fact("tam.tock").Truthy);

        Meet(s, "wayfinder");
        Talk(Convo("wayfinder"), s.C, "margins", "nobody");
        Assert.Equal("nobody", s.World.Fact("wayfinder.name").Str);

        Meet(s, "keegan");
        s.Ch.Traits.Add("risen_once");
        Assert.Contains("under a sheet", new DialogueRunner(Convo("keegan"), s.C).Start()!.Text);
        Assert.True(s.World.Fact("keegan.saw_risen").Truthy);

        s.Ch.Knowledge.Add("lore.firstlamp");
        Talk(Convo("chid"), s.C, "note in ashe's trunk");
        Assert.True(s.World.Fact("chid.note_asked").Truthy);
    }

    [Fact]
    public void Rook_talks_about_whatever_is_still_unsettled()
    {
        var s = Q();
        s.World.Facts["caravan.survivors"] = "rescued";
        var p = Talk(Convo("rook"), s.C, "talk");
        Assert.Contains("Jory Coyle's home", p!.Text);
        Assert.DoesNotContain(p.Choices, c => c.Text.Contains("Jessop"));
        var k = Q();
        Assert.Contains("Jessop", Talk(Convo("rook"), k.C, "talk")!.Text);
    }
}
