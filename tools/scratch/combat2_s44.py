W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Maps/MapGen.cs": [
        ("""    public string Mood = "";
}

public enum AreaKind { Start, Clearing, Altar, Boss }""",
         """    public string Mood = "";
    /// <summary>A Wayfinder's map: how many clearings stand between the start and the ruler's (and
    /// how many of them hold altars). 0: the old map of fourteen clearings and three altars. The
    /// way between is the same snake, cut shorter, its other turns only bends in the way.</summary>
    public int Clearings, AltarCount;
}

/// <summary>A Bend: a widening of the way where it turns, with nothing placed in it but the way's own.</summary>
public enum AreaKind { Start, Clearing, Altar, Boss, Bend }"""),
        ("""        var order = spec.Arena ? new List<(int, int)>() : Snake(rng);""",
         """        var order = spec.Arena ? new List<(int, int)>() : Snake(rng);
        // A map's way is cut to its clearings: 12 turns of the snake for three, 14 for four, all 16
        // for five (the experience lead's shape: 9-12 minutes, a pack every 13-15 s).
        if (spec.Clearings > 0) order = order.Take(Math.Min(order.Count, 6 + 2 * spec.Clearings)).ToList();"""),
        ("""        // Three of the clearings between hold altars: early, midway, late.
        int na = areas.Count;
        if (!spec.Arena) foreach (int k in new[] { rng.Int((int)(na * 0.15), (int)(na * 0.25)), rng.Int((int)(na * 0.4), (int)(na * 0.5)), rng.Int((int)(na * 0.65), (int)(na * 0.75)) })
            areas[k] = areas[k] with { Kind = AreaKind.Altar, R = Math.Max(areas[k].R, 17) };""",
         """        // Three of the clearings between hold altars: early, midway, late.
        int na = areas.Count;
        if (!spec.Arena && spec.Clearings == 0) foreach (int k in new[] { rng.Int((int)(na * 0.15), (int)(na * 0.25)), rng.Int((int)(na * 0.4), (int)(na * 0.5)), rng.Int((int)(na * 0.65), (int)(na * 0.75)) })
            areas[k] = areas[k] with { Kind = AreaKind.Altar, R = Math.Max(areas[k].R, 17) };
        // A Wayfinder's map: its clearings spread evenly along the way, the rest of the turns bends;
        // the altars among the clearings, never the first (the way is learned before its question).
        if (!spec.Arena && spec.Clearings > 0)
        {
            int between = na - 2, n = Math.Min(spec.Clearings, between);
            var at = Enumerable.Range(0, n).Select(i => 1 + (int)Math.Round((i + 0.5) * between / n - 0.5)).ToList();
            for (int k = 1; k < na - 1; k++)
                if (!at.Contains(k)) areas[k] = areas[k] with { Kind = AreaKind.Bend, R = rng.Range(8, 10) };
            int altars = Math.Clamp(spec.AltarCount, 0, Math.Max(0, n - 1));
            for (int i = 0; i < altars; i++)
            {
                int k = at[altars == 1 ? n / 2 : 1 + (int)Math.Round(i * (n - 2) / (double)(altars - 1))];
                areas[k] = areas[k] with { Kind = AreaKind.Altar, R = Math.Max(areas[k].R, 17) };
            }
        }"""),
    ],
    W + "logic/Maps/Charts.cs": [
        ("""        Seed = Seed, Tier = Tier, Theme = Theme, Night = false, Name = Name, Arena = false, People = People,""",
         """        Seed = Seed, Tier = Tier, Theme = Theme, Night = false, Name = Name, Arena = false, People = People,
        // The experience lead's shape: three clearings before the ruler's at tiers 1-2, four at 3-5,
        // five from 6; an altar (the map's event) in each but the first, to three.
        Clearings = Tier <= 2 ? 3 : Tier <= 5 ? 4 : 5, AltarCount = Tier <= 2 ? 1 : Tier <= 5 ? 2 : 3,"""),
    ],
}
