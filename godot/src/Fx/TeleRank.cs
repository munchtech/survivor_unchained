using System;
using System.Text.Json;

namespace SurvivorUnchained.View;

/// <summary>The telegraph rank table (godot/data/content/tele_rank.json), plain C# so a test can read it.
/// Rank 1 (boss) and rank 2 (crowd) are reserved hues her own effects never use. Fallbacks equal the data.</summary>
public sealed partial class TeleRank
{
    public sealed record Row(int Rank, string Name, string Color, string Bed, double Edge, double Fill, double Flare, double Raise, double Charge, double Closing);

    public Row[] Rows { get; }
    TeleRank(Row[] rows) { Rows = rows; }

    public Row Boss => Of("boss");
    public Row Crowd => Of("crowd");
    public Row Ground => Of("ground");
    public Row Of(string name) { foreach (var r in Rows) if (r.Name == name) return r; throw new InvalidOperationException("tele_rank: no row " + name); }

    public static readonly string Fallback = """
{"ranks":[
 {"rank":0,"name":"safe","color":"#8ad0ff","bed":"#10202a","edge":2.2},
 {"rank":0,"name":"wall","color":"#c8c8d0","bed":"#18181a","edge":1.6},
 {"rank":1,"name":"boss","color":"#ff0612","bed":"#2c0604","edge":0.45,"fill":0.55,"flare":1.4},
 {"rank":2,"name":"crowd","color":"#ff1a4a","bed":"#2a0610","edge":0.22,"fill":0.6,"flare":1.3,"raise":0.5,"charge":0.22,"closing":0.5},
 {"rank":3,"name":"ground","color":"#a050ff","bed":"#140a24","edge":2.2}]}
""";

    public static TeleRank Parse(string json)
    {
        using var doc = JsonDocument.Parse(string.IsNullOrWhiteSpace(json) ? Fallback : json);
        var list = new System.Collections.Generic.List<Row>();
        double N(JsonElement e, string k) => e.TryGetProperty(k, out var v) ? v.GetDouble() : 0;
        foreach (var e in doc.RootElement.GetProperty("ranks").EnumerateArray())
            list.Add(new Row(e.GetProperty("rank").GetInt32(), e.GetProperty("name").GetString()!, e.GetProperty("color").GetString()!,
                e.GetProperty("bed").GetString()!, N(e, "edge"), N(e, "fill"), N(e, "flare"), N(e, "raise"), N(e, "charge"), N(e, "closing")));
        return new TeleRank(list.ToArray());
    }
}
