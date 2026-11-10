using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her clips' beats as data (godot/data/anim/her_events.json, written by the P4 pack, read by the views and M3): a built
/// P4 clip's top-level "beats" ({contact: [s], hold: [a, b], cancel: s, loop: [a, b], events: {name: s}}, clip SECONDS,
/// every key optional) become frames at 60 fps (round(s * 60)). The file: {"fps": 60, "clips": {clip: {...}}}, clips
/// sorted by name, keys in the order contact, hold, cancel, loop, events (events by frame), two-space indent.
/// Derivation: docs/team/ARPG_NOTES.md (A1 Stage B lead 4's block).
/// </summary>
public static class HerEvents
{
    public const int Fps = 60;

    /// <summary>One clip's beats in frames; null where a key is absent.</summary>
    public sealed record Beats(int[] Contact, int[]? Hold, int? Cancel, int[]? Loop, (string Name, int Frame)[] Events)
    {
        public bool Empty => Contact.Length == 0 && Hold == null && Cancel == null && Loop == null && Events.Length == 0;
        public static double Sec(int frame) => frame / (double)Fps;
        public double[] ContactSeconds => Contact.Select(Sec).ToArray();
        public (double A, double B)? HoldSeconds => Hold is { Length: 2 } ? (Sec(Hold[0]), Sec(Hold[1])) : null;
        public double? CancelSeconds => Cancel is int c ? Sec(c) : null;
        public (double A, double B)? LoopSeconds => Loop is { Length: 2 } ? (Sec(Loop[0]), Sec(Loop[1])) : null;
        /// <summary>A named event's time in seconds, or null.</summary>
        public double? EventSeconds(string name) => Events.Where(e => e.Name == name).Select(e => (double?)Sec(e.Frame)).FirstOrDefault();
    }

    static int Frame(double seconds) => (int)Math.Round(seconds * Fps, MidpointRounding.AwayFromZero);

    /// <summary>A built clip's "beats" object (clip seconds) as frames; null when the clip has none (or an empty object).</summary>
    public static Beats? FromClip(JsonElement clip)
    {
        if (clip.ValueKind != JsonValueKind.Object || !clip.TryGetProperty("beats", out var b) || b.ValueKind != JsonValueKind.Object) return null;
        int[] contact = Array.Empty<int>();
        if (b.TryGetProperty("contact", out var c) && c.ValueKind == JsonValueKind.Array)
            contact = c.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.Number).Select(x => Frame(x.GetDouble())).OrderBy(x => x).ToArray();
        int[]? Pair(string key)
        {
            if (!b.TryGetProperty(key, out var p) || p.ValueKind != JsonValueKind.Array) return null;
            var v = p.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.Number).Select(x => Frame(x.GetDouble())).ToArray();
            return v.Length == 2 ? v : null;
        }
        int? cancel = b.TryGetProperty("cancel", out var cc) && cc.ValueKind == JsonValueKind.Number ? Frame(cc.GetDouble()) : null;
        var ev = new List<(string, int)>();
        if (b.TryGetProperty("events", out var e) && e.ValueKind == JsonValueKind.Object)
            foreach (var p in e.EnumerateObject())
                if (p.Value.ValueKind == JsonValueKind.Number) ev.Add((p.Name, Frame(p.Value.GetDouble())));
        var beats = new Beats(contact, Pair("hold"), cancel, Pair("loop"), ev.OrderBy(x => x.Item2).ThenBy(x => x.Item1, StringComparer.Ordinal).ToArray());
        return beats.Empty ? null : beats;
    }

    /// <summary>The file's text for these clips (those without beats left out), sorted and indented so it diffs cleanly.</summary>
    public static string Serialize(IEnumerable<KeyValuePair<string, Beats>> clips)
    {
        var list = clips.Where(k => !k.Value.Empty).OrderBy(k => k.Key, StringComparer.Ordinal).ToList();
        var sb = new StringBuilder();
        sb.Append("{\n  \"fps\": ").Append(Fps).Append(",\n  \"clips\": {");
        if (list.Count == 0) { sb.Append("}\n}\n"); return sb.ToString(); }
        sb.Append('\n');
        for (int i = 0; i < list.Count; i++)
        {
            var (name, bt) = (list[i].Key, list[i].Value);
            var parts = new List<string>();
            if (bt.Contact.Length > 0) parts.Add($"\"contact\": [{string.Join(", ", bt.Contact)}]");
            if (bt.Hold != null) parts.Add($"\"hold\": [{bt.Hold[0]}, {bt.Hold[1]}]");
            if (bt.Cancel is int cn) parts.Add($"\"cancel\": {cn}");
            if (bt.Loop != null) parts.Add($"\"loop\": [{bt.Loop[0]}, {bt.Loop[1]}]");
            if (bt.Events.Length > 0) parts.Add("\"events\": {" + string.Join(", ", bt.Events.Select(e => $"{JsonSerializer.Serialize(e.Name)}: {e.Frame}")) + "}");
            sb.Append("    ").Append(JsonSerializer.Serialize(name)).Append(": {\n");
            for (int j = 0; j < parts.Count; j++) sb.Append("      ").Append(parts[j]).Append(j < parts.Count - 1 ? ",\n" : "\n");
            sb.Append("    }").Append(i < list.Count - 1 ? ",\n" : "\n");
        }
        sb.Append("  }\n}\n");
        return sb.ToString();
    }

    /// <summary>The file after a pack: `packed` (the pack's clips with beats) over `file` (what was there), less every
    /// entry of a clip the pack built (`built`: a packed clip that lost its beats loses its entry). Clips the pack does
    /// not build keep their entries (M3's measured contacts).</summary>
    public static Dictionary<string, Beats> Merge(IReadOnlyDictionary<string, Beats> file, IReadOnlyDictionary<string, Beats> packed, IEnumerable<string> built)
    {
        var gone = new HashSet<string>(built, StringComparer.Ordinal);
        var res = file.Where(k => !gone.Contains(k.Key)).ToDictionary(k => k.Key, k => k.Value);
        foreach (var k in packed) res[k.Key] = k.Value;
        return res;
    }

    /// <summary>The file's text read back: per clip its beats (frames; seconds through Beats members). Bad text gives none.</summary>
    public static Dictionary<string, Beats> Load(string text)
    {
        var res = new Dictionary<string, Beats>();
        if (string.IsNullOrWhiteSpace(text)) return res;
        try
        {
            using var d = JsonDocument.Parse(text);
            if (!d.RootElement.TryGetProperty("clips", out var clips) || clips.ValueKind != JsonValueKind.Object) return res;
            foreach (var c in clips.EnumerateObject())
            {
                int[]? Ints(string k) => c.Value.TryGetProperty(k, out var a) && a.ValueKind == JsonValueKind.Array ? a.EnumerateArray().Select(x => x.GetInt32()).ToArray() : null;
                var ev = new List<(string, int)>();
                if (c.Value.TryGetProperty("events", out var e) && e.ValueKind == JsonValueKind.Object)
                    foreach (var p in e.EnumerateObject()) ev.Add((p.Name, p.Value.GetInt32()));
                var hold = Ints("hold"); var loop = Ints("loop");
                res[c.Name] = new Beats(Ints("contact") ?? Array.Empty<int>(), hold is { Length: 2 } ? hold : null,
                    c.Value.TryGetProperty("cancel", out var cn) && cn.ValueKind == JsonValueKind.Number ? cn.GetInt32() : null,
                    loop is { Length: 2 } ? loop : null, ev.OrderBy(x => x.Item2).ThenBy(x => x.Item1, StringComparer.Ordinal).ToArray());
            }
        }
        catch (Exception ex) when (ex is JsonException or FormatException or InvalidOperationException) { res.Clear(); }
        return res;
    }
}
