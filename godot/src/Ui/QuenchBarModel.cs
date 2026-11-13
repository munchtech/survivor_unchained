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
}
