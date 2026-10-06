"""Copy the generated (git-ignored) .import files from the predecessor's worktree
where ours lacks them; their imported data is already in our copied .godot."""
import os
import shutil

P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
M = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
for sub in (r"public\assets",):
    copied = missing_src = 0
    for root, _, files in os.walk(os.path.join(P, sub)):
        for f in files:
            if not (f.endswith(".import") or f.endswith(".uid")):
                continue
            rel = os.path.relpath(os.path.join(root, f), P)
            dst = os.path.join(M, rel)
            if os.path.exists(dst):
                continue
            base = dst[:-len(".import")] if f.endswith(".import") else dst[:-len(".uid")]
            if not os.path.exists(base):
                missing_src += 1
                continue
            shutil.copy2(os.path.join(root, f), dst)
            copied += 1
    print(sub, "copied", copied, "skipped (no source here)", missing_src)
