W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/World/State.cs": [
        ("""    public Arena.ArenaSpec? Arena;""", """    public Arena.ArenaSpec? Arena;
    /// <summary>The Wayfinder's chart being walked, while it is (docs/SKILLS_DESIGN.md §17).</summary>
    public Maps.Chart? Map;"""),
    ],
    W + "logic/Play/Zones/MapRun.cs": [
        ("""        G.Journey.BankGold(B);
        G.After(""", """        G.Journey.BankGold(B);
        G.Journey.World.Map = null;
        G.After("""),
    ],
    W + "src/Game/Game.cs": [
        ("""        "arena" => new ArenaRun(this, currentMap!, World.Arena!),""",
         """        "arena" => new ArenaRun(this, currentMap!, World.Arena!),
        "map" => new MapRun(this, currentMap!, World.Map!),"""),
        ("""        if (id == "arena") { currentMap = SurvivorUnchained.Maps.MapGen.Generate(World.Arena!.Map); data = new ZoneData(currentMap); }""",
         """        if (id == "arena") { currentMap = SurvivorUnchained.Maps.MapGen.Generate(World.Arena!.Map); data = new ZoneData(currentMap); }
        else if (id == "map") { currentMap = SurvivorUnchained.Maps.MapGen.Generate(World.Map!.Map); data = new ZoneData(currentMap); }"""),
        ("""    /// <summary>The arena is over: what came of it, and then back to the story.</summary>""",
         """    /// <summary>Into a Wayfinder's map: the chart is used up as it opens (docs/SKILLS_DESIGN.md §17).</summary>
    public void EnterMap(SurvivorUnchained.Maps.Chart chart)
    {
        if (inTransit || zone is MapRun || zone is ArenaRun) return;
        CloseOverlay();
        Save("map");
        World.Map = chart;
        Travel("map", chart.Name, "A Wayfinder's map");
    }

    /// <summary>The arena is over: what came of it, and then back to the story.</summary>"""),
        ("""        if (z != "lowford")
        {
            // Skipping ahead: the prologue counts as done.""",
         """        // --zone map [--tier T --people ID --mods a+b --seed N]: straight into a Wayfinder's map.
        if (z == "map")
            World.Map = new SurvivorUnchained.Maps.Chart
            {
                Tier = (int)Args.Num("tier", 1), People = Args.Get("people") ?? "pack", Seed = (int)Args.Num("seed", 1234),
                Mods = (Args.Get("mods") ?? "").Split('+', StringSplitOptions.RemoveEmptyEntries).ToList(), Name = "The Test Map",
            };
        if (z != "lowford")
        {
            // Skipping ahead: the prologue counts as done."""),
    ],
}
