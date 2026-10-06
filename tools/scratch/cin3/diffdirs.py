"""List files present in the predecessor's worktree but missing from mine (skipping caches already copied)."""
import os
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695"
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63"
SKIP = {os.path.normcase(os.path.join(P, x)) for x in ["godot\\.godot", "godot\\.shots", "godot\\assets", "node_modules", ".git"]}
missing = []
for root, dirs, files in os.walk(P):
    dirs[:] = [d for d in dirs if os.path.normcase(os.path.join(root, d)) not in SKIP]
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), P)
        if rel == ".git":
            continue
        if not os.path.exists(os.path.join(W, rel)):
            missing.append((rel, os.path.getsize(os.path.join(root, f))))
for rel, size in missing[:200]:
    print(f"{size:>12}  {rel}")
print(len(missing), "missing,", sum(s for _, s in missing) // 1024, "KB")
