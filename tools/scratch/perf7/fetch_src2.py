"""Fetch more Godot 4.5.1-stable source files (text, read-only reference) and log their checksums."""
import hashlib
import os
import sys
import urllib.request

OUT = sys.argv[1]
BASE = "https://raw.githubusercontent.com/godotengine/godot/4.5.1-stable/"
FILES = [
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_reconstruct_dilated_velocity_and_previous_depth.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_accumulate.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_common.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_callbacks_glsl.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_reproject.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_upsample.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_postprocess_lock_status.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_lock.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_depth_clip.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_sample.h",
    "thirdparty/amd-fsr2/shaders/ffx_fsr2_rcas.h",
    "servers/rendering/renderer_rd/forward_clustered/scene_shader_forward_clustered.cpp",
    "servers/rendering/renderer_rd/storage_rd/render_scene_buffers_rd.h",
    "servers/rendering/renderer_rd/storage_rd/render_scene_buffers_rd.cpp",
]
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "CHECKSUMS2.txt"), "w", encoding="utf-8") as log:
    for f in FILES:
        try:
            data = urllib.request.urlopen(BASE + f, timeout=60).read()
        except Exception as e:  # (a file moved between versions: note it, go on)
            print("MISSING", f, e)
            continue
        name = os.path.basename(f)
        with open(os.path.join(OUT, name), "wb") as o:
            o.write(data)
        line = f"{BASE + f}  {len(data)} bytes  sha256 {hashlib.sha256(data).hexdigest()}"
        log.write(line + "\n")
        print(name, len(data), hashlib.sha256(data).hexdigest()[:16])
