"""ComfyUI helpers for the ink layers (Storybook 3): SAM 3 text masks, BiRefNet mattes,
MoGe-2 depth and Krea 2 turbo inpaint, each one call -> a PNG on disk. Needs the gpu turn."""
import os
import shutil
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comfy"))
import comfy  # noqa: E402
import depth as _depth  # noqa: E402
import ink_gen  # noqa: E402


def _up(path):
    """Upload under a unique name (the server keys uploads by file name)."""
    tmp = os.path.join(os.path.dirname(path), "_up_" + uuid.uuid4().hex[:8] + "_" + os.path.basename(path))
    shutil.copy(path, tmp)
    try:
        return comfy.upload(tmp)
    finally:
        os.remove(tmp)


def _run(g, dst):
    work = os.path.join(os.path.dirname(dst) or ".", "_tmp")
    saved = [p for p in comfy.run(g, work) if p.endswith(".png")]
    return saved


def sam(img, text, dst, threshold=0.4):
    """SAM 3 by text: the union mask of every object found, to dst (white: the object)."""
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sam3.1_multiplex_fp16.safetensors"}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": text}},
         "3": {"class_type": "LoadImage", "inputs": {"image": _up(img)}},
         "4": {"class_type": "SAM3_Detect", "inputs": {"model": ["1", 0], "image": ["3", 0], "threshold": threshold,
                                                       "refine_iterations": 2, "individual_masks": False, "conditioning": ["2", 0]}},
         "5": {"class_type": "MaskToImage", "inputs": {"mask": ["4", 0]}},
         "6": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "sb3sam"}}}
    os.replace(_run(g, dst)[0], dst)
    return dst


def birefnet(img, dst):
    g = {"1": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
         "2": {"class_type": "LoadImage", "inputs": {"image": _up(img)}},
         "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["1", 0], "image": ["2", 0]}},
         "4": {"class_type": "MaskToImage", "inputs": {"mask": ["3", 0]}},
         "5": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "sb3bir"}}}
    os.replace(_run(g, dst)[0], dst)
    return dst


def depth(img, dst):
    g = _depth.graph(img, "sb3depth")
    g["img"]["inputs"]["image"] = _up(img)
    os.replace(_run(g, dst)[0], dst)
    return dst


def krea(prompt, w, h, seed, dst, init=None, denoise=1.0, mask=None):
    """Krea 2 turbo (ink_gen's graph); init/mask are local paths."""
    g = ink_gen.graph(prompt, w, h, seed)
    if init:
        g = ink_gen.graph(prompt, w, h, seed, None, denoise, None)
        g.pop("l")
        g["li"] = {"class_type": "LoadImage", "inputs": {"image": _up(init)}}
        g["le"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["li", 0], "vae": ["v", 0]}}
        lat = ["le", 0]
        if mask:
            g["mi"] = {"class_type": "LoadImage", "inputs": {"image": _up(mask)}}
            g["mc"] = {"class_type": "ImageToMask", "inputs": {"image": ["mi", 0], "channel": "red"}}
            g["lm"] = {"class_type": "SetLatentNoiseMask", "inputs": {"samples": lat, "mask": ["mc", 0]}}
            lat = ["lm", 0]
        g["s"]["inputs"]["latent_image"] = lat
    os.replace(_run(g, dst)[0], dst)
    return dst
