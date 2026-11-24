#!/usr/bin/env python3
"""The den's painted set (den round 10, 15 Nov): paintings by an image model (the ChatGPT imaging route, allowed by the
owner; one line per image in set_src/PROVENANCE.txt and docs/team/provenance.md) laid in the den by rule and projected
from the fixed play camera onto the bank and the floor (src/World/DungeonDress.Set.cs, shaders/den_set.gdshader).

  python tools/look/den_set.py ingest   copy the sources from survivorsunchained_inputs/gpt_den into set_src (once)
  python tools/look/den_set.py build    set_src -> art/dungeon/den/set/*.png + set.json (+ .import, lossless, mipmaps)
  python tools/look/den_set.py check    key (no magenta fringe), rects, feet, the floor tiles' wrap seams

The rules (no hand fixes on the outputs):
- KEY: alpha from the magenta-ness min(R, B) - G (255 on the key, under ~20 on every den colour), the key unmixed from
  the edge pixels (c = a f + (1 - a) magenta) and any cast left (min(R, B) over G by more than 12) taken off R and B.
- SCALE: the banks keep their source pixels at BANK_PPM px per metre of the camera's plane (1 source px = 1 screen px at
  the frame's middle, so the big roots read 0.7-1 m thick, the target's; PROMPTS.md's "9 m" runs would draw them a
  third of that); objects are scaled from the metres PROMPTS.md gives their biggest piece and resampled to OBJ_PPM.
- FEET: a bank's foot (where it meets the walkable floor) is its last solid row or column (coverage >= SOLID) on the
  floor's side: far banks the lowest, near banks the highest, a left wall the rightmost, a right wall the leftmost.
- FLOOR: each 4 m tile at FLOOR_PX, made seamless by offset-and-blend (the half-turned tile at the edges, the source at
  its middle cross, a noisy mask between); its height (blurred luminance) rides the alpha for the floor's height blend.
"""
import json, os, shutil, sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DEN = os.path.join(ROOT, "godot", "art", "dungeon", "den")
SRC = os.path.join(DEN, "set_src")
OUT = os.path.join(DEN, "set")
INPUTS = r"C:\Users\munch\Desktop\survivorsunchained_inputs\gpt_den"

BANKS = {   # name: kind (far: its face looks at the camera; near: seen from above and behind; left/right: a wall's side)
    "B1": "far", "B1b": "far", "B2": "near", "B2b": "near", "B3": "left", "B3b": "left", "B3R": "right", "B3Rb": "right",
    "B4": "corner_l", "B4R_2": "corner_r", "B5": "spur",
}
SHEETS = {  # name: (kind, metres of its widest piece or None = the banks' scale)
    "B6": ("spill", None), "O1": ("boulder", 3.2), "O2": ("log", 6.0), "O3": ("bones", 2.0),
    "H1": ("hollow", 5.0), "H2": ("pit", 12.0),
    # (den r18 P5, R17 item 1) the lair's two pits as den_boss.png's (sunken, the far wall lit, veins glowing, roots over the lips):
    # source px kept (None: k 1), since PlaceSetHole lays each painted lip to its hole's own radius, only the resolution rides on it
    "H3": ("pit", None),
    # (r10d) above: the hollows' bowls 3-4 m and the pit 10 m, each with its fading surround
    "O4": ("drift", 5.5),   # (r11) two long low bone drifts for the far banks' feet
    "O6": ("fur", 1.5),     # (den r16 W, R15f item 10) 6 pale fur clumps and 2 dry leaf drifts for the open floor
    "O5": ("blood", 2.0),   # (r11) blood pools, spatters and smears (the owner had ChatGPT make it by hand after a refusal)
    # (den r18 D4, R17 items 2, 7) Batch 6: shaped bones for the litter (3 long bones, 2 ribs, a jaw, 2 skull fragments, 2 shard
    # scatters: the decal dumbbells' place), the lair's arc of standing tusks on earth mounds, flayed hides and gnawed haunches
    "O7": ("bones", 1.25), "O8": ("arc", 1.9), "O9": ("carcass", 2.3),
}
JOIN = {"O7": 30, "O9": 30}   # (den r18 D4) source px within which parts are one piece (a shard scatter is one; default 20)
MIRROR = {"O7", "O8", "O9"}   # (den r18 D4, R17 item 2) each piece followed by its mirror image (piece i + n): the litter's mirroring (light kept from the upper side)
DESAT = {"O6": 0.8}   # (den r16 W, R15f item 10) a sheet's colour pulled this far to its grey (the fur's lilac read pink on screen; target C <= .03)
# (den r17 S, R16 judge item 6: the tufts rendered two-toned, blue h 238-251 or cream h 77-85, never the target's warm grey)
# the fur graded in OKLab to one warm-grey albedo: its value strokes kept (L re-centred on L50, spread kept), hue FUR_H,
# chroma FUR_C (rising from the darks), so the sheet carries the colour and the material's sat can stay near 1. Replaces DESAT.
# (den r17 D3, R16 item: the tufts rendered L .73-.79 C .085-.09 at --den-fur-sat 2, bright confetti; den_room's fur sits
# into the floor, warm grey with a darker underside) l50 and c down, the spread up (its strands), and "under": L taken
# off toward each piece's lower edge (its ground side), up to this much at the foot. Was h 54, c .045, l50 .68, spread .85 (graded on the painting, so the sat 2 material doubles its C).
# (den r19 B, R18b item 8: loud orange leaf clusters, s23 corr (560,690,620,730)) the O6 sheet's dry leaf drifts: chroma x C, L + DL (OKLab); `den_set.py leaves` applies it to O6.png in place
LEAF_GRADE = {"O6": {"c": 0.7, "dl": -0.05}}
FUR_GRADE = {"O6": {"h": 52.0, "c": 0.028, "l50": 0.66, "spread": 1.0, "under": 0.1}}
# (den r17 S, R16 judge item 7: the s23 corridor log's lit top rendered L50 .755, C .120, glowing orange under the shaft, against
# den_room's .678 / .101) a sheet's lit values rolled off in OKLab: above L knee, the rise kept at this share, and its chroma
# scaled toward this (at the top), the darks and strokes untouched.
LIT_KNEE = {"O2": {"knee": 0.58, "share": 0.4, "c": 0.85},
            # (den r18 D4, R17 item 2: bone band h 47-60, C .04-.06, lit L50 <= .70; O8 painted tan) the new bones' lights rolled off
            "O7": {"knee": 0.62, "share": 0.45, "c": 0.85}, "O8": {"knee": 0.58, "share": 0.4, "c": 0.72}}
# (den r18 P5) a hole painting's mouth found as its biggest cool region (R - B over the sum, blurred, under this): H3's veins and
# lit far wall split the dark-mass rule's throat (it took the left third of the bowl); the lip is the warm earth's inner edge
MOUTH_WARM = {"H3": 0.10}
DESTREAK = {"F1": 0.8, "F2": 1.0, "F3": 0.9, "F4": 0.6}   # (r10d) how far each tile's directional mid band is evened (1: fully)
# (r11) the floor's layers, in the shader's order: base earth, trodden, damp, root runs, a second base earth. Batch 4's
# cel-painted tiles (inked stones, drawn cracks); F1-F4's photographic grain read as a soft cloud at the play camera and
# destreak (an FFT cut, never up) took more of what detail they had. The new tiles are not destreaked.
FLOORS = ["F5", "F7", "F8", "F9", "F6"]
BANK_PPM = 80.0      # source px per metre of the camera's plane (the frame's middle draws 76.8 px/m)
OBJ_PPM = 96.0       # objects resampled to this (crisp from the frame's top, 61 px/m, to its bottom, 93)
FLOOR_PX, FLOOR_M = 512, 4.0
SOLID = 0.9
MAG = np.array([255.0, 0.0, 255.0])


def key(rgb):
    """Magenta keyed out: (colour unmixed and despilled, alpha), floats 0-255 and 0-1."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m = np.minimum(r, b) - g
    a = np.clip((235.0 - m) / 215.0, 0.0, 1.0)
    f = (rgb - (1.0 - a[..., None]) * MAG) / np.maximum(a[..., None], 1e-3)
    f = np.clip(f, 0.0, 255.0)
    s = np.maximum(np.minimum(f[..., 0], f[..., 2]) - f[..., 1] - 12.0, 0.0)
    f[..., 0] -= s
    f[..., 2] -= s
    f[a < 1e-3] = 0.0
    return f, a


# (den r15 R, R15 judge item 9) B3R (the right wall's face) has a big pale moss-topped block painted into it: with the wall
# drawn at the play camera it is the "pale cube" (s11 room 1790-1920,620-800; --den-set-dbgmod 1 shows it is the bank's own
# module, not a stone). Its outline (source px, closed polygon) is replaced by bare dirt: the painting inpainted, pulled
# to the surrounding dirt's colour, with a seeded multi-scale grain. Applied by load(), so every build has it.
BANK_FIXES = {"B3R": [(660, 552), (667, 520), (685, 487), (710, 462), (740, 440), (775, 420), (805, 416), (837, 436), (880, 431),
                     (885, 455), (865, 500), (860, 530), (840, 560), (805, 585), (765, 597), (725, 610), (695, 620), (660, 615),
                     (644, 600), (644, 555)]}
DIRT = (112.0, 74.0, 56.0)
# (den r17 S, R16 judge item 9: the cleared block drew a smooth dirt oval at the s11 room's right edge, grad .0079, edge share
# .033, no ink) the cleared area filled from the card's own painting at this offset (source px: B3R's inked roots over dirt
# below the block), its colour matched to the ring round the hole, over the inpaint. None: the r15 inpaint and grain only.
BANK_DONOR = {"B3R": (-100, 400)}


def clear_block(img, poly, donor=None):
    import cv2
    im8 = img.round().clip(0, 255).astype(np.uint8)
    mask = np.zeros(im8.shape[:2], np.uint8)
    cv2.fillPoly(mask, [np.array(poly, np.int32)], 255)
    mask = cv2.dilate(mask, np.ones((11, 11), np.uint8))
    inp = cv2.inpaint(np.ascontiguousarray(im8[..., ::-1]), mask, 9, cv2.INPAINT_TELEA)[..., ::-1].astype(np.float32)
    inp = inp * 0.3 + np.array(DIRT, np.float32) * 0.7
    rng = np.random.default_rng(7)
    h, w = mask.shape
    n = sum(cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), sg) * am for sg, am in ((1.2, 14), (3, 22), (9, 40)))
    inp = inp * (1 + n[..., None] / 160) + n[..., None] * 0.5
    soft = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 5)[..., None]
    if donor is not None:
        dx, dy = donor
        don = np.roll(img, (-dy, -dx), axis=(0, 1)).astype(np.float32)
        hole = mask > 0
        ring = (cv2.dilate(mask, np.ones((41, 41), np.uint8)) > 0) & ~hole
        for ch in range(3):   # the donor's mean and spread to the ring's
            dm, ds = don[..., ch][hole].mean(), don[..., ch][hole].std() + 1e-3
            rm, rs = img[..., ch][ring].mean(), img[..., ch][ring].std()
            don[..., ch] = (don[..., ch] - dm) * min(1.0, rs / ds) + rm
        inp = don
    return np.clip(img * (1 - soft) + inp * soft, 0, 255)


def load(name):
    img = np.asarray(Image.open(os.path.join(SRC, name + ".png")).convert("RGB"), dtype=np.float64)
    if name in BANK_FIXES:
        img = clear_block(img, BANK_FIXES[name], BANK_DONOR.get(name))
    return img


def resample(f, a, k):
    """Premultiplied Lanczos resample by k (colour 0-255, alpha 0-1)."""
    if abs(k - 1.0) < 1e-6:
        return f, a
    h, w = a.shape
    nw, nh = max(1, round(w * k)), max(1, round(h * k))
    pm = np.dstack([f * a[..., None], a * 255.0]).clip(0, 255)
    out = []
    for ch in range(4):
        im = Image.fromarray(pm[..., ch].astype(np.float32), mode="F")
        out.append(np.asarray(im.resize((nw, nh), Image.LANCZOS), dtype=np.float64))
    na = np.clip(out[3] / 255.0, 0.0, 1.0)
    nf = np.dstack(out[:3]) / np.maximum(na[..., None], 1e-3)
    nf[na < 1e-3] = 0.0
    return np.clip(nf, 0, 255), na


def save_rgba(path, f, a):
    arr = np.dstack([f, a * 255.0]).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(path, optimize=True)


def write_import(path, layered=0):
    """A lossless, mipmapped import (Godot fills in the uid and the imported path)."""
    imp = path + ".import"
    if layered:
        txt = ('[remap]\n\nimporter="2d_array_texture"\ntype="CompressedTexture2DArray"\n\n[params]\n\n'
               "compress/mode=0\ncompress/high_quality=false\ncompress/lossy_quality=0.7\ncompress/uastc_level=0\n"
               "compress/rdo_quality_loss=0.0\ncompress/hdr_compression=1\ncompress/channel_pack=0\n"
               f"mipmaps/generate=true\nmipmaps/limit=-1\nslices/horizontal=1\nslices/vertical={layered}\n")
    else:
        txt = ('[remap]\n\nimporter="texture"\ntype="CompressedTexture2D"\n\n[params]\n\n'
               "compress/mode=0\ncompress/high_quality=false\ncompress/lossy_quality=0.7\ncompress/uastc_level=0\n"
               "compress/rdo_quality_loss=0.0\ncompress/hdr_compression=1\ncompress/normal_map=0\ncompress/channel_pack=0\n"
               "mipmaps/generate=true\nmipmaps/limit=-1\nroughness/mode=0\nroughness/src_normal=\"\"\n"
               "process/channel_remap/red=0\nprocess/channel_remap/green=1\nprocess/channel_remap/blue=2\n"
               "process/channel_remap/alpha=3\nprocess/fix_alpha_border=true\nprocess/premult_alpha=false\n"
               "process/normal_map_invert_y=false\nprocess/hdr_as_srgb=false\nprocess/hdr_clamp_exposure=false\n"
               "process/size_limit=0\ndetect_3d/compress_to=0\n")
    # the import group (tools/godot/tex_groups.json) owns the compression keys; a rebuild must not undo it
    sys.path.insert(0, os.path.join(ROOT, "tools", "godot"))
    import tex_groups
    rel = os.path.relpath(path, os.path.join(ROOT, "godot")).replace("\\", "/")
    want = tex_groups.group_params(rel, "2d_array_texture" if layered else "texture")
    if want:
        txt = tex_groups.merge(txt, want)
    if os.path.exists(imp):   # keep Godot's uid and path once it has written them; only the params are ours
        old = open(imp, encoding="utf-8").read()
        if "[params]" in old and old.split("[params]")[1].strip() == txt.split("[params]")[1].strip():
            return
        txt = old.split("[params]")[0] + "[params]" + txt.split("[params]")[1]
    with open(imp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)


def bbox(a, thr=0.02):
    ys, xs = np.nonzero(a > thr)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def feet(kind, a):
    """The foot as a fraction: of the height (far, near) or the width (left, right); corners give both."""
    s = a > 0.5
    h, w = s.shape

    def last(cov, rev):
        idx = np.nonzero(ndimage.uniform_filter1d(cov.astype(float), 9) >= SOLID)[0]
        return None if len(idx) == 0 else int(idx.min() if rev else idx.max())

    out = {}
    if kind in ("far", "corner_l", "corner_r"):
        cols = slice(w // 2, w) if kind == "corner_l" else slice(0, w // 2) if kind == "corner_r" else slice(0, w)
        y = last(s[:, cols].mean(1), False)
        out["foot_v"] = (y + 1) / h if y is not None else 1.0
    if kind == "near":
        y = last(s.mean(1), True)
        out["foot_v"] = y / h if y is not None else 0.0
    if kind in ("left", "corner_l"):
        rows = slice(h // 2, h) if kind == "corner_l" else slice(0, h)
        x = last(s[rows, :].mean(0), False)
        out["foot_u"] = (x + 1) / w if x is not None else 1.0
    if kind in ("right", "corner_r"):
        rows = slice(h // 2, h) if kind == "corner_r" else slice(0, h)
        x = last(s[rows, :].mean(0), True)
        out["foot_u"] = x / w if x is not None else 0.0
    return out


def pieces(a, join=20, keep=0.015):
    """Connected pieces of a sheet: parts within `join` px are one piece; pieces under `keep` of the biggest dropped."""
    grown = ndimage.binary_dilation(a > 0.5, iterations=join)
    lab, n = ndimage.label(grown)
    sizes = ndimage.sum(a > 0.5, lab, range(1, n + 1))
    big = sizes.max()
    out = []
    for i in range(1, n + 1):
        if sizes[i - 1] < keep * big:
            continue
        ys, xs = np.nonzero((lab == i) & (a > 0.02))
        h, w = a.shape   # (a 3 px margin of clear key round each piece, so no rect edge cuts it)
        out.append((max(int(xs.min()) - 3, 0), max(int(ys.min()) - 3, 0), min(int(xs.max()) + 4, w), min(int(ys.max()) + 4, h), i))
    out.sort(key=lambda p: (p[1] // 200, p[0]))
    return out, lab


def seamless(img, rng):
    """Offset-and-blend: the half-turned tile at the edges (it wraps clean), the source at its middle cross."""
    h, w, _ = img.shape
    rolled = np.roll(img, (h // 2, w // 2), axis=(0, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    tri = np.maximum(1.0 - np.abs(2.0 * (xx + 0.5) / w - 1.0), 1.0 - np.abs(2.0 * (yy + 0.5) / h - 1.0))
    noise = ndimage.gaussian_filter(rng.standard_normal((h, w)), w / 40.0, mode="wrap")
    noise = noise / (np.abs(noise).max() + 1e-9)
    m = np.clip((tri + 0.12 * noise - 0.62) / 0.16, 0.0, 1.0)
    m = m * m * (3 - 2 * m)
    return img * m[..., None] + rolled * (1.0 - m[..., None])


def destreak(img, k):
    """(r10d) The tile's brush strokes made non-directional: in each octave of its 2-128 px band, every direction's
    amplitude brought down to the median direction's (never up), on the luminance; the colour follows by ratio. The worn
    tile's diagonal strokes drew parallel streaks across the floor at the play camera."""
    if k <= 0:
        return img
    h, w, _ = img.shape
    lum = img @ np.array([0.299, 0.587, 0.114])
    F = np.fft.fft2(lum)
    fy, fx = np.meshgrid(np.fft.fftfreq(h), np.fft.fftfreq(w), indexing="ij")
    rad = np.hypot(fx, fy)
    ang = np.mod(np.arctan2(fy, fx), np.pi)
    nb = 36
    ab = np.minimum((ang / np.pi * nb).astype(int), nb - 1)
    gain = np.ones_like(rad)
    for lo in (1 / 128, 1 / 64, 1 / 32, 1 / 16, 1 / 8, 1 / 4):
        ring = (rad >= lo) & (rad < 2 * lo)
        amp = np.array([np.abs(F[ring & (ab == b)]).mean() if (ring & (ab == b)).any() else 0.0 for b in range(nb)])
        amp = (np.roll(amp, 1) + 2 * amp + np.roll(amp, -1)) / 4.0
        med = np.median(amp)
        fac = np.clip(med / np.maximum(amp, 1e-9), 0.2, 1.0) ** k
        gain[ring] = fac[ab[ring]]
    nl = np.real(np.fft.ifft2(F * gain))
    return np.clip(img * (np.maximum(nl, 0.0) / np.maximum(lum, 1.0))[..., None], 0, 255)


def mouth(f, a, kind, warm=None):
    """(r10d) A hole painting's mouth (its lip's ellipse) as its centre and half sizes in fractions of the piece (cu, cv,
    ru, rv): the biggest dark mass (luminance blurred at 3% of the piece, under the 2nd percentile + 0.65 of the way to
    the median); for a pit its lit far inner wall stands above that throat, so the lip reaches a quarter further up."""
    h, w = a.shape
    if warm is not None:   # (den r18 P5) see MOUTH_WARM: the lip's ellipse is the bbox of the biggest cool region, as found
        wm = ndimage.gaussian_filter((f[..., 0] - f[..., 2]) / (f.sum(-1) + 1.0), 0.02 * max(w, h))
        cool = ndimage.binary_fill_holes((a > 0.5) & (wm < warm))
        lab, n = ndimage.label(cool)
        if n == 0:
            return [0.5, 0.5, 0.3, 0.3]
        ys, xs = np.nonzero(lab == 1 + int(np.argmax(ndimage.sum(cool, lab, range(1, n + 1)))))
        return [round((xs.min() + xs.max() + 1) / 2 / w, 4), round((ys.min() + ys.max() + 1) / 2 / h, 4),
                round((xs.max() + 1 - xs.min()) / 2 / w, 4), round((ys.max() + 1 - ys.min()) / 2 / h, 4)]
    lum = ndimage.gaussian_filter(f @ np.array([0.299, 0.587, 0.114]), 0.03 * max(w, h))
    inside = a > 0.5
    lo, med = np.percentile(lum[inside], 2), np.median(lum[inside])
    dark = inside & (lum < lo + 0.65 * (med - lo))
    lab, n = ndimage.label(dark)
    if n == 0:
        return [0.5, 0.5, 0.3, 0.3]
    big = 1 + int(np.argmax(ndimage.sum(dark, lab, range(1, n + 1))))
    ys, xs = np.nonzero(lab == big)
    cu, cv = (xs.min() + xs.max() + 1) / 2 / w, (ys.min() + ys.max() + 1) / 2 / h
    ru, rv = (xs.max() + 1 - xs.min()) / 2 / w, (ys.max() + 1 - ys.min()) / 2 / h
    if kind == "pit":
        cv, rv = cv - 0.125 * rv, 1.125 * rv
    return [round(cu, 4), round(cv, 4), round(1.08 * ru, 4), round(1.08 * rv, 4)]


def ingest():
    os.makedirs(SRC, exist_ok=True)
    open(os.path.join(SRC, ".gdignore"), "w").close()
    names = list(BANKS) + list(SHEETS) + FLOORS
    for n in names:
        if os.path.exists(os.path.join(SRC, n + ".png")) and len(sys.argv) < 3:
            continue   # (r10d: once; `ingest all` copies every source again)
        shutil.copy2(os.path.join(INPUTS, n + ".png"), os.path.join(SRC, n + ".png"))
    for t in ("PROMPTS.md", "PROVENANCE.txt"):
        shutil.copy2(os.path.join(INPUTS, t), os.path.join(SRC, t))
    print(f"ingest: {len(names)} paintings + PROMPTS.md, PROVENANCE.txt -> {SRC}")


def build():
    os.makedirs(OUT, exist_ok=True)
    meta = {"bank_ppm": BANK_PPM, "obj_ppm": OBJ_PPM, "banks": [], "sheets": [], "floor": {}}
    for name, kind in BANKS.items():
        f, a = key(load(name))
        x0, y0, x1, y1 = bbox(a)
        f, a = f[y0:y1, x0:x1], a[y0:y1, x0:x1]
        save_rgba(os.path.join(OUT, name + ".png"), f, a)
        write_import(os.path.join(OUT, name + ".png"))
        h, w = a.shape
        e = {"name": name, "kind": kind, "px": [w, h], "metres": [round(w / BANK_PPM, 3), round(h / BANK_PPM, 3)]}
        e.update({k: round(v, 4) for k, v in feet(kind, a).items()})
        meta["banks"].append(e)
        print(f"bank {name:6s} {kind:9s} {w}x{h} px = {w / BANK_PPM:.1f} x {h / BANK_PPM:.1f} m  feet {feet(kind, a)}")
    for name, (kind, widest) in SHEETS.items():
        f, a = key(load(name))
        ps, _ = pieces(a)
        wmax = max(p[2] - p[0] for p in ps)
        src_ppm = BANK_PPM if widest is None else wmax / widest
        k = 1.0 if widest is None else OBJ_PPM / src_ppm
        f, a = resample(f, a, k)
        ppm = src_ppm * k
        ps, lab = pieces(a, join=max(4, round(JOIN.get(name, 20) * k)))
        # each piece cut out by its own label (a neighbour's reach is keyed out) and shelf-packed with 8 px gutters
        cuts = []
        for (x0, y0, x1, y1, li) in ps:
            pa = a[y0:y1, x0:x1] * (lab[y0:y1, x0:x1] == li)
            cuts.append((f[y0:y1, x0:x1], pa))
        leafs = set()
        if kind == "fur":   # (den r16 W) a dry leaf drift is orange (R well over B), the fur grey-lilac: the fur's colour pulled to its grey
            for i, (cf, ca) in enumerate(cuts):
                w_ = ca > 0.5
                if w_.any() and (cf[..., 0][w_].mean() - cf[..., 2][w_].mean()) > 45:
                    leafs.add(i)
                    if name in LEAF_GRADE:
                        import den_rocks as dr
                        L_, A_, B_ = dr.to_oklab(cf)
                        g_ = LEAF_GRADE[name]
                        cuts[i] = (dr.from_oklab(L_ + g_["dl"], A_ * g_["c"], B_ * g_["c"]), ca)
                elif name in FUR_GRADE:
                    import den_rocks as dr
                    g_ = FUR_GRADE[name]
                    L_, A_, B_ = dr.to_oklab(cf)
                    L_ = np.clip(g_["l50"] + (L_ - np.median(L_[w_])) * g_["spread"], 0.05, 0.92)
                    L_ = L_ - g_.get("under", 0.0) * dr.smooth(0.35, 1.0, np.linspace(0.0, 1.0, L_.shape[0]))[:, None]
                    C_ = g_["c"] * dr.smooth(0.25, 0.5, L_)
                    hr = np.radians(g_["h"])
                    cuts[i] = (dr.from_oklab(L_, C_ * np.cos(hr), C_ * np.sin(hr)), ca)
                elif name in DESAT:
                    g = (cf @ np.array([0.299, 0.587, 0.114]))[..., None]
                    cuts[i] = (cf + (g - cf) * DESAT[name], ca)
        if name in LIT_KNEE:
            import den_rocks as dr
            kn = LIT_KNEE[name]
            for i, (cf, ca) in enumerate(cuts):
                L_, A_, B_ = dr.to_oklab(cf)
                over = np.maximum(L_ - kn["knee"], 0.0)
                ck = 1.0 + (kn["c"] - 1.0) * dr.smooth(kn["knee"], kn["knee"] + 0.15, L_)
                cuts[i] = (dr.from_oklab(L_ - over * (1.0 - kn["share"]), A_ * ck, B_ * ck), ca)
        if name in MIRROR:
            cuts += [(cf[:, ::-1].copy(), ca[:, ::-1].copy()) for cf, ca in cuts]
        W = max(512, max(c[1].shape[1] for c in cuts) + 16)
        order = sorted(range(len(cuts)), key=lambda i: -cuts[i][1].shape[0])
        place, x, y, shelf = {}, 8, 8, 0
        for i in order:
            ch, cw = cuts[i][1].shape
            if x + cw + 8 > W:
                x, y, shelf = 8, y + shelf + 8, 0
            place[i] = (x, y)
            x += cw + 8
            shelf = max(shelf, ch)
        H = y + shelf + 8
        fa, aa = np.zeros((H, W, 3)), np.zeros((H, W))
        for i, (cf, ca) in enumerate(cuts):
            px_, py_ = place[i]
            fa[py_:py_ + ca.shape[0], px_:px_ + ca.shape[1]] = cf
            aa[py_:py_ + ca.shape[0], px_:px_ + ca.shape[1]] = ca
        save_rgba(os.path.join(OUT, name + ".png"), fa, aa)
        write_import(os.path.join(OUT, name + ".png"))
        sh = {"name": name, "kind": kind, "px": [W, H], "ppm": round(ppm, 3), "pieces": []}
        for i, (cf, ca) in enumerate(cuts):
            px_, py_ = place[i]
            ch, cw = ca.shape
            # the foot: the lowest row with any solid stone/root/bone in the piece's middle half (its ground contact)
            cols = ca[:, cw // 4:3 * cw // 4] > 0.5
            rows = np.nonzero(cols.any(1))[0]
            fv = (rows.max() + 1) / ch if len(rows) else 1.0
            pe = {"rect": [px_, py_, cw, ch], "metres": [round(cw / ppm, 3), round(ch / ppm, 3)], "foot_v": round(fv, 4)}
            if kind in ("hollow", "pit"):
                pe["mouth"] = mouth(cf, ca, kind, MOUTH_WARM.get(name))
            if i in leafs:
                pe["leaf"] = True
            sh["pieces"].append(pe)
        h, w = H, W
        meta["sheets"].append(sh)
        print(f"sheet {name}: {kind}, {len(ps)} pieces, {w}x{h} px at {ppm:.1f} px/m (x{k:.2f})")
    rng = np.random.default_rng(1015)
    strip = []
    for name in FLOORS:
        im = Image.open(os.path.join(SRC, name + ".png")).convert("RGB").resize((FLOOR_PX, FLOOR_PX), Image.LANCZOS)
        img = destreak(seamless(np.asarray(im, dtype=np.float64), rng), DESTREAK.get(name, 0.0))
        lum = img @ np.array([0.299, 0.587, 0.114])
        hgt = ndimage.gaussian_filter(lum, 3.0, mode="wrap")
        lo, hi = np.percentile(hgt, [2, 98])
        hgt = np.clip((hgt - lo) / max(hi - lo, 1e-6), 0, 1)
        strip.append(np.dstack([img, hgt * 255.0]))
    arr = np.concatenate(strip, 0).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(os.path.join(OUT, "floor.png"), optimize=True)
    write_import(os.path.join(OUT, "floor.png"), layered=len(FLOORS))
    meta["floor"] = {"layers": FLOORS, "px": FLOOR_PX, "metres": FLOOR_M}
    with open(os.path.join(OUT, "set.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1)
    print(f"floor: {len(FLOORS)} tiles {FLOOR_PX} px / {FLOOR_M} m, seamless; set.json written")


def check():
    meta = json.load(open(os.path.join(OUT, "set.json"), encoding="utf-8"))
    bad = 0
    for e in meta["banks"] + meta["sheets"]:
        im = np.asarray(Image.open(os.path.join(OUT, e["name"] + ".png")), dtype=np.float64)
        rgb, a = im[..., :3], im[..., 3] / 255.0
        if list(im.shape[1::-1]) != e["px"]:
            print(f"FAIL {e['name']}: size {im.shape[1::-1]} != json {e['px']}"); bad += 1
        op = a > 0.5
        fringe = ((np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]) > 25) & op
        edge = op & ~ndimage.binary_erosion(op, iterations=2)
        fr, fe = fringe.mean() / max(op.mean(), 1e-9), (fringe & edge).sum() / max(edge.sum(), 1)
        ok = fr < 0.002 and fe < 0.01
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {e['name']:6s} magenta cast {fr * 100:.3f}% of opaque, {fe * 100:.3f}% of edge px")
        for p in e.get("pieces", []):
            x, y, w, h = p["rect"]
            if x < 0 or y < 0 or x + w > e["px"][0] or y + h > e["px"][1]:
                print(f"FAIL {e['name']} rect {p['rect']} outside"); bad += 1
            ring = np.concatenate([a[y, x:x + w], a[y + h - 1, x:x + w], a[y:y + h, x], a[y:y + h, x + w - 1]])
            if ring.max() > 0.5:
                print(f"FAIL {e['name']} rect {p['rect']} cuts its piece"); bad += 1
        for k in ("foot_v", "foot_u"):
            if k in e and not (0.0 <= e[k] <= 1.0):
                print(f"FAIL {e['name']} {k} {e[k]}"); bad += 1
    fl = np.asarray(Image.open(os.path.join(OUT, "floor.png")), dtype=np.float64)[..., :3]
    n = len(meta["floor"]["layers"])
    t = fl.shape[0] // n
    for i, name in enumerate(meta["floor"]["layers"]):
        img = fl[i * t:(i + 1) * t]
        inner = np.abs(np.diff(img, axis=0)).mean()
        wrap_v = np.abs(img[0] - img[-1]).mean()
        wrap_h = np.abs(img[:, 0] - img[:, -1]).mean()
        ok = max(wrap_v, wrap_h) < 1.6 * inner
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} floor {name}: wrap seams {wrap_v:.1f} / {wrap_h:.1f} against {inner:.1f} inside")
    print("check:", "PASS" if bad == 0 else f"{bad} FAIL")
    return bad == 0


# (den r19 S, R19 judge item 1: the lair pits inverted, the cells lit mid-green by the mip bleed and the cracks left dark) the
# painted pits' vein mask, from the painting's own lime lines (lime: G over max(R, cyan x B), linear, so the teal fungus caps
# are not veins): R the cores (the ridge a x lime + b x its white top-hat over k texels, after a sigma-"aa" blur, from lo to hi),
# G a narrow and B a wider glow (the cores blurred at sigma g and b texels, each over its value on a typical vein ("norm", the
# p-th percentile on the cores) and clipped at 1), so the light falls off within a few px of each vein and the plates between
# stay dark. den_set_soft's pit_lines reads it (DungeonDress.SetMat --den-pit-lines). Built from the built sheet (same pixels,
# same UVs): den_set.py veins (build runs it after the sheets)
VEINS = {"H3": {"cyan": 1.6, "aa": 0.7, "a": 0.5, "b_th": 1.0, "k": 11, "lo": 0.04, "hi": 0.12, "g": 4.0, "b": 11.0, "norm": 90}}


def veins():
    for name, v in VEINS.items():
        im = np.asarray(Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")).astype(np.float64) / 255.0
        s = im[..., :3]
        lin = np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)
        lime = np.clip(lin[..., 1] - np.maximum(lin[..., 0], v["cyan"] * lin[..., 2]), 0.0, None) * im[..., 3]
        lime = ndimage.gaussian_filter(lime, v["aa"])
        ridge = v["a"] * lime + v["b_th"] * (lime - ndimage.grey_opening(lime, size=(v["k"], v["k"])))
        t = np.clip((ridge - v["lo"]) / (v["hi"] - v["lo"]), 0.0, 1.0)
        core = t * t * (3.0 - 2.0 * t)
        chans = [core]
        for sg in (v["g"], v["b"]):
            gl = ndimage.gaussian_filter(core, sg)
            chans.append(np.clip(gl / max(np.percentile(gl[core > 0.5], v["norm"]), 1e-4), 0.0, 1.0))
        out = os.path.join(OUT, name + "_vein.png")
        Image.fromarray((np.dstack(chans) * 255.0).round().clip(0, 255).astype(np.uint8), "RGB").save(out, optimize=True)
        write_import(out)
        print(f"veins {name}: cores {100.0 * (core > 0.5).mean():.2f} % of the sheet, glow (g > .1) {100.0 * (chans[1] > 0.1).mean():.2f} %, wide {100.0 * (chans[2] > 0.1).mean():.2f} %")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "ingest":
        ingest()
    elif cmd == "build":
        build()
        veins()
    elif cmd == "leaves":   # (den r19 B) grade O6's leaf drifts (set.json "leaf") in place, as build does: den_set.py leaves
        import den_rocks as dr
        sh = [q for q in json.load(open(os.path.join(OUT, "set.json")))["sheets"] if q["name"] == "O6"][0]
        im = np.asarray(Image.open(os.path.join(OUT, "O6.png")).convert("RGBA")).astype(np.float64)
        for pe in sh["pieces"]:
            if not pe.get("leaf"):
                continue
            x_, y_, w_, h_ = pe["rect"]
            reg = im[y_:y_ + h_, x_:x_ + w_]
            L_, A_, B_ = dr.to_oklab(reg[..., :3])
            g_ = LEAF_GRADE["O6"]
            reg[..., :3] = dr.from_oklab(L_ + g_["dl"], A_ * g_["c"], B_ * g_["c"])
        Image.fromarray(im.round().clip(0, 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "O6.png"), optimize=True)
        print("O6 leaves graded")
    elif cmd == "bank":   # (den r15 R) rebuild one bank's png only (same cut as build): den_set.py bank B3R
        for name in sys.argv[2:]:
            f, a = key(load(name))
            x0, y0, x1, y1 = bbox(a)
            save_rgba(os.path.join(OUT, name + ".png"), f[y0:y1, x0:x1], a[y0:y1, x0:x1])
            print("bank", name, "rebuilt", a[y0:y1, x0:x1].shape)
    elif cmd == "veins":   # (den r19 S) H3's vein mask from the built H3.png (build runs it too): den_set.py veins
        veins()
    elif cmd == "check":
        sys.exit(0 if check() else 1)
    else:
        print(__doc__)
