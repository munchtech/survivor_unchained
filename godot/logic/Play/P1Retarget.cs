using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Play;

/// <summary>
/// P1's body B posed from A's skeleton (the shipped heroine.glb, whose clips and layers drive her), by a global
/// match: each B bone takes A's global turn from A's rest (rest-relative, in skeleton space; A's Head's +7% rest
/// scale dropped by orthonormalising), laid on B's own rest; positions follow B's own bone lengths, but for the root
/// and pelvis, whose moves from rest are scaled by the legs' length (B's pelvis height over A's). The rules, each
/// derived:
///  - by name, where A has the bone and it plays the same part (every limb, finger, clavicle, scapula, breast);
///  - the spine-to-head chain by role, not name (A: spine_01..03, neck_01; B: spine_01..05, neck_01..02, so B's
///    spine_03 is not A's): a B bone takes A's turn at the same fraction of the chain's length (its segment's
///    midpoint, from the pelvis to the Head joint), slerped between the two A bones whose midpoints bracket it
///    (global turns vary smoothly up a spine; the chain's two ends, pelvis and Head, are matched exactly);
///  - B's own bones A lacks (the metacarpals, breast tips) ride their parent (carried at rest), and B's helper bones
///    (rig.json "helpers": twists, shares, points, muscles) are carried at rest for P1Rig.Drive to set by B's laws.
/// Derivation: (a) the gate's need (the brief: "global match, rest-relative, by name and by role"); (c) inherited:
/// the clips' own A skeleton. A is only read, never written.
/// </summary>
public sealed class P1Retarget
{
    enum Kind { Carried, Direct, Chain }

    readonly P1Rig b;
    readonly P1M4[] aRest;
    readonly P1M3[] aRestRot;
    readonly Kind[] kind;
    readonly int[] src0, src1;
    readonly double[] frac;
    readonly int[] order;
    readonly P1M4[] bLocal;
    readonly int aRoot, aPelvis, bRoot, bPelvis;
    readonly P1M3[] align;

    // (not the clavicle: its rest slope is each body's own anatomy, B's sternoclavicular-to-acromion line about 3 deg
    // down, A's game-rig convention 15 deg; standing B's clavicle in A's dropped B's shoulder joint 31 mm in every pose,
    // the arm rode it down while the neck and trapezius held: the dome over her shoulders at the Look and close-up
    // cameras. The clip's clavicle turns still apply, from B's own rest; the upper arm's own stand aims her arm as A's.)
    static bool Limb(string n) => new[] { "upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb", "thigh", "calf", "foot", "ball" }.Any(n.StartsWith);

    static P1M3 Arc(P1V a, P1V c)
    {
        var v = P1V.Cross(a, c);
        double s = v.Len(), co = Math.Clamp(P1V.Dot(a, c), -1, 1);
        return s < 1e-12 ? P1M3.Id : P1Rig.Expm(v / s * Math.Atan2(s, co));
    }
    /// <summary>The pelvis's moves from rest scaled by B's pelvis height over A's (the legs' length).</summary>
    public readonly double LegScale;
    /// <summary>For each A bone, the B bone that plays its part (by name, or the chain's bone at its midpoint); -1 none.</summary>
    public readonly int[] BFor;
    readonly string[] aNames;
    readonly int[] aParent, aChainB, bChainB;
    readonly Dictionary<string, int> aIndexB;

    public P1Retarget(string[] aNames, int[] aParent, P1M4[] aRest, P1Rig b)
    {
        this.b = b; this.aRest = aRest; this.aNames = aNames; this.aParent = aParent;
        aRestRot = aRest.Select(Rot).ToArray();
        int n = b.Names.Length;
        kind = new Kind[n]; src0 = new int[n]; src1 = new int[n]; frac = new double[n];
        var aIndex = new Dictionary<string, int>();
        for (int i = 0; i < aNames.Length; i++) aIndex[aNames[i]] = i;
        // parent-first order (Godot's bone order need not be)
        var o = new List<int>(); var seen = new bool[n];
        void Visit(int j) { if (seen[j]) return; if (b.Parent[j] >= 0) Visit(b.Parent[j]); seen[j] = true; o.Add(j); }
        for (int j = 0; j < n; j++) Visit(j);
        order = o.ToArray();
        bLocal = Enumerable.Range(0, n).Select(j => b.Parent[j] < 0 ? b.Rest[j] : b.Rest[b.Parent[j]].Inverse() * b.Rest[j]).ToArray();
        var aChain = Chain(aNames, aParent, aRest, aIndex);
        var bChain = Chain(b.Names, b.Parent, b.Rest, b.Index);
        aChainB = aChain; bChainB = bChain; aIndexB = aIndex;
        var aChainSet = new HashSet<int>(aChain);
        var aMid = Mids(aChain, aRest);
        var bMid = Mids(bChain, b.Rest);
        for (int j = 0; j < n; j++)
        {
            int ci = Array.IndexOf(bChain, j);
            if (ci > 0 && ci < bChain.Length - 1)
            {
                double t = bMid[ci];
                // bracketed over the whole chain, its ends too (the pelvis's midpoint low, the Head's at 1): B's bones below
                // A's spine_01 midpoint blend from A's pelvis (they took spine_01 whole: the pelvis's sway lost there, 5-6 deg)
                int k = 0;
                while (k < aChain.Length - 2 && aMid[k + 1] < t) k++;
                double lo = aMid[k], hi = aMid[k + 1];
                kind[j] = Kind.Chain; src0[j] = aChain[k]; src1[j] = aChain[k + 1];
                frac[j] = hi > lo ? Math.Clamp((t - lo) / (hi - lo), 0, 1) : 0;
            }
            else if (!b.Helpers.Contains(j) && aIndex.TryGetValue(b.Names[j], out int a)) { kind[j] = Kind.Direct; src0[j] = a; }
            else kind[j] = Kind.Carried;
        }
        // B's limbs (from the upper arm and the thigh down) stood in A's rest first: each limb bone's rest direction turned (the shortest turn, in the world)
        // onto its A bone's, so a clip's limb turns, relative to A's rest, start from A's rest limb. B's rest differs
        // there (her arms forward, hands 19 cm off A's; feet 11 cm forward); the torso, neck and head keep B's own
        // rest (built standing as A stands; the head is A's own, baked in place). A bone's direction: its head to the
        // mean of its A bone's children's heads (A's hierarchy, the names B has: through B's own metacarpals); a limb's
        // last bone takes its parent's turn.
        align = Enumerable.Range(0, n).Select(_ => P1M3.Id).ToArray();
        foreach (int j in order)
        {
            if (kind[j] != Kind.Direct || !Limb(b.Names[j])) continue;
            // the tips by A's own hierarchy (A's children of j's A bone that B has by name, off the spine-to-head chain), so
            // B's segment aims where A's does: B's upper arm at A's elbow, not at the mean with B's share and twist helpers
            int aj = src0[j];
            var tips = Enumerable.Range(0, aNames.Length).Where(k => aParent[k] == aj && !aChainSet.Contains(k)
                && b.Index.TryGetValue(aNames[k], out int bk) && kind[bk] == Kind.Direct).Select(k => b.Index[aNames[k]]).ToList();
            if (tips.Count == 0) { if (b.Parent[j] >= 0) align[j] = align[b.Parent[j]]; continue; }
            var tb = tips.Aggregate(new P1V(0, 0, 0), (acc, k) => acc + b.Rest[k].T()) / tips.Count;
            var ta = tips.Aggregate(new P1V(0, 0, 0), (acc, k) => acc + aRest[src0[k]].T()) / tips.Count;
            var db = tb - b.Rest[j].T(); var da = ta - aRest[src0[j]].T();
            if (db.Len() < 1e-6 || da.Len() < 1e-6) continue;
            align[j] = Arc(db / db.Len(), da / da.Len());
        }
        aRoot = aIndex.GetValueOrDefault("root", -1); aPelvis = aIndex["pelvis"];
        bRoot = b.Index.GetValueOrDefault("root", -1); bPelvis = b.Index["pelvis"];
        LegScale = b.Rest[bPelvis][1, 3] / aRest[aPelvis][1, 3];
        BFor = new int[aNames.Length];
        for (int i = 0; i < aNames.Length; i++)
        {
            int ci = Array.IndexOf(aChain, i);
            if (ci > 0 && ci < aChain.Length - 1)
            {
                // the B chain bone whose segment holds A's midpoint
                int best = bChain[1];
                for (int k = 1; k < bChain.Length - 1; k++) if (Seg(bChain, b.Rest, k).lo <= aMid[ci]) best = bChain[k];
                BFor[i] = best;
            }
            else BFor[i] = b.Index.TryGetValue(aNames[i], out int bj) ? bj : -1;
        }
    }

    /// <summary>B bone j's source (the bake's key rule): 0 carried (no source: a helper, B's own bones A lacks), 1 by
    /// name (A bone s0), 2 the spine-to-head chain (slerped between A bones s0 and s1).</summary>
    public (int Kind, int S0, int S1) Source(int j) => ((int)kind[j], kind[j] == Kind.Carried ? -1 : src0[j], kind[j] == Kind.Chain ? src1[j] : -1);

    /// <summary>The role map (systems keyed to A's bone names, on B): by name off the spine-to-head chain; on the chain
    /// (A's spine_01..03, neck_01) the B bone that carries what A's carries, i.e. the B parent of A's next chain bone
    /// (A's spine_03, her chest, carries neck_01 and the clavicles: on B, spine_05; B's spine_03 is mid-back), BFor
    /// where B lacks that bone; where B has no bone (panel_front), its nearest A ancestor's role; -1 only if none maps.</summary>
    public int Role(int a)
    {
        while (a >= 0)
        {
            int k = Array.IndexOf(aChainB, a);
            if (k > 0 && k < aChainB.Length - 1 && b.Index.TryGetValue(aNames[aChainB[k + 1]], out int next) && b.Parent[next] >= 0) return b.Parent[next];
            if (BFor[a] >= 0) return BFor[a];
            a = aParent[a];
        }
        return -1;
    }

    /// <summary>A share of a turn laid on A's chain bones (spine_01, neck_01 ..), spread over B's: each A bone's share
    /// split evenly among the B chain bones whose segment midpoint lies in its A segment (none: on its role bone), so
    /// the total kept.</summary>
    public List<(int B, double Share)> Spread(IEnumerable<(string A, double Share)> shares)
    {
        var o = new List<(int, double)>();
        var aMid = Mids(aChainB, aRest);
        var aCum = Cum(aChainB, aRest); var bMid = Mids(bChainB, b.Rest);
        foreach (var (name, share) in shares)
        {
            if (!aIndexB.TryGetValue(name, out int a)) continue;
            int k = Array.IndexOf(aChainB, a);
            var mine = new List<int>();
            if (k >= 0 && k < aChainB.Length - 1)
                for (int q = 1; q < bChainB.Length - 1; q++)
                    if (bMid[q] >= aCum[k] && bMid[q] < aCum[k + 1]) mine.Add(bChainB[q]);
            if (mine.Count == 0) { int r = Role(a); if (r >= 0) mine.Add(r); }
            foreach (int j in mine) o.Add((j, share / mine.Count));
        }
        return o;
    }

    static double[] Cum(int[] chain, P1M4[] rest)
    {
        var cum = new double[chain.Length];
        for (int k = 1; k < chain.Length; k++) cum[k] = cum[k - 1] + Len(rest, chain[k - 1], chain[k]);
        return cum.Select(x => x / cum[^1]).ToArray();
    }

    /// <summary>pelvis .. Head (inclusive), walking up from Head.</summary>
    static int[] Chain(string[] names, int[] parent, P1M4[] rest, Dictionary<string, int> index)
    {
        var c = new List<int>();
        int j = index["Head"];
        while (j >= 0) { c.Add(j); if (names[j] == "pelvis") break; j = parent[j]; }
        c.Reverse();
        return c.ToArray();
    }

    static double Len(P1M4[] rest, int i, int k) => (rest[k].T() - rest[i].T()).Len();

    /// <summary>Each chain bone's segment midpoint as a fraction of the chain's length (pelvis's head to Head's).</summary>
    static double[] Mids(int[] chain, P1M4[] rest)
    {
        var cum = new double[chain.Length];
        for (int k = 1; k < chain.Length; k++) cum[k] = cum[k - 1] + Len(rest, chain[k - 1], chain[k]);
        double total = cum[^1];
        var m = new double[chain.Length];
        for (int k = 0; k < chain.Length - 1; k++) m[k] = (cum[k] + cum[k + 1]) / 2 / total;
        m[^1] = 1;
        return m;
    }

    (double lo, double hi) Seg(int[] chain, P1M4[] rest, int k)
    {
        var cum = new double[chain.Length];
        for (int q = 1; q < chain.Length; q++) cum[q] = cum[q - 1] + Len(rest, chain[q - 1], chain[q]);
        return (cum[k] / cum[^1], cum[Math.Min(k + 1, chain.Length - 1)] / cum[^1]);
    }

    public static P1M3 Rot(P1M4 m)
    {
        // Gram-Schmidt on the columns (a uniform or axis scale out; A's Head carries 1.07)
        var x = m.Lin().Col(0); var y = m.Lin().Col(1);
        x = x / x.Len();
        y = y - x * P1V.Dot(x, y); y = y / y.Len();
        var z = P1V.Cross(x, y);
        return new P1M3(x.X, y.X, z.X, x.Y, y.Y, z.Y, x.Z, y.Z, z.Z);
    }

    static P1M3 Slerp(P1M3 r0, P1M3 r1, double t) => t <= 0 ? r0 : r0 * P1Rig.Expm(P1Rig.RotVec(r0.T() * r1) * t);

    /// <summary>B's bone worlds (helpers carried at rest) from A's posed bone worlds (skeleton space).</summary>
    public P1M4[] Map(P1M4[] aPose)
    {
        int n = b.Names.Length;
        var delta = new P1M3[aPose.Length];
        P1M3 D(int a) => delta[a] ??= Rot(aPose[a]) * aRestRot[a].T();
        var G = new P1M4[n];
        foreach (int j in order)
        {
            int p = b.Parent[j];
            var carried = p < 0 ? bLocal[j] : G[p] * bLocal[j];
            if (kind[j] == Kind.Carried) { G[j] = carried; continue; }
            var turn = kind[j] == Kind.Direct ? D(src0[j]) : Slerp(D(src0[j]), D(src1[j]), frac[j]);
            var pos = carried.T();
            if (j == bPelvis) pos = b.Rest[j].T() + (aPose[aPelvis].T() - aRest[aPelvis].T()) * LegScale;
            else if (j == bRoot && aRoot >= 0) pos = b.Rest[j].T() + (aPose[aRoot].T() - aRest[aRoot].T()) * LegScale;
            G[j] = P1M4.From(turn * align[j] * Rot(b.Rest[j]), pos);
        }
        return G;
    }

    /// <summary>(the probe) Per matched bone, the angle (deg) between A's posed segment direction and B's, the bodies'
    /// proportions out: a limb bone's segment is its head to the mean of its A children's heads that B has by name
    /// (the same names on B; leaves skipped); the spine-to-head chain by role, rest-relative (B keeps its own torso
    /// rest): B's chain polyline between the length fractions of A's segment k, at rest turned by A's bone k's turn,
    /// against the same posed; "Head" the angle between the
    /// two Heads' whole turns from rest. Group "limb" or "chain".</summary>
    public List<(string Name, string Group, double Deg)> Directions(P1M4[] aPose, P1M4[] bG)
    {
        var o = new List<(string, string, double)>();
        static double Ang(P1V u, P1V v) => Math.Acos(Math.Clamp(P1V.Dot(u, v) / (u.Len() * v.Len()), -1, 1)) * 180 / Math.PI;
        var chainSet = new HashSet<int>(aChainB);
        for (int i = 0; i < aNames.Length; i++)
        {
            if (chainSet.Contains(i) || !b.Index.TryGetValue(aNames[i], out int j) || b.Helpers.Contains(j)) continue;
            var kids = Enumerable.Range(0, aNames.Length).Where(k => aParent[k] == i && !chainSet.Contains(k) && b.Index.TryGetValue(aNames[k], out int bk) && !b.Helpers.Contains(bk)).ToList();
            if (kids.Count == 0) continue;
            var ta = kids.Aggregate(new P1V(0, 0, 0), (acc, k) => acc + aPose[k].T()) / kids.Count - aPose[i].T();
            var tb = kids.Aggregate(new P1V(0, 0, 0), (acc, k) => acc + bG[b.Index[aNames[k]]].T()) / kids.Count - bG[j].T();
            o.Add((aNames[i], "limb", Ang(ta, tb)));
        }
        double[] Cum(int[] c, P1M4[] g) { var cu = new double[c.Length]; for (int k = 1; k < c.Length; k++) cu[k] = cu[k - 1] + (g[c[k]].T() - g[c[k - 1]].T()).Len(); return cu.Select(x => x / cu[^1]).ToArray(); }
        var fa = Cum(aChainB, aRest); var fb = Cum(bChainB, b.Rest);
        P1V At(double f, P1M4[] g)
        {
            int k = 1; while (k < fb.Length - 1 && fb[k] < f) k++;
            double t = fb[k] > fb[k - 1] ? (f - fb[k - 1]) / (fb[k] - fb[k - 1]) : 0;
            return g[bChainB[k - 1]].T() * (1 - t) + g[bChainB[k]].T() * t;
        }
        var bRestSeg = new P1V[aChainB.Length];
        for (int k = 0; k < aChainB.Length - 1; k++) bRestSeg[k] = At(fa[k + 1], b.Rest) - At(fa[k], b.Rest);
        for (int k = 0; k < aChainB.Length - 1; k++)
            o.Add((aNames[aChainB[k]], "chain", Ang(Rot(aPose[aChainB[k]]) * aRestRot[aChainB[k]].T() * bRestSeg[k], At(fa[k + 1], bG) - At(fa[k], bG))));
        int ah = aIndexB["Head"], bh = b.Index["Head"];
        var dA = Rot(aPose[ah]) * aRestRot[ah].T(); var dB = Rot(bG[bh]) * Rot(b.Rest[bh]).T();
        o.Add(("Head", "chain", P1Rig.RotVec(dA.T() * dB).Len() * 180 / Math.PI));
        return o;
    }
}
