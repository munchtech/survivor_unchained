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
        /// <summary>Fx: the fight's own lingering light x (BattleFx.FlareDim; danger marks stay full).</summary>
        public double Value = 1, Keep = 1, Lights = 1, Emit = 1, Fx = 1;
        public string Tint = "#ffffff";
    }

    public sealed class GradeRules
    {
        /// <summary>Pool: her ember's pool x through the stop, eased with the grade.</summary>
        public double In = 0.066, Out = 0.5, Pool = 1;
        public Grade Night = new(), Day = new();
        public Grade Of(bool night) => night ? Night : Day;
    }

    public sealed class MarkLight { public double Gain = 1, Dark, Strip, Cap = 1; }

    public sealed class MarkRules
    {
        /// <summary>The pool (r2): its radius at a quarter light x the foe's, its falloff's power, its lift over HeightAt (m),
        /// its heart's lean to her ember; the Main's size and light x, its core (radius x the pool's, light x its peak).</summary>
        public double Size = 2.3, Falloff = 2.4, Above = 0.25, Warm = 0.3, Main = 2, Core = 0.32, CoreGain = 1.4, Pulse = 1.6;
        public double Ripple = 0.1, Fade = 0.2, Rim = 0.7, Lift = 0.9;
        /// <summary>The hit (r2 fix 3): the pool's size and light x when the band reaches its foe, the share of that by the
        /// blow (eased in over PreTime s from the release), and the hand-over to the band's rim (s).</summary>
        public double Tight = 0.64, TightLight = 1.7, PreTight = 0.3, PreTime = 0.25, Hand = 0.05;
        public double SeamCore = 0.09, SeamGlow = 0.45, SeamShimmer = 0.8;
        public MarkLight Night = new(), Day = new();
        public MarkLight Of(bool night) => night ? Night : Day;
    }

    /// <summary>The dust in the stop (r2 fix 4, in the web's place): FlareFx.Dust.</summary>
    public sealed class DustLight { public double Light = 0.16, Warm = 0.7; }
    public sealed class DustRules
    {
        public int Count = 440;
        public double Across = 24, Near = 14, Far = 18, Low = 0.2, High = 2.8, Glint = 0.08, GlintSize = 1.6, Drift = 0.025;
        public double[] Size = { 0.04, 0.1 };
        public string Color = "#b4c0f0", WarmColor = "#ffa860";
        public double WarmReach = 5, Gust = 4.5, Up = 1.2, Drag = 2.5, Flash = 2.2, FlashTime = 0.1, Gone = 0.35;
        public DustLight Night = new(), Day = new();
        public DustLight Of(bool night) => night ? Night : Day;
    }

    /// <summary>The foreshadow (r2 fix 7): a "crack" path Flare's future crack lit faintly in the stop, a spark along it.</summary>
    public sealed class ForeLight { public double Light = 0.5, SparkLight = 2.6; }
    public sealed class ForeshadowRules
    {
        public double Blur = 3, Heat = 0.42, Wander = 0.5, In = 0.08, SparkTime = 0.42, SparkFrom = 0.04, SparkGap = 0.12, SparkTail = 2.2;
        public ForeLight Night = new(), Day = new();
        public ForeLight Of(bool night) => night ? Night : Day;
    }

    /// <summary>A Flare's own: its stop; its main blow (the Blow event's Part, and when Last only its last such); where
    /// its band runs from ("her", or "line": out from the blow's line, X/Z to TX/TZ).</summary>
    public sealed class Own
    {
        public double? Stop; public string Blow = ""; public bool Last; public string From = "her";
        /// <summary>The Long Cut's fuse along its seam (m/s; 0: the view's own).</summary>
        public double Fuse;
        /// <summary>Its peak's shape (the light at the main blow): "disk" round where it lands, or "line" along its line.</summary>
        public PeakShape Peak = new();
        /// <summary>The Blow part whose earlier blows are an air and dust ripple, no light (Bell's tolls); "" none.</summary>
        public string Ripple = "";
        /// <summary>A line Flare's path in the stop: "strip" (the marks' seam) or "crack" (its future crack, FlareFx.LongCut).</summary>
        public string Path = "strip";
    }

    /// <summary>A Flare's peak shape: "disk" (Radius m, a Column m tall at its heart) or "line" (Width m either side of its
    /// line, its whole length).</summary>
    public sealed class PeakShape { public string Shape = ""; public double Radius = 8, Width = 2.5, Column, Gain = 1; }

    public sealed class PeakLight { public double Light = 6, Ground = 1, Column = 3; }

    /// <summary>The PEAK at the main blow (H7 r2): Hitstop drawn frames held on the blow frame (the Strike's own on its other
    /// blows); Frames the light's envelope by drawn frame from the blow (real time); Color its dawn gold; Release the
    /// push-in's release from the blow (s); the rig's lights' Height (m), Range (m), Spacing along a line (m) and most
    /// Lights; Night/Day: Light (an omni's energy at the envelope's 1), Ground (the lit shape's light, x albedo), Column (HDR).</summary>
    public sealed class PeakRules
    {
        public int Hitstop = 2, Lights = 6;
        public double[] Frames = { 1, 1, 0.7, 0.3 };
        public string Color = "#ffbe6a";
        public double Release = 0.15, Height = 0.4, Range = 6, Spacing = 4.5;
        public PeakLight Night = new(), Day = new();
        public PeakLight Of(bool night) => night ? Night : Day;
    }

    /// <summary>An air and dust ripple (Bell's first tolls): its front runs Reach m in Time s (Flare time), Lead m soft, a
    /// Dust lift of the ground's value (x, no light), Puffs dust puffs thrown out along it.</summary>
    public sealed class RippleRules { public double Reach = 10, Time = 0.25, Lead = 0.8, Dust = 0.35; public int Puffs = 28; }

    public sealed class BandLight { public double Front = 1, Tail = 0.45; }

    /// <summary>The band on the main blow, a lit FRONT: it runs Reach m in Time s (Flare time, eased out by Ease: at x of
    /// its run it stands at Reach (1 - (1 - x)^Ease)), its soft leading edge Lead m, the ground lit behind it for After s;
    /// its fade over the last share of its run (Fade). Night/Day: Front its light (x albedo), Tail the lit ground's share.</summary>
    public sealed class BandRules
    {
        public double Reach = 22, Time = 0.28, Ease = 1.35, Lead = 0.55, After = 0.15, Fade = 0.3;
        public BandLight Night = new(), Day = new();
        public BandLight Of(bool night) => night ? Night : Day;
    }

    /// <summary>The beat: the camera's kick (px at 1080p), a drop's landing after the band (s) and its scale-in, a
    /// decision-marked hit's hold after its mark shows (frames), the numbers' wait after the band (s).</summary>
    public sealed class BeatRules { public double KickPx = 9, DropLag = 0.05, DropGrow = 0.3, DecisionFrames = 2, NumberLag = 0.02, SpendLight = 8, SpendLightDay = 8; }

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
        public PeakRules Peak = new();
        public RippleRules Ripple = new();
        public DustRules Dust = new();
        public ForeshadowRules Foreshadow = new();
        public Dictionary<string, Own> Flares = new();
    }

    static readonly Own None = new();
    public static BandRules Band => F.Band;
    public static BeatRules Beat => F.Beat;
    public static RecoveryRules Recovery => F.Recovery;
    public static PeakRules Peak => F.Peak;
    public static RippleRules Ripple => F.Ripple;
    public static DustRules Dust => F.Dust;
    public static ForeshadowRules Foreshadow => F.Foreshadow;
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
