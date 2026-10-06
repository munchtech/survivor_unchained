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

/// <summary>The Dig Boils Over (docs/design/STORY_BOSSES.md 3; Play/Story/Dig.cs and
/// Play/Bosses/GrimtunnelStory.cs): windlasses that give to the one who stands at them, the Chucker
/// out of reach while his tubs run, the pump blown by the Perfect of Fuses' last crate, and
/// Grimtunnel on his lip: his barrel, his weakness, his own lamp, the crack, and down the hole.</summary>
[Collection("Balance")]
public class DigTests
{
    static StoryNightTests.Night Dig(int seed = 3, int tier = 1, Action<Journey>? before = null, bool unarmed = false)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        before?.Invoke(j);
        var spec = StoryFights.Spec("dig", j.Ctx, "verge", 0, 0, 0);
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

    /// <summary>Everything hostile but the one named (the crowd, the boiling shafts, his moths) let go.</summary>
    static void Quiet(StoryNightTests.Night n, Enemy? keep = null)
    {
        foreach (var e in n.B.Enemies.Living().Where(e => e != keep && !e.Boss && e.Named == null && e.Disposition == Disposition.Hostile).ToList())
            n.B.Enemies.Release(e);
    }

    [Fact]
    public void The_Dig_is_written_and_she_comes_in_at_the_edge()
    {
        Assert.True(StoryScripts.Has("dig_boils"));
        var n = Dig();
        var (sx, sz) = DigBoilsOver.Ground["start"];
        Assert.True(Dist(n.B.Player.X, n.B.Player.Z, sx, sz) < 0.1);
        Assert.Equal("Break the windlasses (0 of 3)", n.Zone.Beat!.Goal);
        var g = DigBoilsOver.Ground.Gates[0];
        Assert.True(n.B.Collision.Blocked((g.X0 + g.X1) / 2, (g.Z0 + g.Z1) / 2, 0.5));
    }

    /// <summary>Walking and dashing every way from each stage's start (and the boss's), she never leaves
    /// the place: the pit, the heaps and the shut gates hold her.</summary>
    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void The_place_holds_her_walking_and_dashing(int stage)
    {
        for (int k = 0; k < 16; k++)
        {
            var n = Dig(unarmed: true);
            n.Zone.SkipTo(stage);
            foreach (var e in n.B.Enemies.Living().ToList()) n.B.Enemies.Release(e);
            double mx = Math.Cos(k * Math.PI / 8), mz = Math.Sin(k * Math.PI / 8);
            var p = n.B.Player;
            for (int i = 0; i < 60 * 8; i++)
            {
                if (i % 30 == 0) { p.DashCharges = 2; n.B.Dash(mx, mz); }
                n.B.Tick(1 / 60.0, mx, mz);
                n.B.Events.Drain();
                Assert.True(DigBoilsOver.Ground.Inside(p.X, p.Z, -0.6), $"stage {stage}, bearing {k}: out at ({p.X:0.0}, {p.Z:0.0})");
            }
        }
    }

    [Fact]
    public void Every_stage_can_be_walked_to()
    {
        var n = Dig(unarmed: true);
        var g = DigBoilsOver.Ground;
        var map = MapGen.Generate(n.Spec.Map);
        n.Zone.SkipTo(3);
        foreach (var (from, to) in new[] { ("start", "shaft_b"), ("edge_w", "tubs_mid"), ("tubs_in", "brake"), ("brake", "pump"), ("pump_in", "boss_start"), ("pump_e", "boss_at") })
        {
            var nav = new NavField(map, n.B, g[to].X, g[to].Z, g.Bounds());
            Assert.False(double.IsNaN(nav.ToGo(g[from].X, g[from].Z)), $"{from} to {to}");
        }
    }

    /// <summary>A windlass gives to her standing at it, never to anything from across the edge; it goes over,
    /// its shaft falls in and leaves a hole, and the first brings Old Gutter up out of the next.</summary>
    [Fact]
    public void A_windlass_gives_to_the_one_who_stands_at_it_and_its_shaft_falls_in()
    {
        var n = Dig(unarmed: true);
        var p = n.B.Player;
        Step(n, 10, each: _ => Quiet(n));
        Assert.Equal("Break the windlasses (0 of 3)", n.Zone.Beat!.Goal);
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.Def.Id == "mb_wick_mother");
        var (wx, wz) = DigBoilsOver.Ground["shaft_b"];
        Step(n, 12, each: _ => { p.X = wx - 0.8; p.Z = wz; Quiet(n); }, until: () => n.Zone.Beat!.Goal.Contains("1 of 3"));
        Assert.Equal("Break the windlasses (1 of 3)", n.Zone.Beat!.Goal);
        Step(n, 1.5, each: _ => { p.X = wx - 4; p.Z = wz; Quiet(n); });
        Assert.NotEmpty(n.B.Collision.ByTag("shaft"));
        Assert.Contains(n.B.Enemies.Items, e => e.Alive && e.Def.Id == "mb_wick_mother");
    }

    /// <summary>Up on the brake-house the Chucker is out of her reach while his tubs run; then the rails go
    /// quiet and he is hers (at a quarter from beyond eleven metres, whole from closer).</summary>
    [Fact]
    public void The_Chucker_is_out_of_reach_while_his_tubs_run()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(1);
        Step(n, 0.5);
        var chucker = n.B.Enemies.Items.First(e => e.Alive && e.Def.Id == "mb_bombardier");
        var p = n.B.Player;
        var (bx, bz) = DigBoilsOver.Ground["brake"];
        Step(n, 4, each: _ => { p.X = bx; p.Z = bz + 3; n.B.CancelBlows(); Quiet(n); });
        Assert.Equal(0, chucker.TakenMul);
        // Ten tubs, a few seconds apart, wherever she is.
        Step(n, 70, each: _ => { p.X = -14; p.Z = 4; n.B.CancelBlows(); Quiet(n); }, until: () => chucker.TakenMul > 0);
        Assert.Equal(0.25, chucker.TakenMul, 3);
        Step(n, 0.5, each: _ => { p.X = bx; p.Z = bz + 4; n.B.CancelBlows(); Quiet(n); });
        Assert.Equal(1, chucker.TakenMul, 3);
    }

    /// <summary>A tub runs down the rail nearer her and flattens whatever is on it, the Dig's own too.</summary>
    [Fact]
    public void A_tub_flattens_the_lamplings_on_its_rail()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(1);
        Step(n, 0.2);
        var p = n.B.Player;
        Quiet(n);
        // She stands on the east rail; three lamplings stand on it below her, held there.
        var held = new[] { -6.0, -2.0, 2.0 }.Select(z => n.B.SpawnEnemy("lampling", -11.8, z, new Battle.SpawnOpts { Level = 1 })!).ToList();
        Step(n, 6, keep: true, each: _ =>
        {
            p.X = -11.8; p.Z = -10;
            foreach (var (e, k) in held.Select((e, k) => (e, k))) if (e.Alive && e.State != EnemyState.Dying) { e.X = -11.8; e.Z = -6 + 4 * k; e.Vx = e.Vz = 0; }
        });
        Assert.All(held, e => Assert.True(!e.Alive || e.State == EnemyState.Dying));
    }

    /// <summary>While the pump runs, the Perfect of Fuses keeps the steps out of reach and sends his runners;
    /// after his waves he comes down, and when he falls his last crate blows the pump (a wide ring, marked).</summary>
    [Fact]
    public void The_Perfect_of_Fuses_comes_down_after_his_waves_and_the_pump_goes_up()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(2);
        Step(n, 0.5);
        var foe = n.B.Enemies.Items.First(e => e.Alive && e.Def.Id == "mb_fuse_boss");
        Assert.Equal(0, foe.TakenMul);
        Assert.False(n.B.HostileToPlayer(foe));
        var p = n.B.Player;
        var (ix, iz) = DigBoilsOver.Ground["pump_in"];
        Step(n, 100, each: _ => { p.X = ix; p.Z = iz; Quiet(n, foe); foreach (var e in n.B.Enemies.Living().Where(e => e.Def.Id == "lampling_fuse").ToList()) n.B.Enemies.Release(e); },
            until: () => n.B.HostileToPlayer(foe));
        Assert.True(n.B.HostileToPlayer(foe));
        Assert.Equal(1, foe.TakenMul);
        n.B.KillEnemy(foe, true, null);
        Step(n, 0.2, each: _ => { p.X = ix; p.Z = iz + 6; });
        Assert.Contains(n.B.Blows, bl => bl.Label == "The pump" && bl.Radius >= 10);
        Step(n, 6, each: _ => { p.X = ix; p.Z = iz + 6; }, until: () => n.Zone.Now == StoryNight.Stage.Between);
        Assert.Equal(StoryNight.Stage.Between, n.Zone.Now);
        Assert.True(n.Zone.Marked("pump"));
    }

    /// <summary>With the pump already stopped, the Lamplighter holds its wreck instead.</summary>
    [Fact]
    public void With_the_pump_stopped_the_Lamplighter_holds_the_wreck()
    {
        var n = Dig(unarmed: true, before: j => j.World.Facts["dig.pump"] = "broken");
        n.Zone.SkipTo(2);
        Step(n, 0.5);
        Assert.Contains(n.B.Enemies.Items, e => e.Alive && e.Def.Id == "mb_lamplighter");
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.Def.Id == "mb_fuse_boss");
        Assert.Equal("Bring down the Lamplighter", n.Zone.Beat!.Goal);
    }

    static Enemy Boss(StoryNightTests.Night n) => n.B.Enemies.Items.First(e => e.Alive && e.Boss);

    /// <summary>The floors hold: an absurd build still sees all three of his phases. He does not die: spent, he
    /// goes down the crack, and the night is won with the pump blown; the crack, the pits and his lamplings go.</summary>
    [Fact]
    public void An_absurd_build_cannot_skip_Grimtunnel_and_he_goes_down_the_hole()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        Assert.IsType<GrimtunnelStory>(n.Zone.BossScript);
        double t0 = n.B.Time;
        Step(n, 400, each: _ => { if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); },
            until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.InRange(n.B.Time - t0, 80, 220);
        Step(n, 8);
        Assert.Equal("blown", n.J.World.Fact("dig.pump").Str);
        Assert.Empty(n.B.Collision.ByTag("crack").Concat(n.B.Collision.ByTag("pit")));
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.State != EnemyState.Dying && e.Def.Id.StartsWith("lampling"));
    }

    /// <summary>Brought into the Collapse and under half, Snib's barrel comes off the heap. Walked into, it rolls
    /// the way she went; into him it blows, a tenth of him, and his hide cracks.</summary>
    [Fact]
    public void Snibs_barrel_walked_into_him_blows_and_cracks_his_hide()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var gs = (GrimtunnelStory)n.Zone.BossScript!;
        Step(n, 200, each: _ =>
        {
            if (boss.TakenMul > 0 && boss.Hp > boss.MaxHp * 0.5) n.B.HitEnemy(boss, boss.MaxHp * 0.01, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            n.B.CancelBlows();
        }, until: () => gs.BarrelStill);
        Assert.True(gs.BarrelStill);
        // (Under the ground, it rolls over him: wait for him to be up.)
        Step(n, 12, each: _ => n.B.CancelBlows(), until: () => !gs.Under && !gs.Dazed && gs.BarrelStill);
        var (rx, rz) = gs.BarrelAt!.Value;
        // Him two metres past the barrel, held there; her a step behind it: it rolls into him.
        var p = n.B.Player;
        double hp = boss.Hp;
        Step(n, 3, each: t =>
        {
            boss.X = rx + 2.2; boss.Z = rz;
            if (t < 0.1) { p.X = rx - 1.0; p.Z = rz; }
        }, until: () => gs.Cracked);
        Assert.True(gs.Cracked);
        Assert.True(boss.Hp <= hp - boss.MaxHp * 0.04, $"hp {hp:0} -> {boss.Hp:0}");
        // Cracked, he takes more between his moves (not only in the moment it blew).
        Step(n, 1, each: _ => n.B.CancelBlows(), until: () => !gs.Under && !gs.Dazed);
        if (!gs.Under && !gs.Dazed) Assert.Equal(1.25, boss.TakenMul, 3);
    }

    /// <summary>Frost on the mound (his weakness) brings him up at once: no burst, and dazed twice as long.</summary>
    [Fact]
    public void Frost_on_the_mound_brings_him_up_dazed()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var gs = (GrimtunnelStory)n.Zone.BossScript!;
        Step(n, 30, each: _ => n.B.CancelBlows(), until: () => gs.Under);
        Assert.True(gs.Under);
        n.B.HitEnemy(boss, 1, School.Frost, [Tag.Frost], new HitOpts { NoCrit = true });
        Step(n, 0.2);
        Assert.False(gs.Under);
        Assert.True(gs.Dazed);
        Assert.DoesNotContain(n.B.Blows, bl => bl.Label == "He bursts up");
        // Twice a burst's daze: still dazed after six seconds.
        Step(n, 6, each: _ => n.B.CancelBlows());
        Assert.True(gs.Dazed);
    }

    /// <summary>The bane: his own lamp, set down by its prompt, draws his next two Unders up under it, and he
    /// stands looking at it.</summary>
    [Fact]
    public void His_own_lamp_set_down_draws_him_up_under_it()
    {
        var n = Dig(unarmed: true, before: j => Inventory.AddToPack(j.Ch, Inventory.Make(j.Ch, "grimtunnels_lamp")));
        n.Zone.SkipTo(3);
        Step(n, 1);
        var gs = (GrimtunnelStory)n.Zone.BossScript!;
        var boss = Boss(n);
        var p = n.B.Player;
        var offer = n.Zone.Interactables.First(i => i.Id == "story:lamp");
        double lx = p.X, lz = p.Z;
        offer.Act();
        // She walks off from it; he comes up under it, not under her.
        Step(n, 40, each: _ => { p.X = lx - 6; p.Z = lz; n.B.CancelBlows(); }, until: () => gs.Under);
        Assert.True(gs.Under);
        Step(n, 6, each: _ => { p.X = lx - 6; p.Z = lz; n.B.CancelBlows(); }, until: () => !gs.Under);
        Assert.True(Dist(boss.X, boss.Z, lx, lz) < 1.6, $"up at ({boss.X:0.0}, {boss.Z:0.0}), the lamp at ({lx:0.0}, {lz:0.0})");
        Assert.True(gs.Dazed);
    }

    /// <summary>In the Heart the crack opens across the ground: walking does not cross it, a dash does.</summary>
    [Fact]
    public void The_crack_opens_in_the_heart_and_a_dash_carries_her_over()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var gs = (GrimtunnelStory)n.Zone.BossScript!;
        Step(n, 200, each: _ => { if (boss.TakenMul > 0 && gs.PhaseIx < 2) n.B.HitEnemy(boss, boss.MaxHp * 0.01, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); n.B.CancelBlows(); },
            until: () => gs.PhaseIx == 2 && n.B.Collision.ByTag("crack").Count > 0);
        Assert.NotEmpty(n.B.Collision.ByTag("crack"));
        var (ax, az) = DigBoilsOver.Ground["crack_a"];
        var (bx, bz) = DigBoilsOver.Ground["crack_b"];
        double cx = (ax + bx) / 2, cz = (az + bz) / 2, lx = bx - ax, lz = bz - az, ll = Math.Sqrt(lx * lx + lz * lz);
        double nx = -lz / ll, nz = lx / ll;
        var p = n.B.Player;
        p.X = cx - nx * 3.2; p.Z = cz - nz * 3.2;
        // (He and his moths kept out of her way.)
        void Tick() { n.B.Tick(1 / 60.0, nx, nz); n.B.Events.Drain(); n.B.CancelBlows(); p.Hp = n.B.MaxHp; boss.X = 20; boss.Z = -19; Quiet(n); }
        // Walking at it for two seconds: still on her side.
        for (int i = 0; i < 120; i++) Tick();
        Assert.True((p.X - cx) * nx + (p.Z - cz) * nz < 0, "walked over the crack");
        p.DashCharges = 2;
        n.B.Dash(nx, nz);
        for (int i = 0; i < 40; i++) Tick();
        Assert.True((p.X - cx) * nx + (p.Z - cz) * nz > 0, "the dash did not carry her over");
    }

    /// <summary>On his ground, the way back from the pump-house shuts behind her.</summary>
    [Fact]
    public void The_way_back_shuts_behind_her_on_his_ground()
    {
        var n = Dig(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.3);
        var g = DigBoilsOver.Ground.Gates.First(x => x.Into == "lip");
        Assert.True(n.B.Collision.Blocked((g.X0 + g.X1) / 2, (g.Z0 + g.Z1) / 2, 0.5));
    }
}
