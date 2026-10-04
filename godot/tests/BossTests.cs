using System;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The arena boss's contract (docs/SKILLS_DESIGN.md, "Bosses"; docs/bosses):
/// a boss and not the herald again; phases that gate; enrages; stagger; the
/// best chest; and each people's ruler keeping to its story.</summary>
[Collection("Balance")]
public class BossTests
{
    sealed record Fight(Battle B, ArenaRun Zone, HeadlessHost Host, Journey J);

    /// <summary>An arena of `people` brought to the edge of the half hour, the survivor kept alive.
    /// `game`: the battle's hooks wired as the game wires them (BattleHooks.Following), not shared.</summary>
    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false, string? boss = null, string? bossName = null, bool spare = false)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        var spec = new ArenaSpec { Id = "table:test", Name = "Test", Seed = seed, Tier = tier, People = people, Boss = boss, BossName = bossName, Spare = spare };
        Arenas.Begin(j.World, spec);
        var map = MapGen.Generate(spec.Map);
        var host = new HeadlessHost(j, seed);
        var zone = new ArenaRun(host, map, spec);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed, arena: true);
        b.Hooks = game ? BattleHooks.Following(zone.Hooks) : zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        b.GreatOwed = 0;
        b.Time = 30 * 60 - 0.05;
        Step(new Fight(b, zone, host, j), 0.2);
        return new Fight(b, zone, host, j);
    }

    static void Step(Fight f, double seconds, Action<double>? each = null)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            f.Zone.Step(1 / 60.0);
            f.Zone.Frame(1 / 60.0);
            f.B.Tick(1 / 60.0, 0, 0);
            f.B.Events.Drain();
            f.Host.Pass(1 / 60.0);
            f.B.PendingLevels = 0; f.B.PendingBlessings.Clear(); f.B.GreatOwed = 0;
            f.B.Player.Hp = f.B.MaxHp;
            each?.Invoke(t);
            if (f.Zone.Won) return;
        }
    }

    static Enemy Boss(Fight f) => f.B.Enemies.Items.First(e => e.Alive && e.Boss);

    [Theory]
    [InlineData("pack", typeof(PackMother))]
    [InlineData("dead", typeof(BarrowLord))]
    [InlineData("lamplings", typeof(Grimtunnel))]
    [InlineData("kerchiefs", typeof(RedHand))]
    public void The_half_hour_brings_a_boss_with_its_own_script(string people, Type kind)
    {
        var f = At30(people);
        var boss = Boss(f);
        Assert.True(boss.Boss);
        Assert.IsType(kind, f.Zone.BossScript);
        Assert.True(f.Host.Boss is { IsBoss: true });
        // On the picture: no further than the contract's 12-14 m (it walks in a little).
        Assert.True(Math.Sqrt(Math.Pow(boss.X - f.B.Player.X, 2) + Math.Pow(boss.Z - f.B.Player.Z, 2)) < 16);
    }

    /// <summary>The game copied the zone's hooks when the battle began, before the boss
    /// came, so no boss script ran on screen while every test passed.</summary>
    [Theory]
    [InlineData("pack")]
    [InlineData("kerchiefs")]
    public void The_boss_fights_its_own_fight_in_the_game_too(string people)
    {
        var f = At30(people, game: true);
        var boss = Boss(f);
        var s = f.Zone.BossScript!;
        Step(f, 12, _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) f.B.HitEnemy(boss, boss.MaxHp * 0.002, School.Fire, [Tag.Fire], new HitOpts { NoCrit = true });
        });
        Assert.True(s.FightT > 10);
        Assert.True(boss.HpFloor > 0);
        // A stagger reaches the script through the game's hooks.
        for (int i = 0; i < 12 && boss.StaggeredT <= 0; i++) f.B.ApplyStatus(boss, new StatusPayload(StatusKind.Stun, 1, 1, 2), 10);
        Assert.True(boss.StaggeredT > 0);
    }

    /// <summary>A channel broken from inside its own move (the howl hurt enough) ended the
    /// move under the script's feet, and the next tick threw (the sweep found it).</summary>
    [Fact]
    public void Her_howl_hurt_short_stops_cleanly()
    {
        var f = At30("pack");
        var boss = Boss(f);
        var s = f.Zone.BossScript!;
        for (int i = 0; i < 60 * 90 && s.Channel == null; i++)
            Step(f, 1 / 60.0, _ => { if (s.PhaseIx == 0 && boss.TakenMul > 0) f.B.HitEnemy(boss, boss.MaxHp * 0.01, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); });
        Assert.Equal(1, s.PhaseIx);
        Assert.NotNull(s.Channel);
        Step(f, 1 / 60.0, _ => f.B.HitEnemy(boss, boss.MaxHp * 0.07, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }));
        Step(f, 2);
        Assert.Null(s.Channel);
        Assert.True(boss.Alive);
    }

    [Fact]
    public void Every_hook_the_game_wraps_asks_the_zone_when_called()
    {
        var zone = new BattleHooks();
        var h = BattleHooks.Following(zone);
        foreach (var field in typeof(BattleHooks).GetFields()) Assert.NotNull(field.GetValue(h));
        bool ticked = false, hit = false, staggered = false;
        zone.BossTick = (_, _) => ticked = true;
        zone.OnBossHit = (_, _, _) => hit = true;
        zone.OnBossStagger = _ => staggered = true;
        var b = BattleTests.Arena(31);
        var e = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z, new Battle.SpawnOpts())!;
        Assert.True(h.BossTick!(e, 0.1));
        h.OnBossHit!(e, School.Fire, 1);
        h.OnBossStagger!(e);
        Assert.True(ticked && hit && staggered);
    }

    [Fact]
    public void A_herald_is_not_a_boss_and_has_no_boss_music()
    {
        var f = At30("pack");
        var a = Callings.Archetype("warden");
        var b = f.B;
        var herald = b.SpawnEnemy("wolf_alpha", b.Player.X + 8, b.Player.Z, new Battle.SpawnOpts { Elite = true });
        Assert.NotNull(herald);
        Assert.False(herald!.Boss);
    }

    /// <summary>Every ruler, wired as the game wires it, against an absurd build that also does
    /// each end's chore at once (stands over the Barrow Lord, chases Grimtunnel to his hole): a
    /// late build killed the Barrow Lord in about 35 s, since his laying-down, Grimtunnel's going
    /// down and Greymuzzle's going did not wait for the last phase's floor.</summary>
    [Theory]
    [InlineData("pack", null, null, false)]
    [InlineData("pack", "boss_pack", "Greymuzzle", true)]
    [InlineData("dead", null, null, false)]
    [InlineData("lamplings", null, null, false)]
    [InlineData("lamplings", "grimtunnel_roused", "Grimtunnel", false)]
    [InlineData("kerchiefs", null, null, false)]
    public void A_boss_cannot_be_rushed_past_its_floors(string people, string? def, string? name, bool spare)
    {
        var f = At30(people, game: true, boss: def, bossName: name, spare: spare);
        var boss = Boss(f);
        double start = f.B.Time;
        // An absurd build: everything it has, every tick, and always where the end asks to be.
        Step(f, 200, _ =>
        {
            if (boss.Alive && boss.Boss && boss.State != EnemyState.Dying) f.B.HitEnemy(boss, boss.MaxHp * 0.2, School.Holy, [Tag.Holy], new HitOpts { NoCrit = true });
            if (boss.Alive && boss.Boss) { f.B.Player.X = boss.X + 1; f.B.Player.Z = boss.Z; }
        });
        Assert.True(f.Zone.Won);
        double took = f.B.Time - start;
        // Floors of 15, 20 and 15 s, and a transition at each turn.
        Assert.True(took >= 50, $"won in {took:0.0} s");
        Assert.True(f.Zone.BossScript!.BreakSum > 0);
    }

    [Fact]
    public void A_boss_left_alone_shows_every_phase_and_then_its_enrages()
    {
        var f = At30("pack");
        var s = f.Zone.BossScript!;
        Step(f, 130);
        Assert.Equal(2, s.PhaseIx);
        Step(f, 60);
        Assert.True(s.Soft);
        Step(f, 120);
        Assert.True(s.Hard);
    }

    [Fact]
    public void A_boss_is_staggered_not_locked()
    {
        var f = At30("pack");
        var boss = Boss(f);
        for (int i = 0; i < 12 && boss.StaggeredT <= 0; i++) f.B.ApplyStatus(boss, new StatusPayload(StatusKind.Stun, 1, 1, 2), 10);
        Assert.True(boss.StaggeredT > 0);
        Assert.False(boss.Status.Has(StatusKind.Stun));
        for (int i = 0; i < 20; i++) f.B.ApplyStatus(boss, new StatusPayload(StatusKind.Chill, 1, 3, 3), 10);
        Assert.False(boss.Status.Has(StatusKind.Frozen));
    }

    [Fact]
    public void Grimtunnel_goes_back_down_the_hole_and_never_dies()
    {
        // His own night (the Dig Boils Over): the table's Lamplings field the Ganger.
        var f = At30("lamplings", boss: "grimtunnel_roused", bossName: "Grimtunnel");
        var boss = Boss(f);
        bool killed = false;
        Step(f, 260, _ =>
        {
            if (boss.Alive && boss.Boss) f.B.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        });
        foreach (var ev in f.B.Events.Drain()) killed |= ev is Ev.Kill { Boss: true };
        Assert.True(f.Zone.Won);
        Assert.False(killed);
        // His chest is thrown up out of the dust.
        Assert.Contains(f.B.Pickups.Items, p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss");
    }

    /// <summary>The story keeps Grimtunnel and his name for his own night and Act 3
    /// (docs/STORY_BIBLE.md): a table arena fields a foreman of the Dig, who can die.</summary>
    [Fact]
    public void The_tables_lamplings_field_the_ganger_never_grimtunnel()
    {
        var f = At30("lamplings");
        var boss = Boss(f);
        Assert.Equal("boss_lamplings", boss.Def.Id);
        Assert.DoesNotContain("Grimtunnel", boss.Named?.Title ?? "");
        Assert.True(((Grimtunnel)f.Zone.BossScript!).Ganger);
        bool killed = false;
        Step(f, 260, _ =>
        {
            if (boss.Alive && boss.Boss) f.B.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            foreach (var ev in f.B.Events.Drain()) killed |= ev is Ev.Kill { Boss: true };
        });
        Assert.True(f.Zone.Won);
        Assert.True(killed);
    }

    /// <summary>Greymuzzle let go (the story bible, narrowly): brought down, he does not die;
    /// he gets up and goes, and the fight is won without a kill.</summary>
    [Fact]
    public void Greymuzzle_spared_goes_down_gets_up_and_goes()
    {
        var f = At30("pack", boss: "boss_pack", bossName: "Greymuzzle", spare: true);
        var boss = Boss(f);
        bool killed = false;
        Step(f, 260, _ =>
        {
            if (boss.Alive && boss.Boss && boss.TakenMul > 0) f.B.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            foreach (var ev in f.B.Events.Drain()) killed |= ev is Ev.Kill { Boss: true };
        });
        Assert.True(f.Zone.Won);
        Assert.False(killed);
        Assert.Contains(f.B.Pickups.Items, p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss");
        // Not spared, the same fight ends in a kill.
        var g = At30("pack", boss: "boss_pack", bossName: "Greymuzzle");
        var b2 = Boss(g);
        killed = false;
        Step(g, 260, _ =>
        {
            if (b2.Alive && b2.Boss && b2.TakenMul > 0) g.B.HitEnemy(b2, b2.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            foreach (var ev in g.B.Events.Drain()) killed |= ev is Ev.Kill { Boss: true };
        });
        Assert.True(g.Zone.Won);
        Assert.True(killed);
    }

    [Fact]
    public void The_barrow_lord_rises_unless_he_is_laid_down()
    {
        var f = At30("dead");
        var boss = Boss(f);
        var s = (BarrowLord)f.Zone.BossScript!;
        // To his last phase and down to nothing, the survivor kept away from him.
        Step(f, 200, _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) f.B.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            var p = f.B.Player;
            if (s.Channel != null) { p.X = boss.X + 20; p.Z = boss.Z; }
        });
        Assert.False(f.Zone.Won);
        Assert.True(boss.Alive);
        // Stand over him, and he is laid down.
        Step(f, 60, _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) f.B.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            var p = f.B.Player;
            if (s.Channel != null && boss.Alive) { p.X = boss.X + 1; p.Z = boss.Z; }
        });
        Assert.True(f.Zone.Won);
    }

    [Fact]
    public void The_boss_drops_the_runs_best_chest()
    {
        var f = At30("kerchiefs", tier: 3);
        var boss = Boss(f);
        Step(f, 200, _ =>
        {
            if (boss.Alive && boss.State != EnemyState.Dying) f.B.HitEnemy(boss, boss.MaxHp * 0.2, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        });
        var chest = f.B.Pickups.Items.FirstOrDefault(p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss");
        Assert.NotNull(chest);
        Assert.True(chest!.Value >= 5);
    }

    [Fact]
    public void A_cone_is_a_cone()
    {
        var b = BattleTests.Arena(31);
        double hp = b.Player.Hp;
        // Pointing at the survivor: it lands.
        b.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Cone, X = b.Player.X - 3, Z = b.Player.Z, Radius = 5, Angle = 0, Arc = Math.PI / 2, Delay = 0.1, Damage = 20, Source = "test" });
        for (int i = 0; i < 12; i++) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
        Assert.True(b.Player.Hp < hp);
        hp = b.Player.Hp;
        b.Player.Iframes = 0;
        // Pointing away: it does not.
        b.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Cone, X = b.Player.X - 3, Z = b.Player.Z, Radius = 5, Angle = Math.PI, Arc = Math.PI / 2, Delay = 0.1, Damage = 20, Source = "test" });
        for (int i = 0; i < 12; i++) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
        Assert.Equal(hp, b.Player.Hp, 3);
    }
}
