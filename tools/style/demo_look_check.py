"""The demo frame's look, checked (docs/design/LOOK_BIBLE.md "The demo frame: the den"; lane E, demo-look).

    python tools/style/demo_look_check.py targets [--overlay DIR]
        -> each class measured on the approved targets (boxes + Oklab keys in demo_look_targets.json "classes"):
           n, L p10/p50/p90, C p10/p50/p90, h (chroma-weighted), and whether the target's own median sits in its band
    python tools/style/demo_look_check.py frame PNG [PNG...] [--masks MANIFEST.json] [--full]
        -> each frame's whole-frame numbers (palette.py's, over the play crop y 8-80% unless --full) against
           "frame_bands", plus the classes the manifest names for that frame (same box + key format as the targets,
           or "boxes": a shape as the boxes inside it, no key; keyed by the PNG's file name) against "bands". Exit 1 when any number is outside its band.

A class passes when its medians (L50, C50, chroma-weighted h) are inside the band. Numbers are self-checks before a
judge, never a substitute for one (LOOK_BIBLE rule set, "A number is a self-check")."""
import json, os, sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from palette import oklab, stats  # noqa: E402

INPUTS = r"C:\Users\munch\Desktop\survivorsunchained_inputs"
SPEC = json.load(open(os.path.join(HERE, "demo_look_targets.json")))


def key(kd, L, C, H):
    m = np.ones(L.shape, bool)
    for nm, (lo, hi) in kd.items():
        v = {"L": L, "C": C, "h": H}[nm]
        m &= ((v >= lo) & (v <= hi)) if lo <= hi else ((v >= lo) | (v <= hi))
    return m


_cache = {}


def lab(path):
    if path not in _cache:
        x = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
        L, a, b = oklab(x)
        _cache[path] = (x, L, a, b, np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360)
    return _cache[path]


def measure(items, resolve, overlay=None):
    Ls, As, Bs, Cs = [], [], [], []
    for it in items:
        path = resolve(it["img"])
        x, L, a, b, C, H = lab(path)
        # a box, or a shape as boxes laid inside it ("boxes": no colour key needed, so a class can fail on its colour)
        m = np.zeros(L.shape, bool)
        for x0, y0, x1, y1 in it.get("boxes", [it.get("box")]): m[y0:y1, x0:x1] = True
        m &= key(it.get("key", {}), L, C, H)
        for ex in it.get("not", []): m &= ~key(ex, L, C, H)
        Ls.append(L[m]); As.append(a[m]); Bs.append(b[m]); Cs.append(C[m])
        if overlay is not None:
            o = overlay.setdefault(path, x.copy()); o[m] = o[m] * 0.3 + np.array([255, 0, 255]) * 0.7
    L, a, b, C = (np.concatenate(v) for v in (Ls, As, Bs, Cs))
    if not len(L): return None
    p = lambda v, q: float(np.percentile(v, q))
    return dict(n=int(len(L)), L10=p(L, 10), L50=p(L, 50), L90=p(L, 90), C10=p(C, 10), C50=p(C, 50), C90=p(C, 90),
                h=float(np.degrees(np.arctan2((b * C).sum(), (a * C).sum())) % 360))


def inband(v, lo_hi, hue=False):
    lo, hi = lo_hi
    if hue and lo > hi: return v >= lo or v <= hi
    return lo <= v <= hi


def judge_class(name, r):
    band = SPEC["bands"].get(name)
    if band is None or r is None: return True, ""
    bad = [k for k, v in (("L", r["L50"]), ("C", r["C50"]), ("h", r["h"])) if not inband(v, band[k], k == "h")]
    return not bad, ("" if not bad else "OUT " + ",".join(bad))


def row(name, r, verdict=""):
    if r is None: return f"{name:14s} (no px)"
    return (f"{name:14s} n{r['n']:7d}  L {r['L10']:.2f} {r['L50']:.2f} {r['L90']:.2f}  "
            f"C {r['C10']:.3f} {r['C50']:.3f} {r['C90']:.3f}  h {r['h']:5.0f}  {verdict}")


def targets(args):
    ov = {} if "--overlay" in args else None
    imgs = SPEC["images"]
    ok = True
    for name, items in SPEC["classes"].items():
        r = measure(items, lambda k: os.path.join(INPUTS, imgs[k]), ov)
        good, why = judge_class(name, r); ok &= good
        print(row(name, r, why))
    if ov is not None:
        d = args[args.index("--overlay") + 1]; os.makedirs(d, exist_ok=True)
        for p, o in ov.items():
            Image.fromarray(o.clip(0, 255).astype(np.uint8)).save(os.path.join(d, "mask_" + os.path.basename(p).rsplit(".", 1)[0] + ".png"))
    return ok


def frame(args):
    full = "--full" in args
    man = {}
    if "--masks" in args: man = json.load(open(args[args.index("--masks") + 1]))
    pngs = [a for a in args if a.lower().endswith((".png", ".jpg", ".webp")) and not a.startswith("--")]
    fb = SPEC["frame_bands"]; ok = True
    for p in pngs:
        r, _, im = stats(p, not full)
        r["black"] = float((oklab(np.asarray(im).astype(np.float64))[0] < 0.12).mean() * 100)
        ks = ("Lp50", "key", "midC", "shC", "shH", "warm", "cold", "black")
        bad = [k for k in ks if not inband(r[k], fb[k])]
        ok &= not bad
        print(f"{os.path.basename(p)}: " + "  ".join(f"{k} {r[k]:.3f}" if k in ("midC", "shC") else f"{k} {r[k]:.2f}"
                                                     for k in ks)
              + ("   OUT " + ",".join(bad) if bad else "   in band"))
        for name, items in man.get(os.path.basename(p), {}).items():
            cr = measure(items, lambda k: p)
            good, why = judge_class(name, cr); ok &= good
            print("   " + row(name, cr, why))
    return ok


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("targets", "frame"): print(__doc__); sys.exit(2)
    sys.exit(0 if (targets(a[1:]) if a[0] == "targets" else frame(a[1:])) else 1)
