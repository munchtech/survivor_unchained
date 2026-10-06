p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
pairs = [
# --- Sheet
("""        left.AddChild(Style.Label($"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", Style.UiBold, 15, Style.Ink, true));
        double need = Character.XpForLevel(ch.Level);
        left.AddChild(Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need}", Style.Ember));""",
"""        left.AddChild(Style.Label($"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", Style.UiBold, Style.Small, Style.Ink, true));
        double need = Character.XpForLevel(ch.Level);
        // Experience in the day's cool colour, as the HUD's bar has it by day.
        left.AddChild(Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need} to level {ch.Level + 1}", Style.Day));"""),
("""        var artRow = Style.H(6, Glyphs.Icon(ab.Icon, 18), Style.Label($"{ab.Name}  ·  rank {ArtBook.Rank(ch, ch.Ability)}", Style.UiBold, 15, Style.GoldHi), Style.Key(G.Key(Act.Arts)));""",
"""        var artRow = Style.H(6, Glyphs.Icon(ab.Icon, 18), Style.Label($"{ab.Name}  ·  rank {ArtBook.Rank(ch, ch.Ability)}", Style.UiBold, Style.Small, Style.GoldHi), Style.Key(G.Key(Act.Arts)));"""),
("""        arts.CustomMinimumSize = new Vector2(260, 30);""",
"""        arts.CustomMinimumSize = new Vector2(260, 34);"""),
("""        left.AddChild(Style.Label($"Knows: {(knows == "" ? "little" : knows)}", Style.TextItalic, 14, Style.InkDim, true));""",
"""        left.AddChild(Style.Label($"Knows: {(knows == "" ? "little" : knows)}", Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
("""        mid.AddChild(Style.H(8, Style.SubLabel("Attributes"), ch.Points > 0 ? Style.Label($"{ch.Points} to spend", Style.UiBold, 13, Style.EmberHi) : new Control()));""",
"""        mid.AddChild(Style.H(8, Style.SubLabel("Attributes"), ch.Points > 0 ? Style.Label($"{ch.Points} to spend", Style.UiBold, Style.Caption, Style.EmberHi) : new Control()));"""),
("""            var words = Style.V(0, Style.Label(name, Style.UiBold, 16, Style.Ink), Style.Label(text, Style.Ui, 13, Style.InkDim, true));""",
"""            var words = Style.V(0, Style.Label(name, Style.UiBold, Style.Body, Style.Ink), Style.Label(text, Style.Ui, Style.Caption, Style.InkDim, true));"""),
("""            if (ch.Points > 0) { var attr = id; r.AddChild(Style.Button("+", () => G.Gear((j, b) => j.SpendPoint(attr, b)), false, true)); }""",
"""            if (ch.Points > 0) { var attr = id; r.AddChild(Nav.Id(Style.Button("+", () => G.Gear((j, b) => j.SpendPoint(attr, b)), true, true), $"attr:{attr}")); }"""),
("""        right.AddChild(Style.H(8, Style.SubLabel("Traits"), ch.TraitPicks > 0 ? Style.Label($"choose {ch.TraitPicks}", Style.UiBold, 13, Style.EmberHi) : new Control()));
        if (ch.Traits.Count == 0 && ch.TraitPicks == 0) right.AddChild(Style.Label("None yet. Traits come with levels, and with what you do.", Style.TextItalic, 14, Style.InkDim, true));
        foreach (var t in ch.Traits)
        {
            var def = Callings.Trait(t);
            right.AddChild(Style.V(0, Style.Label((def?.Name ?? t) + (def?.Source == TraitSource.World ? " · earned" : ""), Style.UiBold, 15, def?.Source == TraitSource.World ? Style.EmberHi : Style.GoldHi),
                Style.Label(def?.Text ?? "", Style.Ui, 13, Style.InkDim, true)));
        }""",
"""        right.AddChild(Style.H(8, Style.SubLabel("Traits"), ch.TraitPicks > 0 ? Style.Label($"choose {ch.TraitPicks}", Style.UiBold, Style.Caption, Style.EmberHi) : new Control()));
        if (ch.Traits.Count == 0 && ch.TraitPicks == 0) right.AddChild(Style.Label("None yet. Traits come with levels, and with what you do.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        foreach (var t in ch.Traits)
        {
            var def = Callings.Trait(t);
            right.AddChild(Style.V(0, Style.Label((def?.Name ?? t) + (def?.Source == TraitSource.World ? " · earned" : ""), Style.UiBold, Style.Small, def?.Source == TraitSource.World ? Style.EmberHi : Style.GoldHi),
                Style.Label(def?.Text ?? "", Style.Ui, Style.Caption, Style.InkDim, true)));
        }"""),
("""                var inner = Style.V(0, Style.Label(def.Name, Style.UiBold, 15, Style.GoldHi), Style.Label(def.Text, Style.Ui, 13, Style.Ink, true));
                inner.Position = new Vector2(12, 6);
                inner.Size = new Vector2(360, 48);
                b.CustomMinimumSize = new Vector2(380, 60);""",
"""                var inner = Style.V(0, Style.Label(def.Name, Style.UiBold, Style.Small, Style.GoldHi), Style.Label(def.Text, Style.Ui, Style.Caption, Style.Ink, true));
                inner.Position = new Vector2(12, 6);
                inner.Size = new Vector2(360, 52);
                inner.MouseFilter = MouseFilterEnum.Ignore;
                b.CustomMinimumSize = new Vector2(380, 66);
                Nav.Id(b, $"trait:{t}");"""),
("""            right.AddChild(Style.Label($"{Cond.GetValueOrDefault(c.Id, c.Id.ToString())}  ·  {c.Days} day{(c.Days == 1 ? "" : "s")}", Style.UiBold, 14, good ? Style.Good : Style.Bad, true));
        }
        row.AddChild(right);
    }""",
"""            right.AddChild(Style.H(6, Glyphs.Icon(good ? "sun" : "skull", 15, good ? Style.Good : Style.Bad), Style.Label($"{Cond.GetValueOrDefault(c.Id, c.Id.ToString())}  ·  {c.Days} day{(c.Days == 1 ? "" : "s")}", Style.UiBold, Style.Caption, good ? Style.Good : Style.Bad, true)));
        }
        row.AddChild(right);
        body.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        if (ch.Points > 0 || ch.TraitPicks > 0)
            body.AddChild(Controls.Instance.UsingPad ? Footer((Act.Confirm, ch.Points > 0 ? "Spend a point" : "Choose a trait"), (Act.TabNext, "Next page"), (Act.Cancel, "Close"))
                : MouseFooter(ch.Points > 0 ? "Click + to spend a point" : "Click a trait to take it"));
        else if (Controls.Instance.UsingPad) body.AddChild(Footer((Act.TabPrev, "Pack"), (Act.TabNext, "Arts"), (Act.Cancel, "Close")));
    }"""),
("""        var p = new Panel { CustomMinimumSize = new Vector2(width, 18), MouseFilter = MouseFilterEnum.Ignore };
        p.AddThemeStyleboxOverride("panel", Style.Box(new Color(0.04f, 0.035f, 0.05f), Style.GoldDim, 1, 3, 0));
        p.AddChild(new ColorRect { Color = color, Position = new Vector2(2, 2), Size = new Vector2((width - 4) * (float)Math.Clamp(k, 0, 1), 14), MouseFilter = MouseFilterEnum.Ignore });
        var l = Style.Label(text, Style.UiBold, 12, Style.Ink, false, HorizontalAlignment.Center);
        l.Size = new Vector2(width, 18);""",
"""        var p = new Panel { CustomMinimumSize = new Vector2(width, 20), MouseFilter = MouseFilterEnum.Ignore };
        p.AddThemeStyleboxOverride("panel", UiArt.Frame("bar_track", Style.Box(new Color(0.04f, 0.035f, 0.05f), Style.GoldDim, 1, 3, 0)));
        p.AddChild(new ColorRect { Color = color with { A = 0.85f }, Position = new Vector2(2, 2), Size = new Vector2((width - 4) * (float)Math.Clamp(k, 0, 1), 16), MouseFilter = MouseFilterEnum.Ignore });
        var l = Style.Label(text, Style.UiBold, Style.Badge, Style.Ink, false, HorizontalAlignment.Center);
        l.Size = new Vector2(width, 20);
        l.VerticalAlignment = VerticalAlignment.Center;"""),
# --- Journal
("""    public override bool Key(Act a)
    {
        string[] tabs = { "quests", "people", "deeds", "codex" };
        int i = Array.IndexOf(tabs, tab);
        if (a == Act.TabNext) { tab = tabs[(i + 1) % tabs.Length]; Refresh(); return true; }
        if (a == Act.TabPrev) { tab = tabs[(i + tabs.Length - 1) % tabs.Length]; Refresh(); return true; }
        return false;
    }""",
"""    static readonly (string Id, string Name)[] Sections = { ("quests", "Quests"), ("people", "People"), ("deeds", "Deeds"), ("codex", "Codex") };

    public override bool Key(Act a)
    {
        int i = Array.FindIndex(Sections, x => x.Id == tab);
        // Its own pages turn with LT and RT (, and .); LB and RB turn the book's.
        if (a == Act.SubNext) { tab = Sections[(i + 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Hover(); return true; }
        if (a == Act.SubPrev) { tab = Sections[(i + Sections.Length - 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Hover(); return true; }
        // Pages with nothing to choose on them scroll.
        if (a is Act.Up or Act.Down && tab != "quests" && page is { } sc && IsInstanceValid(sc))
        {
            Nav.KeyMode = true;
            sc.ScrollVertical += a == Act.Down ? 90 : -90;
            return true;
        }
        return false;
    }

    ScrollContainer? page;"""),
("""        AddChild(Style.Scrim(G.CloseOverlay));
        var wrap = Style.Centered(Style.V(0), new Vector2(1240, 720));
        AddChild(wrap);
        var tabs = Style.H(4);
        foreach (var (id, name) in new[] { ("quests", "Journal"), ("people", "People"), ("deeds", "Deeds"), ("codex", "Codex") })
        {
            var b = Style.Button(name, () => { tab = id; Refresh(); }, tab == id);
            tabs.AddChild(b);
        }
        var spacer = new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill };
        tabs.AddChild(spacer);
        tabs.AddChild(Style.Button($"{G.Key(Act.Journal)}  Close", G.CloseOverlay, false, true));
        wrap.AddChild(tabs);
        var book = Style.Panel(Style.Paper(26));
        book.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(book);
        book.AddChild(tab switch { "people" => People(), "deeds" => Deeds(), "codex" => Codex(), _ => Quests() });
    }

    static Label P(string text, int size = 16, Font? font = null, Color? color = null) => Style.Label(text, font ?? Style.Text, size, color ?? Ink, true, HorizontalAlignment.Left, false);
    static Label H2(string text) => Style.Label(text, Style.Display, 22, new Color("#3a2414"), true, HorizontalAlignment.Left, false);

    static HBoxContainer Two(Control a, Control b)
    {
        var h = Style.H(30);
        a.SizeFlagsHorizontal = b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        h.AddChild(Style.Scroll(a));
        h.AddChild(Style.Scroll(b));
        return h;
    }""",
"""        AddChild(Style.Scrim(G.CloseOverlay));
        var wrap = Style.Centered(Style.V(0), new Vector2(1240, 720));
        AddChild(wrap);
        BookTabs(new Vector2((1920 - 1240) / 2, (1080 - 720) / 2 - 46));
        // The journal's own sections: ribbons on the book's top edge, turned with LT and RT.
        var tabs = Style.H(4);
        bool pad = Controls.Instance.UsingPad;
        tabs.AddChild(pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev)));
        foreach (var (id, name) in Sections)
        {
            var b = Style.Button(name, () => { tab = id; Refresh(); }, tab == id);
            Nav.Skip(b);
            tabs.AddChild(b);
        }
        tabs.AddChild(pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext)));
        var spacer = new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill };
        tabs.AddChild(spacer);
        tabs.AddChild(Nav.Skip(CloseButton(G.Key(Act.Journal), G.CloseOverlay)));
        wrap.AddChild(tabs);
        var book = Style.Panel(Style.Paper(26));
        book.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(book);
        page = null;
        book.AddChild(tab switch { "people" => People(), "deeds" => Deeds(), "codex" => Codex(), _ => Quests() });
    }

    // Reading text on paper: body size, the ink of a hand that wrote it.
    static Label P(string text, int size = Style.Body, Font? font = null, Color? color = null) => Style.Label(text, font ?? Style.Text, size, color ?? Ink, true, HorizontalAlignment.Left, false);
    static Label H2(string text) => Style.Label(text, Style.Display, Style.Title, new Color("#3a2414"), true, HorizontalAlignment.Left, false);

    HBoxContainer Two(Control a, Control b)
    {
        var h = Style.H(30);
        a.SizeFlagsHorizontal = b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        page = Style.Scroll(a);
        h.AddChild(page);
        h.AddChild(Style.Scroll(b));
        return h;
    }"""),
("""            side.AddChild(Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 12, InkSoft, false, HorizontalAlignment.Left, false));""",
"""            side.AddChild(Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Badge, InkSoft, false, HorizontalAlignment.Left, false));"""),
("""                var b = new Button { Text = (def.Mystery ? "? " : "• ") + def.Name, Alignment = HorizontalAlignment.Left, FocusMode = FocusModeEnum.None, Flat = true };
                Style.Font(b, quest == id ? Style.TextBold : Style.Text, 17, quest == id ? Red : Ink, false);""",
"""                var b = new Button { Text = (def.Mystery ? "? " : "• ") + def.Name, Alignment = HorizontalAlignment.Left, FocusMode = FocusModeEnum.None, Flat = true };
                Nav.Id(b, $"quest:{id}");
                Style.Font(b, quest == id ? Style.TextBold : Style.Text, Style.Body, quest == id ? Red : Ink, false);"""),
("""        if (list.Count == 0) side.AddChild(P("Nothing written yet.", 16, Style.TextItalic, InkSoft));""",
"""        if (list.Count == 0) side.AddChild(P("Nothing written yet. What people ask of you is written here as you hear it.", Style.Small, Style.TextItalic, InkSoft));"""),
("""            page.AddChild(P(qd.Summary, 16, Style.TextItalic, InkSoft));""",
"""            page.AddChild(P(qd.Summary, Style.Body, Style.TextItalic, InkSoft));"""),
("""            if (qst.Outcome != null && qd.Outcomes?.GetValueOrDefault(qst.Outcome) is string o) page.AddChild(P(o, 16, Style.TextBold, Red));
            if (qst.StartedDay is int d) page.AddChild(P($"Begun on day {d}", 13, Style.TextItalic, InkSoft));
        }
        else page.AddChild(P("Choose an entry.", 16, Style.TextItalic, InkSoft));""",
"""            if (qst.Outcome != null && qd.Outcomes?.GetValueOrDefault(qst.Outcome) is string o) page.AddChild(P(o, Style.Body, Style.TextBold, Red));
            if (qst.StartedDay is int d) page.AddChild(P($"Begun on day {d}", Style.Caption, Style.TextItalic, InkSoft));
        }
        else if (list.Count > 0) page.AddChild(P("Choose an entry.", Style.Body, Style.TextItalic, InkSoft));"""),
("""        if (met.Count == 0) return P("You have not met anyone yet.", 16, Style.TextItalic, InkSoft);""",
"""        if (met.Count == 0) return P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft);"""),
("""            v.AddChild(Style.H(10, Style.Label(d.Name, Style.Display, 19, new Color("#3a2414"), false, HorizontalAlignment.Left, false),
                P(d.Role + (s.Alive ? "" : " · dead"), 14, Style.TextItalic, InkSoft), P(Rules.Attitude(s), 14, Style.TextBold, Red)));
            if (s.Alive && Lore.ConcernOf(d.Id, ctx) is string mind) v.AddChild(P(mind, 15, Style.TextItalic));""",
"""            v.AddChild(Style.H(10, Style.Label(d.Name, Style.Display, 20, new Color("#3a2414"), false, HorizontalAlignment.Left, false),
                P(d.Role + (s.Alive ? "" : " · dead"), Style.Caption, Style.TextItalic, InkSoft), P(Rules.Attitude(s), Style.Caption, Style.TextBold, Red)));
            if (s.Alive && Lore.ConcernOf(d.Id, ctx) is string mind) v.AddChild(P(mind, Style.Small, Style.TextItalic));"""),
("""                axes.AddChild(P(label, 13, Style.Ui, InkSoft));""",
"""                axes.AddChild(P(label, Style.Caption, Style.Ui, InkSoft));"""),
("""            if (heard.Count > 0) v.AddChild(P($"Knows that you {string.Join("; ", heard)}.", 14, Style.Text, InkSoft));
            grid.AddChild(v);
        }
        return Style.Scroll(grid);""",
"""            if (heard.Count > 0) v.AddChild(P($"Knows that you {string.Join("; ", heard)}.", Style.Caption, Style.Text, InkSoft));
            grid.AddChild(v);
        }
        page = Style.Scroll(grid);
        return page;"""),
("""            left.AddChild(Style.V(1, P($"Day {h.Day}", 12, Style.UiHeavy, InkSoft), P($"You {h.Text}."),
                P(knowers.Count > 0 ? $"Known to {string.Join(", ", knowers)}" : h.Spread > 0 ? "Word has not got round yet." : "Nobody saw.", 13, Style.TextItalic, InkSoft)));""",
"""            left.AddChild(Style.V(1, P($"Day {h.Day}", Style.Badge, Style.UiHeavy, InkSoft), P($"You {h.Text}."),
                P(knowers.Count > 0 ? $"Known to {string.Join(", ", knowers)}" : h.Spread > 0 ? "Word has not got round yet." : "Nobody saw.", Style.Caption, Style.TextItalic, InkSoft)));"""),
("""            right.AddChild(Style.V(1, Style.H(10, P(st.Name, 17, Style.TextBold), P(st.Word, 15, Style.TextItalic, tone)), P(st.Why, 14, Style.Text, InkSoft)));
        }
        right.AddChild(Style.Rule());
        right.AddChild(P($"Days on the road: {w.Day}    Creatures slain: {ch.Stats.Kills}    Falls: {ch.Stats.Deaths}    Gold earned: {Math.Floor(ch.Stats.GoldEarned)}", 14, Style.UiBold, InkSoft));""",
"""            right.AddChild(Style.V(1, Style.H(10, P(st.Name, Style.Body, Style.TextBold), P(st.Word, Style.Small, Style.TextItalic, tone)), P(st.Why, Style.Caption, Style.Text, InkSoft)));
        }
        right.AddChild(Style.Rule());
        right.AddChild(P($"Days on the road: {w.Day}    Creatures slain: {ch.Stats.Kills}    Falls: {ch.Stats.Deaths}    Gold earned: {Math.Floor(ch.Stats.GoldEarned)}", Style.Caption, Style.UiBold, InkSoft));"""),
("""            left.AddChild(Style.V(1, P($"{e.Name}  × {n}", 16, Style.TextBold), P(e.Note, 14, Style.Text, InkSoft)));""",
"""            left.AddChild(Style.V(1, P($"{e.Name}  × {n}", Style.Body, Style.TextBold), P(e.Note, Style.Caption, Style.Text, InkSoft)));"""),
("""            right.AddChild(Style.V(1, P(found ? d.Name : "???", 16, Style.TextBold, found ? Ink : InkSoft), P(found ? d.Description : d.Hint, 14, Style.TextItalic, InkSoft)));""",
"""            right.AddChild(Style.V(1, P(found ? d.Name : "Not yet found", Style.Body, Style.TextBold, found ? Ink : InkSoft), P(found ? d.Description : d.Hint, Style.Caption, Style.TextItalic, InkSoft)));"""),
]
for old, new in pairs:
    assert old in s, old[:90]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
