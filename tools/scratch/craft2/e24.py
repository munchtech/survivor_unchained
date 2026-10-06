from ed import sub
sub('src/Ui/Pack.cs', [
("""        broke = (Inventory.Name(it), string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))), q.Gives.Keys.First());""",
"""        broke = (Inventory.Name(it), string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))), q.Gives.Keys.First(), Time.GetTicksMsec());"""),
("""    (string Name, string Gives, string Icon)? broke;""",
"""    (string Name, string Gives, string Icon, ulong At)? broke;"""),
("""        if (it == null && broke is { } b)
        {
            broke = null;""",
"""        // Shown for a few seconds, however often the page is built again meanwhile.
        if (it == null && broke is { } b && Time.GetTicksMsec() - b.At < 3000)
        {"""),
("""            note.CreateTween().TweenProperty(note, "modulate:a", 0f, 0.8).SetDelay(3.0);""",
"""            note.CreateTween().TweenProperty(note, "modulate:a", 0f, 0.8).SetDelay(Math.Max(0, 3.0 - (Time.GetTicksMsec() - b.At) / 1000.0));"""),
])
