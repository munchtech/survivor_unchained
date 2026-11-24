namespace SurvivorUnchained.View;

/// <summary>(cool shade lane, 23 Nov 2026; the owner said yes to option C's "cool shade + warm light" in the den) --den-shade 1:
/// the den's shade goes cool violet and its pools are the real projected light (DungeonLight, DenCookie). One switch for the
/// whole look, default 0 until a judge passes it. What it changes, all of it the den's own:
/// the den's rig (rigs.json "den_cool" stands in for "den": Atmosphere.RigsLoad), its grade (Atmospheres "rig_den_cool"), the
/// floor's tint (DungeonFloor), and the real light with its numbers under the shade (DungeonLight). No shared shader, no
/// other zone.</summary>
public static class DenShade
{
    public static readonly bool On = SurvivorUnchained.Args.Num("den-shade", 0f) > 0f;

    /// <summary>The floor's tint under the shade (dungeon_floor's den_tint; --den-tint r,g,b still wins).</summary>
    public static readonly Godot.Vector3 Tint = new(0.56f, 0.55f, 0.56f);   // (neutral and low: the rig's violet key is strong so the walls read, the floor is held at L* 13)

    /// <summary>A den number that has its own default under the shade: --name wins, else <paramref name="shade"/> under
    /// --den-shade 1, else <paramref name="today"/>.</summary>
    public static float Num(string name, float shade, float today) => SurvivorUnchained.Args.Num(name, On ? shade : today);
}
