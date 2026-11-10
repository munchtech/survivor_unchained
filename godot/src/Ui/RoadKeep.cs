using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The minimap's "road keep" mask (M4 UI lead 13, S2). The minimap tells roads by the drawing's dirt hue, so any dirt-hued
/// ground (a camp yard, a bank) draws as a road lump. Plain C#, built once per zone: the road pixels are opened (eroded then
/// dilated) to cut hairlines, the opened mask is labelled, every component under the size on screen is dropped, and the
/// hairlines the opening cut are restored only where they join kept road without also running into a dropped island.
/// </summary>
public static class RoadKeep
{
    /// <summary>A byte mask (255 kept road, 0 not) the size of <paramref name="road"/>. <paramref name="scale"/> is minimap
    /// screen pixels per drawing pixel; islands whose longer bounding-box side is under <paramref name="minScreen"/> screen
    /// pixels are dropped; <paramref name="dropped"/> gets their sizes in screen pixels.</summary>
    public static byte[] Build(bool[] road, int w, int h, float scale, float minScreen, float cutScreen, List<int> dropped)
    {
        int r = Math.Clamp((int)Math.Ceiling(cutScreen / Math.Max(scale, 1e-4f) / 2f), 1, 8);
        var opened = Dilate(Erode(road, w, h, r), w, h, r);
        for (int i = 0; i < opened.Length; i++) opened[i] &= road[i];
        var lab = new int[w * h];
        var keepComp = new List<bool> { false };
        var stack = new Stack<int>();
        int n = 0;
        for (int s = 0; s < lab.Length; s++)
        {
            if (!opened[s] || lab[s] != 0) continue;
            n++;
            int x0 = w, y0 = h, x1 = 0, y1 = 0;
            lab[s] = n; stack.Push(s);
            while (stack.Count > 0)
            {
                int p = stack.Pop(), px = p % w, py = p / w;
                x0 = Math.Min(x0, px); x1 = Math.Max(x1, px); y0 = Math.Min(y0, py); y1 = Math.Max(y1, py);
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        int qx = px + dx, qy = py + dy;
                        if (qx < 0 || qy < 0 || qx >= w || qy >= h) continue;
                        int q = qy * w + qx;
                        if (opened[q] && lab[q] == 0) { lab[q] = n; stack.Push(q); }
                    }
            }
            float across = Math.Max(x1 - x0 + 1, y1 - y0 + 1) * scale;
            bool keep = across >= minScreen;
            keepComp.Add(keep);
            if (!keep) dropped?.Add((int)Math.Round(across));
        }
        var outMask = new byte[w * h];
        for (int i = 0; i < outMask.Length; i++) if (lab[i] > 0 && keepComp[lab[i]]) outMask[i] = 255;
        // the hairlines the opening cut: groups of road pixels outside every opened component
        var seen = new bool[w * h];
        var group = new List<int>();
        var touch = new HashSet<int>();
        for (int s = 0; s < seen.Length; s++)
        {
            if (!road[s] || opened[s] || seen[s]) continue;
            group.Clear(); touch.Clear();
            seen[s] = true; stack.Push(s);
            while (stack.Count > 0)
            {
                int p = stack.Pop(), px = p % w, py = p / w;
                group.Add(p);
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        int qx = px + dx, qy = py + dy;
                        if (qx < 0 || qy < 0 || qx >= w || qy >= h) continue;
                        int q = qy * w + qx;
                        if (opened[q]) touch.Add(lab[q]);
                        else if (road[q] && !seen[q]) { seen[q] = true; stack.Push(q); }
                    }
            }
            int kept = 0; bool hitsDropped = false;
            foreach (var c in touch) { if (keepComp[c]) kept++; else hitsDropped = true; }
            if (kept >= 2 || (kept == 1 && !hitsDropped))
                foreach (var p in group) outMask[p] = 255;
        }
        return outMask;
    }

    static bool[] Erode(bool[] a, int w, int h, int r) => Pass(a, w, h, r, true);
    static bool[] Dilate(bool[] a, int w, int h, int r) => Pass(a, w, h, r, false);

    /// <summary>Square window of half-width r, as two separable passes (outside the image counts as not road).</summary>
    static bool[] Pass(bool[] a, int w, int h, int r, bool erode)
    {
        var t = new bool[a.Length];
        var o = new bool[a.Length];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                bool v = erode;
                for (int k = -r; k <= r && (erode ? v : !v); k++)
                {
                    int q = x + k;
                    bool b = q >= 0 && q < w && a[y * w + q];
                    if (erode) v &= b; else v |= b;
                }
                t[y * w + x] = v;
            }
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                bool v = erode;
                for (int k = -r; k <= r && (erode ? v : !v); k++)
                {
                    int q = y + k;
                    bool b = q >= 0 && q < h && t[q * w + x];
                    if (erode) v &= b; else v |= b;
                }
                o[y * w + x] = v;
            }
        return o;
    }
}
