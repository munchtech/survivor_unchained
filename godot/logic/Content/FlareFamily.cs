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

    public sealed class MarkLight { public double Gain = 1, Dark, Strip, Cap = 1; }

    public sealed class MarkRules
    {
        public double Scale = 1.5, Ripple = 0.1, Pop = 0.15, Fade = 0.2, Main = 2, Pulse = 1.6, Pillar = 2.4, Rim = 0.7;
        /// <summary>The ring's band (its width, x the ring's radius), the warm pool inside it (its light x the ring's, and
        /// how far toward her ember's warmth it leans), the pop's growth (x the ring), the path seam's core and glow widths (m).</summary>
        public double Band = 0.07, Pool = 0.14, Warm = 0.45, PopGrow = 0.45, SeamCore = 0.09, SeamGlow = 0.45, SeamShimmer = 0.8;
        public MarkLight Night = new(), Day = new();
        public MarkLight Of(bool night) => night ? Night : Day;
    }

    /// <summary>A Flare's own: its stop; its main blow (the Blow event's Part, and when Last only its last such); where
    /// its band runs from ("her", or "line": out from the blow's line, X/Z to TX/TZ).</summary>
    public sealed class Own { public double? Stop; public string Blow = ""; public bool Last; public string From = "her"; }

    public sealed class BandLight { public double Gain = 0.5, Wake = 0.3; }

    /// <summary>The shock band on the main blow: its front runs Reach m in Time s (Flare time, eased out by Ease), its soft
    /// lead and its wake (m), and its fade over the last share of its run (Fade).</summary>
    public sealed class BandRules
    {
        public double Reach = 30, Time = 0.3, Ease = 1.6, Lead = 1.4, Wake = 3, Fade = 0.35;
        public BandLight Night = new(), Day = new();
        public BandLight Of(bool night) => night ? Night : Day;
    }

    /// <summary>The beat: the camera's kick (px at 1080p), a drop's landing after the band (s) and its scale-in, a
    /// decision-marked hit's hold after its mark shows (frames), the numbers' wait after the band (s).</summary>
    public sealed class BeatRules { public double KickPx = 3, DropLag = 0.05, DropGrow = 0.3, DecisionFrames = 2, NumberLag = 0.02, SpendLight = 8, SpendLightDay = 8; }

    /// <summary>The recovery: her ember's pool x Pool for Hold s from the main blow, then back over Out s.</summary>
    public sealed class RecoveryRules { public double Pool = 1.3, Hold = 2, Out = 0.4; }

    sealed class File
    {
        public StopRules Stop = new();
        public GradeRules Grade = new();
        public MarkRules Marks = new();
        public BandRules Band = new();
        public BeatRules Beat = new();
        public RecoveryRules Recovery = new();
        public Dictionary<string, Own> Flares = new();
    }

    static readonly Own None = new();
    public static BandRules Band => F.Band;
    public static BeatRules Beat => F.Beat;
    public static RecoveryRules Recovery => F.Recovery;
    /// <summary>A Flare's own rules (an empty one when it has none).</summary>
    public static Own Of(string flare) => F.Flares.TryGetValue(flare, out var o) ? o : None;

    /// <summary>Whether this Blow event is the Flare's main blow (its data's part, its last when the data says so).</summary>
    public static bool IsMain(string flare, string part, bool last)
    {
        var o = Of(flare);
        if (o.Blow.Length == 0) return last;
        return part == o.Blow && (!o.Last || last);
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
