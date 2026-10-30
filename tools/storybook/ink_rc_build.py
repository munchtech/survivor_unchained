"""Storybook 4 (sb00-p3p5-build): cut the re-carved, locally fixed p3 / p3d / p5 pictures into the layers
sb_wire_ink.py wires (out/ink_layers/<plate>/layers.json + PNGs, the same format ink_build writes).

    python tools/storybook/ink_rc_build.py [p3 p3d p5]

The config is ink_layers.PLATES[<plate>] (rc=True). A glow is a carved add layer: the posted picture minus the
posted picture with that light taken out (base + glow = the drawing, so the glow's opacity is the light's level).
p5: the night tone (ink_r5.night) then ink_post's cold light step, as ink_recarve posted it.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_layers as L  # noqa: E402
import ink_post as IP  # noqa: E402

OUT = os.path.join(HERE, "out", "ink_layers")


def gen_img(P):
    return np.asarray(Image.open(os.path.join(HERE, "out", P["gen"])).convert("RGB")).astype(np.float32) / 255


def night(im, k):
    """ink_r5.night on an array: everything sinks to k of its light except pools round the blue fires."""
    l = im.mean(-1)
    fire = ((im[..., 2] - im[..., 0] > 0.10) & (l > 0.5)) | (l > 0.93)
    fire = nd.binary_opening(fire, iterations=1)
    pool = nd.gaussian_filter(nd.binary_dilation(fire, iterations=6).astype(np.float32), 70)
    pool = np.clip(pool / max(1e-6, np.quantile(pool[fire], 0.5) if fire.any() else 1), 0, 1)
    return np.clip(im * (k + (1 - k) * pool)[..., None], 0, 1), fire


def post(P, im):
    return IP.post(IP.upscale(im, P["target"]), light=P["light"])


def warm_of(im):
    return np.clip((im[..., 0] - im[..., 2] - 0.08) / 0.15, 0, 1)


def drain(im, w):
    """Warm (ember) pixels to dark ash where w (as ink_recarve_dawn.regrade)."""
    lum = im.mean(-1, keepdims=True)
    ash = lum * 0.55 + np.array([0.06, 0.065, 0.075], np.float32)
    return im * (1 - w[..., None]) + ash * w[..., None]


def up(m, P, shape):
    return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).resize((shape[1], shape[0]), Image.BILINEAR)).astype(np.float32) / 255


def add_layer(lit, unl, region):
    unl = np.minimum(unl, lit)   # base + glow = the drawing exactly (no channel the drained version lifts)
    """Carved add layer inside region (posted px, 0..1): rgb = lit - unlit, cropped to where it is non-zero."""
    col = np.clip(lit - unl, 0, 1) * region[..., None]
    nz = col.max(-1) > 1.5 / 255
    ys, xs = np.nonzero(nz)
    y0, y1, x0, x1 = max(ys.min() - 4, 0), ys.max() + 5, max(xs.min() - 4, 0), xs.max() + 5
    a = nz[y0:y1, x0:x1].astype(np.float32)
    a = np.maximum(a, nd.binary_dilation(a > 0, iterations=2) * 1.0)
    return np.dstack([col[y0:y1, x0:x1], a]), x0, y0


def write(plate, P, layers):
    out = os.path.join(OUT, plate)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png"):
            os.remove(os.path.join(out, f))
    rec = []
    for name, z, blend, rgba, x0, y0 in layers:
        f = name + ".png"
        IP.save(rgba[..., :3], os.path.join(out, f), rgba[..., 3])
        rec.append(dict(file=f, name=name, z=z, blend=blend, state=None, seed=None,
                        pos=[round(x0 * P["upp"], 1), round(y0 * P["upp"], 1)], scale=P["upp"],
                        size_px=[rgba.shape[1], rgba.shape[0]]))
    H, W = layers[0][3].shape[:2]
    json.dump(dict(plate=plate, source=P["gen"], canvas_units=[round(W * P["upp"]), round(H * P["upp"])],
                   image_px=[W, H], units_per_px=P["upp"], rest=list(P["rest"]),
                   lens_note="pos/scale in canvas units, painted as seen from 'rest'; wiring shifts by (1600,900)-rest",
                   layers=rec), open(os.path.join(out, "layers.json"), "w", encoding="utf-8"), indent=1)
    # a half-size check of the base + glows at rest
    comp = layers[0][3][..., :3].copy()
    for name, z, blend, rgba, x0, y0 in layers[1:]:
        h, w = rgba.shape[:2]
        comp[y0:y0 + h, x0:x0 + w] = np.clip(comp[y0:y0 + h, x0:x0 + w] + rgba[..., :3] * rgba[..., 3:], 0, 1)
    im = Image.fromarray((comp * 255 + 0.5).astype(np.uint8))
    im.resize((W // 3, H // 3), Image.LANCZOS).save(os.path.join(OUT, f"rc_{plate}_third.jpg"), quality=88)
    print(plate, [(n, r.shape[1], r.shape[0]) for n, _, _, r, _, _ in layers], "canvas units", round(W * P["upp"]), round(H * P["upp"]))


def build_p5():
    P = L.PLATES["p5"]
    im, fire = night(gen_img(P), P["night_k"])
    lit = post(P, im)
    dim = im.copy()
    box = np.zeros(fire.shape, bool)
    bx0, by0, bx1, by1 = P["fire_box"]
    box[by0:by1, bx0:bx1] = True
    core = nd.binary_dilation(fire & box, iterations=2)
    dim[core] = dim[core] * 0.45
    unl = np.minimum(post(P, dim), lit)
    region = up(nd.binary_dilation(core, iterations=3), P, lit.shape[:2])
    base = np.dstack([unl, np.ones(unl.shape[:2], np.float32)])
    write("p5", P, [("land", 1.0, "mix", base, 0, 0), ("fires", 1.0, "add") + add_layer(lit, unl, region)])


def build_p3():
    P = L.PLATES["p3"]
    im = gen_img(P)
    H, W = im.shape[:2]
    # a green blotch in the top-left sky (the source's): to the sky's own blue-gray at its lightness
    sky = im[:160, :700]
    green = (sky[..., 1] > sky[..., 2] + 0.01) & (sky[..., 1] > sky[..., 0] + 0.02)
    green = nd.binary_dilation(green, iterations=3)
    ref = sky[~green].reshape(-1, 3).mean(0)
    sky[green] = sky[green].mean(-1, keepdims=True) / ref.mean() * ref
    w = warm_of(im)
    keep = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in P["keep_warm"]:
        keep[y0:y1, x0:x1] = True
    w = w * ~keep
    lit = post(P, im)
    unl = np.minimum(post(P, drain(im, w)), lit)
    dead = np.zeros((H, W), np.float32)
    x0, y0, x1, y1 = P["dead_box"]
    dead[y0:y1, x0:x1] = 1
    dead = up(dead, P, lit.shape[:2])
    base = np.dstack([unl, np.ones(unl.shape[:2], np.float32)])
    write("p3", P, [("field", 1.0, "mix", base, 0, 0),
                    ("dead_light", 1.0, "add") + add_layer(lit, unl, dead),
                    ("ember", 1.0, "add") + add_layer(lit, unl, 1 - dead)])


def build_p3d():
    P = L.PLATES["p3d"]
    lit = post(P, gen_img(P))
    if P.get("band"):     # Storybook 5: the first-light band along the hills (ink_sb5_c.dawn_band)
        import ink_sb5_c
        lit = ink_sb5_c.dawn_band(lit)
    write("p3d", P, [("dawn", 1.0, "mix", np.dstack([lit, np.ones(lit.shape[:2], np.float32)]), 0, 0)])


if __name__ == "__main__":
    for p in sys.argv[1:] or ["p3", "p3d", "p5"]:
        {"p3": build_p3, "p3d": build_p3d, "p5": build_p5}[p]()
