"""The night's value plan as data with a check (L1 lead 11, rule R1: "the four-step night").

    python tools/look/night_values.py measure IMG [IMG ...] [--hud] [--mask x0,y0,x1,y1]
    python tools/look/night_values.py profile IMG --center X,Y [--aspect A] [--her PX] [--hud]
    python tools/look/night_values.py plan                       -> godot/data/look/night_plan.json (from the picked G1 targets)
    python tools/look/night_values.py check IMG [IMG ...] --rig arena_night|night_play [--hud] [--mask ...]   (exit 1 on a miss)
    python tools/look/night_values.py selftest

All in Oklab (tools/style/palette.py), on WORLD pixels: `--hud` cuts the game HUD's three blocks (HUD, fractions
of the frame); `--mask` cuts more boxes (fractions), for example a banner. Damage numbers and nameplates stay in.

Warm (fire) or cold (moon): a pixel is WARM when its chroma is at least 0.02 and its hue is in 300..360 or 0..150
(red-violet through red, orange, gold to the yellow-green of firelit leaves). Everything else is COLD: the blues,
the teal of moonlit leaves, and every near-neutral pixel (ink, dark neutrals). 300 is where the targets' hue
histogram stops following the pool and starts covering the whole frame (285-295 is the blue's own violet side).

  S1, S2  the cold pixels under their own 97th percentile (rims left out), split in two by the iterated mean
          threshold (twoval.py's split): each class's median L and C and its mean hue; `lit` = S2's share;
          `step` = S2 L - S1 L; `sep` = step / pooled within-class spread (one bell cut in half gives 2.2, so
          sep says "two clusters", step says "two levels": two near-equal navies fail on step and on S1/S2).
  S3      the cold top: median L of the brightest 2% of cold pixels (with its hue), and the share of cold above L 0.40.
  S4      warm share of the world; core = median of the brightest tenth of warm (its p95), mid = its p50 (the
          40-60% slice), edge = median of the darkest fifth (its p10); each with its hue.
  floor   the 1st percentile of the world's L (rule R3: nothing under 0.10 outside ink).
"""
import argparse, json, os, sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "style"))
from palette import oklab  # noqa: E402

PLAN = os.path.join(ROOT, "godot", "data", "look", "night_plan.json")
HUD = {"top_right": (0.79, 0.0, 1.0, 0.40), "bottom_bar": (0.23, 0.81, 0.77, 1.0), "timer": (0.80, 0.88, 1.0, 1.0)}
WARM_C, WARM_LO, WARM_HI, RIM_CUT, TOP, HI_L = 0.02, 300.0, 150.0, 0.97, 0.98, 0.40

# Which targets feed which rig; `skip` drops a poor witness from the bands that start with these prefixes.
RIGS = {
    "arena_night": [("09_shaw_horde", {}), ("10_pack_mother", {}),
                    ("12_hud", {"hud": True, "skip": ["s4", "lit", "step", "sep"],
                                "why": "painted with the HUD (masked); a gold telegraph lane runs through its pool (no witness for the fire) and its ground has no crown shade (no witness for the two-step split)"})],
    "night_play": [("05_ford_night", {}), ("06_warden", {})],
}
# band: (kind, least half-width). L and C ranges, hues (circular), shares and separations as minimums.
BANDS = {"s1_L": ("range", 0.03), "s1_C": ("range", 0.015), "s1_h": ("hue", 8), "s2_L": ("range", 0.03), "s2_C": ("range", 0.015),
         "s2_h": ("hue", 8), "lit": ("range", 0.10), "step": ("min", 0.85), "sep": ("min", 0.85),
         "s3_L": ("range", 0.03), "s3_h": ("hue", 10), "s3_share": ("min", 0.5),
         "s4_share": ("min", 0.33), "s4_core_L": ("range", 0.03), "s4_core_h": ("hue", 8), "s4_mid_L": ("range", 0.03),
         "s4_mid_h": ("hue", 8), "s4_edge_L": ("range", 0.03), "s4_edge_h": ("hue", 10), "floor": ("range", 0.03)}
# Lead 11's prose, to print beside what the targets say (the plan follows the targets).
DESIGN = {"s1_L": 0.16, "s1_h": 260, "s2_L": 0.27, "s2_h": 255, "s3_L": 0.50, "s4_core_L": 0.67, "s4_core_h": 60,
          "s4_mid_L": 0.48, "s4_edge_L": 0.28, "floor": 0.10}


def lab_of(path):
    x = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
    L, a, b = oklab(x)
    return L, a, b


def world(shape, hud, masks):
    h, w = shape
    m = np.ones(shape, bool)
    for x0, y0, x1, y1 in (list(HUD.values()) if hud else []) + list(masks or []):
        m[int(y0 * h):int(np.ceil(y1 * h)), int(x0 * w):int(np.ceil(x1 * w))] = False
    return m


def warm_of(a, b):
    C = np.hypot(a, b); H = np.degrees(np.arctan2(b, a)) % 360
    return (C >= WARM_C) & ((H >= WARM_LO) | (H < WARM_HI))


def hue(a, b):
    return float(np.degrees(np.arctan2(b.mean(), a.mean())) % 360) if a.size else float("nan")


def split(L):
    t = float(np.median(L))
    for _ in range(40):
        lo, hi = L[L <= t], L[L > t]
        if not lo.size or not hi.size: break
        n = (lo.mean() + hi.mean()) / 2
        if abs(n - t) < 1e-5: break
        t = n
    return t


def measure_lab(L, a, b, hud=False, masks=None):
    w = world(L.shape, hud, masks)
    L, a, b = L[w], a[w], b[w]
    C = np.hypot(a, b); warm = warm_of(a, b); cold = ~warm
    r = {"floor": float(np.percentile(L, 1)), "under10": float((L < 0.10).mean())}
    cl, ca, cb, cc = L[cold], a[cold], b[cold], C[cold]
    body = cl <= np.quantile(cl, RIM_CUT)
    t = split(cl[body]); lo, hi = body & (cl <= t), body & (cl > t)
    for k, m in (("s1", lo), ("s2", hi)):
        r[k + "_L"], r[k + "_C"], r[k + "_h"] = float(np.median(cl[m])), float(np.median(cc[m])), hue(ca[m], cb[m])
    r["lit"] = float(hi.sum() / body.sum()); r["step"] = r["s2_L"] - r["s1_L"]
    spread = np.sqrt((cl[lo].var() * lo.sum() + cl[hi].var() * hi.sum()) / body.sum())
    r["sep"] = float(r["step"] / max(spread, 1e-6)); r["split"] = t
    top = cl >= np.quantile(cl, TOP)
    r["s3_L"], r["s3_C"], r["s3_h"] = float(np.median(cl[top])), float(np.median(cc[top])), hue(ca[top], cb[top])
    r["s3_share"] = float((cl > HI_L).mean())
    r["s4_share"] = float(warm.mean())
    wl, wa, wb = L[warm], a[warm], b[warm]
    if wl.size >= 50:
        q = np.quantile(wl, [0.2, 0.4, 0.6, 0.9])
        for k, m in (("edge", wl <= q[0]), ("mid", (wl >= q[1]) & (wl <= q[2])), ("core", wl >= q[3])):
            r[f"s4_{k}_L"], r[f"s4_{k}_h"] = float(np.median(wl[m])), hue(wa[m], wb[m])
    else:
        for k in ("edge", "mid", "core"): r[f"s4_{k}_L"] = r[f"s4_{k}_h"] = float("nan")
    return r


def measure(path, hud=False, masks=None):
    return measure_lab(*lab_of(path), hud=hud, masks=masks)


def fmt(k, v):
    if v is None or v != v: return "-"
    return f"{v:.0f}" if k.endswith("_h") else f"{v * 100:.1f}%" if k in ("lit", "s3_share", "s4_share", "under10") else f"{v:.2f}" if k == "sep" else f"{v:.3f}"


ROWS = [("S1 shade", ["s1_L", "s1_C", "s1_h"]), ("S2 lit ground", ["s2_L", "s2_C", "s2_h", "lit", "step", "sep"]),
        ("S3 tops/rims", ["s3_L", "s3_C", "s3_h", "s3_share"]),
        ("S4 fire", ["s4_share", "s4_core_L", "s4_core_h", "s4_mid_L", "s4_mid_h", "s4_edge_L", "s4_edge_h"]),
        ("floor", ["floor", "under10"])]


def show(name, r):
    print(name)
    for title, keys in ROWS:
        print(f"  {title:14s} " + "  ".join(f"{k.split('_', 1)[-1] if k[0] == 's' and k[1].isdigit() else k} {fmt(k, r[k])}" for k in keys))


def in_band(kind, v, lo, hi):
    if v != v: return False
    if kind == "hue":
        return ((v - lo) % 360) <= ((hi - lo) % 360)
    return (lo is None or v >= lo - 1e-9) and (hi is None or v <= hi + 1e-9)


def band(kind, wid, vals):
    vals = [v for v in vals if v == v]
    if kind == "min":
        return [round(float(min(vals) * wid), 4), None]
    if kind == "hue":
        z = np.exp(1j * np.radians(vals)); mid = np.degrees(np.angle(z.mean())) % 360
        d = [((v - mid + 180) % 360) - 180 for v in vals]
        return [round(float((mid + min(min(d), -wid)) % 360), 1), round(float((mid + max(max(d), wid)) % 360), 1)]
    mid = (min(vals) + max(vals)) / 2
    return [round(float(max(0.0, min(min(vals), mid - wid))), 4), round(float(max(max(vals), mid + wid)), 4)]


def targets():
    import pairs
    t = json.load(open(os.path.join(pairs.L1, "a2", "targets.json"), encoding="utf-8"))["frames"]
    return {k: os.path.join(pairs.L1, v.split(" ")[0].replace("/", os.sep)) for k, v in t.items()}


def cmd_plan(_):
    tg = targets(); out = {"about": "The four-step night (L1 lead 11, rule R1), measured from the owner's picked G1 night targets by "
                           "tools/look/night_values.py plan; check a frame with `night_values.py check IMG --rig NAME --hud`. "
                           "Bands are [lo, hi] in Oklab (hues in degrees, a hue band may wrap through 360; null = no bound).",
                           "warm_cold": f"warm = chroma >= {WARM_C} and hue in {WARM_LO:.0f}..360 or 0..{WARM_HI:.0f}; cold = the rest (neutrals included)",
                           "rigs": {}}
    for rig, srcs in RIGS.items():
        ms = []
        for frame, o in srcs:
            r = measure(tg[frame], hud=o.get("hud", False)); ms.append((frame, o, r)); show(f"{rig}  T{frame}  ({os.path.basename(tg[frame])})", r)
        bands, left = {}, []
        for k, (kind, wid) in BANDS.items():
            use = [(f, r[k]) for f, o, r in ms if not any(k.startswith(p) for p in o.get("skip", []))]
            bands[k] = band(kind, wid, [v for _, v in use])
        for f, o, _ in ms:
            if o.get("skip"): left.append(f"{f} left out of {'/'.join(o['skip'])}*: {o['why']}")
        out["rigs"][rig] = {
            "from": f"Measured {', '.join(f for f, _, _ in ms)} (the G1 targets) on 9 Nov 2026; each band is the targets' spread, "
                    f"widened to the least half-width in night_values.py BANDS (L +/-0.03; shares and separations are minimums). " + " ".join(left),
            "sources": {f: {"file": os.path.relpath(tg[f], __import__('pairs').L1).replace(os.sep, "/"), "hud_masked": o.get("hud", False),
                            "measured": {k: (None if r[k] != r[k] else round(r[k], 4)) for k in BANDS}} for f, o, r in ms},
            "bands": bands}
        print(f"\n{rig} plan:"); print("  " + "\n  ".join(f"{k:10s} {b}   design {DESIGN.get(k, '-')}" for k, b in bands.items())); print()
    os.makedirs(os.path.dirname(PLAN), exist_ok=True)
    json.dump(out, open(PLAN, "w", encoding="utf-8", newline="\n"), indent=1); print(PLAN)


def check_one(name, r, bands):
    miss = 0; print(f"{name}\n  {'band':10s} {'measured':>9s}  {'plan':22s}")
    for k, (lo, hi) in bands.items():
        ok = in_band(BANDS[k][0], r[k], lo, hi); miss += not ok
        print(f"  {k:10s} {fmt(k, r[k]):>9s}  [{fmt(k, lo)}, {fmt(k, hi)}]".ljust(48) + ("PASS" if ok else "MISS"))
    print(f"  -> {'PASS' if not miss else f'{miss} MISS'}")
    return miss


def cmd_check(a):
    bands = json.load(open(PLAN, encoding="utf-8"))["rigs"][a.rig]["bands"]
    bad = sum(check_one(os.path.basename(p), measure(p, a.hud, a.mask), bands) > 0 for p in a.img)
    sys.exit(1 if bad else 0)


def cmd_measure(a):
    for p in a.img: show(os.path.basename(p), measure(p, a.hud, a.mask))


def cmd_profile(a):
    L, A, B = lab_of(a.img); h, w = L.shape
    cx, cy = a.center
    if cx <= 1 and cy <= 1: cx, cy = cx * w, cy * h
    wm = world(L.shape, a.hud, a.mask); warm = warm_of(A, B) & wm
    yy, xx = np.mgrid[0:h, 0:w]; dx, dy = xx - cx, yy - cy
    asp = a.aspect
    if asp is None:
        # The pool is a circle on the ground: its warm pixels' spread down the screen over their spread across it
        # (second moments about the center, inside 0.45 of the height so stray lamps stay out) is the foreshortening.
        near = warm & (np.hypot(dx, dy) < 0.45 * h)
        asp = float(np.sqrt((dy[near] ** 2).mean() / (dx[near] ** 2).mean()))
    r = np.hypot(dx, dy / asp) / h; C = np.hypot(A, B)
    print(f"{os.path.basename(a.img)} {w}x{h} center {cx:.0f},{cy:.0f} aspect {asp:.3f}" + (" (from the warm pixels' moments)" if a.aspect is None else ""))
    print("  r/H" + ("   r/her" if a.her else "") + "   warm%   L      C      h    | all L")
    for i in range(int(round(a.to / a.step))):
        m = (r >= i * a.step) & (r < (i + 1) * a.step) & wm; k = m & warm
        if not m.any(): continue
        s = f"  {(i + .5) * a.step:.3f}" + (f"  {(i + .5) * a.step * h / a.her:5.2f}" if a.her else "") + f"  {100 * k.sum() / m.sum():5.1f}"
        s += (f"   {np.median(L[k]):.3f}  {np.median(C[k]):.3f}  {hue(A[k], B[k]):3.0f}" if k.sum() >= 20 else "     -      -      - ")
        print(s + f"  | {np.median(L[m]):.3f}")


def unlab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3; m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    c = np.stack([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                  -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s], -1).clip(0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def synth(parts, n=120000, seed=7):
    """parts: (share, L, C, hue). An image of pixel populations (no layout: the measure has none either)."""
    rng = np.random.default_rng(seed); L, a, b = [], [], []
    for share, l, c, hh in parts:
        k = int(round(share * n)); L.append(l + rng.normal(0, 0.006, k))
        a.append(np.full(k, c * np.cos(np.radians(hh)))); b.append(np.full(k, c * np.sin(np.radians(hh))))
    rgb = np.round(unlab(np.concatenate(L), np.concatenate(a), np.concatenate(b))).reshape(1, -1, 3)
    return oklab(rgb.astype(np.float64))


def cmd_selftest(_):
    bands = json.load(open(PLAN, encoding="utf-8"))["rigs"]["arena_night"]["bands"]
    def mid(k):
        lo, hi = bands[k]
        if BANDS[k][0] == "hue": return (lo + ((hi - lo) % 360) / 2) % 360
        return lo * 1.3 if hi is None else (lo + hi) / 2
    ws = mid("s4_share"); lit = mid("lit"); s3 = max(0.035, mid("s3_share")); cold = 1 - ws - 0.015
    good = [(0.015, mid("floor"), 0.0, 0), (cold * (1 - s3) * (1 - lit), mid("s1_L"), mid("s1_C"), mid("s1_h")),
            (cold * (1 - s3) * lit, mid("s2_L"), mid("s2_C"), mid("s2_h")), (cold * s3, mid("s3_L"), 0.06, mid("s3_h")),
            (ws * 0.3, mid("s4_edge_L"), 0.05, mid("s4_edge_h")), (ws * 0.5, mid("s4_mid_L"), 0.10, mid("s4_mid_h")),
            (ws * 0.2, mid("s4_core_L"), 0.15, mid("s4_core_h"))]
    navy = [(0.015, 0.11, 0.0, 0), (0.49, 0.17, 0.035, 268), (0.47, 0.21, 0.045, 258), (0.025, 0.30, 0.06, 20)]
    g = check_one("synthetic four-step night (the plan's own middles)", measure_lab(*synth(good)), bands)
    n = check_one("synthetic two-navy night", measure_lab(*synth(navy)), bands)
    ok = g == 0 and n > 0
    print("selftest", "OK" if ok else "FAILED", f"(four-step {g} miss, two-navy {n} miss)"); sys.exit(0 if ok else 1)


def box(s):
    v = tuple(float(x) for x in s.split(","))
    if len(v) != 4: raise argparse.ArgumentTypeError("x0,y0,x1,y1 as fractions of the frame")
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    def common(p, many=True):
        p.add_argument("img", nargs="+" if many else None); p.add_argument("--hud", action="store_true")
        p.add_argument("--mask", type=box, action="append")
    p = sub.add_parser("measure"); common(p); p.set_defaults(f=cmd_measure)
    p = sub.add_parser("profile"); common(p, False); p.set_defaults(f=cmd_profile)
    p.add_argument("--center", required=True, type=lambda s: tuple(float(x) for x in s.split(",")), help="her feet: px, or fractions when both <= 1")
    p.add_argument("--aspect", type=float, help="ground foreshortening (screen-vertical over horizontal); default: from the warm pixels")
    p.add_argument("--her", type=float, help="her height in px: adds the radius in her heights")
    p.add_argument("--step", type=float, default=0.02); p.add_argument("--to", type=float, default=0.60)
    p = sub.add_parser("plan"); p.set_defaults(f=cmd_plan)
    p = sub.add_parser("check"); common(p); p.add_argument("--rig", required=True); p.set_defaults(f=cmd_check)
    p = sub.add_parser("selftest"); p.set_defaults(f=cmd_selftest)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
