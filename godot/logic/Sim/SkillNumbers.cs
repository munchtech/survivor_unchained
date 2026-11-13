using System;
using System.Runtime.CompilerServices;

namespace SurvivorUnchained.Sim;

public sealed partial class Battle
{
    /// <summary>(SU-070) What a skill card's numbers depend on, as one stamp: the fight itself, her stats, the lamps lit,
    /// and each carried skill's rank, slot, evolution, cast form and lit wick. Any build change moves it; a card cache keys
    /// on it (with the battle) so a ring equipped or a lamp lit never leaves an old number on a card.</summary>
    public long BuildStamp
    {
        get
        {
            var h = new HashCode();
            h.Add(RuntimeHelpers.GetHashCode(this));
            h.Add(Stats.Version);
            h.Add(RuntimeHelpers.GetHashCode(Lamps));
            h.Add(Lamps.Version);
            h.Add(Weapons.Count);
            // Flips that move a card's area: the reaver's Hand below half, the bound storm's reach once enough are bound.
            h.Add(ReaverHand && Player.Hp < MaxHp * HR.Below);
            h.Add(Lamp("bound.storm_reach") && boundTotal >= (int)Lamps.Full("bound.storm_reach", "at", 3));
            foreach (var w in Weapons)
            {
                h.Add(w.Id); h.Add(w.Rank); h.Add(w.Slot); h.Add(w.Slot2); h.Add(w.Evolution?.Id); h.Add(w.Cast); h.Add(w.Hold); h.Add(w.Pressed); h.Add(w.KindledNow);
                h.Add(w.Wick is { } k ? RuntimeHelpers.GetHashCode(k) : 0);
                h.Add(w.Wick?.Lit.Length ?? 0);
            }
            return h.ToHashCode();
        }
    }

    /* (SU-071) The numbers a skill uses when it fires, one named place each: the runtime calls these and the cards ask
     * SkillNumber, so a card never shows a number the fight doesn't use. */

    internal double LeapRangeOf(WeaponInst w) => RuleLeapRange(w, w.Num(s => s.Range) ?? 9);
    internal double LeapMinOf(WeaponInst w) => Math.Min(LeapRangeOf(w), w.Num(s => s.MinRange) ?? 3);
    internal double LeapRadiusOf(WeaponInst w) => Firing.AreaOf(this, w, WkOver(w, "heroic_leap.crater", "radius", w.Num(s => s.Radius) ?? 3.5));
    internal double LeapStunOf(WeaponInst w) => RuleLeapStun(w, w.Num(s => s.Stun) ?? 0.8);
    internal double ChargeRangeOf(WeaponInst w) => WkOver(w, "shield_charge.headlong", "range", w.Num(s => s.Range) ?? 8);
    internal double ChargeBarrierOf(WeaponInst w) => SkillRule(w, "iron_hide") ? SkillFull(w, "iron_hide", "barrier", 0.25) : w.Num(s => s.Barrier) ?? 0.15;
    internal double BraceSecondsOf(WeaponInst w) => Math.Max(0.05, WkOver(w, "iron_vow.steadfast", "brace", w.Num(s => s.Brace) ?? 2));
    internal double SpinRadiusOf(WeaponInst w) => Firing.AreaOf(this, w, RuleReach(w, w.Num(s => s.Radius) ?? 3.2));
    /// <summary>A swing's reach; still: add the standing-still bonus (the swing does, a card doesn't: it is not a number she holds).</summary>
    internal double SlashReachOf(WeaponInst w, bool still) =>
        Firing.AreaOf(this, w, RuleReach(w, w.Num(s => s.Reach) ?? 2.6)) * (still ? SkillStillReach(w) : 1) + Firing.ReachAdd(this, w);
    internal double NovaRadiusOf(WeaponInst w) => Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 3.5) + Firing.ReachAdd(this, w);
    internal double CrackRangeOf(WeaponInst w)
    {
        double range = w.Num(s => s.Range) ?? 10;
        return SkillRule(w, "fault_line") ? Math.Max(range, SkillFull(w, "fault_line", "reach", 14)) : range;
    }
    internal double CrackRadiusOf(WeaponInst w) => Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 2.5);
    internal double RebukeRadiusOf(WeaponInst w) => Firing.AreaOf(this, w, w.Num(s => s.Radius) ?? 5);
    internal int RebukeOthersOf(WeaponInst w) => (int)(w.Num(s => s.Others) ?? 5);
    internal double RebukeBlockOf(WeaponInst w) => (w.Num(s => s.Block) ?? 0.08) + (w.Num(s => s.BlockStep) ?? 0.01) * (w.Rank - 1);
    internal double BellShareOf(WeaponInst w) => SkillRule(w, "barrier") ? SkillFull(w, "barrier", "share", 0.015) : w.Num(s => s.Barrier) ?? 0.01;
    internal int BellDrawMostOf(WeaponInst w) => (int)(w.Num(s => s.DrawMost) ?? 5);
    internal double BellCapOf(WeaponInst w) => w.Num(s => s.BarrierCap) ?? 0.15;

    /// <summary>(SU-071) The number a skill card's {base.field} stands for: what this fight uses when w fires (its rank,
    /// evolution, lit wick and the lamps' rules all in), or null when the card has no faithful runtime number for it (the
    /// card then falls back to the written base). Fields are the skills.json base names, any case.</summary>
    public double? SkillNumber(WeaponInst w, string field)
    {
        string f = field.ToLowerInvariant();
        switch (w.Def.Id)
        {
            case "sunder":
                if (f == "reach") return SlashReachOf(w, false);
                if (f == "line") return w.Num(s => s.Line) is { } l ? Firing.AreaOf(this, w, l) : null;
                break;
            case "cleaver":
                if (f == "reach") return SlashReachOf(w, false);
                break;
            case "groundbreaker":
                if (f == "range") return CrackRangeOf(w);
                if (f == "radius") return CrackRadiusOf(w);
                if (f == "stun") return w.Num(s => s.Stun) ?? 0.6;
                break;
            case "heroic_leap":
                if (f == "minrange") return LeapMinOf(w);
                if (f == "range") return LeapRangeOf(w);
                if (f == "stun") return LeapStunOf(w);
                if (f == "radius") return LeapRadiusOf(w);
                break;
            case "shield_charge":
                if (f == "range") return ChargeRangeOf(w);
                if (f == "barrier") return ChargeBarrierOf(w);
                if (f == "duration") return w.Num(s => s.Duration) ?? 4;
                break;
            case "iron_vow":
                if (f == "brace") return BraceSecondsOf(w);
                if (f == "radius") return Firing.AreaOf(this, w, RuleVowRadius(w, w.Num(s => s.Radius) ?? 5)); // the held-time growth of unyielding is the burst's own
                break;
            case "watch_bell":
                if (f == "barrier") return BellShareOf(w);
                if (f == "drawmost") return BellDrawMostOf(w);
                if (f == "range") return BellReach(w);
                if (f == "barriercap") return BellCapOf(w);
                break;
            case "dawnpulse":
                if (f == "radius") return NovaRadiusOf(w);
                break;
            case "bladestorm":
                if (f == "radius") return SpinRadiusOf(w);
                if (f == "breakgrow") return w.Num(s => s.BreakGrow) ?? 1.6;
                break;
            case "rebuke":
                if (f == "others") return RebukeOthersOf(w);
                if (f == "radius") return RebukeRadiusOf(w);
                if (f == "block") return RebukeBlockOf(w);
                if (f == "cooldown") return Firing.CooldownOf(this, w);
                break;
        }
        return null;
    }
    /// <summary>(SU-071) A skill card's probe carries the card's own weapon: it joins the fight and its lit wick's rules join the lamps, so
    /// SkillNumber answers as the fight would. Only for a battle built to be asked (never a fight that is played).</summary>
    internal void CarryProbe(WeaponInst w) { if (!Weapons.Contains(w)) Weapons.Add(w); SyncWickRules(); }
}
