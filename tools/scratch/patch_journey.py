import sys
root = sys.argv[1]

def patch(path, pairs):
    p = root + '/' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:90])
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

patch('logic/Play/Journey.cs', [
# Use from any store.
("""        if (Inventory.Find(Ch, uid) is not { InPack: true } loc) return;
        var def = Items.Get(loc.Item.Def);
        if (def.Kind != ItemKind.Consumable || def.Consumable is not { } c) { Equip(uid, null, b); return; }""",
"""        if (Inventory.Find(Ch, uid) is not { Carried: true } loc) return;
        var def = Items.Get(loc.Item.Def);
        if (def.Kind != ItemKind.Consumable || def.Consumable is not { } c) { if (loc.InPack) Equip(uid, null, b); return; }"""),
("""        loc.Item.Qty--;
        if (loc.Item.Qty <= 0) Ch.Pack[loc.Index] = null;
        OnToast(new Toast(ToastKind.World, $"{def.Name} used"));""",
"""        Inventory.Remove(Ch, uid, 1);
        OnToast(new Toast(ToastKind.World, $"{def.Name} used"));"""),
# Drop from any store.
("""        if (Inventory.FromPouch(uid) is { } mat && Ch.Materials.Remove(mat))
        {
            OnToast(new Toast(ToastKind.World, $"Left behind: {Items.Get(mat).Name}"));
            OnTouch();
            return;
        }
        if (Inventory.Find(Ch, uid) is not { InPack: true } loc) return;
        if (StillNeeded(loc.Item)) { Warn("You might need that"); return; }
        Ch.Pack[loc.Index] = null;
        OnToast(new Toast(ToastKind.World, $"Left behind: {Inventory.Name(loc.Item)}"));""",
"""        if (Inventory.Find(Ch, uid) is not { Carried: true } loc) return;
        if (StillNeeded(loc.Item)) { Warn("You might need that"); return; }
        Inventory.Remove(Ch, uid);
        OnToast(new Toast(ToastKind.World, $"Left behind: {Inventory.Name(loc.Item)}"));"""),
# Pickup: gear rolled whole where it fell is taken as it is.
("""        if (p.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Quest && p.Ref != null)
        {""",
"""        // Gear rolled whole where it fell (Rpg/Loot.cs) is taken as it is.
        if (p.Payload is ItemInstance whole) return Take(whole);
        if (p.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Quest && p.Ref != null)
        {"""),
# Selling from any store.
("""        var mine = Ch.Pack.FirstOrDefault(x => x?.Uid == uid) ?? Inventory.Pouch(Ch).FirstOrDefault(x => x.Uid == uid);
        if (mine == null) return null;""",
"""        if (Inventory.Find(Ch, uid) is not { Carried: true } at) return null;
        var mine = at.Item;"""),
("""        ItemInstance it;
        if (Inventory.FromPouch(uid) is { } mat)
        {
            // Out of the pouch, the whole of it: a stack on their counter.
            it = Inventory.Make(Ch, mat, Ch.Materials.GetValueOrDefault(mat));
            Ch.Materials.Remove(mat);
        }
        else
        {
            int i = Ch.Pack.FindIndex(x => x?.Uid == uid);
            it = Ch.Pack[i]!;
            Ch.Pack[i] = null;
        }""",
"""        // Out of wherever it is carried, the whole of it: a stack on their counter.
        var it = Inventory.Remove(Ch, uid)!;"""),
])
print("ok")
