using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/// <summary>
/// Uniform-grid spatial hash over integer ids, rebuilt once per tick. Queries
/// return candidates from the overlapping cells into a caller-owned list, so
/// a query allocates nothing.
/// </summary>
public sealed class SpatialHash
{
    readonly int[] heads;
    int[] next;
    readonly int cols, rows;
    public readonly double Size, Cell;

    public SpatialHash(double size, double cell, int capacity)
    {
        Size = size; Cell = cell;
        cols = (int)Math.Ceiling(size / cell);
        rows = cols;
        heads = new int[cols * rows];
        Array.Fill(heads, -1);
        next = new int[capacity];
        Array.Fill(next, -1);
    }

    double Half => Size / 2;

    public void Clear() => Array.Fill(heads, -1);

    public void Insert(int id, double x, double z)
    {
        int cx = (int)Math.Floor((x + Half) / Cell), cz = (int)Math.Floor((z + Half) / Cell);
        if (cx < 0 || cz < 0 || cx >= cols || cz >= rows) return;
        int c = cz * cols + cx;
        if (id >= next.Length)
        {
            var n = new int[Math.Max(id + 1, next.Length * 2)];
            Array.Fill(n, -1);
            next.CopyTo(n, 0);
            next = n;
        }
        next[id] = heads[c];
        heads[c] = id;
    }

    /// <summary>Candidate ids whose cell overlaps the query circle's bounding square.</summary>
    public List<int> Query(double x, double z, double r, List<int> output)
    {
        output.Clear();
        double h = Half;
        int x0 = Math.Max(0, (int)Math.Floor((x - r + h) / Cell)), x1 = Math.Min(cols - 1, (int)Math.Floor((x + r + h) / Cell));
        int z0 = Math.Max(0, (int)Math.Floor((z - r + h) / Cell)), z1 = Math.Min(rows - 1, (int)Math.Floor((z + r + h) / Cell));
        for (int cz = z0; cz <= z1; cz++)
            for (int cx = x0; cx <= x1; cx++)
                for (int id = heads[cz * cols + cx]; id != -1; id = next[id]) output.Add(id);
        return output;
    }
}
