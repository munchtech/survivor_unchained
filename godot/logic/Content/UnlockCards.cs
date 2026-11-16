using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* One row per unlock on each calling's ladder (data/content/unlock_cards.json; BUILD_UNLOCKS.md): what its level-up card says
 * (title, line, icon) and the lesson that follows it (Play/UnlockLessons.cs). Which skill opens at which level stays in
 * taught_builds.json; a test holds that the two agree. */

/// <summary>The lesson after a card: when (next_fight | first_fire | none), the hint's title and text, the Act whose key it names.</summary>
public sealed class UnlockTeach
{
    public string When = "none", Title = "", Text = "", Key = "";
    public bool NextFight => When == "next_fight";
}

public sealed class UnlockCard
{
    public int Level = 1;
    /// <summary>key | auto | stance | road.</summary>
    public string Kind = "", Id = "", Lands = "", Title = "", Line = "", Icon = "";
    /// <summary>The starting kit (key 1 and auto 1 at level 1): no level-up card.</summary>
    public bool Start;
    public UnlockTeach Teach = new();
}

public static class UnlockCards
{
    static Dictionary<string, List<UnlockCard>>? all;

    /// <summary>The rows by calling ("_" keys are notes).</summary>
    public static IReadOnlyDictionary<string, List<UnlockCard>> All => all ??= Parse(Json.ReadContent("unlock_cards.json"));

    public static Dictionary<string, List<UnlockCard>> Parse(string json)
    {
        var d = new Dictionary<string, List<UnlockCard>>();
        foreach (var (k, v) in JsonNode.Parse(json)!.AsObject())
            if (!k.StartsWith('_') && v != null) d[k] = v.Deserialize<List<UnlockCard>>(Json.Options)!;
        return d;
    }

    /// <summary>A calling's rows in ladder order (none for a calling without any).</summary>
    public static IReadOnlyList<UnlockCard> Rows(string? calling) =>
        calling != null && All.TryGetValue(calling, out var r) ? r : System.Array.Empty<UnlockCard>();

    /// <summary>The row a level opens (the first that is not the starting kit; null when none).</summary>
    public static UnlockCard? At(string? calling, int level) => Rows(calling).FirstOrDefault(r => r.Level == level && !r.Start);

    /// <summary>The row of a skill (or "stance", "road") of a calling, null when it has none.</summary>
    public static UnlockCard? Of(string? calling, string id) => Rows(calling).FirstOrDefault(r => r.Id == id);

    /// <summary>The row of a skill id in any calling (the card's line for a skill: LevelCards.Line).</summary>
    public static UnlockCard? ForSkill(string id) => All.Values.SelectMany(r => r).FirstOrDefault(r => r.Id == id && r.Kind is "key" or "auto");
}
