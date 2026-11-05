using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace SurvivorUnchained.Look;

/// <summary>A class's cel numbers (the per-material uniforms of shaders/cel.gdshaderinc).</summary>
public sealed record CelPreset(float[] Band, float[] Mid, float Form, float[] Spec, float Nmap, int Ink, float RimK);

/// <summary>One cel class of data/look/materials.json. Mid = paint.measured.mid ("#rrggbb") or null.</summary>
public sealed record LookClass(string Name, string From, CelPreset Cel, float[]? Sheen, float[]? Edge, string? Mid);

/// <summary>One assign rule: every given pattern must match.</summary>
public sealed record AssignRule(string Class, Regex? Shader, Regex? Material, Regex? Path);

/// <summary>The material library (data/look/materials.json) as plain data; no Godot types.</summary>
public sealed class MaterialLibrary
{
    public IReadOnlyDictionary<string, LookClass> Classes { get; private init; } = new Dictionary<string, LookClass>();
    public string Fallback { get; private init; } = "";
    public IReadOnlyDictionary<string, string> Shaders { get; private init; } = new Dictionary<string, string>();
    public IReadOnlyList<AssignRule> Assign { get; private init; } = Array.Empty<AssignRule>();
    public IReadOnlyList<(string What, Regex? Shader, Regex? Material)> Exclude { get; private init; } =
        Array.Empty<(string, Regex?, Regex?)>();

    public static MaterialLibrary Parse(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { AllowTrailingCommas = true, CommentHandling = JsonCommentHandling.Skip });
            var root = doc.RootElement;
            var classes = new Dictionary<string, LookClass>();
            foreach (var p in root.GetProperty("classes").EnumerateObject())
            {
                var c = p.Value;
                var cel = c.GetProperty("cel");
                var preset = new CelPreset(
                    Floats(cel.GetProperty("band"), 4, p.Name + ".cel.band"),
                    Floats(cel.GetProperty("mid"), 4, p.Name + ".cel.mid"),
                    cel.GetProperty("form").GetSingle(),
                    Floats(cel.GetProperty("spec"), 4, p.Name + ".cel.spec"),
                    cel.GetProperty("nmap").GetSingle(),
                    cel.GetProperty("ink").GetInt32(),
                    cel.GetProperty("rim_k").GetSingle());
                float[]? sheen = c.TryGetProperty("sheen", out var sh) ? Floats(sh, -1, p.Name + ".sheen") : null;
                float[]? edge = c.TryGetProperty("edge", out var ed) ? Floats(ed, -1, p.Name + ".edge") : null;
                string? mid = null;
                if (c.TryGetProperty("paint", out var paint) && paint.TryGetProperty("measured", out var ms)
                    && ms.TryGetProperty("mid", out var mv) && mv.ValueKind == JsonValueKind.String) mid = mv.GetString();
                classes[p.Name] = new LookClass(p.Name, c.TryGetProperty("from", out var f) ? f.GetString() ?? "" : "", preset, sheen, edge, mid);
            }
            var shaders = new Dictionary<string, string>();
            foreach (var p in root.GetProperty("shaders").EnumerateObject()) shaders[p.Name] = p.Value.GetString() ?? "";
            var assign = new List<AssignRule>();
            foreach (var a in root.GetProperty("assign").EnumerateArray())
                assign.Add(new AssignRule(a.GetProperty("class").GetString() ?? "", Rx(a, "shader"), Rx(a, "material"), Rx(a, "path")));
            var exclude = new List<(string, Regex?, Regex?)>();
            if (root.TryGetProperty("exclude", out var ex))
                foreach (var e in ex.EnumerateArray())
                {
                    var s = Rx(e, "shader"); var m = Rx(e, "material");
                    if (s == null && m == null) continue;
                    exclude.Add((e.TryGetProperty("what", out var w) ? w.GetString() ?? "" : "", s, m));
                }
            return new MaterialLibrary
            {
                Classes = classes,
                Fallback = root.GetProperty("fallback").GetString() ?? "",
                Shaders = shaders,
                Assign = assign,
                Exclude = exclude,
            };
        }
        catch (Exception e) when (e is JsonException or KeyNotFoundException or InvalidOperationException or FormatException or ArgumentException)
        {
            throw new InvalidDataException("materials.json is malformed: " + e.Message, e);
        }
    }

    static Regex? Rx(JsonElement o, string key) =>
        o.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String && !string.IsNullOrEmpty(v.GetString())
            ? new Regex(v.GetString()!, RegexOptions.Compiled | RegexOptions.CultureInvariant) : null;

    static float[] Floats(JsonElement a, int len, string what)
    {
        var r = a.EnumerateArray().Select(x => x.GetSingle()).ToArray();
        if (len >= 0 && r.Length != len) throw new FormatException($"{what} needs {len} numbers, has {r.Length}");
        return r;
    }

    /// <summary>The first rule whose every given pattern matches; null if none.</summary>
    public string? ClassFor(string? shaderPath, string? materialName, string? assetPath)
    {
        foreach (var r in Assign)
            if (M(r.Shader, shaderPath) && M(r.Material, materialName) && M(r.Path, assetPath)) return r.Class;
        return null;
    }

    /// <summary>An exclude entry's shader OR material pattern matches.</summary>
    public bool Excluded(string? shaderPath, string? materialName)
    {
        foreach (var e in Exclude)
            if ((e.Shader != null && !string.IsNullOrEmpty(shaderPath) && e.Shader.IsMatch(shaderPath))
                || (e.Material != null && !string.IsNullOrEmpty(materialName) && e.Material.IsMatch(materialName))) return true;
        return false;
    }

    static bool M(Regex? rx, string? input) => rx == null || (!string.IsNullOrEmpty(input) && rx.IsMatch(input));
}
