import re
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Pack.cs'
s = open(p, encoding='utf-8').read()
a = s.index('<<<<<<< HEAD\n')
m = s.index('=======\n', a)
b = s.index('>>>>>>> origin/claude/vigilant-galileo-l6jqyx\n', m)
s = s[:a] + s[a + len('<<<<<<< HEAD\n'):m] + s[b + len('>>>>>>> origin/claude/vigilant-galileo-l6jqyx\n'):]
# Their rule: a quest item can be left once the story no longer needs it.
pairs = [
("""        if (Items.Get(it.Def).Kind == ItemKind.Quest || !InPack(it)) { Sound.Sfx.Deny(); return; }""",
"""        if (G.Journey.StillNeeded(it) || !InPack(it)) { Sound.Sfx.Deny(); return; }"""),
("""            if (loc.InPack && def.Kind != ItemKind.Quest)
                acts.AddChild(Style.Button(leaving == it.Uid ? "Leave it behind for good" : "Leave behind", () => Leave(it), false, true));""",
"""            if (loc.InPack && !G.Journey.StillNeeded(it))
                acts.AddChild(Style.Button(leaving == it.Uid ? "Leave it behind for good" : "Leave behind", () => Leave(it), false, true));"""),
]
for old, new in pairs:
    assert old in s, old[:70]
    s = s.replace(old, new, 1)
assert '<<<<<<<' not in s and '>>>>>>>' not in s
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
