using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her hair has no blunt cut card ends (hair-chip, 13 Nov: the judge's pale chip at her parting at the
/// close-up, day and night, was an outer card heroine_hair.py's off_brow cut 18 mm along, its stub ending square at
/// full cover under the cel shine). tools/assets/heroine_hair_cut_ends.py tapers each cut card over its last 8 mm and
/// drops the stubs; this reads the shipped gltfs as it does: in every "hair" and "hair_fine" surface, each card (one
/// connected strip of three U columns, V 0 at its root) whose middle column's last links fold onto one point (cut)
/// keeps cover (COLOR_0's alpha, the hair shader's COLOR.a) of at most 0.1 over its last 1.5 mm before the fold, and is
/// no stub still drawn: its full cover (95% of its most) reached at least 9 mm before the fold, or its cover at most
/// 0.1 throughout. (The chip card, tapered but kept, still drew a fainter chip: its full cover began 8 mm before its
/// cut, its fade-in meeting its taper. The NPCs' hair is this braid refitted, so it carried the same card.)</summary>
public class HairCutEndsTests
{
    const float Eps = 2e-4f, Near = 0.0015f, MaxCover = 0.1f, Stub = 0.009f;

    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    sealed class Gltf(JsonElement g, byte[] bin)
    {
        (int Off, int Count, int Stride) At(int ai, int size)
        {
            var a = g.GetProperty("accessors")[ai];
            var bv = g.GetProperty("bufferViews")[a.GetProperty("bufferView").GetInt32()];
            int off = (bv.TryGetProperty("byteOffset", out var o) ? o.GetInt32() : 0) + (a.TryGetProperty("byteOffset", out var o2) ? o2.GetInt32() : 0);
            return (off, a.GetProperty("count").GetInt32(), bv.TryGetProperty("byteStride", out var s) ? s.GetInt32() : size);
        }

        public float[] Floats(int ai, int n)
        {
            var (off, c, st) = At(ai, 4 * n);
            var r = new float[c * n];
            for (int i = 0; i < c; i++) for (int k = 0; k < n; k++) r[i * n + k] = BitConverter.ToSingle(bin, off + i * st + 4 * k);
            return r;
        }

        public float[] Alpha(int ai)
        {
            var a = g.GetProperty("accessors")[ai];
            Assert.Equal(5123, a.GetProperty("componentType").GetInt32());
            var (off, c, st) = At(ai, 8);
            var r = new float[c];
            for (int i = 0; i < c; i++) r[i] = BitConverter.ToUInt16(bin, off + i * st + 6) / 65535f;
            return r;
        }

        public int[] Indices(int ai)
        {
            int ct = g.GetProperty("accessors")[ai].GetProperty("componentType").GetInt32();
            var (off, c, st) = At(ai, ct == 5125 ? 4 : 2);
            var r = new int[c];
            for (int i = 0; i < c; i++) r[i] = ct == 5125 ? (int)BitConverter.ToUInt32(bin, off + i * st) : BitConverter.ToUInt16(bin, off + i * st);
            return r;
        }
    }

    static int Find(int[] p, int x) { while (p[x] != x) x = p[x] = p[p[x]]; return x; }

    /// <summary>Each cut card's worst cover over its last 1.5 mm, and where it ends.</summary>
    static List<(float Cover, float Run, float Most, Vector3 At)> CutEnds(float[] pos, float[] uv, float[] alpha, int[] idx)
    {
        int n = alpha.Length;
        var p = Enumerable.Range(0, n).ToArray();
        for (int t = 0; t < idx.Length; t += 3) { p[Find(p, idx[t])] = Find(p, idx[t + 1]); p[Find(p, idx[t + 1])] = Find(p, idx[t + 2]); }
        var cards = Enumerable.Range(0, n).GroupBy(i => Find(p, i));
        var res = new List<(float, float, float, Vector3)>();
        Vector3 P(int i) => new(pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]);
        foreach (var card in cards)
        {
            var vs = card.ToArray();
            var us = vs.Select(i => MathF.Round(uv[2 * i], 4)).Distinct().OrderBy(u => u).ToArray();
            if (us.Length != 3) continue;
            var mid = vs.Where(i => MathF.Abs(uv[2 * i] - us[1]) < 1e-4f).GroupBy(i => MathF.Round(uv[2 * i + 1], 4)).OrderBy(gr => gr.Key)
                .Select(gr => (V: gr.Key, I: gr.First())).ToArray();
            var arc = new float[mid.Length];
            int last = -1;
            for (int k = 1; k < mid.Length; k++)
            {
                float l = Vector3.Distance(P(mid[k].I), P(mid[k - 1].I));
                arc[k] = arc[k - 1] + l;
                if (l > Eps) last = k;
            }
            if (last < 0 || last >= mid.Length - 1) continue;            // all one point (no area), or not cut
            float end = arc[last];
            float ArcAt(float v)
            {
                int k = Array.FindIndex(mid, m => m.V >= v - 1e-4f);
                if (k <= 0) return 0f;
                return arc[k - 1] + (arc[k] - arc[k - 1]) * Math.Clamp((v - mid[k - 1].V) / Math.Max(mid[k].V - mid[k - 1].V, 1e-6f), 0f, 1f);
            }
            float worst = vs.Where(i => MathF.Abs(ArcAt(MathF.Round(uv[2 * i + 1], 4)) - end) < Near).Select(i => alpha[i]).DefaultIfEmpty(0f).Max();
            float most = vs.Max(i => alpha[i]);
            float full = vs.Where(i => alpha[i] >= 0.95f * most).Select(i => ArcAt(MathF.Round(uv[2 * i + 1], 4))).DefaultIfEmpty(end).Min();
            res.Add((worst, end - full, most, P(mid[last].I)));
        }
        return res;
    }

    [Theory]
    [InlineData("braid")]
    [InlineData("ponytail")]
    [InlineData("pixie")]
    public void Her_hair_has_no_blunt_cut_card_ends_or_stubs(string style)
    {
        var path = Path.Combine(Root(), "art", "people", $"heroine_hair_{style}.gltf");
        var g = JsonDocument.Parse(File.ReadAllText(path)).RootElement;
        var bin = File.ReadAllBytes(Path.Combine(Path.GetDirectoryName(path)!, g.GetProperty("buffers")[0].GetProperty("uri").GetString()!));
        var gl = new Gltf(g, bin);
        var mats = g.GetProperty("materials").EnumerateArray().Select(m => m.TryGetProperty("name", out var nm) ? nm.GetString() : "").ToArray();
        int seen = 0;
        var blunt = new List<string>();
        foreach (var mesh in g.GetProperty("meshes").EnumerateArray())
            foreach (var prim in mesh.GetProperty("primitives").EnumerateArray())
            {
                var name = mats[prim.GetProperty("material").GetInt32()];
                if (name is not ("hair" or "hair_fine")) continue;
                var a = prim.GetProperty("attributes");
                var ends = CutEnds(gl.Floats(a.GetProperty("POSITION").GetInt32(), 3), gl.Floats(a.GetProperty("TEXCOORD_0").GetInt32(), 2),
                    gl.Alpha(a.GetProperty("COLOR_0").GetInt32()), gl.Indices(prim.GetProperty("indices").GetInt32()));
                seen++;
                blunt.AddRange(ends.Where(e => e.Cover > MaxCover).Select(e => $"{name} at {e.At} cover {e.Cover:0.00}"));
                blunt.AddRange(ends.Where(e => e.Cover <= MaxCover && e.Most > MaxCover && e.Run < Stub).Select(e => $"{name} at {e.At}: a stub kept (full cover {e.Run * 1e3f:0.0} mm before its cut)"));
            }
        Assert.True(seen > 0, $"{style}: no hair surfaces read");
        Assert.True(blunt.Count == 0, $"{style}: {blunt.Count} cut cards end blunt or are stubs kept (run tools/assets/heroine_hair_cut_ends.py):\n" + string.Join("\n", blunt.Take(10)));
    }
}
