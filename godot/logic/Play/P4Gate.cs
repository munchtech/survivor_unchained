using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>
/// The P4 pack's gate (tools_scenes/P4Pack.cs): which built clips (body_p1/p4/*.json) go into p4_clips.res. The game lays
/// that file over the shipped bridge clips, so an unjudged clip would replace a walk or idle nobody approved. A clip is
/// judged when tools/anim/p4.py stamped a top-level "judged" with verdict PASS and the build hash it was judged at (the
/// stamp is dropped when the clip changes). The default pack takes judged clips only; a review pack (--review) takes all,
/// for shots and judges in a worktree.
/// </summary>
public static class P4Gate
{
    /// <summary>True when the clip carries a "judged" object with verdict "PASS" and a non-empty "build".</summary>
    public static bool Judged(JsonElement clip) =>
        clip.ValueKind == JsonValueKind.Object && clip.TryGetProperty("judged", out var j) && j.ValueKind == JsonValueKind.Object &&
        j.TryGetProperty("verdict", out var v) && v.ValueKind == JsonValueKind.String && v.GetString() == "PASS" &&
        j.TryGetProperty("build", out var b) && b.ValueKind == JsonValueKind.String && !string.IsNullOrEmpty(b.GetString());

    /// <summary>A review pack takes every clip; the default takes judged ones.</summary>
    public static bool Takes(JsonElement clip, bool review) => review || Judged(clip);

    /// <summary>True when the pack's user args hold --review.</summary>
    public static bool Review(string[] args) => args.Contains("--review");
}
