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

    /// <summary>Count a firing of an every-N count (a skill's own heavy, the Hand's, a rite's): as Count, but the
    /// opening firing of a fresh count is a whole blow, so a fight's first heavy comes no later than the written
    /// blows' (Sunder's every 4th: cut 8 at 4.9 s for the 4th blow at 4.8 s, not cut 10). The cycle after it is
    /// unchanged; at weight 1 it is Count. (Completes read ahead on a fresh count agrees for every >= 2: the opening
    /// firing completes nothing at either weight.)</summary>
    public static void CountFirstWhole(ref int n, ref double part, double w) =>
        Count(ref n, ref part, n == 0 && part == 0 && w < 1 ? 1 : w);

    /// <summary>(M3 MR 3 b1, the landed rule) A chained cut weighs what the wait has earned since its grip's last cut
    /// that LANDED (Battle.BankOf: `earned`, in written blows), at most one whole blow, never under its own share (the
    /// cut's share of the written blow, times a heavy's longer period). Earned within 1e-9 of the share (the held
    /// chain on its beat) is the share to the bit.</summary>
    public static double Rested(double own, double earned) => earned <= own + 1e-9 ? own : Math.Max(own, Math.Min(1, earned));

    /// <summary>A per-blow chance as a per-cut chance: the cuts of one blow's worth compound to c.</summary>
    public static double Chance(double c, double w) => w == 1 || c <= 0 || c >= 1 ? c : 1 - Math.Pow(1 - c, w);
}
