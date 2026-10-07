"""Fetch a few Godot 4.5.1-stable source files (text, read-only reference) and log their checksums."""
import hashlib
import os
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "godot_src")
BASE = "https://raw.githubusercontent.com/godotengine/godot/4.5.1-stable/"
FILES = [
    "servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered.glsl",
    "servers/rendering/renderer_rd/shaders/forward_clustered/scene_forward_clustered_inc.glsl",
    "servers/rendering/renderer_rd/renderer_compositor_rd.cpp",
    "servers/rendering/renderer_rd/storage_rd/render_scene_data_rd.cpp",
    "servers/rendering/renderer_rd/shaders/effects/taa_resolve.glsl",
    "servers/rendering/renderer_rd/renderer_scene_render_rd.cpp",
    "servers/rendering/renderer_rd/forward_clustered/render_forward_clustered.cpp",
    "servers/rendering/renderer_rd/effects/fsr2.cpp",
    "servers/rendering/renderer_viewport.cpp",
    "main/main.cpp",
    "servers/rendering/rendering_server_default.cpp",
    "servers/rendering/renderer_rd/effects/taa.cpp",
    "servers/rendering/renderer_rd/shaders/scene_forward_aa_inc.glsl",
]
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "CHECKSUMS.txt"), "w", encoding="utf-8") as log:
    for f in FILES:
        data = urllib.request.urlopen(BASE + f, timeout=60).read()
        name = os.path.basename(f)
        with open(os.path.join(OUT, name), "wb") as o:
            o.write(data)
        line = f"{BASE + f}  {len(data)} bytes  sha256 {hashlib.sha256(data).hexdigest()}"
        log.write(line + "\n")
        print(name, len(data), hashlib.sha256(data).hexdigest()[:16])
