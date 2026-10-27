using System;

namespace SurvivorUnchained.Core;

/// <summary>
/// How far a hanging front panel (the Reaver's loincloth: a "panels" bone in
/// art/people/rig_helpers.json) swings forward with her leading thigh. The
/// law is tools/anim/helpers.py's panel_turn, number for number; HerJoints
/// turns the bone by it. Plain C#, so the tests hold it to the tools'.
/// </summary>
public static class PanelSwing
{
    public readonly record struct Law(double Amount, double Soft, double SpreadFrom, double SpreadTo, double SpreadDamp, double FallTau = 0.04, double FallRate = 450,
        double Drop = 0, double DropFrom = 45);

    /// <summary>Polynomial smooth max, <paramref name="k"/> wide (max + k/4 where a == b).</summary>
    public static double SmoothMax(double a, double b, double k)
    {
        double h = Math.Max(k - Math.Abs(a - b), 0) / k;
        return Math.Max(a, b) + h * h * k / 4;
    }

    /// <summary>0 below 0, x - k/2 above k, a quadratic between (smooth, never below 0).</summary>
    public static double SoftRelu(double x, double k) => x <= 0 ? 0 : x < k ? x * x / (2 * k) : x - k / 2;

    static double Smooth(double t)
    {
        t = Math.Clamp(t, 0, 1);
        return t * t * (3 - 2 * t);
    }

    /// <summary>Degrees the panel turns forward from each thigh's forward swing
    /// (fl, fr) and spread (al, ar), degrees from rest: the leading thigh's
    /// swing (a smooth max, so no pop as the legs cross), never back, damped
    /// as the thighs spread (on a seat with the knees apart it lifts less).</summary>
    public static double Turn(in Law law, double fl, double fr, double al, double ar)
    {
        double k = law.Soft;
        double lead = SmoothMax(fl, fr, k) - k / 4;
        double sp = Smooth(((al + ar) / 2 - law.SpreadFrom) / (law.SpreadTo - law.SpreadFrom));
        double t = law.Amount * SoftRelu(lead, k) * (1 - law.SpreadDamp * sp);
        // (Body 18: past DropFrom degrees of lead, Drop a degree less, not with the thighs spread: on the thigh, not over it)
        if (law.Drop != 0) t -= law.Drop * SoftRelu(lead - law.DropFrom, k) * (1 - sp);
        return t;
    }

    /// <summary>(Body 18 r4) The sprint law (rig_helpers.json "panels" "sprint"): the lead's held peak past Amp and held
    /// swing past Range (each held, easing back Decay deg/s) blend the law to these numbers: the upper turns Amount a
    /// degree (lying on the thigh down its descent), falls with no hang (FallTau, FallRate) and the fold is critically
    /// damped (Hz, Zeta).</summary>
    public readonly record struct SprintLaw(double AmpFrom, double AmpTo, double RangeFrom, double RangeTo, double Decay,
        double Amount, double FallTau, double FallRate, double Hz, double Zeta);

    /// <summary>The sprint gate's held peak and trough of the lead, frame to frame.</summary>
    public sealed class SprintState
    {
        public bool Started;
        public double Hi, Lo;
    }

    /// <summary>The leading thigh's swing (the smooth max Turn reads).</summary>
    public static double Lead(in Law law, double fl, double fr) => SmoothMax(fl, fr, law.Soft) - law.Soft / 4;

    /// <summary>How much of a sprint the law is in (0..1) from the lead this frame, <paramref name="dt"/> seconds on:
    /// its peak and trough held, each easing back toward the lead Decay deg/s; smoothstep of the held peak over Amp
    /// times smoothstep of the held swing (peak - trough) over Range (a seat or a held pose never counts, nor a run).
    /// helpers.py panel_sprint, number for number.</summary>
    public static double Sprint(in SprintLaw s, SprintState st, double lead, double dt)
    {
        if (!st.Started) { st.Started = true; st.Hi = st.Lo = lead; }
        else
        {
            st.Hi = Math.Max(lead, st.Hi - s.Decay * dt);
            st.Lo = Math.Min(lead, st.Lo + s.Decay * dt);
        }
        return Smooth((st.Hi - s.AmpFrom) / (s.AmpTo - s.AmpFrom)) * Smooth((st.Hi - st.Lo - s.RangeFrom) / (s.RangeTo - s.RangeFrom));
    }

    /// <summary>The law <paramref name="g"/> of the way to the sprint's numbers. helpers.py sprint_blend.</summary>
    public static Law Blend(in Law law, in SprintLaw s, double g) => g <= 0 ? law : law with
    {
        Amount = law.Amount + (s.Amount - law.Amount) * g,
        FallTau = law.FallTau + (s.FallTau - law.FallTau) * g,
        FallRate = law.FallRate + (s.FallRate - law.FallRate) * g,
    };

    /// <summary>The fold <paramref name="g"/> of the way to the sprint's spring (Hz, Zeta).</summary>
    public static FoldLaw Blend(in FoldLaw f, in SprintLaw s, double g) => g <= 0 ? f : f with
    {
        Hz = f.Hz + (s.Hz - f.Hz) * g,
        Zeta = f.Zeta + (s.Zeta - f.Zeta) * g,
    };

    /// <summary>The panel's side shapes' weights (left, right): each thigh's forward swing, smoothstep over
    /// [<paramref name="from"/>, <paramref name="to"/>] degrees (rig_helpers.json "fold" "side"). helpers.py side_weights.</summary>
    public static (double L, double R) SideWeights(double fl, double fr, double from, double to) =>
        (Smooth((fl - from) / (to - from)), Smooth((fr - from) / (to - from)));

    /// <summary>The turn this frame (degrees) from last frame's (<paramref name="prev"/>,
    /// NaN at the first) and the law's (<paramref name="target"/>), <paramref name="dt"/>
    /// seconds on: up with the law at once, down as a loose flap falls, a
    /// first-order lag of FallTau seconds toward the law, never faster than
    /// FallRate degrees a second and never below the law (so never into the
    /// thigh). helpers.py panel_fall, number for number.</summary>
    public static double Fall(in Law law, double prev, double target, double dt)
    {
        if (double.IsNaN(prev) || target >= prev) return target;
        if (dt <= 0) return prev;
        double y = target + (prev - target) * Math.Exp(-dt / law.FallTau);
        return Math.Max(target, Math.Max(y, prev - law.FallRate * dt));
    }

    /// <summary>The lower half's fold (rig_helpers.json "panels" "fold"): three blend shapes on the panel's
    /// mesh turning its points below the hinge forward by Step (a), a further Step (b) and back by Neg (n).</summary>
    public readonly record struct FoldLaw(double Step, double Neg, double Hz, double Zeta, double Rest, double C1, double C0, int Substeps);

    /// <summary>The fold's state from frame to frame: the lower half's angle from plumb, its speed, last frame's contact.</summary>
    public sealed class FoldState
    {
        public bool Started;
        public double Lam, V, Push;
    }

    /// <summary>The lower half's fold this frame (degrees past the upper's turn <paramref name="th"/>, + forward)
    /// from the law's turn (<paramref name="turn"/>, before its fall; <paramref name="amount"/> the law's amount),
    /// <paramref name="dt"/> seconds on: a damped pendulum hanging toward Rest, never below C1 x the lead - C0
    /// (lying on the leading thigh, lifted with it), at most two steps forward and Neg back.
    /// helpers.py panel_fold, number for number.</summary>
    public static double Fold(in FoldLaw f, FoldState st, double turn, double amount, double th, double dt)
    {
        double push = f.C1 * (amount != 0 ? turn / amount : 0) - f.C0;
        if (!st.Started)
        {
            st.Started = true; st.Lam = Math.Max(push, f.Rest); st.V = 0; st.Push = push;
        }
        if (dt > 0)
        {
            // (substeps: at least Substeps, and enough that w h <= 1, so a stiff spring holds at a long frame)
            double w = 2 * Math.PI * f.Hz;
            int n = Math.Max(f.Substeps, (int)Math.Ceiling(w * dt));
            double h = dt / n, p0 = st.Push, rate = (push - p0) / dt;
            double lam = st.Lam, v = st.V;
            for (int s = 0; s < n; s++)
            {
                double ps = p0 + (push - p0) * (s + 1) / n;
                v += (w * w * (f.Rest - lam) - 2 * f.Zeta * w * v) * h;
                lam += v * h;
                if (lam < ps) { lam = ps; v = Math.Max(v, rate); }
            }
            st.Lam = lam; st.V = v; st.Push = push;
        }
        double beta = st.Lam - th;
        if (beta > 2 * f.Step) { beta = 2 * f.Step; st.Lam = th + beta; }
        return Math.Max(beta, -f.Neg);
    }

    /// <summary>The fold's three shapes' weights (a, b, n) for <paramref name="beta"/> degrees. helpers.py fold_weights.</summary>
    public static (double A, double B, double N) FoldWeights(in FoldLaw f, double beta)
        => beta >= 0
            ? (Math.Min(beta / f.Step, 1), Math.Min(Math.Max((beta - f.Step) / f.Step, 0), 1), 0)
            : (0, 0, Math.Min(-beta / f.Neg, 1));

    /// <summary>A thigh's line (its +Y in her rest axes carried with the
    /// pelvis: +Y up, +Z her front) against its rest line: (forward swing in
    /// her side plane, spread out to <paramref name="side"/>, +1 her left, -1
    /// her right), degrees.</summary>
    public static (double Swing, double Spread) SwingSpread(double x, double y, double z, double x0, double y0, double z0, int side)
    {
        static double Fwd(double y, double z) => Math.Atan2(z, -y) * 180 / Math.PI;
        static double Out(double x, int s) => Math.Asin(Math.Clamp(x * s, -1, 1)) * 180 / Math.PI;
        return (Fwd(y, z) - Fwd(y0, z0), Out(x, side) - Out(x0, side));
    }
}
