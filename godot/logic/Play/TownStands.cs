namespace SurvivorUnchained.Play;

/// <summary>
/// The armed townsfolk at ease, and the town's stands kept out of step. The Watch, Wenna and Keegan stand in their own
/// folk clips (tools/anim/clips/folk_armed.py), asked for by name in the town's data only: the bosses' and the fights'
/// armed idles ("Idle_Shield_Loop", "2H_Melee_Idle") keep the library's.
/// </summary>
public static class TownStands
{
    /// <summary>The folk clip (without its "f_"/"m_") for an armed stand's game name, or null for any other:
    /// "Idle_Armed", a one-handed piece hanging easy in the right fist (the gate Watch's sword, Wenna's staff);
    /// "Idle_2H_Rest", a two-handed blade resting on the right shoulder (Keegan).</summary>
    public static string? Armed(string game) => game switch
    {
        "Idle_Armed" => "idle_armed",
        "Idle_2H_Rest" => "idle_2h",
        _ => null,
    };

    /// <summary>Where in its loop a townsperson's first stand starts (0..1), from who or where they are: the same each
    /// time the town is built, but no two neighbours sway in step (FNV-1a over the key).</summary>
    public static double Phase(string key)
    {
        uint h = 2166136261;
        foreach (char c in key) { h ^= c; h *= 16777619; }
        h ^= h >> 15; h *= 2246822519; h ^= h >> 13;
        return (h % 10007) / 10007.0;
    }
}
