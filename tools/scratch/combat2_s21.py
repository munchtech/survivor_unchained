W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/MapRun.cs": [
        ("""        foreach (var s in map.Packs)
            packs.Add(new Pack { Spot = s, People = rival != null && rng.Next() < 1 / 3.0 ? rival : people });""",
         """        // MapGen sets a spot about every 14 m: a pack at each made the way one long fight (a pack every
        // 8 s, a map of 14 minutes). Three in four clearings' spots are kept and one in three of the
        // way's, so packs come with ground between them to walk and to pick up after.
        foreach (var s in map.Packs)
        {
            var a = map.Areas[Math.Clamp(s.Area, 0, map.Areas.Count - 1)];
            bool clearing = (s.X - a.X) * (s.X - a.X) + (s.Z - a.Z) * (s.Z - a.Z) < a.R * a.R;
            if (rng.Next() >= (clearing ? 0.75 : 0.35)) continue;
            packs.Add(new Pack { Spot = s, People = rival != null && rng.Next() < 1 / 3.0 ? rival : people });
        }"""),
        ("""    /// <summary>The ruler's health over the night's (a third: 45-75 s at par, §17.7).</summary>
    public const double BossHealth = 1 / 3.0;""",
         """    /// <summary>The ruler's health over the night's: 45-75 s at par (§17.7). A third measured about
    /// 100 s with a day build at the map's level.</summary>
    public const double BossHealth = 0.2;"""),
        ("""        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level, Elite = elite, Style = style ?? SpawnStyle.Walk });
        return e;""",
         """        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level, Elite = elite, Style = style ?? SpawnStyle.Walk });
        // What the ruler calls is its crowd, as at night (softened as the half hour's horde is): at the
        // map's full strength her drive's wolves were each a pack's worth, and every build fell to her.
        if (e != null && !elite) e.MaxHp = e.Hp = e.MaxHp / ArenaRun.FodderEase(30);
        return e;"""),
    ],
}
