"""Her ears in each face's paint brought to the skin just in front of them.

A face's lay paints her face alone; her ears keep the base head's paint, greyer and bluer than her cheek (own head:
ear 0.651/0.565/0.529 against cheek 0.704/0.573/0.514), and her face's tone (People.HerFaceTone, laid by the
features map's blue) stops short of them. Turned 40 degrees they read waxy grey-pink beside her cheek (judge j1,
11 October 2026). This scales each paint's ear texels, per channel in linear light (so the ear's own detail stays),
to the median of the skin in front of the ear as it renders (its paint times the face's tone where the features'
blue lays it), a touch warmer (WARM: ears run pinker than a cheek), eased in over the ear's root.

    python tools/assets/heroine_ears.py [face ...]     (no faces: all eleven paints in godot/art/people/head_tex)
    python tools/assets/heroine_ears.py --render FILE  (the render's own miss, measured: from_render)

Idempotent only from the originals: it measures the ear against the cheek, so a rerun converges, but run it on
paints fresh from the lay (heroine_face.py) and after heroine_jaw_cut.py.
"""
import os
import re
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402
from heroine_ao_seam import raster  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
PEOPLE = os.path.join(ROOT, "godot", "src", "Actors", "People.cs")
EAR = (0.076, 1.735, -0.018)     # (each ear's middle, metres, glTF axes: x across, y up, z forward)
EAR_R = (0.026, 0.034)           # (all of the ear within the first, eased out by the second)
EAR_X = (0.062, 0.067)           # (and outside her skull's side: nothing on her cheek or temple)
WARM = np.array([1.02, 1.0, 0.985])


def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _block(s, name):
    s = s[s.index("Dictionary<string, Vector3> %s = new()" % name):]
    s = s[:s.index("};")]
    return {k: np.array([float(a), float(b), float(c)]) for k, a, b, c in
            re.findall(r'\["(\w+)"\] = new\(([\d.]+)f, ([\d.]+)f, ([\d.]+)f\)', s)}


def tones():
    """Each face's tone where the features' blue lays it, as People.FaceTone gives it: HerFaceTone times the share
    of HerBodyTone her body doesn't take (BodyK). Her body's share multiplies ear and cheek alike, so it doesn't count."""
    s = open(PEOPLE, encoding="utf-8").read()
    k = float(re.search(r'float BodyK = .*?: ([\d.]+)f;', s).group(1))
    face, body = _block(s, "HerFaceTone"), _block(s, "HerBodyTone")
    return {f: t * body.get(f, np.ones(3)) ** (1 - k) for f, t in face.items()}


def main(faces):
    js, binc = hs._load(GLB)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    ax = np.abs(P[:, 0])
    d = np.linalg.norm(np.c_[ax, P[:, 1:]] - np.array(EAR), axis=1)
    w = (1 - smooth(EAR_R[0], EAR_R[1], d)) * smooth(EAR_X[0], EAR_X[1], ax)
    ref = (ax > 0.055) & (ax < 0.068) & (P[:, 2] > 0.015) & (P[:, 2] < 0.045) & (P[:, 1] > 1.70) & (P[:, 1] < 1.745)
    ear = w > 0.9
    fb = np.asarray(Image.open(os.path.join(TEX, "heroine_features.png")).convert("RGB"))[..., 2] / 255.0
    tone = tones()
    mask = None
    paints = {"own": "heroine_head.jpg"}
    for f in os.listdir(TEX):
        m = re.fullmatch(r"heroine_head_(\w+)\.jpg", f)
        if m: paints[m.group(1)] = f
    for face in faces or sorted(paints):
        path = os.path.join(TEX, paints[face])
        im = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255
        n = im.shape[0]
        if mask is None or mask.shape[0] != n:
            mask = raster(UV, T, w, n)
        def at(img, sel):
            x = np.clip((UV[sel, 0] * img.shape[1]).astype(int), 0, img.shape[1] - 1)
            y = np.clip((UV[sel, 1] * img.shape[0]).astype(int), 0, img.shape[0] - 1)
            return img[y, x]
        t = tone.get(face, np.ones(3))
        fr = at(fb, ref)[:, None]
        cheek = np.median(lin(at(im, ref)) * (1 + (t - 1) * fr), 0)
        e = np.median(lin(at(im, ear)), 0)
        gain = cheek / e * WARM
        L = lin(im)
        out = srgb(L * (1 + (gain - 1) * mask[..., None]))
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, quality=95, subsampling=0)
        print("EARS %-9s gain %.3f %.3f %.3f (ear %s, front of it %s)" % (face, *gain, np.round(srgb(e), 3), np.round(srgb(cheek), 3)))


M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
               [0.0259040371, 0.7827717662, -0.8086757660]])


def oklab(c): return np.cbrt(c @ M1.T) @ M2.T
def unoklab(c): return (c @ np.linalg.inv(M2).T) ** 3 @ np.linalg.inv(M1).T


def from_render(fixes):
    """Each face's ear moved by what its render shows (earmeas.py: her lit ear against her lit cheek at 40 degrees,
    hair that shows it): lightness by the ratio of the two, chroma by theirs, hue turned toward the cheek's, in Oklab
    on the ear's texels (eased in as main's). The paint's own tone is not the render's (her face's tone, the soft
    lamps' tint and the lift lie over it, and the ear is lit at another angle), so this closes the loop on what shows;
    a rerun on a fresh measure converges. fixes: {face: (L ratio, C ratio, hue degrees)}."""
    js, binc = hs._load(GLB)
    mats = [m.get("name") for m in js["materials"]]
    prim = next(p for m in js["meshes"] for p in m["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    ax = np.abs(P[:, 0])
    d = np.linalg.norm(np.c_[ax, P[:, 1:]] - np.array(EAR), axis=1)
    w = (1 - smooth(EAR_R[0], EAR_R[1], d)) * smooth(EAR_X[0], EAR_X[1], ax)
    mask = None
    for face, (rl, rc, dh) in fixes.items():
        path = os.path.join(TEX, "heroine_head.jpg" if face == "own" else "heroine_head_%s.jpg" % face)
        im = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255
        if mask is None or mask.shape[0] != im.shape[0]:
            mask = raster(UV, T, w, im.shape[0])
        lab = oklab(lin(im))
        c, s_ = np.cos(np.radians(dh)), np.sin(np.radians(dh))
        a, b = lab[..., 1] * rc, lab[..., 2] * rc
        moved = np.stack([lab[..., 0] * rl, a * c - b * s_, a * s_ + b * c], -1)
        out = srgb(np.clip(unoklab(lab + (moved - lab) * mask[..., None]), 0, 1))
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, quality=95, subsampling=0)
        print("EARS %-9s L x%.3f C x%.3f h %+.1f" % (face, rl, rc, dh))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--render"]:
        # --render FILE: lines "face L-ratio C-ratio hue-degrees"
        from_render({f: (float(l), float(c), float(h)) for f, l, c, h in (ln.split() for ln in open(sys.argv[2]) if ln.strip())})
    else:
        main(sys.argv[1:])
