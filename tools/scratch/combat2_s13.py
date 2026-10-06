W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/MapRun.cs": [
        ("""    /// <summary>A fall: half of what was picked up here is spilled, and she is up again at the
    /// map's start. The third closes the map.</summary>""",
         """    /// <summary>A fall: half of what was picked up here is spilled, and she is up again where she
    /// was last safe (the last altar she lit, or the map's start). The third closes the map.</summary>"""),
        ("""        p.X = map.Start.X; p.Z = map.Start.Z;
        p.PoisonT = p.BurnT = 0;""", """        var safe = altars.Where(a => a.Lit).OrderByDescending(a => a.Area.Index).Select(a => a.Area).FirstOrDefault() ?? map.Start;
        p.X = safe.X; p.Z = safe.Z;
        p.PoisonT = p.BurnT = 0;"""),
    ],
    W + "balance/Harness/MapSim.cs": [
        ("""    public int BossPhase;""", """    public int BossPhase;
    /// <summary>What was left of the ruler when the map closed (-1: never met).</summary>
    public double BossLeft = -1;"""),
        ("""        r.BossPhase = zone.BossScript?.PhaseIx ?? -1;""", """        r.BossPhase = zone.BossScript?.PhaseIx ?? -1;
        if (zone.Boss is { } zb && zone.BossScript != null) r.BossLeft = zb.Hp / zone.BossScript.MaxHp;"""),
    ],
    W + "balance/Program.cs": [
        ("""boss {(r.BossTtk is double bt ? $"{bt:0}s" : $"phase {r.BossPhase}")}""",
         """boss {(r.BossTtk is double bt ? $"{bt:0}s" : $"phase {r.BossPhase} left {r.BossLeft:0.00}")}"""),
    ],
}
