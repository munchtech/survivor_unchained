using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

/// <summary>The two questlines, played through the same data the game uses, by
/// survivors from different backgrounds taking different roads.</summary>
public class QuestTests
{
    static Setup Q(string bg)
    {
        var s = Make(bg, "Wren", 5);
        s.World.Facts["prologue.done"] = true;
        s.World.Facts["beasts.population"] = 60;
        return s;
    }

    static Conversation Convo(string id) => Dialogue.Find(id) ?? throw new KeyNotFoundException(id);
    static void Day(Setup s, double r) => Simulation.AdvanceDay(s.C, () => r);
    static void Items(Setup s, string id, int qty = 1) => Inventory.AddToPack(s.Ch, Inventory.Make(s.Ch, id, qty: qty));

    [Fact]
    public void A_hunter_can_walk_into_the_Hollow_and_speak_with_Greymuzzle()
    {
        var s = Q("hunter");
        Talk(Convo("greymuzzle"), s.C, "kneel");
        Assert.True(s.World.Fact("hollow.peace").Bool);
        Assert.Contains("greymuzzle_met", s.World.Quests["beasts"].Entries);
        Assert.Contains("clue.sick_wolf", s.Ch.Knowledge);
        Talk(Convo("greymuzzle"), s.C, "leave");
    }

    [Fact]
    public void Someone_with_no_beastlore_cannot()
    {
        var s = Q("scholar");
        var e = Assert.Throws<InvalidOperationException>(() => Talk(Convo("greymuzzle"), s.C, "kneel"));
        Assert.Contains("locked", e.Message);
    }

    [Fact]
    public void A_scholar_reads_the_stream_in_one_visit_to_Wenna()
    {
        var s = Q("scholar");
        Items(s, "stream_sample");
        Talk(Convo("wenna"), s.C, "test it");
        Assert.Contains("root_cause", s.Ch.Knowledge);
        Assert.Equal(0, Inventory.Count(s.Ch, "stream_sample"));
        Assert.Contains("root_cause", s.World.Quests["beasts"].Entries);
    }

    [Fact]
    public void Talking_Snib_into_moving_the_pump_then_resting_cures_the_stream()
    {
        var s = Q("scholar");
        Talk(Convo("snib"), s.C, "sinkhole");
        Assert.Equal("moved", s.World.Fact("dig.pump").Str);
        Day(s, 0.5);
        Day(s, 0.5);
        Assert.Equal("cured", s.World.Fact("beasts.outcome").Str);
        Assert.Equal(QuestStatus.Resolved, s.World.Quests["beasts"].Status);
    }

    [Fact]
    public void Left_alone_the_wolves_come_to_the_gate()
    {
        var s = Q("devout");
        for (int d = 0; d < 7; d++) Day(s, 0.5);
        Assert.Equal("raided", s.World.Fact("tam.farm").Str);
        Assert.Equal("ignored", s.World.Fact("beasts.outcome").Str);
    }

    [Fact]
    public void Lying_to_Holloway_is_remembered()
    {
        var s = Q("outcast");
        Items(s, "wolf_pelt", 4);
        Talk(Convo("holloway"), s.C, "dealt with");
        Assert.True(s.World.Fact("beasts.told_holloway").Bool);
        Assert.DoesNotContain("lied_to_holloway", s.World.Npc("holloway").Memories);
        Day(s, 0.99);
        Assert.Contains("lied_to_holloway", s.World.Npc("holloway").Memories);
        Assert.True(s.World.Npc("holloway").Trust < -30);
    }

    [Fact]
    public void An_outcast_learns_about_the_clerk_from_Rav()
    {
        var s = Q("outcast");
        Talk(Convo("rav"), s.C, "news of coyle");
        Assert.Contains("clerk_turned", s.World.Quests["caravan"].Entries);
        Assert.Contains("clerks_key", s.World.Quests["caravan"].Entries);
        Assert.Equal(1, Inventory.Count(s.Ch, "clerks_key"));
    }

    [Fact]
    public void Pells_ledger_shown_to_Holloway_exposes_him_and_Harlan_hears()
    {
        var s = Q("hunter");
        Items(s, "pell_ledger");
        Talk(Convo("holloway"), s.C, "ledger");
        Assert.Equal("exposed", s.World.Fact("caravan.pell").Str);
        Assert.Contains("exposed_pell", s.World.Npc("harlan").Memories);
        Assert.True(s.World.Npc("harlan").Trust > 30);
    }

    [Fact]
    public void Redcowl_can_be_bluffed_or_bought()
    {
        var s = Q("outcast");
        Talk(Convo("redcowl"), s.C, "watch is on its way");
        Assert.Equal("tricked", s.World.Fact("redcowl").Str);
        var h = Q("hunter");
        Items(h, "wolf_pelt", 5);
        Talk(Convo("redcowl"), h.C, "coyle wagons", "pelts");
        Assert.Equal("bargained", h.World.Fact("redcowl").Str);
        Assert.Equal(0, Inventory.Count(h.Ch, "wolf_pelt"));
    }

    [Fact]
    public void Prisoners_do_not_wait_forever()
    {
        var s = Q("devout");
        for (int d = 0; d < 5; d++) Day(s, 0.5);
        Assert.Equal("dead", s.World.Fact("caravan.survivors").Str);
    }

    [Fact]
    public void The_cargo_has_an_ending_of_its_own()
    {
        // Returned: the quest settles the moment both halves are known.
        var a = Q("hunter");
        a.World.Facts["caravan.survivors"] = "rescued";
        a.World.Facts["caravan.box_taken"] = true;
        Items(a, "coyle_strongbox");
        Talk(Convo("harlan"), a.C, "strongbox");
        Assert.Equal("returned", a.World.Fact("caravan.cargo").Str);
        Assert.Equal(QuestStatus.Resolved, a.World.Quests["caravan"].Status);
        Assert.Equal("returned", a.World.Quests["caravan"].Outcome);
        Assert.Equal("Brought home", Chapter.Summary(a.Ch, a.World).Threads[1].Verdict);
        // Kept: carry the box three days and Harlan writes it off.
        var b = Q("outcast");
        b.World.Facts["caravan.survivors"] = "rescued";
        b.World.Facts["caravan.box_taken"] = true;
        var heard = new List<string>();
        for (int d = 0; d < 4; d++) heard.AddRange(Simulation.AdvanceDay(b.C, () => 0.5).Lines);
        Assert.Contains("Coyle strongbox", string.Join(" ", heard));
        Assert.Equal("kept", b.World.Fact("caravan.cargo").Str);
        Assert.Equal(QuestStatus.Resolved, b.World.Quests["caravan"].Status);
        Assert.True(b.World.Npc("harlan").Trust < -20);
        Assert.Contains("kept the Coyle strongbox", Chapter.Summary(b.Ch, b.World).Epithet);
        // Left in the Roost: the Kerchiefs sell it on.
        var k = Q("scholar");
        k.World.Facts["caravan.survivors"] = "rescued";
        for (int d = 0; d < 5; d++) Day(k, 0.5);
        Assert.Equal("with_kerchiefs", k.World.Fact("caravan.cargo").Str);
        Assert.Contains("cargo_moved", k.World.Quests["caravan"].Entries);
        Assert.Equal(QuestStatus.Resolved, k.World.Quests["caravan"].Status);
        // ...unless there is nobody left in the Roost to move it.
        var r = Q("scholar");
        r.World.Facts["caravan.survivors"] = "rescued";
        r.World.Facts["redcowl"] = "dead";
        for (int d = 0; d < 5; d++) Day(r, 0.5);
        Assert.False(r.World.Facts.ContainsKey("caravan.cargo"));
    }

    [Fact]
    public void With_both_stories_told_Vonnra_sends_for_you()
    {
        var s = Q("scholar");
        s.World.Facts["beasts.outcome"] = "cured";
        s.World.Facts["caravan.survivors"] = "rescued";
        Day(s, 0.5);
        Assert.True(s.World.Fact("chapter.ready").Bool);
        Assert.True(Rules.Test(C("{ fact: 'chapter.ready', eq: true }"), s.C));
    }

    [Fact]
    public void A_night_with_Sella_is_paid_up_front_and_leaves_you_warmed()
    {
        var s = Q("hunter");
        s.Ch.Gold = 20;
        Talk(Convo("sella"), s.C, "how much", "15 gold");
        Assert.Equal(5, s.Ch.Gold);
        Assert.Contains(s.Ch.Conditions, c => c.Id == ConditionId.Warmed);
        Assert.Equal(1, s.World.Fact("sella.nights").Number);
        var poor = Q("hunter");
        poor.Ch.Gold = 10;
        Assert.Contains("locked", Assert.Throws<InvalidOperationException>(() => Talk(Convo("sella"), poor.C, "how much", "15 gold")).Message);
    }

    [Fact]
    public void What_men_say_after_is_a_lead_once()
    {
        var s = Q("hunter");
        s.World.Quests["caravan"] = new QuestState { Id = "caravan", Status = QuestStatus.Active };
        Talk(Convo("sella"), s.C, "what do you hear");
        Talk(Convo("sella"), s.C, "what do you hear");
        Assert.Single(s.World.Quests["caravan"].Entries.Where(e => e == "sella_clerk"));
    }

    [Fact]
    public void Holloway_confronts_a_liar_and_a_debt_paid_softens_it()
    {
        var s = Q("outcast");
        Items(s, "wolf_pelt", 4);
        Talk(Convo("holloway"), s.C, "dealt with");
        Day(s, 0.99);
        double before = s.World.Npc("holloway").Trust;
        s.Ch.Gold = 40;
        Talk(Convo("holloway"), s.C, "pay back");
        Assert.Equal(10, s.Ch.Gold);
        Assert.Equal("repaid", s.World.Fact("holloway.lie_settled").Str);
        Assert.Equal(before + 15, s.World.Npc("holloway").Trust);
    }

    [Fact]
    public void A_lie_that_comes_true_is_never_found_out()
    {
        var s = Q("outcast");
        Items(s, "wolf_pelt", 4);
        Talk(Convo("holloway"), s.C, "dealt with");
        s.World.Facts["dig.pump"] = "broken";
        s.World.Facts["beasts.outcome"] = "cured";
        Day(s, 0.99);
        Assert.DoesNotContain("lied_to_holloway", s.World.Npc("holloway").Memories);
    }

    [Fact]
    public void Vonnra_reads_back_what_you_did_and_the_chapter_closes()
    {
        var s = Q("scholar");
        s.World.Facts["beasts.outcome"] = "cured";
        s.World.Facts["caravan.survivors"] = "rescued";
        s.World.Facts["caravan.cargo"] = "sold";
        Day(s, 0.5);
        Assert.True(s.World.Fact("chapter.ready").Bool);
        var r = new DialogueRunner(Convo("vonnra"), s.C);
        var p = r.Start();
        p = r.Choose(p!.Choices.First(x => Regex.IsMatch(x.Text, "fortune", RegexOptions.IgnoreCase)).Index).Next;
        var read = new List<string>();
        while (p != null && p.Choices.Count == 0) { read.Add(p.Text); p = r.Advance(); }
        read.Add(p!.Text);
        Assert.Matches("water running clear", string.Join(" ", read));
        Assert.Matches("strongbox go the other way", string.Join(" ", read));
        p = r.Choose(p.Choices[0].Index).Next;
        var end = r.Choose(p!.Choices[0].Index);
        Assert.Equal("fortune", end.Action);
        Assert.True(s.World.Fact("chapter.done").Bool);
        var sum = Chapter.Summary(s.Ch, s.World);
        Assert.Equal("Wren, who sold the Coyle strongbox", sum.Epithet);
        Assert.Equal(new[] { "Cured at the source", "Rescued, and robbed" }, sum.Threads.Select(t => t.Verdict));
        Assert.Equal(new[] { "vault", "below" }, sum.Open.Select(o => o.Id));
    }

    [Fact]
    public void A_chapter_with_nothing_settled_still_reads_as_a_page()
    {
        var s = Q("devout");
        var sum = Chapter.Summary(s.Ch, s.World);
        Assert.All(sum.Threads, t => Assert.Equal(ThreadTone.Open, t.Tone));
        Assert.Equal("Wren, late of the Low Ford road", sum.Epithet);
    }

    [Fact]
    public void The_morning_reports_who_heard_what()
    {
        var s = Q("hunter");
        Items(s, "pell_ledger");
        Talk(Convo("holloway"), s.C, "ledger");
        var r = Simulation.AdvanceDay(s.C, () => 0.01);
        Assert.Contains(r.Heard, h => h.Event == "exposed_pell" && h.Npc == "rook");
        Assert.Contains("Harlan Coyle was at the east gate", string.Join(" ", r.Lines));
    }

    [Fact]
    public void The_notice_board_changes_as_the_world_does()
    {
        var s = Q("devout");
        string Read() => new DialogueRunner(Convo("board"), s.C).Start()!.Text;
        Assert.Matches("WOLF BOUNTY", Read());
        s.World.Facts["beasts.outcome"] = "cured";
        s.World.Quests["beasts"].Status = QuestStatus.Resolved;
        s.World.Facts["caravan.survivors"] = "rescued";
        var t = Read();
        Assert.Matches("WITHDRAWN", t);
        Assert.Matches("Jory is home", t);
        Assert.DoesNotMatch("WOLF BOUNTY|MISSING", t);
        Assert.Equal(QuestStatus.Resolved, s.World.Quests["beasts"].Status);
    }

    [Fact]
    public void Pell_buys_the_cure_and_the_stream_clears_on_his_terms()
    {
        var s = Q("outcast");
        s.Ch.Knowledge.Add("root_cause");
        double gold = s.Ch.Gold;
        Talk(Convo("pell"), s.C, "terrible business");
        Talk(Convo("pell"), s.C, "killing the wolves", "forty");
        Assert.Equal(gold + 40, s.Ch.Gold);
        Assert.Contains("dig_sold", s.World.Quests["beasts"].Entries);
        for (int d = 0; d < 5; d++) Day(s, 0.99);
        Assert.Equal("moved", s.World.Fact("dig.pump").Str);
        Assert.Equal("exploited", s.World.Fact("beasts.outcome").Str);
        Assert.Equal(QuestStatus.Resolved, s.World.Quests["beasts"].Status);
        Assert.Equal("Settled, for a price", Chapter.Summary(s.Ch, s.World).Threads[0].Verdict);
    }

    [Fact]
    public void The_Wardens_lore_gets_a_probationary_knight_talking()
    {
        var s = Q("scholar");
        Talk(Convo("keegan"), s.C, "bye");
        s.Ch.Knowledge.Add("lore.warden");
        var p = Talk(Convo("keegan"), s.C, "ford-warden");
        Assert.Matches("keep the Warden asleep", p!.Text);
    }

    [Fact]
    public void Choices_that_no_longer_apply_go()
    {
        var s = Q("hunter");
        List<string> Offered(string id) => new DialogueRunner(Convo(id), s.C).Start()!.Choices.Select(x => x.Text).ToList();
        s.World.Npc("vonnra").Flags["met"] = true;
        Assert.Contains(Offered("vonnra"), t => Regex.IsMatch(t, "pay the toll", RegexOptions.IgnoreCase));
        s.World.Facts["toll.paid"] = true;
        Assert.DoesNotContain(Offered("vonnra"), t => Regex.IsMatch(t, "pay the toll", RegexOptions.IgnoreCase));

        var w = Q("hunter");
        w.Ch.Knowledge.Add("clue.analysis");
        var r = new DialogueRunner(Convo("wenna"), w.C);
        var p = r.Start();
        while (p != null && p.Choices.Count == 0) p = r.Advance();
        Assert.DoesNotContain(p!.Choices, x => Regex.IsMatch(x.Text, "water from the stream", RegexOptions.IgnoreCase));
    }
}

public class ObjectiveTests
{
    static Setup O()
    {
        var s = Make("hunter", "Wren", 5);
        s.World.Facts["prologue.done"] = true;
        return s;
    }

    static List<string> Steps(Ctx c, string id) => Objectives.Of(c).Find(o => o.Id == id)?.Steps.Select(s => s.Text).ToList() ?? new();

    [Fact]
    public void Point_a_newcomer_at_the_inn_then_at_whoever_the_talk_was_about()
    {
        var s = O();
        Assert.Matches("Rook", Steps(s.C, "arrival")[0]);
        Rules.Apply(Es("[{ quest: { id: 'beasts', entry: 'rumour' } }, { quest: { id: 'caravan', entry: 'harlan_plea' } }]"), s.C);
        Assert.Empty(Steps(s.C, "arrival"));
        Assert.Contains(Steps(s.C, "beasts"), t => t.Contains("Holloway, on the square"));
        Assert.Contains(Steps(s.C, "caravan"), t => t.Contains("Harlan Coyle, outside Coyle Trading"));
    }

    [Fact]
    public void Follow_the_Beast_Problem_whichever_way_it_is_walked()
    {
        var s = O();
        Rules.Apply(E("{ quest: { id: 'beasts', status: 'active', entry: 'holloway_bounty' } }"), s.C);
        Assert.Matches("what is wrong with the wolves", Steps(s.C, "beasts")[0]);
        Rules.Apply(Es("[{ learn: ['clue.pipe', 'clue.lampling_tracks'] }, { give: 'slurry_sample' }]"), s.C);
        Assert.Matches("Fill a bottle at the green water", Steps(s.C, "beasts")[0]);
        Inventory.AddToPack(s.Ch, Inventory.Make(s.Ch, "stream_sample"));
        Assert.Matches("to Wenna", Steps(s.C, "beasts")[0]);
        Rules.Apply(Es("[{ take: 'stream_sample' }, { learn: ['clue.analysis', 'root_cause'] }]"), s.C);
        Assert.Matches("Stop the slurry at the Dig", Steps(s.C, "beasts")[0]);
        Rules.Apply(E("{ set: { 'dig.pump': 'broken' } }"), s.C);
        Assert.Matches("a few days to run clear", Steps(s.C, "beasts")[0]);
    }

    [Fact]
    public void Say_how_long_the_cages_will_hold_and_follow_the_caravan_to_its_end()
    {
        var s = O();
        Rules.Apply(E("{ quest: { id: 'caravan', status: 'active', entry: 'harlan_plea' } }"), s.C);
        Assert.Matches("Search the Old Road", Steps(s.C, "caravan")[0]);
        Rules.Apply(E("{ quest: { id: 'caravan', entry: 'wreck' } }"), s.C);
        Assert.Matches("wheel ruts", Steps(s.C, "caravan")[0]);
        s.World.Facts["caravan.days"] = 3;
        Rules.Apply(E("{ quest: { id: 'caravan', entry: 'roost_found' } }"), s.C);
        Assert.Matches("cages.*not last another night", Steps(s.C, "caravan")[0]);
        Rules.Apply(E("{ set: { 'caravan.survivors': 'rescued' } }"), s.C);
        Assert.Contains(Steps(s.C, "caravan"), t => t.Contains("Tell Harlan"));
        Assert.Contains(Steps(s.C, "caravan"), t => t.Contains("strongbox is still in the Roost"));
        Rules.Apply(Es("[{ set: { 'caravan.cargo': 'returned' } }, { quest: { id: 'caravan', status: 'resolved' } }]"), s.C);
        Assert.DoesNotContain(Objectives.Of(s.C), o => o.Id == "caravan");
    }
}
