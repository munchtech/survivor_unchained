using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Play;

/// <summary>
/// P4 clips (SOMA motion retargeted onto B: tools/anim/p4.py, packed into body_p1/p4_clips.res) laid over B's bridge
/// clips (her_clips.res, A's clips baked onto B). The rules: a P4 clip with a bridge clip's name wins (the rebuilt clip
/// replaces the baked one, nothing else changes); a P4 clip with a new name is added; and the dev flag
/// --p4-as target=p4clip[,...] plays a P4 clip under a name the game already asks for (idle_warden_town=p4_demo_idle)
/// without renaming files or touching the animation tree. An alias to a missing P4 clip is ignored (reported).
/// Derivation: (a) the A1 brief (P4 core + first proof on B).
/// </summary>
public static class P4Overlay
{
    /// <summary>Per name the merged library takes from P4, the P4 clip it plays. Bridge names not in the plan stay.</summary>
    public static Dictionary<string, string> Plan(IEnumerable<string> bridge, IEnumerable<string> p4, string? alias, List<string>? rejected = null)
    {
        var have = new HashSet<string>(p4);
        var plan = have.ToDictionary(n => n, n => n);
        foreach (var (target, clip) in ParseAlias(alias))
        {
            if (have.Contains(clip)) plan[target] = clip;
            else rejected?.Add($"{target}={clip}");
        }
        return plan;
    }

    /// <summary>"a=b,c=d" -> (a, b), (c, d); malformed parts skipped.</summary>
    public static IEnumerable<(string Target, string Clip)> ParseAlias(string? alias)
    {
        if (string.IsNullOrWhiteSpace(alias)) yield break;
        foreach (var part in alias.Split(','))
        {
            var kv = part.Split('=');
            if (kv.Length == 2 && kv[0].Trim() != "" && kv[1].Trim() != "") yield return (kv[0].Trim(), kv[1].Trim());
        }
    }

    /// <summary>A clip's ground speed on B: the P4 clip's own (its locked stance, packed as the animation's "speed" meta)
    /// where the plan lays one under that name, else the bridge clip's (heroine_clips.json).</summary>
    public static float Speed(string clip, IReadOnlyDictionary<string, float> p4Speeds, float bridge)
        => p4Speeds.TryGetValue(clip, out var v) && v > 0 ? v : bridge;
}
