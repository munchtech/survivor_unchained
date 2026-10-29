using System;
using System.Collections.Generic;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>A weapon row read from art/weapons/weapons.json: the data form of an Arms.Spec (docs/anim/GRIP_STANDARD.md
/// section 4). Lean is already defaulted by kind.</summary>
public sealed record WeaponRow(string Id, string File, float Length, WeaponKind Kind, string? Node, bool Pistol, float Lean, float Grip);

/// <summary>Reads weapons.json. A new weapon of a known kind is a row here, not a row of C#.</summary>
public static class WeaponsData
{
    /// <summary>The lean a kind's grip takes when the row gives none (as the Arms rows do).</summary>
    public static float DefaultLean(WeaponKind kind) => kind switch
    {
        // The one-handed axe and the wand are held in the blade's fist (BladeDirR, anim-40).
        WeaponKind.Blade1H or WeaponKind.Axe or WeaponKind.Wand => 35,
        WeaponKind.Dagger or WeaponKind.Blunt => 30,
        _ => 0,
    };

    /// <summary>A weapon's file as a resource path: a row's own "res://..." path (our own props under art/, NPC 18's smith
    /// hammer), else the name of a glb in res://assets/weapons.</summary>
    public static string ResPath(string file) => file.StartsWith("res://", StringComparison.Ordinal) ? file : $"res://assets/weapons/{file}.glb";

    /// <summary>Adds each row to the table unless its id is already there (a C# row wins); returns how many were added.</summary>
    public static int Merge<T>(IDictionary<string, T> table, IEnumerable<WeaponRow> rows, Func<WeaponRow, T> make)
    {
        int n = 0;
        foreach (var r in rows) if (table.TryAdd(r.Id, make(r))) n++;
        return n;
    }

    /// <summary>The rows in a json text (null or malformed text gives none; a row with no file, or no length, is skipped).</summary>
    public static List<WeaponRow> Parse(string? json)
    {
        var rows = new List<WeaponRow>();
        if (string.IsNullOrWhiteSpace(json)) return rows;
        try
        {
            using var doc = JsonDocument.Parse(json);
            if (doc.RootElement.ValueKind != JsonValueKind.Object) return rows;
            foreach (var p in doc.RootElement.EnumerateObject())
            {
                var e = p.Value;
                if (e.ValueKind != JsonValueKind.Object) continue;
                if (!e.TryGetProperty("file", out var f) || f.ValueKind != JsonValueKind.String) continue;
                if (!e.TryGetProperty("length", out var l) || !l.TryGetSingle(out var length) || length <= 0) continue;
                var kind = e.TryGetProperty("kind", out var k) && k.ValueKind == JsonValueKind.String ? WeaponSockets.Parse(k.GetString()) : WeaponKind.None;
                string? node = e.TryGetProperty("node", out var n) && n.ValueKind == JsonValueKind.String ? n.GetString() : null;
                bool pistol = e.TryGetProperty("pistol", out var pi) && pi.ValueKind == JsonValueKind.True;
                float lean = e.TryGetProperty("lean", out var le) && le.ValueKind == JsonValueKind.Number && le.TryGetSingle(out var lv) ? lv : DefaultLean(kind);
                float grip = e.TryGetProperty("grip", out var g) && g.ValueKind == JsonValueKind.Number && g.TryGetSingle(out var gv) ? gv : 0.2f;
                rows.Add(new WeaponRow(p.Name, f.GetString()!, length, kind, node, pistol, lean, grip));
            }
        }
        catch (JsonException) { }
        return rows;
    }
}
