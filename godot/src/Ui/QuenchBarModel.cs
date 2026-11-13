using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Ui;

/* (bd-ui2, no Godot: tests link this file) The Quench card's odds strip as numbers: five segments, always in the
 * same order (perfect, finer, nothing, a grade lost, ruin), each as wide as its real share of QuenchOdds(). */
public static class QuenchBarModel
{
    public sealed record Segment(string Id, string Label, double Weight, double Fraction, bool Warm, bool Cold);

    /// <summary>The outcomes left to right, with the word shown for each.</summary>
    public static readonly (string Id, string Label)[] Order =
    {
        ("perfect", "Perfect"), ("up", "Finer"), ("nothing", "Nothing"), ("down", "Grade lost"), ("ruin", "Ruin"),
    };

    /// <summary>The strip for these odds (Crafting.QuenchOdds(): outcome and its share). Missing outcomes weigh nothing;
    /// the fractions are re-taken over what is given, so they always sum to one (zero everywhere when nothing is given).</summary>
    public static List<Segment> Build(IEnumerable<(string Outcome, double Chance)> odds)
    {
        var w = odds.GroupBy(o => o.Outcome).ToDictionary(g => g.Key, g => g.Sum(o => o.Chance));
        double total = Order.Sum(o => w.GetValueOrDefault(o.Id));
        return Order.Select(o =>
        {
            double x = w.GetValueOrDefault(o.Id);
            return new Segment(o.Id, o.Label, x, total > 0 ? x / total : 0, o.Id is "perfect" or "up", o.Id is "down");
        }).ToList();
    }

    /// <summary>A share as a whole percent for the label ("6%"), never "0%" for a chance that exists.</summary>
    public static string Percent(double fraction) => fraction <= 0 ? "0%" : $"{System.Math.Max(1, (int)System.Math.Round(fraction * 100))}%";

    /// <summary>(bd-ui2 r2) What each outcome does to THIS piece, in a few characters: the grades of its plain powers
    /// (tiers), the piece's cap and the rule numbers. One shared grade reads "III -> V"; mixed grades say how many powers
    /// and which way. Keyed by outcome id.</summary>
    public static Dictionary<string, string> Effects(IReadOnlyList<int> tiers, int cap, int bright, int up, int down, int ruin, System.Func<int, string> grade)
    {
        int? g = tiers.Count > 0 && tiers.All(t => t == tiers[0]) ? tiers[0] : null;
        string Common(int to) => to == g ? $"stays {grade(to)}" : $"{grade(g!.Value)} -> {grade(to)}";
        var r = new Dictionary<string, string>();
        if (tiers.Count == 0) { foreach (var o in Order) r[o.Id] = "no powers to move"; return r; }
        r["perfect"] = g != null ? Common(bright) : tiers.All(t => t == bright) ? "stays" : $"all to {grade(bright)}";
        int canUp = tiers.Count(t => t < cap), canDown = tiers.Count(t => t > 0);
        r["up"] = canUp == 0 ? "no room above" : g != null ? Common(g.Value + 1) : $"{System.Math.Min(up, canUp)} powers +1";
        r["nothing"] = g != null ? $"stays {grade(g.Value)}" : "stays";
        r["down"] = canDown == 0 ? "stays" : g != null ? Common(g.Value - 1) : $"{System.Math.Min(down, canDown)} powers -1";
        r["ruin"] = canDown == 0 ? "stays" : g != null ? Common(System.Math.Max(0, g.Value - ruin)) : $"all -{ruin} grades";
        return r;
    }
}
