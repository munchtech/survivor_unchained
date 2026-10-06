import re
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge\fitall.py'
s = open(p, encoding='utf-8').read()


def drop(name):
    global s
    i = s.index(f'def {name}(')
    m = re.search(r'\n(def |# -----|GROUPS)', s[i + 5:])
    j = i + 5 + m.start() + 1
    s = s[:i] + s[j:]


for n in ("f_hint", "f_tooltip", "f_toast", "f_prompt", "f_chip", "f_wslot", "f_buttons", "f_tabs"):
    drop(n)
i = s.index('def f_paper():')
j = s.index('def f_mapframe():')
s = s[:i] + '''def f_paper():
    """Paper and the hint note: made in paper.py (laid paper, foxing, a hand-torn deckle,
    iron caps, a nail and wax), painted over, calmed, tiled."""
    import paper
    paper.build(UI)


''' + s[j:]
s = s.replace('''"""Every painted pick fitted into godot/art/ui/''', '''"""Every painted pick fitted into godot/art/ui/ (the metal chrome is chrome.py; paper is
paper.py, called from here)''', 1) if '"""Every painted pick fitted into godot/art/ui/' in s else s
open(p, 'w', encoding='utf-8').write(s)
print([l for l in s.splitlines() if l.startswith('def f_')])
