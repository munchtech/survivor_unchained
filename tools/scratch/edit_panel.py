import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('src/Ui/Panels.cs', [
("""/// <summary>What the level-up draft shows, and what picking does.</summary>
public sealed record DraftView(int Level, bool Blessing, List<Offer> Offers, int Rerolls, int Banishes, int Queued, string? Tip, HashSet<Tag> Build,
    Action<int> Pick, Action Reroll, Action<int> Banish, string? Great = null);""",
"""/// <summary>What the level-up draft shows, and what picking does: the cards,
/// the tools (reroll, banish, skip), the paths the build walks and its arsenal
/// with what each skill needs to evolve or unite.</summary>
public sealed record DraftView(int Level, bool Blessing, List<Offer> Offers, int Rerolls, int Banishes, int Queued, string? Tip, HashSet<Tag> Build,
    Action<int> Pick, Action Reroll, Action<int> Banish, string? Great = null, Action? Skip = null,
    List<LevelUp.ArsenalLine>? Arsenal = null, List<string>? Paths = null);"""),
("""/// <summary>
/// The ember draft (the web game's overlays/LevelUp.tsx). Time stops; the
/// cards rise out of the dark. Each says in one glance what it is (a new
/// skill, a rank, a blessing), what it touches (its school's colour, tags
/// lit where the build already has them) and how rare it is (the frame).
/// Keys 1-4 take a card, the arrows and Enter too; for a moment after the
/// cards appear they cannot be taken, so a key still held from the fight
/// does not spend a level by accident.
/// </summary>""", """/// <summary>
/// The ember draft (the web game's overlays/LevelUp.tsx). Time stops; the
/// cards rise out of the dark. Each says in one glance what it is (a new
/// skill, a rank, a blessing), what it touches (its school's colour, tags
/// lit where the build already has them), how rare it is (the frame), the
/// path it belongs to and why the ember dealt it (attuned, evolves
/// something, on your path), and for a combat skill what it becomes. Under
/// the cards, the arsenal: each skill carried, its rank, and what it still
/// needs. Keys 1-4 take a card, the arrows and Enter too, X rerolls, B then
/// a number banishes, V skips; for a moment after the cards appear they
/// cannot be taken, so a key still held from the fight does not spend a
/// level by accident.
/// </summary>"""),
("""        AddChild(Style.Scrim(null, 0.72f));
        var col = Style.V(10);
        col.Position = new Vector2(0, 150);
        col.Size = new Vector2(1920, 780);
        AddChild(col);""", """        AddChild(Style.Scrim(null, 0.74f));
        var col = Style.V(8);
        col.Position = new Vector2(0, 70);
        col.Size = new Vector2(1920, 960);
        AddChild(col);"""),
("""        if (v.Queued > 0) col.AddChild(Style.Label($"{v.Queued} more to choose", Style.UiBold, 16, Style.InkDim, false, HorizontalAlignment.Center));
        if (v.Tip != null) col.AddChild(Style.Label(v.Tip, Style.TextItalic, 18, Style.Ink, true, HorizontalAlignment.Center));
        col.AddChild(Style.Gap(20));""", """        if (v.Queued > 0) col.AddChild(Style.Label($"{v.Queued} more to choose", Style.UiBold, 16, Style.InkDim, false, HorizontalAlignment.Center));
        if (v.Paths is { Count: > 0 } paths)
            col.AddChild(Style.Label($"Walking {string.Join(" and ", paths)}", Style.TextItalic, 17, Style.EmberHi, false, HorizontalAlignment.Center));
        if (v.Tip != null) col.AddChild(Style.Label(v.Tip, Style.TextItalic, 18, Style.Ink, true, HorizontalAlignment.Center));
        col.AddChild(Style.Gap(14));"""),
("""        col.AddChild(Style.Gap(24));
        var foot = Style.H(12);
        foot.Alignment = BoxContainer.AlignmentMode.Center;
        var reroll = Style.Button($"{Controls.Instance.KeyLabel(Act.Reroll)}   Reroll  {v.Rerolls}", () => { if (armed && v.Rerolls > 0 && chosen == null) v.Reroll(); }, false, true);
        reroll.Disabled = v.Rerolls <= 0;
        var banish = Style.Button($"{Controls.Instance.KeyLabel(Act.Banish)}   Banish  {v.Banishes}", () => { banishing = !banishing; Mark(); }, false, true);
        banish.Disabled = v.Banishes <= 0;
        foot.AddChild(reroll);
        foot.AddChild(banish);
        col.AddChild(foot);
        Mark();
    }""", """        col.AddChild(Style.Gap(18));
        var foot = Style.H(12);
        foot.Alignment = BoxContainer.AlignmentMode.Center;
        var reroll = Style.Button($"{Controls.Instance.KeyLabel(Act.Reroll)}   Reroll  {v.Rerolls}", () => { if (armed && v.Rerolls > 0 && chosen == null) v.Reroll(); }, false, true);
        reroll.Disabled = v.Rerolls <= 0;
        reroll.TooltipText = "Look again: what was just shown is far less likely to come back. A milestone hands one back.";
        var banish = Style.Button($"{Controls.Instance.KeyLabel(Act.Banish)}   Banish  {v.Banishes}", () => { banishing = !banishing; Mark(); }, false, true);
        banish.Disabled = v.Banishes <= 0;
        banish.TooltipText = "Then a card: it never comes again in this arena.";
        foot.AddChild(reroll);
        foot.AddChild(banish);
        if (v.Skip != null)
        {
            var skip = Style.Button($"{Controls.Instance.KeyLabel(Act.Skip)}   Skip", () => { if (armed && chosen == null) v.Skip(); }, false, true);
            skip.TooltipText = $"Take none: {LevelUp.SkipRefund * 100:0}% of the level's ember comes back, so the next level comes sooner.";
            foot.AddChild(skip);
        }
        col.AddChild(foot);
        if (v.Arsenal is { Count: > 0 } arsenal) col.AddChild(Arsenal(arsenal));
        Mark();
    }

    /// <summary>The arsenal under the cards: each skill carried, its rank, and
    /// what it still needs (the passive that evolves it, the skill it joins).</summary>
    static Control Arsenal(List<LevelUp.ArsenalLine> lines)
    {
        var row = Style.H(14);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var l in lines)
        {
            var col = ItemViews.SchoolColors[l.School];
            var pips = Style.H(2);
            for (int k = 0; k < Weapons.MaxRank; k++)
                pips.AddChild(new ColorRect { CustomMinimumSize = new Vector2(7, 4), MouseFilter = MouseFilterEnum.Ignore, Color = k < l.Rank ? col : new Color("#2a2631") });
            var words = Style.V(1,
                Style.Label(l.Name, Style.UiBold, 14, l.Evolved ? Style.GoldHi : Style.Ink),
                pips,
                Style.Label(l.Note, Style.Ui, 12, l.Ready ? Style.EmberHi : Style.InkDim, true));
            words.CustomMinimumSize = new Vector2(196, 0);
            var item = Style.H(8, Glyphs.Icon(l.Icon, 30, l.Evolved ? Style.GoldHi : col), words);
            var plate = Style.Panel(Style.Box(new Color(0.05f, 0.045f, 0.06f, 0.85f), l.Ready ? Style.EmberHi with { A = 0.7f } : Style.Line, 1, 6, 8), item);
            plate.MouseFilter = MouseFilterEnum.Ignore;
            row.AddChild(plate);
        }
        return row;
    }"""),
("""    static string Kicker(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => "New combat skill",
        OfferKind.Rank => $"Combat skill · rank {o.From} to {o.To}",
        OfferKind.Evolve => "Evolution",""", """    static string Kicker(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => o.To is int r && r > 1 ? $"New combat skill · rank {r}" : "New combat skill",
        OfferKind.Rank => $"Combat skill · rank {o.From} to {o.To}",
        OfferKind.Evolve => "Evolution",
        OfferKind.Union => "Union",
        OfferKind.Hone => $"Honing · {o.To} of {LevelUp.MaxHone}","""),
("""        var r = o.Kind == OfferKind.Evolve ? 4 : (int)o.Rarity;
        var rc = Style.RarityOf(r);
        var school = SchoolOf(o);
        var color = o.Kind == OfferKind.Evolve ? new Color("#ffd88a") : school is School s ? ItemViews.SchoolColors[s] : rc;
        var b = new Button { CustomMinimumSize = new Vector2(300, 460), FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand };""",
"""        bool crown = o.Kind is OfferKind.Evolve or OfferKind.Union;
        var r = crown ? 4 : (int)o.Rarity;
        var rc = Style.RarityOf(r);
        var school = SchoolOf(o);
        var color = crown ? new Color("#ffd88a") : school is School s ? ItemViews.SchoolColors[s] : rc;
        var b = new Button { CustomMinimumSize = new Vector2(320, 560), FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand };"""),
("""        var v2 = Style.V(8);
        v2.Position = new Vector2(20, 20);
        v2.Size = new Vector2(260, 420);
        b.AddChild(v2);""", """        var v2 = Style.V(6);
        v2.Position = new Vector2(20, 18);
        v2.Size = new Vector2(280, 524);
        b.AddChild(v2);"""),
("""        var art = new CenterContainer { CustomMinimumSize = new Vector2(260, 140), MouseFilter = MouseFilterEnum.Ignore };
        art.AddChild(Glyphs.Icon(o.Icon, 76, color));""", """        var art = new CenterContainer { CustomMinimumSize = new Vector2(280, 108), MouseFilter = MouseFilterEnum.Ignore };
        art.AddChild(Glyphs.Icon(o.Icon, 72, color));"""),
("""        var text = o.Kind == OfferKind.Evolve && o.Text.Contains(" becomes ") && o.Text.IndexOf(". ") is int dot && dot > 0 ? o.Text[(dot + 2)..] : o.Text;
        var body = Style.Label(text, Style.Text, 17, Style.Ink, true, HorizontalAlignment.Center);
        body.SizeFlagsVertical = SizeFlags.ExpandFill;
        v2.AddChild(body);""", """        var text = o.Kind == OfferKind.Evolve && o.Text.Contains(" becomes ") && o.Text.IndexOf(". ") is int dot && dot > 0 ? o.Text[(dot + 2)..] : o.Text;
        var body = Style.Label(text, Style.Text, 17, Style.Ink, true, HorizontalAlignment.Center);
        body.SizeFlagsVertical = SizeFlags.ExpandFill;
        v2.AddChild(body);
        // Why the ember dealt it: attuned, on your path, evolves something; a surge.
        foreach (var why in o.Why.Take(2))
            v2.AddChild(Style.Label(why, Style.UiBold, 14, why.StartsWith("Little") ? Style.InkDim : Style.EmberHi, true, HorizontalAlignment.Center));
        // What a combat skill becomes.
        if (o.Recipe is { Length: > 0 } recipe)
            v2.AddChild(Style.Label(recipe, Style.TextItalic, 13, Style.InkDim, true, HorizontalAlignment.Center));"""),
("""        if (fits) v2.AddChild(Style.Label("Fits your build", Style.UiBold, 13, Style.EmberHi, false, HorizontalAlignment.Center));
        var foot = Style.H(8, Style.Label(o.Kind == OfferKind.Evolve ? "Legendary" : o.Rarity.ToString(), Style.UiBold, 14, rc));""",
"""        if (o.Path is { } pid && Paths.Find(pid) is { } path) v2.AddChild(Style.Label(path.Name, Style.DisplayLight, 14, Style.Gold, false, HorizontalAlignment.Center));
        else if (fits) v2.AddChild(Style.Label("Fits your build", Style.UiBold, 13, Style.EmberHi, false, HorizontalAlignment.Center));
        var foot = Style.H(8, Style.Label(crown ? "Legendary" : o.Rarity.ToString(), Style.UiBold, 14, rc));"""),
("""        var ban = Style.Label("BANISH", Style.Display, 26, new Color("#ff8a6a"), false, HorizontalAlignment.Center);
        ban.Position = new Vector2(0, 200); ban.Size = new Vector2(300, 40);""", """        var ban = Style.Label("BANISH", Style.Display, 26, new Color("#ff8a6a"), false, HorizontalAlignment.Center);
        ban.Position = new Vector2(0, 240); ban.Size = new Vector2(320, 40);"""),
("""            case Act.Banish: if (v.Banishes > 0) { banishing = !banishing; Mark(); } break;""", """            case Act.Banish: if (v.Banishes > 0) { banishing = !banishing; Mark(); } break;
            case Act.Skip: if (armed && chosen == null) v.Skip?.Invoke(); break;"""),
])

edit('src/Game/GameMenus.cs', [
("""        hud.Draft(new DraftView(LevelUp.DraftLevel(b), LevelUp.BlessingNext(b), list, b.Rerolls, b.Banishes, LevelUp.Queued(b), tip,
            LevelUp.BuildTags(b), Pick, Reroll, Banish, great));""", """        hud.Draft(new DraftView(LevelUp.DraftLevel(b), LevelUp.BlessingNext(b), list, b.Rerolls, b.Banishes, LevelUp.Queued(b), tip,
            LevelUp.BuildTags(b), Pick, Reroll, Banish, great, LevelUp.CanSkip(b) ? Skip : null,
            LevelUp.Arsenal(b), LevelUp.BuildPaths(b).Select(p => p.Name).ToList()));"""),
])

edit('src/Ui/Menus.cs', [
("""("Draft: take a card", [Act.Pick1], "D-pad, A"), ("Draft: reroll", [Act.Reroll], null), ("Draft: banish", [Act.Banish], null),""",
"""("Draft: take a card", [Act.Pick1], "D-pad, A"), ("Draft: reroll", [Act.Reroll], null), ("Draft: banish", [Act.Banish], null), ("Draft: skip", [Act.Skip], "Right stick"),"""),
])
print('ok')
