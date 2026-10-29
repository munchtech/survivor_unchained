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
        /// <summary>One of our stones (env_rocks.py; kinds rock and pebble): drawn with the one stone material, no look of its kind's.</summary>
        public bool Stone => Kind is "rock" or "pebble";
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

    /// <summary>The kit piece's own pieces in this zone (its file's "own" over the game's), or null. A key "kind/piece"
    /// ("cliff/Rock_Medium_1") wins over the piece's own for copies of that kind (the kit's one rock is a field rock, a
    /// boulder or a cliff by its kind).</summary>
    public static string[]? OwnFor(string zone, string kitPiece, string? kind = null)
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
        if (kind != null && map.TryGetValue($"{kind}/{kitPiece}", out var ok)) return ok;
        return map.TryGetValue(kitPiece, out var o) ? o : null;
    }

    /// <summary>The one stone's data (flora_species.json "stone": its sheet, palette and OWN_ROCK's parameters).</summary>
    public static JsonElement Stone => stone ??= Load(Path).GetProperty("stone").Clone();
    static JsonElement? stone;

    /// <summary>flora_species.json "stands": how a dense stand of a kind (a zone's edge wall, a tree on every cell of its
    /// grid) is thinned into clumps and given its sizes (Dressing.Stands); none: as placed.</summary>
    public static JsonElement? Stands
    {
        get
        {
            if (!standsRead) { standsRead = true; stands = Load(Path).TryGetProperty("stands", out var v) ? v.Clone() : null; }
            return stands;
        }
    }
    static JsonElement? stands;
    static bool standsRead;

    /// <summary>A zone's causeways (its flora_species.json "causeways"; none if it has none): stepping stones laid by Dressing.</summary>
    public static JsonElement[] CausewaysFor(string zone)
    {
        var zp = $"res://data/zones/{zone}/flora_species.json";
        if (zone == "" || !FileAccess.FileExists(zp) || !Load(zp).TryGetProperty("causeways", out var c)) return [];
        var l = new List<JsonElement>();
        foreach (var e in c.EnumerateArray()) l.Add(e.Clone());
        return [.. l];
    }

    /// <summary>The grass kind this zone draws (flora_species.json "grass": its "use" and "kinds"; a zone's own file may
    /// set its own "use" or add kinds): the kind's JSON (atlas, palettes, card, cell, drift, shader).</summary>
    public static JsonElement GrassFor(string zone)
    {
        var root = Load(Path).GetProperty("grass");
        string use = root.GetProperty("use").GetString()!;
        var zp = $"res://data/zones/{zone}/flora_species.json";
        if (zone != "" && FileAccess.FileExists(zp) && Load(zp).TryGetProperty("grass", out var zg))
        {
            if (zg.TryGetProperty("use", out var u)) use = u.GetString()!;
            if (zg.TryGetProperty("kinds", out var zk) && zk.TryGetProperty(use, out var k)) return k.Clone();
        }
        return root.GetProperty("kinds").GetProperty(use).Clone();
    }

    /// <summary>(lf3b) A zone's own ground paint values (its flora_species.json "ground": terrain.gdshader uniform names to
    /// numbers, over Ground.cs's defaults; a --ground-* switch still wins); none if it has none.</summary>
    public static Dictionary<string, float> GroundFor(string zone)
    {
        var d = new Dictionary<string, float>();
        var zp = $"res://data/zones/{zone}/flora_species.json";
        if (zone == "" || !FileAccess.FileExists(zp) || !Load(zp).TryGetProperty("ground", out var g)) return d;
        foreach (var kv in g.EnumerateObject())
            if (kv.Value.ValueKind == JsonValueKind.Number) d[kv.Name] = kv.Value.GetSingle();
        return d;
    }

    /// <summary>(E8 later r2) A zone's footpaths for the ground (flora_species.json "ground_paths": polylines of [x, z]),
    /// as segments (x0, z0, x1, z1), twelve at most (terrain.gdshader path_seg).</summary>
    public static List<Vector4> PathsFor(string zone)
    {
        var l = new List<Vector4>();
        var zp = $"res://data/zones/{zone}/flora_species.json";
        if (zone == "" || !FileAccess.FileExists(zp) || !Load(zp).TryGetProperty("ground_paths", out var g)) return l;
        foreach (var line in g.EnumerateArray())
        {
            if (line.ValueKind != JsonValueKind.Array) continue;
            Vector2? last = null;
            foreach (var pt in line.EnumerateArray())
            {
                var p = new Vector2(pt[0].GetSingle(), pt[1].GetSingle());
                if (last is Vector2 q && l.Count < 12) l.Add(new Vector4(q.X, q.Y, p.X, p.Y));
                last = p;
            }
        }
        return l;
    }

    /// <summary>A species by its name ("stepping").</summary>
    public static Species Named(string name)
    {
        Ensure();
        return species!.TryGetValue(name, out var s) ? s : throw new KeyNotFoundException($"flora_species.json: no species {name}");
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
