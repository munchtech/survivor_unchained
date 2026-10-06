p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot\src\Game\Game.cs'
s = open(p, encoding='utf-8').read()
a = s.index('<<<<<<< HEAD\n')
m = s.index('=======\n', a)
e = s.index('>>>>>>> origin/claude/vigilant-galileo-l6jqyx\n', m)
ours = s[a + len('<<<<<<< HEAD\n'):m]
theirs = s[m + len('=======\n'):e]
ours = ours.replace('        // --cast T: the art in hand used once, T seconds in (a picture of it).\n', '')
s = s[:a] + ours + theirs + s[e + len('>>>>>>> origin/claude/vigilant-galileo-l6jqyx\n'):]
assert '<<<<<<<' not in s and '>>>>>>>' not in s
open(p, 'w', encoding='utf-8').write(s)
print("ok")
