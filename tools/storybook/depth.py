"""Depth maps for the ControlNet's depth mode, made by MoGe-2 on the local ComfyUI
(near white, far and sky black: MoGe's disparity, 0.1-99.9 percentile normalised).
Round 15 takes a plate's layout from depth only (our block-ins, or a picture's
depth edited), never from a picture's edges: edges carry the old picture's hand.

    python tools/storybook/depth.py <img.png>... --out DIR     # writes <name>_depth.png
Take the GPU turn first (tools/turn.py take gpu "storybook: ...").
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comfy"))
import comfy  # noqa: E402

MOGE = "moge_2_vitl_normal_fp16.safetensors"


def graph(img, prefix):
    return {
        "img": {"class_type": "LoadImage", "inputs": {"image": comfy.upload(img)}},
        "moge": {"class_type": "LoadMoGeModel", "inputs": {"model_name": MOGE}},
        "inf": {"class_type": "MoGeInference", "inputs": {"moge_model": ["moge", 0], "image": ["img", 0], "resolution_level": 9,
                                                          "fov_x_degrees": 0.0, "batch_size": 1, "force_projection": True,
                                                          "apply_mask": True, "refine_steps": 3}},
        "ren": {"class_type": "MoGeRender", "inputs": {"moge_geometry": ["inf", 0], "output": "depth"}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["ren", 0], "filename_prefix": prefix}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imgs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in a.imgs:
        name = os.path.splitext(os.path.basename(f))[0]
        dst = os.path.join(a.out, name + "_depth.png")
        saved = comfy.run(graph(f, "sb_depth_" + name), os.path.join(a.out, "_tmp"))
        os.replace([p for p in saved if p.endswith(".png")][0], dst)
        print(dst, flush=True)


if __name__ == "__main__":
    main()
