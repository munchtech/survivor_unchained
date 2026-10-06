import os, shutil
S = os.path.dirname(__file__)
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ae2de192cce8298ca"
M = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
n = 0
for line in open(os.path.join(S, "untracked_p.txt"), encoding="utf8"):
    size, rel = line.rstrip("\n").split("\t")
    if rel.startswith("godot/tests/") or rel == ".git" or rel.startswith(".git"):
        continue
    dst = os.path.join(M, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(P, rel), dst)
        n += 1
        print("copied", rel)
print(n)
