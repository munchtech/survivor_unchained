"""Copy Godot .import/.uid sidecars from the predecessor's worktree where mine lacks them (and the asset exists)."""
import os, shutil
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a4fdbc49786ba8b7f"
M = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a565196002a51af40"
n = 0
for sub in ("godot", "public"):
    base = os.path.join(P, sub)
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in (".godot", "bin", "obj", "node_modules") and not (sub == "godot" and root == base and d == "assets")]
        for f in files:
            if not (f.endswith(".import") or f.endswith(".uid")):
                continue
            rel = os.path.relpath(os.path.join(root, f), P)
            dst = os.path.join(M, rel)
            if not os.path.exists(dst) and os.path.exists(dst[: dst.rfind(".")]):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(os.path.join(root, f), dst)
                n += 1
print("copied", n)
