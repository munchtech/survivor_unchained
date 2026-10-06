import sys
root = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot"

def edit(path, pairs):
    p = root + "\\" + path
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        if s.count(a) != 1:
            print("NOT UNIQUE/FOUND in", path, ":", a[:80], s.count(a)); sys.exit(1)
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(s)

edit(r"balance\Harness\ArenaSim.cs", [
("""    public double Damage, Taken, LowHp = 1, TtkFodder, TtkFodder90, TtkElite;
}""",
"""    public double Damage, Taken, LowHp = 1, TtkFodder, TtkFodder90, TtkElite;
    /// <summary>The horde's charges: runs started, the most at once, seconds with three or
    /// more at once, and spikes (Sim/Charges.cs).</summary>
    public int Charges, ChargePeak, Spikes;
    public double Overlap;
}"""),
("""public static class ArenaSim
{
    public const double Dt = 1 / 60.0;
""",
"""public static class ArenaSim
{
    public const double Dt = 1 / 60.0;
    /// <summary>--charges 0: every charger on its own clock, as before the charge director.</summary>
    public static bool Director = true;
"""),
("""        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
""",
"""        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        b.Charges.On = Director;
        int lastStarted = 0, lastSpikes = 0;
"""),
("""            m.LowHp = Math.Min(m.LowHp, p.Hp / b.MaxHp);
            t += Dt;""",
"""            m.LowHp = Math.Min(m.LowHp, p.Hp / b.MaxHp);
            m.ChargePeak = Math.Max(m.ChargePeak, b.Charges.Live);
            if (b.Charges.Live >= 3) m.Overlap += Dt;
            t += Dt;"""),
("""                m.TtkElite = Median(elite);
                r.ByMinute.Add(m);""",
"""                m.TtkElite = Median(elite);
                m.Charges = b.Charges.Started - lastStarted;
                m.Spikes = b.Charges.SpikesRun - lastSpikes;
                lastStarted = b.Charges.Started; lastSpikes = b.Charges.SpikesRun;
                r.ByMinute.Add(m);"""),
])

edit(r"balance\Harness\Report.cs", [
("""        // Every card: how often offered, taken, and how runs that took it went.""",
"""        // The horde's charges, and how near the survivor came to falling (docs/SKILLS_DESIGN.md, "Encounters").
        sb.AppendLine("### Encounters over the minutes (means; dipped: runs below half health that minute)\\n");
        Head(sb, "minute", "charges/min", "most at once", "s with 3+ at once", "spikes", "dipped below ½");
        foreach (int m in new[] { 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 35, 40, 45 })
        {
            var at = runs.Where(r => r.ByMinute.Count >= m).Select(r => r.ByMinute[m - 1]).ToList();
            if (at.Count == 0) continue;
            Row(sb, m, F(at.Average(x => x.Charges)), F(at.Average(x => x.ChargePeak)), F(at.Average(x => x.Overlap)), F(at.Average(x => x.Spikes), "0.00"),
                Pct(at.Count(x => x.LowHp < 0.5) / (double)at.Count));
        }
        sb.AppendLine();

        // Every card: how often offered, taken, and how runs that took it went."""),
])

edit(r"balance\Program.cs", [
("""Pilot.ReadsBosses = opt.Get("bossread", "1") != "0";""",
"""Pilot.ReadsBosses = opt.Get("bossread", "1") != "0";
ArenaSim.Director = opt.Get("charges", "1") != "0";"""),
(""" *          --bossread 0 (the hands as they were before they read the bosses)""",
""" *          --bossread 0 (the hands as they were before they read the bosses)
 *          --charges 0 (every charger on its own clock, as before the charge director)"""),
])
print("ok")
