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
    /// <summary>B's springs' support under this piece (P1Jiggle.Support): 0 bare .. 1 push-up (stiffer, better damped,
    /// shorter reach, lifted and pressed in: godot/data/body/springs.json "support"). Null: from amount (0.55, plate's,
    /// is 1; 1 is 0).</summary>
    [JsonPropertyName("support")] public double? Support { get; set; }
    [JsonIgnore] public double SupportValue => Support ?? Math.Clamp((1 - Amount) / 0.45, 0, 1);
    /// <summary>Per-piece shape drivers for B's body (blend shapes form_support_lift / _press / _fill): each null = the support value (push-up 1/1/1).</summary>
    [JsonPropertyName("lift")] public double? Lift { get; set; }
    [JsonPropertyName("press")] public double? Press { get; set; }
    [JsonPropertyName("fill")] public double? Fill { get; set; }
    [JsonIgnore] public double LiftValue => Lift ?? SupportValue;
    [JsonIgnore] public double PressValue => Press ?? SupportValue;
    [JsonIgnore] public double FillValue => Fill ?? SupportValue;
}

/// <summary>One spring link of a piece (PieceSprings.Link): a bone from head to tail under its parent (a body bone or
/// another link), its collision radius and, over 0, its own stiffness (1/s); reach: how far off the link its vertices
/// are carried (null: the piece's carry reach).</summary>
public sealed class SpringRow
{
    [JsonPropertyName("bone")] public string Bone { get; set; } = "";
    [JsonPropertyName("parent")] public string Parent { get; set; } = "";
    [JsonPropertyName("head")] public double[] Head { get; set; } = new double[3];
    [JsonPropertyName("tail")] public double[] Tail { get; set; } = new double[3];
    [JsonPropertyName("radius")] public double Radius { get; set; } = 0.04;
    [JsonPropertyName("stiffness")] public double Stiffness { get; set; }
    [JsonPropertyName("reach")] public double? Reach { get; set; }
}

/// <summary>One corrective shape of a piece (PieceSprings.Corrective): 0 at From degrees of the bone's pitch, 1 at To.</summary>
public sealed class CorrectiveRow
{
    [JsonPropertyName("shape")] public string Shape { get; set; } = "";
    [JsonPropertyName("bone")] public string Bone { get; set; } = "";
    [JsonPropertyName("axis")] public string Axis { get; set; } = "pitch";
    [JsonPropertyName("from")] public double From { get; set; }
    [JsonPropertyName("to")] public double To { get; set; } = 90;
    [JsonPropertyName("ref")] public string? Ref { get; set; }
}

/// <summary>One piece's springs in the springs file (ArmorIndex.SpringsFile), with where its numbers came from.</summary>
public sealed class SpringsEntry
{
    [JsonPropertyName("id")] public string Id { get; set; } = "";
    [JsonPropertyName("source")] public string? Source { get; set; }
    [JsonPropertyName("springs")] public List<SpringRow>? Springs { get; set; }
    [JsonPropertyName("correctives")] public List<CorrectiveRow>? Correctives { get; set; }
    [JsonPropertyName("carry")] public CarryRow? Carry { get; set; }
}

/// <summary>A piece's carry onto its springs (Play/SpringCarry): rule "island" (a welded island goes whole to the link
/// whose region holds at least `share` of it: metal plates) or "blend" (each vertex by its place down the link: cloth);
/// reach in metres.</summary>
public sealed class CarryRow
{
    [JsonPropertyName("rule")] public string Rule { get; set; } = "island";
    [JsonPropertyName("reach")] public double Reach { get; set; } = 0.06;
    [JsonPropertyName("share")] public double Share { get; set; } = 0.6;
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
    /// <summary>Its tuck record's full scale, mm (gear_tuck.py: a row says it only when it is not 10, the shader's): a
    /// point's depth is its mark times this (SkinTuck.Merge).</summary>
    [JsonPropertyName("tuck_depth_mm")] public double TuckDepthMm { get; set; } = 10;
    /// <summary>TuckDepthMm as the merge takes it (a row saying 0 or less: 10).</summary>
    [JsonIgnore] public float TuckDepth => TuckDepthMm > 0 ? (float)TuckDepthMm : 10f;
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
    /// <summary>Its spring bones (View/PieceSprings, as a Marionette package piece's manifest has them): each link a bone
    /// added to her skeleton under its parent, swung over her finished pose and kept off her body's capsules. Head and
    /// tail in its file's armature frame, metres. Null: it has none.</summary>
    [JsonPropertyName("springs")] public List<SpringRow>? Springs { get; set; }
    /// <summary>Its corrective shapes driven by a bone's pitch (PieceSprings), as a package piece's.</summary>
    [JsonPropertyName("correctives")] public List<CorrectiveRow>? Correctives { get; set; }
    /// <summary>How its vertices are given to its spring bones at dress time (Play/SpringCarry), when its file's skin does
    /// not already weight them (a piece built for its springs, a package's, is used as it is). Null: the island rule.</summary>
    [JsonPropertyName("carry")] public CarryRow? Carry { get; set; }
    /// <summary>Where its springs came from (the springs file's "source"; null: its own row's).</summary>
    [JsonIgnore] public string? SpringsSource { get; set; }
    [JsonIgnore] public bool HasSprings => Springs is { Count: > 0 } || Correctives is { Count: > 0 };
    /// <summary>The index's folder under art/ ("people" or "armor"), which its tuck path is relative to.</summary>
    [JsonIgnore] public string Dir { get; set; } = "people";
    /// <summary>A built body's gear row (tools/armor/gear_fit.py build, art/gear/out/BODY/gear_index.json): its calling's
    /// play-tier unit (BODY/CALLING.lod.gltf), which HerLod lays for the calling's full set.</summary>
    [JsonPropertyName("lod_file")] public string? LodFile { get; set; }
    /// <summary>A gear index's play-tier unit row (no slot: never worn as a piece; ArmorIndex.AddGear leaves it out).</summary>
    [JsonPropertyName("lod")] public bool Lod { get; set; }
    /// <summary>A row of a built body's gear index (art/gear/out/BODY): its pieces are that body's own.</summary>
    [JsonIgnore] public bool Gear => Dir.StartsWith("gear/", StringComparison.Ordinal);
    /// <summary>Its tuck of her skin as a res:// path (null: it tucks nothing).</summary>
    [JsonIgnore] public string? TuckPath => Tuck == null ? null : $"res://art/{Dir}/{Tuck}";
    /// <summary>Its cover of her (tools/armor/cover.py, gear_tuck.py) as a res:// path, beside its tuck.</summary>
    [JsonIgnore] public string CoverPath => $"res://art/{Dir}/armor_cover/{Id}.bin";
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

    /// <summary>A built body's gear folder under art/ (gear/out/BODY: --body p1, P1Body.GearDir): its gear_index.json is read
    /// INSTEAD of the two A indexes. Null: A's (nothing changes for A).</summary>
    public static string? GearDir;

    /// <summary>Load asked for a gear folder whose gear_index.json is not there: this index is A's.</summary>
    public bool GearMissing { get; private set; }

    /// <summary>The game's index, read once (empty if it cannot be read).</summary>
    public static ArmorIndex Shared
    {
        get
        {
            if (shared != null) return shared;
            try { shared = Load(Text, GearDir); }
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

    /// <summary>Her callings' pieces' springs, kept apart from the index heroine_outfits.py writes (a source, not an
    /// output): [{id, source, springs, correctives, carry}].</summary>
    public const string SpringsFile = "people/springs.json";

    /// <summary>A springs file's entries onto A's rows (the two indexes': never a built body's gear) that have none of
    /// their own (a row that comes with springs, R&D's or a built body's, keeps them); returns how many rows took springs.</summary>
    public int AddSprings(string json)
    {
        var rows = JsonSerializer.Deserialize<List<SpringsEntry>>(json, new JsonSerializerOptions { AllowTrailingCommas = true, ReadCommentHandling = JsonCommentHandling.Skip })
                   ?? new List<SpringsEntry>();
        int n = 0;
        foreach (var e in rows)
        {
            if (!Pieces.TryGetValue(e.Id, out var r) || !Files.Any(f => f.StartsWith(r.Dir + "/")) || r.Springs != null || r.Correctives != null) continue;
            r.Springs = e.Springs; r.Correctives = e.Correctives; r.Carry ??= e.Carry; r.SpringsSource = e.Source;
            n++;
        }
        return n;
    }

    /// <summary>Both indexes through `text` (the second only if it is there); with `gearDir`, that built body's gear index
    /// instead (A's when it is not there: GearMissing).</summary>
    public static ArmorIndex Load(Func<string, string?> text, string? gearDir = null)
    {
        var ix = new ArmorIndex();
        if (gearDir != null)
        {
            if (text($"{gearDir}/gear_index.json") is string g) return ix.AddGear(g, gearDir);
            ix.GearMissing = true;
        }
        foreach (var f in Files)
            if (text(f) is string s) ix.Add(s, f[..f.IndexOf('/')]);
        if (text(SpringsFile) is string sp) ix.AddSprings(sp);
        return ix;
    }

    /// <summary>A built body's gear index ({"body", "body_hash", "rows": [...]}, rows as the A indexes have them, `file` and
    /// `tuck` that body's own): its pieces, each row's Dir the gear folder; the calling play-tier unit rows left out.</summary>
    public ArmorIndex AddGear(string json, string dir)
    {
        using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { AllowTrailingCommas = true, CommentHandling = JsonCommentHandling.Skip });
        if (!doc.RootElement.TryGetProperty("rows", out var rows) || rows.ValueKind != JsonValueKind.Array)
            throw new JsonException($"gear index ({dir}): no rows");
        var keep = rows.EnumerateArray().Where(r => !(r.TryGetProperty("lod", out var l) && l.ValueKind == JsonValueKind.True)).ToList();
        return Add(JsonSerializer.Serialize(keep), dir);
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
