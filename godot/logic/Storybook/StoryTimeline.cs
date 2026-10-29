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

    /// <summary>The first moment after t that the screen is black: a gap with no plate drawn
    /// (the storybook's end black among them), a plate's own fade out to black done with
    /// nothing drawn over it, or the end. +inf when it never goes black after t.</summary>
    public double BlackAfter(double t)
    {
        double at = File.End > t ? File.End : double.PositiveInfinity;
        foreach (var s in Spans)
        {
            if (s.DrawEnd > t && Drawn(s.DrawEnd).Count == 0) at = Math.Min(at, s.DrawEnd);
            if (s.Plate.Out is { Dur: > 0 } o && DarkColour(o.Color) && s.Until > t
                && Drawn(s.Until - 1e-6) is [var only] && only == s)
                at = Math.Min(at, s.Until);
        }
        return at;
    }

    /// <summary>How long a subtitle set at `at` may show: its own length, cut so it is gone
    /// (its own fade out done) by the time the screen goes to black: never over the end
    /// black or a plate's fade out to black.</summary>
    public double SubtitleFor(double at, double seconds) => Math.Max(0, Math.Min(seconds, BlackAfter(at) - at));

    /// <summary>How long a subtitle set at `at` for `seconds` takes to fade out: a quarter second, or,
    /// when it is still up as a plate fades to black, from that fade's start to its own end (it goes
    /// down with the picture, never bright over the black).</summary>
    public double SubtitleFade(double at, double seconds, double fade = 0.25)
    {
        double shown = SubtitleFor(at, seconds), black = BlackAfter(at), end = at + shown;
        if (shown <= 0) return 0;
        foreach (var s in Spans)
            if (Math.Abs(s.Until - black) < 1e-6 && s.Plate.Out is { Dur: > 0 } o && DarkColour(o.Color)
                && end > s.Until - o.Dur)
                return Math.Max(Math.Min(fade, shown), end - Math.Max(at, s.Until - o.Dur));
        return Math.Min(fade, shown);
    }

    /// <summary>A fade's colour reads as black (unset: black).</summary>
    static bool DarkColour(string? hex)
    {
        if (string.IsNullOrEmpty(hex) || hex == "black") return true;
        var h = hex.TrimStart('#');
        if (h.Length < 6) return false;
        try
        {
            int r = Convert.ToInt32(h[..2], 16), g = Convert.ToInt32(h[2..4], 16), b = Convert.ToInt32(h[4..6], 16);
            return 0.2126 * r + 0.7152 * g + 0.0722 * b < 26;
        }
        catch (FormatException) { return false; }
    }

    /// <summary>The silence a storybook's seam may lose: the cinematic after it (C01 after SB00) opens on a
    /// black shot whose sounds are timed from its end; the frames the zone took to stand up under the black
    /// were already silence, so the shot's lengths for after the storybook (its "durs" with a when) lose that
    /// much, down to `keep` (its sounds' share: C01's first drop is 1.3 s from its end). Returns the cut.</summary>
    public static double CutSeam(SurvivorUnchained.Cinema.CineShot shot, double loadSec, double keep)
    {
        double cut = 0;
        foreach (var d in shot.Durs ?? new())
            if (d.When != null)
            {
                double was = d.Dur;
                d.Dur = Math.Max(keep, d.Dur - Math.Max(0, loadSec));
                cut = Math.Max(cut, was - d.Dur);
            }
        return cut;
    }

    /// <summary>--sb-skip-at S: the test switch's skip is due (storybook time S reached).</summary>
    public static bool SkipDue(double t, double? at) => at is { } a && t >= a - 1e-9;

    /// <summary>Whether holding to skip counts yet: from Skip.From seconds on a first view, at once once seen.</summary>
    public static bool CanSkip(double t, bool seen, StorySkip skip) => seen || t >= skip.From;
}
