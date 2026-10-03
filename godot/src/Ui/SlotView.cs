using System;
using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// An item's slot that can be picked up and put down with the mouse: dragged
/// from the pack to the body to wear it, from the body to the pack to take it
/// off, along the pack to move it, from a shelf to the pack to buy it. What a
/// drag carries is a word ("pack:UID", "eq:Head:UID", "shelf:UID"); the slot
/// it is dropped on decides whether it takes it, and lights while it would.
/// </summary>
public partial class SlotView : Panel
{
    /// <summary>What a drag from here carries (null: nothing can be dragged from it).</summary>
    public string? Drag;
    public ItemInstance? Item;
    /// <summary>Whether a drag would be taken here, and what taking it does.</summary>
    public Func<string, bool>? CanTake;
    public Action<string>? Take;
    bool lit;

    public override Variant _GetDragData(Vector2 atPosition)
    {
        if (Drag == null || Item == null) return default;
        var def = Items.Get(Item.Def);
        var holder = new Control { MouseFilter = MouseFilterEnum.Ignore };
        var pic = ItemPhotos.Icon(def.Icon, 64, Style.RarityOf(Item.Rarity).Lightened(0.25f));
        pic.Position = new Vector2(-32, -32);
        pic.Modulate = new Color(1, 1, 1, 0.9f);
        holder.AddChild(pic);
        SetDragPreview(holder);
        // The slot it left shows it is in hand.
        Modulate = new Color(1, 1, 1, 0.35f);
        Sound.Sfx.Click();
        return Drag;
    }

    public override bool _CanDropData(Vector2 atPosition, Variant data)
    {
        bool ok = data.VariantType == Variant.Type.String && data.AsString() != Drag && (CanTake?.Invoke(data.AsString()) ?? false);
        Light(ok);
        return ok;
    }

    public override void _DropData(Vector2 atPosition, Variant data)
    {
        Light(false);
        Take?.Invoke(data.AsString());
    }

    void Light(bool on)
    {
        if (on == lit) return;
        lit = on;
        SelfModulate = on ? new Color(1.6f, 1.4f, 1.05f) : Colors.White;
    }

    public override void _Notification(int what)
    {
        if (what == NotificationMouseExit) Light(false);
        if (what == NotificationDragEnd) { Light(false); Modulate = Colors.White; }
    }
}
