import os, shutil, subprocess
A = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a565196002a51af40'
B = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa1f430bd64b8d1ce'
out = subprocess.run(['git', '-C', A, 'ls-files', '--others', '--exclude-standard', '--', 'godot', 'public'], capture_output=True, text=True).stdout.split('\n')
n = 0
for rel in out:
    rel = rel.strip()
    if not rel.endswith(('.import', '.uid')):
        continue
    src = os.path.join(A, rel); dst = os.path.join(B, rel)
    base = dst[:-7] if dst.endswith('.import') else dst[:-4]
    if not os.path.exists(base) or os.path.exists(dst):
        continue
    shutil.copy2(src, dst); n += 1
# public/assets .import files (through the junction they are untracked under public/)
for root, _, files in os.walk(os.path.join(A, 'public', 'assets')):
    for f in files:
        if f.endswith('.import'):
            src = os.path.join(root, f); rel = os.path.relpath(src, A); dst = os.path.join(B, rel)
            if os.path.exists(dst[:-7]) and not os.path.exists(dst):
                shutil.copy2(src, dst); n += 1
print('copied', n)
