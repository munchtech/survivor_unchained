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

/// <summary>Behind the Sealed Door (docs/design/STORY_BOSSES.md 4; Play/Story/Vault.cs and
/// Play/Bosses/BarrowLordStory.cs): the Decurion behind his shields, the Scorpion's bolts down the hall and
/// the cover that stops them, the Signifer's standards, and the Barrow Lord at the head of the stair: his
/// lines, his testudo and its standard, Chid's bane, the front, and the laying down. They are not beaten;
/// they send her home.</summary>
[Collection("Balance")]
public class VaultTests
{
    static StoryNightTests.Night Vault(int seed = 3, int tier = 1, Action<Journey>? before = null, bool unarmed = false)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        before?.Invoke(j);
        var spec = StoryFights.Spec("vault", j.Ctx, "verge", 0, 0, 0);
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
    static Enemy Boss(StoryNightTests.Night n) => n.B.Enemies.Items.First(e => e.Alive && e.Boss);
    static Enemy? Named(StoryNightTests.Night n, string def) => n.B.Enemies.Items.FirstOrDefault(e => e.Alive && e.Def.Id == def && e.State != EnemyState.Dying);

    /// <summary>The crowd let go (everything hostile and unnamed but the one kept).</summary>
    static void Quiet(StoryNightTests.Night n, Enemy? keep = null)
    {
        foreach (var e in n.B.Enemies.Living().Where(e => e != keep && !e.Boss && e.Named == null && !e.Scripted && e.Disposition == Disposition.Hostile).ToList())
            n.B.Enemies.Release(e);
    }

    [Fact]
    public void The_Vault_is_written_and_she_comes_in_at_the_door()
    {
        Assert.True(StoryScripts.Has("vault_opened"));
        var n = Vault();
        var (sx, sz) = VaultOpened.Ground["start"];
        Assert.True(Dist(n.B.Player.X, n.B.Player.Z, sx, sz) < 0.1);
        Assert.Equal("Bring down the Decurion", n.Zone.Beat!.Goal);
        var g = VaultOpened.Ground.Gates[0];
        Assert.True(n.B.Collision.Blocked((g.X0 + g.X1) / 2, (g.Z0 + g.Z1) / 2, 0.5));
        // The hall's cover stands from the first, solid.
        Assert.Equal(VaultOpened.Cover.Length, n.B.Collision.ByTag("cover").Count);
    }

    /// <summary>Walking and dashing every way from each stage's start (and the boss's), she never leaves the place.</summary>
    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void The_place_holds_her_walking_and_dashing(int stage)
    {
        for (int k = 0; k < 16; k++)
        {
            var n = Vault(unarmed: true);
            n.Zone.SkipTo(stage);
            foreach (var e in n.B.Enemies.Living().Where(e => !e.Scripted).ToList()) n.B.Enemies.Release(e);
            double mx = Math.Cos(k * Math.PI / 8), mz = Math.Sin(k * Math.PI / 8);
            var p = n.B.Player;
            for (int i = 0; i < 60 * 8; i++)
            {
                if (i % 30 == 0) { p.DashCharges = 2; n.B.Dash(mx, mz); }
                n.B.Tick(1 / 60.0, mx, mz);
                n.B.Events.Drain();
                Assert.True(VaultOpened.Ground.Inside(p.X, p.Z, -0.6), $"stage {stage}, bearing {k}: out at ({p.X:0.0}, {p.Z:0.0})");
            }
        }
    }

    [Fact]
    public void Every_stage_can_be_walked_to()
    {
        var n = Vault(unarmed: true);
        var g = VaultOpened.Ground;
        var map = MapGen.Generate(n.Spec.Map);
        n.Zone.SkipTo(3);
        foreach (var (from, to) in new[] { ("start", "line"), ("south_w", "hall_in"), ("hall_in", "scorpion"), ("std_a", "std_c"), ("hall_e", "boss_start"), ("boss_start", "boss_at") })
        {
            var nav = new NavField(map, n.B, g[to].X, g[to].Z, g.Bounds());
            Assert.False(double.IsNaN(nav.ToGo(g[from].X, g[from].Z)), $"{from} to {to}");
        }
    }

    /// <summary>The third rank is the Decurion's, in a shield line: through his shields little reaches him (a
    /// sixth); round the line's end he is open.</summary>
    [Fact]
    public void The_Decurion_is_behind_his_shields_until_she_is_round_them()
    {
        var n = Vault(unarmed: true);
        var p = n.B.Player;
        Step(n, 30, each: _ => Quiet(n), until: () => Named(n, "mb_decurion") != null);
        var d = Named(n, "mb_decurion");
        Assert.NotNull(d);
        Step(n, 0.5, each: _ => Quiet(n, d));
        // Straight down the hall at him, the line between: a sixth reaches him.
        p.X = d!.X; p.Z = d.Z + 9;
        Step(n, 0.1);
        Assert.Equal(0.15, d.TakenMul, 2);
        // Round its end, beside him and a step behind: all of it.
        p.X = d.X + 6; p.Z = d.Z - 3;
        Step(n, 0.1);
        Assert.Equal(1, d.TakenMul, 2);
        Assert.Contains("Decurion", n.Zone.Beat!.Goal);
    }

    /// <summary>The Scorpion's bolts run down the hall's length at her, and the fallen beams and sarcophagi stop
    /// them: a lane is shorter behind cover. Behind his engine, from far down the hall, little reaches him.</summary>
    [Fact]
    public void The_Scorpions_bolts_stop_at_cover_and_she_must_close_on_him()
    {
        var n = Vault(unarmed: true);
        n.Zone.SkipTo(1);
        Step(n, 0.5);
        var s = Named(n, "mb_old_quarrel")!;
        Assert.NotNull(s);
        var p = n.B.Player;
        // Behind the sarcophagus at (-3, -8), on his line: the hall's cover stops a lane short of her.
        var (cx, cz, _, hd, _) = VaultOpened.Cover[2];
        double hx = cx, hz = cz + hd + 1.5;
        double full = Dist(s.X, s.Z, hx, hz);
        Assert.True(VaultOpened.Clear(n.B, s.X, s.Z, hx, hz) < full - 1);
        // In the open beside it, nothing in the way.
        Assert.Equal(Dist(s.X, s.Z, 0, -2), VaultOpened.Clear(n.B, s.X, s.Z, 0, -2), 1);
        // From down the hall a third reaches him; close, all of it.
        p.X = 0; p.Z = 4;
        Step(n, 0.1, each: _ => Quiet(n, s));
        Assert.Equal(0.3, s.TakenMul, 2);
        p.X = s.X + 3; p.Z = s.Z + 3;
        Step(n, 0.1, each: _ => Quiet(n, s));
        Assert.Equal(1, s.TakenMul, 2);
        // And his volleys come down the hall, marked.
        Step(n, 9, each: _ => { p.X = 0; p.Z = 2; Quiet(n, s); }, until: () => n.B.Blows.Any(b => b.Label == "A bolt"));
        Assert.Contains(n.B.Blows, b => b.Label == "A bolt");
    }

    /// <summary>Three standards down the hall: each broken counts, the dead round it stop a moment, and the
    /// Signifer falls with the last.</summary>
    [Fact]
    public void The_Signifer_falls_with_the_last_standard()
    {
        var n = Vault(unarmed: true);
        n.Zone.SkipTo(2);
        Step(n, 0.5);
        Assert.Equal("Break the standards (0 of 3)", n.Zone.Beat!.Goal);
        var standards = n.B.Enemies.Living().Where(e => e.Def.Id == "legion_standard").ToList();
        Assert.Equal(3, standards.Count);
        var sig = Named(n, "mb_ford_bell");
        Assert.NotNull(sig);
        Assert.True(sig!.TakenMul < 1);
        foreach (var (s, i) in standards.Select((s, i) => (s, i)))
        {
            n.B.HitEnemy(s, s.MaxHp * 2, School.Holy, [Tag.Holy], new HitOpts { NoCrit = true });
            Step(n, 0.5);
            if (i < 2) Assert.Equal($"Break the standards ({i + 1} of 3)", n.Zone.Beat!.Goal);
        }
        Step(n, 4);
        Assert.False(sig.Alive && sig.State != EnemyState.Dying);
        Assert.True(n.Zone.BeatIx > 2 || n.Zone.Now != StoryNight.Stage.Beat);
    }

    /// <summary>The floors hold: an absurd build still sees all three of his phases. Spent, he goes down and will
    /// not lie down until she stands over him; laid down, he gets up inside her reach and sends her home
    /// (C13's hand): the night is won, the door opened, and his ranks, lines, spears and standard all go.</summary>
    [Fact]
    public void An_absurd_build_cannot_skip_the_Barrow_Lord_and_he_must_be_laid_down()
    {
        var n = Vault(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var script = Assert.IsType<BarrowLordStory>(n.Zone.BossScript);
        var p = n.B.Player;
        double t0 = n.B.Time;
        // The ranks along the walls are men, never targets.
        Assert.Contains(n.B.Enemies.Items, e => e.Alive && e.Scripted && e.Def.Id == "risen_warrior");
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.Scripted && e.Def.Id == "risen_warrior" && n.B.Targetable(e));
        Step(n, 400, each: _ => { if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); },
            until: () => script.Laying);
        Assert.True(script.Laying);
        Assert.InRange(n.B.Time - t0, 80, 220);
        Assert.False(n.Zone.Won);
        // Stood over, he is laid down; and he sends her home.
        Step(n, 12, each: _ => { p.X = boss.X + 1; p.Z = boss.Z + 1; }, until: () => n.Zone.Won);
        Assert.True(n.Zone.Won);
        Assert.True(n.J.World.Fact("vault.opened").Truthy);
        Step(n, 8);
        Assert.DoesNotContain(n.B.Enemies.Items, e => e.Alive && e.State != EnemyState.Dying && e.Faction == Faction.Dead && e.Def.Id != "boss_dead");
        Assert.Empty(n.B.Collision.ByTag("pilum"));
    }

    /// <summary>Left alone when he goes down, he gets up again with a quarter of himself, and quicker.</summary>
    [Fact]
    public void Not_stood_over_he_gets_up_again()
    {
        var n = Vault(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var script = (BarrowLordStory)n.Zone.BossScript!;
        var p = n.B.Player;
        Step(n, 400, each: _ => { if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); },
            until: () => script.Laying);
        double speed = boss.Speed;
        Step(n, 9, each: _ => { p.X = boss.X + 9; p.Z = boss.Z; });
        Assert.False(script.Laying);
        Assert.True(boss.Alive);
        Assert.InRange(boss.Hp / boss.MaxHp, 0.2, 0.3);
        Assert.True(boss.Speed > speed);
        Assert.False(n.Zone.Won);
    }

    /// <summary>His testudo rings him in shields with the standard at its heart: while it stands he takes half.
    /// Broken, the ring drops and he is held; with Chid's bane known, the standard can be lifted, and then the
    /// century will not close up again.</summary>
    [Fact]
    public void The_testudos_standard_breaks_the_ring_and_with_the_bane_can_be_lifted()
    {
        var n = Vault(unarmed: true, before: j => j.World.Facts["bane.pole"] = true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var script = (BarrowLordStory)n.Zone.BossScript!;
        var p = n.B.Player;
        // Into his second phase.
        Step(n, 200, each: _ => { if (boss.Alive && boss.TakenMul > 0 && script.PhaseIx == 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); },
            until: () => script.Standard != null);
        var st = script.Standard;
        Assert.NotNull(st);
        Assert.Equal(1, script.PhaseIx);
        Step(n, 0.2);
        Assert.Equal(0.5, boss.TakenMul, 2);
        n.B.HitEnemy(st!, st!.MaxHp * 2, School.Fire, [Tag.Fire], new HitOpts { NoCrit = true });
        Step(n, 0.3);
        Assert.Null(script.Standard);
        Assert.True(boss.TakenMul > 1);
        var offer = n.Zone.Interactables.FirstOrDefault(i => i.Id == "story:standard");
        Assert.NotNull(offer);
        Assert.Equal("Lift the standard", offer!.Verb);
        offer.Act();
        Assert.True(script.Carried);
        // Carried, no more shells: past the next testudo's time, none rings him.
        Step(n, 30, each: _ => { p.X = boss.X + 7; p.Z = boss.Z; });
        Assert.Null(script.Standard);
    }

    /// <summary>Without the bane, a broken standard cannot be lifted.</summary>
    [Fact]
    public void Without_the_bane_the_standard_cannot_be_lifted()
    {
        var n = Vault(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var script = (BarrowLordStory)n.Zone.BossScript!;
        Step(n, 200, each: _ => { if (boss.Alive && boss.TakenMul > 0 && script.PhaseIx == 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); },
            until: () => script.Standard != null);
        var st = script.Standard!;
        n.B.HitEnemy(st, st.MaxHp * 2, School.Fire, [Tag.Fire], new HitOpts { NoCrit = true });
        Step(n, 0.3);
        Assert.DoesNotContain(n.Zone.Interactables, i => i.Id == "story:standard");
    }

    /// <summary>On Nondum the ranks close round the fight in a front, a step at a time; holy on him makes it give.</summary>
    [Fact]
    public void The_front_closes_and_holy_drives_it_back()
    {
        var n = Vault(unarmed: true);
        n.Zone.SkipTo(3);
        Step(n, 0.2);
        var boss = Boss(n);
        var script = (BarrowLordStory)n.Zone.BossScript!;
        var p = n.B.Player;
        Step(n, 300, each: _ => { if (boss.Alive && boss.TakenMul > 0) n.B.HitEnemy(boss, boss.MaxHp * 0.02, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true }); },
            until: () => script.PhaseIx == 2 && script.TransitionT <= 0);
        var (mx, mz) = script.Middle;
        Assert.True(script.Inside(mx + 7, mz, 0));
        // A step every eight seconds, to eight metres at the least.
        Step(n, 50, each: _ => { p.X = mx; p.Z = mz + 2; });
        Assert.False(script.Inside(mx + 9, mz, 0));
        Assert.True(script.Inside(mx + 7, mz, 0));
        // Holy on him: it gives a step.
        bool narrow = script.Inside(mx + 8.2, mz, 0);
        n.B.HitEnemy(boss, 1, School.Holy, [Tag.Holy], new HitOpts { NoCrit = true });
        Assert.False(narrow);
        Assert.True(script.Inside(mx + 8.2, mz, 0));
    }
}
