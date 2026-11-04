using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* The ultimate's family (H7): the stop, the grade and the marks every Strike Flare shares, as data
 * (data/content/flare_family.json). The view reads it (Fx/Flare/FlareFx.Family.cs, FlareMarksView.cs); the sim never does:
 * no number or target of a Flare changes here. */
public static class FlareFamily
{
    public sealed class StopRules
    {
        public Dictionary<string, double> Calling = new();
        public double Clutch, Banked, Min = 0.25, Max = 0.4, WorldRate, Hush = 0.06;
    }

    public sealed class Grade
    {
        public double Value = 1, Keep = 1, Lights = 1, Emit = 1;
        public string Tint = "#ffffff";
    }

    public sealed class GradeRules
    {
        public double In = 0.066, Out = 0.5;
        public Grade Night = new(), Day = new();
        public Grade Of(bool night) => night ? Night : Day;
    }

    public sealed class MarkLight { public double Gain = 1, Dark, Strip; }

    public sealed class MarkRules
    {
        public double Scale = 1.5, Ripple = 0.1, Pop = 0.15, Fade = 0.2, Main = 2, Pulse = 1.6, Pillar = 2.4, Rim = 0.7;
        public MarkLight Night = new(), Day = new();
        public MarkLight Of(bool night) => night ? Night : Day;
    }

    public sealed class Own { public double? Stop; }

    sealed class File
    {
        public StopRules Stop = new();
        public GradeRules Grade = new();
        public MarkRules Marks = new();
        public Dictionary<string, Own> Flares = new();
    }

    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("flare_family.json"));

    public static StopRules Stop => F.Stop;
    public static GradeRules Grades => F.Grade;
    public static MarkRules Marks => F.Marks;

    /// <summary>The stop's real seconds for a Flare: its own, else its calling's, plus the clutch's and a banked charge's,
    /// clamped to [min, max].</summary>
    public static double StopOf(string flare, string calling, bool clutch, bool banked)
    {
        var s = F.Stop;
        double t = F.Flares.TryGetValue(flare, out var o) && o.Stop is { } own ? own
            : s.Calling.TryGetValue(calling, out var c) ? c : s.Max;
        t += (clutch ? s.Clutch : 0) + (banked ? s.Banked : 0);
        return Math.Clamp(t, s.Min, s.Max);
    }

    public static void Reload() => file = null;
}
