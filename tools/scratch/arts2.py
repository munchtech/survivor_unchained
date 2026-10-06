R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
p = R + r'\ArtsScreen.cs'
s = open(p, encoding='utf-8').read()

def cut(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

cut("    protected override void Build()\n    {", "    /* ------------------------------------------------------ skills by day -- */", '''    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var known = ArtBook.Known(ch);
        sel ??= ch.Ability != "" ? ch.Ability : known.FirstOrDefault();
        var page = Page(skills ? "Skills by Day" : "Arts",
            skills ? "What the arenas showed you, learned for the day; what you carry is banked for the night"
            : Safe ? "One art in hand. Each grows with use, and its ranks open facets" : "Out here you can choose a facet a rank has opened; change your art where it is safe");
        // The screen's two pages, turned with LT and RT.
        bool pad = Controls.Instance.UsingPad;
        var tabs = Style.H(8, pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev)),
            Nav.Skip(Style.Segment("The art in hand", !skills, () => { skills = false; Refresh(); })), Nav.Skip(Style.Segment("Skills by day", skills, () => { skills = true; Refresh(); })),
            pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext)));
        tabs.Position = Vector2.Zero;
        page.AddChild(tabs);
        if (pad) PageFooter(Footer((Act.Confirm, "Choose"), (Act.SubNext, skills ? "The art in hand" : "Skills by day"), (Act.TabPrev, "Self"), (Act.TabNext, "Journal"), (Act.Cancel, "Close")));
        if (skills) { BuildSkills(page); return; }

        // Every art the calling could know, as medallions: learned first, then the rest, dim.
        var left = Pane(page, new Rect2(0, 56, 560, 864));
        left.AddChild(new Section($"Known  ·  {known.Count}"));
        left.AddChild(Medals(ch, known.Select(Abilities.ById), true));
        var rest = Abilities.All.Values.Where(a => !known.Contains(a.Id) && Abilities.Learnable(a, ch.Archetype)).ToList();
        if (rest.Count > 0)
        {
            left.AddChild(new Section("Not yet learned", "manuals teach them"));
            left.AddChild(Medals(ch, rest, false));
        }

        // The art chosen, on its altar: the great medallion, its rank, its sockets, its four facets.
        var right = Pane(page, new Rect2(590, 56, 1250, 864), null, Style.Gap4);
        if (sel != null && Abilities.Find(sel) is { } def) Altar(right, ch, def, known.Contains(def.Id));
    }

    /// <summary>A grid of arts as medallions, each with its name under it.</summary>
    Control Medals(CharacterData ch, System.Collections.Generic.IEnumerable<AbilityDef> arts, bool known)
    {
        var grid = new GridContainer { Columns = 3, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 12);
        grid.AddThemeConstantOverride("v_separation", 12);
        foreach (var a in arts)
        {
            bool held = ch.Ability == a.Id, on = sel == a.Id;
            int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
            var id = a.Id;
            var b = Style.Button("", () => { sel = id; Refresh(); }, false, true);
            Nav.Mark(b, $"art:{a.Id}", () => { sel = id; Refresh(); });
            b.CustomMinimumSize = new Vector2(160, 178);
            var box = OrnateBox.Make(OrnateBox.Kind.Slab, 8, held ? Style.Ember : Style.Gold);
            if (on) b.AddThemeStyleboxOverride("normal", box);
            var v = Style.V(4);
            v.MouseFilter = MouseFilterEnum.Ignore;
            v.Position = new Vector2(8, 8);
            v.Size = new Vector2(144, 160);
            var m = new Medallion(104, "", a.Icon)
            {
                Arc = known && rank < Abilities.MaxRank ? (float)ArtBook.Progress(ch, a.Id) : 0,
                Ring = held ? Style.Ember : known ? Style.Gold : Style.InkFaint,
                Ink = known ? (held ? Style.EmberHi : Style.GoldHi) : Style.InkDim with { A = 0.6f },
                Core = known ? new Color("#3a2210") : new Color("#16131a"),
                Lit = held,
            };
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(m);
            v.AddChild(mc);
            v.AddChild(Style.Label(a.Name, Style.UiBold, Style.Small, known ? (held ? Style.EmberHi : Style.GoldHi) : Style.InkDim, true, HorizontalAlignment.Center));
            v.AddChild(Style.Label(known ? (held ? "in hand" : $"rank {Numerals[rank - 1]}") + (ArtBook.OpenSlots(ch, a.Id) > 0 ? "  ·  a facet!" : "") : Roles[a.Role].Name,
                Style.Ui, Style.Caption, known ? Roles[a.Role].Color : Style.InkFaint, false, HorizontalAlignment.Center));
            b.AddChild(v);
            grid.AddChild(b);
        }
        return grid;
    }

    void Altar(VBoxContainer d, CharacterData ch, AbilityDef a, bool known)
    {
        int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
        var role = Roles[a.Role];
        bool held = ch.Ability == a.Id;
        var head = Style.H(Style.Gap5);
        // The great medallion with its two sockets beneath: the facets' places, opened by rank.
        var shrine = Style.V(Style.Gap2);
        shrine.Alignment = BoxContainer.AlignmentMode.Center;
        var big = new Medallion(220, "", a.Icon)
        {
            Arc = known && rank < Abilities.MaxRank ? (float)ArtBook.Progress(ch, a.Id) : known ? 1 : 0,
            Ring = held ? Style.Ember : known ? Style.Gold : Style.InkFaint,
            Ink = known ? Style.GoldHi : Style.InkDim,
            Lit = held,
        };
        var bc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        bc.AddChild(big);
        shrine.AddChild(bc);
        int slots = Abilities.FacetSlots(rank), chosen = known ? ArtBook.Facets(ch, a.Id).Count : 0;
        var sockets = Style.H(Style.Gap4);
        sockets.Alignment = BoxContainer.AlignmentMode.Center;
        for (int k = 0; k < 2; k++)
        {
            bool open = k < slots, filled = k < chosen;
            var sm = new Medallion(54, open ? "" : Numerals[k == 0 ? 1 : 3], filled ? "arcane" : null)
            {
                Ring = filled ? Style.Ember : open ? Style.GoldHi : Style.InkFaint,
                Core = filled ? new Color("#4a1c0c") : new Color("#120f14"),
                Ink = filled ? Style.EmberHi : Style.InkDim,
                Lit = open && !filled,
            };
            var sv = Style.V(2, sm, Style.Label(filled ? "set" : open ? "open" : $"rank {Numerals[k == 0 ? 1 : 3]}", Style.Ui, Style.Caption, filled ? Style.EmberHi : open ? Style.GoldHi : Style.InkFaint, false, HorizontalAlignment.Center));
            sockets.AddChild(sv);
        }
        shrine.AddChild(sockets);
        head.AddChild(shrine);

        var words = Style.V(Style.Gap2);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        words.AddChild(Style.Label(a.Name.ToUpperInvariant(), Style.Display, 44, held ? Style.EmberHi : Style.GoldHi));
        words.AddChild(Style.Label($"{role.Name}{(a.Movement ? "  ·  a way of moving" : $"  ·  a {Callings.Archetype(a.Calling!).Name}'s art")}  ·  {a.Cooldown:0} s{(a.Interrupts ? "  ·  breaks channels" : "")}", Style.UiBold, Style.Small, role.Color));
        words.AddChild(Style.Label(a.Description, Style.Text, Style.Lead, Style.Ink, true));
        if (!known)
        {
            words.AddChild(Style.Label("Not yet learned. A manual teaches it: the thing that rules an arena carries one, and they turn up in the packs of the dead.", Style.TextItalic, Style.Small, Style.InkDim, true));
        }
        else
        {
            double xp = ch.Arts.TryGetValue(a.Id, out var st) ? st.Xp : 0;
            string next = rank < Abilities.MaxRank ? $"{xp:0} / {Abilities.RankXp[rank]:0} to rank {Numerals[rank]}" : "Mastered";
            words.AddChild(Style.Gap(Style.Gap1));
            words.AddChild(Style.H(Style.Gap3, Style.Label($"Rank {Numerals[rank - 1]}", Style.Display, 26, Style.GoldHi), SheetScreen.Bar(rank < Abilities.MaxRank ? ArtBook.Progress(ch, a.Id) : 1, next, Style.Ember, 460)));
            words.AddChild(Style.Label($"+{(Abilities.RankPower(rank) - 1) * 100:0}% strength, {(1 - Abilities.RankHaste(rank)) * 100:0}% shorter wait.  It grows with every use, and with what dies while it is fresh.", Style.Ui, Style.Small, Style.InkDim, true));
            if (held) words.AddChild(Style.Label("IN HAND", Style.UiHeavy, Style.Body, Style.EmberHi));
            else if (Safe) words.AddChild(Style.Button($"Take {a.Name} in hand", () => G.Gear((j, b) => j.HoldArt(a.Id, b)), true));
            else words.AddChild(Style.Label("Take it in hand somewhere safe: the Waystation, a quiet road.", Style.TextItalic, Style.Small, Style.InkDim, true));
        }
        head.AddChild(words);
        d.AddChild(head);
        d.AddChild(Facets(ch, a, known));
    }

    /// <summary>The four facets as cards, each with its socket at its head: set, to choose, or waiting on a rank.</summary>
    Control Facets(CharacterData ch, AbilityDef a, bool known)
    {
        var v = Style.V(Style.Gap2);
        int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
        int slots = Abilities.FacetSlots(rank);
        var chosen = known ? ArtBook.Facets(ch, a.Id) : new();
        string opens = slots == 0 ? "rank II opens the first" : slots == 1 ? "rank IV opens the second" : "both open";
        v.AddChild(new Section("Facets", known ? $"{chosen.Count} of {slots} set  ·  {opens}" : "learn the art to set them"));
        var row = Style.H(Style.Gap3);
        foreach (var f in a.Facets)
        {
            bool on = chosen.Contains(f.Id);
            bool canPick = known && !on && chosen.Count < slots;
            bool canDrop = known && on && Safe;
            var accent = on ? Style.Ember : canPick ? Style.GoldHi : Style.InkFaint;
            var box = OrnateBox.Make(OrnateBox.Kind.Card, 14, accent);
            box.Crest = 70;
            var b = Style.Button("", canPick ? () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, true, bt)) : canDrop ? () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, false, bt)) : null);
            foreach (var stt in new[] { "normal", "hover", "pressed", "disabled" }) b.AddThemeStyleboxOverride(stt, box);
            b.CustomMinimumSize = new Vector2(287, 300);
            Nav.Id(b, $"facet:{f.Id}");
            b.Disabled = !canPick && !canDrop;
            var inner = Style.V(Style.Gap2);
            inner.MouseFilter = MouseFilterEnum.Ignore;
            inner.Position = new Vector2(16, 16);
            inner.Size = new Vector2(255, 268);
            var socket = new Medallion(58, "", on ? "arcane" : null)
            {
                Ring = on ? Style.Ember : canPick ? Style.GoldHi : Style.InkFaint,
                Core = on ? new Color("#4a1c0c") : new Color("#120f14"),
                Ink = Style.EmberHi,
                Lit = canPick,
            };
            var sc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            sc.AddChild(socket);
            inner.AddChild(sc);
            inner.AddChild(Style.Label(f.Name, Style.Display, 21, on ? Style.EmberHi : canPick ? Style.GoldHi : Style.Ink, true, HorizontalAlignment.Center));
            var text = Style.Label(f.Text, Style.Ui, Style.Small, on || canPick ? Style.Ink : Style.InkDim, true, HorizontalAlignment.Center);
            text.SizeFlagsVertical = SizeFlags.ExpandFill;
            inner.AddChild(text);
            inner.AddChild(Style.Label(on ? (Safe ? "SET  ·  CHOOSE AGAIN" : "SET") : canPick ? "CHOOSE" : !known ? "" : slots == 0 ? "OPENS AT RANK II" : "SOCKETS FULL",
                Style.UiHeavy, Style.Caption, on ? Style.EmberHi : canPick ? Style.GoldHi : Style.InkFaint, false, HorizontalAlignment.Center));
            b.AddChild(inner);
            if (canDrop) b.TooltipText = "Choose again (frees the socket)";
            row.AddChild(b);
        }
        v.AddChild(row);
        return v;
    }

''')

# Skills by day, laid in the same two panes.
rep("""    void BuildSkills(VBoxContainer v)
    {
        var ch = G.Journey.Ch;
        var seen = ch.Discovered.Where(id => Weapons.All.TryGetValue(id, out var w) && w.Findable && !SkillBook.Knows(ch, id)).ToList();
        selSkill ??= ch.Slotted.FirstOrDefault() ?? ch.Skills.FirstOrDefault() ?? seen.FirstOrDefault();
        var row = Style.H(26);
        v.AddChild(row);
        var list = Style.V(6);
        list.CustomMinimumSize = new Vector2(430, 0);
        list.AddChild(Style.SubLabel($"Learned  ·  carrying {SkillBook.Carried(ch).Count()} of {SkillBook.Slots(ch)}"));""",
"""    void BuildSkills(Control page)
    {
        var ch = G.Journey.Ch;
        var seen = ch.Discovered.Where(id => Weapons.All.TryGetValue(id, out var w) && w.Findable && !SkillBook.Knows(ch, id)).ToList();
        selSkill ??= ch.Slotted.FirstOrDefault() ?? ch.Skills.FirstOrDefault() ?? seen.FirstOrDefault();
        var left = Pane(page, new Rect2(0, 56, 560, 864));
        var list = Style.V(6);
        list.AddChild(new Section("Learned", $"carrying {SkillBook.Carried(ch).Count()} of {SkillBook.Slots(ch)}"));""")
rep("""            list.AddChild(Style.Gap(6));
            list.AddChild(Style.SubLabel("Seen in the arenas  ·  not yet learned"));""", """            list.AddChild(Style.Gap(6));
            list.AddChild(new Section("Seen in the arenas", "not yet learned"));""")
rep("""        var scroll = Style.Scroll(list);
        scroll.CustomMinimumSize = new Vector2(450, 600);
        row.AddChild(scroll);
        if (selSkill != null && Weapons.All.TryGetValue(selSkill, out var def)) row.AddChild(SkillDetail(ch, def));""",
"""        var scroll = Style.Scroll(list);
        scroll.SizeFlagsVertical = SizeFlags.ExpandFill;
        left.AddChild(scroll);
        var right = Pane(page, new Rect2(590, 56, 1250, 864), null, Style.Gap4);
        if (selSkill != null && Weapons.All.TryGetValue(selSkill, out var def)) right.AddChild(SkillDetail(ch, def));""")
rep("""        b.CustomMinimumSize = new Vector2(420, 64);
        if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("row_on", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4)));
        var col = ItemViews.SchoolColors[w.School];""", """        b.CustomMinimumSize = new Vector2(500, 64);
        if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("row_on", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4)));
        var col = ItemViews.SchoolColors[w.School];""")
rep("""        var head = Style.H(16, Glyphs.Icon(w.Art, 64, col));
        head.AddChild(Style.V(2, Style.Label(w.Name, Style.Display, 32, Style.GoldHi),""", """        var head = Style.H(Style.Gap4, new Medallion(160, "", w.Art) { Ink = col, Ring = carried ? Style.Ember : Style.Gold, Lit = carried });
        head.AddChild(Style.V(2, Style.Label(w.Name.ToUpperInvariant(), Style.Display, 40, Style.GoldHi),""")
rep("""        d.AddChild(Style.Label(w.Description, Style.Text, 17, Style.Ink, true));
        string attr = SkillBook.Attribute(w.Id);""", """        d.AddChild(Style.Label(w.Description, Style.Text, Style.Lead, Style.Ink, true));
        string attr = SkillBook.Attribute(w.Id);""")
open(p, 'w', encoding='utf-8', newline='').write(s)

# The medallion learns to glow: the art in hand, a socket waiting.
o = open(R + r'\Ornate.cs', encoding='utf-8').read()
old = """    public Color ArcColor = Style.Ember;
    readonly int size;"""
new = """    public Color ArcColor = Style.Ember;
    /// <summary>Lit: an ember glow behind it (the art in hand, a socket waiting to be set).</summary>
    public bool Lit;
    readonly int size;"""
assert old in o
o = o.replace(old, new, 1)
old = """        var c = new Vector2(size / 2f, size / 2f);
        float r = size / 2f - 3;
        DrawCircle(c + new Vector2(0, 3), r + 2, new Color(0, 0, 0, 0.5f));"""
new = """        var c = new Vector2(size / 2f, size / 2f);
        float r = size / 2f - 3;
        if (Lit)
            for (int i = 6; i >= 1; i--) DrawCircle(c, r + i * size * 0.035f, new Color(1, 0.45f, 0.15f, 0.05f));
        DrawCircle(c + new Vector2(0, 3), r + 2, new Color(0, 0, 0, 0.5f));"""
assert old in o
o = o.replace(old, new, 1)
open(R + r'\Ornate.cs', 'w', encoding='utf-8', newline='').write(o)
print('done')
