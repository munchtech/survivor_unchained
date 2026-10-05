using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The damage numbers, kept to what the eye can take in (the experience
/// director's rule, S-13): a target's hits within a beat sum into one number
/// that rises and grows as they land; at most eight new numbers a frame, the
/// biggest first and her crits always; one struck for a fifth of its life a
/// size bigger, a crit gold; none drawn over her. A crowd struck all at once
/// carpeted itself in numbers that hid both it and the blow.
/// </summary>
public partial class Hits
{
    /// <summary>How long a target's hits keep summing into one number.</summary>
    const double Beat = 0.25;
    const int NewPerFrame = 8;
    /// <summary>The nearest a number is drawn to her, in metres over the ground.</summary>
    const float ClearOfHer = 1.5f;

    struct Tallied
    {
        public int Target;
        public double Sum, Born;
        public bool Crit, Heavy;
        /// <summary>Damage over time's own colour (its school's); none for a blow.</summary>
        public Color? Tint;
    }

    struct Waiting
    {
        public int Target;
        public Vector3 At;
        public double Amount, MaxHp;
        public bool Crit;
        public Color? Tint;
    }

    readonly Tallied[] tallies = new Tallied[64];
    readonly int[] tallyOf = InitTallyOf();
    readonly Dictionary<int, int> labelOfTarget = new();
    readonly List<Waiting> waiting = new();
    double clock;

    static int[] InitTallyOf()
    {
        var a = new int[64];
        Array.Fill(a, int.MinValue);
        return a;
    }

    /// <summary>The label `i` is being reused: whatever target it was counting for lets it go.</summary>
    void Untally(int i)
    {
        if (i < tallyOf.Length && tallyOf[i] != int.MinValue)
        {
            if (labelOfTarget.TryGetValue(tallyOf[i], out int j) && j == i) labelOfTarget.Remove(tallyOf[i]);
            tallyOf[i] = int.MinValue;
        }
    }

    /// <summary>A hit on `target` for this frame's numbers (shown at Flush). Damage over
    /// time passes its school's colour as `dot`, and sums into a number of its own.</summary>
    public void Tally(int target, Vector3 at, double amount, double maxHp, bool crit, Color? dot = null)
    {
        if (dot != null) { target = ~target; crit = false; }
        // Still counting for this target: it sums, at once and whatever the budget.
        if (labelOfTarget.TryGetValue(target, out int i) && numbers[i].T < 1 && clock - tallies[i].Born < Beat)
        {
            ref var t = ref tallies[i];
            t.Sum += amount;
            t.Crit |= crit;
            t.Heavy |= maxHp > 0 && t.Sum > maxHp * 0.2;
            Restyle(i, t);
            // Kept up while it grows, and nudged so the eye sees it climb.
            var (l, _) = numbers[i];
            numbers[i] = (l, Mathf.Min(numbers[i].T, 0.25f));
            return;
        }
        // A second hit the same frame before it was shown sums with the first.
        for (int k = 0; k < waiting.Count; k++)
            if (waiting[k].Target == target)
            {
                var w = waiting[k];
                w.Amount += amount;
                w.Crit |= crit;
                waiting[k] = w;
                return;
            }
        waiting.Add(new Waiting { Target = target, At = at, Amount = amount, MaxHp = maxHp, Crit = crit, Tint = dot });
    }

    /// <summary>Show this frame's new numbers: her crits always, then the biggest, eight at most; `her` is where she stands.</summary>
    public void Flush(Vector3? her)
    {
        if (waiting.Count == 0) return;
        waiting.Sort((a, b) => a.Crit != b.Crit ? (a.Crit ? -1 : 1) : b.Amount.CompareTo(a.Amount));
        int shown = 0;
        foreach (var w in waiting)
        {
            if (shown >= NewPerFrame && !w.Crit) break;
            var at = w.At;
            if (her is { } h)
            {
                var off = new Vector3(at.X - h.X, 0, at.Z - h.Z);
                float d = off.Length();
                if (d < ClearOfHer)
                {
                    off = d > 0.05f ? off / d : new Vector3(-0.7f, 0, -0.7f);
                    at = new Vector3(h.X + off.X * ClearOfHer, at.Y, h.Z + off.Z * ClearOfHer);
                }
            }
            var t = new Tallied { Target = w.Target, Sum = w.Amount, Born = clock, Crit = w.Crit, Heavy = w.MaxHp > 0 && w.Amount > w.MaxHp * 0.2, Tint = w.Tint };
            int i = Show(at, "", Colors.White, 60);
            tallies[i] = t;
            tallyOf[i] = w.Target;
            labelOfTarget[w.Target] = i;
            Restyle(i, t);
            shown++;
        }
        waiting.Clear();
    }

    /// <summary>A tallied number's text, colour and size from what it holds.</summary>
    void Restyle(int i, in Tallied t)
    {
        var l = numbers[i].Label;
        int n = (int)Math.Round(t.Sum);
        l.Text = t.Crit ? $"{n}!" : n.ToString();
        l.Modulate = t.Tint ?? (t.Crit ? new Color(1.6f, 1.15f, 0.4f) : new Color(1, 0.94f, 0.86f));
        // What burns or bleeds a body is told smaller than the blows themselves.
        l.FontSize = t.Tint != null ? 44 : (t.Crit ? 80 : 58) + (t.Heavy ? 18 : 0);
    }

    void StepTally(double dt) => clock += dt;
}
