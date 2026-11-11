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
    /// <summary>F1 lead 27: this frame's events held her step that felled 4+ (BattleFx, Ev.Kill Mass): its numbers fold
    /// into one at Flush (FeelRules.Fold); cleared there.</summary>
    public bool MassStep;
    /// <summary>Bodies felled this frame (set at Ev.Kill, cleared at Flush): a mass total sits over one.</summary>
    public readonly HashSet<int> FelledNow = new();
    /// <summary>F1 r6: this frame's felled, where they fell (chest height), and the launched ones' whole throw (m) and hop
    /// (m): a number keeps off every launched body's flight (FeelRules.NumberSpotLaunched).</summary>
    readonly Dictionary<int, (Vector3 At, Vector3 Throw, float Hop)> launchNow = new();
    readonly List<Vector3> felledAt = new();
    /// <summary>Per pool label: the drawn frame its kill window opened, clearing it off the kill (FeelRules.KillClear).</summary>
    const long NotClearing = long.MinValue;
    readonly long[] clearFrom = FillClear();
    static long[] FillClear() { var a = new long[48]; Array.Fill(a, NotClearing); return a; }

    /// <summary>A body felled this frame (Ev.Kill), at chest height; `throwBy`: a launch's whole throw on the ground
    /// (m), its hop `hop` (m); null when it is not thrown.</summary>
    public void Felled(int enemy, Vector3 at, Vector3? throwBy, float hop)
    {
        FelledNow.Add(enemy);
        felledAt.Add(at);
        if (throwBy is { } t) launchNow[enemy] = (at, t, hop);
    }
    /// <summary>F1 r5: the mass kill's one number and its drawn frame: the blows of the next FeelRules.MassTail frames
    /// (the rest of her step's kills, landing a frame or two late) are added into it, not shown as numbers of their own.</summary>
    int massLabel = -1;
    static readonly bool NumTrace = Args.Has("kill-trace");
    int ntCrowded, ntCapped;
    long massFrame = long.MinValue;
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
        // (F1 27: the targets folded into this label let go with it, so none points at a label reused for another)
        if (i < extraTargets.Length && extraTargets[i] is { } extra)
        {
            foreach (int x in extra)
                if (labelOfTarget.TryGetValue(x, out int j) && j == i) labelOfTarget.Remove(x);
            extra.Clear();
        }
    }

    /// <summary>Per label: the targets whose blows were folded into it (FeelRules.Fold), still summing into it.</summary>
    readonly List<int>?[] extraTargets = new List<int>?[64];

    /// <summary>A hit on `target` for this frame's numbers (shown at Flush). Damage over
    /// time passes its school's colour as `dot`, and sums into a number of its own.</summary>
    public void Tally(int target, Vector3 at, double amount, double maxHp, bool crit, Color? dot = null)
    {
        if (dot != null) { target = ~target; crit = false; }
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
        bool mass = MassStep;
        MassStep = false;
        long now = Engine.GetFramesDrawn();
        int waited = waiting.Count;
        void Out(int shownN, int label, double sum)
        {
            if (NumTrace && mass) GD.Print($"[mass-num] f={now} waiting={waited} shown={shownN} label={label} sum={(int)Math.Round(sum)}");
            FelledNow.Clear();
            launchNow.Clear();
            felledAt.Clear();
        }
        if (waiting.Count == 0) { Out(0, -1, 0); return; }
        if (massLabel >= 0 && FeelRules.MassTail(now - massFrame) && numbers[massLabel].T < 1 && tallyOf[massLabel] != int.MinValue)
        {
            var mt = tallies[massLabel];
            bool any = false;
            for (int k = waiting.Count - 1; k >= 0; k--)
            {
                var w = waiting[k];
                if (w.Tint != null) continue;
                mt.Sum += w.Amount;
                mt.Crit |= w.Crit;
                (extraTargets[massLabel] ??= new List<int>()).Add(w.Target);
                labelOfTarget[w.Target] = massLabel;
                waiting.RemoveAt(k);
                any = true;
            }
            if (any)
            {
                tallies[massLabel] = mt;
                Restyle(massLabel, mt);
                Reclear(massLabel);
                numbers[massLabel] = (numbers[massLabel].Label, Mathf.Min(numbers[massLabel].T, 0.25f));
                if (mass) massFrame = now;
            }
            if (waiting.Count == 0) { Out(0, massLabel, mt.Sum); return; }
        }
        // Still counting for a target: its blows sum into its label, at once and whatever the budget (a mass step's blows
        // are left out: they fold into the one total below).
        for (int k = waiting.Count - 1; k >= 0; k--)
        {
            var w = waiting[k];
            if (mass && w.Tint == null) continue;
            if (!(labelOfTarget.TryGetValue(w.Target, out int li) && numbers[li].T < 1 && clock - tallies[li].Born < Beat && clearFrom[li] == NotClearing)) continue;
            ref var t = ref tallies[li];
            t.Sum += w.Amount;
            t.Crit |= w.Crit;
            t.Heavy |= w.MaxHp > 0 && t.Sum > w.MaxHp * 0.2;
            Restyle(li, t);
            // (F1 r6: its own target thrown now: the number moves off the flight, as a new one would be placed)
            if (w.Tint == null && tallyOf[li] == w.Target && launchNow.ContainsKey(w.Target))
                numbers[li].Label.GlobalPosition = Spot(w.At, her, numbers[li].Label.Text, numbers[li].Label.FontSize, w.Target);
            Reclear(li);
            numbers[li] = (numbers[li].Label, Mathf.Min(numbers[li].T, 0.25f));
            waiting.RemoveAt(k);
        }
        if (waiting.Count == 0) { Out(0, -1, 0); return; }
        // A blow that takes a fifth of what it struck is told first, then crits, then the biggest.
        waiting.Sort((a, b) => Heavy(a) != Heavy(b) ? (Heavy(a) ? -1 : 1) : a.Crit != b.Crit ? (a.Crit ? -1 : 1) : b.Amount.CompareTo(a.Amount));
        // F1 27: the blows fold to at most NumbersPerStep numbers (one on a mass kill); damage over time is left as it is.
        if (mass)
        {
            // The total sits over a felled body: the weightiest blow on one goes first.
            for (int k = 0; k < waiting.Count; k++)
                if (waiting[k].Tint == null && FelledNow.Contains(waiting[k].Target))
                {
                    var pick = waiting[k];
                    waiting.RemoveAt(k);
                    waiting.Insert(0, pick);
                    break;
                }
        }
        var blowAt = new List<int>();
        var amounts = new List<double>();
        for (int k = 0; k < waiting.Count; k++)
            if (waiting[k].Tint == null) { blowAt.Add(k); amounts.Add(waiting[k].Amount); }
        var keptBlows = FeelRules.Fold(amounts, mass, out int[] foldedInto);
        var work = new List<(Waiting W, List<int>? Extra)>();
        for (int k = 0; k < waiting.Count; k++)
        {
            var w = waiting[k];
            if (w.Tint != null) { work.Add((w, null)); continue; }
            int bi = blowAt.IndexOf(k);
            if (foldedInto[bi] != bi) continue;
            // (shown: carries the sum, the crit and the targets of all that folded into it)
            List<int>? extra = null;
            for (int m = 0; m < foldedInto.Length; m++)
            {
                if (m == bi || foldedInto[m] != bi) continue;
                var f = waiting[blowAt[m]];
                w.Crit |= f.Crit;
                (extra ??= new List<int>()).Add(f.Target);
            }
            foreach (var (idx, sum) in keptBlows) if (idx == bi) w.Amount = sum;
            work.Add((w, extra));
        }
        // F1 r6 (judge r5 m5c: "3783" and "928" stood over a new kill): her kill window opens: the numbers of earlier
        // steps near the kill clear off it (gone by N + 3), and the total is placed as if they were gone.
        if (mass && felledAt.Count > 0 && GetViewport()?.GetCamera3D() is { } kcam)
        {
            float kk = GetViewport().GetVisibleRect().Size.Y / 1080f, kx = 0, ky = 0;
            int kn = 0;
            foreach (var p in felledAt)
                if (!kcam.IsPositionBehind(p)) { var sp = kcam.UnprojectPosition(p); kx += sp.X; ky += sp.Y; kn++; }
            if (kn > 0)
            {
                kx /= kn; ky /= kn;
                int cleared = 0;
                for (int k = 0; k < numbers.Count; k++)
                {
                    var l = numbers[k].Label;
                    if (numbers[k].T >= 1 || !l.Visible || clearFrom[k] != NotClearing || kcam.IsPositionBehind(l.GlobalPosition)) continue;
                    var sp = kcam.UnprojectPosition(l.GlobalPosition);
                    if (!SurvivorUnchained.View.FeelRules.KillClears(sp.X, sp.Y, kx, ky, kk)) continue;
                    clearFrom[k] = now;
                    if (k == massLabel) massLabel = -1;
                    cleared++;
                }
                if (NumTrace) GD.Print($"[num-clear] f={now} kill=({kx:0},{ky:0}) felled={kn} cleared={cleared}");
            }
        }
        int live = 0;
        young.Clear();
        for (int k = 0; k < numbers.Count; k++)
        {
            if (numbers[k].T >= 1 || tallyOf[k] == int.MinValue || clearFrom[k] != NotClearing) continue;
            live++;
            if (numbers[k].T < 0.6f) young.Add(numbers[k].Label.GlobalPosition);
        }
        int shown = 0;
        ntCrowded = ntCapped = 0;
        foreach (var (w, extra) in work)
        {
            // No exceptions: in a crowd of the small dead nearly every blow takes a fifth of one.
            if (!(mass && w.Tint == null) && (shown >= NewPerFrame || live >= LiveMost)) { ntCapped = work.Count - shown; break; }
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
            bool blow = w.Tint == null;
            var spot = blow ? Spot(at, her, ((int)Math.Round(t.Sum)).ToString(), HitsPlace.NumberSize(t.Crit, t.Heavy), w.Target) : Beside(at);
            if (!(mass && blow) && Crowded(spot)) { ntCrowded++; continue; }
            int i = Show(spot, "", Colors.White, 46, blow);
            tallies[i] = t;
            tallyOf[i] = w.Target;
            labelOfTarget[w.Target] = i;
            if (extra != null)
            {
                // (Show's Untally cleared the label's old extras: these are this number's own)
                extraTargets[i] = extra;
                foreach (int x in extra) labelOfTarget[x] = i;
            }
            Restyle(i, t);
            Reclear(i);
            if (mass && blow && massFrame != now)
            {
                massLabel = i; massFrame = now;
                HideUnder(i);
            }
            shown++;
            live++;
            young.Add(numbers[i].Label.GlobalPosition);
        }
        if (NumTrace && (mass || blowAt.Count >= 3))
            GD.Print($"[num-trace] f={now} mass={(mass ? 1 : 0)} blows={blowAt.Count} kept={keptBlows.Count} work={work.Count} shown={shown} crowded={ntCrowded} capped={ntCapped} live={live} massLabel={massLabel}");
        double lastSum = massLabel >= 0 && mass ? tallies[massLabel].Sum : 0;
        waiting.Clear();
        Out(shown, mass ? massLabel : -1, lastSum);
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

    /// <summary>F1 27: where a blow number is born: over the victim's body, away from her, never across it
    /// (FeelRules.NumberSpot on the body's screen box, at the victim's depth). `at` is about chest height.</summary>
    Vector3 Spot(Vector3 at, Vector3? her, string text, int size, int target = int.MinValue)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null || cam.IsPositionBehind(at) || NumBox(cam, at, text, size) is not Rect2 nb) return Beside(at);
        float k = GetViewport().GetVisibleRect().Size.Y / 1080f;
        float herX = her is { } h && !cam.IsPositionBehind(h) ? cam.UnprojectPosition(h).X : float.MinValue;
        float depth = (at - cam.GlobalPosition).Dot(-cam.GlobalBasis.Z);
        // F1 r6 (judge r5 m4b: "432" lay across a body thrown in under it): a launched victim's number goes across its
        // throw and off every flight of this frame's launched, its own rise included
        if (launchNow.TryGetValue(target, out var ln) && FlightOf(cam, ln) is { } me)
        {
            var others = new List<FeelRules.Flight>();
            foreach (var (id, o) in launchNow)
                if (id != target && FlightOf(cam, o) is { } of) others.Add(of);
            float rise = cam.UnprojectPosition(ln.At).Y - cam.UnprojectPosition(ln.At + Vector3.Up * RiseByN12).Y;
            var (lx, ly) = FeelRules.NumberSpotLaunched(me, others, herX, nb.Size.X, nb.Size.Y, k, Mathf.Max(0, rise));
            depth = (ln.At - cam.GlobalPosition).Dot(-cam.GlobalBasis.Z);
            if (NumTrace) GD.Print($"[num-launch] f={Engine.GetFramesDrawn()} target={target} body=({me.X0:0},{me.Y0:0} {me.X1:0},{me.Y1:0}) throw=({me.Lx:0},{me.Ly:0}) others={others.Count} spot=({lx:0},{ly:0})");
            return cam.ProjectPosition(new Vector2(lx, ly), depth);
        }
        var (x0, y0, x1, y1) = BodyBox(cam, at);
        var (sx, sy) = FeelRules.NumberSpot(x0, y0, x1, y1, herX, nb.Size.X, nb.Size.Y, k);
        return cam.ProjectPosition(new Vector2(sx, sy), depth);
    }

    /// <summary>How far a number rises (m) over a kill's N..N+12 (Hits._Process: 1.4 m/s easing out over 0.75 s).</summary>
    const float RiseByN12 = 0.24f;

    /// <summary>A body's box on screen from its chest-height point: 0.6 m under to 0.5 m over, 0.55 m to each side.</summary>
    static (float X0, float Y0, float X1, float Y1) BodyBox(Camera3D cam, Vector3 at)
    {
        var side = cam.GlobalBasis.X * 0.55f;
        var feet = at - Vector3.Up * 0.6f;
        var top = at + Vector3.Up * 0.5f;
        var ps = new[] { cam.UnprojectPosition(feet - side), cam.UnprojectPosition(feet + side), cam.UnprojectPosition(top - side), cam.UnprojectPosition(top + side) };
        float x0 = ps[0].X, x1 = x0, y0 = ps[0].Y, y1 = y0;
        foreach (var p in ps) { x0 = Mathf.Min(x0, p.X); x1 = Mathf.Max(x1, p.X); y0 = Mathf.Min(y0, p.Y); y1 = Mathf.Max(y1, p.Y); }
        return (x0, y0, x1, y1);
    }

    /// <summary>A launched body's flight on screen: its box where it fell, its top raised by its hop, and its throw.</summary>
    static FeelRules.Flight? FlightOf(Camera3D cam, (Vector3 At, Vector3 Throw, float Hop) l)
    {
        if (cam.IsPositionBehind(l.At) || cam.IsPositionBehind(l.At + l.Throw)) return null;
        var (x0, y0, x1, y1) = BodyBox(cam, l.At);
        var a = cam.UnprojectPosition(l.At);
        var b = cam.UnprojectPosition(l.At + l.Throw);
        float hop = a.Y - cam.UnprojectPosition(l.At + Vector3.Up * l.Hop).Y;
        return new FeelRules.Flight(x0, y0 - Mathf.Max(0, hop), x1, y1, b.X - a.X, b.Y - a.Y);
    }

    /// <summary>F1 r6: a new kill's total hides at once any clearing number its box meets (they fade by N + 3, but never
    /// over the total).</summary>
    void HideUnder(int i)
    {
        var cam = GetViewport()?.GetCamera3D();
        var me = numbers[i].Label;
        if (cam == null || NumBox(cam, me.GlobalPosition, me.Text, me.FontSize) is not Rect2 mb) return;
        for (int j = 0; j < numbers.Count; j++)
        {
            var (o, t) = numbers[j];
            if (j == i || t >= 1 || clearFrom[j] == NotClearing || !o.Visible) continue;
            if (NumBox(cam, o.GlobalPosition, o.Text, o.FontSize) is Rect2 ob && ob.Grow(6).Intersects(mb))
            {
                o.Visible = false;
                numbers[j] = (o, 1);
                clearFrom[j] = NotClearing;
            }
        }
    }

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
        l.FontSize = t.Tint != null ? 36 : HitsPlace.NumberSize(t.Crit, t.Heavy);
    }

    void StepTally(double dt) => clock += dt;
}
