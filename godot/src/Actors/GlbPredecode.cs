using System;
using System.Collections.Concurrent;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading.Tasks;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>A glb's embedded images decoded on all cores before GltfDocument reads it (it decodes them one at a time,
/// most of a 200 MB package's load). The same decoders Godot picks (the image's mimeType: png or jpeg, else png then
/// jpeg), handed back through GltfDocumentExtension._ParseImageData, so the scene is the same, only sooner; an image it
/// did not decode falls through to Godot's own.</summary>
public partial class GlbPredecode : GltfDocumentExtension
{
    static readonly ConcurrentDictionary<(int Len, ulong Hash), Image> ready = new();

    /// <summary>Decodes `glb`'s images (a binary glTF: its JSON chunk's images by bufferView into the BIN chunk);
    /// returns how many. Nothing (0) for a .gltf or a glb it cannot read.</summary>
    public static int Decode(byte[] glb)
    {
        ready.Clear();
        if (glb.Length < 20 || BitConverter.ToUInt32(glb, 0) != 0x46546C67) return 0;
        int jsonLen = BitConverter.ToInt32(glb, 12);
        if (BitConverter.ToUInt32(glb, 16) != 0x4E4F534A || 20 + jsonLen + 8 > glb.Length) return 0;
        int binAt = 20 + jsonLen + 8;
        if (BitConverter.ToUInt32(glb, 20 + jsonLen + 4) != 0x004E4942) return 0;
        using var doc = JsonDocument.Parse(glb.AsMemory(20, jsonLen));
        var root = doc.RootElement;
        if (!root.TryGetProperty("images", out var images) || !root.TryGetProperty("bufferViews", out var views)) return 0;
        var jobs = new System.Collections.Generic.List<(int At, int Len, string Mime)>();
        foreach (var im in images.EnumerateArray())
        {
            if (!im.TryGetProperty("bufferView", out var bv)) continue;
            var v = views[bv.GetInt32()];
            if (v.TryGetProperty("buffer", out var b) && b.GetInt32() != 0) continue;
            int off = v.TryGetProperty("byteOffset", out var o) ? o.GetInt32() : 0;
            int len = v.GetProperty("byteLength").GetInt32();
            if (binAt + off + len > glb.Length) continue;
            jobs.Add((binAt + off, len, im.TryGetProperty("mimeType", out var mt) ? mt.GetString() ?? "" : ""));
        }
        Parallel.ForEach(jobs, j =>
        {
            var bytes = glb.AsSpan(j.At, j.Len).ToArray();
            var img = new Image();
            if (j.Mime == "image/png") img.LoadPngFromBuffer(bytes);
            else if (j.Mime == "image/jpeg") img.LoadJpgFromBuffer(bytes);
            if (img.IsEmpty()) img.LoadPngFromBuffer(bytes);
            if (img.IsEmpty()) img.LoadJpgFromBuffer(bytes);
            if (!img.IsEmpty()) ready[(j.Len, Hash(bytes))] = img;
        });
        return ready.Count;
    }

    public static void Clear() => ready.Clear();

    public override Error _ParseImageData(GltfState state, byte[] imageData, string mimeType, Image retImage)
    {
        if (ready.TryGetValue((imageData.Length, Hash(imageData)), out var img)) retImage.CopyFrom(img);
        return Error.Ok;
    }

    /// <summary>FNV-1a over 8-byte words (and the tail bytes): a key, not a security hash.</summary>
    static ulong Hash(ReadOnlySpan<byte> data)
    {
        ulong h = 14695981039346656037UL;
        var words = MemoryMarshal.Cast<byte, ulong>(data);
        foreach (var w in words) h = (h ^ w) * 1099511628211UL;
        for (int i = words.Length * 8; i < data.Length; i++) h = (h ^ data[i]) * 1099511628211UL;
        return h;
    }
}
