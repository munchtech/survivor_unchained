using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Nodes;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* The combat skills as data (data/content/skills.json): every weapon with its
 * evolutions nested under it, then the unions that join two of them. A new
 * skill is an entry here, plus a behavior in the runtime only if none of the
 * existing ones does what it needs. Rules ride on the same trigger format
 * items and lamps use ({ "do": "execute", ... }, Sim/ProcsJson.cs).
 *
 * The file is written by Write (the round trip the tests hold stable): unset
 * and default fields left out, the keys in a reading order, and short
 * objects and lists kept on one line so a skill reads as a block. */

public sealed class SkillsFile
{
    public List<WeaponDef> Skills = new();
    public List<UnionDef> Unions = new();
}

public static class SkillsJson
{
    static SkillsFile? file;

    /// <summary>skills.json, read once on first use (after the game has pointed
    /// DataFiles at its own pack).</summary>
    public static SkillsFile File => file ??= Parse(Json.ReadContent("skills.json"));

    public static SkillsFile Parse(string json) => Json.Parse<SkillsFile>(json);

    /* Reading order for a skill's and an evolution's keys; anything not named
     * keeps its place after these. */
    static readonly string[] SkillKeys = ["id", "name", "school", "behavior", "tags", "findable", "growth", "bossDamage", "art", "description", "base", "triggers", "evolutions"];
    static readonly string[] EvoKeys = ["id", "name", "catalysts", "description", "behavior", "school", "addTags", "art", "mods", "set", "triggers"];
    static readonly string[] UnionKeys = ["id", "name", "a", "b", "into", "description"];

    public static string Write(SkillsFile f)
    {
        var root = JsonNode.Parse(Json.Write(f))!.AsObject();
        var defaults = JsonNode.Parse(Json.Write(new WeaponDef()))!.AsObject();
        var skills = new JsonArray();
        foreach (var s in root["skills"]!.AsArray().ToList())
        {
            var o = Prune(s!.AsObject())!;
            // A skill's own defaults (not findable, the usual growth) go; the
            // identity keys stay even when they are the enum's first value.
            foreach (var k in new[] { "findable", "growth" })
                if (o[k] is JsonNode v && defaults[k] is JsonNode d && JsonNode.DeepEquals(v, d)) o.Remove(k);
            if (o["evolutions"] is JsonArray evos)
            {
                var ordered = new JsonArray();
                foreach (var e in evos.ToList()) { evos.Remove(e); ordered.Add(Order(e!.AsObject(), EvoKeys)); }
                o["evolutions"] = ordered;
            }
            skills.Add(Order(o, SkillKeys));
        }
        var unions = new JsonArray();
        foreach (var u in root["unions"]!.AsArray().ToList()) unions.Add(Order(Prune(u!.AsObject())!, UnionKeys));
        var top = new JsonObject { ["skills"] = skills, ["unions"] = unions };
        var sb = new StringBuilder();
        Format(top, sb, 0);
        return sb.Append('\n').ToString();
    }

    /// <summary>Empty strings, lists and objects and a status's stack=false
    /// left out: reading fills them back in as the defaults they are.</summary>
    static JsonObject? Prune(JsonObject o)
    {
        foreach (var (k, v) in o.ToList())
        {
            JsonNode? keep = v switch
            {
                JsonObject c => Prune(c),
                JsonArray a => PruneArray(a),
                JsonValue s when s.TryGetValue<string>(out var str) && str.Length == 0 => null,
                JsonValue b when k == "stack" && b.TryGetValue<bool>(out var flag) && !flag => null,
                _ => v,
            };
            if (keep == null) o.Remove(k);
            else if (!ReferenceEquals(keep, v)) o[k] = keep;
        }
        return o.Count == 0 ? null : o;
    }

    static JsonArray? PruneArray(JsonArray a)
    {
        if (a.Count == 0) return null;
        for (int i = 0; i < a.Count; i++)
            if (a[i] is JsonObject c)
            {
                if (Prune(c) == null) a[i] = new JsonObject();
            }
        return a;
    }

    static JsonObject Order(JsonObject o, string[] keys)
    {
        var n = new JsonObject();
        var props = o.ToList();
        o.Clear();
        foreach (var k in keys)
            foreach (var (pk, pv) in props)
                if (pk == k) n[pk] = pv;
        foreach (var (pk, pv) in props)
            if (!keys.Contains(pk)) n[pk] = pv;
        return n;
    }

    static readonly JsonSerializerOptions Leaf = new() { Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
    const int Width = 118;

    /* An object or list goes on one line when it fits, otherwise one entry a line. */
    static void Format(JsonNode? n, StringBuilder sb, int depth)
    {
        string pad = new(' ', 2 * depth), inner = new(' ', 2 * (depth + 1));
        if (n is JsonObject or JsonArray)
        {
            var flat = Inline(n);
            if (depth > 0 && flat.Length + 2 * depth <= Width) { sb.Append(flat); return; }
        }
        switch (n)
        {
            case JsonObject o:
                sb.Append("{\n");
                int i = 0;
                foreach (var (k, v) in o)
                {
                    sb.Append(inner).Append(JsonSerializer.Serialize(k, Leaf)).Append(": ");
                    Format(v, sb, depth + 1);
                    sb.Append(++i < o.Count ? ",\n" : "\n");
                }
                sb.Append(pad).Append('}');
                break;
            case JsonArray a:
                sb.Append("[\n");
                for (int j = 0; j < a.Count; j++)
                {
                    sb.Append(inner);
                    Format(a[j], sb, depth + 1);
                    sb.Append(j + 1 < a.Count ? ",\n" : "\n");
                }
                sb.Append(pad).Append(']');
                break;
            default:
                sb.Append(n == null ? "null" : n.ToJsonString(Leaf));
                break;
        }
    }

    static string Inline(JsonNode? n) => n switch
    {
        JsonObject o => o.Count == 0 ? "{}" : "{ " + string.Join(", ", o.Select(p => JsonSerializer.Serialize(p.Key, Leaf) + ": " + Inline(p.Value))) + " }",
        JsonArray a => "[" + string.Join(", ", a.Select(Inline)) + "]",
        null => "null",
        _ => n.ToJsonString(Leaf),
    };
}
