from ed import sub

sub("src/Game/Game.cs", [
("""        // --facts k=v,k=v: the world as a later day would have it""",
"""        // --nightkit DEF,DEF: those pieces from the pack worn by night (pictures of the two kits).
        if (Args.Get("nightkit") is string nk)
            foreach (var d in nk.Split(','))
                if (Journey.Ch.Pack.FirstOrDefault(p => p?.Def == d) is { } piece && Items.SlotFor(Items.Get(d)) is EquipSlot ks)
                    Kits.Put(Journey.Ch, KitKind.Night, piece, ks);
        // --facts k=v,k=v: the world as a later day would have it"""),
])
