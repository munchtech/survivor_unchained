from ed import sub
sub('logic/Rpg/Crafting.cs', [
("""/// <summary>A draught brewed: what it takes, the gold, who brews it.</summary>
public sealed class BrewRule { public string Draught = ""; public Dictionary<string, int> Takes = new(); public int Gold; public string Crafter = "wenna"; }""",
"""/// <summary>A draught brewed: what it takes, the gold, who brews it, and the crafter's lines for it
/// (Say: its own lines in turn, "brew.antidote"; Moment: a line said the first time, "brew.moonpetal").</summary>
public sealed class BrewRule { public string Draught = ""; public Dictionary<string, int> Takes = new(); public int Gold; public string Crafter = "wenna"; public string? Say, Moment; }"""),
("""    public static Said? Speak(CraftCtx x, string crafter, Verb v, string? moment = null)
    {""",
"""    public static Said? Speak(CraftCtx x, string crafter, Verb v, string? moment = null, string? say = null)
    {"""),
("""        n.Flags[flag] = true;
        return Line(crafter, key, (int)n.Flag("crafted").Number) is { } l ? new Said(null, l, null) : null;""",
"""        n.Flags[flag] = true;
        return Line(crafter, say != null && Line(crafter, say) != null ? say : key, (int)n.Flag("crafted").Number) is { } l ? new Said(null, l, null) : null;"""),
("""    /// <summary>The line a craft writes on a piece, in the crafter's hand if they have one.</summary>
    static string History(CraftCtx x, string crafter, string key, string fallback)
    {
        string who = Crafter(crafter)?.Name ?? crafter;
        // The night the coal came out of: what lets Act 3 name it.
        string night = x.World.Fact("shards.from").Str is { Length: > 0 } s ? (s.StartsWith("The ") ? "the " + s[4..] : s) : "the night";
        return (Line(crafter, $"history.{key}") ?? fallback).Replace("{who}", who).Replace("{day}", $"{x.World.Day}").Replace("{night}", night);
    }""",
"""    /// <summary>The line a craft writes on a piece, in the crafter's hand if they have one.</summary>
    static string History(CraftCtx x, string crafter, string key, string fallback) => History(x.World, crafter, key, fallback);

    /// <summary>The same, for a piece made in a conversation (Maeca's braid: a "made" give).</summary>
    public static string History(WorldState w, string crafter, string key, string fallback = "Made by {who}, day {day}")
    {
        string who = Crafter(crafter)?.Name ?? crafter;
        // The night the coal came out of: what lets Act 3 name it.
        string night = w.Fact("shards.from").Str is { Length: > 0 } s ? (s.StartsWith("The ") ? "the " + s[4..] : s) : "the night";
        return (Line(crafter, $"history.{key}") ?? fallback).Replace("{who}", who).Replace("{day}", $"{w.Day}").Replace("{night}", night);
    }"""),
])
