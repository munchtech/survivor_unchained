W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "balance/Harness/MapSim.cs": [
        ("""        var route = Route(map);
        int along = 0;""", """        var flow = Flow(map);
        int along = 0;"""),
        ("""            // Onward: the furthest point of the way ahead already reached, then the next.
            for (int k = along; k < Math.Min(route.Count, along + 40); k++)
                if (Dist(p.X, p.Z, route[k].X, route[k].Z) < 5) along = k + 1;
            var onward = along < route.Count ? route[along] : (map.Boss.X, map.Boss.Z);""",
         """            // Onward: downhill on the way's distance to the ruler, a few metres ahead.
            var onward = Downhill(map, flow, p.X, p.Z, 7);
            along = (int)Flow(map, flow, p.X, p.Z);"""),
        ("""Console.Error.WriteLine($"{t / 60:0.00} at ({p.X:0},{p.Z:0}) way {along}/{route.Count} onward""",
         """Console.Error.WriteLine($"{t / 60:0.00} at ({p.X:0},{p.Z:0}) to go {along} m onward"""),
        ("""    /// <summary>The way from the start to the ruler's clearing, point by point.</summary>
    static List<(double X, double Z)> Route(MapBuild map)
    {
        var o = new List<(double X, double Z)>();
        for (int k = 0; k < map.Ways.Count; k++)
        {
            o.Add((map.Areas[k].X, map.Areas[k].Z));
            foreach (var w in map.Ways[k]) o.Add((w.X, w.Z));
        }
        o.Add((map.Boss.X, map.Boss.Z));
        return o;
    }""", """    /// <summary>Metres to the ruler's clearing over walkable ground, cell by cell (each metre near
    /// the trees' edge dearer, so the way's middle is walked): the snake's way is the only road, so
    /// going downhill on it passes every clearing in order.</summary>
    static double[] Flow(MapBuild map)
    {
        int res = map.Meta.Res;
        double half = map.Meta.Size / 2;
        var walk = map.Walkable;
        var edge = new bool[walk.Length];
        for (int j = 1; j < res - 1; j++)
            for (int i = 1; i < res - 1; i++)
            {
                int k = j * res + i;
                if (!walk[k]) continue;
                for (int dj = -2; dj <= 2 && !edge[k]; dj++)
                    for (int di = -2; di <= 2; di++)
                    {
                        int ii = i + di, jj = j + dj;
                        if (ii < 0 || jj < 0 || ii >= res || jj >= res || !walk[jj * res + ii]) { edge[k] = true; break; }
                    }
            }
        var d = new double[walk.Length];
        Array.Fill(d, double.MaxValue);
        int bi = (int)Math.Round(map.Boss.X + half), bj = (int)Math.Round(map.Boss.Z + half);
        var q = new PriorityQueue<int, double>();
        d[bj * res + bi] = 0;
        q.Enqueue(bj * res + bi, 0);
        while (q.TryDequeue(out int k, out double dk))
        {
            if (dk > d[k]) continue;
            int i = k % res, j = k / res;
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    if (di == 0 && dj == 0) continue;
                    int ii = i + di, jj = j + dj;
                    if (ii < 0 || jj < 0 || ii >= res || jj >= res) continue;
                    int n = jj * res + ii;
                    if (!walk[n]) continue;
                    double step = (di != 0 && dj != 0 ? 1.414 : 1) * (edge[n] ? 4 : 1);
                    if (d[k] + step < d[n]) { d[n] = d[k] + step; q.Enqueue(n, d[n]); }
                }
        }
        return d;
    }

    static double Flow(MapBuild map, double[] d, double x, double z)
    {
        int res = map.Meta.Res;
        double half = map.Meta.Size / 2;
        int i = Math.Clamp((int)Math.Round(x + half), 0, res - 1), j = Math.Clamp((int)Math.Round(z + half), 0, res - 1);
        return d[j * res + i];
    }

    /// <summary>`steps` cells downhill from here (from the nearest walkable cell, if pushed off it).</summary>
    static (double X, double Z) Downhill(MapBuild map, double[] d, double x, double z, int steps)
    {
        int res = map.Meta.Res;
        double half = map.Meta.Size / 2;
        int i = Math.Clamp((int)Math.Round(x + half), 0, res - 1), j = Math.Clamp((int)Math.Round(z + half), 0, res - 1);
        if (d[j * res + i] == double.MaxValue)
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
        }
        for (int s = 0; s < steps; s++)
        {
            int bi = i, bj = j;
            double best = d[j * res + i];
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    int ii = i + di, jj = j + dj;
                    if (ii < 0 || jj < 0 || ii >= res || jj >= res) continue;
                    if (d[jj * res + ii] < best) { best = d[jj * res + ii]; bi = ii; bj = jj; }
                }
            if (bi == i && bj == j) break;
            (i, j) = (bi, bj);
        }
        return (i - half, j - half);
    }"""),
    ],
}
