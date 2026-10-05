using System;
using System.Collections.Generic;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>Distance to one place over the ground the survivor can stand on, at half a metre, with
/// what stands on the ground taken from the battle's own collision at her radius: the bots' way
/// through a map (or a story night's place, within its bounds). Downhill from anywhere is the
/// shortest way there; Onward looks as far down it as a straight line stays clear.</summary>
public sealed class NavField
{
    const double Cell = 0.5;
    readonly int nx, nz;
    readonly double ox, oz;
    readonly bool[] free;
    readonly float[] d;

    /// <param name="box">Only this rectangle (a story night's place: a fiftieth of a map's cells).</param>
    public NavField(MapBuild map, Battle b, double toX, double toZ, (double X0, double Z0, double X1, double Z1)? box = null)
    {
        double half = map.Meta.Size / 2;
        var (x0, z0, x1, z1) = box ?? (-half, -half, half, half);
        ox = x0; oz = z0;
        nx = (int)((x1 - x0) / Cell) + 1;
        nz = (int)((z1 - z0) / Cell) + 1;
        free = new bool[nx * nz];
        // In a story night's place, a little more room: a way drawn a hair from a wall's corner was a
        // way the hands could not walk (they caught on the corner and stood).
        double r = b.Player.Radius + (box != null ? 0.25 : 0.05);
        for (int j = 0; j < nz; j++)
            for (int i = 0; i < nx; i++)
            {
                double x = ox + i * Cell, z = oz + j * Cell;
                // As the survivor meets it: the player-only edges too (Blocked leaves them out).
                double rx = x, rz = z;
                free[j * nx + i] = map.CanStand(x, z) && !b.Collision.Resolve(ref rx, ref rz, r, true);
            }
        d = new float[nx * nz];
        Array.Fill(d, float.MaxValue);
        int start = Nearest(Index(toX, toZ), any: true);
        if (start < 0) return;
        var q = new PriorityQueue<int, float>();
        d[start] = 0;
        q.Enqueue(start, 0);
        while (q.TryDequeue(out int k, out float dk))
        {
            if (dk > d[k]) continue;
            int i = k % nx, j = k / nx;
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    if (di == 0 && dj == 0) continue;
                    int ii = i + di, jj = j + dj;
                    if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue;
                    int m = jj * nx + ii;
                    if (!free[m]) continue;
                    // No cutting a corner between two blocked cells.
                    if (di != 0 && dj != 0 && (!free[j * nx + ii] || !free[jj * nx + i])) continue;
                    float step = (float)(Cell * (di != 0 && dj != 0 ? 1.414 : 1));
                    if (dk + step < d[m]) { d[m] = dk + step; q.Enqueue(m, d[m]); }
                }
        }
    }

    int Index(double x, double z)
    {
        int i = (int)Math.Round((x - ox) / Cell), j = (int)Math.Round((z - oz) / Cell);
        return i < 0 || j < 0 || i >= nx || j >= nz ? -1 : j * nx + i;
    }

    (double X, double Z) At(int k) => (ox + k % nx * Cell, oz + k / nx * Cell);

    /// <summary>The nearest free cell to this one (itself if free), searching out a few metres; `any`:
    /// whether or not anything leads there yet (the field's own start).</summary>
    int Nearest(int k, bool any = false)
    {
        if (k < 0) return -1;
        if (free[k]) return k;
        int i0 = k % nx, j0 = k / nx;
        for (int r = 1; r < 16; r++)
            for (int dj = -r; dj <= r; dj++)
                for (int di = -r; di <= r; di++)
                {
                    if (Math.Abs(di) != r && Math.Abs(dj) != r) continue;
                    int ii = i0 + di, jj = j0 + dj;
                    if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue;
                    if (free[jj * nx + ii] && (any || d[jj * nx + ii] < float.MaxValue)) return jj * nx + ii;
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
        // Off the free ground, the free cell nearby that is furthest on (the nearest one flipped from
        // one side of her to the other as she was pushed, and the hands went back and forth for minutes).
        if (k != Index(x, z) && Index(x, z) is int here and >= 0)
        {
            int i0 = here % nx, j0 = here / nx;
            for (int dj = -3; dj <= 3; dj++)
                for (int di = -3; di <= 3; di++)
                {
                    int ii = i0 + di, jj = j0 + dj;
                    if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue;
                    int m = jj * nx + ii;
                    if (free[m] && d[m] < d[k]) k = m;
                }
        }
        // Pushed off the free ground (against a stump, in a corner): look on from the nearest free
        // cell, or the hands go back and forth between it and the way on.
        if (k != Index(x, z)) (x, z) = At(k);
        var best = At(k);
        int cur = k;
        for (int s = 0; s < (int)(reach / Cell); s++)
        {
            int i = cur % nx, j = cur / nx, next = cur;
            float bd = d[cur];
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    int ii = i + di, jj = j + dj;
                    if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue;
                    int m = jj * nx + ii;
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

    /// <summary>The whole way from here to the goal, cell by cell down the field (empty where nothing leads).</summary>
    public List<(double X, double Z)> Path(double x, double z)
    {
        var o = new List<(double X, double Z)>();
        int k = Nearest(Index(x, z));
        if (k < 0 || d[k] == float.MaxValue) return o;
        for (int s = 0; s < nx * nz && d[k] > 0; s++)
        {
            int i = k % nx, j = k / nx, next = k;
            float bd = d[k];
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++)
                {
                    int ii = i + di, jj = j + dj;
                    if (ii < 0 || jj < 0 || ii >= nx || jj >= nz) continue;
                    int m = jj * nx + ii;
                    if (free[m] && d[m] < bd) { bd = d[m]; next = m; }
                }
            if (next == k) break;
            k = next;
            o.Add(At(k));
        }
        return o;
    }

    /// <summary>A straight walk between two points stays on free ground.</summary>
    public bool Clear(double x0, double z0, double x1, double z1)
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
