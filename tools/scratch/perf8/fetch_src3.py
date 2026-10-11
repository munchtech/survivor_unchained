"""Fetch more Godot 4.5.1-stable source files (text, read-only reference) and log their checksums.
    python fetch_src3.py OUTDIR"""
import hashlib
import os
import sys
import urllib.request

OUT = sys.argv[1]
BASE = "https://raw.githubusercontent.com/godotengine/godot/4.5.1-stable/"
FILES = [
    "servers/rendering/renderer_rd/storage_rd/material_storage.cpp",
    "servers/rendering/renderer_rd/effects/fsr2.cpp",
    "servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered.glsl",
]
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "CHECKSUMS3.txt"), "a", encoding="utf-8") as log:
    for f in FILES:
        try:
            data = urllib.request.urlopen(BASE + f, timeout=60).read()
        except Exception as e:
            print("MISSING", f, e)
            continue
        name = os.path.basename(f)
        with open(os.path.join(OUT, name), "wb") as o:
            o.write(data)
        line = f"{BASE + f}  {len(data)} bytes  sha256 {hashlib.sha256(data).hexdigest()}"
        log.write(line + "\n")
        print(name, len(data), hashlib.sha256(data).hexdigest()[:16])
