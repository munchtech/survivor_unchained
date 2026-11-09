using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The lamp-posts (data/content/lamp_posts.json, Content/LampPosts.cs) and the rise at them (Play/Zones/LampRise.cs;
/// ARPG 7.2). Runs alone: it switches the lamp board to v2.</summary>
[Collection("Balance")]
public class LampPostsTests
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

    [Fact]
    public void The_registry_loads_and_its_board_posts_are_the_lamp_boards()
    {
        Lamps.UseV2(true);
        Assert.Equal(new[] { "act1.post1", "act1.post2", "act1.post3", "act1.post4" }, LampPosts.Board.Select(p => p.Id));
        Assert.Equal(LampPosts.Board.Select(p => (p.Id, p.Zone, p.X, p.Z, p.Draft)), Lamps.Posts.Select(p => (p.Id, p.Zone, p.X, p.Z, p.Draft)));
        Assert.All(LampPosts.All, p => Assert.Equal(p.Dark, p.Board));
        var door = Assert.Single(LampPosts.All, p => p.Door);
        Assert.Equal(("lowford", "checkpoint"), (door.Zone, door.Kind));
        Assert.True(LampPosts.Get("waystation.square")!.Town);
        Assert.Single(LampPosts.In("verge"));
        // Each post's lantern is a light of its zone, where the post stands.
        foreach (var p in LampPosts.All.Where(p => p.Light >= 0))
        {
            var l = ZoneMeta.Load(p.Zone).Lights[p.Light];
            Assert.True(Math.Abs(l.X - p.X) < 0.1 && Math.Abs(l.Z - p.Z) < 0.1, $"{p.Id}'s light {p.Light} stands at ({l.X:0.00},{l.Z:0.00})");
        }
    }

    [Fact]
    public void A_checkpoint_post_gives_no_board_point_and_a_dark_one_gives_one()
    {
        Lamps.UseV2(true);
        var j = New();
        var w = j.World;
        int before = LampBook.Earned(j.Ch, w);
        Assert.True(LampBook.LightPost(w, "lowford.watch"));
        Assert.False(LampBook.LightPost(w, "lowford.watch"));
        Assert.True(LampBook.PostLit(w, "lowford.watch"));
        Assert.Equal(before, LampBook.Earned(j.Ch, w));
        Assert.Equal("lowford.watch", LampBook.LastPost(w, "lowford")!.Id);
        Assert.True(LampBook.LightPost(w, "act1.post1"));
        Assert.Equal(before + 1, LampBook.Earned(j.Ch, w));
        Assert.Equal("act1.post1", LampBook.LastPost(w, "lowford")!.Id);
        // A town's post burns from the start, and gives nothing.
        Assert.True(LampBook.PostLit(w, "waystation.square"));
        Assert.False(LampBook.LightPost(w, "waystation.square"));
        Assert.Equal(before + 1, LampBook.Earned(j.Ch, w));
        Assert.Null(LampBook.LastPost(w, "verge"));
    }

    [Fact]
    public void Fallen_after_lighting_the_watch_post_she_rises_there_and_what_she_killed_stays_dead()
    {
        var j = New();
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5, ember: zone.Ember);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        var post = LampPosts.Get("lowford.watch")!;
        // Dark until lit; not to be lit before the Barrow Knight is down. The door's post can be.
        Assert.False(host.FakeLook.IsLit(post.Light));
        Assert.False(zone.Interactables.Single(i => i.Id == "lamppost:lowford.watch").When!());
        Assert.True(zone.Interactables.Single(i => i.Id == "lamppost:lowford.door").When!());
        Assert.True(LampRise.Light(host, b, post));
        Assert.True(host.FakeLook.IsLit(post.Light));

        var champ = b.SpawnEnemy("barrow_knight", 0, 0, new Battle.SpawnOpts { Elite = true })!;
        champ.Hp = 1;
        var near = b.SpawnEnemy("risen", post.X + 5, post.Z, new Battle.SpawnOpts())!;
        var killed = b.SpawnEnemy("risen", 2, 2, new Battle.SpawnOpts())!;
        b.KillEnemy(killed, true, null);
        j.World.Zone("lowford")[Encounters.DoneKey("n_lone")] = true;
        double gold = j.Ch.Gold, xp = j.Ch.Xp;
        int level = j.Ch.Level;

        Assert.True(zone.OnDeath("the dead"));
        b.Player.Alive = false;
        host.Pass(3);
        Assert.True(b.Player.Alive);
        Assert.Equal(b.MaxHp, b.Player.Hp);
        Assert.Equal((post.X, post.Z), host.Revival);
        Assert.Equal((post.X, post.Z), (b.Player.X, b.Player.Z));
        Assert.Equal(champ.MaxHp, champ.Hp);
        Assert.True(near.Alive);   // (nothing is cleared round her: ClearAround is gone)
        Assert.True(!killed.Alive || killed.State == EnemyState.Dying);   // (and it is not raised: dead stays dead)
        Assert.True(j.World.Zone("lowford")[Encounters.DoneKey("n_lone")].Truthy);
        Assert.Equal(1, LampRise.Toll(j.World));
        Assert.Equal((gold, xp, level), (j.Ch.Gold, j.Ch.Xp, j.Ch.Level));
        Assert.Contains("The ember will not let you go so easily.", host.Said);
        // The next rise has the narrator's words, and the toll counts it.
        Assert.True(zone.OnDeath("the dead"));
        host.Pass(3);
        Assert.Equal(2, LampRise.Toll(j.World));
        Assert.Contains(Journey.DayLines.RiseAgain, host.Said);
    }

    static (Journey J, FakeHost Host, Verge Zone, Battle B) MakeVerge()
    {
        var j = New();
        j.World.Time = TimeOfDay.Dawn;
        j.World.Clock = 0;
        j.Apply("""[{ "quest": { "id": "beasts", "status": "active" } }]""");
        var meta = ZoneMeta.Load("verge");
        var host = new FakeHost(j, meta);
        var zone = new Verge(host, meta);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 11);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return (j, host, zone, b);
    }

    [Fact]
    public void In_the_verge_she_rises_at_its_post_and_is_never_carried_to_the_waystation()
    {
        var (j, host, zone, b) = MakeVerge();
        var post = LampPosts.In("verge").Single();
        var entry = zone.ArrivalFrom("waystation");
        // Before its post: up again at the entry.
        Assert.True(zone.OnDeath("a wolf"));
        host.Pass(3);
        Assert.Equal((entry.X, entry.Z), host.Revival);
        var light = zone.Interactables.Single(i => i.Id == "lamppost:verge.entry");
        Assert.True(light.When!());
        light.Act();
        Assert.True(LampBook.PostLit(j.World, post.Id));
        Assert.False(light.When!());
        b.Player.X = 40; b.Player.Z = 40;
        Assert.True(zone.OnDeath("a wolf"));
        host.Pass(3);
        Assert.Equal((post.X, post.Z), host.Revival);
        Assert.Null(host.Travelled);
        Assert.Equal(2, LampRise.Toll(j.World));
        Assert.Contains(Journey.DayLines.Rise, host.Said);
        Assert.Contains(Journey.DayLines.RiseAgain, host.Said);
    }

    static Prologue Day(Journey j, string? from)
    {
        j.World.Facts["prologue.done"] = true;
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta);
        // (a travel asks the zone where she arrives from; a load arrives where it was saved and never asks)
        if (from != null) zone.ArrivalFrom(from);
        var b = j.StartBattle(true, meta.Collision(), (_, _) => 0, 0, -100, 0, 9);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return zone;
    }

    [Fact]
    public void Coming_back_from_another_zone_resets_the_days_packs_and_a_load_does_not()
    {
        Lamps.UseV2(true);
        var j = New();
        j.World.Zone("lowford")[Encounters.DoneKey("boars")] = true;
        Day(j, null);
        Assert.True(j.World.Zone("lowford")[Encounters.DoneKey("boars")].Truthy);
        Day(j, "lowford");
        Assert.True(j.World.Zone("lowford")[Encounters.DoneKey("boars")].Truthy);
        LampBook.LightPost(j.World, "act1.post1");
        Day(j, "waystation");
        Assert.False(j.World.Zone("lowford").ContainsKey(Encounters.DoneKey("boars")));
        // The lamps are world facts: never reset.
        Assert.True(LampBook.PostLit(j.World, "act1.post1"));
        Assert.Equal("act1.post1", LampBook.LastPost(j.World, "lowford")!.Id);
    }

    [Fact]
    public void By_day_a_post_lit_on_the_nights_side_of_the_river_is_left_behind()
    {
        var j = New();
        LampBook.LightPost(j.World, "lowford.door");
        Day(j, null);
        Assert.Null(LampBook.LastPost(j.World, "lowford"));
        LampBook.LightPost(j.World, "lowford.bank");
        LampBook.SetLastPost(j.World, "lowford", "lowford.door");
        Day(j, null);
        Assert.Equal("lowford.bank", LampBook.LastPost(j.World, "lowford")!.Id);
    }
}
