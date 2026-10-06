import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\balance"
FILES = {
os.path.join(ROOT, r"Harness\ArenaSim.cs"): [
("""    double Cap = 40, double Beyond = 0, int Weapon = 0, int Art = 0, int Level = 1, bool Deft = false)
{
    public string Key => $"{Calling}/{Policy}/t{Tier}/{People}/s{Seed}/w{Weapon}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") +
        (Oaths is { Length: > 0 } ? $"/{string.Join("+", Oaths)}" : "");""",
"""    double Cap = 40, double Beyond = 0, int Weapon = 0, int Art = 0, int Level = 1, bool Deft = false, double Minutes = 30)
{
    public string Key => $"{Calling}/{Policy}/t{Tier}/{People}/s{Seed}/w{Weapon}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") +
        (Oaths is { Length: > 0 } ? $"/{string.Join("+", Oaths)}" : "") + (Minutes != 30 ? $"/m{Minutes:0}" : "");"""),
("""    /// <summary>The long night: the boss's returns that came, and the dark's oaths sworn.</summary>
    public int Returns, Dark;""",
"""    /// <summary>The long night: the boss's returns that came, and the dark's oaths sworn.</summary>
    public int Returns, Dark;
    /// <summary>The minibosses met (by def) and those killed: how long each took, and the minute.</summary>
    public List<string> MinibossesMet = new();
    public List<(string Def, double Ttk, double At)> Minibosses = new();"""),
("""        var arena = new ArenaSpec { Id = "table:bot", Name = "The Harness", Seed = spec.Seed, Tier = spec.Tier, People = spec.People, Oaths = (spec.Oaths ?? []).ToList() };""",
"""        // (A night shorter than the table's is a story's: it ends on its boss.)
        var arena = new ArenaSpec { Id = "table:bot", Name = "The Harness", Seed = spec.Seed, Tier = spec.Tier, People = spec.People, Oaths = (spec.Oaths ?? []).ToList(),
            Minutes = spec.Minutes, Story = spec.Minutes != 30 };"""),
("""                    case Ev.Spawn s: firstHit.Remove(s.Enemy); break;""",
"""                    case Ev.Spawn s:
                        firstHit.Remove(s.Enemy);
                        if (Enemies.Get(s.Def).Miniboss) r.MinibossesMet.Add(s.Def);
                        break;"""),
("""                            if (k.Boss) r.BossTtk = ttk;
                            else if (k.Elite)
                            {
                                elite.Add(ttk);""",
"""                            if (k.Boss) r.BossTtk = ttk;
                            else if (k.Elite)
                            {
                                elite.Add(ttk);
                                if (Enemies.Get(k.Def).Miniboss) r.Minibosses.Add((k.Def, ttk, t / 60));"""),
],
os.path.join(ROOT, "Program.cs"): [
("""                                Level: level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), Deft: deft));""",
"""                                Level: level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), Deft: deft, Minutes: opt.Double("minutes", 30)));"""),
(""" *          --charges 0 (every charger on its own clock, as before the charge director)""",
""" *          --charges 0 (every charger on its own clock, as before the charge director)
 *          --minutes 20 (a story's night: twenty minutes, ending on its boss)"""),
],
os.path.join(ROOT, r"Harness\Report.cs"): [
("""        // The long night: how far past the half hour the won runs got, and what ended them.""",
"""        // The minibosses: met, killed, how long they took, and who they killed.
        var mbs = runs.SelectMany(r => r.MinibossesMet).GroupBy(d => d).ToList();
        if (mbs.Count > 0)
        {
            sb.AppendLine("### The minibosses\\n");
            Head(sb, "miniboss", "met", "killed", "TTK (s)", "TTK p90 (s)", "minute killed", "runs it ended");
            foreach (var g in mbs.OrderBy(g => g.Key))
            {
                var kills = runs.SelectMany(r => r.Minibosses).Where(m => m.Def == g.Key).ToList();
                var ttk = kills.Select(m => m.Ttk).OrderBy(x => x).ToList();
                Row(sb, g.Key, g.Count(), kills.Count, F(Median(ttk), "0"), ttk.Count == 0 ? "–" : F(ttk[Math.Min(ttk.Count - 1, (int)(ttk.Count * 0.9))], "0"),
                    F(Median(kills.Select(m => m.At))), runs.Count(r => r.Died && r.KilledBy == g.Key));
            }
            sb.AppendLine();
        }
        // The long night: how far past the half hour the won runs got, and what ended them."""),
],
}
