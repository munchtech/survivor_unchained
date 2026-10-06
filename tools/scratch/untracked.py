import os, sys, collections
S = os.path.dirname(__file__)
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ae2de192cce8298ca"
tracked = set(l.strip() for l in open(os.path.join(S, "tracked.txt"), encoding="utf8"))
skip_dirs = {os.path.join(P, "public"), os.path.join(P, "godot", "assets"), os.path.join(P, "godot", ".godot")}
out = []
for root, dirs, files in os.walk(P):
    dirs[:] = [d for d in dirs if os.path.join(root, d) not in skip_dirs and d not in ("node_modules", ".git", "__pycache__")]
    for f in files:
        if f.endswith(".import") or f.endswith(".uid"):
            continue
        rel = os.path.relpath(os.path.join(root, f), P).replace("\\", "/")
        if rel not in tracked:
            out.append((rel, os.path.getsize(os.path.join(root, f))))
open(os.path.join(S, "untracked_p.txt"), "w", encoding="utf8").write("\n".join(f"{s}\t{r}" for r, s in out))
c = collections.Counter()
sz = collections.Counter()
for r, s in out:
    d = r.rsplit("/", 1)[0] if "/" in r else "."
    c[d] += 1; sz[d] += s
for d, n in c.most_common(60):
    print(n, round(sz[d] / 1e6, 1), "MB", d)
print(len(out))
