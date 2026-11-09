using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Kindled skills (Sim/Kindle.cs): an auto skill with a "kindle" fires itself only when its wait is over and
/// its condition holds (skills.json; ARPG.md's hands rule).</summary>
public sealed class KindleTests
{
    const double Dt = 1 / 60.0;

    static Battle Fight(string id)
    {
        var b = BattleTests.Arena(21, (id, 1));
        b.Calling = null;
        foreach (var w in b.Weapons) w.Timer = 0;
        return b;
    }

    static Enemy Dummy(Battle b, double x, double z, string def = "footpad")
    {
        var e = b.SpawnEnemy(def, x, z)!;
        e.Hp = e.MaxHp = 1e7;
        e.AttackT = e.RangedT = 999;
        return e;
    }

    static void Pin(Battle b, IList<Enemy> es, IList<(double X, double Z)> at)
    {
        for (int i = 0; i < es.Count; i++) { es[i].X = at[i].X; es[i].Z = at[i].Z; es[i].Vx = es[i].Vz = 0; }
        b.Spatial.Clear();
        foreach (var e in b.Enemies.Items) if (e.Alive && e.State != EnemyState.Dying) b.Spatial.Insert(e.Id, e.X, e.Z);
    }

    static int Braces(Battle b, double seconds, IList<Enemy>? es = null, IList<(double X, double Z)>? at = null, Action? each = null)
    {
        int n = 0;
        for (double t = 0; t < seconds - 1e-9; t += Dt)
        {
            if (es != null) Pin(b, es, at!);
            each?.Invoke();
            b.Tick(Dt, 0, 0);
            n += b.Events.Drain().OfType<Ev.Brace>().Count(e => e.Phase == BracePhase.Start);
        }
        return n;
    }

    static (Battle, List<Enemy>, List<(double, double)>) Crowd(int n)
    {
        var b = Fight("iron_vow");
        var p = b.Player;
        var at = Enumerable.Range(0, n).Select(i => (p.X + 1.5 + i * 0.1, p.Z + (i - n / 2.0) * 0.3)).ToList();
        var es = at.Select(a => Dummy(b, a.Item1, a.Item2)).ToList();
        return (b, es, at);
    }

    [Fact]
    public void Iron_vow_is_kindled_by_data_not_pressed()
    {
        var d = Weapons.Get("iron_vow");
        Assert.Equal(CastMode.Auto, d.Cast);
        Assert.Equal(2, d.Kindle!.Any!.Length);
        Assert.Equal("windup", d.Kindle.Any[0].When);
        Assert.Equal(true, d.Kindle.Any[0].Big);
        Assert.Equal(5, d.Kindle.Any[1].Count);
        Assert.Equal("crowd", Weapons.Get("watch_bell").Kindle!.When);
    }

    [Fact]
    public void A_crowd_condition_holds_off_two_foes_and_fires_for_five()
    {
        var (b2, es2, at2) = Crowd(2);
        Assert.Equal(0, Braces(b2, 1.5, es2, at2));
        var (b5, es5, at5) = Crowd(5);
        Assert.Equal(1, Braces(b5, 1.5, es5, at5));
        // Once per wait: its cooldown (10 s) is running.
        Assert.Equal(0, Braces(b5, 3, es5, at5));
    }

    [Fact]
    public void A_big_windup_on_her_kindles_iron_vow_and_nothing_else_does()
    {
        var b = Fight("iron_vow");
        var p = b.Player;
        Assert.Equal(0, Braces(b, 1.0));
        // A footpad's blow is not big.
        var small = Dummy(b, p.X + 3, p.Z);
        b.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = p.X, Z = p.Z, Radius = 2, Delay = 0.5, Damage = 1, From = small, Source = "t" });
        Assert.Equal(0, Braces(b, 0.4));
        // A brute's is, but not before it is within 0.6 s of landing.
        var (b2, _, _) = (Fight("iron_vow"), 0, 0);
        var q = b2.Player;
        var brute = Dummy(b2, q.X + 3, q.Z, "bruiser");
        b2.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = q.X, Z = q.Z, Radius = 2, Delay = 1.2, Damage = 1, From = brute, Source = "t" });
        Assert.Equal(0, Braces(b2, 0.3, each: () => brute.AttackT = 999));
        Assert.Equal(1, Braces(b2, 0.8, each: () => brute.AttackT = 999));
        // A brute's blow aimed elsewhere does not.
        var (b3, _, _) = (Fight("iron_vow"), 0, 0);
        var r = b3.Player;
        var brute3 = Dummy(b3, r.X + 3, r.Z, "bruiser");
        b3.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = r.X + 20, Z = r.Z, Radius = 2, Delay = 0.5, Damage = 1, From = brute3, Source = "t" });
        Assert.Equal(0, Braces(b3, 0.4));
    }

    [Fact]
    public void Iron_vow_still_braces_on_a_press_when_set_to_press()
    {
        var b = Fight("iron_vow");
        var w = b.Weapons.Single();
        w.CastSet = CastMode.Press;
        Assert.Equal(0, Braces(b, 1.0));
        Assert.True(b.PressSkill(w.Slot, b.Player.X, b.Player.Z));
        Assert.True(b.Bracing);
    }

    [Fact]
    public void A_kindled_iron_vow_runs_its_brace_when_it_fires_itself()
    {
        var (b, es, at) = Crowd(5);
        Braces(b, 1.0, es, at);
        Assert.True(b.Bracing);
    }
}
