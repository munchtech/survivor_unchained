PAIRS = [
("""    /// chain's ends where the tabs have no keys of their own (creation's steps).</summary>
    public ChainTabs((string Name, string Key)[] tabs, int on, Action<int> pick, (string Prev, string Next)? ends = null)
    {""", """    /// chain's ends where the tabs have no keys of their own (creation's steps). gap: between the names.</summary>
    public ChainTabs((string Name, string Key)[] tabs, int on, Action<int> pick, (string Prev, string Next)? ends = null, int gap = 26)
    {"""),
("""        row = Style.H(26);""", """        row = Style.H(gap);"""),
("""            b.CustomMinimumSize = inner.GetCombinedMinimumSize();
            b.MouseEntered += () => { if (k != on) inner.Modulate = new Color(1.25f, 1.2f, 1.1f); };""", """            b.CustomMinimumSize = inner.GetCombinedMinimumSize();
            // (measured again in the tree, where its key's cap takes the screen's type)
            b.Ready += () => b.CustomMinimumSize = inner.GetCombinedMinimumSize();
            b.MouseEntered += () => { if (k != on) inner.Modulate = new Color(1.25f, 1.2f, 1.1f); };"""),
("""        var min = row.GetCombinedMinimumSize();
        // (the chain hangs a little below the names, its links up to 44 high, so the row leaves it room)
        chainY = min.Y + 14;
        // Anchored, the eyelet past the first tab stays inside the panel: the names step in to leave it room.
        // (the eyelet is half a cell wide: its middle stays that far inside, past the first name by the run)
        // (the same at the last tab, so a chain set in the middle of a panel is centred, eyes and all)
        var buttons = row.GetChildren().OfType<Button>().ToList();
        float first = buttons.FirstOrDefault()?.GetCombinedMinimumSize().X / 2 ?? 20, last = buttons.LastOrDefault()?.GetCombinedMinimumSize().X / 2 ?? 20;
        insetL = F.Eye ? Math.Max(0, Run + F.Tail + 26 - first) : 0;
        insetR = F.Eye ? Math.Max(0, Run + F.Tail + 26 - last) : 0;
        row.Position = new Vector2(insetL, 0);
        CustomMinimumSize = new Vector2(min.X + insetL + insetR, chainY + 22);
    }

    (Control L, Control R)? caps;
    float insetL, insetR;

    public override void _Ready()
    {
        if (caps is not { } c) return;
        // The caps' own room each side, the row stepped in past the left one, the right one past the eye.
        var min = row.GetCombinedMinimumSize();
        var ls = c.L.GetCombinedMinimumSize();
        var rs = c.R.GetCombinedMinimumSize();
        const float gap = 6;
        row.Position = new Vector2(ls.X + gap + insetL, 0);
        c.L.Position = new Vector2(0, (min.Y - ls.Y) / 2);
        c.R.Position = new Vector2(ls.X + gap + insetL + min.X + insetR + gap, (min.Y - rs.Y) / 2);
        CustomMinimumSize = new Vector2(c.R.Position.X + rs.X, CustomMinimumSize.Y);
    }
""", """        Lay();
    }

    (Control L, Control R)? caps;

    public override void _Ready() => Lay();

    /// <summary>Its room: the names' row stepped in from both ends so the eyes stay inside it, and
    /// the turning keys, if any, outside the eyes. Laid again once in the tree, where the key caps
    /// measure as they are drawn (out of it they take the default theme's type and run wide).</summary>
    void Lay()
    {
        var min = row.GetCombinedMinimumSize();
        // (the chain hangs a little below the names, its links up to 44 high, so the row leaves it room)
        chainY = min.Y + 14;
        // Anchored, the eyelet past the first tab stays inside the panel: the names step in to leave it room.
        // (the eyelet is half a cell wide: its middle stays that far inside, past the first name by the run)
        // (the same at the last tab, so a chain set in the middle of a panel is centred, eyes and all)
        var buttons = row.GetChildren().OfType<Button>().ToList();
        float first = buttons.FirstOrDefault()?.GetCombinedMinimumSize().X / 2 ?? 20, last = buttons.LastOrDefault()?.GetCombinedMinimumSize().X / 2 ?? 20;
        float insetL = F.Eye ? Math.Max(0, Run + F.Tail + 26 - first) : 0;
        float insetR = F.Eye ? Math.Max(0, Run + F.Tail + 26 - last) : 0;
        float x = 0;
        const float gap = 6;
        if (caps is { } c)
        {
            var ls = c.L.GetCombinedMinimumSize();
            var rs = c.R.GetCombinedMinimumSize();
            c.L.Position = new Vector2(0, (min.Y - ls.Y) / 2);
            c.R.Position = new Vector2(ls.X + gap + insetL + min.X + insetR + gap, (min.Y - rs.Y) / 2);
            x = ls.X + gap;
            insetR += gap + rs.X;
        }
        row.Position = new Vector2(x + insetL, 0);
        CustomMinimumSize = new Vector2(x + insetL + min.X + insetR, chainY + 22);
    }
"""),
]
