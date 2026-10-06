"""Copy .import files (and their imported data) for art that has none in this worktree, from the main
checkout or a sibling worktree that has imported it."""
import os, shutil

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\godot"
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees"
SRCS = [r"C:\Users\munch\Desktop\survivorsunchained\godot"] + [os.path.join(W, a, "godot") for a in
        ["agent-a4fdbc49786ba8b7f", "agent-a0bff3ffe4d3ad748", "agent-af01b0d61ef656dd4"]]
EXT = (".png", ".jpg", ".glb", ".ogg", ".wav", ".ttf", ".otf", ".webp", ".mp3", ".exr", ".hdr")
copied, data, missing = 0, 0, []
for root, _, files in os.walk(os.path.join(WT, "art")):
    for f in files:
        if not f.lower().endswith(EXT):
            continue
        p = os.path.join(root, f)
        if os.path.exists(p + ".import"):
            continue
        rel = os.path.relpath(p, WT)
        for s in SRCS:
            q = os.path.join(s, rel) + ".import"
            if not os.path.exists(q):
                continue
            shutil.copy2(q, p + ".import"); copied += 1
            # the imported data it points at (res://.godot/imported/...)
            for line in open(q, encoding="utf-8", errors="replace"):
                if line.startswith(("path=", "path.s3tc=", "path.etc2=", "path.bptc=", "path.astc=")) and "res://.godot/" in line:
                    r = line.split('"')[1].replace("res://", "")
                    src, dst = os.path.join(s, r), os.path.join(WT, r)
                    if os.path.exists(src) and not os.path.exists(dst):
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst); data += 1
                        if os.path.exists(src + ".md5"): shutil.copy2(src + ".md5", dst + ".md5")
            break
        else:
            missing.append(rel)
print("copied", copied, "imported data", data, "missing", len(missing))
for m in missing[:20]:
    print(" ", m)
