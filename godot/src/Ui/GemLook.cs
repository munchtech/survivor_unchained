using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>A support gem's colour (bd-ui W11, W16): clear for the ones that fit any skill, sapphire for Shield's, garnet
/// for Melee's, and bicolor (a stone split garnet and sapphire; its light and label #B37AB6, the blend #9A4E9E lifted
/// 25% toward white) for the ones that fit both. One place, so the socket panel and the loot read the same stone.</summary>
public static class GemLook
{
    public static Color Of(SupportDef g) => new(SocketModel.GemHex(g));

    /// <summary>The two body colours of a bicolor stone (garnet half, sapphire half).</summary>
    public static readonly Color BicolorGarnet = new("#C42B3A"), BicolorSapphire = new("#3F7FD8");
}
