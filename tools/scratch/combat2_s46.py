W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Maps/Charts.cs": [
        ("""    /// <summary>A map's ruler is down: its (people, tier) is marked. True if it is the first time.</summary>""",
         """    /* The atlas's biases (the experience lead's first five): a point a rank, three ranks each,
     * bought with the points the first clears give. Hooks only for now; the table shows them. */
    public const string PeoplesRoad = "peoples_road", TwiceLit = "twice_lit", KeepersDue = "keepers_due", RulersHoard = "rulers_hoard", MarkedMen = "marked_men";
    public const int MaxRank = 3;

    /// <summary>The biases, as the atlas shows them: id, name, what a rank does.</summary>
    public static readonly (string Id, string Name, string Rank)[] Biases =
    [
        (PeoplesRoad, "The people's road", "A fifth more of the charts that drop are of the people you follow"),
        (TwiceLit, "Twice lit", "A third more chance that a second altar's lighting brings its people's question too"),
        (KeepersDue, "The keeper's due", "An altar's keeper carries one thing more"),
        (RulersHoard, "The ruler's hoard", "A map's ruler leaves one thing more"),
        (MarkedMen, "Marked men", "Half again the chance that a magic or rare pack's leader carries one thing more"),
    ];

    public static int Rank(World.WorldState w, string bias) => (int)w.Fact($"atlas.bias.{bias}").Number;
    public static int Unspent(World.WorldState w) => Points(w) - Biases.Sum(b => Rank(w, b.Id));

    /// <summary>A rank more in a bias, for a point: false if none is to spend or it is at three.</summary>
    public static bool Raise(World.WorldState w, string bias)
    {
        if (Unspent(w) <= 0 || Rank(w, bias) >= MaxRank || Biases.All(b => b.Id != bias)) return false;
        w.Facts[$"atlas.bias.{bias}"] = Rank(w, bias) + 1;
        return true;
    }

    /// <summary>The people the road follows (null: none chosen).</summary>
    public static string? Road(World.WorldState w) => w.Fact("atlas.road").IsNull ? null : w.Fact("atlas.road").Str;
    public static void Follow(World.WorldState w, string people) => w.Facts["atlas.road"] = people;

    /// <summary>A map's ruler is down: its (people, tier) is marked. True if it is the first time.</summary>"""),
    ],
    W + "logic/Play/Zones/MapRun.cs": [
        ("""        int n = 3 + (R() < 0.5 * Chart.Quantity ? 1 : 0) + (R() < 0.25 * Chart.Quantity ? 1 : 0) + Atlas.Rank(G.Journey.World, Atlas.KeepersDue);""",
         """        int n = 3 + (R() < 0.5 * Chart.Quantity ? 1 : 0) + (R() < 0.25 * Chart.Quantity ? 1 : 0);"""),
        ("""            int n = 3 + (R() < 0.5 * q ? 1 : 0) + (R() < 0.25 * q ? 1 : 0);
            for (int k = 0; k < n; k++) o.Add(Gear(1.5, 1));""",
         """            int n = 3 + (R() < 0.5 * q ? 1 : 0) + (R() < 0.25 * q ? 1 : 0) + Atlas.Rank(G.Journey.World, Atlas.RulersHoard);
            for (int k = 0; k < n; k++) o.Add(Gear(1.5, 1));"""),
        ("""                var next = MapOffers.Peoples[(int)(R() * MapOffers.Peoples.Length)].Id;""",
         """                var next = MapOffers.Peoples[(int)(R() * MapOffers.Peoples.Length)].Id;
                // The people's road: the charts lean toward the people followed.
                if (Atlas.Road(G.Journey.World) is { } road && R() < 0.2 * Atlas.Rank(G.Journey.World, Atlas.PeoplesRoad)) next = road;"""),
        ("""            int n = grade switch { 3 => 2, 2 => 2, _ => 1 };""",
         """            var w = G.Journey.World;
            int n = grade switch { 3 => 2, 2 => 2, _ => 1 }
                + (grade == 3 ? Atlas.Rank(w, Atlas.KeepersDue) : 0)
                + (grade < 3 && R() < 0.5 * Atlas.Rank(w, Atlas.MarkedMen) / Atlas.MaxRank ? 1 : 0);"""),
    ],
}
