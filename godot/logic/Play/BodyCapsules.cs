using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Play;

/// <summary>
/// The body's capsules a worn piece's springs are kept off (View/PieceSprings): bone to bone, each sized from the body
/// mesh by the vertices its carrier bones carry most at the bind (its first bone's when none are named): the legs a
/// hanging piece swings against, the pelvis and spine it drapes over, and the upper arms a shoulder plate rides. Her
/// rig's upper arm skin is carried by its twist and share bones, not the upper arm's own (R&D her-springs, B: 54 mm L,
/// 55 mm R over 1,317 vertices pooled), so those pool. Data, for every body: a capsule whose bones a body lacks is left
/// out, a carrier it lacks is skipped. Engine-free: the tests hold it.
/// </summary>
public static class BodyCapsules
{
    public readonly record struct Row(string A, string B, string[] Carry);

    public static readonly Row[] Table =
    {
        new("thigh_l", "calf_l", new[] { "thigh_l" }), new("calf_l", "foot_l", new[] { "calf_l" }),
        new("thigh_r", "calf_r", new[] { "thigh_r" }), new("calf_r", "foot_r", new[] { "calf_r" }),
        new("pelvis", "spine_01", new[] { "pelvis" }), new("spine_01", "spine_02", new[] { "spine_01" }),
        new("spine_02", "spine_03", new[] { "spine_02" }), new("spine_03", "neck_01", new[] { "spine_03" }),
        new("upperarm_l", "lowerarm_l", UpperArm("l")), new("upperarm_r", "lowerarm_r", UpperArm("r")),
    };

    static string[] UpperArm(string s) => new[] { $"upperarm_{s}", $"upperarm_twist_01_{s}", $"upperarm_twist_02_{s}",
        $"upperarm_twist_03_{s}", $"upperarm_twist_04_{s}", $"upperarm_share_{s}" };

    /// <summary>Fewest vertices a capsule is sized from; under that it is left out.</summary>
    public const int MinVerts = 20;
    public const float MinR = 0.03f, MaxR = 0.3f;

    /// <summary>A capsule's radius from its vertices' distances off its segment (sorted here): their 80th percentile
    /// (robe and all), clamped; null when too few.</summary>
    public static float? Radius(List<float> dist)
    {
        if (dist.Count < MinVerts) return null;
        dist.Sort();
        return Math.Clamp(dist[(int)(dist.Count * 0.8f)], MinR, MaxR);
    }
}
