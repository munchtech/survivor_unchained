PAIRS = [
("""    readonly Dictionary<string, float> heights = new();
    readonly List<Control> measured = new();
    int measuring;
""",
"""    readonly Dictionary<string, float> heights = new();
    readonly List<Control> measured = new();
    readonly List<ScrollContainer> leaves = new();
    /// <summary>The section whose height is still being found (shown only once it holds), the
    /// frames left before the next measure, and how many measures it has taken.</summary>
    string? settling;
    int measuring, tries;
"""),
("""        page = null;
        measured.Clear();
""",
"""        page = null;
        measured.Clear();
        leaves.Clear();
        if (!heights.ContainsKey(tab)) { settling = tab; tries = 0; }
"""),
("""        if (!heights.ContainsKey(tab))
        {
            // Measured before it is shown: this page and every page the list can open here (a
            // quest chosen later scrolls in a book cut to the first), laid out at a page's width.
            book.Modulate = Colors.Transparent;""",
"""        if (settling == tab)
        {
            // Measured before it is shown: this page and every page the list can open here (a
            // quest chosen later scrolls in a book cut to the first), laid out at a page's width.
            book.Modulate = Colors.Transparent;"""),
("""            measuring = 3;
        }""",
"""            measuring = 4;
        }"""),
("""        // Laid out: the book takes its writing's height, and is shown.
        if (measuring > 0 && --measuring == 0)
        {
            float need = measured.Where(IsInstanceValid).Select(c => c.GetCombinedMinimumSize().Y).DefaultIfEmpty(0).Max();
            // (a little over: a page cut to the pixel shows its scroll bar, the bar narrows the
            // words, and they wrap onto lines it then has no room for)
            heights[tab] = Math.Clamp(need + OpenBook.Chrome + 16, MinH, MaxH);
            if (Args.Has("shot")) GD.Print($"journal {tab}: words {need:0}, book {heights[tab]:0}");
            Refresh();
        }""",
"""        // Laid out: the book takes its writing's height, and is measured again at it until the
        // height holds (wrapped words settle their lines a frame or two after the width they wrap
        // to; a scroll bar, once shown, narrows them onto more), then shown.
        if (measuring > 0 && --measuring == 0 && settling == tab)
        {
            float need = measured.Where(IsInstanceValid).Select(c => c.GetCombinedMinimumSize().Y)
                .Concat(leaves.Where(IsInstanceValid).Select(s => (float)s.GetVScrollBar().MaxValue)).DefaultIfEmpty(0).Max();
            float had = heights.GetValueOrDefault(tab, MaxH), now = Math.Clamp(need + OpenBook.Chrome + 16, MinH, MaxH);
            heights[tab] = now;
            if (Math.Abs(now - had) <= 2 || ++tries >= 4) settling = null;
            if (Args.Has("shot")) GD.Print($"journal {tab}: words {need:0}, book {now:0}{(settling == null ? ", held" : "")}");
            Refresh();
        }"""),
("""        sc.Size = leaf.Size - new Vector2(0, 30);
        leaf.AddChild(sc);
        page ??= sc;""",
"""        sc.Size = leaf.Size - new Vector2(0, 30);
        leaf.AddChild(sc);
        leaves.Add(sc);
        page ??= sc;"""),
]
