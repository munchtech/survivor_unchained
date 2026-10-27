namespace SurvivorUnchained.World;

/// <summary>
/// The walks a Marionette package's manifest may name ("walk": NAME in art/npc/NAME/manifest.json), as the game clip
/// the crowd's own motion stands in for (View.FolkClips.Crowd): "lurch", the risen's undead lurch (the library's
/// zombie walk's name). Any other name, or none: the townsfolk's walk.
/// </summary>
public static class NpcWalks
{
    public const string Lurch = "lurch";

    /// <summary>The game clip a manifest's walk stands for, or null (the townsfolk's walk).</summary>
    public static string? GameClip(string? walk) => walk switch
    {
        Lurch => "Zombie_Walk_Fwd_Loop",
        _ => null,
    };
}
