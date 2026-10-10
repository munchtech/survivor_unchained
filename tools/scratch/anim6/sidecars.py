"""Copy main's untracked Godot sidecars (.import, .uid) into this worktree
where the base file exists here and the sidecar does not."""
import os, shutil
A = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8d33b2672b7be905"
B = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af8dbda3195e438e4"
n = 0
for top in ("godot", "public"):
    for root, dirs, files in os.walk(os.path.join(A, top)):
        rel_root = os.path.relpath(root, A)
        # the junction godot/assets -> public/assets is walked as public/
        dirs[:] = [d for d in dirs if not (rel_root == "godot" and d in ("assets", ".godot"))]
        for f in files:
            if not f.endswith((".import", ".uid")):
                continue
            rel = os.path.join(rel_root, f)
            dst = os.path.join(B, rel)
            base = dst[:-7] if f.endswith(".import") else dst[:-4]
            if os.path.exists(base) and not os.path.exists(dst):
                shutil.copy2(os.path.join(A, rel), dst)
                n += 1
print("copied", n)
