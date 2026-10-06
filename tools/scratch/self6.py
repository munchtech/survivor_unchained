p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("var who = Pane(page, new Rect2(0, 0, 560, 920));", "var who = Pane(page, new Rect2(0, 0, 536, 920));"),
("var mid = Pane(page, new Rect2(590, 0, 840, 920));", "var mid = Pane(page, new Rect2(560, 0, 840, 920));"),
("var right = Pane(page, new Rect2(1460, 0, 380, 920), null, Style.Gap2);", "var right = Pane(page, new Rect2(1424, 0, 416, 920), null, Style.Gap2);"),
("""                label.CustomMinimumSize = new Vector2(160, 0);""", """                label.CustomMinimumSize = new Vector2(150, 0);"""),
("""Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need} to level {ch.Level + 1}", Style.Day, 400));""", """Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need} to level {ch.Level + 1}", Style.Day, 380));"""),
]
for old, new in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
