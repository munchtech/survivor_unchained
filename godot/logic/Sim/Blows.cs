using System;

namespace SurvivorUnchained.Sim;

/// <summary>Counts of blows that take parts of a blow (a chain's cut is a share of the written blow).</summary>
public static class Blows
{
    public const double Eps = 1e-9;

    /// <summary>Will a firing of weight w complete the every-th blow? (w = 1: exactly (n + 1) % every == 0.)</summary>
    public static bool Completes(int n, double part, int every, double w) => every > 0 && n % every + part + w >= every - Eps;

    /// <summary>Count a firing of weight w: whole blows go to n, the part is carried (never reset).</summary>
    public static void Count(ref int n, ref double part, double w)
    {
        part += w;
        while (part >= 1 - Eps) { part = Math.Max(0, part - 1); n++; }
    }

    /// <summary>A per-blow chance as a per-cut chance: the cuts of one blow's worth compound to c.</summary>
    public static double Chance(double c, double w) => w == 1 || c <= 0 || c >= 1 ? c : 1 - Math.Pow(1 - c, w);
}
