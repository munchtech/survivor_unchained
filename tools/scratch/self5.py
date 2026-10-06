p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""        if (ch.Traits.Count == 0 && ch.TraitPicks == 0)
            mid.AddChild(Style.Label("None yet. Traits come with levels, and with what you do.", Style.TextItalic, Style.Small, Style.InkDim, true));
""",
"""        // The places still to fill, so the page shows where a character is going.
        int cells = traits.GetChildCount();
        int next = ch.Level % 2 == 0 ? ch.Level + 2 : ch.Level + 1;
        do
        {
            var box = OrnateBox.Make(OrnateBox.Kind.Well, 14);
            var inner = Style.V(4, Style.H(6, Glyphs.Icon("lock", 15, Style.InkFaint), Style.Label($"A trait at level {next}", Style.UiBold, Style.Body, Style.InkDim)),
                Style.Label("One of three, chosen when you reach it. Others come for what you do.", Style.TextItalic, Style.Caption, Style.InkFaint, true));
            var p = Style.Panel(box, inner);
            p.CustomMinimumSize = new Vector2(258, 118);
            p.MouseFilter = MouseFilterEnum.Ignore;
            traits.AddChild(p);
            next += 2;
            cells++;
        } while (cells % 3 != 0 || cells < 6);
"""),
("""            var col = Style.V(2, Style.Label(group.ToUpperInvariant(), Style.UiHeavy, Style.Caption, Style.Gold));""",
"""            var col = Style.V(4, Style.Label(group.ToUpperInvariant(), Style.UiHeavy, Style.Caption, Style.Gold));"""),
("""                var label = Style.Label(name, Style.Ui, Style.Small, Style.InkDim);
                label.CustomMinimumSize = new Vector2(150, 0);
                var line = Style.H(10, label, Style.Label(fmt(now), Style.UiBold, Style.Small, Style.Ink));
                if (then != null && Math.Abs(then.Get(key) - now) > 1e-6)
                    line.AddChild(Style.Label(Change(key, now, then.Get(key)), Style.UiBold, Style.Small, Style.Good));""",
"""                var label = Style.Label(name, Style.Ui, Style.Body, Style.InkDim);
                label.CustomMinimumSize = new Vector2(160, 0);
                var line = Style.H(10, label, Style.Label(fmt(now), Style.UiBold, Style.Body, Style.Ink));
                if (then != null && Math.Abs(then.Get(key) - now) > 1e-6)
                    line.AddChild(Style.Label(Change(key, now, then.Get(key)), Style.UiBold, Style.Body, Style.Good));"""),
("""            pillar.CustomMinimumSize = new Vector2(188, 320);""",
"""            pillar.CustomMinimumSize = new Vector2(188, 340);"""),
("""            med.AddChild(new Medallion(108, $"{Attr(ch, id)}"));""",
"""            med.AddChild(new Medallion(120, $"{Attr(ch, id)}"));"""),
]
for old, new in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
