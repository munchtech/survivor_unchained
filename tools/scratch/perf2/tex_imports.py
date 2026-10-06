"""Import settings of the textures under the given folders: mode, mipmaps, size, and who loads them."""
import glob
import os
import sys

from PIL import Image

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294\godot"
rows = []
for pat in sys.argv[1:]:
    for imp in glob.glob(os.path.join(ROOT, pat)):
        if not imp.endswith(".import"):
            continue
        src = imp[:-7]
        kv = {}
        for line in open(imp, encoding="utf-8"):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                kv[k] = v
        if kv.get("importer") != '"texture"':
            continue
        try:
            w, h = Image.open(src).size
        except Exception:
            w = h = 0
        rows.append((kv.get("compress/mode"), kv.get("mipmaps/generate"), kv.get("compress/normal_map"), f"{w}x{h}", os.path.relpath(src, ROOT)))
for r in sorted(rows):
    print("mode=%s mip=%s nm=%s %-10s %s" % r)
modes = {}
for r in rows:
    modes[(r[0], r[1])] = modes.get((r[0], r[1]), 0) + 1
print(modes)
