W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/MapRun.cs": [
        ("""    /// <summary>The ruler's health over the night's: 45-75 s at par (§17.7). A third measured about
    /// 100 s with a day build at the map's level.</summary>
    public const double BossHealth = 0.2;""",
         """    /// <summary>The ruler's health, over its body's at the map's level: 45-75 s at par (§17.7). The
    /// night's own multipliers (12 to 43 at the first tier) were set against the ember's builds and
    /// their Breaks; a day build meets the four more evenly (at a fifth of the night's, the Pack-Mother
    /// took 173 s and the Barrow Lord 67), so one number serves all four.</summary>
    public const double BossHealth = 3.5;"""),
        ("""        double mul = (script?.HealthMul(BossTier) ?? 12 + 2 * BossTier) * BossHealth * (again ? 0.5 : 1);""",
         """        double mul = BossHealth * (again ? 0.5 : 1);"""),
    ],
}
