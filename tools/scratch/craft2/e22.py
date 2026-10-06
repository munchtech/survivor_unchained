from ed import sub
sub('src/Ui/Forge.cs', [
("""    /// <summary>The seam most worth working when a piece is put down: an affix that can still be
    /// tempered, else an open seam, else the first.</summary>
    static int DefaultSeam(ItemInstance it)
    {
        int cap = Crafting.Cap(it);
        for (int k = 0; k < it.Affixes.Count; k++)
            if (Plain(Items.Affix(it.Affixes[k].Id)) && it.Affixes[k].Tier < cap) return k;
        return Crafting.OpenSeams(it) > 0 ? it.Affixes.Count : 0;
    }""",
"""    /// <summary>The seam most worth working when a piece is put down: an affix that can still be
    /// tempered, else an open seam, else the first. A hand that only works things in (Wenna's)
    /// starts at the open seam, never offering to work over what the piece has.</summary>
    int DefaultSeam(ItemInstance it)
    {
        int cap = Crafting.Cap(it);
        if (!Crafting.Does(crafter, Verb.Temper) && Crafting.OpenSeams(it) > 0) return it.Affixes.Count;
        for (int k = 0; k < it.Affixes.Count; k++)
            if (Plain(Items.Affix(it.Affixes[k].Id)) && it.Affixes[k].Tier < cap) return k;
        return Crafting.OpenSeams(it) > 0 ? it.Affixes.Count : 0;
    }"""),
])
