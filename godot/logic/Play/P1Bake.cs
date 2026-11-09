using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>
/// The clip bridge's pure part (tools/body/bake_clips.sh; the Godot runner tools_scenes/P1BakeRun.cs): one frame of
/// A's posed skeleton (heroine.glb playing a clip under HerPose alone) taken onto B's own skeleton as local poses B
/// plays natively. The rules, each derived:
///  - the map is P1Retarget's (global, rest-relative, by name and by role);
///  - the girdle: A's final clavicle line is B's (world direction, the rests differ: A's shoulder sits 41 mm under its
///    clavicle head, B's 14 mm, so a turn from rest left B's shoulders high under her neck), reached after B's girdle law:
///    the clavicle is keyed so that P1Rig.ClavicleTurn laid on it at runtime lands on A's line (the law stays for what
///    clips don't author, nothing doubles); scap_{l,r} stand at B's rest local and turn by the law alone. The upper arm
///    keeps its mapped world turn (its head rides the clavicle), all below follow by their locals;
///  - positions: B's rest offsets but for root and pelvis (P1Retarget's LegScale rule), keyed as position tracks (B's
///    trunk joints are A's, so A's pose carries them where A's are: P1Retarget's matched trunk);
///  - keys: a B bone is keyed only if its source A bone(s) are keyed in the clip (by name, or either chain bracket);
///    scap and B's helpers never (partial clips stay partial, the game's filtered blends behave as on A);
///  - the hand clean (tools/body/p1_clips.json) after the hold: per bone additive local turns, and a hold list.
/// Derivation: (a) the owner's rebuild ("B is the actor", 5 Nov) and the brief; (c) inherited: P1Retarget's map.
/// </summary>
public sealed class P1Bake
{
    public readonly P1Rig B;
    public readonly P1Retarget Map;
    readonly int[] order;
    readonly P1M4[] restLocal;
    public readonly HashSet<int> Girdle = new();
    readonly int[] uppers;
    public readonly int Pelvis, Root;

    public P1Bake(P1Rig b, P1Retarget map)
    {
        B = b; Map = map;
        int n = b.Names.Length;
        var o = new List<int>(); var seen = new bool[n];
        void Visit(int j) { if (seen[j]) return; if (b.Parent[j] >= 0) Visit(b.Parent[j]); seen[j] = true; o.Add(j); }
        for (int j = 0; j < n; j++) Visit(j);
        order = o.ToArray();
        restLocal = Enumerable.Range(0, n).Select(j => b.Parent[j] < 0 ? b.Rest[j] : b.Rest[b.Parent[j]].Inverse() * b.Rest[j]).ToArray();
        foreach (var s in new[] { "l", "r" })
            foreach (var g in new[] { "clavicle_", "scap_" })
                if (b.Index.TryGetValue(g + s, out int j)) Girdle.Add(j);
        uppers = new[] { "upperarm_l", "upperarm_r" }.Where(b.Index.ContainsKey).Select(x => b.Index[x]).ToArray();
        Pelvis = b.Index["pelvis"]; Root = b.Index.GetValueOrDefault("root", -1);
    }

    /// <summary>B's rest local of bone j (relative to its parent).</summary>
    public P1M4 RestLocal(int j) => restLocal[j];

    /// <summary>One frame: A's posed globals (skeleton space) to B's locals and globals, girdle held, the clean applied.
    /// aKeyed: the A bones the clip keys (the map lands a chain segment only when all it reads are keyed; null: all).</summary>
    public (P1M4[] Local, P1M4[] G) Frame(P1M4[] aPose, Clean? clean = null, ICollection<int>? aKeyed = null) => Hold(Map.Map(aPose, aKeyed), clean, aPose);

    /// <summary>The girdle and the clean on mapped B globals. aPose: A's final pose, its clavicle lines B's (null: the
    /// clavicles held at B's rest).</summary>
    public (P1M4[] Local, P1M4[] G) Hold(P1M4[] mapped, Clean? clean = null, P1M4[]? aPose = null)
    {
        int n = B.Names.Length;
        var L = new P1M4[n];
        for (int j = 0; j < n; j++)
        {
            int p = B.Parent[j];
            L[j] = p < 0 ? mapped[j] : mapped[p].Inverse() * mapped[j];
            // (only root and pelvis move from B's own offsets)
            if (j != Pelvis && j != Root) L[j] = L[j].WithT(restLocal[j].T());
        }
        // the scapulae at B's rest local (B's law turns them); the clavicle as mapped (P1 R1 arm chain: the plain map with
        // align, B's clavicle head and shoulder being A's, so its line is A's line; before, A's final line was laid from B's
        // neutral by the least turn, the shrug baked in)
        foreach (int j in Girdle) if (Side(j) == null) L[j] = restLocal[j];
        var G = new P1M4[n];
        foreach (int j in order)
        {
            int p = B.Parent[j];
            if (aPose != null && p >= 0 && !B.ClavicleRollNeutral && Side(j) is string cs)
            {
                // the mapped clavicle's line (A's) from B's neutral by the least turn, so B's clavicle keeps its own roll:
                // A's clavicle roll laid on B's clavicle (whose skin is B's upper chest and trapezius) moved B's breasts
                // 10 mm p95 off A's at the Look (round 25 trial: 4.3 -> 10.3). Not on a rig whose girdle lays that roll
                // at runtime (P1Rig.ClavicleRollNeutral, round 27): there the clip keys A's clavicle as mapped, so the
                // game's local blends of clavicle and upper arm run as A's (baked here, the fights' upper arms ran 1-3 deg
                // off A's through blends: round 26)
                var neutral = G[p] * restLocal[j];
                var line = neutral.Lin() * restLocal[B.Index["upperarm_" + cs]].T();
                var want = mapped[B.Index["upperarm_" + cs]].T() - mapped[j].T();
                L[j] = G[p].Inverse() * P1M4.From(Arc(line, want) * P1Retarget.Rot(neutral), neutral.T());
            }
            if (Array.IndexOf(uppers, j) >= 0 && p >= 0)
            {
                // the upper arm's mapped world turn kept, its head where the held parent carries it
                var head = Compose(G[p], restLocal[j]).T();
                G[j] = P1M4.From(P1Retarget.Rot(mapped[j]), head);
                L[j] = G[p].Inverse() * G[j];
            }
            if (clean != null)
            {
                if (clean.Hold.Contains(B.Names[j])) L[j] = restLocal[j];
                if (clean.Turns.TryGetValue(B.Names[j], out var deg))
                    L[j] = L[j] * P1M4.From(P1Rig.Expm(new P1V(deg.X, deg.Y, deg.Z) * (Math.PI / 180)), new P1V(0, 0, 0));
            }
            G[j] = Compose(p < 0 ? null : G[p], L[j]);
        }
        if (aPose != null)
            foreach (var s in new[] { "l", "r" })
            {
                // Keyed under the law: at runtime P1Rig.Girdle lays Rc on this and lands on A's line, the upper arm's world turn kept.
                if (!B.Index.TryGetValue("clavicle_" + s, out int c) || !B.Index.TryGetValue("upperarm_" + s, out int u) || B.ClavicleTurn(G, s) is not P1M3 rc) continue;
                var keyed = P1M4.From(rc.T() * P1Retarget.Rot(G[c]), G[c].T());
                var arm = P1Retarget.Rot(G[u]);
                L[c] = G[B.Parent[c]].Inverse() * keyed;
                L[u] = keyed.Inverse() * P1M4.From(arm, keyed * restLocal[u].T());
                Recompose(L, G, c);
            }
        return (L, G);
    }

    string? Side(int j)
    {
        var n = B.Names[j];
        return n == "clavicle_l" ? "l" : n == "clavicle_r" ? "r" : null;
    }

    static P1M4 Compose(P1M4? parent, P1M4 local) => parent == null ? local : parent * local;

    /// <summary>The foot lock's contact rule: a foot is planted where A's ball is within this of A's lowest ball in the clip, m.</summary>
    public const double ContactBand = 0.02;
    /// <summary>A window counts only if A's own ball holds in it (belt out) within this, m: A's clip really planted there.</summary>
    public const double SourceHold = 0.01;
    /// <summary>A belt under this (m/s) is a standing clip's noise: the ground held still.</summary>
    public const double StillBelt = 0.05;
    /// <summary>Frames the lock's correction eases out over on each side of a window.</summary>
    public const int LockEase = 3;

    /// <summary>The lock's ease weight at step e (1..ease) of an ease frames fade: quintic smootherstep of 1 - e/(ease+1).</summary>
    public static double EaseWeight(int e, int ease)
    {
        double t = 1 - e / (ease + 1.0);
        return t * t * t * (t * (6 * t - 15) + 10);
    }

    /// <summary>The foot lock (every clip that keys a leg): B's legs are not A's (B's run stride swept 729 mm in
    /// contact against A's 692, the planted ball drifting 45 mm against A's 22, belt out), so in A's contact windows
    /// (ball within ContactBand of its clip floor, A's own hold under SourceHold) B's ball is pinned horizontally to its
    /// least-squares anchor riding the belt (A's median planted velocity: the in-place cycle's ground speed), by
    /// two-bone IK on thigh and calf (the knee bends in its own plane, the foot keeps its world turn), the correction
    /// eased out over `ease` frames (default LockEase) either side with a quintic smootherstep weight (C2: no velocity or acceleration step at either end). Heights stay the clip's. For cycles frame n-1 is frame 0 (windows wrap).
    /// L and G are B's locals and globals per frame (changed in place); aBall/aFoot[side][frame] A's ball and foot heads.
    /// Returns per side the windows locked.</summary>
    public int[] FootLock(IList<P1M4[]> L, IList<P1M4[]> G, IList<P1V>[] aBall, IList<P1V>[] aFoot, bool loop, double fps, ISet<int>? keyed = null, int ease = LockEase)
    {
        int n = L.Count, m = loop && n > 2 ? n - 1 : n;
        var sides = new[] { "l", "r" };
        var locked = new int[2];
        if (n < 3) return locked;
        double floor = aBall.Min(b => b.Take(m).Min(p => p.Y));
        // the belt: A's median planted velocity
        var vel = new List<P1V>();
        var planted = aBall.Select(b => Enumerable.Range(0, m).Select(f => b[f].Y < floor + ContactBand).ToArray()).ToArray();
        for (int s = 0; s < 2; s++)
            for (int f = 0; f + 1 < m || loop && f < m; f++)
            {
                int g = (f + 1) % m;
                if (planted[s][f] && planted[s][g]) vel.Add((aBall[s][g] - aBall[s][f]) * fps);
            }
        double Med(Func<P1V, double> c) { var v = vel.Select(c).OrderBy(x => x).ToArray(); return v.Length == 0 ? 0 : v[v.Length / 2]; }
        var belt = new P1V(Med(v => v.X), 0, Med(v => v.Z));
        if (belt.Len() < StillBelt) belt = new P1V(0, 0, 0);   // (a standing clip: the ground does not move)
        for (int s = 0; s < 2; s++)
        {
            if (!B.Index.TryGetValue("thigh_" + sides[s], out int th) || !B.Index.TryGetValue("calf_" + sides[s], out int ca)
                || !B.Index.TryGetValue("foot_" + sides[s], out int fo) || !B.Index.TryGetValue("ball_" + sides[s], out int ba)) continue;
            if (keyed != null && !(keyed.Contains(th) && keyed.Contains(ca) && keyed.Contains(fo))) continue;
            var c = planted[s];
            if (c.All(x => x) && belt.Len() > 0) continue;
            // windows as runs of planted frames (wrapping for cycles), start index and length
            var wins = new List<(int S, int Len)>();
            int start0 = 0;
            if (loop && c.All(x => x)) wins.Add((0, m));
            else
            {
                if (loop) { start0 = Array.IndexOf(c, false); }
                for (int k = 0; k < m; k++)
                {
                    int f = (start0 + k) % m;
                    if (!c[f] || k > 0 && c[(f - 1 + m) % m]) continue;
                    int len = 0;
                    while (len < m && c[(f + len) % m] && (loop || f + len < m)) len++;
                    wins.Add((f, len));
                }
            }
            var corr = new P1V?[m];
            var weight = new double[m];
            foreach (var win in wins)
            {
                var (ws, len) = win;
                if (len < 2) continue;
                int F(int k) => (ws + k) % m;
                // A's own hold in the window, by the ball or the ankle (whichever A plants: a heel-to-toe roll pivots the
                // ball), the window's ends trimmed while A's point leaves it (the lift-off still inside the band)
                int bestS = 0, bestLen = 0, bestPt = 0;
                for (int pt = 0; pt < 2; pt++)
                {
                    var src = pt == 0 ? aBall[s] : aFoot[s];
                    int s0 = 0, l0 = len;
                    double Hold(int a0, int n0) => Enumerable.Range(0, n0).Max(k => Flat(src[F(a0 + k)] - src[F(a0)] - belt * (k / fps)).Len());
                    while (l0 >= 2 && Hold(s0, l0) > SourceHold)
                    {
                        if (Hold(s0 + 1, l0 - 1) <= Hold(s0, l0 - 1)) s0++;
                        l0--;
                    }
                    if (l0 >= 2 && l0 > bestLen) { bestS = s0; bestLen = l0; bestPt = pt; }
                }
                if (bestLen < 2) continue;
                ws = F(bestS); len = bestLen;
                int pj = bestPt == 0 ? ba : fo;
                double mid = (len - 1) / 2.0;
                var anchor = new P1V(0, 0, 0);
                for (int k = 0; k < len; k++) anchor = anchor + Flat(G[F(k)][pj].T() - belt * ((k - mid) / fps));
                anchor = anchor / len;
                for (int k = 0; k < len; k++)
                {
                    corr[F(k)] = Flat(anchor + belt * ((k - mid) / fps) - G[F(k)][pj].T());
                    weight[F(k)] = 1;
                }
                for (int e = 1; e <= ease; e++)
                {
                    double w = EaseWeight(e, ease);
                    foreach (var (f, from) in new[] { (ws - e, F(0)), (ws + len - 1 + e, F(len - 1)) })
                    {
                        if (!loop && (f < 0 || f >= m)) continue;
                        int g = (f % m + m) % m;
                        if (weight[g] >= w) continue;
                        weight[g] = w; corr[g] = corr[from]! * w;
                    }
                }
                locked[s]++;
            }
            for (int f = 0; f < m; f++)
                if (corr[f] is P1V d && d.Len() > 1e-7) LegTo(L[f], G[f], th, ca, fo, G[f][fo].T() + d);
        }
        if (m < n) for (int j = 0; j < B.Names.Length; j++) { L[n - 1][j] = L[0][j]; G[n - 1][j] = G[0][j]; }
        return locked;
    }

    static P1V Flat(P1V v) => new(v.X, 0, v.Z);

    static P1M3 Arc(P1V a, P1V b)
    {
        a = a / a.Len(); b = b / b.Len();
        var v = P1V.Cross(a, b);
        double s = v.Len(), c = Math.Clamp(P1V.Dot(a, b), -1, 1);
        return s < 1e-12 ? P1M3.Id : P1Rig.Expm(v / s * Math.Atan2(s, c));
    }

    /// <summary>Two-bone IK: thigh and calf turned so the foot's head reaches target (clamped to the leg's reach), the
    /// knee bending about its own current axis, the foot keeping its world turn; L and G of the leg's subtree updated.</summary>
    public void LegTo(P1M4[] L, P1M4[] G, int th, int ca, int fo, P1V target)
    {
        var H = G[th].T(); var K = G[ca].T(); var Fp = G[fo].T();
        double a = (K - H).Len(), b = (Fp - K).Len();
        double d = Math.Clamp((target - H).Len(), Math.Abs(a - b) + 1e-4, a + b - 1e-4);
        var footRot = G[fo].Lin();
        var axis = P1V.Cross(K - H, Fp - K);
        if (axis.Len() < 1e-9) axis = G[th].Lin().Col(0);
        axis = axis / axis.Len();
        // the knee's interior angle for reach d
        double cur = Math.Acos(Math.Clamp(P1V.Dot(H - K, Fp - K) / (a * b), -1, 1));
        double want = Math.Acos(Math.Clamp((a * a + b * b - d * d) / (2 * a * b), -1, 1));
        var Rk = P1Rig.Expm(axis * (cur - want));
        var calfG = P1M4.From(Rk * G[ca].Lin(), K);
        var Fn = K + Rk * (Fp - K);
        var Rt = Arc(Fn - H, target - H);
        var thighG = P1M4.From(Rt * G[th].Lin(), H);
        calfG = P1M4.From(Rt * calfG.Lin(), H + Rt * (K - H));
        // each set as a world pose under its (possibly helper-carried) parent, the subtree recomposed after each
        L[th] = G[B.Parent[th]].Inverse() * thighG; Recompose(L, G, th);
        L[ca] = G[B.Parent[ca]].Inverse() * calfG; Recompose(L, G, ca);
        L[fo] = G[B.Parent[fo]].Inverse() * P1M4.From(footRot, G[fo].T()); Recompose(L, G, fo);
    }

    void Recompose(P1M4[] L, P1M4[] G, int top)
    {
        G[top] = B.Parent[top] < 0 ? L[top] : G[B.Parent[top]] * L[top];
        foreach (int j in order)
            if (B.Parent[j] >= 0 && IsUnder(j, top)) G[j] = G[B.Parent[j]] * L[j];
    }

    bool IsUnder(int j, int anc) { for (int k = B.Parent[j]; k >= 0; k = B.Parent[k]) if (k == anc) return true; return false; }

    /// <summary>The key rule: the B bones keyed in a clip whose keyed A bones are aKeyed.</summary>
    public HashSet<int> Keyed(ICollection<int> aKeyed)
    {
        var o = new HashSet<int>();
        for (int j = 0; j < B.Names.Length; j++)
        {
            if (Girdle.Contains(j) && Side(j) == null || B.Helpers.Contains(j)) continue;
            var (k, s0, s1) = Map.Source(j);
            if (k == 1 && aKeyed.Contains(s0) || k == 2 && (aKeyed.Contains(s0) || aKeyed.Contains(s1))) o.Add(j);
        }
        // the clavicle keyed with its arm (P1 pose round 1): Hold always sets it (A's final line under B's law: A's shrug
        // lifts it even where the clip leaves A's clavicle at rest), and the upper arm is keyed under it. A clip that keys
        // the arm and not the clavicle (her sword, dagger and axe blows) left B's clavicle at B's rest local in the game
        // (the deterministic blend's init: a track the shot lacks), not the bake's: the clavicle line 4-6 deg off A's, the
        // upper arm 3-4, the hands 25-48 mm off in fight_close's strikes.
        // (not on a shrug-driven rig, P1 R1 arm chain: there the clavicle is the map of A's, keyed where A keys it, and a
        // blow that leaves A's clavicle unkeyed leaves B's at its init as A's is; A's HerShrug lifts both at runtime)
        if (!B.ShrugDriven)
            foreach (var s in new[] { "l", "r" })
                if (B.Index.TryGetValue("upperarm_" + s, out int u) && o.Contains(u) && B.Index.TryGetValue("clavicle_" + s, out int c)) o.Add(c);
        return o;
    }

    /// <summary>Shoulder joint (upper arm head) height above the pelvis, minus the same at B's rest, m (per side l, r).</summary>
    public (double L, double R) ShoulderDrop(P1M4[] G)
    {
        double D(string s) => B.Index.TryGetValue("upperarm_" + s, out int u)
            ? (G[u][1, 3] - G[Pelvis][1, 3]) - (B.Rest[u][1, 3] - B.Rest[Pelvis][1, 3]) : double.NaN;
        return (D("l"), D("r"));
    }

    /// <summary>One clip's hand clean (tools/body/p1_clips.json): per B bone, an additive local turn (rotation vector,
    /// degrees, laid after the clip's local), and bones held at B's rest local.</summary>
    public sealed class Clean
    {
        public Dictionary<string, P1V> Turns = new();
        public HashSet<string> Hold = new();
        /// <summary>Per-clip foot-lock ease frames ("lock_ease"); null = LockEase.</summary>
        public int? LockEase;
    }

    /// <summary>p1_clips.json's "clips": { name: { "why": .., "turns": { bone: [x, y, z] }, "hold": [bones], "lock_ease": frames (optional) } }.</summary>
    public static Dictionary<string, Clean> ParseCleans(string json)
    {
        var o = new Dictionary<string, Clean>();
        using var d = JsonDocument.Parse(json);
        if (!d.RootElement.TryGetProperty("clips", out var clips)) return o;
        foreach (var c in clips.EnumerateObject())
        {
            var cl = new Clean();
            if (c.Value.TryGetProperty("turns", out var t))
                foreach (var b in t.EnumerateObject())
                {
                    var v = b.Value.EnumerateArray().Select(x => x.GetDouble()).ToArray();
                    cl.Turns[b.Name] = new P1V(v[0], v[1], v[2]);
                }
            if (c.Value.TryGetProperty("hold", out var h))
                foreach (var b in h.EnumerateArray()) cl.Hold.Add(b.GetString()!);
            if (c.Value.TryGetProperty("lock_ease", out var le)) cl.LockEase = le.GetInt32();
            o[c.Name] = cl;
        }
        return o;
    }
}
