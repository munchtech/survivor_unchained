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

    static bool Limb(string n) => new[] { "clavicle", "upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb", "thigh", "calf", "foot", "ball" }.Any(n.StartsWith);

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

    public P1Retarget(string[] aNames, int[] aParent, P1M4[] aRest, P1Rig b)
    {
        this.b = b; this.aRest = aRest;
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
        var aMid = Mids(aChain, aRest);
        var bMid = Mids(bChain, b.Rest);
        for (int j = 0; j < n; j++)
        {
            int ci = Array.IndexOf(bChain, j);
            if (ci > 0 && ci < bChain.Length - 1)
            {
                double t = bMid[ci];
                int k = 1;
                while (k < aChain.Length - 2 && aMid[k + 1] < t) k++;
                double lo = aMid[k], hi = aMid[Math.Min(k + 1, aChain.Length - 2)];
                kind[j] = Kind.Chain; src0[j] = aChain[k]; src1[j] = aChain[Math.Min(k + 1, aChain.Length - 2)];
                frac[j] = hi > lo ? Math.Clamp((t - lo) / (hi - lo), 0, 1) : 0;
            }
            else if (!b.Helpers.Contains(j) && aIndex.TryGetValue(b.Names[j], out int a)) { kind[j] = Kind.Direct; src0[j] = a; }
            else kind[j] = Kind.Carried;
        }
        // B's limbs stood in A's rest first: each limb bone's rest direction turned (the shortest turn, in the world)
        // onto its A bone's, so a clip's limb turns, relative to A's rest, start from A's rest limb. B's rest differs
        // there (her arms forward, hands 19 cm off A's; feet 11 cm forward); the torso, neck and head keep B's own
        // rest (built standing as A stands; the head is A's own, baked in place). A bone's direction: its head to the
        // mean of its nearest descendants matched by name (through B's own carried and helper bones: the metacarpals, the twist chain); a limb's
        // last bone takes its parent's turn.
        align = Enumerable.Range(0, n).Select(_ => P1M3.Id).ToArray();
        foreach (int j in order)
        {
            if (kind[j] != Kind.Direct || !Limb(b.Names[j])) continue;
            var tips = new List<int>();
            var st = new Queue<int>(Enumerable.Range(0, n).Where(k => b.Parent[k] == j));
            while (st.Count > 0)
            {
                int k = st.Dequeue();
                if (kind[k] == Kind.Direct && !b.Helpers.Contains(k)) tips.Add(k);
                else foreach (var c in Enumerable.Range(0, n).Where(q => b.Parent[q] == k)) st.Enqueue(c);   // (through B's carried and helper bones: B's lowerarm hangs under its twist chain)
            }
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
}
