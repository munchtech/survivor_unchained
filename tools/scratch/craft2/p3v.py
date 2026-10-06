from ed import sub
sub('src/Ui/Pack.cs', [
("""        broke = (Inventory.Name(it), string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))), q.Gives.Keys.First(), Time.GetTicksMsec());""",
"""        broke = ($"Broken down: {Inventory.Name(it)}", $"{Style.Cap1(string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))))}, into the pouch for the forge.",
            Items.Get(q.Gives.Keys.First()).Icon, Time.GetTicksMsec());"""),
("""    /// <summary>What was just broken down, and what it came to (said in the reading place).</summary>
    (string Name, string Gives, string Icon, ulong At)? broke;""",
"""    /// <summary>What was just done to a thing and what it came to (broken down, steeped), said in the
    /// reading place: the HUD's toasts are under the pack.</summary>
    (string Title, string Sub, string Icon, ulong At)? broke;

    string? steeping;

    /// <summary>Steeping, by the survivor's own hand (docs/CRAFTING_DESIGN.md 9): the odds said, asked
    /// once, done the second time; what it came to said after. Never in an arena.</summary>
    void Steep(ItemInstance it)
    {
        var q = Crafting.Steep(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        if (steeping != it.Uid) { steeping = it.Uid; breaking = null; leaving = null; Sound.Sfx.Hover(); ShowInspect(it); return; }
        steeping = null;
        Sound.Sfx.Pour();
        if (!G.Journey.Work(it.Uid, q, G.Battle)) return;
        broke = ($"Steeped: {Inventory.Name(it)}", G.Journey.CraftSaid?.After ?? "Green-black veins. It is set for good.", Items.Get(it.Def).Icon, Time.GetTicksMsec());
        sel = null;
        Refresh();
    }"""),
("""            var words = Style.V(1, Style.Label($"Broken down: {b.Name}", Style.UiBold, Style.Body, Style.Ink, true),
                Style.Label($"{Style.Cap1(b.Gives)}, into the pouch for the forge.", Style.TextItalic, Style.Small, Style.InkDim, true));""",
"""            var words = Style.V(1, Style.Label(b.Title, Style.UiBold, Style.Body, Style.Ink, true),
                Style.Label(b.Sub, Style.TextItalic, Style.Small, Style.InkDim, true));"""),
("""            var row = Style.H(Style.Gap3, ItemPhotos.Icon(Items.Get(b.Icon).Icon, 48, Style.InkDim), words);""",
"""            var row = Style.H(Style.Gap3, ItemPhotos.Icon(b.Icon, 48, Style.InkDim), words);"""),
("""    void Select(string uid) { sel = sel == uid ? null : uid; leaving = null; breaking = null; Refresh(); }""",
"""    void Select(string uid) { sel = sel == uid ? null : uid; leaving = null; breaking = null; steeping = null; Refresh(); }"""),
("""            case Act.Cancel when leaving != null || breaking != null:
                leaving = null;
                breaking = null;""",
"""            case Act.Cancel when leaving != null || breaking != null || steeping != null:
                leaving = null;
                breaking = null;
                steeping = null;"""),
("""                if (breaking == it.Uid) bb.AddThemeColorOverride("font_color", Style.Bad);
                acts.AddChild(bb);
            }""",
"""                if (breaking == it.Uid) bb.AddThemeColorOverride("font_color", Style.Bad);
                acts.AddChild(bb);
            }
            // A jar of the Dig's slurry carried: the one gamble, by the survivor's own hand.
            if (!G.Journey.InArena && Inventory.Count(Ch, Crafting.Rules.Slurry.Jar) > 0 && Crafting.Steep(G.Journey.Craft, it) is { Ok: true })
            {
                var sb = Style.Button(steeping == it.Uid ? "Steep it, for good" : "Steep in slurry", () => Steep(it), false, true);
                if (steeping == it.Uid) sb.AddThemeColorOverride("font_color", Style.Bad);
                acts.AddChild(sb);
            }"""),
])
