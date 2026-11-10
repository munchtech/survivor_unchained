using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace SurvivorUnchained.Look;

/// <summary>(P7 round 3, 9 Nov) The skills lead's numbers in data/look/fx_language.json "p7": the judge's sizes (px at the
/// play camera, 1080 lines), counts, timings and alphas per shape, read by the P7 views (View/BattleFx.P7*.cs). A path is
/// dotted ("leap.ring.lead_px"); a number reads as one value, an array (of numbers or [t, v] pairs) flattened in order.
/// Colors are never here: they stay the school's (L1's "physical"). Beside L1's FxLanguage, which it does not change.</summary>
public sealed class FxP7
{
    readonly Dictionary<string, float[]> v = new();

    public static FxP7 Parse(string json)
    {
        var p = new FxP7();
        try
        {
            using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { AllowTrailingCommas = true, CommentHandling = JsonCommentHandling.Skip });
            if (doc.RootElement.TryGetProperty("p7", out var root)) p.Walk(root, "");
        }
        catch (JsonException e) { throw new InvalidDataException("fx_language.json is malformed: " + e.Message, e); }
        return p;
    }

    void Walk(JsonElement e, string path)
    {
        if (e.ValueKind == JsonValueKind.Object)
        {
            foreach (var q in e.EnumerateObject()) Walk(q.Value, path.Length == 0 ? q.Name : path + "." + q.Name);
            return;
        }
        var list = new List<float>();
        Flat(e, list);
        if (list.Count > 0) v[path] = list.ToArray();
    }

    static void Flat(JsonElement e, List<float> into)
    {
        if (e.ValueKind == JsonValueKind.Number) into.Add(e.GetSingle());
        else if (e.ValueKind == JsonValueKind.Array) foreach (var x in e.EnumerateArray()) Flat(x, into);
    }

    public bool Has(string path) => v.ContainsKey(path);
    /// <summary>The path's first value (`or` when it is missing).</summary>
    public float this[string path, float or = float.NaN] => v.TryGetValue(path, out var a) ? a[0] : (float.IsNaN(or) ? throw new KeyNotFoundException("fx_language.json p7: no " + path) : or);
    /// <summary>The path's values, flattened.</summary>
    public float[] All(string path) => v.TryGetValue(path, out var a) ? a : throw new KeyNotFoundException("fx_language.json p7: no " + path);
    /// <summary>A [lo, hi] pair at the path: a value between them at `u` (0..1).</summary>
    public float Range(string path, float u) { var a = All(path); return a.Length < 2 ? a[0] : a[0] + (a[1] - a[0]) * Math.Clamp(u, 0f, 1f); }
    /// <summary>A [lo, hi] count pair: an integer between them, both ends included, at `u` (0..1).</summary>
    public int Count(string path, float u) { var a = All(path); return a.Length < 2 ? (int)a[0] : (int)a[0] + (int)Math.Min(a[1] - a[0], Math.Floor(u * (a[1] - a[0] + 1))); }
    /// <summary>A curve of [t, v] pairs at the path: v at `t`, linear between, held past the ends.</summary>
    public float Curve(string path, float t)
    {
        var a = All(path);
        if (a.Length < 2) return a[0];
        if (t <= a[0]) return a[1];
        for (int i = 2; i + 1 < a.Length; i += 2)
            if (t <= a[i]) return a[i - 1] + (a[i + 1] - a[i - 1]) * (t - a[i - 2]) / Math.Max(1e-6f, a[i] - a[i - 2]);
        return a[^1];
    }
}
