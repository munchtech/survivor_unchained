W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/Pilot.cs": [
        ("""            if (onward != null && e.Wake > 0 && !e.Roused) continue;""",
         """            if (onward != null && (e.Wake > 0 && !e.Roused || e.State == EnemyState.Burrowed)) continue;"""),
    ],
    W + "balance/Harness/MapSim.cs": [
        ("""            // Held on one spot with nothing roused (a pickup out of reach, a corner): walk on.
            if ((int)(t / 4) != (int)((t + Dt) / 4))
            {
                // (Not while fighting close: standing in a press and killing it is not being stuck.)
                // Held again at the same place, it walks on for longer each time (a roused one
                // behind the trees that can neither reach nor be reached holds the hands there).
                if (Dist(p.X, p.Z, lastX, lastZ) < 1.5 && b.HostilesInRadius(p.X, p.Z, 6).Count == 0)
                {
                    holds = Dist(p.X, p.Z, heldX, heldZ) < 6 ? holds + 1 : 0;
                    (heldX, heldZ) = (p.X, p.Z);
                    stuck = 3 * Math.Pow(2, Math.Min(4, holds));
                }
                (lastX, lastZ) = (p.X, p.Z);
            }""",
         """            // No nearer the ruler in twenty seconds with the ruler not up (a pickup out of reach, a
            // corner, a tunneller under the ground the hands wait on): walk on, longer each time.
            if ((int)(t / 20) != (int)((t + Dt) / 20))
            {
                if (zone.Boss == null && !double.IsNaN(along) && along > bestToGo - 3)
                {
                    holds++;
                    stuck = 4 * Math.Pow(2, Math.Min(3, holds - 1));
                }
                else holds = 0;
                if (!double.IsNaN(along)) bestToGo = Math.Min(bestToGo, along);
            }"""),
        ("""        double t = 0, lastKill = 0, lastPack = 0, stuck = 0, lastX = p.X, lastZ = p.Z, heldX = 1e9, heldZ = 1e9;
        int holds = 0;""",
         """        double t = 0, lastKill = 0, lastPack = 0, stuck = 0, bestToGo = double.MaxValue;
        int holds = 0;"""),
    ],
}
