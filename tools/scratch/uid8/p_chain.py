PAIRS = [
("""    public ChainTabs((string Name, string Key)[] tabs, int on, Action<int> pick)
    {
        this.on = on;
        MouseFilter = MouseFilterEnum.Ignore;
        // The links are made at twice their size: drawn smaller, and turned on the sag, they want mipmaps.
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        bool pad = Controls.Instance?.UsingPad == true;
        row = Style.H(26);
        if (pad) row.AddChild(Style.PadButton("LB"));
""", """    /// <summary>The tabs on their chain. on: the open tab, or -1 for none (the pause's way into the
    /// book: the chain hangs cold, nothing heated). ends: the keys that turn them, drawn at the
    /// chain's ends where the tabs have no keys of their own (creation's steps).</summary>
    public ChainTabs((string Name, string Key)[] tabs, int on, Action<int> pick, (string Prev, string Next)? ends = null)
    {
        this.on = on;
        MouseFilter = MouseFilterEnum.Ignore;
        // The links are made at twice their size: drawn smaller, and turned on the sag, they want mipmaps.
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        bool pad = Controls.Instance?.UsingPad == true;
        row = Style.H(26);
        if (pad) row.AddChild(Style.PadButton("LB"));
        else if (ends is { } e0) row.AddChild(Style.Key(e0.Prev));
"""),
("""            var inner = Style.H(8, Style.Label(tabs[i].Name, Style.UiBold, 16, i == on ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false));
            if (!pad) inner.AddChild(Style.Key(tabs[i].Key));""", """            var inner = Style.H(8, Style.Label(tabs[i].Name, Style.UiBold, 16, i == on || on < 0 ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false));
            if (!pad && tabs[i].Key != "") inner.AddChild(Style.Key(tabs[i].Key));"""),
("""        if (pad) row.AddChild(Style.PadButton("RB"));
        AddChild(row);""", """        if (pad) row.AddChild(Style.PadButton("RB"));
        else if (ends is { } e1) row.AddChild(Style.Key(e1.Next));
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        AddChild(row);"""),
("""        float goal = Centre(on);
        if (!placed)""", """        // (none open: the chain at rest, its middle under the middle of the tabs)
        float goal = on >= 0 ? Centre(on) : (Centre(0) + Centre(Tabs - 1)) / 2;
        if (!placed)"""),
("""            bool fresh = !float.IsNaN(lastX) && Time.GetTicksMsec() - lastAt < 1500;""", """            bool fresh = on >= 0 && !float.IsNaN(lastX) && Time.GetTicksMsec() - lastAt < 1500;"""),
("""                float heat = Heat(k);""", """                float heat = on >= 0 ? Heat(k) : 0;"""),
("""                if (k == 0 && Sprite("open") is { } open)""", """                if (k == 0 && on >= 0 && Sprite("open") is { } open)"""),
("""        else if (face)
        {
            var pts = new Vector2[17];""", """        else if (face || k == 0)
        {
            var pts = new Vector2[17];"""),
]
