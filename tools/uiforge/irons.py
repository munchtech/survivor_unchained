"""Her irons into the game: renders blender_irons.py's pieces (Blender, under a turn), then
downsamples each 3x into art/ui/hud/ at twice the shown size, sets every shadow to the spec's
55%, warms the hot ones as the chain's are (chain.ember_glow), computes the glass's light (a
sphere under the house light: the arched window, the hot spot, the refraction rim, the cuff's
shadow) and writes seat.json and the .import files (mipmaps on).

    python tools/uiforge/irons.py [--render] [piece ...]

glass*.png is premultiplied light: draw it with out = under * (1 - a) + rgb (Godot's
BLEND_MODE_PREMULT_ALPHA). cuff_glow.png is additive (rgb times a, tinted by the code).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

import chain as CH
import forge as F
import imports

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "irons", "raw")
HUD = os.path.join(ROOT, "godot", "art", "ui", "hud")
SPEC = json.load(open(os.path.join(HERE, "irons.json"), encoding="utf-8"))
SS = SPEC["scale"] // 2


def load(name):
    a = cv2.imread(os.path.join(RAW, name + ".png"), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
    img = np.dstack([a[..., 2], a[..., 1], a[..., 0], a[..., 3]])
    h, w = img.shape[:2]
    return F.downsample(img, (w // SS, h // SS))


def shadow(img, target=None, keep=None):
    """The catcher's shadow (dark, part transparent pixels) scaled so its deepest is the spec's 55%."""
    target = target or SPEC["shadow"]["alpha"]
    rgb, a = img[..., :3], img[..., 3]
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    sh = (lum < 0.02) & (a < 0.985)
    if keep is not None:
        sh &= keep
    m = a[sh].max() if sh.any() else 1
    out = img.copy()
    out[..., 3] = np.where(sh, a * (target / max(m, 1e-3)), a)
    return out


def save(img, name, premult=False):
    p = os.path.join(HUD, name + ".png")
    if premult:
        Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(p, optimize=True)
    else:
        F.save(F.to_pil(np.clip(img, 0, 1)), p)
    return p


def radial(img, cx, cy, r):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return np.hypot((xx + 0.5) / 2 - cx, (yy + 0.5) / 2 - cy) < r


def glass(r, size, ss=3):
    """The glass's light alone (2x file, premultiplied): a sphere cap of thick old glass under the
    house light. rgb is the light it adds, a how much it darkens what is under it."""
    N = size * 2 * ss
    k = N / size
    yy, xx = (np.mgrid[0:N, 0:N].astype(np.float32) + 0.5) / k - size / 2
    rho = np.hypot(xx, yy)
    Rc = r * 1.18
    nx, ny = xx / Rc, -yy / Rc
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    Rx, Ry, Rz = 2 * nz * nx, 2 * nz * ny, 2 * nz * nz - 1
    Fr = 0.045 + 0.955 * (1 - nz) ** 5

    def lobe(d, sharp):
        d = np.array(d, np.float32) / np.linalg.norm(d)
        return np.clip(Rx * d[0] + Ry * d[1] + Rz * d[2], 0, 1) ** sharp
    # the arched window, up and to the left: a tall opening with a round head, soft-edged
    w0 = np.array([-0.5, 0.58, 0.64], np.float32)
    w0 /= np.linalg.norm(w0)
    ev = np.array([0, 1, 0], np.float32) - w0[1] * w0
    ev /= np.linalg.norm(ev)
    eu = np.cross(ev, w0)
    u = Rx * eu[0] + Ry * eu[1] + Rz * eu[2]
    v = Rx * ev[0] + Ry * ev[1] + Rz * ev[2]
    front = Rx * w0[0] + Ry * w0[1] + Rz * w0[2]
    wu, wv = 0.16, 0.26
    sd = np.where(v < wv - wu, np.maximum(np.abs(u) - wu, -wv - v), np.hypot(u, v - (wv - wu)) - wu)
    win = np.clip(0.5 - sd / 0.05, 0, 1) * (front > 0)
    win *= np.clip(0.55 + 0.45 * (v + wv) / (2 * wv), 0, 1)          # brighter at its head
    light = np.zeros((N, N, 3), np.float32)
    light += (Fr * 6.0 * win)[..., None] * np.array([1.0, 0.95, 0.88], np.float32)
    light += (Fr * 30.0 * lobe([-0.62, 0.62, 0.48], 900))[..., None] * np.array([1.0, 0.94, 0.85], np.float32)
    light += (Fr * 1.6 * lobe([0.7, -0.62, 0.35], 14))[..., None] * np.array([0.72, 0.77, 1.0], np.float32)
    light = np.minimum(light, np.array([0.30, 0.30, 0.30]) + (Fr * 30.0 * lobe([-0.62, 0.62, 0.48], 900))[..., None])
    # the refraction ring: the rim 3 px darker, its lower-right inner edge a 1 px bright line
    ring = np.clip((rho - (r - 3.2)) / 3.0, 0, 1) ** 1.3 * 0.42
    ang = np.arctan2(yy, xx)
    lr = np.clip(np.cos(ang - np.pi / 4), 0, 1) ** 2.5
    line = np.exp(-((rho - (r - 3.4)) / 0.5) ** 2) * lr * 0.5
    light += line[..., None] * np.array([1.0, 0.9, 0.85], np.float32)
    # the cuff's soft shadow on its upper-left rim: how far up-left (toward the light) the rim is
    lx, ly = -0.7071, -0.7071
    b = xx * lx + yy * ly
    t = -b + np.sqrt(np.maximum(b * b - (rho * rho - r * r), 0))
    shade = (1 - np.clip(t / 6.0, 0, 1)) ** 1.6 * 0.55
    a = 1 - (1 - ring) * (1 - shade)
    inside = np.clip((r - rho) * k + 0.5, 0, 1)
    a = np.maximum(a, 2 / 255) * inside
    light = light * inside[..., None]
    out = np.dstack([light, a]).astype(np.float32)
    out = cv2.resize(out, (size * 2, size * 2), interpolation=cv2.INTER_AREA)
    # stored premultiplied, sRGB-encoded light
    rgb = np.clip(out[..., :3], 0, 1) ** (1 / 2.2)
    return np.dstack([rgb, out[..., 3]])


def make(pieces):
    os.makedirs(HUD, exist_ok=True)
    made = []
    c = SPEC["cuff"]
    if "cuff" in pieces:
        cx, cy = c["center"]
        img = load("cuff")
        inside = radial(img, cx, cy, c["glass_r"] - 0.5)
        img[..., 3] = np.where(inside, 0, img[..., 3])        # the glass's own shadow is in glass.png
        made.append(save(shadow(img), "cuff"))
        fr = load("cuff_front")
        made.append(save(shadow(fr), "cuff_front"))
        g = load("cuff_glow")
        pm = g[..., :3] * g[..., 3:4]
        A = pm.max(axis=2)
        A = A / max(A.max(), 1e-4)
        rgb = np.where(A[..., None] > 1e-4, pm / np.maximum(pm.max(axis=2, keepdims=True), 1e-4), 0)
        made.append(save(np.dstack([rgb, A]), "cuff_glow"))
        made.append(save(glass(SPEC["glass"]["r"], SPEC["glass"]["canvas"]), "glass", premult=True))
    if "small" in pieces:
        made.append(save(shadow(load("cuff_small")), "cuff_small"))
        made.append(save(glass(SPEC["glass_small"]["r"], SPEC["glass_small"]["canvas"]), "glass_small", premult=True))
    if "seats" in pieces:
        dims = json.load(open(os.path.join(RAW, "dimples.json")))
        meta = {"size": SPEC["seat"]["canvas"], "seat_at": SPEC["seat"]["at"], "seat": SPEC["seat"]["size"], "dimples": dims}
        for k in SPEC["seat"]["variants"]:
            full = load(f"seat_{k}")
            col = load(f"seat_collar_{k}")
            made.append(save(shadow(full), f"seat_{k}"))
            hot = shadow(load(f"seat_hot_{k}"))
            made.append(save(CH.ember_glow(hot, 0.7, edge=10), f"seat_hot_{k}"))
            # empty: the collar unlit (its rims about 35%), the floor at 60%
            cm = np.clip(col[..., 3] * (col[..., :3] @ np.array([0.3, 0.59, 0.11]) > 0.004), 0, 1)
            e = shadow(full).copy()
            e[..., :3] *= (cm * 0.52 + (1 - cm) * 0.6)[..., None]
            made.append(save(e, f"seat_empty_{k}"))
        json.dump(meta, open(os.path.join(HUD, "seat.json"), "w"), indent=1)
    if "sill" in pieces:
        for N in SPEC["sill"]["counts"]:
            made.append(save(shadow(load(f"sill_{N}")), f"sill_{N}"))
    if "tags" in pieces:
        for w in SPEC["tag"]["widths"]:
            made.append(save(shadow(load(f"tag_{w}")), f"tag_{w}"))
        made.append(save(shadow(load("tag_ring")), "tag_ring"))
    if "lock" in pieces:
        for n in ("lock", "lock_open"):
            made.append(save(shadow(load(n)), n))
        made.append(save(CH.ember_glow(shadow(load("lock_hot")), 0.7, edge=10), "lock_hot"))
        # the chain's middle link's upper bar, from its own sprite (for drawing over the shackle)
        K = SPEC["lock"]["link_variant"]
        for pre in ("", "warm_", "hot_"):
            s = np.asarray(Image.open(os.path.join(ROOT, "godot", "art", "ui", "chain", f"{pre}face_{K}.png")).convert("RGBA"), np.float32) / 255
            h = s.shape[0]
            yy = np.arange(h)[:, None]
            m = (yy < h / 2 - 1) & (s[..., 3] > 0.9)
            m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & (yy < h / 2 - 1)
            o = s.copy()
            o[..., 3] *= m
            made.append(save(o, f"lock_link_front{'_' + pre[:-1] if pre else ''}"))
    return made


def write_imports(paths):
    imports.write(paths)
    for p in paths:
        q = p + ".import"
        t = open(q, encoding="utf-8").read().replace("mipmaps/generate=false", "mipmaps/generate=true")
        if os.path.basename(p).startswith("glass"):
            t = t.replace("process/fix_alpha_border=true", "process/fix_alpha_border=false")
        open(q, "w", encoding="utf-8", newline="\n").write(t)


if __name__ == "__main__":
    args = sys.argv[1:]
    pieces = [a for a in args if not a.startswith("--")] or ["cuff", "small", "seats", "sill", "tags", "lock"]
    if "--render" in args:
        blender = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
        os.makedirs(RAW, exist_ok=True)
        r = subprocess.run([blender, "-b", "-P", os.path.join(HERE, "blender_irons.py"), "--", os.path.join(HERE, "irons.json"), RAW] + pieces,
                           capture_output=True, text=True, timeout=3600)
        if "Traceback" in r.stdout + r.stderr:
            raise SystemExit((r.stdout + r.stderr)[-3000:])
    paths = make(pieces)
    write_imports(paths)
    print("\n".join(paths))
