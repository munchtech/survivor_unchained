using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SurvivorUnchained.Core;

/// <summary>
/// How the game reads and writes JSON: the web game's names (camelCase,
/// enums as their keys: 'active', 'lowHealth'), public fields included,
/// unset values left out. Content, saves and the settings all go through
/// these options.
/// </summary>
public static class Json
{
    public static readonly JsonSerializerOptions Options = Make();

    static JsonSerializerOptions Make()
    {
        var o = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DictionaryKeyPolicy = null,
            IncludeFields = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            ReadCommentHandling = JsonCommentHandling.Skip,
            AllowTrailingCommas = true,
            NumberHandling = JsonNumberHandling.AllowReadingFromString,
        };
        o.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.CamelCase));
        return o;
    }

    public static T Parse<T>(string json) => JsonSerializer.Deserialize<T>(json, Options) ?? throw new JsonException($"no {typeof(T).Name} in the JSON");
    public static string Write<T>(T value, bool indent = false) =>
        JsonSerializer.Serialize(value, indent ? new JsonSerializerOptions(Options) { WriteIndented = true } : Options);

    /// <summary>A deep copy, through JSON (the way the web game clones saves).</summary>
    public static T Clone<T>(T value) => Parse<T>(Write(value));

    /* ------------------------------------------------ where content lives -- */

    /// <summary>Reads a content file by name ('items.json'). The game points
    /// this at res://data/content (Godot's own file access, which works
    /// inside an exported pack); by default it finds godot/data/content on
    /// disk, for the tests.</summary>
    public static Func<string, string> ReadContent = DefaultRead;

    static string? contentDir;

    static string DefaultRead(string name)
    {
        contentDir ??= FindContentDir() ?? throw new DirectoryNotFoundException("data/content not found above " + AppContext.BaseDirectory);
        return File.ReadAllText(Path.Combine(contentDir, name));
    }

    static string? FindContentDir()
    {
        foreach (var start in new[] { AppContext.BaseDirectory, Directory.GetCurrentDirectory() })
            for (var d = new DirectoryInfo(start); d != null; d = d.Parent)
            {
                var a = Path.Combine(d.FullName, "data", "content");
                if (Directory.Exists(a)) return a;
                var b = Path.Combine(d.FullName, "godot", "data", "content");
                if (Directory.Exists(b)) return b;
            }
        return null;
    }
}

/// <summary>A value written either alone or as a list ('lore.x' or ['a', 'b']);
/// always a list here.</summary>
public sealed class OneOrMany<T> : JsonConverter<List<T>>
{
    public override List<T> Read(ref Utf8JsonReader r, Type t, JsonSerializerOptions o)
    {
        if (r.TokenType == JsonTokenType.StartArray) return JsonSerializer.Deserialize<List<T>>(ref r, o) ?? new();
        return new List<T> { JsonSerializer.Deserialize<T>(ref r, o)! };
    }

    public override void Write(Utf8JsonWriter w, List<T> v, JsonSerializerOptions o)
    {
        if (v.Count == 1) JsonSerializer.Serialize(w, v[0], o);
        else JsonSerializer.Serialize(w, v, o);
    }
}
