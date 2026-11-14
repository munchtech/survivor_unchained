using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Which of a worn piece's vertices ride its spring bones (her wear: HerWear; a piece's file is skinned to her body
/// bones only, so its springs need their vertices given to them at dress time, once). Each spring link is a segment
/// (head to tail, the skeleton's rest frame) with a reach; a vertex is in a link's region when it lies within the reach
/// of the segment and beside it (its projection between a little above the head and a little below the tail).
/// Island: each welded island of the mesh (a lappet, a plate, a rivet) goes whole to the link whose region holds the
/// most of its vertices (near ties: the one it lies nearer on average), if that is at least Share of them, weight 1 (a metal plate turns rigidly about its hinge);
/// the rest keep their weights. Blend: each vertex in a region goes to its nearest link by a share rising from 0 at
/// the head to 1 at the tail (cloth: its top stays on the body's weights). Deterministic (ties to the lower link).
/// Engine-free: the tests hold it.
/// </summary>
public static class SpringCarry
{
    public enum Rule { Island, Blend }

    public readonly record struct Seg(Vector3 Head, Vector3 Tail, float Reach);

    /// <summary>How far past the head and the tail (in segment lengths) a region reaches along the link.</summary>
    public const float Overhang = 0.15f;

    public static Rule Parse(string? rule) => rule == "blend" ? Rule.Blend : Rule.Island;

    /// <summary>Whether p is in s's region; t its place along the segment (0 head, 1 tail), d its distance off it.</summary>
    public static bool InRegion(in Seg s, Vector3 p, out float t, out float d)
    {
        var ab = s.Tail - s.Head;
        float l2 = Vector3.Dot(ab, ab);
        t = l2 > 1e-12f ? Vector3.Dot(p - s.Head, ab) / l2 : 0;
        d = Vector3.Distance(p, s.Head + ab * Math.Clamp(t, 0, 1));
        return t >= -Overhang && t <= 1 + Overhang && d <= s.Reach;
    }

    /// <summary>Each vertex's link (-1: none) and its share of the link's weight (0..1).</summary>
    public static (int[] Link, float[] Share) Assign(Vector3[] pos, int[] tris, Seg[] links, Rule rule, float share = 0.6f, float weld = 1e-4f)
    {
        int n = pos.Length;
        var link = new int[n];
        var sh = new float[n];
        Array.Fill(link, -1);
        if (links.Length == 0 || n == 0) return (link, sh);
        if (rule == Rule.Blend)
        {
            for (int i = 0; i < n; i++)
            {
                float best = float.MaxValue;
                for (int k = 0; k < links.Length; k++)
                    if (InRegion(links[k], pos[i], out float t, out float d) && d < best)
                    {
                        best = d; link[i] = k;
                        float u = Math.Clamp(t, 0, 1);
                        sh[i] = u * u * (3 - 2 * u);
                    }
                if (link[i] >= 0 && sh[i] <= 0) link[i] = -1;
            }
            return (link, sh);
        }
        var island = Islands(pos, tris, weld);
        // (per island: its size and, per link, how many of its vertices the link's region holds)
        var size = new Dictionary<int, int>();
        var votes = new Dictionary<int, (int[] N, double[] D)>();
        for (int i = 0; i < n; i++)
        {
            int r = island[i];
            size[r] = size.TryGetValue(r, out int c) ? c + 1 : 1;
            for (int k = 0; k < links.Length; k++)
                if (InRegion(links[k], pos[i], out _, out float d))
                {
                    if (!votes.TryGetValue(r, out var v)) votes[r] = v = (new int[links.Length], new double[links.Length]);
                    v.N[k]++; v.D[k] += d;
                }
        }
        // (the link holding the most of the island; within 5% of that, the nearest on average: a plate between two
        // overlapping regions goes to the one it lies along)
        var pick = new Dictionary<int, int>();
        foreach (var (r, v) in votes)
        {
            int most = v.N.Max(), best = -1;
            for (int k = 0; k < v.N.Length; k++)
                if (v.N[k] >= 0.95 * most && v.N[k] > 0 && (best < 0 || v.D[k] / v.N[k] < v.D[best] / v.N[best])) best = k;
            if (best >= 0 && v.N[best] >= share * size[r]) pick[r] = best;
        }
        for (int i = 0; i < n; i++)
            if (pick.TryGetValue(island[i], out int k)) { link[i] = k; sh[i] = 1; }
        return (link, sh);
    }

    /// <summary>The mesh's welded islands (vertices at one place, to `weld`, are one; triangles join their corners):
    /// each vertex's island id (its island's lowest vertex).</summary>
    public static int[] Islands(Vector3[] pos, int[] tris, float weld = 1e-4f)
    {
        int n = pos.Length;
        var par = new int[n];
        for (int i = 0; i < n; i++) par[i] = i;
        int Find(int x) { while (par[x] != x) { par[x] = par[par[x]]; x = par[x]; } return x; }
        void Join(int a, int b) { a = Find(a); b = Find(b); if (a == b) return; if (a < b) par[b] = a; else par[a] = b; }
        var at = new Dictionary<(long, long, long), int>();
        for (int i = 0; i < n; i++)
        {
            var key = ((long)MathF.Round(pos[i].X / weld), (long)MathF.Round(pos[i].Y / weld), (long)MathF.Round(pos[i].Z / weld));
            if (at.TryGetValue(key, out int j)) Join(i, j); else at[key] = i;
        }
        for (int t = 0; t + 2 < tris.Length; t += 3) { Join(tris[t], tris[t + 1]); Join(tris[t], tris[t + 2]); }
        var o = new int[n];
        for (int i = 0; i < n; i++) o[i] = Find(i);
        return o;
    }

    /// <summary>The carried vertices' weights rewritten in place (k influences a vertex): a share of 1 puts the vertex
    /// wholly on its link's bind; less scales its own weights by 1 - share and gives the link the share in its own
    /// slot, a free one, or that of its smallest weight (renormalised). Returns how many vertices moved.</summary>
    public static int Apply(int[] bones, float[] weights, int k, int[] link, float[] share, int[] linkBind)
    {
        int moved = 0;
        for (int i = 0; i < link.Length; i++)
        {
            if (link[i] < 0) continue;
            int o = i * k, b = linkBind[link[i]];
            float s = Math.Clamp(share[i], 0, 1);
            moved++;
            if (s >= 0.999f)
            {
                for (int j = 0; j < k; j++) { bones[o + j] = j == 0 ? b : 0; weights[o + j] = j == 0 ? 1 : 0; }
                continue;
            }
            int slot = -1;
            for (int j = 0; j < k; j++) { weights[o + j] *= 1 - s; if (bones[o + j] == b && weights[o + j] > 0) slot = j; }
            if (slot < 0)
            {
                slot = 0;
                for (int j = 1; j < k; j++) if (weights[o + j] < weights[o + slot]) slot = j;
                bones[o + slot] = b;
                weights[o + slot] = s;
            }
            else weights[o + slot] += s;
            float sum = 0;
            for (int j = 0; j < k; j++) sum += weights[o + j];
            if (sum > 1e-6f) for (int j = 0; j < k; j++) weights[o + j] /= sum;
        }
        return moved;
    }
}
