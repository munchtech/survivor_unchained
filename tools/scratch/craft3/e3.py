"""The pack's break down and steep held, not asked twice."""
from ed import sub
P = "src/Ui/Pack.cs"
sub(P, [
    ("""    string? breaking;

    /// <summary>Breaking down cannot be undone either: asked once, done the second time (never in an arena).</summary>
    void BreakDown(ItemInstance it)
    {
        var q = Crafting.BreakDown(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        if (breaking != it.Uid) { breaking = it.Uid; Sound.Sfx.Hover(); ShowInspect(it); return; }
        breaking = null;
        if (sel == it.Uid) sel = null;""",
     """    /// <summary>Breaking down cannot be undone either: held to full, never asked twice (never in an arena).</summary>
    void BreakDown(ItemInstance it)
    {
        var q = Crafting.BreakDown(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        if (sel == it.Uid) sel = null;"""),
    ("""    string? steeping;

    /// <summary>Steeping, by the survivor's own hand (docs/CRAFTING_DESIGN.md 9): the odds said, asked
    /// once, done the second time; what it came to said after. Never in an arena.</summary>
    void Steep(ItemInstance it)
    {
        var q = Crafting.Steep(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        if (steeping != it.Uid) { steeping = it.Uid; breaking = null; leaving = null; Sound.Sfx.Hover(); ShowInspect(it); return; }
        steeping = null;
        Sound.Sfx.Pour();""",
     """    /// <summary>Steeping, by the survivor's own hand (docs/CRAFTING_DESIGN.md 9): the odds shown under the
    /// card while a jar is carried, the press held to full; what it came to said after. Never in an arena.</summary>
    void Steep(ItemInstance it)
    {
        var q = Crafting.Steep(G.Journey.Craft, it);
        if (!q.Ok || G.Journey.InArena) { Sound.Sfx.Deny(); return; }
        Sound.Sfx.Pour();"""),
    ("""    void Select(string uid) { sel = sel == uid ? null : uid; leaving = null; breaking = null; steeping = null; Refresh(); }""",
     """    void Select(string uid) { sel = sel == uid ? null : uid; leaving = null; Refresh(); }"""),
    ("""                var bb = Style.Button(breaking == it.Uid ? "Break it down for good" : $"Break down for {Items.Several(Crafting.Iron, bq.Gives[Crafting.Iron])}", () => BreakDown(it), false, true);
                // Asked again, in the colour of what cannot be undone.
                if (breaking == it.Uid) bb.AddThemeColorOverride("font_color", Style.Bad);
                acts.AddChild(bb);""",
     """                // Held, in the colour of what cannot be undone.
                acts.AddChild(Style.HoldButton($"Break down for {Items.Several(Crafting.Iron, bq.Gives[Crafting.Iron])}", () => BreakDown(it)));"""),
    ("""                var sb = Style.Button(steeping == it.Uid ? "Steep it, for good" : "Steep in slurry", () => Steep(it), false, true);
                if (steeping == it.Uid) sb.AddThemeColorOverride("font_color", Style.Bad);
                acts.AddChild(sb);""",
     """                acts.AddChild(Style.HoldButton("Steep", () => Steep(it)));"""),
    ("""    /// <summary>Asked to steep: everything it could come to, said before the jar is opened (design 9).</summary>
    void SteepOdds(ItemInstance it)
    {
        if (steeping != it.Uid) return;
        // The same odds as at Snib's bench, laid out for this piece; asked again in red.
        var lines = Style.V(Style.Gap2, Style.Label("Opened, the jar does one of these, and the piece is set for good after:", Style.UiBold, Style.Small, Style.Bad, true),
            ForgeScreen.SlurryOdds(it, 450));
        var slab = Style.Panel(Style.Box(new Color("#121a10"), Style.Bad with { A = 0.7f }, 2, 5, 12), lines);""",
     """    /// <summary>A jar carried and a piece it can take: everything it could come to, seen before the jar is
    /// opened (design 9), the same odds as at Snib's bench, laid out for this piece.</summary>
    void SteepOdds(ItemInstance it)
    {
        if (G.Journey.InArena || Controls.Instance.UsingPad || Inventory.Count(Ch, Crafting.Rules.Slurry.Jar) == 0 || !Crafting.Steep(G.Journey.Craft, it).Ok) return;
        var lines = Style.V(Style.Gap2, Style.Label("Steeped, it comes to one of these, and is set for good after:", Style.UiBold, Style.Small, Style.Ink, true),
            ForgeScreen.SlurryOdds(it, 450));
        var slab = Style.Panel(Style.Box(new Color("#121a10"), ItemViews.SlurryGreen with { A = 0.45f }, 1, 5, 12), lines);"""),
    ("""            case Act.Cancel when leaving != null || breaking != null || steeping != null:
                leaving = null;
                breaking = null;
                steeping = null;
                Footer();""",
     """            case Act.Cancel when leaving != null:
                leaving = null;
                Footer();"""),
])
