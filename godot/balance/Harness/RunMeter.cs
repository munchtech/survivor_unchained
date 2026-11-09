using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>(M3) The numbers round's measures of one run (a zone, a map), the same in ZoneSim and MapSim.</summary>
public sealed class RunMeasures
{
    /// <summary>The longest stretch with no mark laid on her (H6's rule: under 45-60 s), on the fight clock (time with a roused
    /// foe within 24 m; walking the road between fights does not count) from its 0:45; and the marks counted.</summary>
    public double MarkGapMax = double.NaN;
    public int MarksOnHer;
    /// <summary>Resolve spent (and drained) a minute of fighting time, and the share of play it sat at its cap.</summary>
    public double ResolveSpentPerMin, ResolveFullPct;
    /// <summary>Presses a minute by skill (the hands' presses that went off).</summary>
    public Dictionary<string, double> PressesPerMin = new();
    /// <summary>Her damage by source, in % of the whole; the Flare's casts, first cast (s, -1 none), share of all and of bosses'.</summary>
    public Dictionary<string, double> DamageShare = new();
    public int FlareCasts;
    public double FlareFirst = -1, FlareShare, FlareBossShare = double.NaN;
    /// <summary>Falls: when, where and what took her.</summary>
    public List<string> Falls = new();
    public double Minutes;

    /// <summary>The run line's columns.</summary>
    public string Line() =>
        $"gap {(double.IsNaN(MarkGapMax) ? "-" : MarkGapMax.ToString("0"))}s marks {MarksOnHer} rspent {ResolveSpentPerMin:0}/min rfull {ResolveFullPct:0}% " +
        $"ppm {string.Join(",", PressesPerMin.OrderByDescending(kv => kv.Value).Select(kv => kv.Key + ":" + kv.Value.ToString("0.0")))} " +
        $"flare {FlareCasts}@{FlareFirst:0} {FlareShare:0}%/{(double.IsNaN(FlareBossShare) ? "-" : FlareBossShare.ToString("0"))}%boss " +
        $"dmg {string.Join(",", DamageShare.OrderByDescending(kv => kv.Value).Take(6).Select(kv => kv.Key + ":" + kv.Value.ToString("0")))}" +
        (Falls.Count > 0 ? $" falls [{string.Join("; ", Falls)}]" : "");

    static double Med(IEnumerable<double> xs) { var a = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList(); return a.Count == 0 ? double.NaN : a[a.Count / 2]; }
    static string F(double x, string f = "0") => double.IsNaN(x) ? "-" : x.ToString(f);

    /// <summary>The report's header and one row a group (medians; presses and shares summed over the runs, then per run).</summary>
    public const string Header = "| group | runs | mark gap in fights from 0:45 (s, med / worst) | Resolve spent /min | Resolve at max % | presses /min | damage shares % | Flare casts / first (s) / share % / boss share % | falls (where) |\n|---|---|---|---|---|---|---|---|---|";

    public static string Row(string name, IReadOnlyList<RunMeasures> l)
    {
        if (l.Count == 0) return "";
        var ppm = l.SelectMany(m => m.PressesPerMin).GroupBy(kv => kv.Key).ToDictionary(g => g.Key, g => g.Sum(kv => kv.Value) / l.Count);
        var dmg = l.SelectMany(m => m.DamageShare).GroupBy(kv => kv.Key).ToDictionary(g => g.Key, g => g.Sum(kv => kv.Value) / l.Count);
        var gaps = l.Select(m => m.MarkGapMax).Where(x => !double.IsNaN(x)).ToList();
        var falls = l.SelectMany(m => m.Falls).GroupBy(f => f.Split('@').ElementAtOrDefault(1)?.Trim() ?? f).OrderByDescending(g => g.Count()).Take(4).Select(g => $"{g.Key} x{g.Count()}");
        return $"| {name} | {l.Count} | {F(Med(gaps))} / {(gaps.Count > 0 ? gaps.Max().ToString("0") : "-")} | {F(Med(l.Select(m => m.ResolveSpentPerMin)))} | {F(Med(l.Select(m => m.ResolveFullPct)))} | " +
            $"{string.Join(", ", ppm.OrderByDescending(kv => kv.Value).Select(kv => $"{kv.Key} {kv.Value:0.0}"))} | {string.Join(", ", dmg.OrderByDescending(kv => kv.Value).Take(6).Select(kv => $"{kv.Key} {kv.Value:0}"))} | " +
            $"{F(Med(l.Select(m => (double)m.FlareCasts)))} / {F(Med(l.Where(m => m.FlareFirst >= 0).Select(m => m.FlareFirst)))} / {F(Med(l.Select(m => m.FlareShare)))} / {F(Med(l.Select(m => m.FlareBossShare)))} | {string.Join("; ", falls)} |";
    }
}

/// <summary>Steps alongside a run: the events drained each step and the meter's state.</summary>
public sealed class RunMeter
{
    readonly List<double> marksOn = new();
    double fullSec, playSec, fightSec;
    /// <summary>Falls are read from Ev.PlayerDeath (false: the caller tells them through Fell).</summary>
    public bool Deaths = true;

    /// <summary>A roused hostile within 24 m (ZoneSim's "fighting").</summary>
    public static bool Fighting(Battle b)
    {
        var p = b.Player;
        return b.Enemies.Living().Any(e => e.Roused && e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) < 24 * 24);
    }

    /// <summary>One step: `evs` are the battle's events drained this step (the caller drains once and passes them).</summary>
    public void Step(Battle b, double t, double dt, IEnumerable<CombatEvent> evs, bool fight)
    {
        var p = b.Player;
        playSec += dt;
        if (fight) fightSec += dt;
        if (b.Resolve.On && b.Resolve.Value >= b.Resolve.Max) fullSec += dt;
        foreach (var ev in evs)
            if (ev is Ev.Telegraph { Hostile: true, Phase: TellPhase.Warn } tg && ArenaSim.Covers(tg, p.X, p.Z, p.Radius)) marksOn.Add(fightSec);
            else if (Deaths && ev is Ev.PlayerDeath d) Fell(t, $"{d.Killer} @ ({p.X:0},{p.Z:0})");
    }

    readonly List<string> falls = new();
    /// <summary>A fall the caller knows of another way (a zone's own death hook).</summary>
    public void Fell(double t, string what) => falls.Add($"{t / 60:0.0}m {what}");

    /// <summary>The run's measures.</summary>
    public void Finish(Battle b, double t, RunMeasures m, PressHands? hands = null)
    {
        double until = fightSec;
        var on = marksOn.Where(x => x >= 45 && x < until).ToList();
        m.MarksOnHer = on.Count;
        if (until > 45)
        {
            double last = 45, gap = 0;
            foreach (var x in on) { gap = Math.Max(gap, x - last); last = x; }
            m.MarkGapMax = Math.Max(gap, until - last);
        }
        double min = Math.Max(1e-6, playSec / 60);
        m.Minutes = playSec / 60;
        m.ResolveSpentPerMin = b.Resolve.Spent / min;
        m.ResolveFullPct = 100 * fullSec / Math.Max(1e-6, playSec);
        if (hands != null) foreach (var (k, v) in hands.Presses) m.PressesPerMin[k] = v / min;
        double all = b.DamageBy.Values.Sum();
        foreach (var (k, v) in b.DamageBy) if (v > 0) m.DamageShare[k] = 100 * v / Math.Max(1, all);
        m.FlareCasts = b.FlareCasts;
        m.FlareFirst = b.FlareTimes.Count > 0 ? b.FlareTimes[0] : -1;
        m.FlareShare = 100 * b.DamageBy.GetValueOrDefault("flare") / Math.Max(1, all);
        double boss = b.BossDamageBy.Values.Sum();
        if (boss > 0) m.FlareBossShare = 100 * b.BossDamageBy.GetValueOrDefault("flare") / boss;
        m.Falls.AddRange(falls);
    }
}
