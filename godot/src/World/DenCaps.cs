using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (den r14, judge r13 item 4) One budget per screen for the props that read as repeats: the decals (DenDecals) and the
/// painted set (SetOpen, SetLitter) both ask here before laying a deer skull, a rib cage, a log, ... A kind may lie only
/// while fewer than its cap already lie within its radius, so any camera footprint (about 30 x 18 m at pitch 62, distance
/// 24) holds about the cap of it. Cleared once per dressing (DungeonDress.Dress). --den-caps 0 turns every cap off.
/// </summary>
public static class DenCaps
{
    static readonly bool On = SurvivorUnchained.Args.Num("den-caps", 1f) > 0f;
    static readonly Dictionary<string, List<Vector2>> laid = new();

    public static void Clear() => laid.Clear();

    /// <summary>True (and counted) if one more <paramref name="kind"/> may lie at p: fewer than cap within radius.</summary>
    public static bool Take(string kind, Vector2 p, int cap, float radius)
    {
        if (!laid.TryGetValue(kind, out var l)) laid[kind] = l = new();
        if (On)
        {
            int n = 0;
            float r2 = radius * radius;
            foreach (var q in l) if (q.DistanceSquaredTo(p) < r2 && ++n >= cap) return false;
        }
        l.Add(p);
        return true;
    }

    /// <summary>How many of a kind were laid (for the dressing's counts and tests).</summary>
    public static int Count(string kind) => laid.TryGetValue(kind, out var l) ? l.Count : 0;
}
