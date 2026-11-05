"""The FX and UI language, measured (L1 B6; docs/design/LOOK_BIBLE.md rules 12 and 13).

    python tools/style/fx_measure.py board            -> MB5's bands per school (the boxes in fx_language.json "from")
    python tools/style/fx_measure.py shot PNG X0,Y0,X1,Y1 [--bg X0,Y0,X1,Y1] [--sat-box ...]
                                                      -> a frame's effect measured the same way, plus its saturated share
    python tools/style/fx_measure.py ui               -> the UI swatches from targets 08, 11, 12 (ui_language.json "from")

An effect's pixels are those of its box that stand off the backdrop (Oklab C >= 0.06 or L >= the backdrop's L50 + 0.12);
the bright ones (L >= backdrop + 0.25) are split by k-means on L into the school's band count (edge, mid, core in rising
L), each band's L, C (medians) and h (circular mean) reported with its share of the effect's area; the rest of the
effect's pixels are its glow (the soft outer halo). Fully saturated: Oklab C >= 0.15 (MB5's fire bands sit at 0.17-0.18;
rule 4's night surfaces at 0.09-0.12).

    python tools/style/fx_measure.py build            -> writes fx_language.json "schools": MB5's measured schools (fire,
                                                      frost, holy) and the others derived from Palette.Of by the rules in
                                                      "derive" (keeps each band's calibrated "emit")
Nothing here is read by eye: re-run after moving a box.
"""
import json, math, os, sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
INPUTS = r"C:\Users\munch\Desktop\survivorsunchained_inputs"
FX = os.path.join(ROOT, "godot", "data", "look", "fx_language.json")
UI = os.path.join(ROOT, "godot", "data", "look", "ui_language.json")


def oklab(rgb):
    c = np.asarray(rgb, np.float64) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(lin @ m1.T)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    lab = lms @ m2.T
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    return L, np.hypot(a, b), (np.degrees(np.arctan2(b, a)) + 360) % 360, a, b


def lin_of(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b; m_ = L - 0.1055613458 * a - 0.0638541728 * b; s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]


def gamut_c(L, C, h):
    """C reduced (hue and L kept) until the color is in sRGB."""
    lo, hi = 0.0, C
    if all(-1e-4 <= v <= 1.0001 for v in lin_of(L, C, h)): return C
    for _ in range(30):
        mid = (lo + hi) / 2
        if all(-1e-4 <= v <= 1.0001 for v in lin_of(L, mid, h)): lo = mid
        else: hi = mid
    return lo


def to_srgb_hex(L, C, h):
    C = gamut_c(L, C, h)
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b; m_ = L - 0.1055613458 * a - 0.0638541728 * b; s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]
    out = []
    for v in rgb:
        v = min(1.0, max(0.0, v)); out.append(round(255 * (12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)))
    return "#%02x%02x%02x" % tuple(out)


def cmean(h, w=None):
    r = np.radians(h); w = np.ones_like(r) if w is None else w
    return float((np.degrees(math.atan2(float((np.sin(r) * w).sum()), float((np.cos(r) * w).sum()))) + 360) % 360)


def kmeans1(x, k, it=40):
    c = np.quantile(x, [(i + 0.5) / k for i in range(k)])
    for _ in range(it):
        lab = np.argmin(np.abs(x[:, None] - c[None, :]), 1)
        n = np.array([x[lab == i].mean() if (lab == i).any() else c[i] for i in range(k)])
        if np.allclose(n, c): break
        c = n
    return np.sort(c)


def saturated(rgb):
    return oklab(np.asarray(rgb).reshape(-1, 3))[1].reshape(np.asarray(rgb).shape[:-1]) >= 0.15


def bands(img, box, bg, k):
    a = np.asarray(img.convert("RGB"))
    crop = a[box[1]:box[3], box[0]:box[2]].reshape(-1, 3)
    L, C, h, _, _ = oklab(crop)
    bL = float(np.median(oklab(a[bg[1]:bg[3], bg[0]:bg[2]].reshape(-1, 3))[0]))
    fx = (C >= 0.06) | (L >= bL + 0.12)
    bright = fx & (L >= bL + 0.25) & (C >= 0.04)
    cs = kmeans1(L[bright], k)
    cuts = [(cs[i] + cs[i + 1]) / 2 for i in range(k - 1)]
    idx = np.digitize(L, cuts)
    out = dict(box=list(box), bg=list(bg), bg_L=round(bL, 3), n_fx=int(fx.sum()), thresholds_L=[round(float(c), 3) for c in cuts], bands=[])
    names = ["edge", "mid", "core"] if k == 3 else ["edge", "core"]
    for i in range(k):
        m = bright & (idx == i)
        Lm, Cm, hm = float(np.median(L[m])), float(np.median(C[m])), cmean(h[m], C[m])
        out["bands"].append(dict(name=names[i], L=round(Lm, 3), C=round(Cm, 3), h=round(hm, 1), share=round(float(m.sum() / fx.sum()), 3), hex=to_srgb_hex(Lm, Cm, hm)))
    g = fx & ~bright
    out["glow"] = dict(L=round(float(np.median(L[g])), 3), C=round(float(np.median(C[g])), 3), h=round(cmean(h[g], C[g]), 1), share=round(float(g.sum() / fx.sum()), 3),
                       hex=to_srgb_hex(float(np.median(L[g])), float(np.median(C[g])), cmean(h[g], C[g])))
    out["saturated_share_of_fx"] = round(float(saturated(crop)[fx].mean()), 4)
    return out


def box(s): return [int(v) for v in s.split(",")]


def board(quiet=False):
    d = json.load(open(FX, encoding="utf-8"))
    img = Image.open(os.path.join(INPUTS, d["board"]))
    res = {}
    for school, m in d["measure"].items():
        res[school] = bands(img, m["box"], m["bg"], m["k"])
    sat = saturated(np.asarray(img.convert("RGB")))
    res["board_saturated_share"] = round(float(sat.mean()), 4)
    if not quiet: print(json.dumps(res, indent=1))
    return res


def shot(args):
    img = Image.open(args[0]); b = box(args[1])
    bg = box(args[args.index("--bg") + 1]) if "--bg" in args else [b[0], max(0, b[1] - 60), b[2], b[1]]
    k = int(args[args.index("--k") + 1]) if "--k" in args else 3
    r = bands(img, b, bg, k)
    sat = saturated(np.asarray(img.convert("RGB")))
    inb = np.zeros_like(sat); inb[b[1]:b[3], b[0]:b[2]] = True
    r["frame_saturated_share"] = round(float(sat.mean()), 5)
    r["saturated_in_fx_box"] = round(float((sat & inb).sum() / max(1, sat.sum())), 3)
    print(json.dumps(r, indent=1))
    return r


def ui():
    d = json.load(open(UI, encoding="utf-8"))
    res = {}
    for name, m in d["measure"].items():
        img = np.asarray(Image.open(os.path.join(INPUTS, m["target"])).convert("RGB"))
        px = np.concatenate([img[b[1]:b[3], b[0]:b[2]].reshape(-1, 3) for b in m["boxes"]])
        L, C, h, _, _ = oklab(px)
        if "keep" in m:  # optional mask: L or C [lo, hi]
            k = np.ones(len(L), bool)
            for key, (lo, hi) in m["keep"].items():
                v = {"L": L, "C": C}[key]; k &= (v >= lo) & (v <= hi)
            L, C, h = L[k], C[k], h[k]
        Lm, Cm, hm = float(np.median(L)), float(np.median(C)), cmean(h, C + 1e-6)
        res[name] = dict(L=round(Lm, 3), C=round(Cm, 3), h=round(hm, 1), L10=round(float(np.quantile(L, 0.1)), 3), L90=round(float(np.quantile(L, 0.9)), 3),
                         n=int(len(L)), hex=to_srgb_hex(Lm, Cm, hm))
    print(json.dumps(res, indent=1))
    return res


# Palette.Of (godot/src/Fx/Palette.cs): core, glow, dim per school, sRGB before its HDR gain
PALETTE = {"physical": ("#fff6e4", "#ffd9a0", "#8a7a66"), "fire": ("#ffe29a", "#ff6a1a", "#3a2a24"), "frost": ("#f0fbff", "#6cc8ff", "#a8c8d8"),
           "storm": ("#ffffff", "#8ab4ff", "#5a6a9a"), "nature": ("#e8ffd0", "#7aff4a", "#3a5a2a"), "arcane": ("#e6b8ff", "#c870ff", "#4a3a6a"),
           "holy": ("#fffbe8", "#ffd46a", "#b8a070"), "shadow": ("#b48cff", "#8a4aff", "#1a1024")}


def lch(hx):
    L, C, h, _, _ = oklab([[int(hx[i:i + 2], 16) for i in (1, 3, 5)]])
    return float(L[0]), float(C[0]), float(h[0])


def hmix(a, b, t):
    d = ((b - a + 180) % 360) - 180
    return (a + d * t) % 360


def build():
    d = json.load(open(FX, encoding="utf-8"))
    m = board(True)
    fire = m["fire"]; dv = d["derive"]
    old = d.get("schools", {})
    # MB5's band L, averaged over its three schools (the derived schools' L); fire's chroma per band over Palette's glow C
    Lmean = [round(sum(m[s]["bands"][i]["L"] for s in ("fire", "frost", "holy")) / 3, 3) for i in range(3)]
    fgc = lch(PALETTE["fire"][1])[1]
    schools = {}
    for name, (core, glow, dim) in PALETTE.items():
        k = 2 if name in dv["two_bands"] else 3
        Lc, Cc, hc = lch(core); Lg, Cg, hg = lch(glow)
        if name in m:
            src = m[name]; bands = [dict(name=b["name"], L=b["L"], C=b["C"], h=b["h"], share=b["share"]) for b in src["bands"]]
            frm = f"MB5 {name} box {src['box']} (k-means on L, fx_measure.py board)"
            gl = dict(L=src["glow"]["L"], C=src["glow"]["C"], h=src["glow"]["h"])
        else:
            kc = Cg / fgc
            if Cc < 0.03: hc = hg
            cm = dv["c_max"]
            bands = [dict(name="edge", L=Lmean[0], C=fire["bands"][0]["C"] * kc, h=round(hmix(hg, hc, dv["edge_h"]), 1)),
                     dict(name="mid", L=Lmean[1], C=fire["bands"][1]["C"] * kc, h=round(hmix(hg, hc, dv["mid_h"]), 1)),
                     dict(name="core", L=Lmean[2], C=max(Cc, 0.25 * Cg) * dv["core_c"], h=round(hc, 1))]
            for b in bands: b["C"] = round(gamut_c(b["L"], min(cm, b["C"]), b["h"]), 3)
            fb = fire["bands"]; tot = sum(b["share"] for b in fb)
            for b, f in zip(bands, fb): b["share"] = f["share"]
            frm = "derived: Palette.Of(" + name + ") hues by derive's rules, MB5's band L and fire's chroma ratios"
            gl = dict(L=fire["glow"]["L"], C=round(fire["glow"]["C"] * kc, 3), h=round(hmix(hg, hc, dv["edge_h"]), 1))
        if k == 2:  # edge and core: the mid band folded into the edge
            e, c = bands[0], bands[2]; e["share"] = round(bands[0]["share"] + bands[1]["share"], 3); bands = [e, c]
        tot = sum(b["share"] for b in bands)
        t, acc = [], 0.0
        for b in bands:
            b["share_of_body"] = round(b["share"] / tot, 3)
            b["t"] = round(acc, 3); acc += b["share"] / tot
            b["hex"] = to_srgb_hex(b["L"], b["C"], b["h"])
            prev = next((ob for ob in old.get(name, {}).get("bands", []) if ob["name"] == b["name"]), None)
            b["emit"] = prev["emit"] if prev else [1.0, 1.0, 1.0]
            b.pop("share")
        gl["hex"] = to_srgb_hex(gl["L"], gl["C"], gl["h"])
        # sparks: MB5's fire sparks (measured), in each school's mid hue at its chroma ratio
        spk = d["sparks"]; mid = bands[1] if k == 3 else bands[0]
        sp_hex = to_srgb_hex(spk["L"], spk["C"], spk["h"]) if name == "fire" else to_srgb_hex(spk["L"], min(spk["C"], spk["C"] * mid["C"] / fire["bands"][1]["C"]), mid["h"])
        schools[name] = dict(**{"from": frm}, bands=bands, glow=dict(gl, **d["glow"]), sparks=dict(hex=sp_hex, **{k2: spk[k2] for k2 in ("count", "length", "aspect", "from")}))
        if name in old and "t_tuned" in old[name]: schools[name]["t_tuned"] = old[name]["t_tuned"]
    d["schools"] = schools
    d["board_mean_L"] = Lmean
    json.dump(d, open(FX, "w", encoding="utf-8"), indent=1)
    print("wrote", FX)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    {"board": lambda: board(), "build": lambda: build(), "shot": lambda: shot(a[1:]), "ui": lambda: ui()}[a[0]]()
