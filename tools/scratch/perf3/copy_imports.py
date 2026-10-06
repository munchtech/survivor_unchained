"""Copy the generated (git-ignored) .import files from the predecessor's worktree
where ours lacks them; their imported data is already in our copied .godot."""
import os
import shutil
import sys

P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294"
M = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
for sub in (r"public\assets", r"godot\art"):
    copied = missing_src = 0
    kinds = {}
    for root, _, files in os.walk(os.path.join(P, sub)):
        for f in files:
            if not f.endswith(".import"):
                continue
            rel = os.path.relpath(os.path.join(root, f), P)
            dst = os.path.join(M, rel)
            if os.path.exists(dst):
                continue
            if not os.path.exists(dst[:-len(".import")]):
                missing_src += 1
                continue
            shutil.copy2(os.path.join(root, f), dst)
            copied += 1
            ext = f[:-7].rsplit(".", 1)[-1]
            kinds[ext] = kinds.get(ext, 0) + 1
    print(sub, "copied", copied, kinds, "skipped (no source here)", missing_src)
