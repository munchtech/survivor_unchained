W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'balance\Harness\ArenaSim.cs', [
('''    public double BossBreak;
    public bool BossSoft;''',
'''    public double BossBreak;
    public bool BossSoft;
    /// <summary>The long night: the boss's returns that came, and the dark's oaths sworn.</summary>
    public int Returns, Dark;'''),
('''        r.Kills = b.KillCount;
        r.Ember = b.EmberLevel;''',
'''        r.Returns = zone.Returns;
        r.Dark = zone.DarkSworn;
        r.Kills = b.KillCount;
        r.Ember = b.EmberLevel;'''),
])

edit(r'balance\Harness\Report.cs', [
('''        if (runs.Select(r => r.Spec.Policy).Distinct().Count() > 1 && runs.Select(r => r.Spec.Calling).Distinct().Count() > 1)''',
'''        // The long night: how far past the half hour the won runs got, and what ended them.
        var night = runs.Where(r => r.Won && r.Spec.Beyond > 0).ToList();
        if (night.Count > 0)
        {
            sb.AppendLine("### The long night (won runs, minutes past the half hour)\\n");
            Head(sb, "calling", "runs", "fell", "median", "p10-p90", "furthest", "standing at +15/+30/+45/+60/+90", "returns met", "dark's oaths");
            foreach (var g in night.GroupBy(r => r.Spec.Calling).OrderBy(g => g.Key).Append(night.GroupBy(_ => "all").First()))
            {
                var l = g.ToList();
                var past = l.Select(r => r.Minutes - 30).OrderBy(x => x).ToList();
                string standing = string.Join(" / ", new[] { 15, 30, 45, 60, 90 }.Select(m => Pct(l.Count(r => r.Minutes - 30 >= m) / (double)l.Count)));
                Row(sb, g.Key, l.Count, Pct(Rate(l, r => r.Died)), F(Median(past), "0"), $"{F(past[(int)(past.Count * 0.1)], "0")}-{F(past[Math.Min(past.Count - 1, (int)(past.Count * 0.9))], "0")}",
                    F(past[^1], "0"), standing, F(Median(l.Select(r => (double)r.Returns)), "0"), F(Median(l.Select(r => (double)r.Dark)), "0"));
            }
            var killers = night.Where(r => r.Died).GroupBy(r => r.KilledBy).OrderByDescending(g => g.Count()).Take(6);
            sb.AppendLine("\\nWhat ended them: " + string.Join(", ", killers.Select(g => $"{g.Key} {g.Count()}")) + "\\n");
        }
        if (runs.Select(r => r.Spec.Policy).Distinct().Count() > 1 && runs.Select(r => r.Spec.Calling).Distinct().Count() > 1)'''),
])
print("ok")
