"""Every .import in this worktree whose imported data is missing from .godot/imported: copied from the
main checkout or a sibling worktree that has it (same source hash in the name, so the same file)."""
import os, shutil, glob

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\godot"
SRCS = [r"C:\Users\munch\Desktop\survivorsunchained\godot"] + glob.glob(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\*\godot")
SRCS = [s for s in SRCS if os.path.normcase(s) != os.path.normcase(WT)]
copied, missing = 0, []
for root, _, files in os.walk(WT):
    if ".godot" in root or ".shots" in root:
        continue
    for f in files:
        if not f.endswith(".import"):
            continue
        for line in open(os.path.join(root, f), encoding="utf-8", errors="replace"):
            if not (line.startswith("path") and "res://.godot/imported/" in line):
                continue
            r = line.split('"')[1].replace("res://", "")
            dst = os.path.join(WT, r)
            if os.path.exists(dst):
                continue
            for s in SRCS:
                src = os.path.join(s, r)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    if os.path.exists(src[:src.rfind(".")] + ".md5"):
                        shutil.copy2(src[:src.rfind(".")] + ".md5", dst[:dst.rfind(".")] + ".md5")
                    copied += 1
                    break
            else:
                missing.append(r)
print("copied", copied, "missing", len(missing))
for m in missing[:15]:
    print(" ", m)
