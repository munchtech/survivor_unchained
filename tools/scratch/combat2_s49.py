W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/ArenaRun.cs": [
        ("""        Minibosses();
        if (!runUp && !won && Seconds >= End - 120) RunUp();""",
         """        Minibosses();
        Forerunners();
        if (!runUp && !won && Seconds >= End - 120) RunUp();"""),
        ("""    /* ---------------------------------------------------- the Kindling -- */""",
         """    /* -------------------------------------------------- the forerunners -- */

    /* The run-ups (the experience lead's: into each herald, and the long push) were the calmest
     * stretches of the night: at those minutes the crowd melts as fast as it comes, so more of it
     * asks nothing. What rules the people sends its forerunners ahead of each landmark instead: a
     * pair of signed champions from two sides at once, twice in each run-up, so the stretch asks
     * where to stand and what the build does to one, as the landmark will. */
    int forerunWave = -1;
    double forerunNext;

    void Forerunners()
    {
        if (!Building || MinibossUp || heraldAt > 0)
        {
            if (!Building) forerunWave = -1;
            return;
        }
        if (forerunWave < 0) { forerunWave = 0; forerunNext = Seconds + 8; }
        if (forerunWave >= 2 || Seconds < forerunNext) return;
        forerunWave++;
        forerunNext = Seconds + 45 / Pace;
        double a = R() * Math.Tau;
        for (int k = 0; k < 2; k++)
        {
            if (Around(a + k * Math.PI, 18) is not var (x, z)) continue;
            var c = Spawn(Strongest(), x, z, true);
            if (c == null) continue;
            c.MaxHp = c.Hp = c.MaxHp * 1.5;
            Sign(c, Math.Max(1, SignsFor(false)));
        }
        Shout(people.Id switch
        {
            "pack" => "Two of the Pack's best, from either side: they come ahead of what is coming.",
            "dead" => "Two of the old guard rise, one each side of you.",
            "lamplings" => "Two gangers come up, one each side, lamps lit.",
            "kerchiefs" => "Two of the Kerchiefs' hard men, from either side.",
            _ => "Two of them, from either side.",
        });
    }

    /* ---------------------------------------------------- the Kindling -- */"""),
    ],
}
