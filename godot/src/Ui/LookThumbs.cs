using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>Look thumbnails (bd-ui W23): each look pictured as her wearing its own pieces. STUB: returns the item picture
/// until the live build lands; the API is final.</summary>
public static class LookThumbs
{
    public static Control For(string defId, string slot, int size, bool locked)
    {
        var def = Items.Get(defId);
        var c = ItemPhotos.Icon(def.Icon, size, new Color("#c8b08c"));
        if (locked) c.Modulate = new Color(0.15f, 0.15f, 0.15f, 1);
        return c;
    }
}
