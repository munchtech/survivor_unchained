using System.Collections.Generic;

namespace SurvivorUnchained.Core;

/// <summary>
/// Seeded random stream (mulberry32). The simulation draws from one of these
/// instead of a global random so an expedition can be replayed from its seed
/// and so tests are deterministic. Bit for bit the web game's stream: the
/// same seed gives the same numbers.
/// </summary>
public sealed class Rng
{
    uint s;

    public Rng(uint seed = 0x9e3779b9) { s = seed == 0 ? 1 : seed; }

    public uint State { get => s; set => s = value == 0 ? 1 : value; }

    /// <summary>[0, 1)</summary>
    public double Next()
    {
        unchecked
        {
            s += 0x6D2B79F5u;
            uint t = s;
            t = (t ^ (t >> 15)) * (t | 1u);
            t ^= t + (t ^ (t >> 7)) * (t | 61u);
            return (t ^ (t >> 14)) / 4294967296.0;
        }
    }

    public double Range(double lo, double hi) => lo + (hi - lo) * Next();
    public int Int(int lo, int hiInclusive) => lo + (int)System.Math.Floor(Next() * (hiInclusive - lo + 1));
    public bool Chance(double p) => Next() < p;
    public int Sign() => Next() < 0.5 ? -1 : 1;
    public T Pick<T>(IReadOnlyList<T> list) => list[(int)System.Math.Floor(Next() * list.Count)];

    /// <summary>Weighted pick.</summary>
    public T Weighted<T>(IReadOnlyList<T> list, System.Func<T, double> weight)
    {
        double total = 0;
        foreach (var a in list) total += weight(a);
        double r = Next() * total;
        foreach (var a in list)
        {
            r -= weight(a);
            if (r <= 0) return a;
        }
        return list[^1];
    }

    public List<T> Shuffle<T>(List<T> list)
    {
        for (int i = list.Count - 1; i > 0; i--)
        {
            int j = (int)System.Math.Floor(Next() * (i + 1));
            (list[i], list[j]) = (list[j], list[i]);
        }
        return list;
    }

    /// <summary>Gaussian-ish via a sum of uniforms.</summary>
    public double Normal(double mean = 0, double sd = 1) =>
        mean + sd * ((Next() + Next() + Next() + Next() - 2) * 1.7320508);

    /// <summary>Shared stream for purely cosmetic randomness (particles, idle
    /// offsets). Never used by the simulation, so visuals can't desync
    /// gameplay.</summary>
    public static readonly Rng Fx = new(0xc0ffee);
}
