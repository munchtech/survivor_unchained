W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/ArenaSim.cs": [
        ("""    public int Returns, Dark;""", """    public int Returns, Dark;
    /// <summary>The Kindling's ember-core broken within its minute (null: it never came).</summary>
    public bool? CoreBroken;"""),
        ("""        r.Returns = zone.Returns;""", """        r.Returns = zone.Returns;
        r.CoreBroken = zone.CoreBroken;"""),
    ],
    W + "balance/Harness/Report.cs": [
        ("""            if (toBoss.Count > 0) sb.AppendLine($"\\nFell to the boss: {toBoss.Count}, with a median {Pct(Median(toBoss.Select(r => r.BossLeft)))} of it left.");""",
         """            if (toBoss.Count > 0) sb.AppendLine($"\\nFell to the boss: {toBoss.Count}, with a median {Pct(Median(toBoss.Select(r => r.BossLeft)))} of it left.");
            var kindled = runs.Where(r => r.CoreBroken != null).ToList();
            if (kindled.Count > 0)
                sb.AppendLine($"\\nThe Kindling's core broken within its minute: {string.Join(", ", kindled.GroupBy(r => r.Spec.Policy).OrderBy(g => g.Key).Select(g => $"{g.Key} {Pct(Rate(g.ToList(), r => r.CoreBroken == true))}"))} (of {kindled.Count} that met it).");"""),
    ],
}
