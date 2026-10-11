"""Her ears in each face's paint brought to the skin just in front of them.

A face's lay paints her face alone; her ears keep the base head's paint, greyer and bluer than her cheek (own head:
ear 0.651/0.565/0.529 against cheek 0.704/0.573/0.514), and her face's tone (People.HerFaceTone, laid by the
features map's blue) stops short of them. Turned 40 degrees they read waxy grey-pink beside her cheek (judge j1,
11 October 2026). This scales each paint's ear texels, per channel in linear light (so the ear's own detail stays),
to the median of the skin in front of the ear as it renders (its paint times the face's tone where the features'
blue lays it), a touch warmer (WARM: ears run pinker than a cheek), eased in over the ear's root.

    python tools/assets/heroine_ears.py [face ...]     (no faces: all eleven paints in godot/art/people/head_tex)

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


def tones():
    s = open(PEOPLE, encoding="utf-8").read()
    return {k: np.array([float(a), float(b), float(c)]) for k, a, b, c in
            re.findall(r'\["(\w+)"\] = new\(([\d.]+)f, ([\d.]+)f, ([\d.]+)f\)', s)}


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


if __name__ == "__main__":
    main(sys.argv[1:])
