namespace SurvivorUnchained.Core;

/// <summary>Whether the developer's tuning variables (SU_TEETH, SU_TELLS, SU_BOARDS, SU_LAMPS_V2) are read.
/// On by default, so tests and the balance harnesses keep them; the game turns it to Args.Dev at start, so a
/// player's release build never takes a tuning file from the environment (Codex audit SU-007).</summary>
public static class DevOverrides
{
    public static bool On = true;

    /// <summary>The variable's value when overrides are on and it is set, else null.</summary>
    public static string? Env(string name) =>
        On && System.Environment.GetEnvironmentVariable(name) is { Length: > 0 } v ? v : null;
}
