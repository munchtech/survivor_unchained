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
    /// <summary>(M3 round 4) The Flare's share of the life the bosses lost (BossHealthBy: a gate's overflow past its Break counts not).</summary>
    public double FlareBossLife = double.NaN;
    /// <summary>(M3 round 3) Casts whose blows reached a boss, and what filled the meter (by why, in meters of 100).</summary>
    public int FlareOnBoss;
    public string FlareFills = "";
    /// <summary>Falls: when, where and what took her.</summary>
    public List<string> Falls = new();
    /// <summary>(M3 round 2) Each fall's last 5 s: the blows on her (marked by their label or not, their source), her life,
    /// what she did (dash, leap, presses), the marks laid on her and dodged, and how near the boss stood.</summary>
    public List<string> FallNotes = new();
    /// <summary>(round 2) Her lowest life (a share of max), and the damage taken by source, in max lives (the marked kit's
    /// blows by their label).</summary>
    public double LowLife = 1;
    public Dictionary<string, double> Taken = new();
    public double Minutes;
    /// <summary>(M3 MR 3) The grip's column (Sim/GripMeter.cs): holds, the median hold, the share held, blows, damage and Resolve built.</summary>
    public string Grip = "";
    /// <summary>(M3 lead 16 b6, harness-only) The grips' landed weight by source (GripMeter.SrcLine).</summary>
    public string Src = "";
    /// <summary>(bd-sockets, harness-only) Bladestorm's run: storms started, broken (Sunder's key), ended dry (Resolve 0) or
    /// released, seconds spun, Resolve at its starts (mean), and the seconds a crowd stood round her (4 within 3.5 m, the
    /// plan's "when") with the storm ready but Resolve under its start breath (drain x gap): the storm starved.</summary>
    public int StormStarts, StormBreaks, StormDry, StormReleased;
    public double StormSec, StormResolveAtStart = double.NaN, StormCrowdSec, StormStarvedSec;
    public bool StormCarried;
    public string StormLine() => !StormCarried ? "storm -" :
        $"storm starts {StormStarts} breaks {StormBreaks} dry {StormDry} released {StormReleased} spun {StormSec:0}s r@start {(double.IsNaN(StormResolveAtStart) ? "-" : StormResolveAtStart.ToString("0"))} crowd-ready {StormCrowdSec:0}s starved {StormStarvedSec:0}s";

    /// <summary>The run line's columns.</summary>
    public string Line() =>
        $"gap {(double.IsNaN(MarkGapMax) ? "-" : MarkGapMax.ToString("0"))}s marks {MarksOnHer} rspent {ResolveSpentPerMin:0}/min rfull {ResolveFullPct:0}% " +
        $"ppm {string.Join(",", PressesPerMin.OrderByDescending(kv => kv.Value).Select(kv => kv.Key + ":" + kv.Value.ToString("0.0")))} " +
        $"flare {FlareCasts}@{FlareFirst:0} {FlareShare:0}%/{(double.IsNaN(FlareBossShare) ? "-" : FlareBossShare.ToString("0"))}%boss life {(double.IsNaN(FlareBossLife) ? "-" : FlareBossLife.ToString("0"))}% onboss {FlareOnBoss} fills {FlareFills} " +
        $"dmg {string.Join(",", DamageShare.OrderByDescending(kv => kv.Value).Select(kv => kv.Key + ":" + kv.Value.ToString("0")))} {StormLine()}" +
        (Falls.Count > 0 ? $" falls [{string.Join("; ", Falls)}]" : "") +
        $" low {LowLife:0.00} taken {string.Join(",", Taken.Where(kv => kv.Key[0] is not ('#' or '+')).OrderByDescending(kv => kv.Value).Take(6).Select(kv => kv.Key + ":" + kv.Value.ToString("0.0")))}" +
        $" healed {string.Join(",", Taken.Where(kv => kv.Key[0] == '+').OrderByDescending(kv => kv.Value).Take(4).Select(kv => kv.Key[1..] + ":" + kv.Value.ToString("0.0")))}" +
        $" kit {string.Join(",", Taken.Where(kv => kv.Key[0] == '#').OrderBy(kv => kv.Key).Select(kv => kv.Key[1..].Replace("caught ", "c.").Replace("missed ", "m.") + ":" + kv.Value.ToString("0")))}" + (Grip.Length > 0 ? " " + Grip : "") + (Src.Length > 0 ? " " + Src : "");

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
        var falls = l.SelectMany(m => m.Falls).GroupBy(f => System.Text.RegularExpressions.Regex.Replace(f, @"^\d+(\.\d+)?m ", "")).OrderByDescending(g => g.Count()).Take(4).Select(g => $"{g.Key} x{g.Count()}");
        return $"| {name} | {l.Count} | {F(Med(gaps))} / {(gaps.Count > 0 ? gaps.Max().ToString("0") : "-")} | {F(Med(l.Select(m => m.ResolveSpentPerMin)))} | {F(Med(l.Select(m => m.ResolveFullPct)))} | " +
            $"{string.Join(", ", ppm.OrderByDescending(kv => kv.Value).Select(kv => $"{kv.Key} {kv.Value:0.0}"))} | {string.Join(", ", dmg.OrderByDescending(kv => kv.Value).Take(6).Select(kv => $"{kv.Key} {kv.Value:0}"))} | " +
            $"{F(Med(l.Select(m => (double)m.FlareCasts)))} / {F(Med(l.Where(m => m.FlareFirst >= 0).Select(m => m.FlareFirst)))} / {F(Med(l.Select(m => m.FlareShare)))} / {F(Med(l.Select(m => m.FlareBossShare)))} | {string.Join("; ", falls)} |";
    }
}

/// <summary>(M3 MR 3 m2) Cuts per fodder: the grip's cuts (Sunder's and Oathblade's hits: Ev.Hit.Weapon; not a status
/// tick, not the Flare's) that LANDED on each body before it died, whoever dealt the last blow (two cuts and a
/// Groundbreaker that finishes it count two). Told for fodder (not elite, not boss) the survivor's side killed, the
/// Flare's kills left out; fodder no cut touched is counted apart.</summary>
public sealed class FodderCuts
{
    readonly Dictionary<int, int> on = new();
    /// <summary>Each fodder killed with a cut on it: its cuts.</summary>
    public readonly List<int> Counts = new();
    /// <summary>Fodder killed that no cut touched.</summary>
    public int Uncut;

    public static bool IsCut(Ev.Hit h) => !h.Dot && !h.ByFlare && h.Amount > 0 && h.Weapon is "sunder" or "oathblade";

    /// <summary>One drained event, in the battle's order (a killing hit is told before its kill).</summary>
    public void Read(CombatEvent ev)
    {
        switch (ev)
        {
            case Ev.Hit h when IsCut(h): on[h.Target] = on.GetValueOrDefault(h.Target) + 1; break;
            // (ids are pool slots: a death clears its count, the survivor's or not, and so does a new body in the slot)
            case Ev.Spawn s: on.Remove(s.Enemy); break;
            case Ev.Kill k:
                bool cut = on.Remove(k.Enemy, out int n);
                if (!k.ByPlayer || k.Elite || k.Boss) break;
                if (!cut) Uncut++;
                else if (!k.ByFlare) Counts.Add(n);
                break;
        }
    }

    public double Mean => Counts.Count == 0 ? double.NaN : Counts.Average();
    /// <summary>The median (the upper of two middles, as the report's medians).</summary>
    public double Median { get { if (Counts.Count == 0) return double.NaN; var a = Counts.OrderBy(x => x).ToList(); return a[a.Count / 2]; } }

    /// <summary>The run line's column, after the grip's.</summary>
    public string Line() => Counts.Count == 0 ? $"cuts/fodder mean - med - n 0 uncut {Uncut}" : $"cuts/fodder mean {Mean:0.00} med {Median:0} n {Counts.Count} uncut {Uncut}";
}

/// <summary>Steps alongside a run: the events drained each step and the meter's state.</summary>
public sealed class RunMeter
{
    readonly List<double> marksOn = new();
    double fullSec, playSec, fightSec;
    readonly GripMeter grip = new();
    readonly FodderCuts cuts = new();
    // (bd-sockets) Bladestorm's counters (RunMeasures.StormLine)
    int stStarts, stBreaks, stDry, stRel; double stSec, stCrowd, stStarved, stR0; bool stCarried;
    // (round 2: the last seconds before a fall)
    readonly Queue<(double T, string What)> recent = new();
    readonly Queue<(double T, double Life)> life = new();
    double lifeAt = double.NegativeInfinity;
    /// <summary>Set by the caller's death hook (inside the step's tick): the fall is told once this step's events are read.</summary>
    public string? PendingFall;
    readonly List<string> notes = new();
    readonly Dictionary<string, double> taken = new();
    double low = 1;
    /// <summary>What the hands were doing (the caller's word, e.g. aware or not), read into a fall's note.</summary>
    public Func<string>? Doing;
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
        if (b.Campaign && fight) grip.Step(b, dt, evs as IReadOnlyList<CombatEvent> ?? evs.ToList());
        StormStep(b, dt, fight);
        foreach (var ev in evs)
        {
            if (ev is Ev.Telegraph { Hostile: true, Phase: TellPhase.Warn } tg && ArenaSim.Covers(tg, p.X, p.Z, p.Radius)) { marksOn.Add(fightSec); recent.Enqueue((t, "mark")); }
            else if (Deaths && ev is Ev.PlayerDeath d) Fell(t, $"{d.Killer} @ ({p.X:0},{p.Z:0})");
            if (b.Campaign) cuts.Read(ev);
            if (ev is Ev.Spin sp)
                switch (sp.Phase)
                {
                    case SpinPhase.Start: stStarts++; stR0 += b.Resolve.Value; StormTrace(b, "start"); break;
                    case SpinPhase.Break: stBreaks++; StormTrace(b, "break"); break;
                    case SpinPhase.End: if (b.Resolve.On && b.Resolve.Value <= 0.5) stDry++; else stRel++; StormTrace(b, "end"); break;
                }
            switch (ev)
            {
                case Ev.PlayerHit { Dodged: true }: recent.Enqueue((t, "dodged")); break;
                case Ev.PlayerHit h when h.Amount > 0 || h.Blocked:
                    { string k = h.Label != null ? "[" + h.Label + "]" : h.Source; taken[k] = taken.GetValueOrDefault(k) + h.Amount / Math.Max(1, b.MaxHp); }
                    recent.Enqueue((t, $"{(h.Blocked ? "blocked " : "")}{h.Amount:0} {h.Source}{(h.Label != null ? "[" + h.Label + "]" : h.Dot ? "(dot)" : "(unmarked)")}")); break;
                case Ev.Dash: recent.Enqueue((t, "DASH")); break;
                case Ev.Telegraph { Phase: TellPhase.Land, Tell: { } kind } tl:
                    { string k = (tl.Caught ? "caught " : "missed ") + kind; taken["#" + k] = taken.GetValueOrDefault("#" + k) + 1; if (tl.Caught) recent.Enqueue((t, "CAUGHT " + kind)); } break;
                case Ev.Leap { Phase: LeapPhase.Takeoff } lp: recent.Enqueue((t, $"LEAP {Math.Sqrt((lp.X1 - lp.X0) * (lp.X1 - lp.X0) + (lp.Z1 - lp.Z0) * (lp.Z1 - lp.Z0)):0}m")); break;
                case Ev.Cast c when c.Weapon is not ("sunder" or "oathblade"): recent.Enqueue((t, "cast " + c.Weapon)); break;
                case Ev.KindlePress kp: recent.Enqueue((t, "key " + kp.Weapon)); break;
            }
        }
        if (p.Alive) low = Math.Min(low, p.Hp / Math.Max(1, b.MaxHp));
        if (t - lifeAt >= 0.5) { lifeAt = t; life.Enqueue((t, p.Alive ? p.Hp / Math.Max(1, b.MaxHp) : 0)); }
        while (recent.Count > 0 && recent.Peek().T < t - 5) recent.Dequeue();
        while (life.Count > 0 && life.Peek().T < t - 5) life.Dequeue();
        if (PendingFall != null)
        {
            var boss = b.Enemies.Living().Where(e => e.Boss || e.Named != null).OrderBy(e => (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)).FirstOrDefault();
            string bossAt = boss == null ? "" : $" {boss.Def.Id} {Math.Sqrt((boss.X - p.X) * (boss.X - p.X) + (boss.Z - p.Z) * (boss.Z - p.Z)):0.0}m {boss.State}";
            // (the blows and acts grouped: each as -s before the fall)
            var acts = recent.Select(x => $"-{t - x.T:0.0} {x.What}");
            notes.Add($"{t / 60:0.0}m {PendingFall}{bossAt}{(Doing != null ? " " + Doing() : "")} | life {string.Join(">", life.Select(l => (100 * l.Life).ToString("0")))} | {string.Join(", ", acts)}");
            PendingFall = null;
        }
    }

    static readonly bool stormTrace = Environment.GetEnvironmentVariable("STORM_TRACE") == "1";
    static void StormTrace(Battle b, string what)
    {
        if (!stormTrace) return;
        var w = b.Weapons.Find(x => x.Id == "bladestorm");
        var p = b.Player;
        Console.WriteLine($"    STORM {what} t {b.Time:0.00} ch {w?.ChannelT:0.00} spun {w?.StormT:0.00} ticks {w?.SpinTicks} lines {w?.Lines.Count} near3.5 {b.HostilesInRadius(p.X, p.Z, 3.5).Count} resolve {b.Resolve.Value:0} held {w?.Held} leap {p.Leap != null} dash {p.DashT > 0} chmax {w?.ChannelMax:0.0}");
    }

    void StormStep(Battle b, double dt, bool fight)
    {
        WeaponInst? w = null;
        foreach (var x in b.Weapons) if (x.Id == "bladestorm") { w = x; break; }
        if (w == null) return;
        stCarried = true;
        if (w.Channeling) { stSec += dt; return; }
        if (!fight || w.Timer > 0 || w.DisabledT > 0) return;
        var p = b.Player;
        int n = 0;
        foreach (var e in b.Enemies.Living())
            if (e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) < 3.5 * 3.5) n++;
        if (n < 4) return;
        stCrowd += dt;
        if (b.Resolve.On && w.Press?.Drain is double dr && dr > 0 && b.Resolve.Value < dr * w.ChannelEvery) stStarved += dt;
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
        if (b.Campaign) { m.Grip = grip.Line(fightSec, b.Time) + " " + cuts.Line(); m.Src = grip.SrcLine(fightSec); }
        m.ResolveSpentPerMin = b.Resolve.Spent / min;
        (m.StormCarried, m.StormStarts, m.StormBreaks, m.StormDry, m.StormReleased, m.StormSec, m.StormCrowdSec, m.StormStarvedSec) = (stCarried, stStarts, stBreaks, stDry, stRel, stSec, stCrowd, stStarved);
        if (stStarts > 0) m.StormResolveAtStart = stR0 / stStarts;
        m.ResolveFullPct = 100 * fullSec / Math.Max(1e-6, playSec);
        if (hands != null) foreach (var (k, v) in hands.Presses) m.PressesPerMin[k] = v / min;
        double all = b.DamageBy.Values.Sum();
        foreach (var (k, v) in b.DamageBy) if (v > 0) m.DamageShare[k] = 100 * v / Math.Max(1, all);
        m.FlareCasts = b.FlareCasts;
        m.FlareFirst = b.FlareTimes.Count > 0 ? b.FlareTimes[0] : -1;
        m.FlareOnBoss = b.FlareCastsOnBoss;
        m.FlareFills = string.Join(",", b.FlareFills.OrderByDescending(kv => kv.Value).Select(kv => kv.Key + ":" + (kv.Value / Battle.FlareFull).ToString("0.0")));
        m.FlareShare = 100 * b.DamageBy.GetValueOrDefault("flare") / Math.Max(1, all);
        double boss = b.BossDamageBy.Values.Sum();
        if (boss > 0) m.FlareBossShare = 100 * b.BossDamageBy.GetValueOrDefault("flare") / boss;
        double life = b.BossHealthBy.Values.Sum();
        if (life > 0) m.FlareBossLife = 100 * b.BossHealthBy.GetValueOrDefault("flare") / life;
        m.Falls.AddRange(falls);
        m.FallNotes.AddRange(notes);
        m.LowLife = low;
        foreach (var (k, v) in taken) m.Taken[k] = v;
        foreach (var (k, v) in b.HealBy) m.Taken["+" + k] = v / Math.Max(1, b.MaxHp);
    }
}
