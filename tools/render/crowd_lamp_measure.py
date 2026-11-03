"""Rendering 5: the night crowd under her lamp, five numbers off the frames.

    python tools/render/crowd_lamp_measure.py shoot TAG [--only a,b] [-- extra game args]
    python tools/render/crowd_lamp_measure.py measure BEFORE_TAG [AFTER_TAG ...]
    python tools/render/crowd_lamp_measure.py --help

`shoot` takes the Godot shots of one build (hold a `godot` turn from tools/turn.py first): the night arena with
250 risen at the play camera and her lamp, at her fourth swing (the `mid` frame), once per variant: the normal
frame, the ground with the crowd hidden (--dbg-hide crowd), her lamp off the crowd (--crowd-ember 0 --crowd-omni
off), the debug masks (--crowd-dbg-mode 3..6: near/mid/far/flat/dead, distance bands, the paint classes) and her
lamp's factor as a grey at four scales (mode 7), and the rim and the cool top switched off. The frames land in
godot/.shots/render5/TAG/. `measure` prints the five numbers of the r2 judge's list for each tag, each against its
target (the first tag is the "before": the energy ratios are against it).

The five (all on the same frame, 1:1 at the play camera; L is the cube root of linear luminance x 100, as
Rendering 4's bodyground.py read it; "ground" is the same pixels in the crowd-hidden frame):
  1. LAMP: f(h), the lamp's factor on the crowd at 2, 3.5, 6, 7 m from her, read off mode 7's grey through the display
     curve measured on the f=1 pixels (target 1 / 0.5 / 0.1 / 0); the lamp's energy on the crowd (the frame minus the
     lamp-off frame, linear luma, summed over the bodies) over the first tag's (target 0.65); standing bodies in the
     lamp's pool (within 4 m) over their ground, in L (target 0.7-0.9).
  2. FLAT, DEAD: mean body L over its ground, flat and dead bodies (target 0.6-0.8 or more).
  3. MATERIAL: skin over cloth, linear luma, on the bodies within 4 m of her (target >= 3); hair over cloth in her
     reach (target <= 0.5: hair keeps its own dark paint, cloth is lifted; few risen wear hair cards, so it may read nan);
     the warm rim: what switching it off removes, over the luma of the bodies in her reach (target ~0.15; the first
     tag has no rim switch, so it reads 0).
  4. TOP: moonlit bodies (more than 7.5 m from her) over their ground, L (target <= 0.8); what the cool top adds over
     the first tag's (target 0.5).
  5. NEAR: bodies within 1.5 m of her, mean L over her own (her body's pixels in the box round her) (target 0.75).
"""
import argparse
import os
import subprocess

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")
SHOTS = os.path.join(ROOT, "godot", ".shots")
OUT = os.path.join(SHOTS, "render5")
FRAME = "mid_1"
COMMON = ("--zone arena --time night --quick warden --give oathblade,judgement_disc --lab --horde 250 --dist 4 --spread 10 "
          "--seconds 5 --sex female --preset own --skin fair --eyes moss --hair braid --aa-beats").split()
VARIANTS = {
    "base": [],
    "ground": ["--dbg-hide", "crowd"],
    "lampoff": ["--crowd-ember", "0", "--crowd-omni", "off"],
    "omnionly": ["--crowd-ember", "0", "--crowd-omni", "on"],
    "m3": ["--crowd-dbg-mode", "3"],
    "m4": ["--crowd-dbg-mode", "4"],
    "m5": ["--crowd-dbg-mode", "5"],
    "m6": ["--crowd-dbg-mode", "6"],
    "g1": ["--crowd-dbg-mode", "7", "--crowd-dbg-s", "0.3"],
    "g2": ["--crowd-dbg-mode", "7", "--crowd-dbg-s", "0.15"],
    "g3": ["--crowd-dbg-mode", "7", "--crowd-dbg-s", "0.075"],
    "g4": ["--crowd-dbg-mode", "7", "--crowd-dbg-s", "0.0375"],
    "rimoff": ["--crowd-rim", "0"],
    "topoff": ["--crowd-top", "0"],
}


def shoot(tag, extra, only=None):
    d = os.path.join(OUT, tag)
    os.makedirs(d, exist_ok=True)
    for name, args in VARIANTS.items():
        if only and name not in only:
            continue
        out = os.path.join(d, name + ".png")
        if os.path.exists(out):
            continue
        shot = f"r5_{tag}_{name}"
        for f in os.listdir(SHOTS):
            if f.startswith(shot + "_") or f == shot + ".png":
                os.remove(os.path.join(SHOTS, f))
        cmd = [GODOT, "--path", os.path.join(ROOT, "godot"), "--fixed-fps", "60", "--resolution", "1920x1080", "--"] + COMMON + args + extra + ["--shot", shot]
        with open(os.path.join(d, name + ".log"), "w") as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
        src = os.path.join(SHOTS, f"{shot}_{FRAME}.png")
        if not os.path.exists(src):
            print(f"{tag}/{name}: no {FRAME} frame (see {name}.log)", flush=True)
            continue
        os.replace(src, out)
        print(f"{tag}/{name}: ok", flush=True)
        for f in os.listdir(SHOTS):
            if f.startswith(shot + "_") or f == shot + ".png":
                os.remove(os.path.join(SHOTS, f))


def lin(p):
    a = np.asarray(Image.open(p).convert("RGB"), float) / 255
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4), a


def lum(l):
    return l @ [0.2126, 0.7152, 0.0722]


def numbers(tag):
    """The measures of one tag, as a dict of name -> number."""
    d = os.path.join(OUT, tag)
    fr = {n: lin(os.path.join(d, n + ".png")) for n in VARIANTS if os.path.exists(os.path.join(d, n + ".png"))}
    Y = {n: lum(v[0]) for n, v in fr.items()}
    L = {n: np.cbrt(y) * 100 for n, y in Y.items()}
    g = L["ground"]
    gr = fr["ground"][1]

    def changed(m):
        # a pixel is the crowd's where the debug mask differs from the crowd-hidden frame
        return np.abs(fr[m][1] - gr).max(-1) * 255 > 20

    # What the tonemap makes of the mask's emissions (8-bit sRGB; measured on Rendering 5's frames: re-measure if the grade changes).
    REF = {"R": (164, 34, 4), "G": (104, 170, 56), "B": (2, 46, 142), "Y": (192, 176, 72), "M": (104, 120, 176)}

    def classes(m, names):
        # Each crowd pixel of a debug mask goes to its nearest reference colour (within 45), and is kept only if its four
        # neighbours are the same (a body's edge blends with what is behind it).
        a = fr[m][1] * 255
        crowdpx = changed(m)
        dist = np.stack([np.abs(a - np.array(REF[n])).sum(-1) for n in names], -1)
        k = dist.argmin(-1)
        ok = crowdpx & (dist.min(-1) < 60)
        out = []
        for i in range(len(names)):
            c = ok & (k == i)
            out.append(binary_erosion(c, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)))
        return out

    d3 = changed("m3")
    near5, far, mid, flat, dead = classes("m3", ["R", "G", "B", "Y", "M"])
    b4 = classes("m4", ["R", "G", "B"])   # < 1.5 m, 1.5-2.5 m, 3-4 m
    b5 = classes("m5", ["R", "G", "B"])   # 5.5-6.5, 6.5-7.5, > 7.5
    cloth, skin, hair = classes("m6", ["R", "G", "B"])
    body = d3 | b4[0] | b4[1] | b4[2] | b5[0] | b5[1] | b5[2]
    ratio = lambda m: float(L["base"][m].mean() / g[m].mean()) if m.sum() > 20 else float("nan")
    out = {"px": {"<1.5": int(b4[0].sum()), "1.5-2.5": int(b4[1].sum()), "3-4": int(b4[2].sum()), "5.5-6.5": int(b5[0].sum()),
                  "6.5-7.5": int(b5[1].sum()), ">7.5": int(b5[2].sum()), "flat": int(flat.sum()), "dead": int(dead.sum()),
                  "skin": int(skin.sum()), "cloth": int(cloth.sum()), "hair": int(hair.sum())}}
    # 1. the lamp's factor: mode 7's grey in g1..g4 is the factor x 0.3, 0.15, 0.075, 0.0375 through the display curve.
    # The pixels within 1.5 m of her (the factor is whole there) give the curve's points; invert by log-log interpolation.
    xs, ys = [], []
    for n, s in (("g4", 0.0375), ("g3", 0.075), ("g2", 0.15), ("g1", 0.3)):
        xs.append(s)
        ys.append(float(np.median(fr[n][0][b4[0], 1])) if b4[0].sum() > 20 else float("nan"))
    lx, ly = np.log(xs), np.log(ys)

    def f_of(m):
        v = np.median(fr["g1"][0][m, 1]) if m.sum() > 20 else float("nan")
        if not v > 0:
            return 0.0
        if np.log(v) < ly[0]:   # below the table: the power law of its two lowest points
            k = (lx[1] - lx[0]) / (ly[1] - ly[0])
            return float(np.exp(lx[0] + k * (np.log(v) - ly[0]))) / 0.3
        return float(np.exp(np.interp(np.log(v), ly, lx))) / 0.3
    out["f_2"] = f_of(b4[1])          # 1.5-2.5 m (centre 2)
    out["f_3.5"] = f_of(b4[2])        # 3-4 m
    out["f_6"] = f_of(b5[0])          # 5.5-6.5 m
    out["f_7"] = f_of(b5[1])          # 6.5-7.5 m
    lamp = Y["base"] - Y["lampoff"]
    out["lamp_energy"] = float(lamp[body].sum())
    pool = (b4[0] | b4[1] | b4[2]) & ~flat & ~dead
    out["pool_over_ground"] = ratio(pool)
    # 2.
    out["flat_over_ground"] = ratio(flat)
    out["dead_over_ground"] = ratio(dead)
    # 3.
    near4 = b4[0] | b4[1] | b4[2]
    sy = Y["base"][skin & near4].mean() if (skin & near4).sum() > 20 else float("nan")
    cy = Y["base"][cloth & near4].mean() if (cloth & near4).sum() > 20 else float("nan")
    out["skin_over_cloth"] = float(sy / cy)
    lit = near4 | b5[0]   # the bodies in her lamp's reach (within 6.5 m)
    hh, cc = hair & (lit | b5[1]), cloth & lit
    out["hair_over_cloth"] = float(Y["base"][hh].mean() / Y["base"][cc].mean()) if hh.sum() > 20 else float("nan")
    if "rimoff" in fr:
        dy = Y["base"] - Y["rimoff"]
        out["rim_added_over_body"] = float(dy[lit].sum() / Y["base"][lit].sum()) if lit.sum() else float("nan")
    # 4.
    out["moonlit_over_ground"] = ratio(b5[2] & ~flat & ~dead)
    if "topoff" in fr:
        out["top_added"] = float((Y["base"] - Y["topoff"])[body & ~dead & ~flat].sum())   # (the standing: the dead's own lift would scale it)
    # 5.
    hm = np.zeros_like(body)
    hm[470:600, 925:995] = True
    hm &= ~body
    out["her_L"] = float(L["base"][hm].mean())
    out["near1.5_L"] = float(L["base"][b4[0]].mean()) if b4[0].sum() > 20 else float("nan")
    out["near_over_her"] = out["near1.5_L"] / out["her_L"]
    return out


TARGETS = [
    ("f_2", "1", "lamp factor at 2 m"), ("f_3.5", "0.5", "at 3.5 m"), ("f_6", "0.1", "at 6 m"), ("f_7", "0", "at 7 m"),
    ("lamp_energy_rel", "0.65", "the lamp's energy on the crowd, over the first tag's"),
    ("pool_over_ground", "0.7-0.9", "standing bodies in the pool over the lit floor"),
    ("flat_over_ground", ">=0.6", "flat bodies over their ground"), ("dead_over_ground", ">=0.6", "dead bodies over their ground"),
    ("skin_over_cloth", ">=3", "skin over cloth, within 4 m"), ("hair_over_cloth", "<=0.5", "hair (not lifted) over cloth, in her reach"),
    ("rim_added_over_body", "~0.15", "the warm rim added, over the bodies' luma"),
    ("moonlit_over_ground", "<=0.8", "moonlit bodies over the moonlit floor"), ("top_added_rel", "0.5", "the cool top's addition, over the first tag's"),
    ("near_over_her", "0.75", "bodies within 1.5 m over her own L"),
]


def measure(tags):
    res = {t: numbers(t) for t in tags}
    first = res[tags[0]]
    for r in res.values():
        r["lamp_energy_rel"] = r["lamp_energy"] / first["lamp_energy"]
        if "top_added" in r and "top_added" in first:
            r["top_added_rel"] = r["top_added"] / first["top_added"]
    print(f"{'measure':22s} {'target':8s} " + " ".join(f"{t:>10s}" for t in tags))
    for k, tg, what in TARGETS:
        print(f"{k:22s} {tg:8s} " + " ".join(f"{r.get(k, float('nan')):10.3f}" for r in res.values()) + "   " + what)
    for t, r in res.items():
        print(t, "pixels", r["px"], "| her L %.1f, within 1.5 m L %.1f" % (r["her_L"], r["near1.5_L"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shoot", help="take all the variant shots of one build")
    s.add_argument("tag")
    s.add_argument("--only", help="comma list of variants")
    s.add_argument("extra", nargs="*", help="extra game args, after --")
    m = sub.add_parser("measure", help="print the numbers for one or more tags")
    m.add_argument("tags", nargs="+")
    a = ap.parse_args()
    if a.cmd == "shoot":
        shoot(a.tag, a.extra, a.only.split(",") if a.only else None)
    else:
        measure(a.tags)


if __name__ == "__main__":
    main()
