"""Copy the generated (git-ignored) .import files under public/assets from the
predecessor's worktree where ours lacks them; their imported data is already in
our copied .godot."""
import os
import shutil

P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a9586a5171413db0b\public\assets"
M = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294\public\assets"
copied = missing_src = 0
kinds = {}
for root, _, files in os.walk(P):
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
print("copied", copied, kinds, "skipped (no source here)", missing_src)
