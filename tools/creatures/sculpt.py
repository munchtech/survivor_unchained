"""A creature's picture turned into a sculpt by TRELLIS 2, locally.

    python tools/creatures/sculpt.py PICTURE.png --out DIR [--seeds 42,7] [--tex 4096]

Runs tools/comfy/graphs/trellis_img.json with its switch set to TRELLIS 2
(MIT; never Hunyuan3D, legal brief 5(g)). Each seed writes the textured
mesh (about 700k triangles with TRELLIS's own 4K paint) and the bare shape,
and a record beside them: the picture's hash, the seed, the model, the date.
The team's retopology, rig, paint and clips come after (tools/creatures/boar_build.py).

Take the GPU turn first; the script frees ComfyUI's models when it ends.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "comfy"))
import comfy  # noqa: E402

GRAPH = os.path.join(HERE, "..", "comfy", "graphs", "trellis_img.json")


def free():
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req).read()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("picture")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--tex", type=int, default=4096)
    ap.add_argument("--faces", type=int, default=700000)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    name = comfy.upload(a.picture)
    stem = os.path.splitext(os.path.basename(a.picture))[0]
    try:
        for seed in (int(s) for s in a.seeds.split(",")):
            api = json.load(open(GRAPH, encoding="utf-8"))
            api["122"]["inputs"]["image"] = name
            api["316"]["inputs"]["value"] = True        # TRELLIS 2, not Pixal3D
            api["288"]["inputs"]["value"] = a.tex
            api["186"]["inputs"]["target_face_count"] = a.faces
            for node in ("3", "18", "23", "12"):          # structure, shape, upsample, texture
                api[node]["inputs"]["seed"] = seed
            api["900"]["inputs"]["filename_prefix"] = f"creatures/{stem}_s{seed}_textured"
            api["901"]["inputs"]["filename_prefix"] = f"creatures/{stem}_s{seed}_shape"
            # Only the two meshes are wanted: drop the previews and loose files
            # that nothing reads (some previews pass their images on, and stay).
            used = {v[0] for n in api.values() for v in n["inputs"].values() if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str)}
            for k in [k for k, v in api.items() if v["class_type"] in ("PreviewImage", "MaskPreview", "MeshToFile3D") and k not in used]:
                del api[k]
            sub = os.path.join(a.out, f"s{seed}")
            saved = comfy.run(api, sub)
            record = {
                "picture": os.path.basename(a.picture), "picture_sha256": sha256(a.picture), "seed": seed,
                "model": "TRELLIS 2 (microsoft/TRELLIS.2-4B, MIT) int8, with DINOv3 ViT-L, BiRefNet; ComfyUI's own nodes",
                "graph": "tools/comfy/graphs/trellis_img.json (switch: TRELLIS 2)", "texture": a.tex, "faces": a.faces,
                "files": [os.path.basename(s) for s in saved],
                "tool": "local ComfyUI " + comfy.get("/system_stats")["system"]["comfyui_version"],
                "date": datetime.datetime.now().isoformat(timespec="seconds"),
            }
            with open(os.path.join(sub, "record.json"), "w", encoding="utf-8") as f:
                json.dump(record, f, indent=1)
            shutil.copy(a.picture, os.path.join(sub, os.path.basename(a.picture)))
    finally:
        free()


if __name__ == "__main__":
    main()
