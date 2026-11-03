using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/// <summary>
/// A walkable route across the ground, round what is solid (the collision world's walls, stalls,
/// trees, rocks): A* on a half-metre grid in a box round the two ends, then cut to the corners that
/// can see each other. For whatever must walk somewhere on its own and not wedge on a wall: the
/// autopilot following the tracker's pins (tools/experience/demo_run.py), and a check that every
/// goal's pin can be reached from where the player arrives.
/// </summary>
public static class GroundPath
{
    /// <summary>The route from (fx, fz) to (tx, tz) for a body of radius r, as waypoints after the start (the
    /// last is the goal, or the nearest open cell to it); null when nothing open joins them in the box.</summary>
    public static List<(double X, double Z)>? Find(CollisionWorld col, double fx, double fz, double tx, double tz, double r = 0.45, double cell = 0.5, double margin = 24, int maxNodes = 60000)
    {
        double x0 = Math.Min(fx, tx) - margin, z0 = Math.Min(fz, tz) - margin;
        int w = (int)Math.Ceiling((Math.Abs(fx - tx) + margin * 2) / cell) + 1, h = (int)Math.Ceiling((Math.Abs(fz - tz) + margin * 2) / cell) + 1;
        if ((long)w * h > 400_000) return null;
        var open = new sbyte[w * h]; // 0 unknown, 1 open, -1 blocked
        bool Open(int i, int j)
        {
            if (i < 0 || j < 0 || i >= w || j >= h) return false;
            ref var o = ref open[j * w + i];
            if (o == 0) o = col.Blocked(x0 + i * cell, z0 + j * cell, r, true) ? (sbyte)-1 : (sbyte)1;
            return o > 0;
        }
        (int, int) Cell(double x, double z) => ((int)Math.Round((x - x0) / cell), (int)Math.Round((z - z0) / cell));
        var (si, sj) = Cell(fx, fz);
        var (gi, gj) = Cell(tx, tz);
        // The goal itself is often inside its own counter or ring: aim at the nearest open cell to it.
        if (!Open(gi, gj))
        {
            bool found = false;
            for (int rr = 1; rr <= 8 && !found; rr++)
                for (int dj = -rr; dj <= rr && !found; dj++)
                    for (int di = -rr; di <= rr && !found; di++)
                        if (Math.Max(Math.Abs(di), Math.Abs(dj)) == rr && Open(gi + di, gj + dj)) { gi += di; gj += dj; found = true; }
            if (!found) return null;
        }
        var g = new Dictionary<int, double>();
        var from = new Dictionary<int, int>();
        var pq = new PriorityQueue<int, double>();
        int start = sj * w + si, goal = gj * w + gi;
        g[start] = 0;
        pq.Enqueue(start, 0);
        int seen = 0;
        while (pq.Count > 0 && seen++ < maxNodes)
        {
            int c = pq.Dequeue();
            if (c == goal) break;
            int ci = c % w, cj = c / w;
            double gc = g[c];
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    if (di == 0 && dj == 0) continue;
                    int ni = ci + di, nj = cj + dj;
                    if (!Open(ni, nj)) continue;
                    // (no cutting a corner between two solid cells)
                    if (di != 0 && dj != 0 && (!Open(ci + di, cj) || !Open(ci, cj + dj))) continue;
                    int n = nj * w + ni;
                    double ng = gc + (di != 0 && dj != 0 ? 1.4142 : 1);
                    if (g.TryGetValue(n, out var old) && old <= ng) continue;
                    g[n] = ng; from[n] = c;
                    pq.Enqueue(n, ng + Math.Sqrt((ni - gi) * (ni - gi) + (nj - gj) * (nj - gj)));
                }
        }
        if (!from.ContainsKey(goal) && goal != start) return null;
        var cells = new List<int>();
        for (int c = goal; c != start; c = from[c]) cells.Add(c);
        cells.Reverse();
        (double, double) P(int c) => (x0 + c % w * cell, z0 + c / w * cell);
        // Keep only the corners: a waypoint is dropped while the one after it is in plain sight.
        var route = new List<(double X, double Z)>();
        var at = (fx, fz);
        int k = 0;
        while (k < cells.Count)
        {
            int far = k;
            for (int m = cells.Count - 1; m > k; m--)
                if (Clear(col, at, P(cells[m]), r)) { far = m; break; }
            var next = P(cells[far]);
            route.Add(next);
            at = next;
            k = far + 1;
        }
        return route;
    }

    /// <summary>Whether a body of radius r walks straight from a to b without touching anything solid.</summary>
    public static bool Clear(CollisionWorld col, (double X, double Z) a, (double X, double Z) b, double r)
    {
        double len = Math.Sqrt((b.X - a.X) * (b.X - a.X) + (b.Z - a.Z) * (b.Z - a.Z));
        int n = Math.Max(1, (int)Math.Ceiling(len / 0.25));
        for (int i = 1; i <= n; i++)
            if (col.Blocked(a.X + (b.X - a.X) * i / n, a.Z + (b.Z - a.Z) * i / n, r, true)) return false;
        return true;
    }
}
