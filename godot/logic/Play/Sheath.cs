namespace SurvivorUnchained.Play;

/// <summary>
/// Whether she carries her weapons sheathed (in a safe place, with nothing hostile near and her not acting) or
/// drawn, decided here without the engine (PlayerView mounts the pieces and picks the town clips). She sheathes
/// after After seconds of continuous quiet; she draws at once on a threat, on leaving the safe place, or on acting
/// (an attack, a skill, a cast). Entering a place: sheathed at once if it is safe, with no clip.
/// </summary>
public sealed class Sheath
{
    /// <summary>Seconds of continuous safe, no threat, not acting before she sheathes.</summary>
    public const double After = 1.5;

    public bool Sheathed { get; private set; }
    double quiet;

    /// <summary>The clip to play for a stop, a break or a sprint: the town one (base + "_town" + suffix) while sheathed,
    /// else the armed one (base + suffix). Null when sheathed and the town clip does not exist (play nothing, or
    /// for the sprint fall back to the town run). base is e.g. "stop_warden", suffix e.g. "_l" or "".</summary>
    public static string? Pick(bool sheathed, string baseName, string suffix, System.Func<string, bool> has)
    {
        if (!sheathed) return baseName + suffix;
        var town = baseName + "_town" + suffix;
        return has(town) ? town : null;
    }

    /// <summary>A new place: sheathed at once where it is safe, drawn otherwise.</summary>
    public void Enter(bool safe)
    {
        Sheathed = safe;
        quiet = safe ? After : 0;
    }

    /// <summary>One frame; true when the state changed this frame.</summary>
    public bool Update(double dt, bool safe, bool threat, bool acting)
    {
        bool was = Sheathed;
        if (!safe || threat || acting)
        {
            quiet = 0;
            Sheathed = false;
        }
        else
        {
            quiet += dt;
            if (quiet >= After) Sheathed = true;
        }
        return Sheathed != was;
    }
}
