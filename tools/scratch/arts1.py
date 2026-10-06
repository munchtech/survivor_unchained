p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\ArtsScreen.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""    bool Safe => G.Battle is not { Combat: true };
""",
"""    bool Safe => G.Battle is not { Combat: true };

    /// <summary>Its two pages turn with LT and RT (, and .).</summary>
    public override bool Key(Act a)
    {
        if (a is not (Act.SubNext or Act.SubPrev)) return false;
        skills = !skills;
        Sound.Sfx.Hover();
        Refresh();
        return true;
    }
"""),
("""        var tabs = Style.H(8, Style.Segment("The art in hand", !skills, () => { skills = false; Refresh(); }), Style.Segment("Skills by day", skills, () => { skills = true; Refresh(); }));
        v.AddChild(tabs);
        if (skills) { BuildSkills(v); return; }""",
"""        bool pad = Controls.Instance.UsingPad;
        var tabs = Style.H(8, pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev)),
            Nav.Skip(Style.Segment("The art in hand", !skills, () => { skills = false; Refresh(); })), Nav.Skip(Style.Segment("Skills by day", skills, () => { skills = true; Refresh(); })),
            pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext)));
        v.AddChild(tabs);
        if (skills) { BuildSkills(v); Foot(v); return; }"""),
("""        if (sel != null && Abilities.Find(sel) is { } def) row.AddChild(Detail(ch, def, known.Contains(def.Id)));
    }""",
"""        if (sel != null && Abilities.Find(sel) is { } def) row.AddChild(Detail(ch, def, known.Contains(def.Id)));
        Foot(v);
    }

    void Foot(VBoxContainer v)
    {
        if (!Controls.Instance.UsingPad) return;
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        v.AddChild(Footer((Act.Confirm, "Choose"), (Act.SubNext, skills ? "The art in hand" : "Skills by day"), (Act.TabNext, "Next page"), (Act.Cancel, "Close")));
    }"""),
("""        var b = Style.Button("", () => { sel = a.Id; Refresh(); });
        b.CustomMinimumSize = new Vector2(420, 62);""",
"""        var b = Style.Button("", () => { sel = a.Id; Refresh(); });
        Nav.Id(b, $"art:{a.Id}");
        b.CustomMinimumSize = new Vector2(420, 64);"""),
("""            Style.Label(tag, Style.Ui, 13, known ? role.Color : Style.InkDim with { A = 0.6f }));""",
"""            Style.Label(tag, Style.Ui, Style.Caption, known ? role.Color : Style.InkDim with { A = 0.6f }));"""),
("""            Style.Label($"{role.Name}{(a.Movement ? "  ·  a way of moving" : $"  ·  a {Callings.Archetype(a.Calling!).Name}'s art")}  ·  {a.Cooldown:0} s{(a.Interrupts ? "  ·  breaks channels" : "")}", Style.UiBold, 14, role.Color));""",
"""            Style.Label($"{role.Name}{(a.Movement ? "  ·  a way of moving" : $"  ·  a {Callings.Archetype(a.Calling!).Name}'s art")}  ·  {a.Cooldown:0} s{(a.Interrupts ? "  ·  breaks channels" : "")}", Style.UiBold, Style.Caption, role.Color));"""),
("""            d.AddChild(Style.Label($"Not yet learned. A manual teaches it: the thing that rules an arena carries one, and they turn up in the packs of the dead.", Style.TextItalic, 15, Style.InkDim, true));""",
"""            d.AddChild(Style.Label($"Not yet learned. A manual teaches it: the thing that rules an arena carries one, and they turn up in the packs of the dead.", Style.TextItalic, Style.Small, Style.InkDim, true));"""),
("""        d.AddChild(Style.H(10, Style.Label($"Rank {Numerals[rank - 1]}", Style.UiBold, 16, Style.GoldHi), Style.Label(next, Style.Ui, 14, Style.InkDim)));
        d.AddChild(bar);
        d.AddChild(Style.Label($"+{(Abilities.RankPower(rank) - 1) * 100:0}% strength, {(1 - Abilities.RankHaste(rank)) * 100:0}% shorter wait.  It grows with every use, and with what dies while it is fresh.", Style.Ui, 13, Style.InkDim, true));""",
"""        d.AddChild(Style.H(10, Style.Label($"Rank {Numerals[rank - 1]}", Style.UiBold, Style.Body, Style.GoldHi), Style.Label(next, Style.Ui, Style.Caption, Style.InkDim)));
        d.AddChild(bar);
        d.AddChild(Style.Label($"+{(Abilities.RankPower(rank) - 1) * 100:0}% strength, {(1 - Abilities.RankHaste(rank)) * 100:0}% shorter wait.  It grows with every use, and with what dies while it is fresh.", Style.Ui, Style.Caption, Style.InkDim, true));"""),
("""        else d.AddChild(Style.Label("Take it in hand somewhere safe: the Waystation, a quiet road.", Style.TextItalic, 14, Style.InkDim, true));""",
"""        else d.AddChild(Style.Label("Take it in hand somewhere safe: the Waystation, a quiet road.", Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
("""        v.AddChild(Style.H(8, Style.SubLabel("Facets"), Style.Label(known ? $"{chosen.Count} of {slots} chosen{(opens != "" ? $"  ·  {opens}" : "")}" : "", Style.Ui, 13, Style.InkDim)));""",
"""        v.AddChild(Style.H(8, Style.SubLabel("Facets"), Style.Label(known ? $"{chosen.Count} of {slots} chosen{(opens != "" ? $"  ·  {opens}" : "")}" : "", Style.Ui, Style.Caption, Style.InkDim)));"""),
("""            b.CustomMinimumSize = new Vector2(390, 84);""",
"""            b.CustomMinimumSize = new Vector2(390, 88);
            Nav.Id(b, $"facet:{f.Id}");"""),
("""                Style.Label(f.Text, Style.Ui, 13, on || canPick ? Style.Ink : Style.InkDim, true));""",
"""                Style.Label(f.Text, Style.Ui, Style.Caption, on || canPick ? Style.Ink : Style.InkDim, true));"""),
("""        if (ch.Skills.Count == 0) list.AddChild(Style.Label("None yet. What burns in the arenas can be learned by day.", Style.TextItalic, 14, Style.InkDim, true));""",
"""        if (ch.Skills.Count == 0) list.AddChild(Style.Label("None yet. What burns in the arenas can be learned by day.", Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
("""        if (unseen > 0) list.AddChild(Style.Label($"{unseen} more the arenas have not shown you yet.", Style.TextItalic, 13, Style.InkDim, true));""",
"""        if (unseen > 0) list.AddChild(Style.Label($"{unseen} more the arenas have not shown you yet.", Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
("""        var b = Style.Button("", () => { selSkill = id; Refresh(); });
        b.CustomMinimumSize = new Vector2(420, 62);""",
"""        var b = Style.Button("", () => { selSkill = id; Refresh(); });
        Nav.Id(b, $"skill:{id}");
        b.CustomMinimumSize = new Vector2(420, 64);"""),
("""            Style.Label(tag, Style.Ui, 13, meets ? Style.Good : Style.Bad));""",
"""            Style.Label(tag, Style.Ui, Style.Caption, meets ? Style.Good : Style.Bad));"""),
("""            Style.Label($"{w.School.ToString().ToLowerInvariant()}  ·  {string.Join(", ", w.Tags.Select(t => t.ToString().ToLowerInvariant()))}", Style.UiBold, 14, col)));""",
"""            Style.Label($"{w.School.ToString().ToLowerInvariant()}  ·  {string.Join(", ", w.Tags.Select(t => t.ToString().ToLowerInvariant()))}", Style.UiBold, Style.Caption, col)));"""),
("""            Style.UiBold, 15, meets ? Style.Good : Style.Bad, true));
        d.AddChild(Style.Label($"By day it is rank {Ranks[SkillBook.Rank(ch)]}, and grows with you (every third level). In the night's arenas the ember starts from nothing, whatever you know.", Style.Ui, 14, Style.InkDim, true));""",
"""            Style.UiBold, Style.Small, meets ? Style.Good : Style.Bad, true));
        d.AddChild(Style.Label($"By day it is rank {Ranks[SkillBook.Rank(ch)]}, and grows with you (every third level). In the night's arenas the ember starts from nothing, whatever you know.", Style.Ui, Style.Caption, Style.InkDim, true));"""),
("""            d.AddChild(Style.Label("You have seen it burn. Learn it from a tome (a story fight won, Vonnra's Curiosities), or your calling may teach it as you grow.", Style.TextItalic, 15, Style.InkDim, true));
        else if (!Safe)
            d.AddChild(Style.Label(carried ? "Carried. Change what you carry somewhere safe." : "Change what you carry somewhere safe: the Waystation, a quiet road.", Style.TextItalic, 14, Style.InkDim, true));""",
"""            d.AddChild(Style.Label("You have seen it burn. Learn it from a tome (a story fight won, Vonnra's Curiosities), or your calling may teach it as you grow.", Style.TextItalic, Style.Small, Style.InkDim, true));
        else if (!Safe)
            d.AddChild(Style.Label(carried ? "Carried. Change what you carry somewhere safe." : "Change what you carry somewhere safe: the Waystation, a quiet road.", Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
("""            d.AddChild(Style.Label("Your hands are full: put one down first. More room comes at the fourth level and the eighth.", Style.TextItalic, 14, Style.InkDim, true));""",
"""            d.AddChild(Style.Label("Your hands are full: put one down first. More room comes at the fourth level and the eighth.", Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
]
for old, new in pairs:
    assert old in s, old[:90]
    s = s.replace(old, new, 1)
s = s.replace("using System.Linq;\nusing Godot;", "using System.Linq;\nusing Godot;", 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
