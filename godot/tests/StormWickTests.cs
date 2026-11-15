using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>Bladestorm's wick (data/content/wicks.json, Sim/Turns.cs, Sim/PressedWarden.cs FireSpin): the three strands, and
/// each Turn (Line on Line, Long Blade, Hold Fast) held in the real sim: lines every 2nd blow, 30% more reach, a freeze on the 5th cut.</summary>
public sealed class StormWickTests(ITestOutputHelper output)
{
    const double Dt = 1 / 60.0;

    static readonly string[] Lines4 = ["bladestorm.lines.1", "bladestorm.lines.2", "bladestorm.lines.3", "bladestorm.lines.4"];
    static readonly string[] Long4 = ["bladestorm.long.1", "bladestorm.long.2", "bladestorm.long.3", "bladestorm.long.4"];
    static readonly string[] Hold4 = ["bladestorm.hold.1", "bladestorm.hold.2", "bladestorm.hold.3", "bladestorm.hold.4"];

    static Battle Fight(params (string Id, int Rank)[] skills)
    {
        var b = BattleTests.Arena(21, skills);
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

    static List<CombatEvent> Run(Battle b, double seconds, Action? each = null, Func<bool>? until = null)
    {
        var evs = new List<CombatEvent>();
        for (double t = 0; t < seconds - 1e-9; t += Dt)
        {
            each?.Invoke();
            b.Tick(Dt, 0, 0);
            evs.AddRange(b.Events.Drain());
            if (until?.Invoke() == true) break;
        }
        return evs;
    }

    static (Battle B, WeaponInst W) Storm(string[]? path = null)
    {
        var b = Fight(("sunder", 8), ("bladestorm", 8));
        var w = b.Weapons.Single(x => x.Id == "bladestorm");
        HoldGrip(b);
        w.Timer = 0;
        if (path != null) b.SetWickPath("bladestorm", path);
        return (b, w);
    }

    static void HoldGrip(Battle b)
    {
        var g = b.Weapons.Single(x => x.Id == "sunder");
        g.Press = g.Def.Press!.WithChain(null);
        g.CastSet = CastMode.Press;
    }

    /// <summary>Starts the storm and holds it for these seconds (a dummy, if any, pinned each tick). Events kept.</summary>
    static List<CombatEvent> Spin(Battle b, WeaponInst w, double seconds, Action? each = null)
    {
        var p = b.Player;
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
        var evs = b.Events.Drain().ToList();
        evs.AddRange(Run(b, seconds, () => { b.HoldSkill(w.Slot, true); each?.Invoke(); }));
        return evs;
    }

    static int Ticks(IEnumerable<CombatEvent> evs) => evs.Count(e => e is Ev.Spin { Phase: SpinPhase.Tick });
    static int Thrown(IEnumerable<CombatEvent> evs) => evs.Count(e => e is Ev.SpinLine { Phase: SpinLinePhase.Thrown });

    [Fact]
    public void Bladestorm_has_a_wick_of_three_strands()
    {
        var wick = Wicks.Of("bladestorm")!;
        Assert.Equal(["bladestorm.lines", "bladestorm.long", "bladestorm.hold"], wick.Strands);
        Assert.Equal("bladestorm.lines", wick.Suggested);
        var def = Weapons.Get("bladestorm");
        foreach (var s in Wicks.StrandsOf("bladestorm"))
            Assert.True(Wicks.Suits(s, def.Behavior, def.Tags, def.School, (def.Base.Splash ?? 0) > 0), s.Id);
        Assert.False(WickBook.NoWickYet("bladestorm"));
        Assert.StartsWith("Line on Line:", Wicks.Text("bladestorm", "bladestorm.lines.4"));
        Assert.StartsWith("Long Blade:", Wicks.Text("bladestorm", "bladestorm.long.4"));
        Assert.StartsWith("Hold Fast:", Wicks.Text("bladestorm", "bladestorm.hold.4"));

        var lines = Wicks.Turn("bladestorm.lines");
        Assert.Equal(2, lines.HeavyEvery);
        Assert.Equal(0.8, lines.Damage, 9);
        var lng = Wicks.Turn("bladestorm.long");
        Assert.Equal(1.3, lng.Area, 9);
        Assert.Equal(0.8, lng.Damage, 9);
        Assert.Contains("2nd", lines.Text); Assert.Contains("4th", lines.Text); Assert.Contains("20%", lines.Text);
        Assert.Contains("30%", lng.Text); Assert.Contains("20%", lng.Text);
        var hold = Wicks.Turn("bladestorm.hold");
        Assert.Contains("5th", hold.Text); Assert.Contains("3 s", hold.Text);

        var rule = Wicks.Strand("bladestorm", "bladestorm.hold")!.Rules![3].Single().Rule!;
        Assert.Equal("skill.status", rule.Rule);
        Assert.Equal(StatusKind.Chill, rule.Status);
        Assert.Equal("bladestorm", rule.Skill);

        foreach (var (strand, path) in new[] { ("bladestorm.lines", Lines4), ("bladestorm.long", Long4), ("bladestorm.hold", Hold4) })
        {
            var (b, w) = Storm(path);
            Assert.NotNull(w.Wick);
            Assert.Contains(strand, w.Wick!.Turns);
            Assert.Empty(w.Wick.Dark);
        }
    }

    [Fact]
    public void Line_on_Line_throws_a_line_every_second_turn()
    {
        var (b0, w0) = Storm();
        var evs0 = Spin(b0, w0, 3.2);
        var (b1, w1) = Storm(Lines4);
        var evs1 = Spin(b1, w1, 3.2);
        int t0 = Ticks(evs0), t1 = Ticks(evs1), l0 = Thrown(evs0), l1 = Thrown(evs1);
        output.WriteLine($"no wick: ticks {t0} thrown {l0}; Line on Line: ticks {t1} thrown {l1}");
        Assert.True(t0 >= 8, $"ticks {t0}");
        Assert.Equal(t0, t1);
        Assert.Equal(t0 / 4, l0);
        Assert.Equal(t1 / 2, l1);
        Assert.True(l1 >= 2 * l0 - 1);

        // Broken inside its window: the lines held (up to MaxLines) all split, so more lines struck.
        var (b2, w2) = Storm();
        Spin(b2, w2, 2.0);
        Assert.True(b2.PressSkill(b2.BreakSlot(w2), b2.Player.X + 2, b2.Player.Z));
        var (b3, w3) = Storm(Lines4);
        Spin(b3, w3, 2.0);
        Assert.True(b3.PressSkill(b3.BreakSlot(w3), b3.Player.X + 2, b3.Player.Z));
        output.WriteLine($"LinesStruck: no wick {b2.LinesStruck}, Line on Line {b3.LinesStruck}");
        Assert.True(b3.LinesStruck > b2.LinesStruck);
    }

    [Fact]
    public void Long_Blade_reaches_30_percent_further()
    {
        var (bn, wn) = Storm();
        var (bl, wl) = Storm(Long4);
        double rn = bn.SkillNumber(wn, "radius")!.Value, rl = bl.SkillNumber(wl, "radius")!.Value;
        output.WriteLine($"radius {rn} -> {rl}; damage {wn.Damage} -> {wl.Damage}");
        Assert.Equal(1.3 * 1.1, rl / rn, 6);
        Assert.Equal(0.8 * 1.1, wl.Damage / wn.Damage, 6);

        double Struck(Battle b, WeaponInst w)
        {
            var p = b.Player;
            var at = new List<(double, double)> { (p.X + 1.2 * rn, p.Z) };
            var es = new List<Enemy> { Dummy(b, at[0].Item1, at[0].Item2) };
            Run(b, 0.3, () => Pin(b, es, at));
            b.Events.Drain();
            Spin(b, w, 1.5, () => Pin(b, es, at));
            return es[0].MaxHp - es[0].Hp;
        }
        Assert.Equal(0, Struck(bn, wn));
        Assert.True(Struck(bl, wl) > 0);
    }

    [Fact]
    public void Hold_Fast_freezes_what_stays_in_the_storm()
    {
        var (b, w) = Storm(Hold4);
        var p = b.Player;
        var at = new List<(double, double)> { (p.X + 1.5, p.Z) };
        var es = new List<Enemy> { Dummy(b, at[0].Item1, at[0].Item2) };
        Run(b, 0.3, () => Pin(b, es, at));
        b.Events.Drain();
        int ticks = 0, chilledAt = -1, frozenAt = -1;
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, p.X + 2, p.Z));
        ticks = Ticks(b.Events.Drain());
        for (int i = 0; i < 200 && frozenAt < 0; i++)
        {
            b.HoldSkill(w.Slot, true);
            Pin(b, es, at);
            b.Tick(Dt, 0, 0);
            ticks += Ticks(b.Events.Drain());
            if (chilledAt < 0 && es[0].Status.Has(StatusKind.Chill)) chilledAt = ticks;
            if (es[0].Status.Has(StatusKind.Frozen)) frozenAt = ticks;
        }
        output.WriteLine($"chilled after blow {chilledAt}, frozen after blow {frozenAt}");
        Assert.Equal(1, chilledAt);
        Assert.Equal(5, frozenAt);

        // The three lead-ins alone (no Turn): no chill at all, and 5% more reach each.
        var (b3, w3) = Storm(Hold4.Take(3).ToArray());
        var q = b3.Player;
        var at3 = new List<(double, double)> { (q.X + 1.5, q.Z) };
        var es3 = new List<Enemy> { Dummy(b3, at3[0].Item1, at3[0].Item2) };
        Run(b3, 0.3, () => Pin(b3, es3, at3));
        b3.Events.Drain();
        bool chilled = false;
        Spin(b3, w3, 2.0, () => { Pin(b3, es3, at3); chilled |= es3[0].Status.Has(StatusKind.Chill) || es3[0].Status.Has(StatusKind.Frozen); });
        Assert.False(chilled);
        var (bn, wn) = Storm();
        Assert.Equal(1.15, b3.SkillNumber(w3, "radius")!.Value / bn.SkillNumber(wn, "radius")!.Value, 6);
    }
}
