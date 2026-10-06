W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Maps/Charts.cs": [
        ("""    /// <summary>The kinds a map of this tier fields:""",
         """    /// <summary>A chart as a pickup carries it (Pickup.Ref): read back by FromRef when it is picked up.</summary>
    public static string Ref(Chart c) => $"chart:{c.Tier}:{c.People}:{c.Seed}:{c.Rarity}:{string.Join(",", c.Mods)}:{c.Theme}:{c.Name}";

    public static Chart? FromRef(string r)
    {
        var f = r.Split(':', 8);
        if (f.Length < 8 || f[0] != "chart") return null;
        return new Chart
        {
            Tier = int.Parse(f[1]), People = f[2], Seed = int.Parse(f[3]), Rarity = int.Parse(f[4]),
            Mods = f[5].Length == 0 ? new() : f[5].Split(',').ToList(), Theme = f[6], Name = f[7],
        };
    }

    /// <summary>What a chart is called in the pack: its tier, who holds it, and its name.</summary>
    public static string Title(Chart c) => $"{c.Name} (tier {c.Tier}, {MapOffers.People(c.People).Name})";

    /// <summary>The kinds a map of this tier fields:"""),
        ("""    public static List<string> Guardians(Denizens people, int tier) =>
        people.Stretches.Take(StretchesOpen(tier)).Select(s => s.Miniboss).ToList();
}
""",
         """    public static List<string> Guardians(Denizens people, int tier) =>
        people.Stretches.Take(StretchesOpen(tier)).Select(s => s.Miniboss).ToList();
}

/// <summary>The Wayfinder's atlas: which peoples' maps have been cleared at which tier. The first
/// clear of each pair gives a point; the points will buy the atlas's biases (§17.6, with the
/// experience lead).</summary>
public static class Atlas
{
    static string Key(string people, int tier) => $"atlas.{people}.{tier}";

    public static bool Done(World.WorldState w, string people, int tier) => w.Fact(Key(people, tier)).Truthy;

    /// <summary>The highest tier cleared of any people, and the points the first clears gave.</summary>
    public static int Best(World.WorldState w) => (int)w.Fact("atlas.best").Number;
    public static int Points(World.WorldState w) => (int)w.Fact("atlas.points").Number;

    /// <summary>A map's ruler is down: its (people, tier) is marked. True if it is the first time.</summary>
    public static bool Complete(World.WorldState w, Chart c)
    {
        bool first = !Done(w, c.People, c.Tier);
        w.Facts[Key(c.People, c.Tier)] = true;
        w.Facts["atlas.cleared"] = w.Fact("atlas.cleared").Number + 1;
        if (first)
        {
            w.Facts["atlas.points"] = Points(w) + 1;
            w.Facts["atlas.best"] = Math.Max(Best(w), c.Tier);
        }
        return first;
    }
}
"""),
    ],
    W + "logic/Play/Zones/MapRun.cs": [
        ("""        if (bossUp && boss is { } bb && (!bb.Alive || bb.State == EnemyState.Dying) && !cleared) { }
""", ""),
        ("""    bool bossUp, cleared, over, restlessDone, eventLit;""", """    bool bossUp, cleared, over, restlessDone, eventLit, firstClear;"""),
        ("""        bool first = Atlas.Complete(G.Journey.World, Chart);""", """        bool first = firstClear = Atlas.Complete(G.Journey.World, Chart);"""),
        ("""bossTtk, cleared && Atlas.Firsts(G.Journey.World, Chart), new(spilled));""", """bossTtk, firstClear, new(spilled));"""),
    ],
}
