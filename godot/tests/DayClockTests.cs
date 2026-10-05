using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The day moving on by itself, and the story's fights called by the night
/// (docs/design/STORY_NIGHTS_AND_TIME.md; World/DayClock.cs, Play/Journey.Day.cs, Play/StoryFights.cs).</summary>
public class DayClockTests
{
    static Journey New()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
    }

    /// <summary>A journey on its first morning, the arrival over (a trouble in her journal).</summary>
    static Journey Arrived()
    {
        var j = New();
        j.World.Time = TimeOfDay.Dawn;
        j.World.Clock = 0;
        j.Apply("""[{ "quest": { "id": "beasts", "status": "active" } }]""");
        return j;
    }

    [Fact]
    public void The_first_day_waits_until_she_has_somewhere_to_be()
    {
        var j = New();
        j.World.Time = TimeOfDay.Dawn;
        j.World.Clock = 0;
        Assert.Empty(j.PassTime(DayClock.NightEnds));
        Assert.Equal(TimeOfDay.Dawn, j.World.Time);
        j.Apply("""[{ "quest": { "id": "caravan", "status": "active" } }]""");
        Assert.True(j.ClockStarted);
        Assert.NotEmpty(j.PassTime(DayClock.DayAt));
    }

    [Fact]
    public void Twelve_minutes_of_free_play_bring_the_night_and_six_more_see_it_out()
    {
        var j = Arrived();
        var turns = new System.Collections.Generic.List<(double At, ClockTurn Turn)>();
        for (double s = 0; s < 1200; s += 0.5)
            foreach (var t in j.PassTime(0.5)) turns.Add((s + 0.5, t));
        Assert.Equal([ClockTurn.Day, ClockTurn.Dusk, ClockTurn.Night, ClockTurn.Nudge, ClockTurn.NightOver], turns.Select(t => t.Turn));
        Assert.Equal([60.0, 600, 720, 900, 1080], turns.Select(t => t.At));
        // The night holds at its end until the host lets it pass: no turn twice, no day skipped.
        Assert.Equal(TimeOfDay.Night, j.World.Time);
        Assert.Equal(1, j.World.Day);
        Assert.Empty(j.PassTime(600));
        var lines = j.SeeNightOut(() => 0.5);
        Assert.Equal(2, j.World.Day);
        Assert.Equal(TimeOfDay.Dawn, j.World.Time);
        Assert.Equal(0, j.World.Clock);
        Assert.Equal(Journey.DayLines.NightOut, lines[0]);
    }

    [Fact]
    public void A_night_seen_out_is_not_a_rest_and_a_story_night_lost_wakes_her_on_chids_bench()
    {
        var j = Arrived();
        j.Expedition = new Expedition { Hp = 12 };
        j.Nightfall();
        j.SeeNightOut(() => 0.5);
        Assert.Equal(12, j.Expedition!.Hp);
        // Lost: a day on, no wound, and Chid tells the waking for that fight (not the clock).
        j.World.Facts["dig.hostile"] = true;
        var spec = StoryFights.Spec("dig", j.Ctx, "verge", 0, 0, 0);
        var lines = j.WakeAfterLoss(spec, null, () => 0.5);
        Assert.Null(j.Expedition);
        Assert.Equal(3, j.World.Day);
        Assert.Equal(TimeOfDay.Dawn, j.World.Time);
        Assert.Equal("dig_boils", j.World.Fact("player.carried_home").Str);
        Assert.True(j.World.Fact("player.just_died").Truthy);
        Assert.DoesNotContain(lines, l => l.Contains("Chid"));
        Assert.Equal("carried", new DialogueRunner(Dialogue.Find("chid")!, j.Ctx).Start()!.Node.Id);
    }

    [Fact]
    public void Her_first_rise_is_the_prologues_words_and_every_later_one_takes_less()
    {
        var j = Arrived();
        Assert.Equal(Journey.DayLines.Rise, j.RiseLine());
        Assert.Equal(Journey.DayLines.RiseAgain, j.RiseLine());
        Assert.Equal(Journey.DayLines.RiseAgain, j.RiseLine());
    }

    [Fact]
    public void Back_from_one_fight_she_has_fought_tonight_and_a_new_night_forgets_it()
    {
        var j = Arrived();
        j.Nightfall();
        Assert.False(j.FoughtTonight);
        j.BackFromFight();
        Assert.True(j.FoughtTonight);
        j.SeeNightOut(() => 0.5);
        j.Nightfall();
        Assert.False(j.FoughtTonight);
    }

    [Fact]
    public void The_inn_and_waiting_for_nightfall_are_shortcuts_through_the_same_clock()
    {
        var j = Arrived();
        j.PassTime(200);
        j.Nightfall();
        Assert.Equal(TimeOfDay.Night, j.World.Time);
        Assert.Equal(DayClock.NightAt, j.World.Clock);
        // The night goes on from nightfall.
        Assert.Equal([ClockTurn.Nudge], j.PassTime(DayClock.NudgeAt - DayClock.NightAt));
        j.Ch.Gold = 100;
        Assert.NotNull(j.Sleep(null, () => 0.5));
        Assert.Equal(2, j.World.Day);
        Assert.Equal(TimeOfDay.Day, j.World.Time);
        Assert.Equal(DayClock.DayAt, j.World.Clock);
        Assert.Equal([ClockTurn.Dusk], j.PassTime(DayClock.DuskAt - DayClock.DayAt));
    }

    [Fact]
    public void Back_from_a_fight_the_night_keeps_time_to_go_straight_on_to_another()
    {
        var j = Arrived();
        j.Nightfall();
        j.PassTime(DayClock.NightLength - 20);
        j.BackFromFight();
        Assert.Equal(DayClock.NightEnds - DayClock.AfterFight, j.World.Clock);
        Assert.Equal(TimeOfDay.Night, j.World.Time);
        // Early in the night, nothing is given back.
        var k = Arrived();
        k.Nightfall();
        k.BackFromFight();
        Assert.Equal(DayClock.NightAt, k.World.Clock);
    }

    [Fact]
    public void A_save_from_before_the_clock_starts_at_its_time_of_days_beginning()
    {
        var w = new WorldState { Time = TimeOfDay.Night };
        DayClock.Sync(w);
        Assert.Equal(DayClock.NightAt, w.Clock);
        w.Time = TimeOfDay.Day;
        w.Clock = 300;
        DayClock.Sync(w);
        Assert.Equal(300, w.Clock);
    }

    [Fact]
    public void The_night_calls_the_storys_fight_from_anywhere_and_its_spec_is_the_verges()
    {
        var j = Arrived();
        // The Roost stands open from the start (the violent road), but the night does not call it
        // until the story has pointed her at it.
        Assert.Contains(StoryFights.Open(j.Ctx), f => f.Id == "roost");
        Assert.Null(j.Tonight);
        j.Apply("""[{ "quest": { "id": "caravan", "status": "active", "entry": "roost_found" } }]""");
        Assert.Equal("roost", j.Tonight?.Id);
        var spec = StoryFights.Spec("roost", j.Ctx, "waystation", 3, 4, 0);
        Assert.True(spec.Story);
        Assert.Equal("roost_raid", spec.Id);
        Assert.Equal(("waystation", 3.0, 4.0), (spec.ReturnZone, spec.ReturnX, spec.ReturnZ));
        // The Dig turned on her is called at once, whatever else is open.
        j.World.Facts["dig.hostile"] = true;
        Assert.Contains(StoryFights.Called(j.Ctx), f => f.Id == "dig");
        // Every fight has a line for dusk, and so has a night with none.
        foreach (var f in StoryFights.All) Assert.True(Journey.DayLines.Tonight.ContainsKey(f.Id), f.Id);
        Assert.True(Journey.DayLines.Tonight.ContainsKey(""));
    }

    [Fact]
    public void A_story_fight_lost_wakes_her_in_town_and_a_table_night_lost_does_not()
    {
        var j = Arrived();
        j.World.Facts["dig.hostile"] = true;
        var spec = StoryFights.Spec("dig", j.Ctx, "verge", 0, 0, 0);
        Arenas.Begin(j.World, spec);
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        var lost = Arenas.Finish(j, b, spec, won: false);
        Assert.True(lost.WakesInTown);
        Assert.Contains(j.World.Rematches, r => r.Id == "dig_boils");
        var table = new ArenaSpec { Id = "table:1", Name = "Table", People = "pack" };
        Arenas.Begin(j.World, table);
        var b2 = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        Assert.False(Arenas.Finish(j, b2, table, won: false).WakesInTown);
    }

    [Fact]
    public void The_wood_opens_its_scars_at_nightfall_and_puts_them_out_at_dawn()
    {
        var j = Arrived();
        j.World.Time = TimeOfDay.Dusk;
        j.World.Clock = DayClock.DuskAt;
        var meta = ZoneMeta.Load("verge");
        var host = new FakeHost(j, meta);
        var zone = new Verge(host, meta);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 11);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        Assert.False(zone.HasScars);
        j.PassTime(DayClock.NightAt - DayClock.DuskAt);
        zone.TimeTurned(TimeOfDay.Night);
        Assert.True(zone.HasScars);
        Assert.Contains(zone.Interactables, i => i.Id.StartsWith("scar:"));
        Assert.NotNull(zone.NearestScar(b.Player.X, b.Player.Z));
        j.SeeNightOut(() => 0.5);
        zone.TimeTurned(TimeOfDay.Dawn);
        Assert.False(zone.HasScars);
        Assert.DoesNotContain(zone.Interactables, i => i.Id.StartsWith("scar:"));
    }
}
