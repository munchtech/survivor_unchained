using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Look;

/// <summary>One stepped band of a spell (L1 B6, bible rule 13): it starts at heat T (0..1 of the 1D gradient), its color is
/// Hex (the displayed color it is FROM, with Oklab L, C, H), Emit the linear gain that lands it there in the game.</summary>
public sealed record FxBand(string Name, float T, string Hex, float L, float C, float H, float[] Emit);

/// <summary>The soft outer glow: Width the falloff's e-fold and Reach where it ends (head radii), Head and Tail its strength.</summary>
public sealed record FxGlow(string Hex, float Width, float Reach, float Head, float Tail);

/// <summary>Painted sparks: Count per effect, Length (of the effect's length) and Aspect.</summary>
public sealed record FxSparks(string Hex, int Count, float Length, float Aspect);

/// <summary>One school's family: two or three bands in rising heat (edge first, core last), the glow, the sparks.</summary>
public sealed record FxSchool(string Name, string From, IReadOnlyList<FxBand> Bands, FxGlow Glow, FxSparks Sparks)
{
    public FxBand Edge => Bands[0];
    public FxBand Core => Bands[^1];
    /// <summary>The middle band; with two bands, the core (so the mid threshold equals the core's: no third step).</summary>
    public FxBand Mid => Bands.Count == 3 ? Bands[1] : Bands[^1];
}

/// <summary>data/look/fx_language.json as plain data; no Godot types.</summary>
public sealed class FxLanguage
{
    public IReadOnlyDictionary<string, FxSchool> Schools { get; private init; } = new Dictionary<string, FxSchool>();
    public FxSchool? this[string school] => Schools.TryGetValue(school.ToLowerInvariant(), out var s) ? s : null;

    public static FxLanguage Parse(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { AllowTrailingCommas = true, CommentHandling = JsonCommentHandling.Skip });
            var schools = new Dictionary<string, FxSchool>();
            foreach (var p in doc.RootElement.GetProperty("schools").EnumerateObject())
            {
                var s = p.Value;
                var bands = s.GetProperty("bands").EnumerateArray().Select(b => new FxBand(
                    b.GetProperty("name").GetString() ?? "", b.GetProperty("t").GetSingle(), Hex(b, p.Name),
                    b.GetProperty("L").GetSingle(), b.GetProperty("C").GetSingle(), b.GetProperty("h").GetSingle(),
                    UiLanguage.Floats(b.GetProperty("emit"), 3, p.Name + ".emit"))).ToList();
                if (bands.Count is not (2 or 3)) throw new InvalidDataException($"fx_language.json: {p.Name} has {bands.Count} bands (two or three)");
                for (int i = 1; i < bands.Count; i++)
                    if (!(bands[i].T > bands[i - 1].T) || bands[i].T >= 1) throw new InvalidDataException($"fx_language.json: {p.Name}'s band thresholds do not rise inside 0..1");
                var g = s.GetProperty("glow");
                var sp = s.GetProperty("sparks");
                schools[p.Name] = new FxSchool(p.Name, s.TryGetProperty("from", out var f) ? f.GetString() ?? "" : "", bands,
                    new FxGlow(Hex(g, p.Name), g.GetProperty("width").GetSingle(), g.GetProperty("reach").GetSingle(), g.GetProperty("head").GetSingle(), g.GetProperty("tail").GetSingle()),
                    new FxSparks(Hex(sp, p.Name), sp.GetProperty("count").GetInt32(), sp.GetProperty("length").GetSingle(), sp.GetProperty("aspect").GetSingle()));
            }
            return new FxLanguage { Schools = schools };
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException or FormatException)
        {
            throw new InvalidDataException("fx_language.json is malformed: " + e.Message, e);
        }
    }

    static string Hex(JsonElement e, string where)
    {
        var h = e.GetProperty("hex").GetString() ?? "";
        if (!UiLanguage.IsHex(h)) throw new InvalidDataException($"fx_language.json: {where} has a bad color '{h}'");
        return h;
    }

    /// <summary>A "#rrggbb" as linear RGB (the sRGB curve undone), each times its gain: what a shader is given.</summary>
    public static float[] Linear(string hex, float[]? gain = null)
    {
        var o = new float[3];
        for (int i = 0; i < 3; i++)
        {
            float c = int.Parse(hex.AsSpan(1 + 2 * i, 2), NumberStyles.HexNumber) / 255f;
            o[i] = (c <= 0.04045f ? c / 12.92f : MathF.Pow((c + 0.055f) / 1.055f, 2.4f)) * (gain?[i] ?? 1f);
        }
        return o;
    }
}

/// <summary>A painted block of the screens (bible rule 12): its field, its one highlight band (Band: its share of the
/// block's height), its ink outline.</summary>
public sealed record UiBlock(string Name, string From, string Field, string Highlight, string Ink, float Band);

/// <summary>The panel: a dark painted field (Field at its middle, FieldDeep at its edges) in a bronze frame (FrameWidth
/// px at 1080 lines), the frame's ink Line in px, Corner the corner plate's size, Grain the field's brush strength.</summary>
public sealed record UiPanel(string From, string Field, string FieldDeep, string Frame, float FrameWidth, float Line, float Corner, float Grain);

/// <summary>data/look/ui_language.json as plain data: the swatches (blocks, text, accents), the panel and the line weight.</summary>
public sealed class UiLanguage
{
    public IReadOnlyDictionary<string, UiBlock> Blocks { get; private init; } = new Dictionary<string, UiBlock>();
    public IReadOnlyDictionary<string, string> Text { get; private init; } = new Dictionary<string, string>();
    public IReadOnlyDictionary<string, string> Accents { get; private init; } = new Dictionary<string, string>();
    public UiPanel Panel { get; private init; } = null!;
    /// <summary>The ink outline's weight in px at 1080 lines.</summary>
    public float Line { get; private init; }

    public static UiLanguage Parse(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { AllowTrailingCommas = true, CommentHandling = JsonCommentHandling.Skip });
            var r = doc.RootElement;
            string H(JsonElement e, string k, string where)
            {
                var h = e.GetProperty(k).GetString() ?? "";
                if (!IsHex(h)) throw new InvalidDataException($"ui_language.json: {where}.{k} has a bad color '{h}'");
                return h;
            }
            var blocks = new Dictionary<string, UiBlock>();
            foreach (var p in r.GetProperty("blocks").EnumerateObject())
            {
                if (p.Value.ValueKind != JsonValueKind.Object) continue;
                blocks[p.Name] = new UiBlock(p.Name, p.Value.GetProperty("from").GetString() ?? "", H(p.Value, "field", p.Name), H(p.Value, "highlight", p.Name),
                    H(p.Value, "ink", p.Name), p.Value.GetProperty("band").GetSingle());
            }
            Dictionary<string, string> Swatches(string key) =>
                r.GetProperty(key).EnumerateObject().Where(p => p.Value.ValueKind == JsonValueKind.Object).ToDictionary(p => p.Name, p => H(p.Value, "hex", key + "." + p.Name));
            var pn = r.GetProperty("panel");
            return new UiLanguage
            {
                Blocks = blocks,
                Text = Swatches("text"),
                Accents = Swatches("accents"),
                Line = r.GetProperty("line").GetProperty("px").GetSingle(),
                Panel = new UiPanel(pn.GetProperty("from").GetString() ?? "", H(pn, "field", "panel"), H(pn, "field_deep", "panel"), H(pn, "frame", "panel"),
                    pn.GetProperty("frame_px").GetSingle(), pn.GetProperty("line_px").GetSingle(), pn.GetProperty("corner_px").GetSingle(), pn.GetProperty("grain").GetSingle()),
            };
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException or FormatException)
        {
            throw new InvalidDataException("ui_language.json is malformed: " + e.Message, e);
        }
    }

    internal static bool IsHex(string h) => h.Length == 7 && h[0] == '#' && h.Skip(1).All(Uri.IsHexDigit);

    internal static float[] Floats(JsonElement e, int n, string where)
    {
        var a = e.EnumerateArray().Select(x => x.GetSingle()).ToArray();
        if (n >= 0 && a.Length != n) throw new InvalidDataException($"{where}: {a.Length} numbers, not {n}");
        return a;
    }
}
