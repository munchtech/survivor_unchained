"""Copy main's .import/.uid sidecars that my worktree lacks (their resource present here)."""
import os, shutil
MAIN = r'C:\Users\munch\Desktop\survivorsunchained\godot'
MINE = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791\godot'
n = 0
for root, dirs, files in os.walk(MAIN):
    dirs[:] = [d for d in dirs if d not in ('.godot', 'assets', '.shots', 'bin', 'obj')]
    for f in files:
        if not (f.endswith('.import') or f.endswith('.uid')):
            continue
        src = os.path.join(root, f)
        rel = os.path.relpath(src, MAIN)
        dst = os.path.join(MINE, rel)
        res = dst[:-7] if f.endswith('.import') else dst[:-4]
        if not os.path.exists(dst) and os.path.exists(res):
            shutil.copy2(src, dst); n += 1
print('copied', n)
