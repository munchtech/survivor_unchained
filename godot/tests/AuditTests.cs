using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>What the Act 1 audit found, each proved fixed by playing into it
/// (docs/WRITING_PASS.md section 15): a reward that could be taken twice, a
/// choice offered after it stopped making sense, a mark over someone's head
/// with nothing behind it, a journal line written into a story already
/// over, a thing the world forgot when the game was saved.</summary>
public class AuditTests
{
    /* ------------------------------------------------- the same thing twice -- */

    [Fact]
    public void Redcowl_keeps_Pells_book_so_where_Pell_sleeps_is_told_once()
    {
        var p = Route.New("outcast");
        p.Give("pell_ledger");
        p.Talk("redcowl", "sold you out", "in the loft");
        Assert.Equal("taken", p.S("pell.fate"));
        Assert.Equal(0, p.Count("pell_ledger"));
        // Not again, and not the other way: he has the book.
        Assert.DoesNotContain(p.Offered("redcowl"), t => t.Contains("sold you out"));
        Assert.True(p.Has("caravan", "pell_given"));
        Assert.False(p.Has("caravan", "pell_hunted"));
        // And Holloway is never shown a book that would put a man in irons who is already gone.
        p.Apply("""[{ "quest": { "id": "caravan", "entry": "wreck" } }, { "quest": { "id": "caravan", "entry": "harlan_plea" } }]""");
        Assert.DoesNotContain(p.Offered("holloway"), t => t.Contains("Here's his ledger") || t.Contains("found this book"));
        Assert.NotEqual("?", p.Marker("holloway"));
    }

    [Fact]
    public void Redcowls_hundred_buys_the_teamsters_as_he_says_and_their_keep_is_paid_once()
    {
        var p = Route.New("outcast").Enter("verge");
        p.Walk("roost");
        Assert.True(p.CanUse("redcowl"));
        p.Talk("redcowl", "coyle wagons", "hundred");
        Assert.Equal("bargained", p.S("redcowl"));
        // "Open them yourself; my lads won't stop you."
        p.Walk("cages");
        Assert.True(p.CanUse("cage0"), p.Refusal("cage0"));
        // Someone who pays for the teamsters alone pays once.
        var k = Route.New("outcast");
        k.Talk("redcowl", "let the teamsters go", "pay fifty");
        Assert.DoesNotContain(k.Offered("redcowl"), t => t.Contains("Let the teamsters go"));
        // And nobody sells you a strongbox you are already carrying.
        var b = Route.New("outcast");
        b.W.Facts["caravan.box_taken"] = true;
        b.Give("coyle_strongbox");
        Assert.DoesNotContain(b.Offered("redcowl"), t => t.Contains("Coyle wagons"));
    }

    [Fact]
    public void Rav_slides_Jessops_key_across_the_table_once()
    {
        var p = Route.New("outcast");
        p.Talk("rav", "news of coyle");
        p.Talk("rav", "news of coyle");
        p.Talk("rav", "news of coyle");
        Assert.Equal(1, p.Count("clerks_key"));
    }

    [Fact]
    public void Vonnra_is_accused_once_however_often_the_fortune_is_read()
    {
        var p = Route.New("scholar");
        p.W.Facts["beasts.outcome"] = "cured";
        p.W.Facts["caravan.survivors"] = "rescued";
        p.W.Facts["chapter.ready"] = true;
        p.Apply("""[{ "quest": { "id": "lamps", "entry": "irons" } }, { "quest": { "id": "lamps", "entry": "coin" } }]""");
        p.Talk("vonnra", "goodbye");
        Assert.Equal("?", p.Marker("vonnra"));
        var (_, choices, r, last) = p.Fortune();
        Assert.Contains(choices, c => c.Contains("You lit the lamps"));
        // Said, and the conversation left before the door: the chapter is not closed yet.
        r.Choose(last.Choices.First(c => c.Text.Contains("You lit the lamps")).Index);
        var v = p.W.Npc("vonnra");
        (double trust, double respect) = (v.Trust, v.Respect);
        Assert.False(p.F("chapter.done").Truthy);
        // Read again: the accusation was made; it is not offered, nor paid for, twice.
        var again = p.Fortune();
        Assert.DoesNotContain(again.Choices, c => c.Contains("You lit the lamps"));
        Assert.Equal((trust, respect), (v.Trust, v.Respect));
        var door = again.R.Choose(again.Last.Choices.First(c => c.Text.Contains("door")).Index).Next!;
        Assert.Equal("fortune", again.R.Choose(door.Choices[0].Index).Action);
        // The book closed: "Your chapter is written". She reads it no more, and is no longer waiting on you.
        Assert.DoesNotContain(p.Offered("vonnra"), c => c.Contains("fortune"));
        Assert.Null(p.Marker("vonnra"));
    }

    [Fact]
    public void The_toll_ledger_is_paid_for_once()
    {
        var p = Route.New("hunter");
        p.Talk("rook", "talk");
        p.Talk("vonnra", "goodbye");
        p.Talk("vonnra", "pay your toll", "five gold");
        Assert.True(p.Has("caravan", "toll_ledger"));
        Assert.DoesNotContain(p.Offered("vonnra"), t => t.Contains("pay your toll"));
    }

    /* ------------------------------------------- choices that outlive their sense -- */

    [Fact]
    public void Snib_is_not_asked_to_move_a_pump_that_no_longer_pumps_into_the_stream()
    {
        var p = Route.New("scholar");
        p.Learn("clue.green_stream");
        p.Talk("snib", "sinkhole");
        Assert.Equal("moved", p.S("dig.pump"));
        var (said, offered) = p.Greet("snib");
        Assert.Contains("sinkhole now", said);
        Assert.DoesNotContain(offered, t => t.Contains("sinkhole") || t.Contains("poisoning") || t.Contains("shut it off"));
        // Broken, he knows exactly who.
        var b = Route.New("outcast");
        b.Learn("clue.green_stream");
        b.W.Facts["dig.pump"] = "broken";
        var (bs, bo) = b.Greet("snib");
        Assert.Contains("BROKEN", bs);
        Assert.DoesNotContain(bo, t => t.Contains("How much") || t.Contains("shut it off"));
        b.Talk("snib", "leave");
        Assert.Contains("Pump is BROKEN", b.Greet("snib").Said);
    }

    [Fact]
    public void Greymuzzle_met_before_the_Roost_was_known_can_still_be_asked_to_run()
    {
        var p = Route.New("hunter");
        var locked = p.Talk("greymuzzle", "kneel").Last!.Choices.Single(c => c.Text.Contains("Run with me"));
        Assert.False(locked.Enabled);
        Assert.Equal("You would need somewhere to lead them", locked.Locked);
        p.Talk("greymuzzle", "leave");
        Assert.Equal("met", p.S("greymuzzle"));
        // Somewhere to lead them, found since.
        p.Talk("rav", "about the kerchiefs");
        p.Talk("greymuzzle", "run with me", "go");
        Assert.True(p.F("pack.allied").Truthy);
        Assert.Equal("allied", p.S("beasts.outcome"));
        Assert.Equal(QuestStatus.Resolved, p.Status("beasts"));
        // Not offered to someone who broke their word to him.
        var b = Route.New("hunter");
        b.Talk("greymuzzle", "kneel", "stop whatever is poisoning");
        b.W.Facts["promise.broken"] = true;
        b.Learn("hint.roost");
        Assert.DoesNotContain(b.Offered("greymuzzle"), t => t.Contains("Run with me"));
    }

    [Fact]
    public void Harlan_does_not_ask_for_news_of_a_nephew_who_is_home()
    {
        var p = Route.New("hunter");
        p.Talk("harlan", "goodbye");
        Assert.Contains(p.Offered("harlan"), t => t.Contains("What happened to the caravan"));
        p.W.Facts["caravan.survivors"] = "rescued";
        var o = p.Offered("harlan");
        Assert.DoesNotContain(o, t => t.Contains("What happened to the caravan") || t.Contains("Which road") || t.Contains("It wasn't wolves"));
        Assert.Contains(o, t => t.Contains("Jory's alive"));
    }

    [Fact]
    public void The_arrests_way_out_is_the_ledger_only_for_someone_who_knows_what_it_proves()
    {
        var p = Route.New("outcast");
        p.W.Facts["player.wanted"] = true;
        p.Give("pell_ledger");
        Assert.DoesNotContain(p.Offered("holloway"), t => t.Contains("who paid the Kerchiefs"));
        p.Apply("""[{ "quest": { "id": "caravan", "entry": "wreck" } }]""");
        p.Talk("holloway", "who paid the Kerchiefs");
        Assert.Equal("exposed", p.S("caravan.pell"));
        Assert.True(p.F("player.pardoned").Truthy);
    }

    /* ---------------------------------------------------- marks over heads -- */

    [Fact]
    public void A_question_mark_means_there_is_something_to_bring_them()
    {
        var p = Route.New("hunter");
        p.Talk("harlan", "goodbye");
        p.Talk("holloway", "that's all");
        Assert.Null(p.Marker("harlan"));
        // The Roost found: Harlan would want to know where his wagons are.
        p.Apply("""[{ "quest": { "id": "caravan", "entry": "roost_found" } }]""");
        Assert.Equal("?", p.Marker("harlan"));
        p.Talk("harlan", "seen your wagons");
        Assert.Null(p.Marker("harlan"));
        // Jory home: news to carry, until it is carried.
        p.W.Facts["caravan.survivors"] = "rescued";
        Assert.Equal("?", p.Marker("harlan"));
        p.Talk("harlan", "jory's alive");
        Assert.Null(p.Marker("harlan"));
        // A box kept past his patience is not something he is waiting for.
        p.Give("coyle_strongbox");
        Assert.Equal("?", p.Marker("harlan"));
        p.W.Facts["caravan.cargo"] = "kept";
        Assert.Null(p.Marker("harlan"));
        // Holloway's mark for the ledger: while he would read it, and when it proves something.
        p.Give("pell_ledger");
        var h = Route.New("hunter");
        h.Talk("holloway", "that's all");
        h.Give("pell_ledger");
        Assert.Equal("?", h.Marker("holloway"));
        h.Talk("holloway", "found this book");
        Assert.Null(h.Marker("holloway"));
        h.Talk("rav", "about the kerchiefs");
        Assert.Equal("?", h.Marker("holloway"));
    }

    [Fact]
    public void Tam_warms_to_being_believed_once_not_every_time_he_tells_it()
    {
        var p = Route.New("hunter");
        p.Talk("tam", "listening", "did right");
        var tam = p.W.Npc("tam");
        (double t, double a) = (tam.Trust, tam.Affection);
        p.Talk("tam", "tell me again");
        p.Talk("tam", "tell me again");
        Assert.Equal((t, a), (tam.Trust, tam.Affection));
        Assert.DoesNotContain(p.Talk("tam", "tell me again").Last!.Choices, c => c.Text.Contains("You did right"));
    }

    [Fact]
    public void A_journal_line_is_announced_under_its_quests_name_whatever_colons_it_has()
    {
        var p = Route.New("hunter");
        var toasts = new List<Toast>();
        p.J.OnToast = toasts.Add;
        p.Apply("""[{ "quest": { "id": "lamps", "entry": "nell" } }]""");
        var t = toasts.Single(x => x.Kind == ToastKind.Quest);
        Assert.Equal("The Lamps at the Low Ford", t.Text);
        Assert.Equal(Lore.EntryText("lamps", "nell"), t.Sub);
        Assert.Contains(": twelve", t.Sub);
    }

    /* --------------------------------------------- the journal, kept honest -- */

    [Fact]
    public void A_settled_story_is_not_given_back_its_leads()
    {
        var p = Route.New("hunter");
        p.W.Facts["beasts.outcome"] = "cured";
        p.Apply("""[{ "quest": { "id": "beasts", "status": "resolved", "outcome": "cured" } }]""");
        p.W.Facts["caravan.survivors"] = "rescued";
        p.W.Facts["caravan.cargo"] = "returned";
        p.Apply("""[{ "quest": { "id": "caravan", "status": "resolved", "entry": "survivors_freed" } }]""");
        var beasts = p.Journal("beasts");
        var caravan = p.Journal("caravan");
        p.Talk("rook", "talk");
        p.Talk("holloway", "wolves");
        p.Talk("harlan", "goodbye");
        p.Talk("wenna", "getting bolder");
        p.Talk("tam", "i did");
        p.Talk("tam", "tell me again");
        Assert.Equal(beasts, p.Journal("beasts"));
        Assert.Equal(caravan, p.Journal("caravan"));
        // Maeca thanks whoever cleared the water, before anything about a bounty.
        Assert.Contains("never once saved anything", p.Greet("maeca").Said);
        // Wenna does not ask for water she has already tested.
        var w = Route.New("scholar");
        w.Learn("clue.analysis");
        w.Talk("wenna", "getting bolder");
        Assert.False(w.Has("beasts", "wenna_request"));
    }

    [Fact]
    public void The_town_says_a_thing_happened_once_it_has()
    {
        var p = Route.New("hunter");
        p.Talk("holloway", "watch-post", "lit again");
        bool Folk(string fragment) => Lore.FolkLines.Any(l => l.Text.Contains(fragment) && Rules.Test(l.When, p.C));
        Assert.False(Folk("brought old Corran home"));
        Assert.NotEqual("Has brought Corran home from the Low Ford post, and crossed out a word in his book.", Lore.ConcernOf("holloway", p.C));
        Assert.Contains("handcart and a spade", string.Join(" ", p.Sleep()));
        Assert.True(Folk("brought old Corran home"));
        Assert.Equal("Has brought Corran home from the Low Ford post, and crossed out a word in his book.", Lore.ConcernOf("holloway", p.C));
        // Aldo is buried the day after the wolves took him, not the morning they did.
        var a = Route.New("devout");
        a.W.Facts["beasts.severity"] = 6;
        a.Sleep();
        Assert.True(a.F("wolves.at_gate").Truthy);
        Assert.DoesNotContain(Lore.FolkLines, l => l.Text.Contains("buried Aldo") && Rules.Test(l.When, a.C));
        a.Sleep();
        Assert.Contains(Lore.FolkLines, l => l.Text.Contains("buried Aldo") && Rules.Test(l.When, a.C));
    }

    /* -------------------------------------------- what the world remembers -- */

    [Fact]
    public void Cages_opened_stay_open_across_a_save_and_Jory_is_never_caged_again()
    {
        var p = Route.New("outcast").Enter("verge");
        p.Walk("roost");
        p.Talk("redcowl", "let the teamsters go", "pay fifty");
        p.Walk("cages");
        p.Use("cage0");
        p.Use("cage1");
        p.SaveAndLoad();
        Assert.False(p.Offers("cage0"));
        Assert.False(p.Offers("cage1"));
        Assert.False(p.Host!.FakeLook.Shown(p.Meta!.Refs.GetProperty("cages")[0].GetString()!));
        Assert.True(p.Offers("cage2"));
        p.Use("cage2");
        Assert.Equal("rescued", p.S("caravan.survivors"));
        Assert.True(p.Has("caravan", "survivors_freed"));
        p.Leave();
        p.Enter("verge");
        for (int k = 0; k < 3; k++) Assert.False(p.Offers($"cage{k}"));
    }

    [Fact]
    public void What_the_story_carries_off_is_gone_from_the_Roost()
    {
        var p = Route.New("outcast").Enter("verge");
        p.Learn("clue.blasting_ember");
        p.Walk("roost");
        p.Talk("redcowl", "watch is on its way");
        p.Walk("cages");
        var cargo = p.Meta!.Place("V", "cargo");
        int colliders = p.B!.Collision.All().Count;
        p.Use("strongbox");
        Assert.Contains(p.Host!.FakeLook.PropsHidden, h => h.Id == "props/Chest_Wood");
        Assert.DoesNotContain(p.B.Collision.All(), c => c.Tag == "strongbox");
        Assert.DoesNotContain(p.Host.FakeLook.PropsHidden, h => h.Id == "props/Crate_Wooden");
        p.Use("crates_sink");
        Assert.Contains(p.Host.FakeLook.PropsHidden, h => h.Id == "props/Crate_Wooden");
        Assert.DoesNotContain(p.B.Collision.All(), c => Math.Abs(c.X - cargo.X) < 0.01 && Math.Abs(c.Z - cargo.Z) < 0.01);
        // And when the survivor comes back.
        p.Leave();
        p.Enter("verge");
        Assert.Contains(p.Host!.FakeLook.PropsHidden, h => h.Id == "props/Chest_Wood");
        Assert.Contains(p.Host.FakeLook.PropsHidden, h => h.Id == "props/Crate_Wooden");
        // Redcowl's crates stay in his camp.
        var r = Route.New("outcast");
        r.Learn("clue.blasting_ember");
        r.Talk("redcowl", "six crates", "blasting ember", "deep enough", "keep them dry");
        r.Enter("verge");
        Assert.DoesNotContain(r.Host!.FakeLook.PropsHidden, h => h.Id == "props/Crate_Wooden");
    }

    [Fact]
    public void The_Roost_is_empty_once_its_last_defender_falls_whoever_fell_first()
    {
        var p = Route.New("hunter").Enter("verge");
        p.Walk("roost");
        p.Kill(e => e.Tag == "redcowl");
        Assert.Equal("dead", p.S("redcowl"));
        Assert.False(p.F("roost.cleared").Truthy);
        p.Kill(e => e.Tag == "roost");
        Assert.True(p.F("roost.cleared").Truthy);
    }

    [Fact]
    public void Fire_at_the_Roost_burns_whoever_is_in_the_cages_and_whatever_is_under_the_canvas()
    {
        // With the teamsters in their cages.
        var p = Route.New("outcast").Enter("verge");
        var roost = p.Meta!.Place("V", "roost");
        p.Zone!.Hooks.OnHitProp!("powder", -1, Sim.School.Fire, 10, roost.X, roost.Z);
        Assert.Equal("dead", p.S("caravan.survivors"));
        Assert.Contains(p.W.History, h => h.Id == "burned_roost");
        Assert.Equal("burned", p.S("be.crates"));
        Assert.Equal("lost", p.S("caravan.cargo"));
        // With the teamsters long dead of hunger: nobody is burned alive, but the crates go up all the same.
        var s = Route.New("outcast");
        s.Sleeps(5);
        Assert.Equal("dead", s.S("caravan.survivors"));
        s.Enter("verge");
        s.Zone!.Hooks.OnHitProp!("powder", -1, Sim.School.Fire, 10, roost.X, roost.Z);
        Assert.DoesNotContain(s.W.History, h => h.Id == "burned_roost");
        Assert.Equal("burned", s.S("be.crates"));
        s.Leave();
        s.Learn("clue.blasting_ember");
        s.Apply("""[{ "quest": { "id": "caravan", "entry": "roost_found" } }]""");
        Assert.DoesNotContain(s.Offered("harlan"), t => t.Contains("six crates"));
    }

    [Fact]
    public void Cargo_sold_down_the_south_road_takes_the_crates_with_it()
    {
        // The teamsters freed, the box left in the Roost three days: the Kerchiefs sell the lot on.
        var p = Route.New("hunter");
        p.Learn("clue.blasting_ember");
        p.Apply("""[{ "quest": { "id": "caravan", "entry": "roost_found" } }]""");
        p.W.Facts["caravan.survivors"] = "rescued";
        Assert.Contains(p.Offered("harlan"), t => t.Contains("six crates"));
        Assert.Contains("Coyle cloth at half its price", p.Sleeps(3));
        Assert.Equal("with_kerchiefs", p.S("caravan.cargo"));
        Assert.Equal("dig", p.S("be.crates"));
        Assert.DoesNotContain(p.Offered("harlan"), t => t.Contains("six crates"));
        Assert.DoesNotContain(p.Offered("redcowl"), t => t.Contains("six crates"));
        p.W.Facts["beasts.outcome"] = "cured";
        p.W.Facts["chapter.ready"] = true;
        Assert.Contains("gone down the south road", p.Fortune().Read);
    }

    /* ------------------------------ reported by the CI review (docs/cloud/ci-health.md) -- */

    static bool Blighted(Route p, string? tag = null) => p.B!.Enemies.Living().Any(e => e.Def.Id == "wolf_blighted" && (tag == null || e.Tag == tag));

    [Fact]
    public void R1_a_Pack_that_runs_with_you_or_was_bought_off_is_not_sick_once_the_water_runs_clear()
    {
        // Allied: the poison still running, the sick lie in the Hollow with the rest.
        var p = Route.New("hunter");
        p.Talk("rav", "about the kerchiefs");
        p.Talk("greymuzzle", "kneel", "run with me", "go");
        Assert.Equal("allied", p.S("beasts.outcome"));
        p.Enter("verge");
        p.Walk("hollow", 20, 0);
        Assert.True(Blighted(p, "hollow"));
        // The pump stopped, two days on: the stream runs clear, and so do they.
        p.W.Facts["dig.pump"] = "broken";
        p.Leave();
        Assert.Contains("Your wolves were drinking", p.Sleeps(2));
        Assert.Equal("allied", p.S("beasts.outcome"));
        p.Enter("verge");
        p.Walk("hollow", 20, 0);
        Assert.False(Blighted(p, "hollow"));
        // Bought off (the Dig sold to Pell): his pump moved, the water clean, the wood well.
        var b = Route.New("scholar");
        b.Give("stream_sample");
        b.Talk("wenna", "test it");
        b.Talk("pell", "killing the wolves", "forty");
        b.Sleeps(4);
        Assert.Equal("exploited", b.S("beasts.outcome"));
        Assert.True(b.F("stream.clear").Truthy);
        b.Enter("verge");
        Assert.False(Blighted(b));
        b.Walk("hollow", 20, 0);
        Assert.False(Blighted(b, "hollow"));
    }

    [Fact]
    public void R2_after_a_slaughter_the_stream_still_clears_and_the_bitterroot_goes_with_the_poison()
    {
        var p = Route.New("hunter");
        p.Talk("holloway", "wolves");
        p.W.Facts["beasts.population"] = 4;
        p.Sleep();
        Assert.Equal("slaughtered", p.S("beasts.outcome"));
        p.Enter("verge");
        Assert.True(p.Offers("root0"));
        p.W.Facts["dig.pump"] = "broken";
        p.Leave();
        Assert.Contains("nothing left in the wood to drink from it", p.Sleeps(2));
        Assert.True(p.F("stream.clear").Truthy);
        Assert.Equal("slaughtered", p.S("beasts.outcome"));
        p.Enter("verge");
        for (int k = 0; k < 3; k++) Assert.False(p.Offers($"root{k}"));
    }

    [Fact]
    public void R3_a_promise_to_the_Pack_is_broken_by_killing_a_wolf_at_peace_not_one_that_came_for_you()
    {
        var p = Route.New("hunter");
        p.Talk("greymuzzle", "kneel", "stop whatever is poisoning");
        Assert.True(p.F("promise.pack").Truthy);
        // Their kin worn into the Hollow: the den comes for you, and you defend yourself.
        p.Give("wolfhide_cloak");
        p.J.Equip(p.J.Ch.Pack.First(i => i?.Def == "wolfhide_cloak")!.Uid, null, null);
        p.Enter("verge");
        p.Walk("hollow", 10, 0);
        var den = p.B!.Enemies.Living().First(e => e.Tag == "hollow" && e.Disposition == Sim.Disposition.Hostile);
        p.B.KillEnemy(den, true, null);
        p.Wait(0.2);
        Assert.False(p.F("promise.broken").Truthy);
        Assert.DoesNotContain(p.W.History, h => h.Id == "broke_promise");
        // A wolf minding its own business, struck down on purpose: that breaks it.
        p.Leave();
        p.J.Unequip(EquipSlot.Cloak, null);
        p.Enter("verge");
        p.Walk("hollow", 10, 0);
        var calm = p.B!.Enemies.Living().First(e => e.Tag == "hollow" && e.Disposition == Sim.Disposition.Neutral);
        p.B.Provoke(calm);
        p.B.KillEnemy(calm, true, null);
        p.Wait(0.2);
        Assert.True(p.F("promise.broken").Truthy);
        Assert.Contains(p.W.History, h => h.Id == "broke_promise");
    }

    [Fact]
    public void R4_running_with_the_Pack_is_the_louder_name_but_the_cleared_water_is_on_the_page()
    {
        // Decided: "who runs with wolves" outranks "who cleared the water" (the
        // allied verdict is its own), and the deed is still read back.
        var p = Route.New("hunter");
        p.Talk("rav", "about the kerchiefs");
        p.Talk("greymuzzle", "kneel", "run with me", "go");
        p.Apply("""[{ "set": { "dig.pump": "broken" } }, { "quest": { "id": "beasts", "entry": "pump_broken" } }, { "history": { "id": "broke_pump", "text": "wrecked the Dig's pump", "tags": ["beasts"], "spread": 2 } }]""");
        p.Sleeps(2);
        Assert.True(p.F("stream.clear").Truthy);
        var sum = Chapter.Summary(p.J.Ch, p.W);
        Assert.Equal("Wren, who runs with wolves", sum.Epithet);
        var beasts = sum.Threads.Single(t => t.Id == "beasts");
        Assert.Equal("Ran with the Pack", beasts.Verdict);
        Assert.Contains(Lore.EntryText("beasts", "pump_broken"), beasts.Beats);
        Assert.Contains("stopped the poison in the Thornhollow stream", sum.Deeds);
    }

    [Fact]
    public void Nothing_the_story_still_needs_goes_over_a_counter()
    {
        var p = Route.New("outcast");
        p.Give("coyle_strongbox");
        p.Give("pell_ledger");
        p.Give("sigil_fragment");
        p.J.OpenShop("rav", new Random(1));
        p.J.OpenShop("vonnra", new Random(1));
        foreach (var it in p.J.Ch.Pack.Where(i => i != null && Items.Get(i.Def).Kind == ItemKind.Quest))
        {
            Assert.Null(p.J.PriceOf("rav", it!.Uid, false));
            Assert.Null(p.J.PriceOf("vonnra", it.Uid, false));
        }
        // The fence is Rav's word, not his counter.
        p.Talk("rav", "buy this, quietly", "sell it");
        Assert.Equal("sold", p.S("caravan.cargo"));
        Assert.True(p.Has("caravan", "cargo_sold"));
    }
}
