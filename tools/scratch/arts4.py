R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
p = R + r'\ArtsScreen.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

rep("""        int unseen = Weapons.Pool.Count(id => !ch.Discovered.Contains(id));
        if (unseen > 0) list.AddChild(Style.Label($"{unseen} more the arenas have not shown you yet.", Style.TextItalic, Style.Caption, Style.InkDim, true));""",
"""        int unseen = Weapons.Pool.Count(id => !ch.Discovered.Contains(id));
        if (unseen > 0)
        {
            // The ones still to see, as blank medallions: the collection shows its gaps.
            list.AddChild(Style.Gap(6));
            list.AddChild(new Section("Not yet shown", $"{unseen} more burn in the arenas"));
            var blanks = new GridContainer { Columns = 6, MouseFilter = MouseFilterEnum.Ignore };
            blanks.AddThemeConstantOverride("h_separation", 12);
            blanks.AddThemeConstantOverride("v_separation", 12);
            for (int i = 0; i < unseen; i++) blanks.AddChild(new Medallion(70, "?") { Ring = Style.InkFaint, Ink = Style.InkFaint, Core = new Color("#120f14") });
            list.AddChild(blanks);
        }""")
rep("""        if (selSkill != null && Weapons.All.TryGetValue(selSkill, out var def)) right.AddChild(SkillDetail(ch, def));""",
"""        if (selSkill != null && Weapons.All.TryGetValue(selSkill, out var def)) right.AddChild(SkillDetail(ch, def));
        else HowSkillsCome(right);""")
rep("""    Control SkillEntry(CharacterData ch, string id, bool known)""", """    /// <summary>With nothing learned yet, the page says how a skill comes to you, as three steps.</summary>
    static void HowSkillsCome(VBoxContainer d)
    {
        d.AddChild(Style.Label("HOW A SKILL COMES TO YOU", Style.Display, 32, Style.GoldHi));
        d.AddChild(Style.Label("The night's arenas burn with skills the ember lends you. By day you can keep them.", Style.Text, Style.Lead, Style.Ink, true));
        var row = Style.H(Style.Gap4);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var (glyph, title, text) in new[]
        {
            ("flame", "Seen", "An arena shows it to you: the ember offers it in a draft, and you use it."),
            ("book", "Learned", "A tome teaches it: a story fight won, Vonnra's Curiosities; your calling may teach one as you grow."),
            ("embers", "Carried", "Carry it by day and it is banked: the ember offers it in the night's first drafts, at a higher rank."),
        })
        {
            var box = OrnateBox.Make(OrnateBox.Kind.Card, 18, Style.Gold);
            box.Crest = 80;
            var card = Style.Panel(box);
            card.CustomMinimumSize = new Vector2(360, 340);
            var v = Style.V(Style.Gap2);
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(new Medallion(120, "", glyph));
            v.AddChild(mc);
            v.AddChild(Style.Label(title.ToUpperInvariant(), Style.Display, 24, Style.GoldHi, false, HorizontalAlignment.Center));
            v.AddChild(Style.Label(text, Style.Ui, Style.Small, Style.Ink, true, HorizontalAlignment.Center));
            card.AddChild(v);
            row.AddChild(card);
        }
        d.AddChild(Style.Gap(Style.Gap3));
        d.AddChild(row);
    }

    Control SkillEntry(CharacterData ch, string id, bool known)""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
