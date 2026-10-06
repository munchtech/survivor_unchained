W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""                // (Not while fighting close: standing in a press and killing it is not being stuck.)
                stuck = Dist(p.X, p.Z, lastX, lastZ) < 1.5 && b.HostilesInRadius(p.X, p.Z, 6).Count == 0 ? 3 : stuck;
                (lastX, lastZ) = (p.X, p.Z);""",
         """                // (Not while fighting close: standing in a press and killing it is not being stuck.)
                // Held again at the same place, it walks on for longer each time (a roused one
                // behind the trees that can neither reach nor be reached holds the hands there).
                if (Dist(p.X, p.Z, lastX, lastZ) < 1.5 && b.HostilesInRadius(p.X, p.Z, 6).Count == 0)
                {
                    holds = Dist(p.X, p.Z, heldX, heldZ) < 6 ? holds + 1 : 0;
                    (heldX, heldZ) = (p.X, p.Z);
                    stuck = 3 * Math.Pow(2, Math.Min(4, holds));
                }
                (lastX, lastZ) = (p.X, p.Z);"""),
        ("""        double t = 0, lastKill = 0, lastPack = 0, stuck = 0, lastX = p.X, lastZ = p.Z;""",
         """        double t = 0, lastKill = 0, lastPack = 0, stuck = 0, lastX = p.X, lastZ = p.Z, heldX = 1e9, heldZ = 1e9;
        int holds = 0;"""),
    ],
}
