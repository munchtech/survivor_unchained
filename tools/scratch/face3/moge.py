"""moge.py <image> <out dir> [left|right|whole]: MoGe-2's point map of a picture, as a mesh (glb) and depth/normal images."""
import os
import sys

sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9\tools\comfy")
import comfy  # noqa: E402
from PIL import Image  # noqa: E402

src, out = sys.argv[1], os.path.abspath(sys.argv[2])
part = sys.argv[3] if len(sys.argv) > 3 else "whole"
os.makedirs(out, exist_ok=True)
im = Image.open(src).convert("RGB")
if part != "whole":
    w = im.size[0]
    im = im.crop((0, 0, w // 2, im.size[1])) if part == "left" else im.crop((w // 2, 0, w, im.size[1]))
p = os.path.join(out, "input.png")
im.save(p)
name = comfy.upload(p)
g = {
    "1": {"class_type": "LoadImage", "inputs": {"image": name}},
    "2": {"class_type": "LoadMoGeModel", "inputs": {"model_name": "moge_2_vitl_normal_fp16.safetensors"}},
    "3": {"class_type": "MoGeInference", "inputs": {"moge_model": ["2", 0], "image": ["1", 0], "resolution_level": 9, "fov_x_degrees": 0,
                                                    "batch_size": 1, "force_projection": True, "apply_mask": True, "refine_steps": 0}},
    "4": {"class_type": "MoGePointMapToMesh", "inputs": {"moge_geometry": ["3", 0], "batch_index": 0, "decimation": 1,
                                                        "discontinuity_threshold": 0.04, "texture": True}},
    "5": {"class_type": "SaveGLB", "inputs": {"mesh": ["4", 0], "filename_prefix": "moge/face"}},
    "6": {"class_type": "MoGeRender", "inputs": {"moge_geometry": ["3", 0], "output": "normal_opengl"}},
    "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "moge_normal"}},
    "8": {"class_type": "MoGeRender", "inputs": {"moge_geometry": ["3", 0], "output": "depth_colored"}},
    "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "moge_depth"}},
    "10": {"class_type": "MoGeGeometryToFOV", "inputs": {"moge_geometry": ["3", 0], "axis": "horizontal", "unit": "degrees"}},
}
got = comfy.run(g, out)
print("GOT", got)

