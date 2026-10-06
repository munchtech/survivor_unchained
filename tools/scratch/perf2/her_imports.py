"""Her textures: lossless, with mipmaps, never turned into VRAM-compressed by the 3D detection;
heroine.glb: its embedded images given mipmaps by tools_scenes/import_mipmaps.gd.
    python her_imports.py [--dry]"""
import glob
import os
import re
import sys

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294\godot"
dry = "--dry" in sys.argv
changed = []
for pat in ["art/people/outfit_tex/*.import", "art/people/head_tex/*.import", "art/people/paint/*.import", "art/people/skin_pores.png.import"]:
    for f in glob.glob(os.path.join(ROOT, pat)):
        s = open(f, encoding="utf-8", newline="").read()
        if 'importer="texture"' not in s:
            continue
        t = s
        t = re.sub(r"(?m)^compress/mode=\d+", "compress/mode=0", t)
        t = re.sub(r"(?m)^mipmaps/generate=\w+", "mipmaps/generate=true", t)
        t = re.sub(r"(?m)^detect_3d/compress_to=\d+", "detect_3d/compress_to=0", t)
        if t != s:
            changed.append(os.path.relpath(f, ROOT))
            if not dry:
                open(f, "w", encoding="utf-8", newline="").write(t)
glb = os.path.join(ROOT, "art/people/heroine.glb.import")
s = open(glb, encoding="utf-8", newline="").read()
t = s.replace('import_script/path=""', 'import_script/path="res://tools_scenes/import_mipmaps.gd"')
if t != s:
    changed.append("art/people/heroine.glb.import")
    if not dry:
        open(glb, "w", encoding="utf-8", newline="").write(t)
print(len(changed), "files")
for c in changed:
    print(" ", c)
