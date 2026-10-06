import sys
root = sys.argv[1]

def patch(path, pairs):
    p = root + '/' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:90])
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

patch('logic/Maps/Charts.cs', [
("""    /// <summary>A chart carried, taken out of the pack to be set on the table (it is used up as its
    /// map opens); null if it is not there.</summary>
    public static Chart? TakeOut(Rpg.CharacterData ch, string uid)
    {
        int i = ch.Pack.FindIndex(p => p?.Uid == uid && p.Chart != null);
        if (i < 0) return null;
        var c = ch.Pack[i]!.Chart;
        ch.Pack[i] = null;
        return c;
    }""",
"""    /// <summary>A chart carried, taken out of the satchel to be set on the table (it is used up as its
    /// map opens); null if it is not there.</summary>
    public static Chart? TakeOut(Rpg.CharacterData ch, string uid)
    {
        int i = ch.Satchel.FindIndex(p => p.Uid == uid && p.Chart != null);
        if (i < 0) return null;
        var c = ch.Satchel[i].Chart;
        ch.Satchel.RemoveAt(i);
        return c;
    }"""),
("""        ch.Pack.Where(p => p?.Chart != null).Select(p => p!).OrderByDescending(p => p.Chart!.Tier).ThenByDescending(p => p.Chart!.Rarity).ToList();""",
"""        ch.Satchel.Where(p => p.Chart != null).OrderByDescending(p => p.Chart!.Tier).ThenByDescending(p => p.Chart!.Rarity).ToList();"""),
("""        Best(w) > 0 || ch != null && ch.Pack.Any(p => p?.Chart != null);""",
"""        Best(w) > 0 || ch != null && ch.Satchel.Any(p => p.Chart != null);"""),
])

patch('logic/Maps/MapSpoils.cs', [
("""        ch.Pack.Where(p => p != null).Select(p => p!).Concat(Items.EquipSlots.Select(s => ch.Equipment[s]).Where(x => x != null).Select(x => x!));""",
"""        ch.Pack.Where(p => p != null).Select(p => p!).Concat(ch.Satchel).Concat(ch.Keys)
            .Concat(Items.EquipSlots.Select(s => ch.Equipment[s]).Where(x => x != null).Select(x => x!));"""),
])

patch('logic/Rpg/CraftingCharts.cs', [
("""        else if (Inventory.Find(x.Ch, from.Uid) is not { InPack: true }) q.Blocked = "Carry it in your pack.";""",
"""        else if (!Inventory.Holds(x.Ch, from.Uid)) q.Blocked = "Carry it with you.";"""),
("""        it.Chart is { } c ? ch.Pack.Where(p => p?.Chart is { } f && p.Uid != it.Uid && f.People == c.People).OrderBy(p => p!.Chart!.Rarity).ThenBy(p => p!.Chart!.Tier).FirstOrDefault() : null;""",
"""        it.Chart is { } c ? ch.Satchel.Where(p => p.Chart is { } f && p.Uid != it.Uid && f.People == c.People).OrderBy(p => p.Chart!.Rarity).ThenBy(p => p.Chart!.Tier).FirstOrDefault() : null;"""),
("""                ch.Pack[Inventory.Find(ch, q.Donor!)!.Index] = null;
                return 0;""",
"""                Inventory.Remove(ch, q.Donor!);
                return 0;"""),
])

patch('logic/Rpg/Crafting.cs', [
("""        ch.Pack.Where(p => p != null && MarkIn(p) != null).Select(p => p!).OrderByDescending(p => MarkIn(p)!.Tier).ToList();""",
"""        ch.Satchel.Concat(ch.Pack.Where(p => p != null).Select(p => p!)).Where(p => MarkIn(p) != null).OrderByDescending(p => MarkIn(p)!.Tier).ToList();"""),
("""        if (Inventory.Find(x.Ch, from.Uid) is not { InPack: true }) q.Blocked ??= "Carry it in your pack.";""",
"""        if (!Inventory.Holds(x.Ch, from.Uid)) q.Blocked ??= "Carry it with you.";"""),
("""        if (q.Verb is Verb.Bind or Verb.Mark or Verb.Annotate && (q.Donor == null || Inventory.Find(ch, q.Donor) is not { InPack: true })) return false;""",
"""        if (q.Verb is Verb.Bind && (q.Donor == null || Inventory.Find(ch, q.Donor) is not { InPack: true })) return false;
        if (q.Verb is Verb.Mark or Verb.Annotate && (q.Donor == null || !Inventory.Holds(ch, q.Donor))) return false;"""),
("""                // The ruler's thing is used up: what it held is written into the piece.
                ch.Pack[Inventory.Find(ch, q.Donor!)!.Index] = null;""",
"""                // The ruler's thing is used up: what it held is written into the piece.
                Inventory.Remove(ch, q.Donor!);"""),
])

patch('logic/Play/JourneyCrafting.cs', [
("""        if (!loc.InPack) RefreshKit(b); else OnTouch();""",
"""        if (loc.Worn) RefreshKit(b); else OnTouch();"""),
])
print("ok")
