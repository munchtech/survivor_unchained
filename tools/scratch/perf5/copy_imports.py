"""Copy generated (git-ignored) .import/.uid files from the predecessor's imported worktree
into ours where ours lacks them and the source asset exists here."""
import os, shutil
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
M = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad57a6dd0798688d7"
for sub in (r"public\assets", r"godot"):
    copied = missing = 0
    for root, dirs, files in os.walk(os.path.join(P, sub)):
        dirs[:] = [d for d in dirs if d not in (".godot", "assets", "bin", "obj", ".shots")]
        for f in files:
            if not (f.endswith(".import") or f.endswith(".uid")):
                continue
            rel = os.path.relpath(os.path.join(root, f), P)
            dst = os.path.join(M, rel)
            if os.path.exists(dst):
                continue
            base = dst.rsplit(".", 1)[0]
            if not os.path.exists(base):
                missing += 1
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, f), dst)
            copied += 1
    print(sub, "copied", copied, "skipped", missing)
