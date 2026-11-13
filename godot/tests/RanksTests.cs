using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>bd-ranks (docs/design/BUILD_DIRECTION.md "Progression", BUILD_UNLOCKS.md): the level cap of 75, each level slower
/// than the last, Act 1 still ending near level 12; a lamp a level to the cap; and the road as the early subclass, chosen at
/// level 6 and changed at any lamp-post.</summary>
[Collection("Balance")]
public sealed class RanksTests
{
    static CreationChoice Choice(string calling = "warden", string type = "")
    {
        var a = Callings.Archetype(calling);
        return new CreationChoice { Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0], Type = type };
    }

    static Journey Begin(string calling = "warden", string type = "") => Journey.Begin(Choice(calling, type), 7);

    /// <summary>Experience to the next level, through the journey's own path (Learn: what a kill or a stone pays).</summary>
    static void LevelTo(Journey j, int level)
    {
        while (j.Ch.Level < level) j.Learn(Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
    }

    /* ------------------------------------------------------------ levels -- */

    [Fact]
    public void The_cap_is_75_and_it_is_reached()
    {
        Assert.Equal(75, Character.MaxLevel);
        var ch = Character.Create(Choice(), seed: 7);
        int guard = 0;
        while (ch.Level < Character.MaxLevel && guard++ < 1000) Character.GainXp(ch, Character.XpForLevel(ch.Level) - ch.Xp + 1);
        Assert.Equal(75, ch.Level);
        Assert.Equal(0, ch.Xp);
        Assert.Equal(0, Character.GainXp(ch, 1e9));
        Assert.Equal(75, ch.Level);
    }

    [Fact]
    public void Every_level_is_slower_than_the_last()
    {
        for (int l = 2; l < Character.MaxLevel; l++)
        {
            // More experience each level...
            Assert.True(Character.XpForLevel(l) > Character.XpForLevel(l - 1), $"level {l} asks no more than {l - 1}");
            // ...and more kills of foes her own level each level: the curve outgrows what a foe of her level pays.
            double kills(int x) => Character.XpForLevel(x) / Enemies.ScaleFor(x).Xp;
            Assert.True(kills(l) > kills(l - 1), $"level {l} takes no more kills than {l - 1}");
        }
    }

    [Fact]
    public void The_first_twelve_levels_cost_what_they_did()
    {
        // (the curve before the cap went to 75: 120 L^1.55; reaching level 12 costs the same, so Act 1 ends where it did)
        for (int l = 1; l < 12; l++) Assert.Equal(MathX.Round(120 * Math.Pow(l, 1.55)), Character.XpForLevel(l));
        Assert.True(Character.XpForLevel(12) > MathX.Round(120 * Math.Pow(12, 1.55)));
    }

    /// <summary>Act 1 in the harness's measure (ARPG.md 7.1's hours, the measured Low Ford): the first hour's 500 kills bring her to
    /// level 5 (the zone sim's gate: 4-5, median 4.5), and four Act 1 hours of 700 kills a foe of her level follow. The per-kill
    /// experience is calibrated on that first hour; she ends Act 1 at 11 to 13, before any boss's or quest's experience.</summary>
    [Fact]
    public void Act_1_ends_near_level_12()
    {
        double cost(int to) => Enumerable.Range(1, to - 1).Sum(Character.XpForLevel);
        double per = cost(5) / 500 / Enemies.ScaleFor(3).Xp;
        int level = 1; double xp = 0;
        void Gain(double x) { xp += x; while (xp >= Character.XpForLevel(level)) { xp -= Character.XpForLevel(level); level++; } }
        for (int k = 0; k < 500; k++) Gain(per * Enemies.ScaleFor(Math.Min(level, 5)).Xp);
        Assert.Equal(5, level);
        for (int k = 0; k < 4 * 700; k++) Gain(per * Enemies.ScaleFor(level).Xp);
        Assert.InRange(level, 11, 13);
    }

    [Fact]
    public void Traits_stop_at_the_old_cap()
    {
        var ch = Character.Create(Choice(), seed: 7);
        while (ch.Level < Character.MaxLevel) Character.GainXp(ch, Character.XpForLevel(ch.Level) - ch.Xp + 1);
        Assert.Equal(Character.LastTraitLevel / 2, ch.TraitPicks);
        Assert.True(Callings.Traits.Count >= ch.TraitPicks);
    }

    /* ------------------------------------------------------------- lamps -- */

    [Fact]
    public void At_75_she_has_earned_74_lamps_and_every_story_atlas_and_post_lamp()
    {
        var j = Begin();
        LevelTo(j, Character.MaxLevel);
        var w = j.World;
        Assert.Equal(74, LampBook.Earned(j.Ch, w));
        foreach (var id in Lamps.StoryFights) w.Facts[$"arena.{id}"] = "won";
        w.Facts["lamps.atlas"] = LampBook.AtlasLamps;
        foreach (var p in Lamps.Posts) w.Facts[$"lampposts.{p.Id}"] = true;
        int all = 74 + Lamps.StoryFights.Count + LampBook.AtlasLamps + Lamps.Posts.Count;
        Assert.Equal(all, LampBook.Earned(j.Ch, w));
        // The board can take them all: the lamps a Warden may light (none of another calling's home) past her free ones.
        var free = LampBook.Free(j.Ch);
        int room = Lamps.All.Values.Count(d => !(d.Home && d.Calling != j.Ch.Archetype) && !free.Contains(d.Id));
        Assert.True(room >= all, $"{room} lamps to light for {all} earned");
    }

    /* -------------------------------------------------------------- road -- */

    [Fact]
    public void A_new_survivor_walks_no_road_but_keeps_her_Flare()
    {
        var j = Begin();
        var ch = j.Ch;
        Assert.True(LampBook.Roadless(ch));
        Assert.All(LampBook.State(ch).Layouts, l => Assert.Equal("", l.Type));
        // No road's entry lit; her calling's first Strike is free and carried.
        Assert.DoesNotContain(LampBook.Now(ch).Lit, id => Lamps.Get(id).Kind == LampKind.Entry);
        Assert.Equal(LampBook.FlareRoad(ch).Strike, LampBook.Carried(ch));
        Assert.Equal("the_long_cut", LampBook.Carried(ch));
        // Creation still teaches the calling's first skill (no road needed).
        Assert.Contains("sunder", ch.Skills);
        // No road's lamp can be lit before her road, however many lamps she holds.
        LevelTo(j, 5);
        var road = Lamps.All.Values.First(d => d.Road == "sunderer" && d.Kind != LampKind.Entry && Lamps.Next(d.Id).Any(LampBook.Now(ch).Lit.Contains) && !LampBook.Now(ch).Lit.Contains(d.Id));
        Assert.Equal(LampNo.NoRoad, LampBook.CanLight(ch, j.World, road.Id));
        Assert.Equal(LampNo.NoRoad, LampBook.CanLight(ch, j.World, Lamps.Entry("bulwark")));
        // The hearth's lamps can.
        Assert.Contains(Lamps.All.Values, d => d.Region == LampRegion.Hearth && LampBook.CanLight(ch, j.World, d.Id) == LampNo.None);
        // And she cannot choose yet.
        Assert.False(j.RoadDue);
        Assert.NotNull(j.WalkRoad("bulwark", "waystation"));
        Assert.True(LampBook.Roadless(ch));
    }

    [Fact]
    public void Level_6_raises_the_road_once_and_a_scene_or_a_post_makes_the_choice()
    {
        var j = Begin();
        var said = new List<Announcement>();
        int raised = 0;
        j.OnAnnounce = a => said.Add(a);
        j.OnRoadOpen = () => raised++;
        LevelTo(j, 5);
        Assert.False(j.World.Fact(Journey.RoadOpenFact).Truthy);
        LevelTo(j, 6);
        Assert.True(j.RoadDue);
        Assert.True(j.World.Fact(Journey.RoadOpenFact).Truthy);
        Assert.Equal(1, raised);
        Assert.Contains(said, a => a.Title == "Choose your road");
        LevelTo(j, 7);
        Assert.Equal(1, raised);
        // The post menu offers it first while it waits.
        var post = LampPosts.Board.First();
        j.World.Facts[$"lampposts.{post.Id}"] = true;
        Assert.Equal(PostMenu.Option.Road, PostMenu.Options(j.World, null, post, j.Ch)[0].Option);
        // The story's scene picks it by a fact (here, the Bulwark).
        j.Apply($$"""[{ "set": { "{{Journey.RoadPickFact}}": "bulwark" } }]""");
        Assert.False(j.RoadDue);
        Assert.Equal("bulwark", LampBook.Now(j.Ch).Type);
        Assert.All(LampBook.State(j.Ch).Layouts, l => Assert.Equal("bulwark", l.Type));
        Assert.Equal("bulwark", j.World.Fact(Journey.RoadWalkedFact).Str);
        Assert.False(j.World.Fact(Journey.RoadPickFact).Truthy);
        // Its entry and Strike are lit free; its own skill is hers.
        Assert.Contains(Lamps.Entry("bulwark"), LampBook.Now(j.Ch).Lit);
        Assert.Equal("bell_of_the_morning", LampBook.Carried(j.Ch));
        Assert.Contains(LampBook.RoadSkill(j.Ch, "bulwark")!, j.Ch.Skills);
        Assert.Equal(LampBook.Earned(j.Ch, j.World), LampBook.Spare(j.Ch, j.World));
        // Once walked, the post lists it after the Lamps, as a change.
        var opts = PostMenu.Options(j.World, null, post, j.Ch).Select(o => o.Option).ToList();
        Assert.True(opts.IndexOf(PostMenu.Option.Road) > opts.IndexOf(PostMenu.Option.Rest));
    }

    [Fact]
    public void A_change_at_a_lamp_post_refunds_the_board_and_re_picks_cleanly()
    {
        var j = Begin();
        LevelTo(j, 12);
        Assert.Null(j.WalkRoad("sunderer", null));
        var ch = j.Ch;
        var w = j.World;
        // Spend every lamp she can on the road and the hearth.
        while (LampBook.Spare(ch, w) > 0 && LampBook.Suggest(ch, w) is { } s) Assert.True(LampBook.Light(ch, w, s));
        Assert.True(LampBook.Spent(ch) > 0);
        var other = LampBook.Now(ch).Lit.ToList();
        // Away from a post, by night in the field: refused, nothing changed.
        Assert.NotNull(j.WalkRoad("bulwark", "lowford"));
        Assert.Equal(other, LampBook.Now(ch).Lit);
        // At a lit post: free, the board refunded to the Bulwark's free lamps, its Flare carried.
        var post = LampPosts.Board.First();
        w.Facts[$"lampposts.{post.Id}"] = true;
        Assert.Null(j.WalkRoad("bulwark", post.Zone, post.Id));
        Assert.Equal("bulwark", LampBook.Now(ch).Type);
        Assert.Equal(LampBook.Free(ch).OrderBy(x => x), LampBook.Now(ch).Lit.OrderBy(x => x));
        Assert.Equal(0, LampBook.Spent(ch));
        Assert.Equal(LampBook.Earned(ch, w), LampBook.Spare(ch, w));
        Assert.Equal("bell_of_the_morning", LampBook.Carried(ch));
        Assert.DoesNotContain(Lamps.Entry("sunderer"), LampBook.Now(ch).Lit);
        // Its lamps light again; and back to the Sunderer the same way.
        Assert.NotNull(LampBook.Suggest(ch, w));
        Assert.Null(j.WalkRoad("sunderer", post.Zone, post.Id));
        Assert.Equal("the_long_cut", LampBook.Carried(ch));
        Assert.NotNull(j.WalkRoad("butcher", post.Zone, post.Id)); // another calling's road
    }

    [Fact]
    public void An_old_save_keeps_its_road()
    {
        // A save from before the road's level: a survivor of level 3 walking the Bulwark (the creation screen named it then).
        var j = Begin("warden", "bulwark");
        LevelTo(j, 3);
        var d = new SaveData { Character = j.Ch, World = j.World };
        var back = Saves.Migrate(Json.Parse<SaveData>(Json.Write(d)));
        Assert.Equal("bulwark", LampBook.Now(back.Character).Type);
        Assert.Contains(Lamps.Entry("bulwark"), LampBook.Now(back.Character).Lit);
        Assert.False(Journey.From(back, 0).RoadDue);
        // And a roadless save round-trips roadless.
        var k = Begin();
        var back2 = Saves.Migrate(Json.Parse<SaveData>(Json.Write(new SaveData { Character = k.Ch, World = k.World })));
        Assert.True(LampBook.Roadless(back2.Character));
        Assert.Equal("the_long_cut", LampBook.Carried(back2.Character));
    }

    [Fact]
    public void The_harness_survivor_past_level_6_walks_her_callings_first_road()
    {
        var j = Begin();
        DevVeteran.Dress(j.Ch, 20, 2, 1);
        Assert.Equal(LampBook.DefaultType("warden"), LampBook.Now(j.Ch).Type);
    }
}
