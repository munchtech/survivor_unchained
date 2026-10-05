using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Thornhollow Verge, run without a screen (Play/Zones/Verge.cs).</summary>
public class VergeTests
{
    sealed record Setup(Journey J, FakeHost Host, Verge Zone, Battle B, ZoneMeta Meta);

    static Setup Make(TimeOfDay time = TimeOfDay.Day, Journey? j = null)
    {
        var a = Callings.Archetype("warden");
        j ??= Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        j.World.Time = time;
        var meta = ZoneMeta.Load("verge");
        var host = new FakeHost(j, meta);
        var zone = new Verge(host, meta);
        var ground = Heightfield.Load(meta);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), ground.HeightAt, at.X, at.Z, at.Facing, 11);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, meta);
    }

    static void Run(Setup s, double seconds, double mx = 0, double mz = 0)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, mx, mz);
            s.B.Events.Drain();
            s.Host.Pass(1 / 60.0);
        }
    }

    static Interactable I(Setup s, string id) => s.Zone.Interactables.Single(i => i.Id == id);

    [Fact]
    public void Arriving_starts_the_day_and_the_tracker()
    {
        var s = Make();
        Assert.Same(Atmospheres.Day, s.Host.Air);
        Assert.Contains(s.Host.Announced, a => a.Title == "zone");
        // Quiet at the gate: nothing near it, and nothing coming.
        Run(s, 10);
        var p = s.B.Player;
        Assert.DoesNotContain(s.B.Enemies.Living(), e => e.Disposition == Disposition.Hostile && (e.Roused || Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) < 25));
    }

    [Fact]
    public void By_day_the_wood_keeps_its_packs_where_they_lie_until_you_come()
    {
        var s = Make();
        Assert.False(s.B.EmberOn);
        var packs = s.B.Enemies.Living().Where(e => e.Disposition == Disposition.Hostile && e.Wake > 0).ToList();
        Assert.True(packs.Count > 12, $"{packs.Count} resting");
        // Nothing comes looking for you while you keep your distance.
        Run(s, 20);
        Assert.All(packs.Where(e => e.Alive), e => Assert.False(e.Roused));
        Assert.Equal(packs.Count, s.B.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && e.Wake > 0));
        // Go close to one, and it wakes, and its fellows with it.
        var one = packs.First(e => e.Def.Id == "wolf");
        s.B.Player.X = one.X + 6; s.B.Player.Z = one.Z;
        Run(s, 1);
        Assert.True(one.Roused);
        Assert.All(packs.Where(o => o.HomeX == one.HomeX && o.HomeZ == one.HomeZ), o => Assert.True(o.Roused));
        // Putting them down teaches the survivor.
        double xp = s.J.Ch.Xp;
        s.J.Killed(one, true);
        Assert.True(s.J.Ch.Xp > xp);
    }

    [Fact]
    public void After_dark_the_ember_burns_through_and_pulls_you_into_an_arena()
    {
        // None by day.
        Assert.DoesNotContain(Make().Zone.Interactables, i => i.Id.StartsWith("scar:"));
        var s = Make(TimeOfDay.Night);
        var scars = s.Zone.Interactables.Where(i => i.Id.StartsWith("scar:")).ToList();
        Assert.InRange(scars.Count, 2, 4);
        Assert.Contains(s.Zone.MapMarks(), m => m.Kind == MarkKind.Danger && m.Label.StartsWith("The Scar"));
        // Stepping in pulls you into an arena held by that part of the wood's people, and brings you back where you stood.
        var dead = scars.Single(i => i.Name == "The Scar at the Sealed Door");
        s.B.Player.X = dead.X; s.B.Player.Z = dead.Z;
        dead.Act();
        var spec = s.Host.Entered!;
        Assert.Equal("dead", spec.People);
        Assert.Equal("verge", spec.ReturnZone);
        Assert.Equal(dead.X, spec.ReturnX, 3);
        // Won, it is out for the rest of the night.
        s.J.Apply(spec.OnWin!);
        var again = Make(TimeOfDay.Night, s.J);
        Assert.DoesNotContain(again.Zone.Interactables, i => i.Name == "The Scar at the Sealed Door");
    }

    [Fact]
    public void The_storys_great_fights_are_the_nights_and_the_story_remembers_how_they_went()
    {
        var s = Make();
        // The Pack hostile, the Kerchiefs out, the Dig turned, the sigil's fragment in hand.
        s.J.World.Facts["hollow.hostile"] = true;
        s.J.World.Facts["dig.hostile"] = true;
        s.J.Apply("""[{ "quest": { "id": "vault", "status": "active", "entry": "fragment" } }]""");
        var day = Make(TimeOfDay.Day, s.J);
        var fights = day.Zone.Interactables.Where(i => i.Id.StartsWith("night:")).ToList();
        Assert.Equal(["night:hollow", "night:roost", "night:dig", "night:vault"], fights.Select(f => f.Id));
        // By day: the place says so.
        Assert.All(fights.Where(f => f.When!()), f => Assert.NotNull(f.Locked!()));
        var night = Make(TimeOfDay.Night, s.J);
        foreach (var f in night.Zone.Interactables.Where(i => i.Id.StartsWith("night:")))
        {
            Assert.True(f.When!(), f.Id);
            Assert.Null(f.Locked!());
            f.Act();
            var spec = night.Host.Entered!;
            Assert.True(spec.Story);
            Assert.NotNull(spec.BossName);
            // Each ends on the narrator's own line for how it went, never "the story goes on".
            Assert.False(string.IsNullOrWhiteSpace(spec.EndWon), spec.Id);
            Assert.False(string.IsNullOrWhiteSpace(spec.EndLost), spec.Id);
            Assert.DoesNotContain("story", spec.EndWon + spec.EndLost);
            // Both outcomes are real changes, with real quest entries.
            foreach (var change in new[] { spec.OnWin!, spec.OnLose! })
                foreach (var c in Json.Parse<List<Change>>(change).Where(c => c.Quest?.Entry != null))
                    Assert.True(Lore.Quests[c.Quest!.Id].Entries.ContainsKey(c.Quest.Entry!), $"{spec.Id}: {c.Quest.Id}.{c.Quest.Entry}");
        }
        // The hunt won: Greymuzzle is dead, and there is no hunt left.
        night.Zone.Interactables.Single(i => i.Id == "night:hollow").Act();
        s.J.Apply(night.Host.Entered!.OnWin!);
        Assert.Equal("dead", s.J.World.Fact("greymuzzle").Str);
        Assert.True(s.J.World.Fact("beasts.population").Number <= 30);
        Assert.False(Make(TimeOfDay.Night, s.J).Zone.Interactables.Single(i => i.Id == "night:hollow").When!());
        // And the town hears it in the morning.
        Assert.Contains(Simulation.AdvanceDay(s.J.Ctx, () => 0.5).Lines, l => l.Contains("howled from the Hollow"));
        // The raid lost: the story is told so, and it waits at the table.
        var raid = Make(TimeOfDay.Night, s.J);
        raid.Zone.Interactables.Single(i => i.Id == "night:roost").Act();
        var spec2 = raid.Host.Entered!;
        SurvivorUnchained.Arena.Arenas.Begin(s.J.World, spec2);
        var b2 = s.J.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        SurvivorUnchained.Arena.Arenas.Finish(s.J, b2, spec2, won: false);
        Assert.Contains(s.J.World.Rematches, r => r.Id == "roost_raid");
        Assert.True(Quest(s.J, "caravan", "roost_repelled"));
    }

    static bool Quest(Journey j, string id, string entry) => j.World.Quests.TryGetValue(id, out var q) && q.Entries.Contains(entry);

    static SurvivorUnchained.Arena.ArenaSpec Fight(Journey j, string id)
    {
        var night = Make(TimeOfDay.Night, j);
        night.Zone.Interactables.Single(i => i.Id == $"night:{id}").Act();
        return night.Host.Entered!;
    }

    [Fact]
    public void Redcowl_on_his_knee_is_hers_to_spare_or_finish()
    {
        // The owner, 4 October: "Spare him" or "Finish it". Nothing chooses for her.
        var s = Make();
        s.J.Apply("""[{ "quest": { "id": "caravan", "status": "active", "entry": "roost_found" } }]""");
        var spec = Fight(s.J, "roost");
        Assert.Equal("Spare him", spec.SpareVerb);
        Assert.NotNull(spec.OnSpare);
        Assert.False(spec.Spare);
        // Spared: he lives, owes her, and takes his people off the Old Road; the camp is hers to go through.
        SurvivorUnchained.Arena.Arenas.Won(s.J, spec, spared: true);
        var w = s.J.World;
        Assert.True(spec.Spared);
        Assert.Equal("spared", w.Fact("redcowl").Str);
        Assert.True(w.Fact("roost.cleared").Truthy);
        Assert.False(w.Fact("roost.hostile").Truthy);
        Assert.True(w.Fact("redcowl.last_words").IsNull);
        Assert.True(Quest(s.J, "caravan", "roost_spared"));
        Assert.False(Quest(s.J, "caravan", "roost_raided"));
        Assert.Contains(w.History, h => h.Id == "spared_redcowl");
        Assert.Contains("does not limp", spec.EndSpared);
        Assert.False(Make(TimeOfDay.Night, s.J).Zone.Interactables.Single(i => i.Id == "night:roost").When!());
        Assert.Contains(Standings.Of(s.J.Ctx), x => x.Id == "kerchief" && x.Word == "In your debt");
        // The town sees them go, and Rav has two cups out.
        Assert.Contains(Simulation.AdvanceDay(s.J.Ctx, () => 0.5).Lines, l => l.Contains("would not get on a cart"));
        w.Npc("rav").Flags["met"] = true;
        var rav = H.Talk(Dialogue.Find("rav")!, s.J.Ctx, "two he owes");
        Assert.Contains("terrible payer", rav!.Text);
        // A rematch from the table is the same choice.
        Assert.Equal(spec.OnSpare, SurvivorUnchained.Arena.Arenas.Again(spec, "waystation", 0, 0, 0).OnSpare);

        // Finished: C11's last words, and the red hat in the mud.
        var k = Make();
        var kill = Fight(k.J, "roost");
        SurvivorUnchained.Arena.Arenas.Won(k.J, kill, spared: false);
        Assert.False(kill.Spared);
        Assert.Equal("dead", k.J.World.Fact("redcowl").Str);
        Assert.Equal("leg", k.J.World.Fact("redcowl.last_words").Str);
        Assert.True(Quest(k.J, "caravan", "roost_raided"));
        // And left unsaid (today's runtime), he dies, as he always has.
        var t = Make();
        SurvivorUnchained.Arena.Arenas.Won(t.J, Fight(t.J, "roost"));
        Assert.Equal("dead", t.J.World.Fact("redcowl").Str);
    }

    [Fact]
    public void Spared_he_takes_the_crates_he_swore_to_keep_and_leaves_the_rest()
    {
        var s = Make();
        s.J.World.Facts["be.crates"] = "redcowl";
        SurvivorUnchained.Arena.Arenas.Won(s.J, Fight(s.J, "roost"), spared: true);
        // The Act 2 army's powder goes with him; nobody else will settle them.
        s.J.World.Facts["chapter.done"] = true;
        Simulation.AdvanceDay(s.J.Ctx, () => 0.5);
        Assert.Equal("redcowl", s.J.World.Fact("be.crates").Str);
        // Unclaimed, they wait in the empty Roost with the Coyle cargo, and the Watch has them at the act's end.
        var u = Make();
        SurvivorUnchained.Arena.Arenas.Won(u.J, Fight(u.J, "roost"), spared: true);
        u.J.World.Facts["chapter.done"] = true;
        Simulation.AdvanceDay(u.J.Ctx, () => 0.5);
        Assert.Equal("watch", u.J.World.Fact("be.crates").Str);
    }

    [Fact]
    public void Greymuzzle_let_go_is_her_choice_and_finishing_him_breaks_the_promise()
    {
        var s = Make();
        s.J.World.Facts["hollow.hostile"] = true;
        s.J.World.Facts["promise.pack"] = true;
        s.J.World.Facts["stream.clear"] = true;
        var spec = Fight(s.J, "hollow");
        Assert.Equal("Let him go", spec.SpareVerb);
        // Today's runtime lets him go by itself, as before.
        SurvivorUnchained.Arena.Arenas.Won(s.J, spec);
        Assert.Equal("spared", s.J.World.Fact("greymuzzle").Str);
        Assert.Contains("old wolf is breathing", spec.EndSpared);
        // "Finish it" breaks the promise she knelt to make.
        var k = Make();
        k.J.World.Facts["hollow.hostile"] = true;
        k.J.World.Facts["promise.pack"] = true;
        k.J.World.Facts["stream.clear"] = true;
        SurvivorUnchained.Arena.Arenas.Won(k.J, Fight(k.J, "hollow"), spared: false);
        Assert.Equal("dead", k.J.World.Fact("greymuzzle").Str);
        Assert.True(k.J.World.Fact("promise.broken").Truthy);
        // Without the promise and the clean stream there is no choice to make.
        var n = Make();
        n.J.World.Facts["hollow.hostile"] = true;
        Assert.Null(Fight(n.J, "hollow").OnSpare);
    }

    [Fact]
    public void A_lost_story_fight_wakes_her_on_Chids_bench_the_next_morning()
    {
        // The owner, 4 October: the night is lost, Chid carries her home, and she wakes in town.
        foreach (var (id, people, morning, wakes, chid) in new[]
        {
            ("hollow", "pack", "stopped, all at once", "wolf's spit", "Maeca"),
            ("roost", "kerchiefs", "the slow kind", "the way the Kerchiefs lay out their dead", "stitched up half of it"),
            ("dig", "lamplings", "where the wall's lamps reach", "little hands", "kettle"),
            ("vault", "dead", "like a door shutting", "a mailed hand", "very old book"),
        })
        {
            var s = Make();
            s.J.World.Facts["hollow.hostile"] = true;
            s.J.World.Facts["dig.hostile"] = true;
            s.J.Apply("""[{ "quest": { "id": "vault", "status": "active", "entry": "fragment" } }]""");
            var spec = Fight(s.J, id);
            SurvivorUnchained.Arena.Arenas.Begin(s.J.World, spec);
            var b = s.J.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
            SurvivorUnchained.Arena.Arenas.Finish(s.J, b, spec, won: false);
            Assert.StartsWith("The last thing you know", spec.EndLost);
            // The town has its morning, and she wakes into it.
            Assert.Contains(Simulation.AdvanceDay(s.J.Ctx, () => 0.5).Lines, l => l.Contains(morning));
            s.J.CarriedHome(spec);
            var r = new DialogueRunner(Dialogue.Find("chid")!, s.J.Ctx);
            var p = r.Start()!;
            Assert.Equal("carried", p.Node.Id);
            Assert.Contains(wakes, p.Text);
            p = r.Advance()!;
            Assert.Contains(chid, p.Text);
            Assert.Contains("A carter, I expect", p.Text);
            Assert.DoesNotContain("your things", p.Text);
            Assert.Equal(people, s.J.World.Fact("arena.last.people").Str);
            // Told once: the next time she falls in the world, Chid's ordinary waking.
            Assert.True(s.J.World.Fact("player.carried_home").IsNull);
            s.J.World.Facts["player.just_died"] = true;
            Assert.Equal("woke", new DialogueRunner(Dialogue.Find("chid")!, s.J.Ctx).Start()!.Node.Id);
        }
    }

    [Fact]
    public void The_wreck_gives_up_the_manifest_once()
    {
        var s = Make();
        var wreck = I(s, "wreck");
        Assert.True(wreck.When!());
        wreck.Act();
        Assert.Contains(s.J.Ch.Pack, p => p?.Def == "caravan_manifest");
        Assert.Contains("wreck", s.J.World.Quests["caravan"].Entries);
        Assert.False(wreck.When!());
        Assert.NotEmpty(s.Host.Said);
    }

    [Fact]
    public void The_watch_fire_lights_and_rests_you_once()
    {
        var s = Make();
        Assert.False(I(s, "postrest").When!());
        I(s, "postfire").Act();
        Assert.True(I(s, "postrest").When!());
        s.B.Player.Hp = 5;
        I(s, "postrest").Act();
        Assert.Equal(s.B.MaxHp, s.B.Player.Hp);
        Assert.Contains("fire", s.Host.Saved);
        Assert.NotNull(I(s, "postrest").Locked!());
    }

    [Fact]
    public void Fire_opens_the_brambles()
    {
        var s = Make();
        var br = s.Meta.Refs.GetProperty("brambles")[0];
        int col = br.GetProperty("collider").GetInt32();
        string node = br.GetProperty("node").GetString()!;
        Assert.True(s.Host.FakeLook.Shown(node));
        s.Zone.Hooks.OnHitProp!("bramble:0", col, School.Fire, 5, br.GetProperty("x").GetDouble(), br.GetProperty("z").GetDouble());
        Assert.False(s.Host.FakeLook.Shown(node));
        Assert.DoesNotContain(s.B.Collision.All(), c => c.Id == col);
        Assert.Contains(s.Host.Said, l => l.Contains("brambles go up"));
    }

    [Fact]
    public void Greymuzzle_waits_at_the_hollow_and_his_death_is_remembered()
    {
        var s = Make();
        var hollow = s.Meta.Place("V", "hollow");
        s.B.Player.X = hollow.X + 20; s.B.Player.Z = hollow.Z;
        Run(s, 0.5);
        var grey = s.B.Enemies.Living().Single(e => e.Tag == "greymuzzle");
        s.B.KillEnemy(grey, true, null);
        Assert.Equal("dead", s.J.World.Fact("greymuzzle").Str);
        Assert.Contains("alpha_dead", s.J.World.Quests["beasts"].Entries);
        Assert.Contains(s.J.World.History, h => h.Id == "killed_greymuzzle");
    }

    [Fact]
    public void Breaking_the_pump_stops_the_wheel_and_its_light()
    {
        var s = Make();
        var pump = I(s, "pump");
        Assert.Null(pump.Locked!());
        pump.Act();
        Assert.Equal("broken", s.J.World.Fact("dig.pump").Str);
        Assert.Contains("pump_wheel", s.Host.FakeLook.Stopped);
        Assert.False(pump.When!());
    }

    [Fact]
    public void A_ledger_read_for_its_date_sends_you_to_the_wagons()
    {
        // K5b, the map: the red fletching is in the wagons' sideboards.
        var s = Make();
        MarkKind Wagons() => s.Zone.MapMarks().Single(m => m.Label == "Coyle Wagons").Kind;
        Assert.Equal(MarkKind.Turn, Wagons());
        Rules.Apply(Json.Parse<Change>("""{ "quest": { "id": "caravan", "status": "active", "entry": "ledger_read" } }"""), s.J.Ctx);
        Assert.Equal(MarkKind.Quest, Wagons());
        I(s, "wreck").Act();
        Assert.Equal(MarkKind.Place, Wagons());
    }

    [Fact]
    public void Every_thing_that_can_be_done_can_be_done()
    {
        // Every interactable offered and not refused runs (its effects are
        // valid rules, its lines are there), the map and the sound read.
        var s = Make(TimeOfDay.Night);
        s.J.GiveItem("blasting_ember");
        foreach (var it in s.Zone.Interactables.ToList())
        {
            if (it.When?.Invoke() == false || it.Locked?.Invoke() != null) continue;
            it.Act();
        }
        Run(s, 8);
        Assert.NotEmpty(s.Zone.MapMarks());
        _ = s.Zone.Ambience(0, 0);
        s.Zone.Frame(1 / 60.0);
        Assert.Equal("waystation", s.Host.Travelled?.Zone);
        Assert.True(Inventory.Count(s.J.Ch, "moonpetal") > 0);
    }
}
