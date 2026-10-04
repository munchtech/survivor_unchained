using System.Collections.Generic;

namespace SurvivorUnchained.View;

/// <summary>
/// How a survivor's own clips are named (OwnClips: hers and his): by the
/// calling, from the outfit worn, and by what is held.
/// </summary>
public static class HerClips
{
    /// <summary>The calling, from the outfit worn ("her:ranger" or "him:ranger" is the stalker's).</summary>
    public static string Calling(IEnumerable<string>? outfit)
    {
        if (outfit == null) return "";
        foreach (var o in outfit)
            if (o.StartsWith("her:") || o.StartsWith("him:")) return o[4..] == "ranger" ? "stalker" : o[4..];
        return "";
    }

    /// <summary>What is held, as the clips name it.</summary>
    public static string Kind(string? right, string? left, string? forearm) => right switch
    {
        "chevalier_sword" or "viking_sword" or "longsword" => "sword",
        "viking_axe" or "snake_axe" => left is "viking_axe" or "snake_axe" ? "axes" : "axe",
        "mage_staff" or "short_staff" => "staff",
        "wand" => "wand",
        "crossbow" => "crossbow",
        "daggers" => "daggers",
        _ => "",
    };

    /// <summary>The swings for what is held: alternate cuts, the first
    /// from the left to the right as the game's first arc sweeps.</summary>
    public static string[] Swings(string kind) => kind switch
    {
        "sword" => new[] { "sword_back", "sword_fore" },
        "axe" => new[] { "axe_back", "axe_fore" },
        "axes" => new[] { "axes_left", "axes_right" },
        "daggers" => new[] { "daggers_back", "daggers_fore" },
        _ => System.Array.Empty<string>(),
    };

    public static string Heavy(string kind) => kind switch
    {
        "sword" => "sword_heavy", "axe" => "axe_heavy", "axes" => "axes_heavy", "daggers" => "daggers_heavy", _ => "",
    };
}
