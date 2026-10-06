import sys
root = sys.argv[1]

def patch(path, pairs):
    p = root + '/' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

patch('src/Ui/Pack.cs', [
("""    /// <summary>The filters: what each shows.</summary>
    static readonly (string Name, Func<ItemDef, bool> Has)[] Filters =
    {
        ("All", _ => true),
        ("Gear", d => Items.SlotFor(d) != null),
        ("Draughts", d => d.Kind == ItemKind.Consumable),
        ("Materials", d => d.Kind is ItemKind.Material or ItemKind.Trophy or ItemKind.Tool),
        ("Quest", d => d.Kind == ItemKind.Quest),
    };""",
"""    /// <summary>The pack's places, then the slotless stores (docs/design/LOOT_DESIGN.md §6). A stop-gap
    /// row until UI design's tabs land: each shows its store, and Use and Leave work from it.</summary>
    static readonly (string Name, Func<CharacterData, List<ItemInstance>>? Of)[] Filters =
    {
        ("Pack", null),
        ("Pouch", Inventory.Pouch),
        ("Satchel", ch => ch.Satchel.ToList()),
        ("Key ring", ch => ch.Keys.ToList()),
        ("Belt", Inventory.Belt),
    };"""),
("""        // Materials live in the pouch, not the pack (docs/CRAFTING_DESIGN.md 4.3): their filter shows it.
        if (filter == PouchFilter) centre.AddChild(ItemViews.Grid(PouchView(ch), 8, 84, it => it.Uid == sel, null, it => Select(it.Uid), null, Hover, "pack", Leave, null));""",
"""        // Only gear takes a place; the stores show what they hold (docs/design/LOOT_DESIGN.md §6).
        if (Filters[filter].Of is { } of) centre.AddChild(ItemViews.Grid(StoreView(of(ch)), 8, 84, it => it.Uid == sel, null, it => Select(it.Uid), Primary, Hover, "pack", Leave, null));"""),
("""    const int PouchFilter = 3;

    /// <summary>The pouch's materials, then the trophies and tools the pack holds, as one shelf.</summary>
    static List<ItemInstance?> PouchView(CharacterData ch)
    {
        var o = Inventory.Pouch(ch).Cast<ItemInstance?>().Concat(ch.Pack.Where(p => p != null && Items.Get(p.Def).Kind is ItemKind.Trophy or ItemKind.Tool)).ToList();
        while (o.Count < 24 || o.Count % 8 != 0) o.Add(null);
        return o;
    }""",
"""    /// <summary>A store as one shelf of tiles.</summary>
    static List<ItemInstance?> StoreView(List<ItemInstance> things)
    {
        var o = things.Cast<ItemInstance?>().ToList();
        while (o.Count < 24 || o.Count % 8 != 0) o.Add(null);
        return o;
    }"""),
("""            if (!Filters[filter].Has(Items.Get(it.Def))) view.Modulate = new Color(1, 1, 1, 0.22f);
""", ""),
("""        if (!loc.InPack) { if (loc.Slot != EquipSlot.Weapon) G.Gear((j, b) => j.Unequip(loc.Slot, b)); else Sound.Sfx.Deny(); return; }""",
"""        if (loc.Worn) { if (loc.Slot != EquipSlot.Weapon) G.Gear((j, b) => j.Unequip(loc.Slot, b)); else Sound.Sfx.Deny(); return; }"""),
("""    bool InPack(ItemInstance it) => Inventory.Find(Ch, it.Uid) is { InPack: true } || Inventory.FromPouch(it.Uid) != null;""",
"""    bool InPack(ItemInstance it) => Inventory.Holds(Ch, it.Uid);"""),
("""        // A stack in the pouch: read, and left behind if it must be.
        if (Inventory.FromPouch(it.Uid) != null)
        {
            if (!Controls.Instance.UsingPad) acts.AddChild(Style.Button(leaving == it.Uid ? "Leave it all behind for good" : "Leave behind", () => Leave(it), false, true));
            inspect.AddChild(ItemViews.Card(it, Ch, false, acts, 480));
            return;
        }
        var loc = Inventory.Find(Ch, it.Uid);
        if (loc == null) return;""",
"""        var loc = Inventory.Find(Ch, it.Uid);
        if (loc == null) return;
        // A thing in a store: read, used if it is used, and left behind if it must be.
        if (!loc.InPack && !loc.Worn)
        {
            if (!Controls.Instance.UsingPad && def.Kind == ItemKind.Consumable) acts.AddChild(Style.Button("Use", () => Primary(it), true, true));
            if (!Controls.Instance.UsingPad && !G.Journey.StillNeeded(it))
                acts.AddChild(Style.Button(leaving == it.Uid ? "Leave it behind for good" : "Leave behind", () => Leave(it), false, true));
            inspect.AddChild(ItemViews.Card(it, Ch, false, acts, 480));
            return;
        }"""),
])

patch('src/Ui/Forge.cs', [
("""            bool worn = Inventory.Find(Ch, it.Uid) is { InPack: false };""",
"""            bool worn = Inventory.Find(Ch, it.Uid) is { Worn: true };"""),
])
print("ok")
