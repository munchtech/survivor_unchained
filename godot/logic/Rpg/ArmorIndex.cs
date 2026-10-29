using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Rpg;

/// <summary>How firmly a piece holds her (HerJiggle's Amount and Squash): plate over her breasts swings less and never squashes.</summary>
public sealed class ArmorHold
{
    [JsonPropertyName("amount")] public double Amount { get; set; } = 1;
    [JsonPropertyName("squash")] public double Squash { get; set; } = 1;
}

/// <summary>One wearable piece (docs/handoff/armor.md items 1 and 6): a row of art/people/armor_index.json (her callings'
/// outfits, heroine_outfits.py) or art/armor/armor_index.json (new pieces, tools/armor/build.py).</summary>
public sealed class ArmorPiece
{
    [JsonPropertyName("id")] public string Id { get; set; } = "";
    /// <summary>Pieces worn in this calling row's place when an equipped piece displaces it (a leotard that also clothes her groin: the arcanist's top): each fills its own visual slot unless that slot is equipped, hidden by an equipped piece's covers, or hidden by `hide`.</summary>
    [JsonPropertyName("under")] public List<string>? Under { get; set; }
    /// <summary>The calling's outfit it was cut from (null for a new piece).</summary>
    [JsonPropertyName("outfit")] public string? Outfit { get; set; }
    [JsonPropertyName("slot")] public string Slot { get; set; } = "";
    [JsonPropertyName("layer")] public int Layer { get; set; }
    /// <summary>The visual slots it hides while worn (its own among them).</summary>
    [JsonPropertyName("covers")] public List<string> Covers { get; set; } = new();
    /// <summary>Its meshes' names in its file (dots: Godot's import makes them underscores).</summary>
    [JsonPropertyName("meshes")] public List<string> Meshes { get; set; } = new();
    /// <summary>Its tuck of her skin, a path under its index's folder (null: it tucks nothing).</summary>
    [JsonPropertyName("tuck")] public string? Tuck { get; set; }
    [JsonPropertyName("tuck_count")] public int? TuckCount { get; set; }
    [JsonPropertyName("body_hash")] public string? BodyHash { get; set; }
    [JsonPropertyName("hold")] public ArmorHold? Hold { get; set; }
    /// <summary>A rigid piece (a plate style, or a free mesh made only of `_rigid` parts): the garment tuck never bends it
    /// (GarmentTuck.Over is false with it inner), so its plates keep their shape under any piece over it.</summary>
    [JsonPropertyName("rigid")] public bool Rigid { get; set; }
    /// <summary>Its own file (res://art/armor/ID.gltf) for a new piece; null: its outfit's heroine_outfit_OUTFIT.gltf.</summary>
    [JsonPropertyName("file")] public string? File { get; set; }
    [JsonPropertyName("tier")] public JsonElement? Tier { get; set; }
    /// <summary>What it does to her hair while worn: "keep" (default) or "hide" (a closed helm: her hair mesh is left off).</summary>
    [JsonPropertyName("hair")] public string Hair { get; set; } = "keep";
    /// <summary>The id of a calling's outfit row this piece stands in for: a calling's fill (ArmorIndex.Calling) wears this piece
    /// where it would wear that row. The piece keeps its own row.</summary>
    [JsonPropertyName("replaces")] public string? Replaces { get; set; }
    /// <summary>The index's folder under art/ ("people" or "armor"), which its tuck path is relative to.</summary>
    [JsonIgnore] public string Dir { get; set; } = "people";
}

/// <summary>Every wearable piece by id, from the two indexes (the second only when it exists).</summary>
public sealed class ArmorIndex
{
    public static readonly string[] Files = ["people/armor_index.json", "armor/armor_index.json"];

    /// <summary>An index's text by its path under art/, or null when it is not there. The game points it at res://art;
    /// by default it finds godot/art on disk, for the tests and tools.</summary>
    public static Func<string, string?> Text = rel =>
    {
        var p = Path.Combine(DataFiles.Dir, "..", "art", rel);
        return System.IO.File.Exists(p) ? System.IO.File.ReadAllText(p) : null;
    };

    static ArmorIndex? shared;

    /// <summary>The game's index, read once (empty if it cannot be read).</summary>
    public static ArmorIndex Shared
    {
        get
        {
            if (shared != null) return shared;
            try { shared = Load(Text); }
            catch (Exception e) { Console.Error.WriteLine("ArmorIndex: " + e.Message); shared = new ArmorIndex(); }
            return shared;
        }
    }

    /// <summary>Read again on next use (after Text changes).</summary>
    public static void Reset() => shared = null;

    public readonly Dictionary<string, ArmorPiece> Pieces = new();

    public ArmorPiece? Find(string id) => Pieces.GetValueOrDefault(id);

    /// <summary>A piece's visual slot: its row's, or (a piece not in the index) the part of its id after the last dot.</summary>
    public string SlotOf(string id) => Find(id)?.Slot is { Length: > 0 } s ? s : Wear.SlotOfId(id);

    /// <summary>Adds an index's rows (a later row with the same id replaces the earlier).</summary>
    public ArmorIndex Add(string json, string dir)
    {
        var rows = JsonSerializer.Deserialize<List<ArmorPiece>>(json, new JsonSerializerOptions { AllowTrailingCommas = true, ReadCommentHandling = JsonCommentHandling.Skip })
                   ?? throw new JsonException($"armor index ({dir}): no rows");
        foreach (var r in rows)
        {
            if (r.Id == "") throw new JsonException($"armor index ({dir}): a row with no id");
            if (r.Slot == "") r.Slot = Wear.SlotOfId(r.Id);
            if (r.Covers.Count == 0) r.Covers.Add(r.Slot);
            r.Dir = dir;
            Pieces[r.Id] = r;
        }
        return this;
    }

    public static ArmorIndex Parse(string json, string dir = "people") => new ArmorIndex().Add(json, dir);

    /// <summary>Both indexes through `text` (the second only if it is there).</summary>
    public static ArmorIndex Load(Func<string, string?> text)
    {
        var ix = new ArmorIndex();
        foreach (var f in Files)
            if (text(f) is string s) ix.Add(s, f[..f.IndexOf('/')]);
        return ix;
    }

    /// <summary>A calling's own pieces (its outfit's rows), by visual slot; a row another piece `replaces` is given as that piece.</summary>
    public Dictionary<string, string> Calling(string calling)
    {
        var own = Pieces.Values.Where(r => r.Outfit == calling).ToDictionary(r => r.Slot, r => r.Id);
        foreach (var r in Pieces.Values)
            if (r.Replaces is { } from && own.TryGetValue(r.Slot, out var cur) && cur == from) own[r.Slot] = r.Id;
        return own;
    }
}
