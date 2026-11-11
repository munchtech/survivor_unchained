using System;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

public sealed class LocalHitStopTests
{
    readonly ITestOutputHelper output;
    public LocalHitStopTests(ITestOutputHelper output) => this.output = output;
    const double Dt = 1 / 60.0;

    static HitStopDef Policy(bool on = true)
    {
        var d = HitStop.Parse(Json.ReadContent("hit_stop.json"));
        d.Enabled = on;
        return d;
    }

    static Battle Fight(bool on = true)
    {
        var b = BattleTests.Arena();
        b.LocalHitStop = Policy(on);
        b.Weapons.Clear();
        return b;
    }

    static Enemy Foe(Battle b, double x = 2, double z = 0)
    {
        var e = b.SpawnEnemy("footpad", x, z)!;
        e.Hp = e.MaxHp = 10000;
        e.AttackT = e.RangedT = 999;
        return e;
    }

    [Fact]
    public void Shipped_policy_is_off_and_the_complete_class_table_is_in_data()
    {
        var d = HitStop.File;
        Assert.False(d.Enabled);
        Assert.Equal(150, d.CapMs);
        Assert.Equal(0, d.DurationMs[HitClass.Trash]);
        Assert.InRange(d.DurationMs[HitClass.Heavy], 40, 60);
        Assert.InRange(d.DurationMs[HitClass.Critical], 40, 60);
        Assert.InRange(d.DurationMs[HitClass.EliteKill], 80, 100);
        Assert.InRange(d.DurationMs[HitClass.Finisher], 80, 100);
        Assert.Equal(Enum.GetValues<HitClass>().Length, d.DurationMs.Count);
        Assert.Equal(30, d.Crowd.Above);
        Assert.Equal(0.5, d.Crowd.Scale);
        foreach (var kind in Enum.GetValues<HitClass>()) Assert.Equal(0, d.Seconds(kind, 0));
    }

    [Theory]
    [InlineData(HitClass.Trash, 0)]
    [InlineData(HitClass.Heavy, 0.05)]
    [InlineData(HitClass.Critical, 0.05)]
    [InlineData(HitClass.EliteKill, 0.09)]
    [InlineData(HitClass.Finisher, 0.09)]
    public void Enabled_table_resolves_each_class(HitClass kind, double seconds) => Assert.Equal(seconds, Policy().Seconds(kind, 0), 9);

    [Fact]
    public void Crowd_scales_only_above_the_data_threshold()
    {
        var d = Policy();
        Assert.Equal(0.05, d.Seconds(HitClass.Heavy, 30), 9);
        Assert.Equal(0.025, d.Seconds(HitClass.Heavy, 31), 9);
        d.Crowd.Above = 4; d.Crowd.Scale = 0.25;
        Assert.Equal(0.0125, d.Seconds(HitClass.Heavy, 5), 9);
    }

    [Fact]
    public void Oversized_duration_is_capped_and_invalid_cap_is_rejected()
    {
        var d = Policy();
        d.DurationMs[HitClass.Heavy] = 900;
        Assert.Equal(0.15, d.Seconds(HitClass.Heavy, 0), 9);
        d.CapMs = 151;
        Assert.Throws<ArgumentException>(() => HitStop.Parse(Json.Write(d)));
    }

    [Fact]
    public void Repeated_hits_take_the_longer_remainder_never_the_sum()
    {
        var c = new HitStopClock();
        c.Raise(0.09, 0.15);
        Assert.Equal(0, c.Step(0.02));
        c.Raise(0.05, 0.15);
        Assert.Equal(0.07, c.Remaining, 9);
        c.Raise(0.09, 0.15);
        Assert.Equal(0.09, c.Remaining, 9);
        c.Raise(0.09, 0.15);
        Assert.Equal(0.09, c.Remaining, 9);
    }

    [Fact]
    public void A_continuous_stream_releases_by_the_cap_and_a_later_hit_can_start_again()
    {
        var c = new HitStopClock();
        double held = 0;
        bool released = false;
        for (int i = 0; i < 30; i++)
        {
            c.Raise(9, 0.15);
            double free = c.Step(0.01);
            held += 0.01 - free;
            if (free > 1e-9) { released = true; break; }
        }
        Assert.True(released);
        Assert.Equal(0.15, held, 9);
        Assert.False(c.Held);
        c.Raise(0.05, 0.15);
        Assert.Equal(0.05, c.Remaining, 9);
    }

    [Theory]
    [InlineData(false, false, false, 0)]
    [InlineData(true, false, false, 0.05)]
    [InlineData(false, true, false, 0.05)]
    [InlineData(false, false, true, 0.09)]
    public void Real_hits_classify_trash_heavy_critical_and_elite_kills(bool heavy, bool crit, bool eliteKill, double seconds)
    {
        var b = Fight(); var e = Foe(b);
        if (eliteKill) { e.Elite = true; e.Hp = 1; }
        b.HitEnemy(e, 10, School.Physical, [Tag.Melee], new HitOpts { Heavy = heavy, Crit = crit, NoCrit = !crit, NoProcs = true });
        Assert.Equal(seconds, e.HitStop.Remaining, 9);
        Assert.Equal(seconds, b.Player.HitStop.Remaining, 9);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void Off_flag_or_damage_over_time_never_holds(bool dot)
    {
        var b = Fight(dot); var e = Foe(b);
        b.HitEnemy(e, 10, School.Physical, [Tag.Melee], new HitOpts { Heavy = true, NoCrit = true, Dot = dot });
        Assert.False(e.HitStop.Held);
        Assert.False(b.Player.HitStop.Held);
    }

    [Fact]
    public void An_elite_killed_by_damage_over_time_still_uses_the_kill_class()
    {
        var b = Fight(); var e = Foe(b);
        e.Elite = true; e.Hp = 1;
        b.HitEnemy(e, 10, School.Fire, [Tag.Fire], new HitOpts { Dot = true, NoCrit = true, NoProcs = true });
        Assert.Equal(0.09, e.HitStop.Remaining, 9);
        Assert.Equal(0.09, b.Player.HitStop.Remaining, 9);
    }

    [Fact]
    public void Only_live_hostiles_inside_the_screen_count_toward_crowding()
    {
        var b = Fight(); var target = Foe(b);
        for (int i = 0; i < 30; i++) Foe(b, i, 5);
        var ally = Foe(b); ally.Disposition = Disposition.Ally;
        var dying = Foe(b); dying.State = EnemyState.Dying;
        b.HitStopOnScreen = e => e.Id != 30;
        b.HitEnemy(target, 10, School.Physical, [Tag.Melee], new HitOpts { Heavy = true, NoCrit = true });
        Assert.Equal(0.05, target.HitStop.Remaining, 9);
        b.HitStopOnScreen = _ => true;
        var second = b.Enemies.Items[1];
        b.HitEnemy(second, 10, School.Physical, [Tag.Melee], new HitOpts { Heavy = true, NoCrit = true });
        Assert.Equal(0.025, second.HitStop.Remaining, 9);
    }

    [Fact]
    public void Only_attacker_and_target_wait_while_world_time_and_projectiles_advance()
    {
        var b = Fight(); var target = Foe(b); var other = Foe(b, 8);
        var missile = b.SpawnProjectile(Side.Player, 30, 30, 1, School.Physical)!;
        missile.Vx = 2; missile.Life = 2;
        b.HitEnemy(target, 10, School.Physical, [Tag.Melee], new HitOpts { Heavy = true, NoCrit = true });
        double x = b.Player.X, tx = target.X, anim = target.AnimT, ot = other.AnimT, px = missile.X;
        b.Tick(Dt, 1, 0);
        Assert.Equal(Dt, b.Time, 9);
        Assert.Equal(x, b.Player.X);
        Assert.Equal(tx, target.X);
        Assert.Equal(anim, target.AnimT);
        Assert.True(other.AnimT > ot);
        Assert.True(missile.X > px);
        Assert.False(b.Dash(1, 0));
        Assert.False(b.UseAbility(1, 0));
        for (int i = 0; i < 5; i++) b.Tick(Dt, 1, 0);
        Assert.True(b.Player.X > x);
        Assert.True(target.AnimT > anim);
    }

    [Fact]
    public void Summon_hit_holds_its_attacker_and_target_without_holding_the_player()
    {
        var b = Fight(); var target = Foe(b); var ally = Foe(b, 4);
        ally.Disposition = Disposition.Ally;
        b.HitEnemy(target, 10, School.Physical, [Tag.Summon], new HitOpts { Summon = true, Attacker = ally, Heavy = true, NoCrit = true });
        Assert.True(ally.HitStop.Held && target.HitStop.Held);
        Assert.False(b.Player.HitStop.Held);
    }

    [Fact]
    public void Enemy_heavy_hit_holds_that_enemy_and_the_player_only()
    {
        var b = Fight(); var from = Foe(b); from.Elite = true;
        var other = Foe(b, 8);
        b.HurtPlayerRaw(10, School.Physical, "test", from);
        Assert.Equal(0.05, b.Player.HitStop.Remaining, 9);
        Assert.Equal(0.05, from.HitStop.Remaining, 9);
        Assert.False(other.HitStop.Held);
    }

    [Fact]
    public void A_finisher_uses_its_class_even_when_the_bark_is_suppressed()
    {
        var b = Fight(); var e = Foe(b);
        b.ExecutedBark(e);
        Assert.Equal(0.09, e.HitStop.Remaining, 9);
    }

    [Fact]
    public void A_pending_contact_waits_and_resumes_without_restarting_the_swing()
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true,
            Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)],
        });
        b.LocalHitStop = Policy();
        b.Calling = "warden";
        b.Weapons[0].Timer = 0;
        var e = Foe(b);
        Assert.True(b.PressSkill(0, 2, 0));
        Assert.True(b.PendingBlows > 0);
        var anim = b.Player.AttackAnim!;
        double contact = b.Swing!.ContactAt, hp = e.Hp;
        b.Player.HitStop.Raise(0.1, 0.15);
        for (int i = 0; i < 5; i++) b.Tick(Dt, 0, 0);
        Assert.Equal(hp, e.Hp);
        Assert.Equal(anim.T, b.Player.AttackAnim!.T);
        Assert.Equal(contact + 5 * Dt, b.Swing!.ContactAt, 9);
        for (int i = 0; i < 60 && e.Hp == hp; i++) b.Tick(Dt, 0, 0);
        Assert.True(e.Hp < hp);
    }

    [Fact]
    public void An_enemy_mark_waits_with_its_caster_while_other_marks_land()
    {
        var b = Fight(); var caster = Foe(b);
        var held = b.Blow(new Battle.EnemyBlow { From = caster, Delay = 0.03, X = 80, Z = 80 });
        var other = b.Blow(new Battle.EnemyBlow { Delay = 0.03, X = 80, Z = 80 });
        caster.HitStop.Raise(0.09, 0.15);
        for (int i = 0; i < 3; i++) b.Tick(Dt, 0, 0);
        Assert.Equal(0.03, held.T, 9);
        Assert.True(other.T <= 0);
        for (int i = 0; i < 6; i++) b.Tick(Dt, 0, 0);
        Assert.True(held.T <= 0);
    }

    [Fact]
    public void Recycled_enemy_slots_start_without_a_hold()
    {
        var b = Fight(); var e = Foe(b);
        e.HitStop.Raise(0.09, 0.15);
        b.Enemies.Release(e);
        var fresh = Foe(b);
        Assert.Equal(e.Id, fresh.Id);
        Assert.False(fresh.HitStop.Held);
        Assert.Equal(0, fresh.HitStop.Total);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void A_projectile_holds_only_its_original_caster(bool recycle)
    {
        var b = Fight(); var from = Foe(b, 20);
        from.Elite = true;
        var pr = b.SpawnProjectile(Side.Enemy, 0.1, 0, 10, School.Physical)!;
        pr.OwnerId = from.Id; pr.HitStopOwnerSeed = from.Seed;
        pr.Life = 2; pr.Tags = [Tag.Projectile];
        if (recycle)
        {
            b.Enemies.Release(from);
            var fresh = Foe(b, 20); fresh.Elite = true;
            Assert.Equal(from.Id, fresh.Id);
            Assert.NotEqual(pr.HitStopOwnerSeed, fresh.Seed);
        }
        double hp = b.Player.Hp;
        b.Tick(Dt, 0, 0);
        Assert.True(b.Player.Hp < hp);
        Assert.Equal(!recycle, b.Player.HitStop.Held);
        Assert.Equal(!recycle, from.HitStop.Held);
    }

    [Theory]
    [InlineData("human")]
    [InlineData("deft")]
    public void Enabled_zone_sim_completes(string bot)
    {
        var r = ZoneSim.Play(new ZoneRunSpec(1, "lowford", bot, 2), quiet: true, hitStop: Policy());
        output.WriteLine($"{bot}: through {r.Reached}, {r.PlaySeconds / 60:0.0} min, kills {r.Kills}, falls {r.Falls}");
        Assert.True(r.Reached, r.StuckAt ?? "capped");
        Assert.True(r.Seconds < ZoneSim.Cap);
    }
}
