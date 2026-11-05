using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>H7, the Flare's marks (Sim/FlareMarks.cs): every foe a staged Strike hits was marked on an earlier tick
/// (FlareLateMarks stays 0), few marks go unhit, the hovered foe is the one Main mark, and the marks never touch the fight.</summary>
public class FlareMarksTests(ITestOutputHelper log)
{
    static readonly (string Id, string[] Mods)[] Strikes =
    [
        ("the_long_cut", ["long_cut.second_cut", "long_cut.through_the_wall", "long_cut.line_of_morning"]),
        ("bell_of_the_morning", ["bell.fourth_toll", "bell.for_the_dead"]),
        ("burns_twice", ["burns.called_down", "burns.black_ice", "burns.more_embers"]),
        ("the_roads_toll", ["toll.doubled", "toll.last_cut"]),
        ("the_branding", ["branding.second", "branding.eye", "branding.deep"]),
        ("one_arrow", ["arrow.heart", "arrow.split", "arrow.pinned"]),
        ("drag_them_under", ["drag.deeper", "drag.grinder", "drag.hold_him"]),
        ("the_butchers_bill", ["bill.wide_chops", "bill.running_tab", "bill.feast"]),
    ];

    const int Seeds = 24;

    sealed record Tally(int Casts, int Late, int Decision, int Marked, int Unhit, int Kills, int Hit);

    /// <summary>A seeded fight: 10-60 risen round her, some at her reach's edge walking in, some frightened walking out,
    /// some fast, champions, a boss in every third seed, a hovered foe in half; the Flare cast along a seeded aim.</summary>
    static Battle Fight(string id, string[] mods, int seed, bool marks, Action<Battle>? eachTick = null)
    {
        var rng = new Random(seed * 7919 + id.Length);
        string[] lit = seed % 4 == 0 ? [] : [mods[seed % mods.Length]];
        var b = FlareStagedTests.Carrying(id, lit);
        b.FlareMarksOn = marks;
        if (id == "the_butchers_bill") b.Player.Hp = b.MaxHp * (0.2 + 0.7 * rng.NextDouble());
        double reach = Lamps.Flare(id)!.Radius;
        int n = 10 + rng.Next(51);
        var foes = new List<Enemy>();
        for (int i = 0; i < n; i++)
        {
            double a = rng.NextDouble() * Math.PI * 2;
            double d = rng.NextDouble() < 0.3 ? reach + (rng.NextDouble() * 2 - 1) * 1.5 : rng.NextDouble() * reach * 1.4;
            double hp = rng.NextDouble() switch { < 0.25 => 30, < 0.5 => 300, < 0.75 => 3000, < 0.9 => 30000, _ => 1e6 };
            var e = FlareStagedTests.Foe(b, b.Player.X + Math.Cos(a) * Math.Max(1, d), b.Player.Z + Math.Sin(a) * Math.Max(1, d), hp, elite: rng.NextDouble() < 0.1);
            if (rng.NextDouble() < 0.2) e.Speed *= 2.5;
            if (rng.NextDouble() < 0.15) b.ApplyStatus(e, new StatusPayload(StatusKind.Fear, 1, 1, 0.3 + rng.NextDouble()), 0);
            foes.Add(e);
        }
        if (seed % 3 == 0)
        {
            double a = rng.NextDouble() * Math.PI * 2, d = 2 + rng.NextDouble() * reach * 0.8;
            foes.Add(FlareStagedTests.Foe(b, b.Player.X + Math.Cos(a) * d, b.Player.Z + Math.Sin(a) * d, 2e6, boss: true));
        }
        if (seed % 2 == 1) b.Priority = foes[rng.Next(foes.Count)].Id;
        // A breath of walking first, so the crowd is moving at the press.
        for (int t = 0; t < 10; t++) b.Tick(1 / 60.0, 0, 0);
        b.FillFlare(100, "t");
        double aim = rng.NextDouble() * Math.PI * 2;
        Assert.True(b.UseFlare(Math.Cos(aim), Math.Sin(aim)));
        for (int t = 0; t < 180; t++)
        {
            b.Tick(1 / 60.0, 0, 0);
            eachTick?.Invoke(b);
        }
        b.Events.Drain();
        return b;
    }

    Tally Run(string id, string[] mods)
    {
        int late = 0, dec = 0, marked = 0, unhit = 0, kills = 0, hit = 0;
        for (int s = 0; s < Seeds; s++)
        {
            var b = Fight(id, mods, s, true, x =>
            {
                // (c) at most one Main; the hovered foe, when marked, is it.
                Assert.True(x.FlareMarks.Count(m => m.Main) <= 1);
                if (x.Priority >= 0 && x.FlareMarks.Any(m => m.Id == x.Priority)) Assert.True(x.FlareMarks.Single(m => m.Id == x.Priority).Main);
                if (x.FlareMarks.Count > 0) Assert.True(x.FlareMarksLive);
            });
            Assert.False(b.FlareMarksLive);
            Assert.Empty(b.FlareMarks);
            late += b.FlareLateMarks;
            dec += b.FlareDecisionMarks;
            marked += b.FlareMarkedCount;
            unhit += b.FlareMarkedUnhit;
            hit += b.FlareMarkedCount - b.FlareMarkedUnhit;
            kills += b.Enemies.Items.Count(e => e.Def != null && (!e.Alive || e.State == EnemyState.Dying));
        }
        return new Tally(Seeds, late, dec, marked, unhit, kills, hit);
    }

    public static IEnumerable<object[]> StrikeIds() => Strikes.Select(s => new object[] { s.Id });

    /// <summary>(a) and (b): no hit unmarked over 24 seeded casts each; the marked-never-hit share reported.</summary>
    [Theory]
    [MemberData(nameof(StrikeIds))]
    public void Every_hit_of_a_staged_strike_was_marked_on_an_earlier_tick(string id)
    {
        var mods = Strikes.Single(s => s.Id == id).Mods;
        var t = Run(id, mods);
        double share = t.Marked > 0 ? (double)t.Unhit / t.Marked : 0;
        log.WriteLine($"{id}: casts {t.Casts}, marked {t.Marked}, hit {t.Hit}, marked-unhit {t.Unhit} ({share:P1}), late {t.Late}, decision {t.Decision}, foes dead at the end {t.Kills}");
        Assert.True(t.Marked >= t.Casts, $"{id}: only {t.Marked} marks");
        Assert.Equal(0, t.Late);
        Assert.True(share < 0.2, $"{id}: {share:P1} of marks never hit");
    }

    /// <summary>A marked foe killed between ticks by something else (her weapons in the game): the cut, chop or ember that
    /// meant it re-picks at the blow itself, and that re-pick is marked at the decision (FlareDecisionMarks), never late.</summary>
    [Theory]
    [MemberData(nameof(StrikeIds))]
    public void A_marked_foe_killed_by_something_else_is_re_picked_marked(string id)
    {
        var mods = Strikes.Single(s => s.Id == id).Mods;
        int late = 0, dec = 0, killed = 0;
        for (int s = 0; s < Seeds; s++)
        {
            var rng = new Random(s);
            var b = Fight(id, mods, s, true, x =>
            {
                if (x.FlareMarks.Count == 0 || rng.NextDouble() > 0.2) return;
                var e = x.Enemies.Items[x.FlareMarks[rng.Next(x.FlareMarks.Count)].Id];
                if (e.Boss || !e.Alive || e.State == EnemyState.Dying) return;
                x.KillEnemy(e, true, null);
                killed++;
            });
            late += b.FlareLateMarks;
            dec += b.FlareDecisionMarks;
        }
        log.WriteLine($"{id}: killed between ticks {killed}, decision marks {dec}, late {late}");
        Assert.True(killed > Seeds);
        Assert.Equal(0, late);
    }

    /// <summary>(c) The hovered foe in the set is the one Main mark; with none hovered, the Flare's own main is.</summary>
    [Fact]
    public void The_hovered_foe_is_the_one_main_mark()
    {
        var b = FlareStagedTests.Carrying("the_roads_toll");
        var a = FlareStagedTests.Foe(b, 3, 0, 500);
        var c = FlareStagedTests.Foe(b, -3, 0, 900);
        var strong = FlareStagedTests.Foe(b, 0, 4, 5000, elite: true);
        b.Tick(1 / 60.0, 0, 0);
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        Assert.True(b.FlareMarksLive);
        Assert.Equal(new[] { a.Id, c.Id, strong.Id }.OrderBy(x => x), b.FlareMarks.Select(m => m.Id).OrderBy(x => x));
        // The Toll's last cut falls on the strongest: its own main.
        Assert.Equal(strong.Id, b.FlareMarks.Single(m => m.Main).Id);
        b.Priority = a.Id;
        int v = b.FlareMarksVersion;
        b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(a.Id, b.FlareMarks.Single(m => m.Main).Id);
        Assert.NotEqual(v, b.FlareMarksVersion);
    }

    /// <summary>The Long Cut shows both its shapes: the sweep's circle and the cleave's line, then only the line.</summary>
    [Fact]
    public void The_long_cut_shows_its_circle_and_its_line()
    {
        var b = FlareStagedTests.Carrying("the_long_cut");
        FlareStagedTests.Foe(b, b.Player.X + 20, b.Player.Z);
        b.Tick(1 / 60.0, 0, 0);
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        Assert.Equal([FlareMarkShapeKind.Circle, FlareMarkShapeKind.Line], b.FlareMarkShapes.Select(s => s.Kind));
        Assert.Single(b.FlareMarks);
        for (int t = 0; t < 22 && b.FlareMarkShapes.Count > 1; t++) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(FlareMarkShapeKind.Line, b.FlareMarkShapes.Single().Kind);
        Assert.Equal(24, b.FlareMarkShapes[0].Length, 3);
    }

    /// <summary>A Stand gets no marks.</summary>
    [Fact]
    public void A_stand_gets_no_marks()
    {
        var b = FlareStagedTests.Carrying("butchers_hour");
        FlareStagedTests.Foe(b, 2, 0);
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        for (int t = 0; t < 30; t++) { b.Tick(1 / 60.0, 0, 0); Assert.Empty(b.FlareMarks); }
        Assert.False(b.FlareMarksLive);
    }

    /// <summary>(d) The marks read and never write: the same seeded fight with the predictor on and off ends the same
    /// (every creature's life, health and place, hers, and the next draw of the fight's dice).</summary>
    [Theory]
    [MemberData(nameof(StrikeIds))]
    public void The_marks_never_touch_the_fight(string id)
    {
        var mods = Strikes.Single(s => s.Id == id).Mods;
        for (int s = 0; s < 8; s++)
        {
            var on = Fight(id, mods, s, true);
            var off = Fight(id, mods, s, false);
            Assert.True(on.FlareMarkedCount > 0 || on.Enemies.Items.All(e => !e.Alive));
            Assert.Equal(0, off.FlareMarkedCount);
            Assert.Equal(State(off), State(on));
            Assert.Equal(off.Rng.Next(), on.Rng.Next());
        }
    }

    static string State(Battle b) =>
        $"{b.Time:R} {b.Player.X:R} {b.Player.Z:R} {b.Player.Hp:R} {b.FlareMeter:R} " +
        string.Join(";", b.Enemies.Items.Select(e => $"{e.Alive}{e.State}{e.Hp:R},{e.X:R},{e.Z:R}"));
}
