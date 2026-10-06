W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "src/Game/Game.cs": [
        ("""        if (Args.Get("at") is string s)
        {""", """        if (Args.Get("at") is string s && s != "boss")
        {"""),
        ("""                Mods = (Args.Get("mods") ?? "").Split('+', StringSplitOptions.RemoveEmptyEntries).ToList(), Name = "The Test Map",
            };""", """                Mods = (Args.Get("mods") ?? "").Split('+', StringSplitOptions.RemoveEmptyEntries).ToList(), Name = "The Test Map",
            };
        // --at boss: on a map, at the edge of its ruler's clearing (pictures of the ruler's fight).
        if (z == "map" && Args.Get("at") == "boss")
        {
            var bc = SurvivorUnchained.Maps.MapGen.Generate(World.Map!.Map).Boss;
            at = new Arrival(bc.X, bc.Z - bc.R + 1);
        }"""),
    ],
}
