using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>(iron-vow-a, 22 Nov; the owner picked BUILD_DIRECTION Round 10 option A, "a warcry vow") Iron Vow's press goads
/// the lesser foes near her to her for the brace, so the burst always has blows to store, and the burst has a floor.</summary>
public sealed class IronVowWarcryTests(ITestOutputHelper output)
{
    const double Dt = 1 / 60.0;

    static Battle Fight()
    {
        var b = BattleTests.Arena(21, ("iron_vow", 1));
        b.Calling = null;
        foreach (var w in b.Weapons) w.Timer = 0;
        b.Weapons.Single(x => x.Id == "iron_vow").CastSet = CastMode.Press;
        b.Player.Hp = 1e6;
        return b;
    }

    static Enemy Foe(Battle b, double x, double z, string def = "footpad", bool elite = false, bool boss = false)
    {
        var e = b.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Elite = elite, Boss = boss })!;
        e.Hp = e.MaxHp = 1e7;
        return e;
    }

    static void Step(Battle b, double seconds, Func<bool>? until = null)
    {
        for (double t = 0; t < seconds - 1e-9; t += Dt) { b.Tick(Dt, 0, 0); b.Events.Drain(); if (until?.Invoke() == true) break; }
    }

    [Fact]
    public void The_press_goads_the_lesser_foes_within_six_metres_and_not_elites_bosses_or_the_far()
    {
        var b = Fight();
        var w = b.Weapons.Single(x => x.Id == "iron_vow");
        Assert.Equal(6, w.Num(s => s.Goad));
        var p = b.Player;
        var near = Foe(b, p.X + 4, p.Z);
        var archer = Foe(b, p.X, p.Z + 5.5, "risen_archer");
        var far = Foe(b, p.X - 8, p.Z);
        var elite = Foe(b, p.X - 3, p.Z, elite: true);
        var boss = Foe(b, p.X, p.Z - 4, boss: true);
        Step(b, 0.05);
        Assert.True(b.PressSkill(w.Slot, p.X, p.Z));
        Assert.True(b.RuleGoaded(near));
        Assert.True(b.RuleGoaded(archer));
        Assert.False(b.RuleGoaded(far));
        Assert.False(b.RuleGoaded(elite));
        Assert.False(b.RuleGoaded(boss));
        // It lasts the plant and the brace, and ends with the burst.
        Step(b, 2.0);
        Assert.True(b.Bracing);
        Assert.True(b.RuleGoaded(near));
        Step(b, 1.0, () => !b.Bracing);
        Assert.False(b.Bracing);
        Assert.False(b.RuleGoaded(near));
        Assert.False(b.RuleGoaded(archer));
    }

    /// <summary>An archer goaded by the vow closes on her (its own want keeps its range), so its blows are hers to store.</summary>
    [Fact]
    public void A_goaded_archer_comes_to_her_where_an_ungoaded_one_keeps_its_range()
    {
        double Closest(bool press)
        {
            var b = Fight();
            var w = b.Weapons.Single(x => x.Id == "iron_vow");
            var p = b.Player;
            var e = Foe(b, p.X + 5.5, p.Z, "risen_archer");
            e.Roused = true;
            Step(b, 0.05);
            if (press) Assert.True(b.PressSkill(w.Slot, p.X, p.Z));
            double least = double.MaxValue;
            for (double t = 0; t < 2.2; t += Dt)
            {
                b.Tick(Dt, 0, 0); b.Events.Drain();
                least = Math.Min(least, Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)));
            }
            return least;
        }
        double free = Closest(false), goaded = Closest(true);
        output.WriteLine($"archer's closest in 2.2 s: {free:0.00} m free, {goaded:0.00} m goaded");
        Assert.True(goaded < 2.0, $"goaded archer only came to {goaded:0.00} m");
        Assert.True(goaded < free - 1.5, $"goaded {goaded:0.00} m against free {free:0.00} m");
    }

    /// <summary>The floor: a burst with nothing stored strikes for 1.5 x its damage; a stored one past that is the store's.</summary>
    [Fact]
    public void An_empty_burst_strikes_at_the_floor_and_a_stored_one_above_it()
    {
        (double Dealt, double Stored) Dealt(double blow)
        {
            var b = Fight();
            var w = b.Weapons.Single(x => x.Id == "iron_vow");
            var p = b.Player;
            var e = Foe(b, p.X + 1.5, p.Z);
            e.AttackT = e.RangedT = 999;
            Assert.True(b.PressSkill(w.Slot, p.X, p.Z));
            Step(b, 1.0);
            e.X = p.X + 1.5; e.Z = p.Z; e.Vx = e.Vz = 0; e.AttackT = 999;
            if (blow > 0) { p.Iframes = 0; b.HurtPlayer(blow, School.Physical, "test", null); }
            double h0 = e.Hp, stored = b.VowStored;
            Step(b, 2.0, () => !b.Bracing);
            Assert.False(b.Bracing);
            return (h0 - e.Hp, stored);
        }
        var w0 = Fight().Weapons.Single(x => x.Id == "iron_vow");
        Assert.Equal(1.5, w0.Num(s => s.Floor));
        var (empty, _) = Dealt(0);
        var (small, ss) = Dealt(5);
        var (big, sb) = Dealt(200);
        output.WriteLine($"base {w0.Damage:0.0}: empty {empty:0.0}; a 5 blow stored {ss:0.0}, {small:0.0}; a 200 blow stored {sb:0.0}, {big:0.0}");
        // A small blow's store x3 is under the floor's half-again: it strikes as the empty one.
        Assert.True(ss > 0 && ss * 3 < w0.Damage * 0.5);
        Assert.Equal(empty, small, 6);
        Assert.True(big > empty * 2, $"a stored burst {big:0.0} against the floor {empty:0.0}");
        Assert.Equal((w0.Damage + sb * 3) / (w0.Damage * 1.5), big / empty, 3);
    }

    /// <summary>(measuring only: IRONVOW_MEASURE=1) The den at level 9 (Iron Vow on the bar), the deft bot, three seeds: each
    /// burst's store, ring count and damage, and the den's pack times (DenFeel), to pick the floor and to see the den move.</summary>
    [Fact]
    public void Measure_the_vow_in_the_den()
    {
        if (Environment.GetEnvironmentVariable("IRONVOW_MEASURE") != "1") return;
        int level = int.TryParse(Environment.GetEnvironmentVariable("IRONVOW_LEVEL"), out var lv) ? lv : 9;
        var seeds = new[] { 1, 2, 3 };
        var bursts = new List<(int Seed, double Stored, int Hit, double Dmg)>();
        int presses = 0;
        var ratios = new List<double>();
        var diag = new List<(int Near, double Stored, double Lost)>();
        var gate = new object();
        Parallel.ForEach(seeds, seed =>
        {
            double lastBy = 0;
            int pressed = 0, nearAt = 0; double hpAt = 0;
            var mine = new List<(int, double, int, double)>();
            var pending = new List<(double Stored, int Hit)>();
            MapSim.Tap = (t, evs, b, boss) =>
            {
                double by = b.DamageBy.GetValueOrDefault("iron_vow");
                foreach (var ev in evs)
                {
                    if (ev is Ev.Brace { Phase: BracePhase.Start }) { pressed++; nearAt = b.HostilesInRadius(b.Player.X, b.Player.Z, 6).Count(e => !e.Elite && !e.Boss); hpAt = b.Player.Hp; }
                    if (ev is Ev.Brace { Phase: BracePhase.Burst } bz) lock (gate) diag.Add((nearAt, bz.Stored, hpAt - b.Player.Hp));
                    if (ev is Ev.Brace { Phase: BracePhase.Burst } br) pending.Add((br.Stored, br.Hit));
                    if (ev is Ev.Brace { Phase: BracePhase.Burst } bq && b.Weapons.FirstOrDefault(w => w.Id == "iron_vow") is { } vw) lock (gate) ratios.Add(1 + bq.Stored * (vw.Num(s => s.StoreMul) ?? 3) / vw.Damage);
                }
                if (pending.Count > 0) { foreach (var p in pending) mine.Add((seed, p.Stored, p.Hit, (by - lastBy) / pending.Count)); pending.Clear(); }
                lastBy = by;
            };
            MapSim.Play(new MapRunSpec(seed, "warden", 1, DungeonGen.Get("hollow")!.People, level, 1, [], "deft", 8, "hollow"));
            MapSim.Tap = null;
            lock (gate) { bursts.AddRange(mine); presses += pressed; }
        });
        if (bursts.Count > 0)
        {
            var st = bursts.Select(x => x.Stored).OrderBy(x => x).ToList();
            var dm = bursts.Select(x => x.Dmg).OrderBy(x => x).ToList();
            var hit = bursts.Select(x => (double)x.Hit).OrderBy(x => x).ToList();
            double Q(List<double> l, double q) => l[Math.Min(l.Count - 1, (int)(q * l.Count))];
            output.WriteLine($"L{level}: presses {presses}, bursts {bursts.Count}; stored p10/p50/p90 {Q(st, .1):0.0}/{Q(st, .5):0.0}/{Q(st, .9):0.0}, zero-store {st.Count(x => x < 1e-6)}; ring p50 {Q(hit, .5):0} (empty {hit.Count(x => x == 0)}); damage dealt per burst p10/p50/p90 {Q(dm, .1):0}/{Q(dm, .5):0}/{Q(dm, .9):0}");
        }
        else output.WriteLine($"L{level}: presses {presses}, no bursts");
        if (ratios.Count > 0) { var rr = ratios.OrderBy(x => x).ToList(); output.WriteLine($"L{level}: burst over its base (1 + stored x storeMul / damage) p25/p50/p75/p90/max {rr[rr.Count / 4]:0.00}/{rr[rr.Count / 2]:0.00}/{rr[rr.Count * 3 / 4]:0.00}/{rr[rr.Count * 9 / 10]:0.00}/{rr[^1]:0.00}; mean {rr.Average():0.00}"); }
        foreach (var g in diag.GroupBy(d => d.Stored > 0).OrderBy(g => g.Key))
            output.WriteLine($"L{level}: {(g.Key ? "stored" : "nothing stored")} {g.Count()}: lesser within 6 m at the press mean {g.Average(d => d.Near):0.0} (none {g.Count(d => d.Near == 0)}); her life over the brace {g.Average(d => d.Lost):0.0}");
        var runs = seeds.AsParallel().Select(seed => DenFeel.Play(new MapRunSpec(seed, "warden", 1, DungeonGen.Get("hollow")!.People, level, 1, [], "deft", 8, "hollow"))).ToList();
        var packs = runs.SelectMany(r => r.Packs).Where(p => p.Killed && p.FirstHit >= 0).ToList();
        var normal = packs.Where(p => p.Grade == 0).Select(p => p.LastDeath - p.FirstHit).OrderBy(x => x).ToList();
        double ttk = normal.Count > 0 ? normal[normal.Count / 2] : -1, together = packs.Count(p => p.Together >= 0.4) / (double)Math.Max(1, packs.Count);
        double lanes = runs.Sum(r => r.Lanes) / Math.Max(1, runs.Sum(r => r.RoomFight)) * 8;
        output.WriteLine($"L{level} den: {packs.Count} packs killed; normal TTK p50 {ttk:0.0} s ({normal.Count}); together >=40% {together:P0}; lanes {lanes:0.00} per 8 s; cleared {runs.Count(r => r.R.Cleared)}/3, falls {runs.Sum(r => r.R.Falls)}");
    }
}
