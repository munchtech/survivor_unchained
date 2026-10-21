using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>Our own flora's species and which kit pieces they stand for (godot/data/flora_species.json, a zone's
/// own file merged over it): how each is drawn (its file, LODs, cells, shadow, wind) and its material's parameters.
/// The art is tools/assets/env_trees.py's.</summary>
public static class FloraSpecies
{
    public sealed record Species(string Name, string[] Pieces, bool Packed, string Kind, float[] Lod, float End, float Cell, bool Shadow, float? Wind,
        Dictionary<string, JsonElement> Shader)
    {
        /// <summary>A piece's file (without .gltf) and its index in it (0 when each piece is its own file).</summary>
        public (string File, int Variant) FileOf(string piece) => Packed ? (Name, System.Array.IndexOf(Pieces, piece)) : (piece, 0);
        public bool Broadleaf => Shader.TryGetValue("broadleaf", out var b) && b.GetDouble() > 0;
    }

    const string Path = "res://data/flora_species.json";
    static Dictionary<string, Species>? species;
    static readonly Dictionary<string, Dictionary<string, string[]>> own = new();
    static readonly Dictionary<string, Species> byPiece = new();

    static JsonElement Load(string path) => JsonDocument.Parse(FileAccess.GetFileAsString(path)).RootElement;

    static Species Read(string name, JsonElement e)
    {
        var pieces = new List<string>();
        foreach (var p in e.GetProperty("pieces").EnumerateArray()) pieces.Add(p.GetString()!);
        var lod = new List<float>();
        if (e.TryGetProperty("lod", out var l)) foreach (var x in l.EnumerateArray()) lod.Add(x.GetSingle());
        var sh = new Dictionary<string, JsonElement>();
        if (e.TryGetProperty("shader", out var s)) foreach (var kv in s.EnumerateObject()) sh[kv.Name] = kv.Value.Clone();
        float F(string k, float d) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetSingle() : d;
        return new Species(name, [.. pieces], e.TryGetProperty("packed", out var pk) && pk.GetBoolean(), e.TryGetProperty("kind", out var k) ? k.GetString()! : name,
            [.. lod], F("end", 0), F("cell", 24), !e.TryGetProperty("shadow", out var sd) || sd.GetBoolean(),
            e.TryGetProperty("wind", out var w) && w.ValueKind == JsonValueKind.Number ? w.GetSingle() : null, sh);
    }

    static void Ensure()
    {
        if (species != null) return;
        species = new();
        var root = Load(Path);
        foreach (var kv in root.GetProperty("species").EnumerateObject()) species[kv.Name] = Read(kv.Name, kv.Value);
        foreach (var sp in species.Values) foreach (var p in sp.Pieces) byPiece[p] = sp;
        own[""] = OwnMap(root, new());
    }

    static Dictionary<string, string[]> OwnMap(JsonElement root, Dictionary<string, string[]> into)
    {
        if (root.TryGetProperty("own", out var o))
            foreach (var kv in o.EnumerateObject())
            {
                if (kv.Value.ValueKind == JsonValueKind.Array) { var l = new List<string>(); foreach (var x in kv.Value.EnumerateArray()) l.Add(x.GetString()!); into[kv.Name] = [.. l]; }
                else into[kv.Name] = [kv.Value.GetString()!];
            }
        return into;
    }

    /// <summary>The kit piece's own pieces in this zone (its file's "own" over the game's), or null.</summary>
    public static string[]? OwnFor(string zone, string kitPiece)
    {
        Ensure();
        if (!own.TryGetValue(zone, out var map))
        {
            map = new(own[""]);
            var zp = $"res://data/zones/{zone}/flora_species.json";
            if (zone != "" && FileAccess.FileExists(zp))
            {
                var root = Load(zp);
                OwnMap(root, map);
                // (a zone's species entries override the game's, whole, by name)
                if (root.TryGetProperty("species", out var sps))
                    foreach (var kv in sps.EnumerateObject()) { var sp = Read(kv.Name, kv.Value); species![kv.Name] = sp; foreach (var p in sp.Pieces) byPiece[p] = sp; }
            }
            own[zone] = map;
        }
        return map.TryGetValue(kitPiece, out var o) ? o : null;
    }

    /// <summary>The species a piece of ours belongs to ("spruce_a": spruce).</summary>
    public static Species Of(string piece)
    {
        Ensure();
        return byPiece.TryGetValue(piece, out var s) ? s : throw new KeyNotFoundException($"flora_species.json: no species has the piece {piece}");
    }

    /// <summary>A species by its material's name (Leaves_Own&lt;Species&gt;), or null.</summary>
    public static Species? ByMaterial(string material)
    {
        Ensure();
        int i = material.IndexOf("Own");
        if (i < 0) return null;
        var n = material[(i + 3)..].ToLowerInvariant();
        int dot = n.IndexOfAny(['.', '_', ' ']);
        if (dot > 0) n = n[..dot];
        return species!.TryGetValue(n, out var s) ? s : null;
    }
}
