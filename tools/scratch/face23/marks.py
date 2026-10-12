"""marks.py OUTDIR: the owner's two marks (12 Oct) in UV space. Crops of every map the skin shader reads (paint of
several faces, the head's relief normal map from heroine.glb, ao, features) at the mouth and the left eye, each with
the mesh's edges overlaid (thin, half the tiles), so a line in a map can be put against the mesh's lip/lid."""
import os, sys, io, json
import numpy as np
from PIL import Image, ImageDraw
R = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0"
sys.path.insert(0, R + "/tools/assets")
import heroine_seam as hs
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
js, binc = hs._load(R + "/godot/art/people/heroine.glb")
mats = js["materials"]
prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]].get("name") == "skin_head")
mat = mats[prim["material"]]
print("skin_head material:", json.dumps({k: v for k, v in mat.items() if k != "extensions"})[:400])
P = hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
print("head bbox", P.min(0).round(3), P.max(0).round(3))

def glb_image(idx):
    im = js["images"][idx]; bv = js["bufferViews"][im["bufferView"]]
    off = bv.get("byteOffset", 0)
    return Image.open(io.BytesIO(bytes(binc[off:off + bv["byteLength"]]) if not isinstance(binc, list) else b""))

maps = {}
H = R + "/godot/art/people/head_tex/"
for f in ("own:heroine_head.jpg", "doe:heroine_head_doe.jpg", "vixen:heroine_head_vixen.jpg", "ao:heroine_ao.png",
          "features:heroine_features.png", "freckles:heroine_freckles.png", "brows:../paint/brows.png"):
    k, fn = f.split(":"); maps[k] = Image.open(H + fn)
nt = mat.get("normalTexture")
if nt is not None:
    try:
        src = js["textures"][nt["index"]]["source"]; maps["relief"] = glb_image(src).convert("RGB")
        print("relief from glb image", src, maps["relief"].size)
    except Exception as e:
        print("relief read failed", e)
else:
    print("skin_head has NO normalTexture")

# regions: the mouth (front, midline, between nose and chin) and the left eye
zf = P[:, 2]
def box(sel, pad):
    u = UV[sel]; u0 = u.min(0) - pad; u1 = u.max(0) + pad; return u0, u1
mid = (np.abs(P[:, 0]) < 0.022)
front = zf > np.percentile(zf, 93)
regions = {}
regions["mouth"] = (np.array([0.36, 0.36]), np.array([0.46, 0.46]))
ey = (P[:, 0] > 0.018) & (P[:, 0] < 0.05) & (P[:, 1] > 1.742) & (P[:, 1] < 1.778) & (P[:, 2] > 0.07)
regions["eye"] = (np.array([0.41, 0.48]), np.array([0.53, 0.60]))
for rn, (u0, u1) in regions.items():
    print(rn, "uv box", u0.round(4), u1.round(4))
    tiles = []
    for k, im in maps.items():
        W, Hh = im.size
        # glTF uv: v down from the top in image space
        x0, y0, x1, y1 = int(u0[0] * W), int(u0[1] * Hh), int(u1[0] * W), int(u1[1] * Hh)
        c = im.convert("RGBA" if k in ("ao", "features", "freckles", "brows") else "RGB").crop((x0, y0, x1, y1))
        sc = 512 / max(c.width, 1)
        c = c.resize((512, int(c.height * sc)), Image.LANCZOS)
        chans = [("rgb", c.convert("RGB"))] if k not in ("ao", "features", "freckles") else \
            [(ch, Image.merge("RGB", [c.getchannel(i)] * 3)) for i, ch in enumerate("rgba")]
        for ch, ci in chans:
            for wire in (False, True):
                t = ci.copy(); d = ImageDraw.Draw(t)
                if wire:
                    for tri in T:
                        uv = UV[tri]
                        if (uv[:, 0] < u0[0]).all() or (uv[:, 0] > u1[0]).all() or (uv[:, 1] < u0[1]).all() or (uv[:, 1] > u1[1]).all():
                            continue
                        pts = [((a - u0[0]) * W * sc, (b - u0[1]) * Hh * sc) for a, b in uv]
                        d.line(pts + [pts[0]], fill=(0, 255, 255), width=1)
                d.text((4, 4), f"{k}.{ch}{' wire' if wire else ''}", fill=(255, 255, 0))
                t.save(os.path.join(out, f"{rn}_{k}_{ch}{'_w' if wire else ''}.png"))
print("done")
