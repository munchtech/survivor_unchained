from ed import sub
sub('src/Ui/Pack.cs', [
("""        broke = (Inventory.Name(it), string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))), q.Gives.Keys.First(), Time.GetTicksMsec());
        G.Gear((j, b) => j.Work(it.Uid, q, b));""",
"""        broke = (Inventory.Name(it), string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))), q.Gives.Keys.First(), Time.GetTicksMsec());
        // Only the pack changed: the figure is not dressed again (that rebuilds her, and she blinks out).
        G.Journey.Work(it.Uid, q, G.Battle);
        Refresh();"""),
])
sub('src/Ui/Forge.cs', [
("""        // The pad's focus comes back to the seam worked when the press it was on is gone.
        Nav.Prefer = seam >= 0 ? $"seam:{seam}" : "worn:0";
        G.Gear((j, b) => j.Work(uid, q, b));""",
"""        // The pad's focus comes back to the seam worked when the press it was on is gone.
        Nav.Prefer = seam >= 0 ? $"seam:{seam}" : "worn:0";
        // A craft changes what a piece does, never how it looks: the kit is folded back into the
        // fight (Journey.Work), and the figure is not dressed again.
        G.Journey.Work(uid, q, G.Battle);
        Refresh();"""),
])
