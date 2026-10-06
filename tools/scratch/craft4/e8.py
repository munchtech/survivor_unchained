from ed import sub

sub("logic/Play/JourneyCrafting.cs", [
("""        if (night != null && y.Kept.ContainsKey(Crafting.Shard)) World.Facts["shards.from"] = night;
        OnTouch();
    }
}""",
"""        if (night != null && y.Kept.ContainsKey(Crafting.Shard)) World.Facts["shards.from"] = night;
        OnTouch();
    }

    /* ----------------------------------------------------------- the two kits -- */

    /// <summary>A piece from the pack worn in one of the two kits (Rpg/Kits.cs), a ring to whichever hand
    /// of that kit is free; the fight takes it up at once if that kit is the one on.</summary>
    public void EquipKit(string uid, KitKind kit, EquipSlot? slot, Battle? b)
    {
        if (Inventory.Find(Ch, uid) is not { InPack: true } loc) return;
        var def = Items.Get(loc.Item.Def);
        if ((slot ?? Items.SlotFor(def)) is not EquipSlot t || !Items.Fits(def, t)) return;
        if (slot == null && t == EquipSlot.Ring1 && Kits.HasOwn(Ch, kit, EquipSlot.Ring1) && !Kits.HasOwn(Ch, kit, EquipSlot.Ring2)) t = EquipSlot.Ring2;
        if (!Kits.Put(Ch, kit, loc.Item, t)) { Warn("No room in your pack for what you are wearing"); return; }
        bool on = kit == Kits.On(Ch);
        OnToast(new Toast(ToastKind.Loot, on ? $"Wearing {Inventory.Name(loc.Item)}" : $"{Inventory.Name(loc.Item)}, worn {(kit == KitKind.Night ? "by night" : "by day")}",
            Icon: def.Icon, Rarity: loc.Item.Rarity));
        RefreshKit(b);
    }

    /// <summary>A kit's piece taken off into the pack; off the night kit, that slot wears the day's piece again.</summary>
    public void UnequipKit(KitKind kit, EquipSlot slot, Battle? b)
    {
        // (the night's own weapon can go: the day's is still in hand by night)
        if (kit == KitKind.Day && slot == EquipSlot.Weapon) { Warn("You will not walk this road unarmed"); return; }
        if (!Kits.Clear(Ch, kit, slot)) { Warn("Your pack is full"); return; }
        RefreshKit(b);
    }
}"""),
])
