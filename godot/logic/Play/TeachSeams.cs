using System;

namespace SurvivorUnchained.Play;

/// <summary>The tutorial's seams (docs/story/TUTORIAL_COPY.md, M6): hooks other lanes set once their parts exist, so
/// the beats that wait on them (A5a, A6, A6b) can be asked. Unset, or returning nothing, each beat stays inert.
/// Set on the zone that teaches them (Prologue.Seams).</summary>
public sealed class TeachSeams
{
    /// <summary>skills-p7: the HUD target of the lamp's wick the level-up card offers now (Third Blow on Sunder), null: no lamp offer up (A5a).</summary>
    public Func<string?>? LampOffered;
    /// <summary>loot-m9: where the first pack's captain's first Rare lies with its beam (its label over it), null: none on the ground (A6).</summary>
    public Func<(double X, double Z)?>? RareOnGround;
    /// <summary>loot-m9: the loot filter key's label from her bindings, null: no binding yet (A6b stays inert).</summary>
    public Func<string?>? FilterKey;
    /// <summary>loot-m9: the HUD target of the filter key's chip (null: "filter") (A6b).</summary>
    public Func<string?>? FilterChip;
    /// <summary>loot-m9: how many common drops lie on the ground near her now (A6b asks at three or more).</summary>
    public Func<int>? CommonsOnGround;
}
