"""Storybook 4 "flatten then re-carve": a ChatGPT figure source (fine scratchboard) flattened to big flat value masses,
then Krea img2img in p6's woodcut hand (the fine hatching in an init is what tells Krea "fine hatching").

    python tools/storybook/ink_recarve.py prep      # crop + flatten (f1 light, f2 strong) -> out/ink_rc/_init_*.png
    python tools/storybook/ink_recarve.py gen       # Krea img2img at 0.40/0.50/0.60 x 2 seeds (gpu turn)
    python tools/storybook/ink_recarve.py post      # p5: night post (_nc), p3: standard post; contact sheets
    python tools/storybook/ink_recarve.py campath <p5name> <p3name>
    python tools/storybook/ink_recarve.py dawn <p3name>    # dawn candidates registered on the night plate (gpu turn)

Flatten: area-downscale (the hatching averages to a tone), mean-shift (edge-preserving, region colour), median,
then Oklab-ish L quantized to 4-5 levels by quantile; the darkest level is one solid black mass (chroma 0); hue is
the region's mean-shifted a/b, so the blue fire, orange ember and slate cloak stay flat colour areas.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out", "ink_rc")
SRC = os.path.join(os.environ.get("SB4_GPT", r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained"
                                  r"\b8482b68-211d-4b86-99c7-1203c4f7e317\scratchpad\storybook4\chatgpt"))
PLATES = {  # name: (source, crop box in source px, gen size)
    "p5R1": (os.path.join(SRC, "out2", "p5_R1.png"), (0, 104, 1536, 920), (2048, 1088)),
    "p5A2": (os.path.join(SRC, "out", "p5_A2.png"), (0, 104, 1536, 920), (2048, 1088)),
    "p3N1": (os.path.join(SRC, "out2", "p3_N1.png"), (0, 6, 2051, 762), (2432, 896)),
}
# flatten strengths: (downscale factor, mean-shift spatial, colour radius, median k at gen px, quantile cuts)
FLAT = {"f1": (2, 6, 18, 5, (0.42, 0.66, 0.86, 0.96)),
        "f2": (3, 10, 30, 9, (0.50, 0.78, 0.94))}
DENOISE = (0.40, 0.50, 0.60)
SEEDS = (47, 202)
R2 = json.load(open(os.path.join(HERE, "ink_jobs", "r2.json"), encoding="utf-8"))
P5_PROMPT = json.load(open(os.path.join(HERE, "ink_jobs", "r5g_p5.json"), encoding="utf-8"))["jobs"][0]["prompt"]
P3_PROMPT = (
    "A shadow puppet theatre frieze in carved black ink. Winter night on a frozen field beside a rutted dirt road, low "
    "dark hills under a black sky carved in long sweeping gouge lines. Ember glints in the frosted soil like coals in "
    "ash, small bold orange marks. At left a crack runs through the frost glowing ember orange, and a dead hand claws up "
    "out of it. Center-left a dead man stands, gaunt, in a torn ragged tunic, arms slack, his face blank and slack, not "
    "a skull: ember orange light burns at his open mouth, his eye sockets and the wounds in his chest, like a lamp behind "
    "paper. Center-right an old Watch soldier with a gray beard, a long slate blue-gray wool cloak and tabard, a round "
    "wooden shield on his left arm and a small iron oil lamp hanging at his belt, lunges and drives one long spear "
    "through a second dead man; his breath smokes white in the cold. The speared dead man sags on the spear, head hung, "
    "no breath, and his light pours out of the wound and falls onto the frost as small glowing ember stones. At right a "
    "body lies fallen empty and dark on the frost. The dead never breathe smoke. The frost and field are carved in "
    "long gouge strokes, dim blue-gray; large masses of solid black. The only warm color is the orange ember light; "
    "everything else is black, slate and deep blue-black ink.")


def oklab(rgb):
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]], np.float32)
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]], np.float32)
    return np.cbrt(lin @ M1.T) @ M2.T


def from_oklab(lab):
    M2i = np.linalg.inv(np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                                  [0.0259040371, 0.7827717662, -0.8086757660]], np.float32))
    M1i = np.linalg.inv(np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                                  [0.0883024619, 0.2817188376, 0.6299787005]], np.float32))
    lin = np.clip((lab @ M2i.T) ** 3, 0, 1) @ M1i.T
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def flatten(src_rgb, strength):
    f, sp, sr, med, cuts = FLAT[strength]
    H, W = src_rgb.shape[:2]
    small = cv2.resize(src_rgb, (W // f, H // f), interpolation=cv2.INTER_AREA)
    ms = cv2.pyrMeanShiftFiltering(small, sp, sr, maxLevel=1)
    ms = cv2.pyrMeanShiftFiltering(ms, sp, sr, maxLevel=1)
    up = cv2.resize(ms, (W, H), interpolation=cv2.INTER_CUBIC)
    up = cv2.medianBlur(up, med)
    lab = oklab(up[..., ::-1].astype(np.float32) / 255)       # cv2 is BGR
    L = lab[..., 0]
    edges = np.quantile(L, cuts)
    lev = np.digitize(L, edges)
    lev = np.asarray(Image.fromarray(lev.astype(np.uint8)).filter(__import__("PIL.ImageFilter").ImageFilter.ModeFilter(med)))
    lev = lev.copy()
    # the darkest level as one solid mass: close its small holes, drop its specks
    blk = lev == 0
    blk = nd.binary_closing(blk, iterations=2)
    blk = nd.binary_opening(blk, iterations=1)
    lev[blk] = 0
    lev[(~blk) & (lev == 0)] = 1
    vals = [float(np.median(L[lev == k])) if (lev == k).any() else 0 for k in range(len(cuts) + 1)]
    vals[0] = 0.12
    out = np.zeros_like(lab)
    out[..., 0] = np.take(vals, lev)
    # region hue: the mean-shifted a/b, smoothed, kept at full strength where it is saturated (fire, ember), muted elsewhere
    ab = cv2.GaussianBlur(lab[..., 1:], (0, 0), 3)
    chroma = np.hypot(ab[..., 0], ab[..., 1])
    keep = np.clip((chroma - 0.02) / 0.06, 0.35, 1.0)[..., None]
    out[..., 1:] = ab * keep * (lev > 0)[..., None]
    rgb = from_oklab(out)
    return (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), lev


def prep():
    os.makedirs(OUT, exist_ok=True)
    for name, (src, box, (gw, gh)) in PLATES.items():
        im = Image.open(src).convert("RGB").crop(box).resize((gw, gh), Image.LANCZOS)
        raw = os.path.join(OUT, f"_init_{name}_f0.png")
        im.save(raw)
        bgr = np.asarray(im)[..., ::-1].copy()
        for s in FLAT:
            rgb, _ = flatten(bgr, s)
            Image.fromarray(rgb).save(os.path.join(OUT, f"_init_{name}_{s}.png"))
            print(name, s, flush=True)


def jobs():
    out = []
    for name in PLATES:
        prompt = P5_PROMPT if name.startswith("p5") else P3_PROMPT
        gw, gh = PLATES[name][2]
        for s in FLAT:
            for d in DENOISE:
                seeds = SEEDS if name != "p5A2" else SEEDS[:1]
                out.append({"name": f"{name}_{s}_d{round(d * 100)}", "w": gw, "h": gh, "seeds": list(seeds),
                            "prompt": prompt, "init": os.path.join(OUT, f"_init_{name}_{s}.png"), "denoise": d})
        if name != "p5A2":   # control: the unflattened source at 0.50
            out.append({"name": f"{name}_f0_d50", "w": gw, "h": gh, "seeds": list(SEEDS), "prompt": prompt,
                        "init": os.path.join(OUT, f"_init_{name}_f0.png"), "denoise": 0.5})
    return out


def gen():
    spec = {"_note": "Storybook 4 re-carve: ChatGPT sources flattened (ink_recarve.py FLAT) then Krea img2img in the r2 hand.",
            "prefix": R2["prefix"], "style": R2["style"], "jobs": jobs()}
    jp = os.path.join(HERE, "ink_jobs", "rc_p5p3.json")
    json.dump(spec, open(jp, "w", encoding="utf-8"), indent=1)
    import subprocess
    subprocess.check_call([sys.executable, os.path.join(HERE, "ink_gen.py"), jp, OUT])


def post():
    import ink_r5 as R
    R.R5 = OUT
    os.makedirs(os.path.join(OUT, "posted"), exist_ok=True)
    gens = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".png") and f.startswith("p"))
    p5 = [n for n in gens if n.startswith("p5")]
    p3 = [n for n in gens if n.startswith("p3")]
    R.post_night(p5)
    for n in p3:
        R.post_one(os.path.join(OUT, n + ".png"), os.path.join(OUT, "posted", n + ".png"), w=5400)
    for tag, names, suf in (("p5R1", [n for n in p5 if n.startswith("p5R1")], "_nc"),
                            ("p5A2", [n for n in p5 if n.startswith("p5A2")], "_nc"), ("p3N1", p3, "")):
        inits = [os.path.join(OUT, f"_init_{tag}_{s}.png") for s in ("f0",) + tuple(FLAT)]
        R.sheet_of(inits + [os.path.join(OUT, "posted", n + suf + ".png") for n in names],
                   os.path.join(OUT, f"{tag}_sheet_half.jpg"), cols=3, tw=900)


P3_KEYS = [(0.0, 1750, 1180, 1.12, "the crack + the hand"), (5.0, 2600, 1180, 1.12, "tracking: the standing dead"),
           (10.5, 3550, 1180, 1.12, "the spear, the stones"), (20.0, 3800, 900, 1.0, "tilt up (dawn)")]


def campath(p5, p3):
    import ink_r5 as R
    R.R5 = OUT
    img = Image.open(os.path.join(OUT, "posted", p5 + ".png")).convert("RGB")
    fx, fy = {"p5R1_f1_d40_s47_nc": (1910, 610)}.get(p5, R.P5_FORD.get(p5, (1830, 560)))
    keys = [(0.0, fx, fy + 40, 2.2, "open: water, cages, the fourth light"), (7.0, fx, fy + 60, 1.5, "end of the slow push"),
            (10.5, (fx + 1800) / 2, (fy + 1000) / 2 + 30, 1.2, "pulling back up the road"), (14.5, 1800, 950, 1.0, "the full wide")]
    sheets = []
    for n, im, ks in ((p5, img, keys), (p3, Image.open(os.path.join(OUT, "posted", p3 + ".png")).convert("RGB"), P3_KEYS)):
        fr = [R.frame(im, x, y, z, f"{n}  t={t:.1f}s  zoom {z}  {lab}") for t, x, y, z, lab in ks]
        sheet = Image.new("RGB", (1920 * 2 + 10, 1080 * 2 + 10), "#202020")
        for i, f in enumerate(fr):
            sheet.paste(f, ((i % 2) * 1930, (i // 2) * 1090))
        p = os.path.join(OUT, f"{n}_campath_half.jpg")
        sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS).save(p, quality=90)
        sheets.append(p)
        print(p)
    return sheets


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "prep":
        prep()
    elif a == "gen":
        gen()
    elif a == "post":
        post()
    elif a == "campath":
        campath(sys.argv[2], sys.argv[3])
    elif a == "dawn":
        import ink_recarve_dawn as D
        D.dawn(sys.argv[2])
