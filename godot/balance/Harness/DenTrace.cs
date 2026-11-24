using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play.Pilots;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>(P3 den human bar, measuring only: nothing in a run reads it) DEN_TRACE=file: the ruler's fight as she lived it,
/// one run's lines appended at its end. Each tick the ruler is up: where she is (its room, a hall, another room), in its
/// contact reach or not, the human's hands aware or not, slowed, knocked down. Each blow of the ruler's on her (its kind:
/// a plain bite, the Drive, a marked blow by its label) with that state; each Drive laid on her (how far she had to go to
/// leave its lane, the share of its windup the hands were aware, caught or not); each fall with its last 6 s.</summary>
public sealed class DenTrace
{
    public static readonly string? File = Environment.GetEnvironmentVariable("DEN_TRACE") is { Length: > 0 } f ? f : null;
    static readonly object gate = new();
    readonly string who;
    readonly List<string> lines = new();
    readonly DungeonLayout? dg;
    readonly Human? human;
    double upAt = -1, last = -1, hpUp = -1;
    // seconds the ruler was up: by where she stood, in its contact reach, aware, slowed, knocked down; where it stood
    readonly Dictionary<string, double> at = new(), pmAt = new();
    double contact, aware, slowed, knocked, quaffs, pmWindSec;
    readonly Queue<(double T, string Kind, double Amt, bool Contact, bool Aware, bool Slow, bool Knock, string Loc)> recent = new();
    readonly Queue<(double T, bool Contact, bool Aware, bool Slow, bool Knock)> ticks = new();
    sealed class Drive { public int Id; public double Bt, Need, AwareSec, Sec, FirstAware = -1, PmWind; public Dictionary<string, double> Top = new(); public string Loc = ""; public bool Covered, SlowAtWarn, KnockAtWarn, AwareAtWarn; }
    readonly Dictionary<int, Drive> drives = new();
    string loc = "", pmLoc = "";
    int step;

    public DenTrace(MapRunSpec spec, DungeonLayout? dg, Human? human)
    {
        who = $"{spec.Bot} {spec.Seed}";
        this.dg = dg;
        this.human = human;
    }

    string Where(double x, double z)
    {
        if (dg == null) return "map";
        foreach (var rm in dg.Rooms) if (rm.Dist(x, z) < 0) return rm.Role == RoomRole.Boss ? "boss" : "room";
        return "hall";
    }

    public void Step(double t, double dt, Battle b, Enemy? boss, IEnumerable<CombatEvent> evs, bool quaff)
    {
        var p = b.Player;
        if (boss == null || !boss.Alive) { if (upAt >= 0 && last < 0) last = t; return; }
        if (upAt < 0) { upAt = t; hpUp = p.Hp / Math.Max(1, b.MaxHp); }
        double bt = t - upAt;
        if (step++ % 3 == 0) { loc = Where(p.X, p.Z); pmLoc = Where(boss.X, boss.Z); }
        double d = Math.Sqrt((boss.X - p.X) * (boss.X - p.X) + (boss.Z - p.Z) * (boss.Z - p.Z));
        bool inContact = d <= boss.Radius + p.Radius + 0.4;
        bool aw = human?.LastAware ?? false;
        bool sl = p.SlowT > 0 && p.SlowF < 0.99;
        bool kn = p.RootT > 0;
        at[loc] = at.GetValueOrDefault(loc) + dt;
        pmAt[pmLoc] = pmAt.GetValueOrDefault(pmLoc) + dt;
        if (inContact) contact += dt;
        if (aw) aware += dt;
        if (sl) slowed += dt;
        if (kn) knocked += dt;
        if (quaff) quaffs++;
        ticks.Enqueue((t, inContact, aw, sl, kn));
        while (ticks.Count > 0 && ticks.Peek().T < t - 6) ticks.Dequeue();
        // the most urgent threat the human's hands would weigh (Human.Aware's categories, read-only): its kind
        string top = "-"; double left = double.MaxValue;
        foreach (var bl in b.Blows) if (bl.Hit(p.X, p.Z, p.Radius + 4) && bl.T < left) { left = bl.T; top = bl.Tell != null ? "kit" : "blow"; }
        foreach (var e in b.Enemies.Living())
            if (e.Disposition == Disposition.Hostile && e.State == EnemyState.Windup && (e.Def.Charge ?? e.Def.Lunge) != null && Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) < 9 && e.StateT < left) { left = e.StateT; top = e.Boss ? "pmWindup" : "lungeWindup"; }
        foreach (var z in b.Zones.Living()) if (z.Owner is Side.Enemy or Side.World && Math.Sqrt((z.X - p.X) * (z.X - p.X) + (z.Z - p.Z) * (z.Z - p.Z)) < z.Radius + p.Radius + 1 && 0.5 < left) { left = 0.5; top = "zone"; }
        foreach (var st in b.EnemyStrikes()) if (Math.Sqrt((st.X - p.X) * (st.X - p.X) + (st.Z - p.Z) * (st.Z - p.Z)) < st.R + p.Radius + 3 && st.Left < left) { left = st.Left; top = "strike"; }
        if (boss.State == EnemyState.Windup) pmWindSec += dt;
        foreach (var dv in drives.Values) { dv.Sec += dt; dv.Top[top] = dv.Top.GetValueOrDefault(top) + dt; if (boss.State == EnemyState.Windup) dv.PmWind = boss.StateT; if (aw) { dv.AwareSec += dt; if (dv.FirstAware < 0) dv.FirstAware = dv.Sec; } }
        string name = boss.Named?.Title ?? boss.Def.Name;
        foreach (var ev in evs)
        {
            switch (ev)
            {
                case Ev.Telegraph { Hostile: true, Phase: TellPhase.Warn, Tell: "charge", Boss: true } tg:
                {
                    bool cov = ArenaSim.Covers(tg, p.X, p.Z, p.Radius);
                    double need = 0;
                    if (cov && tg.X1 is double x1 && tg.Z1 is double z1)
                    {
                        double lx = x1 - tg.X, lz = z1 - tg.Z, ll = Math.Max(1e-6, Math.Sqrt(lx * lx + lz * lz));
                        double perp = Math.Abs(((p.X - tg.X) * lz - (p.Z - tg.Z) * lx) / ll);
                        need = (tg.Width ?? 0) / 2 + p.Radius - perp;
                    }
                    drives[tg.Id] = new Drive { Id = tg.Id, Bt = bt, Need = need, Loc = loc, Covered = cov, SlowAtWarn = sl, KnockAtWarn = kn, AwareAtWarn = aw };
                    break;
                }
                case Ev.Telegraph { Phase: TellPhase.Land, Tell: "charge" } tl when drives.Remove(tl.Id, out var dv):
                    lines.Add($"DRIVE {who} {dv.Bt:0.0} cov {(dv.Covered ? 1 : 0)} need {dv.Need:0.00} loc {dv.Loc} awareFrac {(dv.Sec > 0 ? dv.AwareSec / dv.Sec : 0):0.00} firstAware {dv.FirstAware:0.00} awareAtWarn {(dv.AwareAtWarn ? 1 : 0)} slowAtWarn {(dv.SlowAtWarn ? 1 : 0)} knockAtWarn {(dv.KnockAtWarn ? 1 : 0)} top {string.Join(",", dv.Top.OrderByDescending(k => k.Value).Select(k => k.Key + ":" + k.Value.ToString("0.00")))} pmStateT {dv.PmWind:0.00} caught {(tl.Caught ? 1 : 0)} slowNow {(sl ? 1 : 0)}");
                    break;
                case Ev.PlayerHit h when h.Amount > 0 && !h.Dot:
                {
                    bool pm = h.Source == name || h.Source == boss.Def.Name;
                    string kind = !pm ? "other" : h.Label != null ? h.Label : h.Tell != null ? "Drive" : "bite";
                    double amt = h.Amount / Math.Max(1, b.MaxHp);
                    recent.Enqueue((t, kind, amt, inContact, aw, sl, kn, loc));
                    if (pm) lines.Add($"HIT {who} {bt:0.0} {kind} {amt:0.000} loc {loc} pm {pmLoc} contact {(inContact ? 1 : 0)} aware {(aw ? 1 : 0)} slow {(sl ? 1 : 0)} knock {(kn ? 1 : 0)} d {d:0.0} hp {p.Hp / Math.Max(1, b.MaxHp):0.00}");
                    break;
                }
                case Ev.PlayerDeath pd:
                {
                    var w = recent.Where(r => r.T >= t - 6).ToList();
                    string Sum(string k) => w.Where(r => r.Kind == k).Sum(r => r.Amt).ToString("0.00");
                    var tk = ticks.ToList();
                    double F(Func<(double T, bool Contact, bool Aware, bool Slow, bool Knock), bool> f) => tk.Count == 0 ? 0 : tk.Count(f) / (double)tk.Count;
                    lines.Add($"DEATH {who} {bt:0.0} by {pd.Killer.Replace(' ', '_')} loc {loc} pm {pmLoc} d {d:0.0} last6 bite {Sum("bite")} Drive {Sum("Drive")} Hamstring {Sum("Hamstring")} Shake {Sum("Shake")} Slurry {Sum("Slurry")} other {Sum("other")} n {w.Count} contact6 {F(x => x.Contact):0.00} aware6 {F(x => x.Aware):0.00} slow6 {F(x => x.Slow):0.00} knock6 {F(x => x.Knock):0.00} phase {(boss != null ? "?" : "-")}");
                    break;
                }
            }
        }
        while (recent.Count > 0 && recent.Peek().T < t - 6) recent.Dequeue();
    }

    public void Finish(double t, bool cleared, bool alive, Play.Bosses.ArenaBoss? script)
    {
        if (File == null) return;
        if (upAt >= 0)
        {
            double sec = (last >= 0 ? last : t) - upAt;
            string A(Dictionary<string, double> m) => string.Join(" ", new[] { "boss", "hall", "room" }.Select(k => $"{k} {m.GetValueOrDefault(k):0}"));
            lines.Add($"RUN {who} cleared {(cleared ? 1 : 0)} alive {(alive ? 1 : 0)} up {upAt:0} sec {sec:0} hpUp {hpUp:0.00} her[{A(at)}] pm[{A(pmAt)}] contact {contact:0} aware {aware:0} slowed {slowed:0} knocked {knocked:0} quaffs {quaffs:0} pmWindup {pmWindSec:0} phase {script?.PhaseIx ?? -1}");
        }
        else lines.Add($"RUN {who} cleared {(cleared ? 1 : 0)} alive {(alive ? 1 : 0)} up -1");
        lock (gate) System.IO.File.AppendAllLines(File, lines);
    }
}
