using System;
using System.Collections.Generic;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>Distance to one place over the ground the survivor can stand on, at half a metre, with
/// what stands on the ground taken from the battle's own collision at her radius: the bots' way
/// through a map. Downhill from anywhere is the shortest way there; Onward looks as far down it as
/// a straight line stays clear.</summary>
public sealed class NavField
{
    const double Cell = 0.5;
    readonly int n;
    readonly double half;
    readonly bool[] free;
    readonly float[] d;

    public NavField(MapBuild map, Battle b, double toX, double toZ)
    {
        half = map.Meta.Size / 2;
        n = (int)(map.Meta.Size / Cell) + 1;
        free = new bool[n * n];
        double r = b.Player.Radius + 0.05;
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                double x = i * Cell - half, z = j * Cell - half;
                // As the survivor meets it: the player-only edges too (Blocked leaves them out).
                double rx = x, rz = z;
                free[j * n + i] = map.CanStand(x, z) && !b.Collision.Resolve(ref rx, ref rz, r, true);
            }
        d = new float[n * n];
        Array.Fill(d, float.MaxValue);
        int start = Nearest(Index(toX, toZ));
        if (start < 0) return;
        var q = new PriorityQueue<int, float>();
        d[start] = 0;
        q.Enqueue(start, 0);
        while (q.TryDequeue(out int k, out float dk))
        {
            if (dk > d[k]) continue;
            int i = k % n, j = k / n;
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    if (di == 0 && dj == 0) continue;
                    int ii = i + di, jj = j + dj;
                    if (ii < 0 || jj < 0 || ii >= n || jj >= n) continue;
                    int m = jj * n + ii;
                    if (!free[m]) continue;
                    // No cutting a corner between two blocked cells.
                    if (di != 0 && dj != 0 && (!free[j * n + ii] || !free[jj * n + i])) continue;
                    float step = (float)(Cell * (di != 0 && dj != 0 ? 1.414 : 1));
                    if (dk + step < d[m]) { d[m] = dk + step; q.Enqueue(m, d[m]); }
                }
        }
    }

    int Index(double x, double z)
    {
        int i = (int)Math.Round((x + half) / Cell), j = (int)Math.Round((z + half) / Cell);
        return i < 0 || j < 0 || i >= n || j >= n ? -1 : j * n + i;
    }

    (double X, double Z) At(int k) => (k % n * Cell - half, k / n * Cell - half);

    /// <summary>The nearest free cell to this one (itself if free), searching out a few metres.</summary>
    int Nearest(int k)
    {
        if (k < 0) return -1;
        if (free[k]) return k;
        int i0 = k % n, j0 = k / n;
        for (int r = 1; r < 16; r++)
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Abs(di) != r && Math.Abs(dj) != r) continue;
                    int ii = i0 + di, jj = j0 + dj;
                    if (ii < 0 || jj < 0 || ii >= n || jj >= n) continue;
                    if (free[jj * n + ii] && d[jj * n + ii] < float.MaxValue) return jj * n + ii;
                }
        return -1;
    }

    /// <summary>Metres to go from here (NaN where nothing leads there).</summary>
    public double ToGo(double x, double z)
    {
        int k = Nearest(Index(x, z));
        return k < 0 || d[k] == float.MaxValue ? double.NaN : d[k];
    }

    /// <summary>Where to walk to go on: down the field from here, as far (to `reach` metres) as a
    /// straight line from here stays on free ground.</summary>
    public (double X, double Z) Onward(double x, double z, double reach = 6)
    {
        int k = Nearest(Index(x, z));
        if (k < 0) return (x, z);
        // Pushed off the free ground (against a stump, in a corner): look on from the nearest free
        // cell, or the hands go back and forth between it and the way on.
        if (k != Index(x, z)) (x, z) = At(k);
        var best = At(k);
        int cur = k;
        for (int s = 0; s < (int)(reach / Cell); s++)
        {
            int i = cur % n, j = cur / n, next = cur;
            float bd = d[cur];
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    int ii = i + di, jj = j + dj;
                    if (ii < 0 || jj < 0 || ii >= n || jj >= n) continue;
                    int m = jj * n + ii;
                    if (free[m] && d[m] < bd) { bd = d[m]; next = m; }
                }
            if (next == cur) break;
            cur = next;
            var p = At(cur);
            if (!Clear(x, z, p.X, p.Z)) break;
            best = p;
        }
        return best;
    }

    bool Clear(double x0, double z0, double x1, double z1)
    {
        double len = Math.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0));
        int steps = Math.Max(1, (int)(len / (Cell * 0.5)));
        for (int s = 1; s <= steps; s++)
        {
            double t = (double)s / steps;
            int k = Index(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t);
            if (k < 0 || !free[k]) return false;
        }
        return true;
    }
}
