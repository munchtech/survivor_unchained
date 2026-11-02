using System;

namespace SurvivorUnchained.World;

/// <summary>
/// A package NPC's arm set over the shared town clips (art/npc/NAME/manifest.json "arms": {"in": DEG, "wrist": SHARE}):
/// how far each upper arm is brought in toward the body (degrees, in the chest's frontal plane, never past Floor from
/// hanging straight) and how much of the clip's wrist bend is let go toward the rest (0 the clip, 1 a straight wrist).
/// For a body whose full sleeves read wider than the clip's arms were set for (the townswoman, NPC 15), so the shared
/// walk stays as it is for everyone else.
/// </summary>
public static class NpcArmSet
{
    /// <summary>The closest an arm is brought to hanging straight down in the frontal plane, degrees.</summary>
    public const float Floor = 6f;
    /// <summary>The most a manifest may ask, degrees in; the most of the wrist let go.</summary>
    public const float MaxIn = 30f, MaxWrist = 1f;

    /// <summary>The turn in (degrees) for an arm the clip holds Abduction degrees out in the frontal plane.</summary>
    public static float TurnIn(float abduction, float wantIn) =>
        Math.Clamp(Math.Min(Math.Clamp(wantIn, 0f, MaxIn), abduction - Floor), 0f, MaxIn);

    /// <summary>A manifest's (or a shot's "IN,WRIST") values, clamped; (0, 0) for none.</summary>
    public static (float In, float Wrist) Parse(string? s)
    {
        if (string.IsNullOrWhiteSpace(s)) return (0f, 0f);
        var p = s.Split(',');
        float a = 0f, w = 0f;
        var ci = System.Globalization.CultureInfo.InvariantCulture; var ns = System.Globalization.NumberStyles.Float;
        if (p.Length > 0) float.TryParse(p[0], ns, ci, out a);
        if (p.Length > 1) float.TryParse(p[1], ns, ci, out w);
        return (Math.Clamp(a, 0f, MaxIn), Math.Clamp(w, 0f, MaxWrist));
    }
}
