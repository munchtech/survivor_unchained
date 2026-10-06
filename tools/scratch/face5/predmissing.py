import os, sys
P = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
M = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
since = os.path.getmtime(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4\refs_front.log')
skip = {'.godot', '.' + 'git', 'node_modules', '.shots', '.import', 'bin', 'obj', '__pycache__'}
out = []
for root, dirs, files in os.walk(P):
    dirs[:] = [d for d in dirs if d not in skip]
    for f in files:
        fp = os.path.join(root, f)
        try: st = os.stat(fp)
        except OSError: continue
        pass
        rel = os.path.relpath(fp, P)
        mp = os.path.join(M, rel)
        same = os.path.exists(mp) and os.path.getsize(mp) == st.st_size and open(mp, 'rb').read() == open(fp, 'rb').read()
        if not os.path.exists(mp): out.append((rel, st.st_size, os.path.exists(mp)))
for r, s, e in sorted(out): print(f'{s:>12} {"M" if e else "N"} {r}')
