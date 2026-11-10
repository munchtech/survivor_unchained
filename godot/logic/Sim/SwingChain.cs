using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/* The held swing as a chain (M3 MR 3; campaign only; opt-in by a press record's "chain" block, PressDef.Chain).
 * The owner: "fluid animations like slashing back and forth instead of reset slash reset slash".
 *
 * A chained skill's cuts are one flowing chain, kept per weapon (WeaponInst.Chain):
 *   - with no live chain a press starts cut 0 at once; in a live chain the next cut starts when the last cut's period has
 *     run out (the skill's wait, Firing.CooldownOf: exactly the wait an unchained swing has), with the next index and
 *     the other side. Held without a break, the next cut starts on the instant the period ends, not on the step after
 *     it (the step's overshoot is carried), so a held chain never drifts off its interval;
 *   - the cut's clip fills its period: rate = the clip's length / the period (AttackAnim.Rate), so the blow lands at
 *     start + contact / rate and the cancel beat falls at start + cancel / rate (HerEvents.ChainBeats: the clip's written
 *     len, contact, cancel; the timing contract's where one is not written). Attack speed scales all three with the period;
 *   - a heavy cut (the skill's own count or the Hand's, as before) on its heavy clip takes a period longer by its clip's
 *     length over the cut's (54/42 by the contract);
 *   - the aim, reach and targets are the contact blow's as before (Sim/Contact.cs): the aim fixed at the cut's start;
 *   - a dash that starts before the contact drops the blow (no damage, no Resolve, no Ev.Slash); the cut still counts
 *     and its period still runs from its start;
 *   - no cut starts while she dashes, leaps or rushes (Battle.CutBarred). The key held through it, the chain stays live
 *     and goes on with the next index when it ends: no reset, no Ev.SwingRelease;
 *   - letting go never stops a cut that has started. Ev.SwingRelease is told at the later of the release and the cut's
 *     cancel beat, unless the grip is held again by then (once a cut). From that instant the chain lives `grace` seconds
 *     more: held (or pressed) again inside it, the chain goes on; past it, the next cut is cut 0 on the first side;
 *   - from its cancel beat a cut no longer limits her: the cast pose's walk and plant end there at the latest
 *     (Battle.CastPose), and her AttackAnim is kept until then.
 * A record with no chain block never comes here: its swings are Sim/Contact.cs's, bit for bit. */

/// <summary>A chained skill's live state (WeaponInst.Chain; Battle.Swing for the grip in hand): read-only outside the sim.</summary>
public sealed class SwingChain
{
    /// <summary>A chain is live: cuts were thrown and the grace after a release has not run out.</summary>
    public bool Live { get; internal set; }
    /// <summary>The current (or last) cut: its 0-based index in the chain, its side (-1 on even cuts, +1 on odd, or the
    /// clip's written side), whether it is a heavy, and its clip (null: the record names none).</summary>
    public int Cut { get; internal set; }
    public int Side { get; internal set; }
    public bool Heavy { get; internal set; }
    public string? Clip { get; internal set; }
    /// <summary>The cut's clock (the battle's time): its start, its blow, its cancel beat, and when the next may start.</summary>
    public double StartAt { get; internal set; }
    public double ContactAt { get; internal set; }
    public double CancelAt { get; internal set; }
    public double PeriodEnd { get; internal set; }
    /// <summary>The clip's rate (its length over the period), and the heavy's period over the cut's (1 for a cut).</summary>
    public double Rate { get; internal set; } = 1;
    public double PeriodScale { get; internal set; } = 1;
    /// <summary>(M3 J12) The cut is a block's answer: one whole written blow (its weight 1, its wait the blow's: PeriodScale is
    /// 1 / the cut's share), on the cut's own clip at the cut's rate.</summary>
    public bool Whole { get; internal set; }
    /// <summary>The cut's blow has landed; or it was dropped (a dash before its contact, a knockdown).</summary>
    public bool Landed { get; internal set; }
    public bool Dropped { get; internal set; }
    /// <summary>The grip is held; else when it was let go, when Ev.SwingRelease is (or was) due, whether it was told, and
    /// until when the chain then lives.</summary>
    public bool Held { get; internal set; }
    public double ReleasedAt { get; internal set; } = double.NaN;
    public double ReleaseAt { get; internal set; } = double.NaN;
    public bool Released { get; internal set; }
    public double GraceUntil { get; internal set; } = double.NaN;
    /// <summary>The step its wait ran out on, and how far into that step (the next cut starts on the instant, not the step).</summary>
    internal double ReadyStep = double.NaN, Overshoot;
    /// <summary>Ev.SwingRelease was told for this cut (once a cut).</summary>
    internal bool Told;
    /// <summary>Its blow landed this step: the wait is set from PeriodEnd before the step counts it down (the landing ran first).</summary>
    internal bool Sync;
}

public sealed partial class Battle
{
    /// <summary>The skills that have thrown a chain's cut (stepped each tick; empty when no carried record is chained).</summary>
    readonly List<WeaponInst> chains = new(2);
    SwingChain? swing;

    /// <summary>The chain of the grip in hand (the last chained skill to start a cut), while it is live; else null. Its
    /// ContactAt and CancelAt are the current cut's beats (the Pilot's step, the views).</summary>
    public SwingChain? Swing => swing is { Live: true } ? swing : null;

    public const double ChainGrace = 0.40, ChainRecover = 18;

    /// <summary>Whether a chained skill's key is held: its own, or (Bladestorm's other half) its union's second key.</summary>
    bool ChainHeld(WeaponInst w)
    {
        foreach (var x in Weapons) if (ReferenceEquals(x.Half, w)) return x.Held2;
        return w.Held;
    }

    /// <summary>(M3 MR 3 job A) A chained skill's cut never STARTS while she dashes, leaps or rushes (Firing.Press and
    /// SwingHalf ask before anything is spent or posed). Its key may stay down through it: a held chain stays live
    /// (StepChains), nothing is released and no grace runs, and the cut after it is the next index. An unchained skill is
    /// never barred.</summary>
    internal bool CutBarred(WeaponInst w) => w.Chained && (Player.DashT > 0 || Player.Leap != null || Art.Rush != null);

    /// <summary>A chained skill's press (Battle.DeferBlow): the next cut of its chain starts; its blow is queued for the
    /// cut's contact beat. False: no aim or not her own cast, and it lands now, as an unchained press does.</summary>
    bool DeferCut(WeaponInst w, bool heavy, bool ownHeavy, double mul)
    {
        if (Refiring || FireFrom != null || CastAt == null || w.Press is not { } r) return false;
        if (w.Behavior is not (WeaponBehavior.Slash or WeaponBehavior.Crack)) return false;
        var c = w.Chain;
        if (c == null) { c = w.Chain = new SwingChain(); chains.Add(w); }
        else if (!chains.Contains(w)) chains.Add(w);
        bool go = c.Live;
        int cut = go ? c.Cut + 1 : 0;
        // The cut's clip and beats: the heavy's own clip when it has one, else the chain's clips in turn by the cut's index.
        string? light = r.Clip is { Length: > 0 } cs ? cs[cut % cs.Length] : null;
        bool heavyClip = r.ClipHeavy != null && (heavy || light == null);
        string? clip = heavyClip ? r.ClipHeavy : light;
        var beats = HerEvents.ChainBeats(clip, heavyClip || heavy && clip == null);
        double scale = heavy && (heavyClip && light != null || clip == null) ? beats.Len / HerEvents.ChainBeats(light, false).Len : 1;
        // (M3 J12c) sunderer.momentum: a cut of a written blow the blow before paid for takes (1 - sooner) on its period
        // (BlowN at a cut's start is its blow), so its rate, its beats and its wait all follow; the same factor again at
        // its contact (Firing.Rearm). 1 when not lit.
        double cd = Firing.CooldownOf(this, w) * Firing.MomentumMul(this, w, w.BlowN);
        double period = cd * scale;
        // (M3 J12) A block's answer (WeaponInst.AnswerDue, taken here: after the returns above, so a press that lands at
        // once does not eat it) is one whole blow: the wait after it is the blow's. Its clip keeps the cut's rate and
        // beats (period and rate below are the cut's), so only the wait takes the factor.
        bool whole = w.AnswerDue && w.BlowWeight != 1;
        w.AnswerDue = false;
        // (the chain's "answer", when written: that wait in place of the blow's, over the cut's period, so haste and the
        // other multipliers apply to it as they do to the written wait)
        double wait = !whole ? scale : r.Chain is { Answer: > 0 and var aw, Period: > 0 and var cp } ? aw / cp : 1 / w.BlowWeight;
        // Held on from the last cut, it starts on the instant the wait ran out (inside this step), not on the step.
        double start = go && c.ReadyStep == Time ? Time - c.Overshoot : Time;
        double rate = Math.Max(1e-3, beats.Len / period);
        c.Live = true; c.Cut = cut; c.Heavy = heavy; c.Clip = clip;
        // (sw2) the weapon's own count's rule (WeaponInst.NextSide: -1 first), so a hold's first cut swings the record's
        // first clip from the side the unchained first blow did, and alternates from there
        c.Side = (clip != null ? HerEvents.Side(clip) : null) ?? ((cut & 1) == 0 ? -1 : 1);
        c.StartAt = start; c.Rate = rate; c.PeriodScale = wait; c.Whole = whole;
        c.ContactAt = start + beats.Contact / rate; c.CancelAt = start + beats.Cancel / rate; c.PeriodEnd = start + cd * wait;
        c.Landed = c.Dropped = c.Told = false;
        c.Held = ChainHeld(w);
        c.Released = false; c.GraceUntil = double.NaN;
        (c.ReleasedAt, c.ReleaseAt) = c.Held ? (double.NaN, double.NaN) : (start, c.CancelAt);
        swing = c;

        var aim = CastAt.Value;
        var p = Player;
        double dx = aim.X - p.X, dz = aim.Z - p.Z;
        double a = dx * dx + dz * dz > 0.01 ? Math.Atan2(dz, dx) : Math.Atan2(Math.Cos(p.Facing), Math.Sin(p.Facing));
        w.WasOwnHeavy = ownHeavy;
        p.AttackAnim = new AttackAnim(w.Id, a, start, heavy || w.Behavior == WeaponBehavior.Crack, clip, rate, cut);
        w.ClipSide = c.Side;
        w.Timer = Math.Max(0, cd * wait - (Time - start));
        pendingBlows.Add(new PendingBlow { W = w, Due = c.ContactAt, At = start, Mul = mul, Aim = aim, Cut = true });
        return true;
    }

    /// <summary>Each step: every chain's release (Ev.SwingRelease at the later of the release and the cancel beat, unless
    /// held again by then) and its grace running out.</summary>
    void StepChains()
    {
        foreach (var w in chains)
        {
            if (w.Chain is not { Live: true } c) continue;
            if (ChainHeld(w)) { c.Held = true; c.Released = false; c.ReleasedAt = c.ReleaseAt = c.GraceUntil = double.NaN; continue; }
            if (c.Held || double.IsNaN(c.ReleasedAt)) { c.Held = false; c.Released = false; c.ReleasedAt = Time; c.ReleaseAt = Math.Max(Time, c.CancelAt); }
            if (!c.Released && Time >= c.ReleaseAt - 1e-9)
            {
                c.Released = true;
                c.GraceUntil = c.ReleaseAt + (w.Press?.Chain?.Grace ?? ChainGrace);
                if (!c.Told)
                {
                    c.Told = true;
                    Events.Emit(new Ev.SwingRelease { Weapon = w.Id, Slot = w.Slot, Cut = c.Cut, Side = c.Side, Time = c.ReleaseAt, Recover = (w.Press?.Chain?.Recover ?? ChainRecover) / 60 / c.Rate });
                }
            }
            if (c.Released && Time > c.GraceUntil + 1e-9) c.Live = false;
        }
    }

    /// <summary>A dash has started (Battle.Dash): every chain's cut not yet landed is dropped; its period runs on.</summary>
    void DropCuts()
    {
        for (int i = pendingBlows.Count - 1; i >= 0; i--)
        {
            var pb = pendingBlows[i];
            if (!pb.Cut) continue;
            pendingBlows.RemoveAt(i);
            pb.W.ClipSide = 0;
            if (pb.W.Chain is { } c) c.Dropped = true;
        }
    }

    /// <summary>Her swing's pose is a chain's cut still before its cancel beat (it is kept until then).</summary>
    bool CutHolds(AttackAnim a) => swing is { Live: true } c && c.StartAt == a.T && Time < c.CancelAt;
}

public static partial class Firing
{
    /// <summary>Before a chained skill's wait counts down a step: the step it runs out on is noted, and how far into it.</summary>
    internal static void ChainReady(Battle b, WeaponInst w, double dt)
    {
        if (w.Chain is not { } c) return;
        if (c.Sync) { c.Sync = false; w.Timer = Math.Max(0, c.PeriodEnd - (b.Time - dt)); }
        if (w.Timer > 0 && w.Timer <= dt) { c.ReadyStep = b.Time; c.Overshoot = dt - w.Timer; }
    }
}
