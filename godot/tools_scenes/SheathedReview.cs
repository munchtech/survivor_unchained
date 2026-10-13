using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// For tools_scenes/anim_review.gd with SHEATH=1: her pieces at their sockets as the game mounts them
/// (Arms.HoldSheathed: the same MakeSheathed piece, its scabbard, materials and the outfit's clearance),
/// not the dumped meshes, so the review sheets show what the game shows.
/// </summary>
public partial class SheathedReview : Node
{
    /// <summary>Mount `id` sheathed on the skeleton; false if it has no socket (it stays in hand). `calling`: the
    /// outfit's ("" none).</summary>
    public bool Mount(Skeleton3D skeleton, string id, bool left, string calling) => Arms.HoldSheathed(skeleton, id, left, calling) != null;
}
