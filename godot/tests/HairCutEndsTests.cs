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

        public float[] Alpha(int ai) => Channel(ai, 3);

        /// <summary>COLOR_0's channel k (0 r .. 3 a), unsigned short.</summary>
        public float[] Channel(int ai, int k)
        {
            var a = g.GetProperty("accessors")[ai];
            Assert.Equal(5123, a.GetProperty("componentType").GetInt32());
            var (off, c, st) = At(ai, 8);
            var r = new float[c];
            for (int i = 0; i < c; i++) r[i] = BitConverter.ToUInt16(bin, off + i * st + 2 * k) / 65535f;
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

    const float FrontTh = 50f, EdgeEl = 8f, RiseFull = 0.030f, CheckMax = 0.1f;

    /// <summary>The braid's front hairline cards carry no shine over their rise (hair-chip r2, 13 Nov: the judge's grey
    /// striped bars over a dark-haired NPC's hairline at the chest camera, day and night, and her faint parting speck:
    /// each shine-carrying card rooted on her front hairline rises off her forehead over its first 15-45 mm, its strand
    /// turned square to the half-vector there, so the cel band lit it, one card between matte under-layer cards: a
    /// stripe). heroine_hair_cut_ends.py's front_rise marks their first 30 mm matte (COLOR_0's blue 0.5, the hair
    /// shader's matte mark), eased to none (0.45) by 55 mm. Read as it reads them: a card within 50 degrees of her
    /// front (+Z, round the hair's box middle, 17 cm under its top), drawn, its root within 8 degrees of elevation of
    /// its 10-degree slice's lowest drawn root, not all matte already, has blue 0.49 or more over its first 30 mm.</summary>
    [Fact]
    public void Her_braid_front_hairline_cards_are_matte_over_their_rise()
    {
        var path = Path.Combine(Root(), "art", "people", "heroine_hair_braid.gltf");
        var g = JsonDocument.Parse(File.ReadAllText(path)).RootElement;
        var bin = File.ReadAllBytes(Path.Combine(Path.GetDirectoryName(path)!, g.GetProperty("buffers")[0].GetProperty("uri").GetString()!));
        var gl = new Gltf(g, bin);
        var mats = g.GetProperty("materials").EnumerateArray().Select(m => m.TryGetProperty("name", out var nm) ? nm.GetString() : "").ToArray();
        var prim = g.GetProperty("meshes").EnumerateArray().SelectMany(m => m.GetProperty("primitives").EnumerateArray())
            .First(pr => mats[pr.GetProperty("material").GetInt32()] == "hair");
        var a = prim.GetProperty("attributes");
        var pos = gl.Floats(a.GetProperty("POSITION").GetInt32(), 3);
        var uv = gl.Floats(a.GetProperty("TEXCOORD_0").GetInt32(), 2);
        var alpha = gl.Alpha(a.GetProperty("COLOR_0").GetInt32());
        var blue = gl.Channel(a.GetProperty("COLOR_0").GetInt32(), 2);
        var idx = gl.Indices(prim.GetProperty("indices").GetInt32());
        int n = alpha.Length;
        Vector3 P(int i) => new(pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]);
        var lo = new Vector3(float.MaxValue); var hi = new Vector3(float.MinValue);
        for (int i = 0; i < n; i++) { lo = Vector3.Min(lo, P(i)); hi = Vector3.Max(hi, P(i)); }
        var cen = new Vector3((lo.X + hi.X) / 2, hi.Y - 0.17f, (lo.Z + hi.Z) / 2);
        var p = Enumerable.Range(0, n).ToArray();
        for (int t = 0; t < idx.Length; t += 3) { p[Find(p, idx[t])] = Find(p, idx[t + 1]); p[Find(p, idx[t + 1])] = Find(p, idx[t + 2]); }
        var cards = new List<(int[] Vs, float[] Arc, Vector3 Root, float Th, float El, bool Drawn)>();
        foreach (var card in Enumerable.Range(0, n).GroupBy(i => Find(p, i)))
        {
            var vs = card.ToArray();
            var us = vs.Select(i => MathF.Round(uv[2 * i], 4)).Distinct().OrderBy(u => u).ToArray();
            if (us.Length != 3) continue;
            var mid = vs.Where(i => MathF.Abs(uv[2 * i] - us[1]) < 1e-4f).GroupBy(i => MathF.Round(uv[2 * i + 1], 4)).OrderBy(gr => gr.Key)
                .Select(gr => (V: gr.Key, I: gr.First())).ToArray();
            var arc = new float[mid.Length];
            for (int k = 1; k < mid.Length; k++) arc[k] = arc[k - 1] + Vector3.Distance(P(mid[k].I), P(mid[k - 1].I));
            float ArcAt(float v)
            {
                int k = Array.FindIndex(mid, m => m.V >= v - 1e-4f);
                if (k < 0) return arc[^1];
                if (k == 0) return 0f;
                return arc[k - 1] + (arc[k] - arc[k - 1]) * Math.Clamp((v - mid[k - 1].V) / Math.Max(mid[k].V - mid[k - 1].V, 1e-6f), 0f, 1f);
            }
            var r = P(mid[0].I) - cen;
            cards.Add((vs, vs.Select(i => ArcAt(MathF.Round(uv[2 * i + 1], 4))).ToArray(), P(mid[0].I),
                MathF.Atan2(r.X, r.Z) * 180f / MathF.PI, MathF.Atan2(r.Y, MathF.Sqrt(r.X * r.X + r.Z * r.Z)) * 180f / MathF.PI,
                vs.Max(i => alpha[i]) > CheckMax));
        }
        var low = cards.Where(c => c.Drawn).GroupBy(c => MathF.Floor(c.Th / 10f)).ToDictionary(gr => gr.Key, gr => gr.Min(c => c.El));
        var front = cards.Where(c => c.Drawn && MathF.Abs(c.Th) <= FrontTh && c.El <= low[MathF.Floor(c.Th / 10f)] + EdgeEl
            && !c.Vs.All(i => MathF.Abs(blue[i] - 0.5f) < 0.006f)).ToList();
        Assert.True(front.Count >= 20, $"braid: only {front.Count} front hairline cards found");
        var shining = new List<string>();
        foreach (var c in front)
        {
            var rise = Enumerable.Range(0, c.Vs.Length).Where(k => c.Arc[k] < RiseFull).Select(k => blue[c.Vs[k]]).DefaultIfEmpty(1f).Min();
            if (rise < 0.49f) shining.Add($"card rooted at {c.Root} (blue {rise:0.00} on its rise)");
        }
        Assert.True(shining.Count == 0, $"braid: {shining.Count} of {front.Count} front hairline cards shine on their rise (run tools/assets/heroine_hair_cut_ends.py):\n" + string.Join("\n", shining.Take(10)));
    }
}
