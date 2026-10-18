"""Stance numbers for built clips: pelvis height, knee bends, the pelvis's
fore-aft offset over the midpoint of her feet (ankle to ball, both feet), and
optional hand-over deltas between clips.

  python tools/scratch/anim38/stance.py [--body hero] clip ...
  python tools/scratch/anim38/stance.py --seam a:end b:start   (per-bone rot and hips pos delta)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ANIM = Path(__file__).resolve().parents[2] / "anim"
sys.path.insert(0, str(ANIM))
from rig import DATA, Skeleton, qangle, qinv, qmul  # noqa: E402

body = "heroine"
args = sys.argv[1:]
if "--body" in args:
    body = args[args.index("--body") + 1]
    args = [a for i, a in enumerate(args) if a != "--body" and args[i - 1] != "--body"]
sk = Skeleton.load(DATA / ("hero_skeleton.json" if body == "hero" else "heroine_skeleton.json"))
OUT = ANIM / "out" / ("hero" if body == "hero" else "clips")


def load(name):
    d = json.loads((OUT / f"{name}.json").read_text())
    T = len(next(t for t in d["tracks"])["keys"])
    rot = np.tile(sk.rest_rot, (T, 1, 1))
    pos = np.tile(sk.rest_pos, (T, 1, 1))
    for t in d["tracks"]:
        j = sk.i(t["bone"])
        (rot if t["type"] == "rot" else pos)[:, j] = np.array(t["keys"])
    return rot, pos


def numbers(name):
    rot, pos = load(name)
    g, p = sk.fk(rot, pos)
    pel = p[:, sk.i("pelvis")]
    out = {"pelvis_y": pel[:, 1]}
    mids, fwds = [], []
    for s in "lr":
        a, b, c = p[:, sk.i(f"thigh_{s}")], p[:, sk.i(f"calf_{s}")], p[:, sk.i(f"foot_{s}")]
        u, v = b - a, c - b
        cos = np.sum(u * v, 1) / np.linalg.norm(u, axis=1) / np.linalg.norm(v, axis=1)
        out[f"knee_{s}"] = np.degrees(np.arccos(np.clip(cos, -1, 1)))
        ball = p[:, sk.i(f"ball_{s}")]
        mids.append((c + ball) / 2)
        f = ball - c
        f[:, 1] = 0
        fwds.append(f)
    mid = (mids[0] + mids[1]) / 2
    fwd = fwds[0] + fwds[1]
    fwd /= np.linalg.norm(fwd, axis=1, keepdims=True)
    out["pel_fwd"] = np.sum((pel - mid) * fwd, 1)
    tr = p[:, sk.i("neck_01")] - pel
    out["trunk"] = np.degrees(np.arctan2(np.sum(tr * fwd, 1), tr[:, 1]))
    from rig import qrot
    gr, _ = sk.rest_globals()
    hj = sk.i("Head")
    hd = qrot(qmul(g[:, hj], qinv(gr[0, hj])), [0, 1, 0])
    out["neck"] = np.degrees(np.arctan2(np.sum(hd * fwd, 1), hd[:, 1]))
    # ankle-to-ball span, for scale
    out["foot_len"] = np.linalg.norm(fwds[0], axis=1)
    return out


def seam(a, b):
    na, wa = a.split(":")
    nb, wb = b.split(":")
    ra, pa = load(na)
    rb, pb = load(nb)
    ia = -1 if wa == "end" else (0 if wa == "start" else int(wa))
    ib = 0 if wb == "start" else (-1 if wb == "end" else int(wb))
    pel = sk.i("pelvis")
    rd = [((qangle(qmul(qinv(ra[ia, j]), rb[ib, j]))), sk.names[j]) for j in range(len(sk))]
    rd.sort(reverse=True)
    pd = np.linalg.norm(pa[ia, pel] - pb[ib, pel])
    # the clip's own frame-to-frame motion near the seam
    fa = max((qangle(qmul(qinv(ra[ia - 1, j]), ra[ia, j]))) for j in range(len(sk)))
    fb = max((qangle(qmul(qinv(rb[ib, j]), rb[ib + 1, j]))) for j in range(len(sk)))
    pfa = np.linalg.norm(pa[ia, pel] - pa[ia - 1, pel])
    print(f"{a} -> {b}: worst rot {rd[0][0]:.2f} deg ({rd[0][1]}), next {rd[1][0]:.2f} ({rd[1][1]}), "
          f"hips pos {pd * 100:.2f} cm | own step: rot {fa:.2f}/{fb:.2f} deg, hips {pfa * 100:.2f} cm")


if args and args[0] == "--seam":
    for i in range(1, len(args), 2):
        seam(args[i], args[i + 1])
elif args and args[0] == "--ends":
    for n in args[1:]:
        o = numbers(n)
        for w, i in (("start", 0), ("end", -1)):
            print(f"{n:22s} {w:5s} " + "  ".join(f"{k} {o[k][i]:.3f}" for k in ("pelvis_y", "knee_l", "knee_r", "pel_fwd", "trunk", "neck")))
else:
    for n in args:
        o = numbers(n)
        f = lambda k: f"{o[k].mean():.3f} [{o[k].min():.3f}..{o[k].max():.3f}]"
        print(f"{n:24s} pelvis_y {f('pelvis_y')}  knee_l {o['knee_l'].mean():.1f} [{o['knee_l'].min():.1f}..{o['knee_l'].max():.1f}]"
              f"  knee_r {o['knee_r'].mean():.1f} [{o['knee_r'].min():.1f}..{o['knee_r'].max():.1f}]  pel_fwd {f('pel_fwd')}  trunk {o['trunk'].mean():.1f} neck {o['neck'].mean():.1f}")
