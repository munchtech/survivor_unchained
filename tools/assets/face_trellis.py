"""A head made from a portrait by TRELLIS 2 (MIT) on the local ComfyUI: its
shape, for tools/assets/face_wrap.py to lay her MakeHuman face on, and the
same shape painted with TRELLIS's own colours (for her landmarks to be
read off a render of it, and for the paint of her head's sides).

    python tools/assets/face_trellis.py <picture.png> <out dir> [--seed N] [--res 1536]

Writes <out>/input.png, <out>/shape_*.glb (TRELLIS's surface, remeshed
clean and thinned to a million and a half faces) and <out>/painted_*.glb
(the same, with its colours on its points). ComfyUI must be running; its models are freed after.

Why TRELLIS: MakeHuman's targets only move a face's outlines (her lips,
lids and cheeks stayed thin and gaunt under every fit), and MoGe-2 reads a
picture's surface only from in front, flatter than it is. TRELLIS makes the
whole head, its volumes guessed as a sculptor would from the picture.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comfy"))
import comfy  # noqa: E402
from PIL import Image  # noqa: E402


def graph(name, seed=56, res="1536"):
    g = {
        "1": {"class_type": "LoadImage", "inputs": {"image": name}},
        "2": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
        "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "ImageCropToMask", "inputs": {"images": ["1", 0], "masks": ["3", 0], "width": 1024, "height": 1024,
                                                          "pad_factor": 1.1, "grow_mask": 0, "background": "#808080"}},
        "5": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "dino_v3_L_naf_fp32.safetensors"}},
        "6": {"class_type": "Trellis2Conditioning", "inputs": {"clip_vision_model": ["5", 0], "image": ["4", 0]}},
        "7": {"class_type": "UNETLoader", "inputs": {"unet_name": "trellis_2_int8_convrot.safetensors", "weight_dtype": "default"}},
        # (the structure's model and the shape's, CFG eased off at the end as TRELLIS's own graph has them)
        "8": {"class_type": "CFGOverride", "inputs": {"model": ["7", 0], "cfg": 1, "start_percent": 0.667, "end_percent": 1}},
        "9": {"class_type": "RescaleCFG", "inputs": {"model": ["8", 0], "multiplier": 0.7}},
        "10": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["9", 0], "shift": 5}},
        "11": {"class_type": "CFGOverride", "inputs": {"model": ["7", 0], "cfg": 1, "start_percent": 0.769, "end_percent": 1}},
        "12": {"class_type": "RescaleCFG", "inputs": {"model": ["11", 0], "multiplier": 0.5}},
        "13": {"class_type": "EmptyTrellis2LatentStructure", "inputs": {"batch_size": 1}},
        "14": {"class_type": "KSampler", "inputs": {"model": ["10", 0], "positive": ["6", 0], "negative": ["6", 1],
                                                    "latent_image": ["13", 0], "seed": seed, "steps": 12, "cfg": 7.5,
                                                    "sampler_name": "euler", "scheduler": "normal", "denoise": 1}},
        "15": {"class_type": "VAELoader", "inputs": {"vae_name": "trellis_2_shape_vae_bf16.safetensors"}},
        "16": {"class_type": "VaeDecodeStructureTrellis2", "inputs": {"samples": ["14", 0], "vae": ["15", 0], "resolution": "32"}},
        "17": {"class_type": "Trellis2ShapeStage", "inputs": {"positive": ["6", 0], "negative": ["6", 1], "voxel": ["16", 0]}},
        "18": {"class_type": "KSampler", "inputs": {"model": ["12", 0], "positive": ["17", 0], "negative": ["17", 1],
                                                    "latent_image": ["17", 2], "seed": seed + 1, "steps": 20, "cfg": 7.5,
                                                    "sampler_name": "euler", "scheduler": "normal", "denoise": 1}},
        "19": {"class_type": "Trellis2UpsampleStage", "inputs": {"positive": ["17", 0], "negative": ["17", 1], "shape_latent": ["18", 0],
                                                                 "vae": ["15", 0], "target_resolution": res}},
        "20": {"class_type": "KSampler", "inputs": {"model": ["12", 0], "positive": ["19", 0], "negative": ["19", 1],
                                                    "latent_image": ["19", 2], "seed": seed + 2, "steps": 12, "cfg": 7.5,
                                                    "sampler_name": "euler", "scheduler": "simple", "denoise": 1}},
        "21": {"class_type": "VaeDecodeShapeTrellis", "inputs": {"samples": ["20", 0], "vae": ["15", 0]}},
        # (remeshed clean, finer than TRELLIS's own graph and hardly smoothed:
        # a face's lids and lips are small. Thinned raw on the GPU, its
        # surface ran it out of memory. A UDF remesh is a thin shell, two
        # surfaces back to back: the inner one dropped.)
        "30": {"class_type": "RemeshMesh", "inputs": {"mesh": ["21", 0], "resolution": 1024, "sign_mode": "udf", "sign_mode.qef": False,
                                                      "sign_mode.drop_inverted_components": True,
                                                      "sign_mode.drop_enclosed_components": True, "band": 1, "project_back": 0,
                                                      "fix_poles": False, "smooth_iters": 4, "drop_small_components": 0.01,
                                                      "precluster_max_verts": 20000000}},
        "31": {"class_type": "DecimateMesh", "inputs": {"mesh": ["30", 0], "target_face_count": 1500000, "placement_mode": "midpoint"}},
        "23": {"class_type": "SaveGLB", "inputs": {"mesh": ["31", 0], "filename_prefix": "trellis_face/shape"}},
        "32": {"class_type": "Trellis2TextureStage", "inputs": {"positive": ["19", 0], "negative": ["19", 1], "shape_latent": ["20", 0]}},
        "33": {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["32", 0], "negative": ["32", 1],
                                                    "latent_image": ["32", 2], "seed": seed + 3, "steps": 12, "cfg": 1,
                                                    "sampler_name": "euler", "scheduler": "normal", "denoise": 1}},
        "34": {"class_type": "VAELoader", "inputs": {"vae_name": "trellis_2_texture_vae_bf16.safetensors"}},
        "35": {"class_type": "VaeDecodeTextureTrellis", "inputs": {"samples": ["33", 0], "vae": ["34", 0], "shape_subdivides": ["21", 1]}},
        "36": {"class_type": "PaintMesh", "inputs": {"mesh": ["31", 0], "voxel_colors": ["35", 0]}},
        "37": {"class_type": "SaveGLB", "inputs": {"mesh": ["36", 0], "filename_prefix": "trellis_face/painted"}},
        "38": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "trellis_face/cond"}},
    }
    return g


def free():
    """The shared GPU given back (the server answers with nothing)."""
    req = urllib.request.Request(comfy.URL + "/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req).read()


if __name__ == "__main__":
    src, out = sys.argv[1], os.path.abspath(sys.argv[2])
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 56
    res = sys.argv[sys.argv.index("--res") + 1] if "--res" in sys.argv else "1536"
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "input.png")
    Image.open(src).convert("RGB").save(p)
    try:
        for f in comfy.run(graph(comfy.upload(p), seed, res), out):
            print("TRELLIS", f)
    finally:
        free()
