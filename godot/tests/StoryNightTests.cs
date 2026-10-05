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

/// <summary>A story night (docs/design/STORY_BOSSES.md; Play/Zones/StoryNight.cs): stages ended by
/// their goals and never by a clock, a checkpoint at each, one rise in Act 1, and a boss whose
/// floors hold and whose end is the story's. The Hollow by Night is the template.</summary>
[Collection("Balance")]
public class StoryNightTests
{
    internal sealed record Night(Journey J, HeadlessHost Host, StoryNight Zone, Battle B, ArenaSpec Spec);

    internal static Night Hollow(int seed = 3, int tier = 1, Action<Journey>? before = null, bool unarmed = false)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        before?.Invoke(j);
        var spec = StoryFights.Spec("hollow", j.Ctx, "verge", 0, 0, 0);
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
        return new Night(j, host, zone, b, spec);
    }

    internal static void Step(Night n, double seconds, bool keep = true, Action<double>? each = null, Func<bool>? until = null)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            n.Zone.Step(1 / 60.0);
            n.Zone.Frame(1 / 60.0);
            n.B.Tick(1 / 60.0, 0, 0);
            n.B.Events.Drain();
            n.Host.Pass(1 / 60.0);
            n.B.PendingLevels = 0; n.B.PendingBlessings.Clear(); n.B.GreatOwed = 0;
            if (keep) n.B.Player.Hp = n.B.MaxHp;
            each?.Invoke(t);
            if (n.Host.Result != null || until?.Invoke() == true) return;
        }
    }

    static Enemy? Named(Night n) => n.B.Enemies.Items.FirstOrDefault(e => e.Alive && e.Named != null && !e.Boss && e.State != EnemyState.Dying);

    [Fact]
    public void She_comes_in_at_the_clough_with_its_gate_shut()
    {
        var n = Hollow();
        var p = n.B.Player;
        var (sx, sz) = HollowByNight.Ground["start"];
        Assert.True(Math.Abs(p.X - sx) < 0.01 && Math.Abs(p.Z - sz) < 0.01);
        var g = HollowByNight.Ground.Gates[0];
        Assert.True(n.B.Collision.Blocked((g.X0 + g.X1) / 2, (g.Z0 + g.Z1) / 2, 0.5));
        Assert.Equal(StoryNight.Stage.Beat, n.Zone.Now);
        Assert.Equal("Silence Old Blue", n.Zone.Beat!.Goal);
        // Old Blue is on the bar from the first second.
        Step(n, 0.5);
        Assert.Equal("Old Blue", n.Host.Boss?.Name);
    }

    /// <summary>The place holds her: walking and dashing every way from each stage's start, she never
    /// leaves it (a wall a dash went through left a bot outside, its fire out of reach).</summary>
    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void The_place_holds_her_walking_and_dashing(int stage)
    {
        for (int k = 0; k < 16; k++)
        {
            var n = Hollow(unarmed: true);
            n.Zone.SkipTo(stage);
            foreach (var e in n.B.Enemies.Living().ToList()) n.B.Enemies.Release(e);
            double mx = Math.Cos(k * Math.PI / 8), mz = Math.Sin(k * Math.PI / 8);
            var p = n.B.Player;
            for (int i = 0; i < 60 * 8; i++)
            {
                if (i % 30 == 0) { p.DashCharges = 2; n.B.Dash(mx, mz); }
                n.B.Tick(1 / 60.0, mx, mz);
                n.B.Events.Drain();
                Assert.True(HollowByNight.Ground.Inside(p.X, p.Z, -0.6), $"stage {stage}, bearing {k}: out at ({p.X:0.0}, {p.Z:0.0})");
            }
        }
    }

    /// <summary>Each stage's goal can be walked to from where the stage before left her: the bots'
    /// way (the harness's NavField) finds it through the opened gates.</summary>
    [Fact]
    public void Every_stage_can_be_walked_to()
    {
        var n = Hollow(unarmed: true);
        var g = HollowByNight.Ground;
        n.Zone.SkipTo(1);
        var map = MapGen.Generate(n.Spec.Map);
        foreach (var (from, to) in new[] { ("rock", "fire:a"), ("rock", "fire:b"), ("head_w", "water_in"), ("start", "fire:b") })
        {
            var nav = new NavField(map, n.B, g[to].X, g[to].Z, g.Bounds());
            Assert.False(double.IsNaN(nav.ToGo(g[from].X, g[from].Z)), $"{from} to {to}");
        }
        n.Zone.SkipTo(2);
        foreach (var (from, to) in new[] { ("fire:a", "den"), ("water_in", "den_n"), ("rock", "den_mouth") })
        {
            var nav = new NavField(map, n.B, g[to].X, g[to].Z, g.Bounds());
            Assert.False(double.IsNaN(nav.ToGo(g[from].X, g[from].Z)), $"{from} to {to}");
        }
    }

    /// <summary>No clock: hands that do nothing never finish a stage.</summary>
    [Fact]
    public void A_stage_ends_on_its_goal_never_on_a_clock()
    {
        var n = Hollow(unarmed: true);
        Step(n, 150);
        Assert.Equal(0, n.Zone.BeatIx);
        Assert.Equal(StoryNight.Stage.Beat, n.Zone.Now);
    }

    [Fact]
    public void Old_Blue_down_opens_the_clough_and_the_next_stage_begins_after_the_quiet()
    {
        var n = Hollow(unarmed: true);
        Step(n, 0.5);
        var blue = Named(n)!;
        Assert.Equal("mb_caller", blue.Def.Id);
        n.B.KillEnemy(blue, true, null);
        Step(n, 0.5);
        Assert.Equal(StoryNight.Stage.Between, n.Zone.Now);
        var g = HollowByNight.Ground.Gates[0];
        Assert.False(n.B.Collision.Blocked((g.X0 + g.X1) / 2, (g.Z0 + g.Z1) / 2, 0.5));
        Step(n, 7);
        Assert.Equal(1, n.Zone.BeatIx);
        Assert.Equal(StoryNight.Stage.Beat, n.Zone.Now);
        Assert.Single(n.Zone.Log);
    }

    [Fact]
    public void Old_Blues_howl_is_broken_by_fire()
    {
        var n = Hollow(unarmed: true);
        Step(n, 0.5);
        var blue = Named(n)!;
        Step(n, 7, until: () => n.Host.Boss?.Channel != null);
        Assert.NotNull(n.Host.Boss?.Channel);
        n.B.HitEnemy(blue, 1, School.Fire, [Tag.Fire], new HitOpts { NoCrit = true });
        Step(n, 0.2);
        Assert.Null(n.Host.Boss?.Channel);
        Assert.Equal(EnemyState.Stunned, blue.State);
    }

    [Fact]
    public void Standing_at_a_deadfall_lights_it_and_the_Pack_keeps_out_of_its_light()
    {
        var n = Hollow(unarmed: true);
        n.Zone.SkipTo(1);
        var f = n.Zone.Fires.First(x => x.Id == "fire:a");
        var p = n.B.Player;
        p.X = f.X + 1; p.Z = f.Z;
        Step(n, 2.2);
        Assert.True(f.Burning && f.EverLit);
        var wolf = n.B.SpawnEnemy("wolf_blighted", f.X + 2, f.Z, new Battle.SpawnOpts { Level = 3 })!;
        Step(n, 0.1);
        Assert.True(Math.Sqrt(Math.Pow(wolf.X - f.X, 2) + Math.Pow(wolf.Z - f.Z, 2)) >= f.Reach - 0.3);
    }

    /// <summary>Act 1 gives one rise: back to the stage's start with the build she brought into it
    /// (what she took since is gone), the stage begun again; the next fall loses the night, and a
    /// story night lost wakes her in town.</summary>
    [Fact]
    public void One_rise_in_Act_1_to_the_stage_she_fell_in_then_the_night_is_lost()
    {
        var n = Hollow();
        n.Zone.SkipTo(1);
        string brought = string.Join(",", n.B.Weapons.Select(w => w.Id + w.Rank));
        n.B.AddWeapon("knifestorm", 4);
        n.B.AddBoon("might");
        Step(n, 1, keep: false);
        n.B.HurtPlayer(n.B.MaxHp * 9, School.Physical, "test", null);
        Assert.True(n.B.Player.Alive);
        Step(n, 1.5, keep: false);
        Assert.Equal(1, n.Zone.BeatIx);
        Assert.Equal(brought, string.Join(",", n.B.Weapons.Select(w => w.Id + w.Rank)));
        Assert.False(n.B.Boons.ContainsKey("might"));
        var (sx, sz) = HollowByNight.Ground["water_in"];
        Assert.True(Math.Abs(n.B.Player.X - sx) < 0.5 && Math.Abs(n.B.Player.Z - sz) < 0.5);
        Assert.Equal(1, n.B.Player.Rose);

        n.B.Player.Iframes = 0;
        n.B.HurtPlayer(n.B.MaxHp * 9, School.Physical, "test", null);
        Step(n, 4, keep: false);
        Assert.NotNull(n.Host.Result);
        Assert.False(n.Host.Result!.Won);
        Assert.True(n.Host.Result.WakesInTown);
    }

    [Fact]
    public void Past_Act_1_a_fall_loses_the_night_unless_she_carries_the_rise()
    {
        var n = Hollow(before: j => j.World.Facts["chapter.done"] = true);
        n.B.HurtPlayer(n.B.MaxHp * 9, School.Physical, "test", null);
        Step(n, 4, keep: false);
        Assert.False(n.Host.Result!.Won);

        var held = Hollow(before: j => { j.World.Facts["chapter.done"] = true; j.Ch.Ability = "cold_then_not"; });
        held.B.HurtPlayer(held.B.MaxHp * 9, School.Physical, "test", null);
        Step(held, 2, keep: false);
        Assert.Null(held.Host.Result);
        // Up at half (and mending since).
        Assert.InRange(held.B.Player.Hp, held.B.MaxHp * 0.5 - 1, held.B.MaxHp * 0.6);
        Assert.Equal(0, held.Zone.Falls);
    }

    static Night AtBoss(int tier = 1, Action<Journey>? before = null)
    {
        var n = Hollow(tier: tier, before: before, unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        return n;
    }

    static Enemy Boss(Night n) => n.B.Enemies.Items.First(e => e.Alive && e.Boss);

    [Fact]
    public void Greymuzzle_comes_with_his_ring_and_it_holds_her_in()
    {
        var n = AtBoss();
        var g = Assert.IsType<Greymuzzle>(n.Zone.BossScript);
        Assert.Equal(Greymuzzle.RingWolves, n.B.Enemies.Items.Count(e => e.Alive && e.Scripted && !e.Boss));
        // The ring is never a target.
        Assert.DoesNotContain(n.B.Enemies.Items.Where(e => e.Alive && e.Scripted && !e.Boss), e => n.B.HostileToPlayer(e));
        var (cx, cz) = HollowByNight.Ground["den"];
        var p = n.B.Player;
        p.X = cx + 13.5; p.Z = cz;
        Step(n, 0.1);
        Assert.True(Math.Sqrt(Math.Pow(p.X - cx, 2) + Math.Pow(p.Z - cz, 2)) < 12);
    }

    [Fact]
    public void A_fed_fire_bows_the_ring_out_round_its_light()
    {
        var n = AtBoss();
        var g = (Greymuzzle)n.Zone.BossScript!;
        var (cx, cz) = HollowByNight.Ground["den"];
        var f = n.Zone.Fires.First(x => x.Id == "fire:d");
        double a = Math.Atan2(f.Z - cz, f.X - cx);
        double before = g.RingAt(a);
        f.Lit = 10;
        Assert.True(g.RingAt(a) > before + 3);
    }

    /// <summary>The floors hold for every ending: an absurd build through the game's own wiring still
    /// sees all three phases, about two minutes at the least.</summary>
    [Fact]
    public void An_absurd_build_cannot_skip_him()
    {
        var n = AtBoss();
        var boss = Boss(n);
        double t0 = n.B.Time;
        Step(n, 400, each: _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        }, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.InRange(n.B.Time - t0, 80, 200);
        Assert.Equal("dead", n.J.World.Fact("greymuzzle").Str);
        // Arena changes end with the fight: no wolf of the ring is left standing for it.
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.Scripted);
    }

    /// <summary>Where the story offers it, his end is her choice: let go (and he walks to his den), or
    /// finished. The outcome is the one she chose.</summary>
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Where_she_promised_she_chooses_his_end(bool letGo)
    {
        var n = AtBoss(before: j =>
        {
            j.World.Facts["promise.pack"] = true;
            j.World.Facts["stream.clear"] = true;
        });
        n.Spec.OnSpare = """[{ "set": { "greymuzzle": "spared" } }]""";
        n.Spec.OnWin = """[{ "set": { "greymuzzle": "dead", "promise.broken": true } }]""";
        var boss = Boss(n);
        Step(n, 400, each: _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        }, until: () => n.Zone.Interactables.Any(i => i.Id == "story:let_go"));
        var choice = n.Zone.Interactables.First(i => i.Id == (letGo ? "story:let_go" : "story:finish"));
        Assert.Equal("Let him go", n.Zone.Interactables.First(i => i.Id == "story:let_go").Verb);
        choice.Act();
        Step(n, 12, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.Equal(letGo ? "spared" : "dead", n.J.World.Fact("greymuzzle").Str);
        Assert.Equal(!letGo, n.J.World.Fact("promise.broken").Truthy);
        Assert.Empty(n.Zone.Interactables.Where(i => i.Id.StartsWith("story:")));
    }

    [Fact]
    public void His_moon_howl_brings_the_cold_and_a_fed_fire_keeps_it_off()
    {
        var n = AtBoss();
        var g = (Greymuzzle)n.Zone.BossScript!;
        var boss = Boss(n);
        // To the Moon: his health to its mark, past the floor.
        Step(n, 120, each: _ =>
        {
            if (g.PhaseIx == 0 && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.01, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        }, until: () => g.Channel != null);
        Assert.Equal(1, g.PhaseIx);
        Assert.NotNull(g.Channel);
        var p = n.B.Player;
        var f = n.Zone.Fires.First(x => x.Id == "fire:c");
        f.Lit = 30;
        var (cx, cz) = HollowByNight.Ground["den"];
        // In the fire's light: no cold.
        p.X = f.X; p.Z = f.Z;
        double taken = n.B.DamageTaken;
        Step(n, 3, keep: false, each: _ => { p.X = f.X; p.Z = f.Z; p.Iframes = 0; n.B.CancelBlows(); });
        Assert.Equal(taken, n.B.DamageTaken, 3);
        // Out of it, as the cold closes, it bites.
        f.Lit = 0;
        Step(n, 3, keep: false, each: _ => { p.X = cx + 9; p.Z = cz; p.Iframes = 0; n.B.CancelBlows(); });
        Assert.True(n.B.DamageTaken > taken);
    }

    [Fact]
    public void A_rise_at_the_boss_begins_him_again_and_she_is_whole()
    {
        var n = AtBoss();
        var first = Boss(n);
        Step(n, 5);
        n.B.Player.Hp = 1;
        n.B.Player.Iframes = 0;
        n.B.HurtPlayer(n.B.MaxHp * 9, School.Physical, "test", null);
        Step(n, 1.5, keep: false);
        var again = Boss(n);
        Assert.Equal(n.B.MaxHp, n.B.Player.Hp, 1);
        Assert.Equal(0, ((Greymuzzle)n.Zone.BossScript!).PhaseIx);
        Assert.Equal(again.MaxHp, again.Hp, 1);
        Assert.Equal(Greymuzzle.RingWolves, n.B.Enemies.Items.Count(e => e.Alive && e.Scripted && !e.Boss));
    }

    [Fact]
    public void A_story_night_is_paid_for_its_own_minutes()
    {
        var spec = new ArenaSpec { Id = "hollow_by_night", Story = true, Minutes = 20, Tier = 1 };
        var table = new ArenaSpec { Id = "table:1", Minutes = 30, Tier = 1 };
        Assert.Equal(Arenas.XpFor(table, 12 * 60, false), Arenas.XpFor(spec, 12 * 60, false));
    }
}
