using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Act 1 played end to end, every road the writing pass names
/// (docs/WRITING_PASS.md sections 4 to 6 and 12) and the wrong turns
/// between them: through the game's own conversations, the Waystation, the
/// Verge and the nights, with a save and a load at the turns that matter,
/// asserting what opens, what stays shut, what the journal says and where
/// each road ends.</summary>
public class RouteTests
{
    static void Same(Route p, Action<Route> check)
    {
        // A save in the middle of a questline loses nothing: the same state, the same next step.
        string before = p.Snapshot();
        var steps = Objectives.Of(p.C).Select(o => string.Join("|", o.Steps.Select(s => s.Text))).ToList();
        p.SaveAndLoad();
        Assert.Equal(before, p.Loaded);
        Assert.Equal(steps, Objectives.Of(p.C).Select(o => string.Join("|", o.Steps.Select(s => s.Text))).ToList());
        check(p);
    }

    /* ------------------------------------------------- The Beast Problem -- */

    [Fact]
    public void B1_in_order_the_scholar_reads_the_water_and_talks_the_pump_into_the_sinkhole()
    {
        var p = Route.New("scholar");
        Assert.Matches("Mother Rook", p.Steps("arrival")[0]);
        p.Talk("rook", "talk");
        Assert.Equal(["rumour"], p.Journal("beasts"));
        Assert.Matches("Find out what is wrong with the wolves", p.Steps("beasts")[0]);
        p.Talk("holloway", "wolves");
        p.Talk("maeca", "driving them out");
        p.Talk("tam", "listening");
        Assert.True(p.Knows("hint.stream"));
        Assert.Matches("Fill a bottle at the green water", p.Steps("beasts")[0]);
        // Out of the east gate, five gold to Vonnra's toll.
        p.Enter("waystation");
        double gold = p.J.Ch.Gold;
        p.Use("gate:east");
        Assert.Equal(gold - 5, p.J.Ch.Gold);
        Assert.Equal("verge", p.Host!.Travelled?.Zone);
        p.Enter("verge");
        Assert.Equal(MarkKind.Quest, p.Map().Single(m => m.Label == "The green water").Kind);
        p.Use("sample");
        Assert.Matches("Take the bottle of green water to Wenna", p.Steps("beasts")[0]);
        p.Use("pipe");
        Assert.True(p.Knows("clue.pipe"));
        Assert.False(p.Knows("root_cause"));
        Same(p, q => Assert.Matches("Take the bottle of green water to Wenna", q.Steps("beasts")[0]));
        p.Leave();
        Assert.Equal("!", p.Marker("wenna"));
        var said = p.Talk("wenna", "water from the stream").Last!.Text;
        Assert.Contains("From a pipe?", said);
        Assert.True(p.Knows("root_cause"));
        Assert.Matches("Stop the slurry at the Dig", p.Steps("beasts")[0]);
        Assert.Equal("?", p.Marker("maeca"));
        p.Talk("maeca", "ember slurry");
        Assert.Null(p.Marker("maeca"));
        // At the Dig, Snib is offered, and the sinkhole with him.
        p.Enter("verge");
        p.Walk("pump");
        Assert.True(p.CanUse("snib"));
        Assert.Contains(p.Offered("snib"), t => t.Contains("sinkhole"));
        p.Talk("snib", "sinkhole");
        Assert.Equal("moved", p.S("dig.pump"));
        Assert.Matches("slurry has stopped", p.Steps("beasts")[0]);
        p.Leave();
        Assert.Contains("running clear", p.Sleeps(2));
        Assert.Equal("cured", p.S("beasts.outcome"));
        Assert.Equal(QuestStatus.Resolved, p.Status("beasts"));
        Assert.Equal(["rumour", "holloway_bounty", "maeca_theory", "tam_plea", "clue.green_stream", "sample", "clue.pipe", "clue.lampling_tracks", "clue.analysis", "root_cause", "pump_moved"], p.Journal("beasts"));
        Assert.DoesNotContain(Objectives.Of(p.C), o => o.Id == "beasts");
        // The town hears it.
        Assert.Contains("Pa says you did it", p.Greet("tam").Said);
        Assert.Contains("WITHDRAWN", p.Greet("board").Said);
        Same(p, q => Assert.Equal("cured", q.S("beasts.outcome")));
    }

    [Fact]
    public void B2_the_Dig_first_then_a_sick_wolf_gives_a_reason_to_ask_and_Pell_a_charge_the_same_day()
    {
        var p = Route.New("hunter").Enter("verge");
        p.Walk("pump");
        Assert.True(p.CanUse("snib"));
        Assert.Equal(["What are you pumping?", "Leave."], p.Offered("snib"));
        p.Talk("snib", "what are you pumping");
        Assert.Equal(QuestStatus.Active, p.Status("beasts"));
        Assert.Equal(["snib_slurry"], p.Journal("beasts"));
        Assert.True(p.Knows("clue.pipe"));
        Assert.False(p.Knows("root_cause"));
        Assert.Matches("Fill a bottle at the green water", p.Steps("beasts")[0]);
        // The dead wolf by the road: a reason to care about the water.
        p.Use("carcass");
        var asks = p.Offered("snib");
        Assert.Contains(asks, t => t.Contains("poisoning the stream"));
        Assert.DoesNotContain(asks, t => t.Contains("sinkhole"));
        p.Talk("snib", "poisoning the stream", "leave");
        Assert.True(p.Knows("root_cause"));
        Assert.True(p.Has("below", "grimtunnel"));
        p.Leave();
        // Pell has blasting ember on his shelf for someone who knows the Dig, the same day.
        var shelf = p.J.OpenShop("pell", new Random(3))!;
        var ember = shelf.Stock.Single(i => i.Def == "blasting_ember");
        p.J.Buy("pell", ember.Uid);
        Assert.Equal(1, p.Count("blasting_ember"));
        Same(p, q => Assert.Equal(1, q.Count("blasting_ember")));
        // Set at the pump, and run.
        p.Enter("verge");
        p.Walk("pump", 12, 0);
        Assert.True(p.CanUse("charge"));
        p.Use("charge");
        p.Wait(4);
        Assert.Equal("blown", p.S("dig.pump"));
        Assert.True(p.Has("beasts", "pump_blown"));
        Assert.True(p.F("dig.hostile").Truthy);
        Assert.Equal(0, p.Count("blasting_ember"));
        p.Leave();
        Assert.Contains("lamplings were carrying their own", p.Sleeps(2));
        Assert.Equal("cured", p.S("beasts.outcome"));
    }

    [Fact]
    public void B6_Redcowls_charge_blows_the_pump_and_takes_the_crates_off_Harlans_books()
    {
        var p = Route.New("outcast").Enter("verge");
        p.Use("wreck");
        Assert.True(p.Has("caravan", "manifest"));
        p.Leave();
        Assert.Contains(p.Steps("caravan"), t => t.Contains("Harlan Coyle, outside Coyle Trading"));
        p.Talk("harlan", "besides salt and cloth");
        Assert.True(p.Knows("clue.blasting_ember"));
        p.Enter("verge");
        p.Walk("roost");
        Assert.True(p.CanUse("redcowl"));
        p.Talk("redcowl", "six crates", "blasting ember", "deep enough", "give me one");
        Assert.Equal("redcowl", p.S("be.crates"));
        Assert.True(p.Has("beasts", "redcowl_charge"));
        Assert.Equal(QuestStatus.Active, p.Status("beasts"));
        // Harlan's crates are spoken for, and the empty-camp choices never open.
        Assert.False(p.Offers("crates_charge"));
        Assert.False(p.Offers("crates_sink"));
        Same(p, q => Assert.Equal(1, q.Count("blasting_ember")));
        p.Walk("pump", 12, 0);
        p.Use("charge");
        p.Wait(4);
        Assert.Equal("blown", p.S("dig.pump"));
        p.Leave();
        Assert.DoesNotContain(p.Offered("harlan"), t => t.Contains("six crates"));
        p.Sleeps(2);
        Assert.Equal("cured", p.S("beasts.outcome"));
        Assert.Contains(Lore.EntryText("beasts", "redcowl_charge"), Chapter.Summary(p.J.Ch, p.W).Threads[0].Beats);
    }

    [Fact]
    public void B7_the_cure_sold_to_Pell_clears_the_water_on_his_terms()
    {
        var p = Route.New("scholar");
        p.Give("stream_sample");
        p.Talk("wenna", "test it");
        Assert.True(p.Knows("root_cause"));
        p.Talk("pell", "killing the wolves", "forty");
        Assert.True(p.Has("beasts", "dig_sold"));
        Assert.Matches("Pell Varrow says to give it two days", p.Steps("beasts")[0]);
        Same(p, q => Assert.True(q.F("dig.sold").Truthy));
        p.Sleeps(2);
        Assert.Equal("moved", p.S("dig.pump"));
        Assert.True(p.F("dig.pell_cut").Truthy);
        Assert.Contains("whistling", p.Sleeps(2));
        Assert.Equal("exploited", p.S("beasts.outcome"));
        Assert.Equal("Wren, who sold the cure", Chapter.Summary(p.J.Ch, p.W).Epithet);
    }

    [Fact]
    public void B5_the_hunter_kneels_to_Greymuzzle_and_the_Pack_runs_with_whoever_knows_the_Roost()
    {
        var p = Route.New("hunter");
        p.Talk("rav", "about the kerchiefs");
        p.Enter("verge");
        p.Walk("hollow", 10, 0);
        Assert.True(p.CanUse("greymuzzle"));
        p.Talk("greymuzzle", "kneel", "run with me", "go");
        Assert.Equal("allied", p.S("beasts.outcome"));
        Assert.Equal(QuestStatus.Resolved, p.Status("beasts"));
        Same(p, q => Assert.True(q.F("pack.allied").Truthy));
        p.Leave();
        p.Enter("verge");
        Assert.Equal(4, p.B!.Enemies.Living().Count(e => e.Tag == "packmate"));
        p.Leave();
        Assert.Equal("Wren, who runs with wolves", Chapter.Summary(p.J.Ch, p.W).Epithet);
    }

    [Fact]
    public void B8_left_alone_the_wolves_come_to_the_gate_and_the_town_buries_its_own()
    {
        var p = Route.New("devout");
        p.Talk("rook", "talk");
        var morning = p.Sleeps(7);
        Assert.Contains("Aldo off the wall", morning);
        Assert.Equal("ignored", p.S("beasts.outcome"));
        Assert.Equal(QuestStatus.Failed, p.Status("beasts"));
        Assert.Contains("buried Aldo", p.Sleeps(1));
        Assert.Contains("CURFEW", p.Greet("board").Said);
    }

    [Fact]
    public void A_hunt_that_empties_the_wood_settles_it_by_slaughter()
    {
        var p = Route.New("hunter");
        p.Talk("holloway", "wolves");
        p.W.Facts["beasts.population"] = 8;
        p.Enter("verge");
        p.Kill(e => e.Def.Family == Sim.Family.Wolf);
        Assert.True(p.F("beasts.population").Number <= 5);
        p.Leave();
        Assert.Contains("No howling last night", p.Sleeps(1));
        Assert.Equal("slaughtered", p.S("beasts.outcome"));
        Assert.Contains("BOUNTY CLOSED", p.Greet("board").Said);
    }

    /* ----------------------------------------------- The Missing Caravan -- */

    [Fact]
    public void K1_in_order_the_wagons_the_ruts_the_Roost_bought_the_cages_and_the_box_home()
    {
        var p = Route.New("outcast");
        p.Talk("harlan", "goodbye");
        Assert.Contains("harlan_plea", p.Journal("caravan"));
        Assert.Matches("Search the Old Road", p.Steps("caravan")[0]);
        p.Enter("verge");
        Assert.Equal(MarkKind.Quest, p.Map().Single(m => m.Label == "Coyle Wagons").Kind);
        p.Use("wreck");
        Assert.Matches("wheel ruts", p.Steps("caravan")[0]);
        Assert.Contains(p.Map(), m => m.Label == "Wheel ruts" && m.Kind == MarkKind.Quest);
        p.Use("ruts");
        Assert.Matches("Kerchief camp in the ravine", p.Steps("caravan")[0]);
        p.Walk("roost");
        Assert.True(p.Has("caravan", "roost_found"));
        Assert.Matches("Free the prisoners", p.Steps("caravan")[0]);
        p.Talk("redcowl", "coyle wagons", "hundred");
        Same(p, q => Assert.Equal("bargained", q.S("redcowl")));
        p.Walk("cages");
        for (int k = 0; k < 3; k++) p.Use($"cage{k}");
        Assert.Equal("rescued", p.S("caravan.survivors"));
        Assert.Contains("Tell Harlan Coyle that Jory is alive", p.Steps("caravan"));
        Assert.Contains("The Coyle strongbox is still in the Roost, with the rest of the cargo", p.Steps("caravan"));
        p.Use("strongbox");
        Assert.False(p.F("roost.hostile").Truthy);
        Assert.Contains("Take the Coyle strongbox to Harlan Coyle, at Coyle Trading in the Waystation, or keep it", p.Steps("caravan"));
        Same(p, q => Assert.Equal(1, q.Count("coyle_strongbox")));
        p.Leave();
        Assert.Equal("?", p.Marker("harlan"));
        double gold = p.J.Ch.Gold;
        p.Talk("harlan", "jory's alive", "something else", "strongbox");
        Assert.Equal(gold + 200, p.J.Ch.Gold);
        Assert.Equal(QuestStatus.Resolved, p.Status("caravan"));
        Assert.Equal("returned", p.W.Quests["caravan"].Outcome);
        Assert.Null(p.Marker("harlan"));
        Assert.Equal("Brought home", Chapter.Summary(p.J.Ch, p.W).Threads[1].Verdict);
        Assert.DoesNotContain(Objectives.Of(p.C), o => o.Id == "caravan");
        // Jory is in town, and asks what he was carrying.
        Assert.Contains(p.Offered("jory"), t => t.Contains("What was in the crates"));
    }

    [Fact]
    public void K2_the_Roost_found_first_is_news_to_carry_to_Harlan()
    {
        var p = Route.New("outcast").Enter("verge");
        p.Walk("roost");
        Assert.Equal(QuestStatus.Active, p.Status("caravan"));
        Assert.Equal(["roost_found"], p.Journal("caravan"));
        Assert.Contains("Coyle", Lore.EntryText("caravan", "roost_found"));
        p.Leave();
        Assert.Equal("!", p.Marker("harlan"));
        Assert.Contains("Verge on your boots", p.Greet("harlan").Said);
        p.Talk("harlan", "seen your wagons");
        Assert.True(p.Has("caravan", "roost_told"));
        Assert.Contains(Lore.EntryText("caravan", "roost_told"), Chapter.Summary(p.J.Ch, p.W).Threads[1].Beats);
    }

    [Fact]
    public void K3_and_K10_the_cages_first_by_a_bluff_and_the_box_sold_to_Ravs_friend()
    {
        var p = Route.New("outcast").Enter("verge");
        p.Walk("roost");
        p.Talk("redcowl", "watch is on its way");
        Assert.Equal("tricked", p.S("redcowl"));
        p.Walk("cages");
        for (int k = 0; k < 3; k++) p.Use($"cage{k}");
        p.Use("strongbox");
        p.Leave();
        // Harlan, never met, hears it as news.
        var (said, _) = p.Greet("harlan");
        Assert.Contains("bar in your hands", said);
        Assert.False(p.Has("caravan", "harlan_plea"));
        p.Talk("harlan", "jory's alive");
        // Rav's friend, quietly.
        p.Talk("rav", "buy this, quietly", "sell it");
        Assert.Equal("sold", p.S("caravan.cargo"));
        Assert.True(p.F("player.wanted").Truthy);
        Assert.Equal(QuestStatus.Resolved, p.Status("caravan"));
        Same(p, q => Assert.True(q.F("player.wanted").Truthy));
        Assert.Contains("WANTED: a traveller", p.Greet("board").Said);
        p.Talk("holloway", "pay the hundred");
        Assert.True(p.F("player.fined").Truthy);
        Assert.Equal("Rescued, and robbed", Chapter.Summary(p.J.Ch, p.W).Threads[1].Verdict);
        Assert.Equal("Wren, who sold the Coyle strongbox", Chapter.Summary(p.J.Ch, p.W).Epithet);
        // A bluffed Roost is an empty one: the crates could be had by someone who knew.
        Assert.Contains("You bluffed the Kerchiefs out of their own camp.", Chapter.Summary(p.J.Ch, p.W).Threads[1].Beats);
    }

    [Fact]
    public void K5_the_ledger_burgled_on_the_first_night_starts_the_caravan_and_exposes_Pell_once_it_proves_something()
    {
        var p = Route.New("outcast");
        p.Night();
        p.Enter("waystation");
        Assert.True(p.CanUse("warehouse"));
        p.Use("warehouse");
        Assert.Equal(1, p.Count("pell_ledger"));
        Assert.Equal(QuestStatus.Active, p.Status("caravan"));
        Assert.Equal(["pell_ledger"], p.Journal("caravan"));
        Assert.False(p.Offers("warehouse"));
        Same(p, q => Assert.Contains(q.Steps("caravan"), t => t.StartsWith("Someone who knows the dates")));
        p.Leave();
        p.Sleep();
        // Pell, faced by a thief who does not know what he stole, is relieved.
        Assert.Contains("don't know what you're holding", p.Talk("pell", "read your ledger").Last!.Text);
        p.Talk("holloway", "found this book");
        Assert.True(p.Has("caravan", "ledger_read"));
        Assert.DoesNotContain(p.Offered("holloway"), t => t.Contains("Here's his ledger"));
        p.Enter("verge");
        Assert.Equal(MarkKind.Quest, p.Map().Single(m => m.Label == "Coyle Wagons").Kind);
        p.Use("wreck");
        p.Leave();
        Assert.Equal("?", p.Marker("holloway"));
        p.Talk("holloway", "his ledger");
        Assert.Equal("exposed", p.S("caravan.pell"));
        Assert.Equal(0, p.Count("pell_ledger"));
        Assert.Contains("sealed pending inquiry", p.Greet("board").Said);
        // Pell is not about the square any more.
        p.Enter("waystation");
        p.Wait(1);
        Assert.True(p.Zone!.Actors["pell"].Hidden);
    }

    [Fact]
    public void K12_who_tells_Redcowl_where_Pell_sleeps()
    {
        var p = Route.New("outcast");
        p.Night();
        p.Enter("waystation");
        p.Use("warehouse");
        p.Enter("verge");
        p.Walk("roost");
        p.Talk("redcowl", "sold you out", "in the loft");
        Assert.Equal(0, p.Count("pell_ledger"));
        Assert.Equal("taken", p.S("pell.fate"));
        p.Leave();
        Assert.Contains("red thread", p.Sleeps(1));
        Assert.Contains("in a cage that was built for someone else", FortuneOf(p));
        var beats = Chapter.Summary(p.J.Ch, p.W).Threads[1].Beats;
        Assert.Contains(Lore.EntryText("caravan", "pell_given"), beats);
        Assert.DoesNotContain("Pell Varrow fled the Waystation in the night.", beats);
    }

    static string FortuneOf(Route p)
    {
        p.W.Facts["chapter.ready"] = true;
        return p.Fortune().Read;
    }

    [Fact]
    public void K16_left_too_long_the_cages_are_too_late_and_the_box_is_all_that_comes_home()
    {
        var p = Route.New("hunter");
        p.Talk("harlan", "goodbye");
        var heard = p.Sleeps(4);
        Assert.Contains("stopped feeding their prisoners", heard);
        Assert.Equal("dead", p.S("caravan.survivors"));
        Assert.Contains("I heard. I heard.", p.Greet("harlan").Said);
        p.Enter("verge");
        for (int k = 0; k < 3; k++) Assert.False(p.Offers($"cage{k}"));
        p.W.Facts["redcowl"] = "tricked";
        p.Use("strongbox");
        p.Leave();
        p.Talk("harlan", "strongbox");
        Assert.Equal(QuestStatus.Resolved, p.Status("caravan"));
        Assert.Equal("The goods, not the men", Chapter.Summary(p.J.Ch, p.W).Threads[1].Verdict);
    }

    [Fact]
    public void A_strongbox_carried_three_days_is_kept_and_Harlan_still_pays_for_the_boy()
    {
        var p = Route.New("outcast").Enter("verge");
        p.Walk("roost");
        p.Talk("redcowl", "watch is on its way");
        p.Walk("cages");
        for (int k = 0; k < 3; k++) p.Use($"cage{k}");
        p.Use("strongbox");
        p.Leave();
        Assert.Contains("written the strongbox off", p.Sleeps(3));
        Assert.Equal("kept", p.S("caravan.cargo"));
        Assert.Equal(QuestStatus.Resolved, p.Status("caravan"));
        // The boy is still paid for, once.
        Assert.NotNull(p.Marker("harlan"));
        double gold = p.J.Ch.Gold;
        p.Talk("harlan", "take it");
        Assert.Equal(gold + 100, p.J.Ch.Gold);
        Assert.Null(p.Marker("harlan"));
        // The box is Rav's business now, not Harlan's, nor a counter's.
        Assert.Null(p.J.PriceOf("vonnra", p.J.Ch.Pack.First(i => i?.Def == "coyle_strongbox")!.Uid, false));
        p.Talk("rav", "buy this, quietly", "sell it");
        Assert.Equal("sold", p.S("caravan.cargo"));
    }

    /* ------------------------------------------------- the night's fights -- */

    [Fact]
    public void The_Roost_raided_by_night_leaves_an_empty_camp_the_cages_and_the_crates()
    {
        var p = Route.New("hunter");
        p.Talk("harlan", "goodbye");
        p.Talk("rav", "about the kerchiefs");
        p.Learn("clue.blasting_ember");
        p.Night();
        p.Enter("verge");
        Assert.True(p.CanUse("night:roost"));
        var spec = p.StoryFight("roost", won: true);
        Assert.Equal("dead", p.S("redcowl"));
        Assert.True(p.F("roost.cleared").Truthy);
        Assert.True(p.Has("caravan", "roost_raided"));
        Assert.False(p.Offers("night:roost"));
        // Nobody left to watch: the cages, the box and the crates are the survivor's to see to.
        p.Walk("cages");
        for (int k = 0; k < 3; k++) Assert.True(p.CanUse($"cage{k}"), p.Refusal($"cage{k}"));
        Assert.True(p.CanUse("crates_charge"));
        Assert.True(p.CanUse("crates_sink"));
        Same(p, q => Assert.True(q.CanUse("cage0")));
        for (int k = 0; k < 3; k++) p.Use($"cage{k}");
        p.Use("crates_sink");
        p.Leave();
        Assert.Equal("sunk", p.S("be.crates"));
        // Rav says his brother's name, the once.
        Assert.Contains("Dunstan", p.Greet("rav").Said);
        Assert.DoesNotContain("Dunstan", p.Greet("rav").Said);
        p.W.Facts["chapter.done"] = true;
        p.Sleep();
        Assert.Equal("sunk", p.S("be.crates"));
    }

    [Fact]
    public void The_Dig_turned_against_you_boils_over_by_night_and_the_pump_dies_with_it()
    {
        var p = Route.New("outcast");
        p.Learn("clue.green_stream");
        p.Talk("snib", "shut it off myself");
        Assert.True(p.F("dig.hostile").Truthy);
        p.Enter("verge");
        Assert.NotNull(p.Refusal("night:dig"));
        p.Night();
        p.Enter("verge");
        p.StoryFight("dig", won: true);
        Assert.Equal("blown", p.S("dig.pump"));
        Assert.True(p.Has("beasts", "dig_overrun"));
        Assert.True(p.Has("beasts", "pump_blown"));
        Assert.False(p.Offers("night:dig"));
        p.Leave();
        p.Sleeps(2);
        Assert.Equal("cured", p.S("beasts.outcome"));
    }

    [Fact]
    public void The_Pack_hunted_in_its_own_Hollow_is_remembered_by_everyone_who_cared()
    {
        var p = Route.New("scholar");
        p.Talk("maeca", "goodbye");
        p.Talk("holloway", "wolves");
        p.Night();
        p.Enter("verge");
        Assert.True(p.CanUse("night:hollow"));
        p.StoryFight("hollow", won: true);
        Assert.Equal("dead", p.S("greymuzzle"));
        Assert.True(p.Has("beasts", "alpha_dead"));
        Assert.Equal(1, p.Count("greymuzzle_fang"));
        p.Leave();
        Assert.Contains("Get out of my light", p.Greet("maeca").Said);
        Assert.Equal("?", p.Marker("holloway"));
        double gold = p.J.Ch.Gold;
        p.Talk("holloway", "bounty", "hand over the fang");
        Assert.Equal(gold + 50, p.J.Ch.Gold);
        Assert.Null(p.Marker("holloway"));
    }

    [Fact]
    public void The_sealed_door_opens_by_night_for_whoever_carries_the_sigils_fragment()
    {
        var p = Route.New("devout").Enter("verge");
        p.Use("vaultbody");
        Assert.True(p.Has("vault", "fragment"));
        Assert.NotNull(p.Refusal("night:vault"));
        // The fragment cannot be dropped while the door waits for it.
        var frag = p.J.Ch.Pack.First(i => i?.Def == "sigil_fragment")!;
        p.J.Drop(frag.Uid);
        Assert.Equal(1, p.Count("sigil_fragment"));
        p.Night();
        p.Enter("verge");
        p.StoryFight("vault", won: true);
        Assert.True(p.F("vault.opened").Truthy);
        Assert.True(p.Has("vault", "opened"));
        // Its part played, it is a keepsake: it can be left behind now.
        p.J.Drop(frag.Uid);
        Assert.Equal(0, p.Count("sigil_fragment"));
    }

    /* ---------------------------------------------- The Lamps at the Low Ford -- */

    [Fact]
    public void L_every_piece_of_the_lamps_and_the_accusation_at_the_fortune()
    {
        var p = Route.New("hunter");
        Assert.Equal(["book"], p.Journal("lamps"));
        p.Talk("holloway", "watch-post", "lit again");
        p.Talk("keegan", "ford-warden");
        p.Talk("brannoc", "lamp-irons");
        p.Talk("rook", "low ford road", "what did she say");
        p.Talk("vonnra", "goodbye");
        p.Talk("vonnra", "coin on the cord");
        p.Greet("board");
        Assert.Equal(["book", "post", "keegan", "irons", "rook", "coin", "notice"], p.Journal("lamps"));
        Same(p, q => Assert.Equal(7, q.Journal("lamps").Count));
        // Brannoc asks after Nell from the second day, by day.
        p.Sleep();
        p.Talk("brannoc", "wagon on its side", "put her down", "quick");
        Assert.True(p.Has("lamps", "nell"));
        Assert.Contains("Brannoc banked his forge", p.Sleeps(1));
        // Both stories settled: the fortune, and the lamps said to her face.
        p.W.Facts["beasts.outcome"] = "cured";
        p.W.Facts["caravan.survivors"] = "rescued";
        p.Sleep();
        Assert.True(p.F("chapter.ready").Truthy);
        Assert.Equal("?", p.Marker("vonnra"));
        var (read, choices, r, last) = p.Fortune();
        Assert.Contains(choices, c => c.Contains("You lit the lamps"));
        r.Choose(last.Choices.First(c => c.Text.Contains("You lit the lamps")).Index);
        var door = r.Advance()!;
        Assert.Contains("Wren", door.Text);
        Assert.Equal("fortune", r.Choose(door.Choices[0].Index).Action);
        Assert.True(p.F("chapter.done").Truthy);
        Assert.Equal("accused", p.Journal("lamps")[^1]);
        Assert.Null(p.Marker("vonnra"));
        Same(p, q => Assert.True(q.F("vonnra.accused").Truthy));
        var sum = Chapter.Summary(p.J.Ch, p.W);
        Assert.Equal("Wren, who said it to Vonnra's face", sum.Epithet);
        Assert.Equal(Lore.EntryText("lamps", "accused"), sum.Open.Single(o => o.Id == "lamps").Line);
    }

    /* -------------------------------------------------- the whole chapter -- */

    [Fact]
    public void The_chapter_from_the_gate_to_the_fortune_with_a_save_at_every_turn()
    {
        var p = Route.New("outcast");
        p.Talk("rook", "talk");
        p.Talk("harlan", "goodbye");
        p.Talk("tam", "listening");
        p.Enter("verge");
        p.Use("wreck");
        p.Use("carcass");
        p.Use("sample");
        Same(p, _ => { });
        p.Walk("roost");
        p.Talk("redcowl", "coyle wagons", "hundred");
        p.Walk("cages");
        for (int k = 0; k < 3; k++) p.Use($"cage{k}");
        p.Use("strongbox");
        Same(p, _ => { });
        p.Leave();
        p.Talk("harlan", "jory's alive", "something else", "strongbox");
        p.Talk("wenna", "water from the stream");
        Assert.False(p.Knows("root_cause"));
        Assert.Matches("Follow the stream up", p.Steps("beasts")[0]);
        p.Enter("verge");
        p.Walk("pump");
        p.Talk("snib", "poisoning the stream", "how much", "forty gold");
        Assert.Equal("moved", p.S("dig.pump"));
        Same(p, _ => { });
        p.Leave();
        var morning = p.Sleeps(3);
        Assert.Contains("violet ink", morning);
        Assert.NotNull(p.Marker("vonnra"));
        Assert.Equal(["Vonnra has sent for you, to read your fortune: the Toll Tower, by the east gate"], p.Steps("fortune"));
        var (read, choices, r, last) = p.Fortune();
        Assert.Contains("water running clear", read);
        Assert.Contains("boy asleep in a wagon", read);
        Assert.DoesNotContain(choices, c => c.Contains("You lit the lamps"));
        var door = r.Choose(last.Choices.First(c => c.Text.Contains("door")).Index).Next!;
        Assert.Equal("fortune", r.Choose(door.Choices[0].Index).Action);
        Assert.Empty(p.Steps("fortune"));
        var sum = Chapter.Summary(p.J.Ch, p.W);
        Assert.Equal(["Cured at the source", "Brought home"], sum.Threads.Select(t => t.Verdict));
        Assert.Equal("Wren, who cleared the water and opened the cages", sum.Epithet);
        Assert.Equal(["vault", "below", "lamps"], sum.Open.Select(o => o.Id));
        // At the chapter's end the crates nobody stopped go to the Dig.
        p.Sleep();
        Assert.Equal("dig", p.S("be.crates"));
    }

    /* ---------------------------------------- what is given, not bought -- */

    [Fact]
    public void Wenna_gives_her_mask_to_the_scholar_who_cleaned_her_stream()
    {
        // B1's road, played to the end; then the mask, earned by the cure alone
        // (WRITING_PASS section 16; the explorer's search rarely gets this deep).
        var p = Route.New("scholar");
        p.Talk("rook", "talk");
        p.Talk("holloway", "wolves");
        p.Talk("maeca", "driving them out");
        p.Talk("tam", "listening");
        p.Enter("verge");
        p.Use("sample");
        p.Use("pipe");
        p.Leave();
        p.Talk("wenna", "water from the stream");
        p.Enter("verge");
        p.Walk("pump");
        p.Talk("snib", "sinkhole");
        p.Leave();
        p.Sleeps(2);
        Assert.Equal("cured", p.S("beasts.outcome"));
        Assert.True(p.W.Npc("wenna").Affection < 20);
        Assert.Contains("You cleaned my stream", p.Talk("wenna", "beaked mask").Last!.Text);
        Assert.Equal(1, p.Count("blightward_mask"));
    }

    [Fact]
    public void Keegan_sups_with_whoever_read_the_watchmans_book_and_found_Ashe()
    {
        // The road to Keegan's supper (WRITING_PASS section 16), every step played:
        // the dead watchman's book (read in the prologue), Ashe's trunk in the
        // Quiet Garden and Rook asked about it, both told to Keegan, the dinner
        // she refuses, and back after dark.
        var p = Route.New("scholar");
        p.Enter("waystation");
        p.Use("garden");
        p.Leave();
        p.Talk("rook", "grave in the garden");
        Assert.True(p.Knows("lore.ashe"));
        p.Talk("keegan", "Ford-Warden");
        p.Talk("keegan", "Captain Ashe");
        p.Talk("keegan", "dinner");
        Assert.DoesNotContain(p.Offered("keegan"), c => c.Contains("Have you eaten"));
        p.Night();
        p.Talk("keegan", "Have you eaten");
        Assert.True(p.F("keegan.supper").Truthy);
    }
}
