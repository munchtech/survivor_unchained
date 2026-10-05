using System;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Raid on the Roost by night (docs/design/STORY_BOSSES.md 2; Play/Story/Roost.cs and
/// Play/Bosses/Redcowl.cs): the pickets on the lips, the locks that give to the one who stands by them,
/// the levy in step with its captain behind it, the crates by a prompt only, and Redcowl at his knee.</summary>
[Collection("Balance")]
public class RoostTests
{
    static StoryNightTests.Night Roost(int seed = 3, int tier = 1, Action<Journey>? before = null, bool unarmed = false)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        before?.Invoke(j);
        var spec = StoryFights.Spec("roost", j.Ctx, "verge", 0, 0, 0);
        spec.Tier = tier;
        Arenas.Begin(j.World, spec);
        var map = MapGen.Generate(spec.Map);
        var host = new HeadlessHost(j, seed);
        var zone = new StoryNight(host, map, spec, StoryScripts.For(spec.Id)!);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed, arena: true, ember: true);
        b.Hooks = BattleHooks.Following(zone.Hooks);
        host.Battle = b;
        if (unarmed) foreach (var w in b.Weapons.ToList()) b.RemoveWeapon(w.Id);
        zone.Begin(b);
        b.GreatOwed = 0;
        return new StoryNightTests.Night(j, host, zone, b, spec);
    }

    static void Step(StoryNightTests.Night n, double seconds, bool keep = true, Action<double>? each = null, Func<bool>? until = null) =>
        StoryNightTests.Step(n, seconds, keep, each, until);

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    [Fact]
    public void The_Roost_is_written_and_she_comes_in_at_the_foot_of_the_ruts()
    {
        Assert.True(StoryScripts.Has("roost_raid"));
        var n = Roost();
        var (sx, sz) = RaidOnTheRoost.Ground["start"];
        Assert.True(Dist(n.B.Player.X, n.B.Player.Z, sx, sz) < 0.1);
        Assert.StartsWith("Break the pincer", n.Zone.Beat!.Goal);
    }

    /// <summary>Walking and dashing every way from each stage's start (and the boss's), she never leaves
    /// the place.</summary>
    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void The_place_holds_her_walking_and_dashing(int stage)
    {
        for (int k = 0; k < 16; k++)
        {
            var n = Roost(unarmed: true);
            n.Zone.SkipTo(stage);
            foreach (var e in n.B.Enemies.Living().ToList()) n.B.Enemies.Release(e);
            double mx = Math.Cos(k * Math.PI / 8), mz = Math.Sin(k * Math.PI / 8);
            var p = n.B.Player;
            for (int i = 0; i < 60 * 8; i++)
            {
                if (i % 30 == 0) { p.DashCharges = 2; n.B.Dash(mx, mz); }
                n.B.Tick(1 / 60.0, mx, mz);
                n.B.Events.Drain();
                Assert.True(RaidOnTheRoost.Ground.Inside(p.X, p.Z, -0.6), $"stage {stage}, bearing {k}: out at ({p.X:0.0}, {p.Z:0.0})");
            }
        }
    }

    [Fact]
    public void Every_stage_can_be_walked_to()
    {
        var n = Roost(unarmed: true);
        var g = RaidOnTheRoost.Ground;
        var map = MapGen.Generate(n.Spec.Map);
        n.Zone.SkipTo(3);
        foreach (var (from, to) in new[] { ("start", "cage_3"), ("picket_c", "cage_1"), ("yard_in", "camp"), ("store", "crates"), ("cage_2", "levy") })
        {
            var nav = new NavField(map, n.B, g[to].X, g[to].Z, g.Bounds());
            Assert.False(double.IsNaN(nav.ToGo(g[from].X, g[from].Z)), $"{from} to {to}");
        }
    }

    /// <summary>A picket on the lip is out of her reach (not a target, nothing hurts him) until his pincers
    /// are broken; then he comes down to her.</summary>
    [Fact]
    public void A_picket_is_out_of_reach_on_the_lip_until_his_pincers_are_broken()
    {
        var n = Roost(unarmed: true);
        Step(n, 0.8);
        var picket = n.B.Enemies.Items.First(e => e.Alive && e.Named?.Title == "Kerchief Picket");
        Assert.False(n.B.HostileToPlayer(picket));
        Assert.Equal(0, picket.TakenMul);
        // Three of his whistles, each pincer broken as it comes.
        for (int k = 0; k < 4 && !n.B.HostileToPlayer(picket); k++)
            Step(n, 9, each: _ =>
            {
                foreach (var e in n.B.Enemies.Living().Where(e => e.Def.Id == "footpad" && e.Named == null).ToList()) n.B.KillEnemy(e, true, null);
            }, until: () => n.B.HostileToPlayer(picket));
        Assert.True(n.B.HostileToPlayer(picket));
        Assert.Equal(1, picket.TakenMul);
    }

    /// <summary>A lock gives to the one who stands by it, never to a shot from across the yard, and not
    /// while Barn-Door stands in front of it. The last frees the teamsters, as by day.</summary>
    [Fact]
    public void The_locks_give_to_the_one_who_stands_by_them_and_the_last_frees_the_teamsters()
    {
        var n = Roost(unarmed: true);
        n.Zone.SkipTo(1);
        var door = n.B.Enemies.Items.First(e => e.Alive && e.Def.Id == "mb_barn_door");
        var p = n.B.Player;
        var (cx, cz) = RaidOnTheRoost.Ground["cage_1"];
        // Standing across the yard: nothing gives.
        Step(n, 12, each: _ => { foreach (var e in n.B.Enemies.Living().Where(e => e != door && e.Disposition == Disposition.Hostile).ToList()) n.B.Enemies.Release(e); });
        Assert.StartsWith("Break the cage locks (0 of 3)", n.Zone.Beat!.Goal);
        // At the lock, with him in front of it: nothing gives.
        Step(n, 12, each: _ => { p.X = cx + 1; p.Z = cz; door.X = cx - 1; door.Z = cz; });
        Assert.StartsWith("Break the cage locks (0 of 3)", n.Zone.Beat!.Goal);
        // Him gone: each lock gives to her standing at it.
        n.B.KillEnemy(door, true, null);
        foreach (var c in new[] { "cage_1", "cage_2", "cage_3" })
        {
            var (x, z) = RaidOnTheRoost.Ground[c];
            Step(n, 11, each: _ => { p.X = x + 1; p.Z = z; });
        }
        Assert.Equal("rescued", n.J.World.Fact("caravan.survivors").Str);
        Step(n, 1);
        Assert.Equal(StoryNight.Stage.Between, n.Zone.Now);
    }

    /// <summary>The levy is a locked line: its middle is not a target, its ends are. Through it, little
    /// reaches the Pike-Captain behind.</summary>
    [Fact]
    public void The_levy_is_a_locked_line_with_breakable_ends_and_the_captain_behind_it()
    {
        var n = Roost(unarmed: true);
        n.Zone.SkipTo(2);
        Step(n, 0.5);
        var pikes = n.B.Enemies.Items.Where(e => e.Alive && e.Def.Id == "levy_pike" && e.Scripted).ToList();
        Assert.True(pikes.Count >= 7);
        Assert.Equal(2, pikes.Count(e => n.B.HostileToPlayer(e)));
        var captain = n.B.Enemies.Items.First(e => e.Alive && e.Def.Id == "mb_pike_captain");
        // From in front of the line, she is screened: he takes a fraction.
        var p = n.B.Player;
        var (lx, lz) = RaidOnTheRoost.Ground["levy"];
        Step(n, 0.2, each: _ => { p.X = captain.X + (lx - captain.X) * 3; p.Z = captain.Z + (lz - captain.Z) * 3; });
        Assert.True(captain.TakenMul < 0.5, $"taken {captain.TakenMul}");
    }

    /// <summary>A fire build standing by the crates does not blow them; the prompt does, and then the line
    /// breaks and the crates are gone from the story (be.crates = burned).</summary>
    [Fact]
    public void The_crates_go_up_only_by_their_prompt()
    {
        var n = Roost();
        n.Zone.SkipTo(2);
        var p = n.B.Player;
        var (cx, cz) = RaidOnTheRoost.Ground["crates"];
        n.B.AddWeapon("cinderfall", 6);
        Step(n, 8, each: _ => { p.X = cx + 2; p.Z = cz; });
        Assert.True(n.J.World.Fact("be.crates").IsNull);
        var prompt = n.Zone.Interactables.First(i => i.Id == "story:crates");
        prompt.Act();
        Step(n, 3.5, each: _ => { p.X = cx + 20; p.Z = cz; });
        Assert.Equal("burned", n.J.World.Fact("be.crates").Str);
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.State != EnemyState.Dying && e.Def.Id == "levy_pike" && e.Scripted);
    }

    static Enemy Boss(StoryNightTests.Night n) => n.B.Enemies.Items.First(e => e.Alive && e.Boss);

    /// <summary>The floors hold: an absurd build still sees all three of his phases.</summary>
    [Fact]
    public void An_absurd_build_cannot_skip_Redcowl()
    {
        var n = Roost(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        Assert.IsType<Redcowl>(n.Zone.BossScript);
        double t0 = n.B.Time;
        Step(n, 400, each: _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            if (n.Zone.Choice != null) n.Zone.Answer("finish");
        }, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.InRange(n.B.Time - t0, 80, 220);
        Assert.Equal("dead", n.J.World.Fact("redcowl").Str);
        // His people go with him: no watcher, cart or post is left standing.
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.Scripted);
        Assert.Empty(n.B.Collision.ByTag("carts").Concat(n.B.Collision.ByTag("cage")));
    }

    /// <summary>At his knee, the owner's choice: spare him, or finish it. It is put to her wherever she stands,
    /// named; the outcome is the one she chose.</summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void At_his_knee_she_spares_him_or_finishes_it(bool spare)
    {
        var n = Roost(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        Step(n, 400, each: _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        }, until: () => n.Zone.Choice != null);
        var c = n.Zone.Choice!;
        Assert.Equal("Redcowl", c.Who);
        Assert.Equal("Spare him, or finish it", c.Title);
        Assert.Equal(["Spare him", "Finish it"], c.Answers.Select(a => a.Verb));
        // Nothing near him to walk to: the choice is answered from anywhere.
        Assert.Empty(n.Zone.Interactables.Where(i => i.Id.StartsWith("story:")));
        // Left waiting, it waits, and his lot keep back from her.
        Step(n, 20);
        Assert.Same(c, n.Zone.Choice);
        Assert.False(n.Zone.Won);
        Assert.Empty(n.B.Enemies.Living().Where(e => !e.Scripted && e.State != EnemyState.Dying && n.B.HostileToPlayer(e) && !e.Status.Has(StatusKind.Fear)).Select(e => $"{e.Def.Id} {e.State} {e.Disposition} at ({e.X:0},{e.Z:0})"));
        n.Zone.Answer(spare ? "let_go" : "finish");
        Assert.Null(n.Zone.Choice);
        Step(n, 12, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.Equal(spare ? "spared" : "dead", n.J.World.Fact("redcowl").Str);
    }

    /// <summary>The cage: ten posts round her with one gap facing him. A post gives to her standing by it
    /// from inside, and the cage is gone after its eight seconds.</summary>
    [Fact]
    public void His_cage_gives_at_the_post_she_stands_by()
    {
        var n = Roost(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var rc = (Redcowl)n.Zone.BossScript!;
        // To Forty-One Mouths.
        Step(n, 200, each: _ =>
        {
            if (rc.PhaseIx == 0 && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.01, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        }, until: () => rc.InCage);
        Assert.True(rc.InCage);
        Assert.Equal(10, n.B.Collision.ByTag("cage").Count);
        var post = rc.Posts.OrderByDescending(q => Dist(q.X, q.Z, rc.Door.X, rc.Door.Z)).First();
        var p = n.B.Player;
        var (cx, cz) = rc.CageAt;
        Step(n, 1.6, each: _ => { p.X = post.X + (cx - post.X) * 0.25; p.Z = post.Z + (cz - post.Z) * 0.25; n.B.CancelBlows(); });
        Assert.True(post.Broken);
        Assert.Equal(9, n.B.Collision.ByTag("cage").Count);
        Step(n, 9, each: _ => n.B.CancelBlows());
        Assert.Empty(n.B.Collision.ByTag("cage"));
    }

    /// <summary>On the boss's ground, the way back shuts behind her (a fight that drifts back down the way
    /// in never ends).</summary>
    [Fact]
    public void The_way_back_shuts_behind_her_on_his_ground()
    {
        var n = Roost(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.3);
        var g = RaidOnTheRoost.Ground.Gates.First(x => x.Into == "fire");
        Assert.True(n.B.Collision.Blocked((g.X0 + g.X1) / 2, (g.Z0 + g.Z1) / 2, 0.5));
    }
}
