namespace SurvivorUnchained.View;

/// <summary>Draw order of ground decals, in ONE place (Decal.SortingOffset: a larger offset draws over a smaller one where
/// decals overlap). What is on screen is ranked (docs/design/ARPG_FUN.md P0 item 4): corpses, gore and her lingering
/// ground never cover an enemy's telegraph. Gore.cs numbers its splats 0 .. SplatMax*0.001 (0.18), under Scars.</summary>
public static class DecalLayer
{
    /// <summary>Gore's top (its i*0.001 offsets stay under this).</summary>
    public const float Gore = 0f;
    /// <summary>Scars (burns, cuts in the ground) over gore.</summary>
    public const float Scar = 0.3f;
    /// <summary>Her lingering ground effects (a consecration, a warden ground, a disc's glow): over gore and scars.</summary>
    public const float HerGround = 0.6f;
    /// <summary>A hostile telegraph's edge and bed (any rank): over everything above. Its fill sits just over it.</summary>
    public const float Telegraph = 2f, TelegraphFill = 2.01f;
}
