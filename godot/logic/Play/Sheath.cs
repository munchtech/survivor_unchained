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

    /// <summary>The own clips to try, in order, for a stand or a run ("idle", "run") of a calling holding a kind. Sheathed:
    /// the kind's own town clip (idle_arcanist_staff_town), then the calling's
    /// (idle_arcanist_town; skipped for a kind that stays in her hand: its free-armed town clips are not for it), then the armed ones. Drawn: the kind's (idle_stalker_daggers), then the calling's.</summary>
    public static string[] Names(string stem, string calling, string kind, bool sheathed) => sheathed
        ? (StaysInHand(kind)
            ? [$"{stem}_{calling}_{kind}_town", $"{stem}_{calling}_{kind}", $"{stem}_{calling}"]
            : [$"{stem}_{calling}_{kind}_town", $"{stem}_{calling}_town", $"{stem}_{calling}_{kind}", $"{stem}_{calling}"])
        : [$"{stem}_{calling}_{kind}", $"{stem}_{calling}"];

    /// <summary>The walk clips to try, in order: Names("walk"), except that a drawn kind with its own run but no walk of
    /// its own gets none (the calling's walk is built for the calling's default weapon, in the wrong hands).</summary>
    public static string[] WalkNames(string calling, string kind, bool sheathed, System.Func<string, bool> has) =>
        !sheathed && has($"run_{calling}_{kind}") && !has($"walk_{calling}_{kind}") ? [] : Names("walk", calling, kind, sheathed);

    /// <summary>Whether a calling holding a kind has a town stand (and so sheathes in a safe place).</summary>
    public static bool HasTown(string calling, string kind, System.Func<string, bool> has) =>
        has($"idle_{calling}_{kind}_town") || (!StaysInHand(kind) && has($"idle_{calling}_town"));

    /// <summary>A kind with no sheathed socket (the staff) stays in her hand, so the calling's town stand, made
    /// for empty hands, does not do for it.</summary>
    static bool StaysInHand(string kind)
    {
        var k = WeaponSockets.Parse(kind);
        return k != WeaponKind.None && WeaponSockets.SocketOf(k) == null;
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
