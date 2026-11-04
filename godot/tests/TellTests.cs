using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The telegraph kit (Sim/Tells.cs, data/content/telegraphs.json): each named blow lands on her if she stands,
/// misses if she dashes out in time, and does its own thing in its windup (the ring roots, the pull drags, the charger
/// plants and then runs its lane, the closing holds its ring and then sends it in).</summary>
public class TellTests
{
    const double Dt = 1 / 60.0;

    static Battle Fresh()
    {
        var b = BattleTests.Arena(7);
        b.Tick(Dt, 0, 0);
        b.Events.Drain();
        b.Player.DashCharges = 2;
        return b;
    }

    /// <summary>Ticks for `seconds`, walking (mx, mz) from `from` s on, and gathers the kit's marks.</summary>
    static List<Ev.Telegraph> Run(Battle b, double seconds, double mx = 0, double mz = 0, double from = 0, Action<double>? at = null)
    {
        var marks = new List<Ev.Telegraph>();
        for (double t = 0; t < seconds; t += Dt)
        {
            at?.Invoke(t);
            bool walk = t >= from;
            b.Tick(Dt, walk ? mx : 0, walk ? mz : 0);
            marks.AddRange(b.Events.Drain().OfType<Ev.Telegraph>().Where(e => e.Tell != null));
        }
        return marks;
    }

    static Ev.Telegraph Land(List<Ev.Telegraph> marks, string kind) => Assert.Single(marks, m => m.Tell == kind && m.Phase == TellPhase.Land);

    [Fact]
    public void A_ring_lands_on_her_if_she_stands_and_says_so()
    {
        var b = Fresh();
        var p = b.Player;
        var blow = b.Tell("ring", null, p.X, p.Z);
        Assert.NotNull(blow);
        Assert.Equal(b.MaxHp * SurvivorUnchained.Content.Telegraphs.Get("ring")!.Damage, blow!.Damage, 6);
        var marks = b.Events.Drain().OfType<Ev.Telegraph>().ToList();
        var warn = Assert.Single(marks, m => m.Tell == "ring");
        Assert.Equal(TellPhase.Warn, warn.Phase);
        Assert.Equal(TelegraphShape.Circle, warn.Shape);
        Assert.Equal(2.0, warn.Duration, 6);
        marks = Run(b, 2.3);
        var land = Land(marks, "ring");
        Assert.True(land.Caught);
        Assert.True(p.Hp < b.MaxHp - 10, $"hp {p.Hp}");
        Assert.Empty(b.ActiveTells);
    }

    [Fact]
    public void A_ring_misses_her_if_she_dashes_out_in_time()
    {
        var b = Fresh();
        var p = b.Player;
        b.Tell("ring", null, p.X, p.Z);
        var marks = Run(b, 2.3, mx: 1, from: 0.1, at: t => { if (Math.Abs(t - 0.1) < Dt / 2) Assert.True(b.Dash(1, 0)); });
        Assert.False(Land(marks, "ring").Caught);
        Assert.Equal(b.MaxHp, p.Hp, 6);
    }

    [Fact]
    public void A_ring_slows_her_in_its_fill_and_roots_her_at_its_heart_until_she_dashes()
    {
        var b = Fresh();
        var p = b.Player;
        b.Tell("ring", null, p.X, p.Z);
        Run(b, 0.5);
        Assert.True(p.SlowF < 0.7, $"slow {p.SlowF}");
        Run(b, 0.45);
        Assert.True(p.RootT > 0.3, $"root {p.RootT}");
        double x0 = p.X;
        Run(b, 0.2, mx: 1);
        Assert.Equal(x0, p.X, 6);
        Assert.True(b.Dash(1, 0));
        Assert.Equal(0, p.RootT);
        Run(b, 0.3);
        Assert.True(p.X > x0 + 4, $"x {p.X - x0}");
    }

    [Fact]
    public void A_pull_drags_her_toward_its_heart_and_lands_on_her_if_she_lets_it()
    {
        var b = Fresh();
        var p = b.Player;
        double x0 = p.X;
        b.Tell("pull", null, p.X + 6, p.Z);
        Assert.Single(b.ActiveTells, t => t.Pull > 0 && t.Reach == 9);
        Run(b, 0.5);
        Assert.InRange(p.X - x0, 1.2, 1.8);
        var marks = Run(b, 1.3);
        Assert.True(Land(marks, "pull").Caught);
        Assert.True(p.Hp < b.MaxHp - 10, $"hp {p.Hp}");
    }

    [Fact]
    public void A_pull_misses_her_if_she_dashes_out_of_it()
    {
        var b = Fresh();
        var p = b.Player;
        b.Tell("pull", null, p.X + 6, p.Z);
        var marks = Run(b, 1.8, mx: -1, from: 0.3, at: t => { if (Math.Abs(t - 0.3) < Dt / 2) Assert.True(b.Dash(-1, 0)); });
        Assert.False(Land(marks, "pull").Caught);
        Assert.Equal(b.MaxHp, p.Hp, 6);
    }

    [Fact]
    public void A_charge_plants_its_foe_lands_down_its_lane_and_runs_it()
    {
        var b = Fresh();
        var p = b.Player;
        var e = b.SpawnEnemy("risen", p.X + 10, p.Z)!;
        b.Tick(Dt, 0, 0);
        b.Events.Drain();
        double ex = e.X, ez = e.Z;
        var blow = b.Tell("charge", e, p.X, p.Z)!;
        Assert.Equal(TelegraphShape.Line, blow.Shape);
        Assert.Equal(16, Math.Sqrt((blow.X1 - blow.X) * (blow.X1 - blow.X) + (blow.Z1 - blow.Z) * (blow.Z1 - blow.Z)), 6);
        Run(b, 0.8);
        Assert.Equal(ex, e.X, 6);
        Assert.Equal(ez, e.Z, 6);
        var marks = Run(b, 0.8);
        Assert.True(Land(marks, "charge").Caught);
        Assert.True(p.Hp < b.MaxHp - 5, $"hp {p.Hp}");
        Assert.True(e.X < ex - 14, $"ran {ex - e.X}");
    }

    [Fact]
    public void A_charge_misses_her_if_she_dashes_off_its_lane_and_ends_with_its_foe()
    {
        var b = Fresh();
        var p = b.Player;
        var e = b.SpawnEnemy("risen", p.X + 10, p.Z)!;
        b.Tick(Dt, 0, 0);
        b.Tell("charge", e, p.X, p.Z);
        var marks = Run(b, 1.4, at: t => { if (Math.Abs(t - 0.5) < Dt / 2) Assert.True(b.Dash(0, 1)); });
        Assert.False(Land(marks, "charge").Caught);
        Assert.Equal(b.MaxHp, p.Hp, 6);

        // A charger felled in its windup: no lane lands.
        var f = b.SpawnEnemy("risen", p.X + 10, p.Z)!;
        b.Tick(Dt, 0, 0);
        b.Tell("charge", f, p.X, p.Z);
        b.KillEnemy(f, false, null);
        marks = Run(b, 1.4);
        Assert.DoesNotContain(marks, m => m.Phase == TellPhase.Land);
        Assert.Empty(b.Blows);
    }

    [Fact]
    public void A_closing_gives_its_ring_holds_it_for_the_windup_then_sends_it_in()
    {
        var b = Fresh();
        var p = b.Player;
        var pts = b.TellClosing(p.X, p.Z, 12);
        Assert.Equal(12, pts.Count);
        Assert.All(pts, q => Assert.InRange(Math.Sqrt((q.X - p.X) * (q.X - p.X) + (q.Z - p.Z) * (q.Z - p.Z)), 8, 9.5));
        var warn = Assert.Single(b.Events.Drain().OfType<Ev.Telegraph>(), m => m.Tell == "closing");
        Assert.Equal(TelegraphShape.Ring, warn.Shape);
        var foes = pts.Select(q => b.SpawnEnemy("risen", q.X, q.Z)!).ToList();
        Assert.All(foes, f => Assert.True(b.Closes(f)));
        var at = foes.Select(f => (f.X, f.Z)).ToList();
        Run(b, 1.2);
        for (int i = 0; i < foes.Count; i++) { Assert.Equal(at[i].X, foes[i].X, 6); Assert.Equal(at[i].Z, foes[i].Z, 6); }
        var marks = Run(b, 0.6);
        Land(marks, "closing");
        Assert.All(foes, f => { Assert.True(f.HasteT > 3); Assert.Equal(1.6, f.Haste, 6); });
        Assert.Equal(b.MaxHp, p.Hp, 6);
    }

    [Fact]
    public void The_kit_casts_nothing_it_does_not_have_and_no_charge_without_a_foe()
    {
        var b = Fresh();
        Assert.Null(b.Tell("meteor", null, 0, 0));
        Assert.Null(b.Tell("charge", null, 0, 0));
        Assert.Empty(b.ActiveTells);
        Assert.Empty(b.Blows);
        Assert.False(b.Closes(b.SpawnEnemy("risen", 5, 0)!));
    }

    [Fact]
    public void A_scaled_cast_is_bigger_and_a_checkpoint_calls_it_off()
    {
        var b = Fresh();
        var p = b.Player;
        var blow = b.Tell("ring", null, p.X, p.Z, 1.5)!;
        Assert.Equal(6.5 * 1.5, blow.Radius, 6);
        Run(b, 0.95);
        Assert.True(p.RootT > 0);
        b.CancelBlows();
        Assert.Empty(b.ActiveTells);
        Assert.Equal(0, p.RootT);
        Assert.DoesNotContain(Run(b, 1.5), m => m.Phase == TellPhase.Land);
    }

    [Fact]
    public void A_closing_with_teeth_opens_a_gap_and_its_ring_bites_once_each_on_the_rush()
    {
        var b = Fresh();
        b.ClosingTeeth = true;
        var p = b.Player;
        p.DashCharges = 0;
        var pts = b.TellClosing(p.X, p.Z, 24);
        var warn = Assert.Single(b.Events.Drain().OfType<Ev.Telegraph>(), m => m.Tell == "closing");
        Assert.Equal(3.5, warn.GapWidth, 6);
        // No foe stands in the way out: the gap's mouth is clear by its width.
        double r = (warn.Inner + warn.Radius) / 2;
        Assert.All(pts, q => Assert.True(Math.Abs(Math.IEEERemainder(Math.Atan2(q.Z - p.Z, q.X - p.X) - warn.GapAngle, Math.Tau)) * r > warn.GapWidth / 2));
        Assert.True(pts.Count < 24 && pts.Count >= 20);
        var foes = pts.Select(q => b.SpawnEnemy("risen", q.X, q.Z)!).ToList();
        Assert.All(foes, f => Assert.True(b.Closes(f)));
        var t = Assert.Single(b.ActiveTells, x => x.Kind == "closing");
        double before = p.Hp, bit = 0;
        Run(b, 1.65);
        Assert.True(t.RushLeft > 3);
        // Her own foes' blows aside, the rush's bites: each at most once, each 4% of her max life.
        for (double s = 0; s < 4 && p.Alive; s += Dt)
        {
            b.Tick(Dt, 0, 0);
            foreach (var h in b.Events.Drain().OfType<Ev.PlayerHit>()) if (Math.Abs(h.Amount - 0.04 * b.MaxHp) < 0.5 * 0.04 * b.MaxHp) bit += h.Amount;
        }
        Assert.True(before - p.Hp > 0.1 * b.MaxHp, $"the ring cost {(before - p.Hp) / b.MaxHp:0.00}");
        Assert.True(bit <= pts.Count * 0.04 * b.MaxHp * 1.25);
    }

    [Fact]
    public void A_closing_without_teeth_is_as_it_was_whole_and_harmless()
    {
        var b = Fresh();
        var p = b.Player;
        Assert.Equal(12, b.TellClosing(p.X, p.Z, 12).Count);
        Assert.Equal(0, Assert.Single(b.Events.Drain().OfType<Ev.Telegraph>(), m => m.Tell == "closing").GapWidth);
    }

    [Fact]
    public void Two_kit_tells_near_her_land_at_least_the_spacing_apart()
    {
        var b = Fresh();
        var p = b.Player;
        var foe = b.SpawnEnemy("risen", p.X + 6, p.Z)!;
        Assert.Equal(0, b.KitWait("ring", null));
        b.Tell("ring", null, p.X, p.Z);
        // A charge now would land 0.9 s before the ring: it waits to land 1.5 s after it (2.0 + 1.5 - 1.1).
        Assert.Equal(2.4, b.KitWait("charge", foe), 6);
        // Far from her, nothing waits on it.
        var c = BattleTests.Arena(7); c.Tick(Dt, 0, 0);
        c.Tell("ring", null, c.Player.X + 30, c.Player.Z);
        Assert.Equal(0, c.KitWait("ring", null));
    }

    [Fact]
    public void At_most_two_fodder_lanes_are_alive_near_her()
    {
        var w = Content.Telegraphs.Waves;
        double keep = w.Spacing;
        w.Spacing = 0;
        try
        {
            var b = Fresh();
            var p = b.Player;
            var foes = Enumerable.Range(0, 3).Select(i => b.SpawnEnemy("risen", p.X + 5, p.Z + (i - 1) * 3)!).ToList();
            Assert.Equal(0, b.KitWait("charge", foes[0]));
            b.Tell("charge", foes[0], p.X, p.Z);
            Assert.Equal(0, b.KitWait("charge", foes[1]));
            b.Tell("charge", foes[1], p.X, p.Z);
            Assert.True(b.KitWait("charge", foes[2]) > 1);
            Run(b, 1.5);
            Assert.Equal(0, b.KitWait("charge", foes[2]));
        }
        finally { w.Spacing = keep; }
    }
}
