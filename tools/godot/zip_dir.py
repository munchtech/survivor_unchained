"""Zip a folder under one top folder name: python zip_dir.py <dir> <out.zip> <top> (the demo's zip, tools/godot/export.sh)."""
import os, sys, zipfile

src, out, top = sys.argv[1], sys.argv[2], sys.argv[3]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, _, files in os.walk(src):
        for f in files:
            p = os.path.join(root, f)
            z.write(p, os.path.join(top, os.path.relpath(p, src)))
