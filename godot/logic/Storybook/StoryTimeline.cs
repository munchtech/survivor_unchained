using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Storybook;

/// <summary>A plate placed in time: drawn from Start (its "at", where its
/// transition in begins) until DrawEnd (its "until", or later while the next
/// plate's transition is still spreading over it).</summary>
public sealed record PlateSpan(StoryPlate Plate, int Index, double Start, double DrawEnd)
{
    public double Until => Plate.Until;
    /// <summary>Its transition in is done.</summary>
    public double InEnd => Start + (Plate.In.Kind == "cut" ? 0 : Plate.In.Dur);
}

/// <summary>What the screen shows at a moment: the plate under (null: black),
/// the plate coming in over it (null: none), and how far the transition has
/// got (0..1, linear: the shader eases it).</summary>
public readonly record struct StoryMix(PlateSpan? Under, PlateSpan? Over, double K);

public sealed record TimedStoryCue(double T, int Order, StoryCue Cue, PlateSpan? Plate);

/// <summary>
/// A storybook laid out in time. The rule for overlaps: a plate's "at" is
/// when its transition in starts, and the plate before it is drawn on until
/// that transition ends. At most two plates are mixed at once: the newest
/// whose transition is under way over the one it is replacing.
/// </summary>
public sealed class StoryTimeline
{
    public readonly StoryFile File;
    public readonly List<PlateSpan> Spans = new();
    public readonly List<TimedStoryCue> Cues = new();
    public double Length => File.End;

    public StoryTimeline(StoryFile f)
    {
        File = f;
        var plates = f.Plates;
        for (int i = 0; i < plates.Count; i++)
        {
            var p = plates[i];
            double end = p.Until;
            // Drawn on under every plate that starts while it is still up, until that one has spread over it.
            for (int j = i + 1; j < plates.Count && plates[j].At <= p.Until + 1e-6; j++)
                end = Math.Max(end, plates[j].At + (plates[j].In.Kind == "cut" ? 0 : plates[j].In.Dur));
            Spans.Add(new PlateSpan(p, i, p.At, end));
        }
        // Same moment: in the order written, the file's own cues before its plates'.
        int order = 0;
        foreach (var c in f.Cues) Cues.Add(new TimedStoryCue(c.At, order++, c, null));
        foreach (var s in Spans)
            foreach (var c in s.Plate.Cues) Cues.Add(new TimedStoryCue(s.Start + c.At, order++, c, s));
        Cues.Sort((a, b) => a.T != b.T ? a.T.CompareTo(b.T) : a.Order.CompareTo(b.Order));
    }

    /// <summary>The plates drawn at t, oldest first.</summary>
    public List<PlateSpan> Drawn(double t) => Spans.Where(s => t >= s.Start && t < s.DrawEnd).ToList();

    public StoryMix Mix(double t)
    {
        var drawn = Drawn(t);
        if (drawn.Count == 0) return new StoryMix(null, null, 0);
        var top = drawn[^1];
        if (t < top.InEnd)
        {
            double k = Math.Clamp((t - top.Start) / Math.Max(1e-6, top.InEnd - top.Start), 0, 1);
            // The plate it spreads over: the newest before it still drawn (none: over black).
            var under = drawn.Count > 1 ? drawn[^2] : null;
            return new StoryMix(under, top, k);
        }
        return new StoryMix(top, null, 0);
    }

    /// <summary>A plate's own fade out at t (0..1 toward its out colour).</summary>
    public static double OutFade(PlateSpan s, double t)
    {
        if (s.Plate.Out is not { } o || o.Dur <= 0) return 0;
        return Math.Clamp((t - (s.Until - o.Dur)) / o.Dur, 0, 1);
    }

    /// <summary>The cues after `from` up to and including `to`: what a frame from one to the other
    /// sets off (start from a little below 0, so cues at 0 go on the first frame).</summary>
    public IEnumerable<TimedStoryCue> Between(double from, double to) => Cues.Where(c => c.T > from && c.T <= to);

    /// <summary>Whether holding to skip counts yet: from Skip.From seconds on a first view, at once once seen.</summary>
    public static bool CanSkip(double t, bool seen, StorySkip skip) => seen || t >= skip.From;
}
