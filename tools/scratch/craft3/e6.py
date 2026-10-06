"""The Wayfinder's table on the bench page: charts on the anvil, their mods as rows."""
from ed import sub
F = "src/Ui/Forge.cs"
sub(F, [
    ("""    bool Takes(ItemInstance it) =>
        Crafting.Workable(it) && (Crafting.Does(crafter, Verb.Temper) || Crafting.Does(crafter, Verb.Remake) || Crafting.WorkInChoices(it, crafter).Count > 0
            || Crafting.Does(crafter, Verb.Bind) || Crafting.Does(crafter, Verb.Steep));""",
     """    bool Takes(ItemInstance it) => Charting ? it.Chart != null :
        Crafting.Workable(it) && (Crafting.Does(crafter, Verb.Temper) || Crafting.Does(crafter, Verb.Remake) || Crafting.WorkInChoices(it, crafter).Count > 0
            || Crafting.Does(crafter, Verb.Bind) || Crafting.Does(crafter, Verb.Steep));

    /// <summary>The Wayfinder's table: charts on the anvil, not gear (design 20.4).</summary>
    bool Charting => Crafting.Does(crafter, Verb.Ink);

    /// <summary>What the next bench opened puts on its anvil first (the table's chart in hand).</summary>
    public static string? PutDown;"""),
    ("""        if (Args.Has("make") && Crafting.Does(crafter, Verb.Commission)) { making = true; pattern = Args.Get("pattern"); }""",
     """        if (Args.Has("make") && Crafting.Does(crafter, Verb.Commission)) { making = true; pattern = Args.Get("pattern"); }
        if (PutDown != null) { sel = PutDown; PutDown = null; }"""),
    ("""    IEnumerable<ItemInstance> Workable() =>
        Items.EquipSlots.Select(s => Ch.Equipment[s]).Concat(Ch.Pack).Where(it => it != null && Crafting.Workable(it)).Select(it => it!);""",
     """    IEnumerable<ItemInstance> Workable() => Charting ? Maps.Charts.Carried(Ch) :
        Items.EquipSlots.Select(s => Ch.Equipment[s]).Concat(Ch.Pack).Where(it => it != null && Crafting.Workable(it)).Select(it => it!);"""),
    ("""        if (Crafting.Does(crafter, Verb.Buy) && crafter == Crafting.Rules.Slurry.Crafter) v.AddChild(JarTile());
        v.AddChild(new Section("What you wear", "choose a piece"));""",
     """        if (Crafting.Does(crafter, Verb.Buy) && crafter == Crafting.Rules.Slurry.Crafter) v.AddChild(JarTile());
        if (Charting) { ChartsCarried(v); return; }
        v.AddChild(new Section("What you wear", "choose a piece"));"""),
    ("""        if (seam < 0 || seam >= Places(it)) seam = Places(it) > 0 ? DefaultSeam(it) : -1;
        var body = Style.V(Style.Gap3);
        body.AddChild(Head(it));""",
     """        if (it.Chart != null) { ChartAnvil(v, it); return; }
        if (seam < 0 || seam >= Places(it)) seam = Places(it) > 0 ? DefaultSeam(it) : -1;
        var body = Style.V(Style.Gap3);
        body.AddChild(Head(it));"""),
    ("""            v.AddChild(Style.Label(Crafting.Does(crafter, Verb.Temper)""",
     """            v.AddChild(Style.Label(Charting ? "Choose a chart you carry. A map's ruler leaves the next when it falls."
                : Crafting.Does(crafter, Verb.Temper)"""),
    ("""            Verb.Steep => q.Index,
            _ => -1,""",
     """            Verb.Steep => q.Index,
            // A chart's new mod rings where it was written; a pin where it holds.
            Verb.Ink => (Inventory.Find(Ch, uid)?.Item.Chart?.Mods.Count ?? 0) - 1,
            Verb.Pin => Inventory.Find(Ch, uid)?.Item.Chart?.Mods.IndexOf(q.Affix ?? "") ?? -1,
            _ => -1,"""),
    ("""                default: Sparks(row, at, now.Verb is Verb.Cage or Verb.Rekindle); break;""",
     """                case Verb.Ink or Verb.Pin or Verb.Scrape or Verb.Annotate: Motes(row, at, new Color("#f4ead0"), new Color("#9ab0d8"), -25, 1.4); break;
                default: Sparks(row, at, now.Verb is Verb.Cage or Verb.Rekindle or Verb.Burn); break;"""),
    ("""    /* ---------------------------------------------------- the slurry's -- */""",
     """    /* ------------------------------------------------- the Wayfinder's -- */

    /// <summary>The charts carried, to choose among (the highest tier first), and the pouch.</summary>
    void ChartsCarried(VBoxContainer v)
    {
        var charts = Maps.Charts.Carried(Ch).Cast<ItemInstance?>().ToList();
        v.AddChild(new Section("Your charts", charts.Count == 0 ? "none carried" : "choose one"));
        while (charts.Count < 10 || charts.Count % 5 != 0) charts.Add(null);
        v.AddChild(Grid(charts, "pack"));
        v.AddChild(new Section("The pouch", "materials, never in the pack"));
        var pouch = Inventory.Pouch(Ch).Cast<ItemInstance?>().ToList();
        while (pouch.Count % 5 != 0) pouch.Add(null);
        if (pouch.Count > 0) v.AddChild(Style.Panel(Style.Well(8), ItemViews.Grid(pouch, 5, 72, null, null, null, null, (it, over) => Tip(it != null ? ItemViews.Card(it, Ch, false) : null, over), "pouch")));
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var purse = Style.H(Style.Gap2, Glyphs.Icon("coin", 26, Style.GoldHi), Style.Label($"{Math.Floor(Ch.Gold)}", Style.Display, 30, Style.GoldHi), Style.Label("gold", Style.TextItalic, Style.Body, Style.InkDim));
        purse.Alignment = BoxContainer.AlignmentMode.Center;
        v.AddChild(purse);
    }

    /// <summary>A chart on the table (design 20.4): its mods as rows, the foe's then yours, one chosen to pin
    /// or scrape; what works the whole chart below (ink a side, burn and redraw, annotate); its heat the
    /// budget, as a piece's is.</summary>
    void ChartAnvil(VBoxContainer v, ItemInstance it)
    {
        var c = it.Chart!;
        var mods = c.Rolled.OrderBy(m => m.Prefix ? 0 : 1).ToList();
        if (seam >= mods.Count) seam = mods.Count > 0 ? 0 : -1;
        if (seam < 0 && mods.Count > 0) seam = 0;
        var body = Style.V(Style.Gap3);
        body.AddChild(Head(it));
        if (closed != null) body.AddChild(Style.Panel(Style.Slab(12), Style.Label(closed, Style.TextItalic, Style.Body, Style.Bad, true, HorizontalAlignment.Center)));
        var list = Style.V(Style.Gap1);
        list.AddChild(new Section("Sworn on it", mods.Count == 0 ? null : $"choose one to pin or scrape  ·  three to a side  ·  {Pct(c.Quantity - 1)} more found, {Pct(c.RarityBonus - 1)} finer"));
        if (mods.Count == 0) list.AddChild(Quiet("Sworn under nothing: plain ground, plain pay. Ink it to swear it to more, and to pay more."));
        for (int k = 0; k < mods.Count; k++) list.AddChild(ModRow(c, mods[k], c.Mods.IndexOf(mods[k].Id), k));
        body.AddChild(list);
        if (seam >= 0 && seam < mods.Count)
        {
            var m = mods[seam];
            var at = Style.V(Style.Gap2);
            at.AddChild(new Section(m.Name, m.Prefix ? "sworn for the foe" : "sworn against you"));
            var grid = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
            grid.AddThemeConstantOverride("h_separation", Style.Gap2);
            var pin = Crafting.Pin(X, it, m.Id, crafter);
            var pc = Craft("Pin it", pin, () => Work(pin, Sound.Sfx.Click), c.Pinned == m.Id ? "Pinned" : "Pin it", null, "pin");
            pc.CustomMinimumSize = new Vector2(452, 0);
            grid.AddChild(pc);
            var scrape = Crafting.Scrape(X, it, m.Id, crafter);
            scrape.Before = null;
            var sc = Craft("Scrape", scrape, () => Work(scrape, Sound.Sfx.Click), "Scrape it off", null, "scrape");
            sc.CustomMinimumSize = new Vector2(452, 0);
            grid.AddChild(sc);
            at.AddChild(grid);
            body.AddChild(at);
        }
        // The whole chart.
        var whole = Style.V(Style.Gap2);
        whole.AddChild(new Section("The chart itself"));
        var row = Style.H(Style.Gap3);
        var inkFoe = Crafting.Ink(X, it, true, crafter);
        row.AddChild(Tile("Ink the foe's side", inkFoe.After, inkFoe, () => Work(inkFoe, Sound.Sfx.Click), "Ink", "ink:foe", null));
        var inkYou = Crafting.Ink(X, it, false, crafter);
        row.AddChild(Tile("Ink your side", inkYou.After, inkYou, () => Work(inkYou, Sound.Sfx.Click), "Ink", "ink:you", null));
        whole.AddChild(row);
        var row2 = Style.H(Style.Gap3);
        var burn = Crafting.Burn(X, it, crafter);
        row2.AddChild(Tile("Burn and redraw", burn.After, burn, () => Work(burn, Sound.Sfx.Cage), "Burn", "burn", null));
        var from = Crafting.AnnotateFrom(Ch, it);
        var note = Crafting.Annotate(X, it, from, crafter);
        row2.AddChild(Tile("Annotate", from?.Chart is { } f ? $"{note.After}, written from {f.Name}, which is given up" : note.After, note,
            () => Work(note, Sound.Sfx.Page), "Annotate", "annotate", null));
        whole.AddChild(row2);
        body.AddChild(whole);
        var scroll = Style.Scroll(body);
        scroll.CustomMinimumSize = new Vector2(920, 880);
        v.AddChild(scroll);
    }

    static string Pct(double x) => $"{Math.Round(x * 100)}%";

    /// <summary>One mod sworn on a chart, sealed in wax beside its terms (the table's own look): red wax for
    /// the foe's side, violet for yours; what it asks, what it pays; pinned, said so.</summary>
    Control ModRow(Maps.Chart c, Maps.ChartMod m, int index, int k)
    {
        bool on = k == seam, pinned = c.Pinned == m.Id;
        var panel = Style.Panel(Style.Box(on ? new Color("#2a1c12") : new Color("#141118"), on ? Style.Focus : Style.Line with { A = 0.25f }, on ? 2 : 1, 5, 10));
        panel.MouseFilter = MouseFilterEnum.Stop;
        var seal = new Panel { CustomMinimumSize = new Vector2(34, 34), MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkCenter };
        var wax = Style.Box(m.Prefix ? new Color("#8a1c14") : new Color("#3a2a5a"), m.Prefix ? new Color("#5a0e0a") : new Color("#221636"), 2, 17, 0);
        wax.ShadowColor = new Color(0, 0, 0, 0.35f); wax.ShadowSize = 3; wax.ShadowOffset = new Vector2(1, 2);
        seal.AddThemeStyleboxOverride("panel", wax);
        var pays = new List<string>();
        if (m.Quantity > 0) pays.Add($"{Pct(m.Quantity)} more found");
        if (m.Rarity > 0) pays.Add($"{Pct(m.Rarity)} finer");
        if (m.PackSize > 0) pays.Add($"packs {Pct(m.PackSize)} larger");
        var words = Style.V(1, Style.Label(m.Says, Style.UiBold, Style.Body, Style.Ink, true),
            Style.Label($"{m.Name}  ·  pays {string.Join(", ", pays)}", Style.TextItalic, Style.Caption, Style.InkDim, true));
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var h = Style.H(Style.Gap3, seal, words);
        if (pinned) h.AddChild(Style.Label("pinned", Style.UiHeavy, Style.Badge, Style.GoldHi));
        if (on) h.AddChild(Style.Label("on the table", Style.UiHeavy, Style.Badge, Style.Focus));
        panel.AddChild(h);
        panel.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) Pick(k); };
        Nav.Mark(panel, $"seam:{k}", () => Pick(k));
        if (index >= 0) rows[index] = (panel, seal);
        return panel;
    }

    /* ---------------------------------------------------- the slurry's -- */"""),
])
# The head names a chart for what it is.
sub(F, [("""        var kind = Style.H(Style.Gap2, Style.Label($"{Inventory.RarityName(it)} {def.Kind.ToString().ToLowerInvariant()}", Style.Ui, Style.Small, Style.InkDim), Style.Gems(it.Rarity, 7));""",
         """        string what = it.Chart is { } ch ? $"{(ch.Rarity switch { 2 => "A rare chart", 1 => "A fine chart", _ => "A plain chart" })}, tier {ch.Tier}: {Maps.MapOffers.People(ch.People).Name}'s ground"
            : $"{Inventory.RarityName(it)} {def.Kind.ToString().ToLowerInvariant()}";
        var kind = Style.H(Style.Gap2, Style.Label(what, Style.Ui, Style.Small, Style.InkDim), Style.Gems(it.Rarity, 7));""")])
