using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>(P3, DEN_ROSTER.md "Clear-feel targets") The den's clear feel, measured on MapSim's runs through its taps:
/// each pack's time to kill (from its first roused member, and from her first blow on it), the share of its melee members
/// inside 3.5 m of her first area blow that reaches it (a Heroic Leap's landing or a Bladestorm's start), the most of it
/// that fell inside one 1.5 s window, and the red lanes (hostile line marks, not a ruler's) in the rooms' fights.
/// `dotnet run --project godot/balance -- denfeel --bots deft --seeds 3 [--seed0 1] [--level 6] [--gear 1] [--cap 8]`.</summary>
public static class DenFeel
{
    public const double AreaR = 3.5, Window = 1.5, SeenR = 20, LeapAt = 9;

    public sealed class PackRow
    {
        public string Recipe = ""; public int Grade, Size;
        public double Woke = -1, FirstHit = -1, LastDeath = -1;
        public bool Killed;
        /// <summary>Share of its live melee members within AreaR of the first area blow that reached any of it (-1: none did).</summary>
        public double Inside = -1;
        /// <summary>(den first blow, 22 Nov) The same share over the pack as it stood when the blow landed: the members the blow
        /// itself felled are counted (Inside drops them from the pack and from the count, so a landing that kills what it
        /// catches reads as catching little or nothing). Fell1: the melee members that fell on that step. KindAll: 'L' / 'S'.</summary>
        public double InsideAll = -1; public int Fell1; public char KindAll = '-';
        /// <summary>(diagnostic) The first area blow's kind ('L' leap, 'S' spin), its seconds after the wake, and the best share any area blow caught.</summary>
        public char FirstKind = '-'; public double FirstLag = -1, Best = -1;
        /// <summary>The most of the pack that fell inside one Window (a share of its size).</summary>
        public double Together;
        public readonly List<double> Deaths = new();
        /// <summary>(diagnostic) At the first area blow: each live melee member's kind and its distance from the blow's centre.</summary>
        public readonly List<(string Def, double D)> AtFirst = new();
        /// <summary>A first blow that is a Bladestorm: the share of the melee members live at its start that came inside AreaR
        /// at any time while that spin channelled (a spin catches what walks into it; -1: the first blow was a leap or none).</summary>
        public double SpinWhole = -1;
        public HashSet<Enemy>? SpinBase, SpinCaught;
        /// <summary>(diagnostic) The first blow's melee members, and the share of them inside AreaR of her 1 s after it (-1: not yet).</summary>
        /// <summary>(diagnostic) At the wake: a wall between her and the pack's home (it comes round or through a door).</summary>
        public bool Walled;
        /// <summary>The opener variant pressed its opener on this pack ('L' leap, 'S' spin; '-' not).</summary>
        public char Opener = '-';
        /// <summary>(diagnostic) The most of its live melee members inside AreaR of her on any step before the first of it fell, and
        /// the share of its melee members that a blow of hers has already reached by its first area blow.</summary>
        public double Peak = -1, HitBefore = -1;
        public List<Enemy>? Base1; public double Due1 = -1, Inside1 = -1;
        /// <summary>(first-blow item) Its spread, arrivals and leap landing: DenCause.</summary>
        public readonly DenCause.Row C = new();
    }

    public sealed class Run
    {
        public MapRunResult R = null!;
        /// <summary>The bot, with "+open" for the opener variant.</summary>
        public string Label = "";
        public int Opened;
        public readonly List<PackRow> Packs = new();
        public double RoomFight, LaneSecOver1;
        public int Lanes, Circles, MaxLanes;
    }

    /// <summary>`opener` (measuring only, the coordinator 22 Nov): before the bot's hands act, a fresh roused pack (none of it hit or
    /// fallen) is opened with Heroic Leap at its melee's middle when that is within LeapAt m and none of it is yet in her
    /// reach, else with Bladestorm once one of it is inside AreaR of her. The default bots and the shipped plan are untouched.</summary>
    /// <summary>`lead` (measuring only, the coordinator 22 Nov): the opener, but its Leap aims where the pack's middle will be when
    /// she lands (its middle's speed over LeapAir s), as a player leading with the cursor would: it separates "the pack cannot
    /// be caught" from "the bot aims late". Her skill is untouched.</summary>
    public const double LeapAir = 0.62;
    public static Run Play(MapRunSpec spec, bool opener = false, bool lead = false)
    {
        var run = new Run { Label = spec.Bot + (lead ? "+lead" : opener ? "+open" : "") };
        var last = new Dictionary<object, (double X, double Z, double T)>();
        var vel = new Dictionary<object, (double X, double Z)>();
        MapRun? zone = null;
        var rows = new Dictionary<object, PackRow>();
        var dead = new HashSet<(Enemy, double)>();
        var lanes = new List<double>();
        bool spinning = false;
        MapSim.ZoneTap = z => zone = z;
        if (opener || lead) MapSim.PreAct = b =>
        {
            var p = b.Player;
            if (zone == null || !p.Alive || p.Leap != null || b.Weapons.Any(w => w.Channeling)) return;
            var leap = b.Weapons.FirstOrDefault(w => w.Id == "heroic_leap");
            var storm = b.Weapons.FirstOrDefault(w => w.Id == "bladestorm");
            foreach (var (_, _, members) in zone.PackLives)
            {
                var live = members.Where(m => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying).Select(m => m.E).ToList();
                var melee = live.Where(e => Melee(e.Def)).ToList();
                if (melee.Count == 0 || live.Count < members.Count || !live.Any(e => e.Roused) || live.Any(e => e.Hp < e.MaxHp)) continue;
                double cx = melee.Average(e => e.X), cz = melee.Average(e => e.Z);
                double near = melee.Min(e => Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) - e.Radius);
                double mid = Math.Sqrt((cx - p.X) * (cx - p.X) + (cz - p.Z) * (cz - p.Z));
                double ax = cx, az = cz;
                if (lead && vel.TryGetValue(members, out var v)) { ax += v.X * LeapAir; az += v.Z * LeapAir; mid = Math.Sqrt((ax - p.X) * (ax - p.X) + (az - p.Z) * (az - p.Z)); }
                if (leap != null && leap.Timer <= 0 && mid <= LeapAt && (!lead || mid >= 3) && near > 2.5 && b.PressSkill(leap.Slot, ax, az)) { run.Opened++; if (rows.TryGetValue(members, out var ro)) ro.Opener = 'L'; return; }
                if (storm != null && storm.Timer <= 0 && near < AreaR && b.PressSkill(storm.Slot, p.X, p.Z)) { run.Opened++; if (rows.TryGetValue(members, out var ro)) ro.Opener = 'S'; return; }
            }
        };
        MapSim.Tap = (t, evs, b, bossUp) =>
        {
            if (zone == null) return;
            var p = b.Player;
            // The area blows this step: a leap's landing, a spin's first step.
            var areas = new List<(double X, double Z, char K)>();
            foreach (var ev in evs) if (ev is Ev.Leap { Phase: LeapPhase.Land } lp) areas.Add((lp.X1, lp.Z1, 'L'));
            bool spinNow = b.Weapons.Any(w => w.Channeling && w.Behavior == WeaponBehavior.Spin);
            if (spinNow && !spinning) areas.Add((p.X, p.Z, 'S'));
            spinning = spinNow;
            foreach (var (recipe, grade, members) in zone.PackLives)
            {
                if (!rows.TryGetValue(members, out var row)) rows[members] = row = new PackRow { Recipe = recipe, Grade = grade, Size = members.Count };
                if (row.Killed) continue;
                bool anyLive = false;
                var fell = new List<Enemy>();
                foreach (var m in members)
                {
                    bool live = m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying;
                    if (live)
                    {
                        anyLive = true;
                        if (row.Woke < 0 && m.E.Roused) { row.Woke = t; row.Walled = b.Collision.Raycast(p.X, p.Z, m.E.HomeX, m.E.HomeZ, 0.3) != null; }
                        if (row.FirstHit < 0 && m.E.Hp < m.E.MaxHp) row.FirstHit = t;
                    }
                    else if (dead.Add((m.E, m.Seed))) { row.Deaths.Add(t); if (m.E.Seed == m.Seed && Melee(m.E.Def)) fell.Add(m.E); }
                }
                if (row.Woke >= 0 && anyLive)
                {
                    var ml = members.Where(m => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying && Melee(m.E.Def)).Select(m => m.E).ToList();
                    if (ml.Count > 0)
                    {
                        DenCause.Step(row.C, t, row.Woke, ml, p, evs, row.Deaths.Count > 0, fell);
                        // The middle's speed (smoothed), for the lead-aim opener.
                        double mx = ml.Average(e => e.X), mz = ml.Average(e => e.Z);
                        if (last.TryGetValue(members, out var q) && t > q.T)
                        {
                            double vx = (mx - q.X) / (t - q.T), vz = (mz - q.Z) / (t - q.T);
                            vel[members] = vel.TryGetValue(members, out var v0) ? (v0.X * 0.75 + vx * 0.25, v0.Z * 0.75 + vz * 0.25) : (vx, vz);
                        }
                        last[members] = (mx, mz, t);
                    }
                }
                if (areas.Count > 0 && (anyLive || fell.Count > 0))
                    foreach (var a in areas)
                    {
                        var melee = members.Where(m => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying && Melee(m.E.Def)).ToList();
                        if (row.InsideAll < 0 && melee.Count + fell.Count > 0)
                        {
                            int inAll = melee.Count(m => Math.Sqrt((m.E.X - a.X) * (m.E.X - a.X) + (m.E.Z - a.Z) * (m.E.Z - a.Z)) < AreaR + m.E.Radius)
                                + fell.Count(e => Math.Sqrt((e.X - a.X) * (e.X - a.X) + (e.Z - a.Z) * (e.Z - a.Z)) < AreaR + e.Radius);
                            if (inAll > 0) { row.InsideAll = (double)inAll / (melee.Count + fell.Count); row.Fell1 = fell.Count; row.KindAll = a.K; }
                        }
                        if (melee.Count == 0) break;
                        int inR = melee.Count(m => Math.Sqrt((m.E.X - a.X) * (m.E.X - a.X) + (m.E.Z - a.Z) * (m.E.Z - a.Z)) < AreaR + m.E.Radius);
                        if (inR == 0) continue;
                        double share = (double)inR / melee.Count;
                        row.Best = Math.Max(row.Best, share);
                        if (row.Inside >= 0) continue;
                        row.Inside = share; row.FirstKind = a.K; row.FirstLag = row.Woke >= 0 ? t - row.Woke : -1;
                        row.Base1 = melee.Select(m => m.E).ToList(); row.Due1 = t + 1;
                        DenCause.AtBlow(row.C, t, row.Base1, a.X, a.Z, a.K);
                        row.HitBefore = (double)melee.Count(m => m.E.Hp < m.E.MaxHp) / melee.Count;
                        if (a.K == 'S') { row.SpinBase = melee.Select(m => m.E).ToHashSet(); row.SpinCaught = new(); }
                        foreach (var m in melee) row.AtFirst.Add((m.E.Def.Id, Math.Sqrt((m.E.X - a.X) * (m.E.X - a.X) + (m.E.Z - a.Z) * (m.E.Z - a.Z)) - m.E.Radius));
                    }
                if (row.Woke >= 0 && row.Deaths.Count == 0 && anyLive)
                {
                    int n = 0, inn = 0;
                    foreach (var m in members)
                        if (m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying && Melee(m.E.Def))
                        { n++; if (Math.Sqrt((m.E.X - p.X) * (m.E.X - p.X) + (m.E.Z - p.Z) * (m.E.Z - p.Z)) < AreaR + m.E.Radius) inn++; }
                    if (n > 0) row.Peak = Math.Max(row.Peak, (double)inn / n);
                }
                if (row.Base1 != null && row.Inside1 < 0 && t >= row.Due1)
                    row.Inside1 = (double)row.Base1.Count(e => e.Alive && e.State != EnemyState.Dying && Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) < AreaR + e.Radius) / Math.Max(1, row.Base1.Count(e => e.Alive && e.State != EnemyState.Dying));
                if (row.SpinBase != null && row.SpinWhole < 0)
                {
                    foreach (var e in row.SpinBase)
                        if (e.Alive && Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) < AreaR + e.Radius) row.SpinCaught!.Add(e);
                    if (!spinNow || !anyLive) row.SpinWhole = (double)row.SpinCaught!.Count / Math.Max(1, row.SpinBase.Count);
                }
                if (!anyLive && row.Woke >= 0 && p.Alive)
                {
                    row.Killed = true;
                    row.LastDeath = t;
                    var d = row.Deaths.OrderBy(x => x).ToList();
                    int best = 0;
                    for (int i = 0, j = 0; i < d.Count; i++) { while (d[i] - d[j] > Window) j++; best = Math.Max(best, i - j + 1); }
                    row.Together = row.Size > 0 ? (double)best / row.Size : 0;
                }
            }
            bool fighting = !bossUp && RunMeter.Fighting(b);
            if (fighting) run.RoomFight += 1 / 60.0;
            foreach (var ev in evs)
                if (ev is Ev.Telegraph { Hostile: true, Phase: TellPhase.Warn, Boss: false } tg && !bossUp && Math.Sqrt((tg.X - p.X) * (tg.X - p.X) + (tg.Z - p.Z) * (tg.Z - p.Z)) < SeenR)
                {
                    if (tg.Shape == TelegraphShape.Line) { run.Lanes++; lanes.Add(t + Math.Max(0.3, tg.Duration)); }
                    else if (tg.Shape == TelegraphShape.Circle) run.Circles++;
                }
            lanes.RemoveAll(e => e <= t);
            run.MaxLanes = Math.Max(run.MaxLanes, lanes.Count);
            if (lanes.Count > 1) run.LaneSecOver1 += 1 / 60.0;
        };
        try { run.R = MapSim.Play(spec); }
        finally { MapSim.Tap = null; MapSim.ZoneTap = null; MapSim.PreAct = null; }
        run.Packs.AddRange(rows.Values.Where(r => r.Woke >= 0));
        return run;
    }

    /// <summary>A member that closes to bite: not one that hangs back to shoot or call.</summary>
    static bool Melee(EnemyDef d) => d.Behavior is not (Behavior.Ranged or Behavior.Caster) && d.Ranged == null;

    static double Q(IEnumerable<double> xs, double q)
    {
        var a = xs.OrderBy(x => x).ToList();
        if (a.Count == 0) return double.NaN;
        return a[Math.Clamp((int)Math.Round(q * (a.Count - 1)), 0, a.Count - 1)];
    }

    public static string Report(IReadOnlyList<Run> runs)
    {
        var sb = new StringBuilder();
        sb.AppendLine("| bot | runs | packs woke/killed | TTK wake p25/p50/p75 s | TTK first blow p25/p50/p75 | recipe-1 TTK blow p50 (n) | in 6-10 s (blow) | inside 3.5 m p50 / >=50% | together 1.5 s p50 / >=40% | lanes / 8 s | max lanes / s >1 lane | circle marks / min | pack gap s |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        foreach (var g in runs.GroupBy(r => r.Label).OrderBy(g => g.Key))
        {
            var ps = g.SelectMany(r => r.Packs).ToList();
            var k = ps.Where(p => p.Killed).ToList();
            var wake = k.Select(p => p.LastDeath - p.Woke).ToList();
            var blow = k.Where(p => p.FirstHit >= 0).Select(p => p.LastDeath - p.FirstHit).ToList();
            var r1 = k.Where(p => p.Recipe == "hunting" && p.Grade == 0 && p.FirstHit >= 0).Select(p => p.LastDeath - p.FirstHit).ToList();
            var inside = ps.Where(p => p.Inside >= 0).Select(p => p.Inside).ToList();
            var tog = k.Select(p => p.Together).ToList();
            double fight = g.Sum(r => r.RoomFight), mins = fight / 60;
            string pct(int a, int n) => n == 0 ? "-" : $"{100.0 * a / n:0}%";
            sb.AppendLine($"| {g.Key} | {g.Count()} | {ps.Count}/{k.Count} | {Q(wake, .25):0.0}/{Q(wake, .5):0.0}/{Q(wake, .75):0.0} | {Q(blow, .25):0.0}/{Q(blow, .5):0.0}/{Q(blow, .75):0.0} | {Q(r1, .5):0.0} ({r1.Count}) | {pct(blow.Count(x => x >= 6 && x <= 10), blow.Count)} | {Q(inside, .5):0.00} / {pct(inside.Count(x => x >= 0.5), inside.Count)} | {Q(tog, .5):0.00} / {pct(tog.Count(x => x >= 0.4), tog.Count)} | {(fight > 0 ? g.Sum(r => r.Lanes) / fight * 8 : 0):0.00} | {g.Max(r => r.MaxLanes)} / {g.Sum(r => r.LaneSecOver1):0.0} | {(mins > 0 ? g.Sum(r => r.Circles) / mins : 0):0.0} | {Q(g.Select(r => r.R.PackGap).Where(x => x > 0), .5):0.0} |");
        }
        sb.AppendLine();
        foreach (var g in runs.GroupBy(r => r.Label).OrderBy(g => g.Key))
        {
            var ps = g.SelectMany(r => r.Packs).Where(p => p.Inside >= 0).ToList();
            sb.AppendLine($"{g.Key} first area blow: leap {ps.Count(p => p.FirstKind == 'L')}, spin {ps.Count(p => p.FirstKind == 'S')}; inside if leap p50 {Q(ps.Where(p => p.FirstKind == 'L').Select(p => p.Inside), .5):0.00}, if spin {Q(ps.Where(p => p.FirstKind == 'S').Select(p => p.Inside), .5):0.00}; s after wake p50 {Q(ps.Select(p => p.FirstLag), .5):0.0}; best any blow p50 {Q(ps.Select(p => p.Best), .5):0.00} (>=50%: {100.0 * ps.Count(p => p.Best >= 0.5) / Math.Max(1, ps.Count):0}%); 1 s after it, of those still up, inside 3.5 m of her p50 {Q(ps.Where(p => p.Inside1 >= 0).Select(p => p.Inside1), .5):0.00} (>=50%: {100.0 * ps.Count(p => p.Inside1 >= 0.5) / Math.Max(1, ps.Count(p => p.Inside1 >= 0)):0}%); first spin's whole channel p50 {Q(ps.Where(p => p.SpinWhole >= 0).Select(p => p.SpinWhole), .5):0.00} (>=50%: {100.0 * ps.Count(p => p.SpinWhole >= 0.5) / Math.Max(1, ps.Count(p => p.SpinWhole >= 0)):0}%)");
        }
        foreach (var w in new[] { false, true })
        {
            var ps = runs.SelectMany(r => r.Packs).Where(p => p.Inside >= 0 && p.Walled == w).ToList();
            sb.AppendLine($"woke {(w ? "through a wall" : "in sight")}: {ps.Count} packs, inside first blow p50 {Q(ps.Select(p => p.Inside), .5):0.00} (>=50%: {100.0 * ps.Count(p => p.Inside >= 0.5) / Math.Max(1, ps.Count):0}%), s after wake p50 {Q(ps.Select(p => p.FirstLag), .5):0.0}");
        }
        {
            var ps = runs.SelectMany(r => r.Packs).Where(p => p.Inside >= 0).ToList();
            sb.AppendLine($"peak crowd inside 3.5 m of her before the first death p50 {Q(ps.Where(p => p.Peak >= 0).Select(p => p.Peak), .5):0.00} (>=50%: {100.0 * ps.Count(p => p.Peak >= 0.5) / Math.Max(1, ps.Count):0}%); members already hit by the first area blow p50 {Q(ps.Select(p => p.HitBefore), .5):0.00}; packs with a death before the first area blow {100.0 * ps.Count(p => p.Deaths.Count > 0 && p.Deaths.Min() < p.Woke + p.FirstLag) / Math.Max(1, ps.Count):0}%");
        }
        sb.AppendLine("Counting the members the blow itself felled (the pack as it stood when the blow landed; `Inside` above drops them):");
        foreach (var g in runs.GroupBy(r => r.Label).OrderBy(g => g.Key))
        {
            var ps = g.SelectMany(r => r.Packs).Where(p => p.InsideAll >= 0).ToList();
            string line(IEnumerable<PackRow> q0) { var q = q0.ToList(); return $"p50 {Q(q.Select(p => p.InsideAll), .5):0.00} (>=50%: {100.0 * q.Count(p => p.InsideAll >= 0.5) / Math.Max(1, q.Count):0}%, n {q.Count})"; }
            sb.AppendLine($"FELLED {g.Key}: first area blow {line(ps)}; if leap {line(ps.Where(p => p.KindAll == 'L'))}; if spin {line(ps.Where(p => p.KindAll == 'S'))}; fell on that step mean {ps.Select(p => (double)p.Fell1).DefaultIfEmpty().Average():0.00} (if leap {ps.Where(p => p.KindAll == 'L').Select(p => (double)p.Fell1).DefaultIfEmpty().Average():0.00}); opened with leap {line(ps.Where(p => p.Opener == 'L'))}; opened with spin {line(ps.Where(p => p.Opener == 'S'))}");
        }
        foreach (var g in runs.Where(r => r.Label.EndsWith("+open") || r.Label.EndsWith("+lead")).GroupBy(r => r.Label).OrderBy(g => g.Key))
        {
            var op = g.SelectMany(r => r.Packs).Where(p => p.Opener != '-' && p.Inside >= 0).ToList();
            sb.AppendLine($"{g.Key}: packs opened {op.Count} of {g.SelectMany(r => r.Packs).Count()} (leap {op.Count(p => p.Opener == 'L')}, spin {op.Count(p => p.Opener == 'S')}); of those, inside 3.5 m at the first landing p50 {Q(op.Select(p => p.Inside), .5):0.00} (>=50%: {100.0 * op.Count(p => p.Inside >= 0.5) / Math.Max(1, op.Count):0}%); leap-opened p50 {Q(op.Where(p => p.Opener == 'L').Select(p => p.Inside), .5):0.00} (>=50%: {100.0 * op.Count(p => p.Opener == 'L' && p.Inside >= 0.5) / Math.Max(1, op.Count(p => p.Opener == 'L')):0}%)");
        }
        sb.AppendLine("At the first area blow, by kind (all bots): share inside, edge distance p25/p50/p75 m:");
        foreach (var g in runs.SelectMany(r => r.Packs).SelectMany(p => p.AtFirst).GroupBy(x => x.Def).OrderBy(g => g.Key))
            sb.AppendLine($"- {g.Key} n {g.Count()}: inside {100.0 * g.Count(x => x.D < AreaR) / g.Count():0}%, {Q(g.Select(x => x.D), .25):0.0}/{Q(g.Select(x => x.D), .5):0.0}/{Q(g.Select(x => x.D), .75):0.0}");
        sb.AppendLine();
        sb.AppendLine("By recipe (all bots): | recipe/grade | killed | TTK blow p50 | inside p50 | together p50 |");
        foreach (var g in runs.SelectMany(r => r.Packs).Where(p => p.Killed && p.FirstHit >= 0).GroupBy(p => $"{p.Recipe}/{p.Grade}").OrderBy(g => g.Key))
            sb.AppendLine($"| {g.Key} | {g.Count()} | {Q(g.Select(p => p.LastDeath - p.FirstHit), .5):0.0} | {Q(g.Where(p => p.Inside >= 0).Select(p => p.Inside), .5):0.00} | {Q(g.Select(p => p.Together), .5):0.00} |");
        sb.Append(DenCause.Report(runs));
        return sb.ToString();
    }
}
