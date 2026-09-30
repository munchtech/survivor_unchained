using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The dash everyone has, and what timing it earns (Battle.Dash, Battle.PerfectDodge).</summary>
public class DashTests
{
    static Battle Arena() => BattleTests.Arena(3);

    static void Tick(Battle b, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
    }

    [Fact]
    public void Everyone_starts_with_two_dashes_and_they_come_back()
    {
        var b = Arena();
        Assert.Equal(2, b.Player.DashCharges);
        Assert.True(b.Dash(1, 0));
        Assert.True(b.Dash(1, 0) || b.Player.DashT > 0);
        Tick(b, 0.3);
        Assert.True(b.Dash(1, 0));
        Assert.Equal(0, b.Player.DashCharges);
        Tick(b, Abilities.Dash.Recharge + 0.1);
        Assert.True(b.Player.DashCharges >= 1);
    }

    [Fact]
    public void Slipping_a_lunge_as_it_lands_is_a_perfect_dodge()
    {
        var b = Arena();
        var wolf = b.SpawnEnemy("wolf", b.Player.X + 1, b.Player.Z)!;
        var other = b.SpawnEnemy("risen", b.Player.X - 1.5, b.Player.Z)!;
        b.Dash(0, 1);
        Tick(b, 1 / 60.0);
        int left = b.Player.DashCharges;
        var seen = new System.Collections.Generic.List<CombatEvent>();
        // The blow lands in the first moments of the dash.
        b.HurtPlayer(10, School.Physical, "wolf", wolf, telegraphed: true);
        seen.AddRange(b.Events.Drain());
        Assert.Contains(seen, e => e is Ev.PerfectDodge);
        Assert.Equal(left + 1, b.Player.DashCharges);
        Assert.True(b.Player.SureCritT > 0);
        Assert.True(other.Status.Has(StatusKind.Stun) || other.Hp < other.MaxHp);
        // Once a dash.
        b.HurtPlayer(10, School.Physical, "wolf", wolf, telegraphed: true);
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.PerfectDodge);
    }

    [Fact]
    public void The_crowd_brushing_past_is_not_a_perfect_dodge()
    {
        var b = Arena();
        var risen = b.SpawnEnemy("risen", b.Player.X + 1, b.Player.Z)!;
        b.Dash(0, 1);
        b.HurtPlayer(10, School.Physical, "risen", risen);
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.PerfectDodge);
    }

    [Fact]
    public void Too_late_in_the_dash_is_only_a_dodge()
    {
        var b = Arena();
        var wolf = b.SpawnEnemy("wolf", b.Player.X + 1, b.Player.Z)!;
        b.Dash(0, 1);
        Tick(b, Abilities.Dash.Perfect + 0.03);
        double hp = b.Player.Hp;
        b.HurtPlayer(10, School.Physical, "wolf", wolf, telegraphed: true);
        Assert.DoesNotContain(b.Events.Drain(), e => e is Ev.PerfectDodge);
        Assert.Equal(hp, b.Player.Hp);
    }

    [Fact]
    public void Out_of_a_dash_there_is_a_burst_of_pace()
    {
        var b = Arena();
        double walk = b.Stats.Get(Stat.MoveSpeed);
        b.Dash(1, 0);
        Tick(b, Abilities.Dash.Time + 0.05);
        Assert.True(b.Stats.Get(Stat.MoveSpeed) > walk * 1.1);
        Tick(b, Abilities.Dash.Momentum + 0.2);
        Assert.Equal(walk, b.Stats.Get(Stat.MoveSpeed), 3);
    }
}
