PAIRS = [
("""    Control DollView(CharacterData ch)
    {
        var holder = new Control { CustomMinimumSize = new Vector2(DollW, DollH), MouseFilter = MouseFilterEnum.Ignore };""",
"""    /// <summary>The kit looked at (by day or by night, crafting's design 20.2); null: the one worn now.</summary>
    static KitKind? kitShown;
    KitKind Shown => kitShown ?? Kits.On(Ch);
    /// <summary>Looking at the kit not worn now: what is put on or taken off goes into that one.</summary>
    bool OtherKit => Kits.Shown(Ch) && Shown != Kits.On(Ch);

    Control DollView(CharacterData ch)
    {
        var holder = new Control { CustomMinimumSize = new Vector2(DollW, DollH), MouseFilter = MouseFilterEnum.Ignore };
        if (!Kits.Shown(ch)) { kitShown = null; return Doll_(ch, holder); }
        // Two kits once a coal or a Mark is owned: the switch over the doll, the one worn now marked
        // with an ember; the night kit's empty places wear the day's piece, faint, "as by day".
        var on = Kits.On(ch);
        var tabs = Kit.Tabs(new[] { "By day", "By night" }, (int)Shown, k => { kitShown = (KitKind)k; Refresh(); }, 15, 26);
        tabs.Alignment = BoxContainer.AlignmentMode.Center;
        var worn = Style.Label(on == KitKind.Night ? "the night kit is on" : "the day kit is on", Style.TextItalic, 13, Style.Ember, false, HorizontalAlignment.Center, false);
        var col = Style.V(4, tabs, worn, Doll_(ch, holder));
        return col;
    }

    Control Doll_(CharacterData ch, Control holder)
    {"""),
("""        foreach (var (s, right, y) in Doll)
        {
            var it = ch.Equipment[s];
            var (name, glyph) = Slots[s];
            var slot = s;
            Action? off = it != null && slot != EquipSlot.Weapon ? () => G.Gear((j, b) => j.Unequip(slot, b)) : null;
            var view = ItemViews.Slot(it, SlotS, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,
                over => Hover(it, over), glyph, name, $"eq:{slot}", null, false, false, false, ch, engraved: true);
            view.Position = new Vector2(right ? DollW - SlotS - 6 : 6, y);
            // Dragged from the pack, a thing that fits is worn here; dragged away from here, it is taken off.
            view.Drag = it != null && slot != EquipSlot.Weapon ? $"eq:{slot}:{it.Uid}" : null;
            view.CanTake = d => d.StartsWith("pack:") && Inventory.Find(Ch, d[5..]) is { } w && Items.Fits(Items.Get(w.Item.Def), slot);
            view.Take = d => { Sound.Sfx.Equip(); G.Gear((j, b) => j.Equip(d[5..], slot, b)); };
            holder.AddChild(view);
        }
        return holder;""",
"""        var kit = Shown;
        bool two = Kits.Shown(ch);
        foreach (var (s, right, y) in Doll)
        {
            var it = two ? Kits.Piece(ch, kit, s) : ch.Equipment[s];
            bool asDay = two && kit == KitKind.Night && it != null && !Kits.HasOwn(ch, KitKind.Night, s);
            var (name, glyph) = Slots[s];
            var slot = s;
            Action? off = it != null && slot != EquipSlot.Weapon && !asDay ? () => TakeOff(slot) : null;
            var view = ItemViews.Slot(it, SlotS, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,
                over => Hover(it, over), glyph, name, $"eq:{slot}", null, false, false, false, ch, engraved: true);
            view.Position = new Vector2(right ? DollW - SlotS - 6 : 6, y);
            if (asDay) { view.Modulate = new Color(1, 1, 1, 0.4f); view.TooltipText = "As by day: the night kit wears the day's piece here"; }
            // Dragged from the pack, a thing that fits is worn here; dragged away from here, it is taken off.
            view.Drag = it != null && slot != EquipSlot.Weapon && !asDay ? $"eq:{slot}:{it.Uid}" : null;
            view.CanTake = d => d.StartsWith("pack:") && Inventory.Find(Ch, d[5..]) is { } w && Items.Fits(Items.Get(w.Item.Def), slot);
            view.Take = d => { Sound.Sfx.Equip(); PutOn(d[5..], slot); };
            holder.AddChild(view);
        }
        return holder;
    }

    /// <summary>Worn in the kit looked at (the one on now, or the other).</summary>
    void PutOn(string uid, EquipSlot? slot)
    {
        if (OtherKit) { var k = Shown; G.Gear((j, b) => j.EquipKit(uid, k, slot, b)); }
        else G.Gear((j, b) => j.Equip(uid, slot, b));
    }

    void TakeOff(EquipSlot slot)
    {
        if (OtherKit) { var k = Shown; G.Gear((j, b) => j.UnequipKit(k, slot, b)); }
        else G.Gear((j, b) => j.Unequip(slot, b));"""),
("""        else if (Items.SlotFor(def) != null) { Sound.Sfx.Equip(); G.Gear((j, b) => j.Equip(it.Uid, null, b)); }""",
"""        else if (Items.SlotFor(def) != null) { Sound.Sfx.Equip(); PutOn(it.Uid, null); }"""),
]
