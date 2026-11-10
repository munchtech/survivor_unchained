using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The damage numbers, kept to what the eye can take in (the experience
/// director's rule, S-13): a target's hits within a beat sum into one number
/// that rises and grows as they land; at most four new numbers a frame and
/// twelve on screen, the biggest first and crits before them, none laid over
/// another still rising; one struck for a fifth of its life a size bigger
/// and told first, a crit gold; none drawn over her. A crowd struck all at
/// once carpeted itself in numbers that hid both it and the blow.
/// </summary>
public partial class Hits
{
    /// <summary>How long a target's hits keep summing into one number.</summary>
    const double Beat = 0.25;
    const int NewPerFrame = 4;
    /// <summary>The most numbers on screen at once (a big blow is told past it).</summary>
    const int LiveMost = 12;
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
            Reclear(i);
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

    /// <summary>Show this frame's new numbers, the weightiest first, `her` being where she
    /// stands. A crowd is told by a few: no more than LiveMost on screen at once and none laid
    /// over another still rising (summed per target, eight a frame, a packed crowd still wore a
    /// number on every body, overlapping into a carpet).</summary>
    public void Flush(Vector3? her)
    {
        if (waiting.Count == 0) return;
        // A blow that takes a fifth of what it struck is told first, then crits, then the biggest.
        waiting.Sort((a, b) => Heavy(a) != Heavy(b) ? (Heavy(a) ? -1 : 1) : a.Crit != b.Crit ? (a.Crit ? -1 : 1) : b.Amount.CompareTo(a.Amount));
        int live = 0;
        young.Clear();
        for (int k = 0; k < numbers.Count; k++)
        {
            if (numbers[k].T >= 1 || tallyOf[k] == int.MinValue) continue;
            live++;
            if (numbers[k].T < 0.6f) young.Add(numbers[k].Label.GlobalPosition);
        }
        int shown = 0;
        foreach (var w in waiting)
        {
            // No exceptions: in a crowd of the small dead nearly every blow takes a fifth of one.
            if (shown >= NewPerFrame || live >= LiveMost) break;
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
            if (Crowded(at)) continue;
            var t = new Tallied { Target = w.Target, Sum = w.Amount, Born = clock, Crit = w.Crit, Heavy = w.MaxHp > 0 && w.Amount > w.MaxHp * 0.2, Tint = w.Tint };
            int i = Show(Beside(at), "", Colors.White, 46);
            tallies[i] = t;
            tallyOf[i] = w.Target;
            labelOfTarget[w.Target] = i;
            Restyle(i, t);
            Reclear(i);
            shown++;
            live++;
            young.Add(numbers[i].Label.GlobalPosition);
        }
        waiting.Clear();
    }

    /// <summary>One big number past the caps (H7 r3: the Long Cut's line, told as one total at its far end once the band
    /// has crossed it, its victims past the twelve on screen): heavy, white-gold, a size over a heavy blow's. Its box is kept
    /// inside the screen's safe area (safe: the margin's share of each side; r3, it could land past the right edge).</summary>
    public void Total(Vector3 at, double amount, float safe = 0.05f)
    {
        int i = Show(at, "", Colors.White, 60);
        var t = new Tallied { Target = int.MinValue + 1, Sum = amount, Born = clock, Heavy = true };
        tallies[i] = t;
        tallyOf[i] = int.MinValue + 1;
        Restyle(i, t);
        var l = numbers[i].Label;
        l.FontSize = 96;
        // (white-gold in the UI's own colours: on the canvas nothing is over 1, and (1.25, 1.05, 0.7) clamped is a lemon)
        l.Modulate = TotalGold;
        numA[i] = 1;
        l.GlobalPosition = InSafe(l.GlobalPosition, l.Text, l.FontSize, safe);
    }

    /// <summary>A number's box moved inside the screen's safe area (safe: the margin's share of each side), at its depth.</summary>
    Vector3 InSafe(Vector3 at, string text, int size, float safe)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null || NumBox(cam, at, text, size) is not Rect2 b) return at;
        var vs = GetViewport().GetVisibleRect().Size;
        float mx = vs.X * safe, my = vs.Y * safe;
        var c = b.GetCenter();
        float x = Mathf.Clamp(c.X, mx + b.Size.X / 2, Mathf.Max(mx + b.Size.X / 2, vs.X - mx - b.Size.X / 2));
        float y = Mathf.Clamp(c.Y, Mathf.Max(my, SurvivorUnchained.Ui.GameHud.TopClear + 34) + b.Size.Y / 2, Mathf.Max(my + b.Size.Y / 2, vs.Y - my - b.Size.Y / 2));
        if (Mathf.IsEqualApprox(x, c.X) && Mathf.IsEqualApprox(y, c.Y)) return at;
        GD.Print($"hits: total '{text}' kept in the safe area: ({c.X:0},{c.Y:0}) -> ({x:0},{y:0}) of {vs.X:0}x{vs.Y:0}");
        float depth = (at - cam.GlobalPosition).Dot(-cam.GlobalBasis.Z);
        return AboveHud(cam.ProjectPosition(new Vector2(x, y), depth), text, size);
    }

    readonly List<Vector3> young = new();

    static bool Heavy(in Waiting w) => w.MaxHp > 0 && w.Amount > w.MaxHp * 0.2 && w.Tint == null;

    /// <summary>Whether a number at `at` would be laid over one still rising (on the ground's
    /// plane: the camera looks down, so nearness there is nearness on screen).</summary>
    bool Crowded(Vector3 at)
    {
        foreach (var y in young)
        {
            float dx = (at.X - y.X) / 1.2f, dz = (at.Z - y.Z) / 0.8f;
            if (dx * dx + dz * dz < 1) return true;
        }
        return false;
    }

    /// <summary>A tallied number's text, colour and size from what it holds.</summary>
    void Restyle(int i, in Tallied t)
    {
        var l = numbers[i].Label;
        int n = (int)Math.Round(t.Sum);
        l.Text = n.ToString();
        Color col = t.Tint ?? (t.Crit ? NumCrit : NumBone);
        numA[i] = col.A;
        l.Modulate = col;
        if (t.Crit && t.Tint == null) { numPunch[i] = 0; l.Scale = 1.35f; }
        // What burns or bleeds a body is told smaller than the blows themselves.
        l.FontSize = t.Tint != null ? 36 : (t.Crit ? 72 : 46) + (t.Heavy ? (t.Crit ? 12 : 12) : 0);
    }

    void StepTally(double dt) => clock += dt;
}
