"""A picture's surface read by MoGe-2 on the local ComfyUI (MIT): every
pixel a point in 3D, as a mesh whose UVs are the pixels (for
tools/assets/face_warp.py to lay her face on), with its normals and depth
drawn as pictures to judge it by.

    python tools/assets/face_moge.py <picture.png> <out dir> [left|right|whole]

left or right: that half of a reference (face_refs.py paints two views side
by side). Writes <out>/input.png (the picture as read), face_*.glb,
moge_normal_*.png and moge_depth_*.png. ComfyUI must be running; its
models are freed after.

What we learnt of it (2026-10-04, on her reference heroine_11): its normals
are very good (lids and their folds, the lips' volume, the nose, the
cheekbones, all clean); its depths are smoother and flatter than its
normals, a little striped across, and a long lens's portrait it reads
somewhat deeper than it is (face_warp.py scales its depth to hers).
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comfy"))
import comfy  # noqa: E402
from PIL import Image  # noqa: E402


def graph(name):
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": name}},
        "2": {"class_type": "LoadMoGeModel", "inputs": {"model_name": "moge_2_vitl_normal_fp16.safetensors"}},
        "3": {"class_type": "MoGeInference", "inputs": {"moge_model": ["2", 0], "image": ["1", 0], "resolution_level": 9,
                                                        "fov_x_degrees": 0, "batch_size": 1, "force_projection": True,
                                                        "apply_mask": True, "refine_steps": 0}},
        "4": {"class_type": "MoGePointMapToMesh", "inputs": {"moge_geometry": ["3", 0], "batch_index": 0, "decimation": 1,
                                                            "discontinuity_threshold": 0.04, "texture": True}},
        "5": {"class_type": "SaveGLB", "inputs": {"mesh": ["4", 0], "filename_prefix": "moge/face"}},
        "6": {"class_type": "MoGeRender", "inputs": {"moge_geometry": ["3", 0], "output": "normal_opengl"}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "moge_normal"}},
        "8": {"class_type": "MoGeRender", "inputs": {"moge_geometry": ["3", 0], "output": "depth_colored"}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "moge_depth"}},
    }


def free():
    """The shared GPU given back (the server answers with nothing)."""
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req).read()


if __name__ == "__main__":
    src, out = sys.argv[1], os.path.abspath(sys.argv[2])
    part = sys.argv[3] if len(sys.argv) > 3 else "whole"
    os.makedirs(out, exist_ok=True)
    im = Image.open(src).convert("RGB")
    if part != "whole":
        w = im.size[0]
        im = im.crop((0, 0, w // 2, im.size[1])) if part == "left" else im.crop((w // 2, 0, w, im.size[1]))
    p = os.path.join(out, "input.png")
    im.save(p)
    try:
        for f in comfy.run(graph(comfy.upload(p)), out):
            print("MOGE", f)
    finally:
        free()
