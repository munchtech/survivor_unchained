using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace SurvivorUnchained.Viewer;

/// <summary>
/// What a package folder's look is made of: its manifest.json and every file the manifest names, as the game's
/// NpcPackage reads them (body.glb, each piece's file, default armor/ID.glb, the hair file, the baked lod), hashed
/// into one fingerprint. A record of which package a frame shows, and the look viewer's test that two frames had the
/// same input.
/// </summary>
public static class PackageFingerprint
{
    /// <summary>The files a manifest names, relative to its folder, manifest.json first; null: not a manifest.</summary>
    public static List<string>? Files(string manifestJson)
    {
        JsonDocument doc;
        try { doc = JsonDocument.Parse(manifestJson); }
        catch (JsonException) { return null; }
        using (doc)
        {
            var r = doc.RootElement;
            if (r.ValueKind != JsonValueKind.Object) return null;
            var files = new List<string> { "manifest.json" };
            void Add(string f) { f = f.Replace('\\', '/'); if (f != "" && !files.Contains(f)) files.Add(f); }
            Add(r.TryGetProperty("body", out var b) && b.ValueKind == JsonValueKind.String ? b.GetString()! : "body.glb");
            if (r.TryGetProperty("pieces", out var ps) && ps.ValueKind == JsonValueKind.Array)
                foreach (var p in ps.EnumerateArray())
                {
                    if (p.ValueKind != JsonValueKind.Object) continue;
                    if (p.TryGetProperty("file", out var f) && f.ValueKind == JsonValueKind.String) Add(f.GetString()!);
                    else if (p.TryGetProperty("id", out var id) && id.ValueKind == JsonValueKind.String) Add($"armor/{id.GetString()}.glb");
                }
            foreach (var key in new[] { "hair", "lod" })
                if (r.TryGetProperty(key, out var h) && h.ValueKind == JsonValueKind.Object && h.TryGetProperty("file", out var hf) && hf.ValueKind == JsonValueKind.String)
                    Add(hf.GetString()!);
            return files;
        }
    }

    public sealed record Entry(string File, long Size, string Sha256);

    /// <summary>(fingerprint, the files, the named files missing). read(relative path) gives a file's bytes or null.</summary>
    public static (string Hash, List<Entry> Files, List<string> Missing) Compute(Func<string, byte[]?> read)
    {
        var man = read("manifest.json") ?? throw new LookError("no manifest.json");
        var names = Files(Encoding.UTF8.GetString(man)) ?? throw new LookError("manifest.json is not a JSON object");
        var entries = new List<Entry>();
        var missing = new List<string>();
        var all = new StringBuilder();
        foreach (var n in names)
        {
            var bytes = n == "manifest.json" ? man : read(n);
            if (bytes == null) { missing.Add(n); all.Append(n).Append(" missing\n"); continue; }
            var sha = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
            entries.Add(new Entry(n, bytes.LongLength, sha));
            all.Append(n).Append(' ').Append(sha).Append('\n');
        }
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(all.ToString()))).ToLowerInvariant();
        return (hash, entries, missing);
    }

    /// <summary>One hash over a folder's files (relative path, size, content), e.g. godot/shaders: the shader fingerprint.</summary>
    public static string Tree(IEnumerable<(string Rel, byte[] Bytes)> files)
    {
        var all = new StringBuilder();
        foreach (var (rel, bytes) in files.OrderBy(f => f.Rel, StringComparer.Ordinal))
            all.Append(rel.Replace('\\', '/')).Append(' ').Append(Convert.ToHexString(SHA256.HashData(bytes))).Append('\n');
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(all.ToString()))).ToLowerInvariant()[..16];
    }
}
