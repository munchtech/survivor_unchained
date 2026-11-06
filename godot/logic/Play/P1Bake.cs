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
///  - the girdle hold: clavicle_{l,r} and scap_{l,r} stand at B's rest local (B's girdle law, P1Rig.Drive, turns them
///    at runtime from the arm; A's clip clavicle turn dropped B's shoulder joint 22-32 mm in the town idle: the dome),
///    the upper arm keeps its mapped world turn (its head rides the held clavicle), all below follow by their locals;
///  - positions: B's rest offsets but for root and pelvis (P1Retarget's LegScale rule);
///  - keys: a B bone is keyed only if its source A bone(s) are keyed in the clip (by name, or either chain bracket);
///    the girdle and B's helpers never (partial clips stay partial, the game's filtered blends behave as on A);
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

    /// <summary>One frame: A's posed globals (skeleton space) to B's locals and globals, girdle held, the clean applied.</summary>
    public (P1M4[] Local, P1M4[] G) Frame(P1M4[] aPose, Clean? clean = null) => Hold(Map.Map(aPose), clean);

    /// <summary>The girdle hold and the clean on mapped B globals.</summary>
    public (P1M4[] Local, P1M4[] G) Hold(P1M4[] mapped, Clean? clean = null)
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
        foreach (int j in Girdle) L[j] = restLocal[j];
        var G = new P1M4[n];
        foreach (int j in order)
        {
            int p = B.Parent[j];
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
        return (L, G);
    }

    static P1M4 Compose(P1M4? parent, P1M4 local) => parent == null ? local : parent * local;

    /// <summary>The key rule: the B bones keyed in a clip whose keyed A bones are aKeyed.</summary>
    public HashSet<int> Keyed(ICollection<int> aKeyed)
    {
        var o = new HashSet<int>();
        for (int j = 0; j < B.Names.Length; j++)
        {
            if (Girdle.Contains(j) || B.Helpers.Contains(j)) continue;
            var (k, s0, s1) = Map.Source(j);
            if (k == 1 && aKeyed.Contains(s0) || k == 2 && (aKeyed.Contains(s0) || aKeyed.Contains(s1))) o.Add(j);
        }
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
    }

    /// <summary>p1_clips.json's "clips": { name: { "why": .., "turns": { bone: [x, y, z] }, "hold": [bones] } }.</summary>
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
            o[c.Name] = cl;
        }
        return o;
    }
}
