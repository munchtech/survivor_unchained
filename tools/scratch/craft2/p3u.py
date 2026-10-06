from ed import sub
sub('logic/Rpg/Crafting.cs', [
("""    /// <summary>A jar bought: paid, in the pouch, and counted against the day's three.</summary>""",
"""    /// <summary>How many jars Snib will still sell today.</summary>
    public static int JarsLeft(WorldState w) =>
        Math.Max(0, Rules.Slurry.PerDay - ((int)w.Fact("slurry.day").Number == w.Day ? (int)w.Fact("slurry.sold").Number : 0));

    /// <summary>A jar bought: paid, in the pouch, and counted against the day's three.</summary>"""),
])
sub('src/Ui/Forge.cs', [
("""    bool breaking;""",
"""    bool breaking, steeping;
    /// <summary>The donor a binding is armed to unmake ("uid:index"): asked once, done the second time.</summary>
    string? unmaking;"""),
("""    bool Takes(ItemInstance it) =>
        Crafting.Workable(it) && (Crafting.Does(crafter, Verb.Temper) || Crafting.Does(crafter, Verb.Remake) || Crafting.WorkInChoices(it, crafter).Count > 0);""",
"""    bool Takes(ItemInstance it) =>
        Crafting.Workable(it) && (Crafting.Does(crafter, Verb.Temper) || Crafting.Does(crafter, Verb.Remake) || Crafting.WorkInChoices(it, crafter).Count > 0
            || Crafting.Does(crafter, Verb.Bind) || Crafting.Does(crafter, Verb.Steep));

    /// <summary>The crafter does something to one seam (temper, work in, cage, bind); the slurry works the whole piece.</summary>
    bool SeamCrafts => Crafting.Does(crafter, Verb.Temper) || Crafting.Does(crafter, Verb.WorkIn) || Crafting.Does(crafter, Verb.Cage) || Crafting.Does(crafter, Verb.Bind);"""),
("""        if (Crafting.Does(crafter, Verb.Commission)) v.AddChild(MakeTile());""",
"""        if (Crafting.Does(crafter, Verb.Commission)) v.AddChild(MakeTile());
        if (Crafting.Does(crafter, Verb.Buy) && crafter == Crafting.Rules.Slurry.Crafter) v.AddChild(JarTile());"""),
("""        if (seam >= 0) body.AddChild(AtSeam(it));""",
"""        if (seam >= 0 && SeamCrafts) body.AddChild(AtSeam(it));"""),
("""        string note = open ? (Crafting.Does(crafter, Verb.Cage) ? "work a material in, or cage a coal" : "work a material in")""",
"""        string note = open ? (Crafting.Does(crafter, Verb.Cage) ? "work a material in, or cage a coal" : Crafting.Does(crafter, Verb.WorkIn) ? "work a material in"
                : Crafting.Does(crafter, Verb.Bind) ? "bind a power into it" : "empty")"""),
("""        if (Crafting.Does(crafter, Verb.Cage)) v.AddChild(Coals(it, k, open, coal));""",
"""        if (Crafting.Does(crafter, Verb.Cage)) v.AddChild(Coals(it, k, open, coal));
        if (Crafting.Does(crafter, Verb.Bind)) v.AddChild(Binding(it, k, open, ad));"""),
("""        if (row.GetChildCount() == 0) return null;""",
"""        if (Crafting.Does(crafter, Verb.Steep))
        {
            var q = Crafting.Steep(X, it, crafter);
            string odds = string.Join(";  ", Crafting.Odds().Select(o => $"{o.Chance:0%} {Odds(o.Outcome)}"));
            bool settled = q.Blocked != null && q.Takes.Keys.All(m => Inventory.Count(Ch, m) > 0) && q.Blocked != closed;
            row.AddChild(Tile(steeping ? "Steep it, and set it for good?" : "Steep in slurry", $"{Style.Cap1(odds)}. Whatever it comes to, it is set for good.", q, () =>
            {
                if (!steeping) { steeping = true; Sound.Sfx.Hover(); Refresh(); return; }
                steeping = false;
                Work(q, Sound.Sfx.Pour);
            }, steeping ? "Steep it" : "Steep", "steep", settled ? q.Blocked : null));
        }
        if (row.GetChildCount() == 0) return null;"""),
("""        if (a == Act.Cancel && breaking) { breaking = false; Refresh(); return true; }""",
"""        if (a == Act.Cancel && breaking) { breaking = false; Refresh(); return true; }
        if (a == Act.Cancel && (steeping || unmaking != null)) { steeping = false; unmaking = null; Refresh(); return true; }"""),
("""    /* ------------------------------------------------------ make me one -- */""",
"""    /* ---------------------------------------------------- the binder's -- */

    /// <summary>What can be bound into this seam: the powers in what the survivor carries that this kind
    /// of piece takes, each at the grade it would come in at. The thing it comes from is unmade, so a
    /// press is asked once and done the second time.</summary>
    Control Binding(ItemInstance it, int k, bool open, AffixDef? lost)
    {
        var v = Style.V(Style.Gap2);
        v.AddChild(new Section("Bind", lost != null ? $"in place of “{lost.Name}”, which is lost; what gives its power is unmade" : "a power lifted out of something you carry, which is unmade"));
        var donors = Crafting.Donors(Ch, it).Where(d => it.Affixes.Where((a, i) => open || i != k).All(a => a.Id != d.Donor.Affixes[d.Index].Id)).ToList();
        // A coal in what is carried will not come out for her: said in her words, once.
        bool caged = Ch.Pack.Any(p => p != null && p.Affixes.Any(a => Items.Affix(a.Id) is { Kindled: not null } c && c.Slots.Contains(Items.Get(it.Def).Kind)));
        if (donors.Count == 0)
        {
            v.AddChild(Quiet($"Carry something with a power this {Items.Get(it.Def).Kind.ToString().ToLowerInvariant()} would take: {He} lifts it out, and what it came from is gone. What you wear cannot give: take it off first."));
            if (caged && Crafting.Line(crafter, "bind.caged") is { } c1) v.AddChild(Quiet($"“{c1}”"));
            return v;
        }
        var grid = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", Style.Gap2);
        grid.AddThemeConstantOverride("v_separation", Style.Gap2);
        int n = 0;
        foreach (var (d, i) in donors)
        {
            var q = Crafting.Bind(X, it, d, i, open ? -1 : k, crafter);
            q.Before = null;
            string key = $"{d.Uid}:{i}";
            bool armed = unmaking == key;
            var dd = Items.Get(d.Def);
            string lead = armed ? $"{Inventory.Name(d)} is unmade for it. Again to bind." : $"{Items.Affix(d.Affixes[i].Id)?.Name} from {Inventory.Name(d)}";
            var card = Craft(armed ? "Unmake it" : "Bind", q, () =>
            {
                if (unmaking != key) { unmaking = key; Sound.Sfx.Hover(); Refresh(); return; }
                unmaking = null;
                Work(q, () => { Sound.Sfx.Cage(); Sound.Sfx.Discovery(); });
            }, lead, ItemPhotos.Icon(dd.Icon, 44, Style.RarityOf(d.Rarity)), $"bind:{n++}");
            card.CustomMinimumSize = new Vector2(452, 0);
            if (armed) card.Modulate = new Color(1.15f, 0.92f, 0.85f);
            grid.AddChild(card);
        }
        v.AddChild(grid);
        if (caged && Crafting.Line(crafter, "bind.caged") is { } c2) v.AddChild(Quiet($"Not the caged coals: “{c2}”"));
        return v;
    }

    /* ---------------------------------------------------- the slurry's -- */

    static string Odds(string outcome) => outcome switch
    {
        "up" => "a grade past what the forge can do",
        "affix" => "a slurry power past its seams, strong with a price",
        "nothing" => "only the veins",
        "down" => "a grade lost",
        _ => outcome,
    };

    /// <summary>A jar of the Dig's slurry: Snib's three a day, bought at his bench.</summary>
    Control JarTile()
    {
        var q = Crafting.BuyJar(X);
        var s = Crafting.Rules.Slurry;
        var panel = Style.Panel(Style.Box(new Color("#141a12"), new Color("#4a7a3a") with { A = 0.6f }, 1, 5, 10));
        var h = Style.H(Style.Gap3);
        h.AddChild(ItemPhotos.Icon(Items.Get(s.Jar).Icon, 48, new Color("#8acf6a")));
        var words = Style.V(1);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        int carry = Inventory.Count(Ch, s.Jar), left = Crafting.JarsLeft(G.Journey.World);
        words.AddChild(Style.Label("A jar of slurry", Style.UiBold, Style.Body, new Color("#a8e08a")));
        words.AddChild(Style.Label(q.Ok ? $"{q.Gold} gold  ·  {left} left today  ·  you carry {carry}" : q.Blocked!, Style.TextItalic, Style.Caption, q.Ok ? Style.InkDim : Style.Bad, true));
        h.AddChild(words);
        var b = Style.Button("Buy", null, q.Ok, true);
        b.Disabled = !q.Ok;
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        b.Pressed += () => { if (!q.Ok) { Sound.Sfx.Deny(); return; } Sound.Sfx.Loot(false); if (G.Journey.Make(q)) Refresh(); };
        Nav.Mark(b, "jar", () => b.EmitSignal(BaseButton.SignalName.Pressed));
        h.AddChild(b);
        panel.AddChild(h);
        return panel;
    }

    /* ------------------------------------------------------ make me one -- */"""),
])
