"""Cut boom_sim.py's frames into a flipbook atlas (premultiplied RGBA, sRGB-encoded colour, as flipbook.gdshader and
flare_fb.gdshader read it), or preview them over a ground colour the way the game lays them over its ground.

    python tools/fxsim/pack.py atlas FRAMES_DIR OUT.png [--cols 8] [--cell 384] [--fps 24] [--first 1] [--last N]
    python tools/fxsim/pack.py preview FRAMES_DIR OUT.jpg [--every 4] [--cell 320] [--bg 0.05,0.05,0.06]
    python tools/fxsim/pack.py frames FRAMES_DIR OUT_PREFIX --at 4,10,24 [--cell 448]   (night | day, full size)
    [--tone "exp=1.2;knee=0.6"]  overrides the take's tone (FRAMES_DIR/take.json)

Frames are f_NNN.exr (scene-linear, premultiplied: boom_sim.py's default) or f_NNN.png (straight alpha, older takes).
The EXR's fire is tone-mapped here, hue kept: each pixel's colour scaled so its brightest channel rolls off softly
past `knee` toward 1 (orange stays orange, never clips to cream); `hot` lets the very hottest lean to yellow-white;
`amb` gives the smoke a dark warm grey of its own (premultiplied, so it scales with the smoke's opacity). Alpha is
raised to at least the colour (the game's shader clamps rgb to alpha).

The atlas is refused (exit 2) when any frame's light reaches its border: the square of the quad would show. The game
also fades everything past 0.88 of the quad's half-width (a circle), so light out there is reported as a warning.
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

TONE = dict(exp=1.0, knee=0.65, hot=0.0, sat=1.0, amb=(0.0, 0.0, 0.0))
GAIN, SMOKE = 1.25, 0.9  # the game's (FlareFx.Boom.cs): fire's colour times gain, smoke's alpha times SMOKE


def frames(d, first=1, last=None):
    fs = sorted(glob.glob(os.path.join(d, "f_[0-9][0-9][0-9].exr"))) or \
        sorted(glob.glob(os.path.join(d, "f_[0-9][0-9][0-9].png")))
    return [f for f in fs if int(os.path.basename(f)[2:5]) >= first and (last is None or int(os.path.basename(f)[2:5]) <= last)]


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def lin(x):
    return np.where(x <= 0.04045, x / 12.92, np.power((x + 0.055) / 1.055, 2.4))


def tone_of(d, av):
    t = dict(TONE)
    try:
        t.update(json.load(open(os.path.join(d, "take.json")))["settings"].get("tone", {}))
    except (OSError, KeyError, ValueError):
        pass
    for kv in filter(None, opt(av, "--tone", "").split(";")):
        k, v = kv.split("=")
        t[k] = tuple(float(x) for x in v.split(",")) if "," in v else float(v)
    t["amb"] = tuple(t["amb"]) if not isinstance(t["amb"], (int, float)) else (t["amb"],) * 3
    return t


def load(f, tone):
    """A frame as premultiplied, scene-linear float RGBA in [0, 1], tone-mapped, alpha >= colour."""
    if f.endswith(".exr"):
        import OpenEXR  # pip install OpenEXR (the ASWF's own bindings)
        with OpenEXR.File(f) as ex:
            a = np.array(ex.channels()["RGBA"].pixels, np.float32)
        a = np.nan_to_num(np.maximum(a, 0))
        rgb, al = a[..., :3] * tone["exp"], np.clip(a[..., 3:4], 0, 1)
        m = rgb.max(2, keepdims=True)
        k = tone["knee"]
        mm = np.where(m < k, m, k + (1 - k) * (1 - np.exp(-(m - k) / (1 - k))))
        # Hue kept, saturation deepened: each channel's ratio to the brightest raised to `sat` (a pale linear
        # (1, 0.8, 0.38) reads cream on screen; at sat 2 it is (1, 0.64, 0.14), a hot orange-yellow).
        out = mm * np.power(np.clip(rgb / np.maximum(m, 1e-6), 0, 1), tone.get("sat", 1.0))
        if tone["hot"] > 0:
            # Past the knee the hottest lean to a pale yellow, a little (never a flat cream field).
            w = np.clip((m - 1.0) / 2.0, 0, 1) * tone["hot"]
            out = out * (1 - w) + mm * np.array([1.0, 0.86, 0.62], np.float32) * w
        out = out + al * np.array(tone["amb"], np.float32)
        al = np.maximum(al, out.max(2, keepdims=True))
        return np.concatenate([np.clip(out, 0, 1), np.clip(al, 0, 1)], 2)
    im = Image.open(f)
    a = np.asarray(im, dtype=np.float32)
    a = a / (65535.0 if a.max() > 255.5 else 255.0)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.ones_like(a[..., :1])], 2)
    a[..., :3] = lin(a[..., :3]) * a[..., 3:4]
    return a


def resize(a, cell):
    if a.shape[0] == cell:
        return a
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(a[..., c], np.float32), "F").resize((cell, cell), Image.LANCZOS)) for c in range(4)], 2)


def edge_fade(a):
    h, w = a.shape[:2]
    y = np.minimum(np.arange(h), np.arange(h)[::-1]) / (h * 0.05)
    x = np.minimum(np.arange(w), np.arange(w)[::-1]) / (w * 0.05)
    m = np.clip(np.minimum(y[:, None], x[None, :]), 0, 1)
    return a * m[..., None]


TINT = (1.0, 1.0, 1.0)  # the game's fire_tint (flare_fb.gdshader); --tint 1,0.92,0.6 previews the old one


def over(a, bg):
    """The game's blend (premultiplied, its gain, tint and smoke factor, its clamp of colour to alpha) over a ground
    of display colour bg, back to display colour."""
    rgb = np.minimum(a[..., :3], a[..., 3:4]) * GAIN * np.array(TINT, np.float32)
    return srgb(rgb + lin(np.array(bg, np.float32)) * (1 - a[..., 3:4] * SMOKE))


def opt(argv, k, d, t=str):
    return t(argv[argv.index(k) + 1]) if k in argv else d


def main():
    global TINT, SMOKE
    mode, src, out = sys.argv[1:4]
    av = sys.argv[4:]
    TINT = tuple(float(v) for v in opt(av, "--tint", "1,1,1").split(","))
    SMOKE = opt(av, "--smoke", SMOKE, float)
    tone = tone_of(src, av)
    if mode == "atlas":
        cols, cell, fps = opt(av, "--cols", 8, int), opt(av, "--cell", 384, int), opt(av, "--fps", 24.0, float)
        fs = frames(src, opt(av, "--first", 1, int), opt(av, "--last", None, int))
        rows = (len(fs) + cols - 1) // cols
        atlas = np.zeros((rows * cell, cols * cell, 4), np.float32)
        bad, round_ = [], []
        for i, f in enumerate(fs):
            a = load(f, tone)
            b = 0.04
            h, w = a.shape[:2]
            ring = np.concatenate([a[: int(h * b)].reshape(-1, 4), a[-int(h * b):].reshape(-1, 4),
                                   a[:, : int(w * b)].reshape(-1, 4), a[:, -int(w * b):].reshape(-1, 4)])
            if ring[:, 3].max() > 0.06:
                bad.append((os.path.basename(f), float(ring[:, 3].max())))
            yy, xx = np.mgrid[0:h, 0:w]
            rr = np.hypot((xx + 0.5) / w * 2 - 1, (yy + 0.5) / h * 2 - 1)
            far = a[rr > 0.88][:, 3]
            if far.size and far.max() > 0.06:
                round_.append((os.path.basename(f), round(float(far.max()), 3)))
            a = resize(edge_fade(a), cell)
            r, c = divmod(i, cols)
            atlas[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = np.clip(a, 0, 1)
        if bad and "--force" not in av:
            print("REFUSED: light at the border in", bad[:6]); sys.exit(2)
        if round_:
            print("WARNING: light past the game's round fade (r > 0.88) in", round_[:8])
        enc = np.nan_to_num(np.concatenate([srgb(atlas[..., :3]), atlas[..., 3:4]], 2))
        Image.fromarray((enc * 255 + 0.5).astype(np.uint8), "RGBA").save(out)
        json.dump({"grid": cols, "rows": rows, "frames": len(fs), "fps": fps, "source": os.path.basename(src.rstrip("/\\")),
                   "tone": tone}, open(os.path.splitext(out)[0] + ".json", "w"))
        print("ATLAS", out, atlas.shape, len(fs), "frames", "border warnings" if bad else "")
    elif mode == "frames":
        cell = opt(av, "--cell", 448, int)
        night = [float(v) for v in opt(av, "--bg", "0.09,0.085,0.08").split(",")]
        day = [float(v) for v in opt(av, "--day", "0.42,0.38,0.32").split(",")]
        for n in [int(v) for v in opt(av, "--at", "4,10,24").split(",")]:
            f = [g for g in frames(src) if int(os.path.basename(g)[2:5]) == n][0]
            a = resize(load(f, tone), cell)
            sheet = np.concatenate([over(a, night), over(a, day)], 1)
            p = f"{out}_f{n:03d}.png"
            Image.fromarray((sheet * 255 + 0.5).astype(np.uint8)).save(p)
            # The judge's numbers: the cloud (alpha > 0.1), the share of it that is bright fire (the game's light
            # over 0.25 linear, about 0.54 on screen), how much of the dense cloud is opaque, and near-white pixels
            # (every channel over 0.8 on screen, over the night ground) as a share of the whole frame.
            al = a[..., 3]
            cloud = al > 0.1
            lit = np.minimum(a[..., :3], a[..., 3:4]) * GAIN * np.array(TINT, np.float32)
            flame = lit.max(2) > 0.25
            dark = cloud & (lit.max(2) < 0.06)
            white = over(a, night).min(2) > 0.8
            nc = max(int(cloud.sum()), 1)
            print("FRAME", p, "cloud %.1f%%" % (100 * cloud.mean()), "flame/cloud %.1f%%" % (100 * (flame & cloud).sum() / nc),
                  "dark/cloud %.1f%%" % (100 * dark.sum() / nc), "opaque(a>0.85)/cloud %.1f%%" % (100 * ((al > 0.85) & cloud).sum() / nc),
                  "near-white %.2f%%" % (100 * white.mean()))
    else:
        every, cell = opt(av, "--every", 4, int), opt(av, "--cell", 320, int)
        bg = [float(v) for v in opt(av, "--bg", "0.05,0.05,0.06").split(",")]
        fs = frames(src)[::every]
        tiles = [Image.fromarray((over(resize(load(f, tone), cell), bg) * 255).astype(np.uint8)) for f in fs]
        cols = min(len(tiles), 6)
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell, rows * cell))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * cell, (i // cols) * cell))
        sheet.save(out, quality=88)
        print("PREVIEW", out, sheet.size, [os.path.basename(f) for f in fs])


main()
