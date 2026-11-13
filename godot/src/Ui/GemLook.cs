using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>A support gem's colour (bd-ui W11): clear for the ones that fit any skill, sapphire for Shield's, garnet
/// otherwise. One place, so the socket panel and the loot read the same stone.</summary>
public static class GemLook
{
    public static Color Of(SupportDef g) => new(SocketModel.GemHex(g));
}
