p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Panels.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""        strip.AddChild(Style.Label("YOUR BUILD", Style.UiHeavy, Style.Caption, Style.Gold));
        strip.AddChild(Style.Gap(0) is var g ? g : null!);
""", """        strip.AddChild(Style.Label("YOUR BUILD", Style.UiHeavy, Style.Caption, Style.Gold));
"""),
("""        if (fits) v2.AddChild(Style.H(4, Glyphs.Icon("flame", 15, Style.EmberHi), Style.Label("Fits your build", Style.UiBold, Style.Caption, Style.EmberHi)) is var fl ? Centre(fl) : null!);""",
"""        if (fits)
        {
            var fl = Style.H(4, Glyphs.Icon("flame", 15, Style.EmberHi), Style.Label("Fits your build", Style.UiBold, Style.Caption, Style.EmberHi));
            fl.Alignment = BoxContainer.AlignmentMode.Center;
            v2.AddChild(fl);
        }"""),
("""    static Control Centre(HBoxContainer h) { h.Alignment = BoxContainer.AlignmentMode.Center; return h; }

""", ""),
("""        if (!Full) { Finish(); return true; }
        if (n >= 0) { if (n < d.Choices.Count && d.Choices[n].Enabled) d.Choose(d.Choices[n].Index); else Sound.Sfx.Deny(); return true; }
        if (d.CanContinue) d.Advance();
        else if (focus >= 0 && focus < lines.Count && lines[focus].Enabled) d.Choose(lines[focus].Index);
        return true;""",
"""        if (!Full) { Finish(); return true; }
        if (n >= 0) { if (n < d.Choices.Count && d.Choices[n].Enabled) d.Choose(d.Choices[n].Index); else Sound.Sfx.Deny(); return true; }
        if (d.CanContinue) d.Advance();
        // Enter or A says the lit line; the use key (pressed to start talking) only when there is one thing to say.
        else if (a == Act.Confirm && focus >= 0 && focus < lines.Count && lines[focus].Enabled) d.Choose(lines[focus].Index);
        else if (d.Choices.Count(c => c.Enabled) == 1) d.Choose(d.Choices.First(c => c.Enabled).Index);
        return true;"""),
]
for old, new in pairs:
    assert old in s, old[:60]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
