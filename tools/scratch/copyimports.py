"""Copy Godot .import/.uid sidecars from the main checkout where my worktree lacks them."""
import os, shutil
MAIN = r"C:\Users\munch\Desktop\survivorsunchained"
M = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab82cbe99e2937ddd"
n = 0
for sub in ("godot", "public"):
    base = os.path.join(MAIN, sub)
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in (".godot", "assets", "node_modules", "bin", "obj") or root.endswith("public")]
        for f in files:
            if not (f.endswith(".import") or f.endswith(".uid")):
                continue
            rel = os.path.relpath(os.path.join(root, f), MAIN)
            dst = os.path.join(M, rel)
            src_asset = dst[: dst.rfind(".")]
            if not os.path.exists(dst) and os.path.exists(src_asset):
                shutil.copy2(os.path.join(root, f), dst)
                n += 1
print("copied", n)
