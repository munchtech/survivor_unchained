using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Sim;

/// <summary>(M3 MR 3) What the hands did with the grip (the campaign's held swing: a hold record, or a spin union's other
/// half on its second key), one step at a time, after the battle's tick: the holds, how long each lasted, the share of
/// the time a foe stood in its reach that it was held, its cuts that landed, its damage and the Resolve its blows built.
/// Read-only on the fight. The harness's run line (RunMeter), the chain's tests and the game's trace read the same numbers.</summary>
public sealed class GripMeter
{
    /// <summary>Seconds stepped; of them with a foe in the grip's reach (and the plan's pad); held; held with a foe in reach.</summary>
    public double Seconds, InReach, Held, HeldInReach;
    /// <summary>Holds begun, and each finished hold's length (s).</summary>
    public int Holds;
    public readonly List<double> HoldLens = new();
    /// <summary>The grip's cuts told (Ev.Slash, Held), those that struck a foe, its damage and the Resolve landed blows built.</summary>
    public int Cuts, Blows;
    public double Damage, Fill;
    /// <summary>Gaps a chained grip's key was held into (a foe in its reach and the pad on the step before, none on this
    /// one, the key down on both; the gap lasts until a foe is in reach again, the key up or not), and the cuts that
    /// STARTED in such a gap (a live chain's StartAt moved: GripHoldTests (5)'s whiffed cuts, not `Struck == 0`).</summary>
    public int Gaps, Whiffs;
    /// <summary>(m3) Chains opened (a cut that is the first of its chain); cuts dropped before their contact (a dash, a
    /// knockdown: SwingChain.Dropped, each once); the weights of the cuts that struck a foe (WeightOf: written
    /// blows landed; an unchained grip's are its Blows); and what a banked opening would have paid on top: for each
    /// opening cut min(1, rest / wait) - its weight, floored at 0 (rest: since this grip's cut before started, a whole 1
    /// for its first; wait: the unchained record's at that step, Firing.CooldownOf(b, grip) / grip.BlowWeight).</summary>
    public int Opens, Drops;
    /// <summary>The weight of a grip's cut in hand: a share of the written blow (BlowWeight, times a heavy's longer period;
    /// a block's answer a whole 1), as Firing.CastWeighed gives its cast; 1 unchained.</summary>
    /// (M3 MR 3 b1: the landed rule: what the cut earned from its grip's bank, SwingChain.Weight; an answer 1.)
    public static double WeightOf(WeaponInst g) => g.Chained && g.Chain is { } c ? c.Weight : 1;
    public double CutW, Bank;
    readonly Dictionary<string, double> dropAt = new();
    readonly List<WeaponInst> grips = new();
    bool wasNear, gap;
    readonly Dictionary<string, double> cutAt = new();
    bool was;
    double since, fillSeen, dmgSeen;
    readonly HashSet<string> ids = new();

    public void Step(Battle b, double dt, IReadOnlyList<CombatEvent> evs)
    {
        var p = b.Player;
        bool any = false, held = false, near = false, chained = false, started = false;
        double pad = PressPlan.Def.GripPad;
        grips.Clear();
        foreach (var w in b.Weapons)
        {
            WeaponInst? g = null; bool h = false;
            if (w.Hold) { g = w; h = w.Held; }
            else if (w.Behavior == Content.WeaponBehavior.Spin && w.Slot2 >= 0 && Firing.HalfOf(w) is { Hold: true } half)
            {
                // (the hands may hold the half's key, or press it every step: both are the key down)
                g = half; h = w.Held2 || b.Time - b.HalfPressAt <= dt + 1e-9;
            }
            if (g == null) continue;
            any = true; held |= h; ids.Add(g.Id); grips.Add(g);
            near |= b.NearestHostile(p.X, p.Z, (g.Num(s => s.Reach) ?? 2.6) + pad) != null;
            // (the chain is kept on the weapon that swings: a union's half carries its own, the union's record none)
            if (g.Chained)
            {
                chained = true;
                if (g.Chain is { } c)
                {
                    bool first = !cutAt.TryGetValue(g.Id, out var at);
                    if (c.Live && (first || at != c.StartAt))
                    {
                        cutAt[g.Id] = c.StartAt; started = true;
                        if (c.Cut == 0)
                        {
                            Opens++;
                            double wait = Firing.CooldownOf(b, g) / g.BlowWeight;
                            Bank += Math.Max(0, (first ? 1 : Math.Min(1, (c.StartAt - at) / wait)) - WeightOf(g));
                        }
                    }
                    if (c.Dropped && (!dropAt.TryGetValue(g.Id, out var dAt) || dAt != c.StartAt)) { dropAt[g.Id] = c.StartAt; Drops++; }
                }
            }
        }
        // (the fill and the damage are the battle's running sums: their steps are taken, a new fight's reset is not a loss)
        double fill = b.Resolve.LandedFill, dmg = 0;
        foreach (var id in ids) dmg += b.DamageBy.GetValueOrDefault(id);
        if (fill > fillSeen) Fill += fill - fillSeen;
        if (dmg > dmgSeen) Damage += dmg - dmgSeen;
        fillSeen = fill; dmgSeen = dmg;
        foreach (var ev in evs) if (ev is Ev.Slash { Held: true } s)
        {
            Cuts++;
            if (s.Struck <= 0) continue;
            Blows++;
            // (the cut's weight is its grip's cut in hand's: the slash names its grip by its art)
            CutW += (grips.Find(x => x.Art == s.Art) ?? (grips.Count == 1 ? grips[0] : null)) is { } by ? WeightOf(by) : 1;
        }
        if (!any || !p.Alive) held = false;
        // (the gap opens before its cut is counted: a cut that starts on the gap's first step is a whiff)
        if (near) gap = false;
        else if (chained && held && was && wasNear) { gap = true; Gaps++; }
        if (gap && started) Whiffs++;
        wasNear = near;
        Seconds += dt;
        if (near) InReach += dt;
        if (held) { Held += dt; if (near) HeldInReach += dt; }
        if (held && !was) { Holds++; since = b.Time - dt; }
        else if (!held && was) HoldLens.Add(b.Time - dt - since);
        was = held;
    }

    /// <summary>The median hold (s; a hold still on counts with what it has), NaN with none.</summary>
    public double MedianHold(double now = double.NaN)
    {
        var a = HoldLens.ToList();
        if (was && !double.IsNaN(now)) a.Add(now - since);
        if (a.Count == 0) return double.NaN;
        a.Sort();
        return a[a.Count / 2];
    }

    /// <summary>The run line's column: per minute and second of `fightSec` (the harness's fight clock), and per second held.</summary>
    public string Line(double fightSec, double now = double.NaN)
    {
        double min = Math.Max(1e-6, fightSec / 60), hs = Math.Max(1e-6, Held);
        return $"grip holds {Holds / min:0.0}/min med {MedianHold(now):0.00}s held {100 * HeldInReach / Math.Max(1e-6, InReach):0}%reach {100 * Held / Math.Max(1e-6, fightSec):0}%fight " +
               $"blows {Blows / min:0.0}/min gdmg {Damage / Math.Max(1e-6, fightSec):0.0}/s gfill {Fill / Math.Max(1e-6, fightSec):0.00}/s perheld {Blows / hs:0.00}b {Damage / hs:0.0}d {Fill / hs:0.00}f gaps {Gaps} whiff {Whiffs} opens {Opens} drop {Drops} cutw {CutW:0.00} bank {Bank:0.00} fmin {fightSec / 60:0.00}";
    }
}
