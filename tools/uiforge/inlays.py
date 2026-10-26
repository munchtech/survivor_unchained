"""Enamel inlays for the seats (docs/design/HUD_V2.md 3, "The glyph"): a skill's line glyph
(godot/data/content/glyphs.json, resolved as Glyphs.PathFor does) cut into the seat's dark iron
floor and filled with its school's enamel, glassy, domed a little so each stroke holds a small
highlight; closed shapes (Z) are filled as enamel fields. A height field (relief.py) lit in Blender
by the house light with the irons' rim turned down (blender_relief.py, RELIEF_LIGHT), so the
inlay and its seat share one light.

    python tools/uiforge/inlays.py [art_key ...]     # default: SPEC "keys"

Writes godot/art/ui/inlay/<art_key>.png (76 px, shown at 38: UiArt.Art($"inlay/{art}.png")),
straight alpha, the groove and its enamel only (the floor round it is the seat's own), and the
.import files with mipmaps.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

import cv2
import numpy as np

import forge as F
import imports
import relief as RL
import svgglyph as SG

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "godot", "art", "ui", "inlay")
IRONS = json.load(open(os.path.join(HERE, "irons.json"), encoding="utf-8"))
SPEC = IRONS["inlay"]
# ItemViews.SchoolColors
SCHOOL = {"physical": "#e8dcc4", "fire": "#ff8a4a", "frost": "#8fd0ff", "storm": "#9ab8ff", "nature": "#8ae05a",
          "arcane": "#cc88ff", "holy": "#ffd46a", "shadow": "#a87aff"}
# Glyphs.cs Families, in order
FAMILIES = [("slash|blade|oath|edge|grave", "slash"), ("axe|gyre|wheel", "axe"), ("dagger|knife|steel|cuts", "dagger"),
            ("arrow|volley|bow", "arrow"), ("mote|star|arcane", "arcane"), ("cinder|flame|fire|pyre|hell", "flame"),
            ("shard|frost|ice|rime|winter|hail|glacier", "frost"), ("arc|storm|sky|tempest|thunder", "bolt"),
            ("nova|dawn|sun|sanct|holy|ring", "sun"), ("beam|lance|gaze", "spear"), ("tether|siphon|coil|umbral|ruin|shadow", "drain"),
            ("blight|plague|rot", "plague"), ("thorn|bloom|root|briar", "thorn"), ("moon", "moon"), ("disc|aegis|reckon", "disc"),
            ("palm|temple", "palm"), ("herd|hunt", "herd"), ("chakram|gale|razor", "chakram"), ("zone|ground", "retaura")]


def path_key(key):
    if key in SG.glyphs():
        return key
    for pat, fam in FAMILIES:
        if re.search(pat, key.lower()):
            return fam
    return "arcane"


def schools():
    """Art key -> school from Weapons.cs: a weapon's art takes its school, an evolution's the School
    it names on its line, else its weapon's."""
    out, cur = {}, None
    for line in open(os.path.join(ROOT, "godot", "logic", "Content", "Weapons.cs"), encoding="utf-8"):
        w = re.search(r'Id = "[a-z_]+", Name = "[^"]*", School = School\.(\w+)', line)
        if w:
            cur = w.group(1).lower()
        a = re.search(r'\bArt = "([a-z_]+)"', line)
        if a and cur:
            s = None if w else re.search(r"School = School\.(\w+)", line)
            out.setdefault(a.group(1), s.group(1).lower() if s else cur)
    return out


def build(key, school):
    sp = SPEC
    N, ss = sp["file"], sp["ss"]
    R = RL.Relief(N, N, ss)
    S = N * ss
    u = S / 38.0 / (N / 76)                     # render px per shown px (76 file px = 38 shown)
    k = S / (24 + 2 * sp["pad"])                 # render px per glyph unit
    cl = np.zeros((S, S), np.uint8)
    fill = np.zeros((S, S), np.uint8)
    for pts, closed in SG.subpaths(SG.glyphs()[path_key(key)]):
        P = np.round((np.asarray(pts) + sp["pad"]) * k * 16).astype(np.int32)
        cv2.polylines(cl, [P], closed, 255, 1, cv2.LINE_8, shift=4)
        if closed and np.ptp(np.asarray(pts), axis=0).max() > 2.5:
            cv2.fillPoly(fill, [P], 255, cv2.LINE_8, shift=4)
    half = sp["width"] / 2 * u
    dcl = cv2.distanceTransform(255 - cl, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    ink = ((dcl <= half) | (fill > 0)).astype(np.uint8)
    x = cv2.distanceTransform(ink, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)      # in from the groove's edge
    lipw, run, we = sp["lip"] * u, sp["run"] * u, sp["dome"] * u
    HF, eE, sag, lipd = sp["floor_h"] * u, sp["edge_depth"] * u, sp["sag"] * u, sp["lip_depth"] * u
    t = np.clip(x / lipw, 0, 1)
    z = HF - lipd * (1 - np.cos(t * np.pi / 2))
    z = np.where(x > lipw, HF - lipd - (eE - lipd) * np.clip((x - lipw) / run, 0, 1), z)
    xe = np.clip((x - lipw - run) / we, 0, 1)
    z = np.where(x > lipw + run, HF - eE + sag * (1 - (1 - xe) ** 2), z)
    z = np.where(ink > 0, z, HF)
    fl = IRONS["seat"]
    RL.MATS["seat_floor"] = (fl["floor"], fl.get("floor_metal", 0.0), fl.get("floor_rough", 0.7), fl["floor"], 0.0)
    c = F.hexc(SCHOOL[school]) * sp["enamel_k"]                       # linear albedo
    ehex = "#" + "".join("%02x" % int(round(255 * v)) for v in F.lin_to_srgb(np.clip(c, 0, 1)))
    RL.MATS["enamel"] = (ehex, 0.0, sp["enamel_rough"], ehex, 0.0)
    RL.IDS.clear()
    RL.IDS.update({m: i for i, m in enumerate(RL.MATS)})
    one = np.ones((S, S), np.float32)
    R.put(one, height=z.astype(np.float32), mat="seat_floor", mode="set")
    en = (x > lipw + run - 0.5).astype(np.float32)
    R.put(en, mat="enamel")
    tint = sp["edge_min"] + (1 - sp["edge_min"]) * (xe * xe * (3 - 2 * xe))
    R.tint = np.where(en[..., None] > 0.5, tint[..., None], 1.0).astype(np.float32) * np.ones(3, np.float32)
    light = IRONS.get("light", {})
    os.environ["RELIEF_LIGHT"] = json.dumps(light)
    h = hashlib.sha1((json.dumps(sp, sort_keys=True) + json.dumps(light) + json.dumps(fl, sort_keys=True)).encode()).hexdigest()[:8]
    img = R.render(f"inlay_{key}_{h}", samples=sp["samples"], wear=0, grime=0, grain=0)
    img = img.copy()
    img[..., 3] *= cv2.GaussianBlur(ink.astype(np.float32), (0, 0), 0.6)
    img = F.downsample(img, (N, N))
    # cut, not printed: at 1080 the render's walls are under a pixel, so the cut's two edges are
    # set exactly, one shown px each: the wall in shade along the strokes' upper left (inside the
    # groove), the floor's lit lip along their lower right (outside it)
    b = max(1, int(round(sp.get("bevel_px", 1.0) * N / 38)))
    A = img[..., 3].copy()
    Aul = np.zeros_like(A)
    Aul[b:, b:] = A[:-b, :-b]
    dark, lip = A * (1 - Aul), (1 - A) * Aul
    img[..., :3] *= (1 - sp.get("shade", 0.72) * dark)[..., None]
    la = lip * sp.get("lip_alpha", 0.7)
    lc = np.array(sp.get("lip_rgb", [0.56, 0.54, 0.58]), np.float32)
    oa = A + la * (1 - A)
    img[..., :3] = (img[..., :3] * A[..., None] + lc * (la * (1 - A))[..., None]) / np.maximum(oa[..., None], 1e-4)
    img[..., 3] = oa
    return img


def main(keys):
    os.makedirs(OUT, exist_ok=True)
    sch = schools()
    paths = []
    for key in keys:
        img = build(key, sch.get(key, "physical"))
        p = os.path.join(OUT, key + ".png")
        F.save(F.to_pil(np.clip(img, 0, 1)), p)
        paths.append(p)
        print(p, path_key(key), sch.get(key))
    imports.write(paths)
    for p in paths:
        q = p + ".import"
        t = open(q, encoding="utf-8").read().replace("mipmaps/generate=false", "mipmaps/generate=true")
        open(q, "w", encoding="utf-8", newline="\n").write(t)
    return paths


if __name__ == "__main__":
    main(sys.argv[1:] or SPEC["keys"])
