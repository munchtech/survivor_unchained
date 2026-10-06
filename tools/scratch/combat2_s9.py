W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""            if (!p.Alive) break;
            t += Dt;""", """            if (!p.Alive) break;
            // MAP_TRACE=1: where the hands are every ten seconds (why a map was not finished).
            if (trace && (int)(t / 10) != (int)((t + Dt) / 10))
                Console.Error.WriteLine($"{t / 60:0.00} at ({p.X:0},{p.Z:0}) way {along}/{route.Count} onward ({onward.X:0},{onward.Z:0}) roused {b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && (e.Wake == 0 || e.Roused))} hp {p.Hp:0}/{b.MaxHp:0} packs {zone.PacksCleared}/{zone.PacksPlaced}");
            t += Dt;"""),
        ("""        var kills = new List<double>();""", """        var kills = new List<double>();
        bool trace = Environment.GetEnvironmentVariable("MAP_TRACE") == "1";"""),
    ],
}
