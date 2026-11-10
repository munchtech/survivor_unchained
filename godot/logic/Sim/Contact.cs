using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/* Her blows land on the clip's contact frame (M3, ONE_BUILD 5.14; campaign only). A pressed or held blow of a Slash or a
 * Crack whose press record names its clips (skills.json press "clip" / "clipHeavy") is not struck at the press: the
 * press spends, poses her (Ev.Cast), starts her clip (Player.AttackAnim with the clip and its rate) and fixes the aim;
 * the cast itself (its hits, Resolve's landed fill, the heavy counts, the lamps that count swings, its cooldown's rules)
 * runs on the step the clip's contact comes round (data/anim/her_events.json, by clip name, over the clip's rate).
 * A blow pending when she dies or is knocked down is dropped. The arena never defers: it stays as it was. */
public sealed partial class Battle
{
    /// <summary>A blow swung and not yet landed: the skill, when it lands, the aim fixed at the press, its damage
    /// scale (a kindled heave's), and when it was pressed (its cooldown runs from the press).</summary>
    internal struct PendingBlow
    {
        public WeaponInst W;
        public double Due, At, Mul;
        public (double X, double Z, Enemy? Foe)? Aim;
        /// <summary>A chain's cut (Sim/SwingChain.cs): a dash before its contact drops it.</summary>
        public bool Cut;
    }

    readonly List<PendingBlow> pendingBlows = new(4);
    /// <summary>A pending blow is landing (FireSlash / FireCrack leave her clip alone: it started at the press).</summary>
    internal bool Landing;
    /// <summary>Her swings' clips alternate swing to swing (the view's old count, now the sim's).</summary>
    int clipSwing;

    /// <summary>Blows swung and not yet landed (tests, the harness).</summary>
    public int PendingBlows => pendingBlows.Count;

    internal bool BlowPending(WeaponInst w)
    {
        foreach (var p in pendingBlows) if (ReferenceEquals(p.W, w)) return true;
        return false;
    }

    /// <summary>Drop every blow not yet landed (she died, or was knocked down).</summary>
    public void DropBlows()
    {
        foreach (var pb in pendingBlows) if (pb.Cut && pb.W.Chain is { } c) { c.Dropped = true; pb.W.ClipSide = 0; }
        pendingBlows.Clear();
    }

    /// <summary>Whether this press waits for its clip's contact: campaign, a Slash or Crack, an aim, and a clip with a
    /// contact for the blow it will be. Its clip, rate and delay out.</summary>
    bool ContactOf(WeaponInst w, bool heavy, out string clip, out double rate, out double delay)
    {
        clip = ""; rate = 1; delay = 0;
        if (!Campaign || Refiring || FireFrom != null || CastAt == null || w.Press is not { } r) return false;
        if (w.Behavior is not (WeaponBehavior.Slash or WeaponBehavior.Crack)) return false;
        string? c = heavy && r.ClipHeavy != null ? r.ClipHeavy : r.Clip is { Length: > 0 } cs ? cs[clipSwing % cs.Length] : r.ClipHeavy;
        if (c == null || HerEvents.Contact(c) is not double ct) return false;
        bool asHeavy = heavy && r.ClipHeavy != null || r.Clip is not { Length: > 0 };
        rate = Math.Max(0.1, asHeavy ? r.ClipHeavyRate ?? 1.5 : r.ClipRate ?? 1.6);
        clip = c;
        delay = ct / rate;
        return true;
    }

    /// <summary>The press of a blow that lands on its contact (Firing.Press, KindledPress, SwingHalf; CastAt is the
    /// press's aim): her clip starts now, the blow is queued. False: it lands now, as before (the caller casts it).</summary>
    internal bool DeferBlow(WeaponInst w, double mul = 1)
    {
        if (!Campaign) return false;
        // The blow it will be, read ahead of its cast (CastOnce decides it again on the contact, the same way).
        int own = Firing.HeavyEveryOf(this, w);
        // (Sim.Blows: inside Battle the bare name is its own list of enemy blows)
        // (M3 J12: a block's answer owed, the next firing is a whole blow: WeaponInst.NextW)
        // (M3 MR 3 o2: a chained cut that starts on a press carries the rest its grip had, Battle.RestOf: the counts are
        // asked at the LIGHT cut's rested weight, here and again at the contact, WeaponInst.CastAsk)
        double rest = w.AnswerDue ? 0 : RestOf(w);
        double ask = rest > 0 ? Sim.Blows.Rested(w.NextW, rest) : w.NextW;
        bool ownHeavy = Sim.Blows.Completes(w.OwnBlows, w.OwnPart, own, ask);
        bool heavy = ownHeavy || HandHeavyNext(w, ask);
        // (a chained record's cut: its own clock and clip beats, Sim/SwingChain.cs)
        if (w.Chained) return DeferCut(w, heavy, ownHeavy, mul, rest);
        if (!ContactOf(w, heavy, out var clip, out var rate, out var delay)) return false;
        var aim = CastAt!.Value;
        var p = Player;
        double dx = aim.X - p.X, dz = aim.Z - p.Z;
        double a = dx * dx + dz * dz > 0.01 ? Math.Atan2(dz, dx) : Math.Atan2(Math.Cos(p.Facing), Math.Sin(p.Facing));
        w.WasOwnHeavy = ownHeavy;
        p.AttackAnim = new AttackAnim(w.Id, a, Time, heavy || w.Behavior == WeaponBehavior.Crack, clip, rate);
        w.ClipSide = HerEvents.Side(clip) ?? 0;
        clipSwing++;
        // Ready again after its wait from the press (the contact's rules may shorten it: Firing.LandBlow).
        w.Timer = Firing.CooldownOf(this, w);
        pendingBlows.Add(new PendingBlow { W = w, Due = Time + delay, At = Time, Mul = mul, Aim = aim });
        return true;
    }

    /// <summary>Each step (Tick, the fight's top): the blows whose contact has come land, at the aim fixed at their press.</summary>
    void LandBlows()
    {
        if (!Player.Alive) { pendingBlows.Clear(); return; }
        for (int i = 0; i < pendingBlows.Count; i++)
        {
            var pb = pendingBlows[i];
            if (Time < pb.Due - 1e-9) continue;
            pendingBlows.RemoveAt(i--);
            var (aim0, fm) = (CastAt, pb.W.FireMul);
            CastAt = pb.Aim;
            pb.W.FireMul = fm * pb.Mul;
            Landing = true;
            try { Firing.LandBlow(this, pb.W, Time - pb.At, pb.Cut); }
            finally { CastAt = aim0; pb.W.FireMul = fm; Landing = false; }
        }
    }
}

public static partial class Firing
{
    /// <summary>A pending blow's contact (Battle.LandBlows): the cast its press held back, then its wait's rules (momentum,
    /// the cleaver's next cut) as a press would have set them, less the time since the press.</summary>
    internal static void LandBlow(Battle b, WeaponInst w, double since, bool cut = false)
    {
        int kills0 = w.Kills, key0 = w.BlowN;
        var c = cut ? w.Chain : null;
        // (a chain's heavy cut is a longer share of the blow: its weight grows with its period)
        // (M3 J12: a block's answer is a whole blow: PeriodScale is 1 / BlowWeight, and the heavy counts ask at weight 1)
        bool fired;
        // (M3 MR 3 o2: a cut that started on a press carries its rest: its weight is its share plus the rest, the heavy
        // counts ask at the light cut's rested weight. Not through PeriodScale: that is the WAIT's factor.)
        w.WholeCast = c?.Whole ?? false;
        w.CastRest = c?.Rest ?? 0;
        try { fired = CastOnce(b, w, c?.PeriodScale ?? 1); }
        finally { w.WholeCast = false; w.CastRest = 0; }
        w.ClipSide = 0;
        if (c != null) c.Landed = true;
        if (!fired) return;
        Rearm(b, w, true, kills0, key0);
        // (a chain's heavy cut waits its own longer period)
        if (c != null) w.Timer *= c.PeriodScale;
        w.Timer = Math.Max(0, w.Timer - since);
        // (M3 J12: a block while this cut was pending: the answer is next, from this cut's cancel beat)
        if (c != null && w.AnswerDue) w.Timer = 0;
        // (a chain's next cut never starts before this one's cancel beat, whatever shortened its wait)
        if (c != null) { w.Timer = Math.Max(w.Timer, c.CancelAt - b.Time); c.PeriodEnd = b.Time + w.Timer; c.Sync = true; }
    }
}
