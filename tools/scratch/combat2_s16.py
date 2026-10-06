W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""        var flow = Flow(map, (x, z) => b.Collision.Blocked(x, z, 0.55));""",
         """        var flow = Flow(map, (x, z) => b.Collision.Blocked(x, z, 0.3));"""),
        ("""                stuck = Dist(p.X, p.Z, lastX, lastZ) < 1.5 && !b.Enemies.Living().Any(e => e.Disposition == Disposition.Hostile && (e.Wake == 0 || e.Roused) && Dist(e.X, e.Z, p.X, p.Z) < 16) ? 5 : stuck;""",
         """                // (Not while fighting close: standing in a press and killing it is not being stuck.)
                stuck = Dist(p.X, p.Z, lastX, lastZ) < 1.5 && b.HostilesInRadius(p.X, p.Z, 6).Count == 0 ? 3 : stuck;"""),
        ("""        if (d[j * res + i] == double.MaxValue)
        {
            double best = double.MaxValue;
            int bi = i, bj = j;
            for (int r = 1; r < 8 && best == double.MaxValue; r++)
                for (int dj = -r; dj <= r; dj++)
                    for (int di = -r; di <= r; di++)
                    {
                        int ii = i + di, jj = j + dj;
                        if (ii < 0 || jj < 0 || ii >= res || jj >= res) continue;
                        if (d[jj * res + ii] < best) { best = d[jj * res + ii]; bi = ii; bj = jj; }
                    }
            return (bi - half, bj - half);
        }""", """        if (d[j * res + i] == double.MaxValue)
        {
            double best = double.MaxValue;
            int bi = i, bj = j;
            for (int r = 1; r < 8 && best == double.MaxValue; r++)
                for (int dj = -r; dj <= r; dj++)
                    for (int di = -r; di <= r; di++)
                    {
                        int ii = i + di, jj = j + dj;
                        if (ii < 0 || jj < 0 || ii >= res || jj >= res) continue;
                        if (d[jj * res + ii] < best) { best = d[jj * res + ii]; bi = ii; bj = jj; }
                    }
            if (best == double.MaxValue) return (x, z);
            (i, j) = (bi, bj);
        }"""),
    ],
}
