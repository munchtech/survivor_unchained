from ed import sub
sub('src/Ui/Pack.cs', [
("""            inspect.AddChild(ItemViews.Card(it, Ch, true, acts, 480));
            var worn = ItemViews.Against(it, Ch);""",
"""            inspect.AddChild(ItemViews.Card(it, Ch, true, acts, 480));
            SteepOdds(it);
            var worn = ItemViews.Against(it, Ch);"""),
("""        inspect.AddChild(ItemViews.Card(it, Ch, loc.InPack, acts, 480));
    }""",
"""        inspect.AddChild(ItemViews.Card(it, Ch, loc.InPack, acts, 480));
        SteepOdds(it);
    }

    /// <summary>Asked to steep: everything it could come to, said before the jar is opened (design 9).</summary>
    void SteepOdds(ItemInstance it)
    {
        if (steeping != it.Uid) return;
        var lines = Style.V(2, Style.Label("Opened, the jar does one of these, and the piece is set for good after:", Style.UiBold, Style.Small, Style.Ink, true));
        foreach (var (o, p) in Crafting.Odds())
            lines.AddChild(Style.Label($"{p:0%}  {o switch { "up" => "one of its powers a grade past what the forge can do", "affix" => "a slurry power past its seams, strong, with a price", "nothing" => "only the veins", _ => "one of its powers a grade lower" }}",
                Style.Ui, Style.Small, o == "down" ? Style.Bad : new Color("#a8e08a"), true));
        var slab = Style.Panel(Style.Box(new Color("#121a10"), new Color("#4a7a3a") with { A = 0.7f }, 1, 5, 12), lines);
        slab.CustomMinimumSize = new Vector2(480, 0);
        inspect.AddChild(slab);
    }"""),
])
