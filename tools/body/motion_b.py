#!/usr/bin/env python3
"""Lane G motion probe (16 Nov): A | B in motion, from tools/body/gate/motion_b.sh's run (godot/.shots/motion_b/<A|B>/<cam>/).

    python tools/body/motion_b.py [--root DIR] [--cam play] [--mesh-cam play] [--strips] [--json OUT]

Per clip and per --clip-tour-shots frame k (t = k * len / N), from the pose ruler's full dump (P1PoseProbe, rows tagged clip/t):
  flex_l/r   elbow flexion (deg, 0 = straight): upper arm line vs forearm line
  clav_l/r   clavicle elevation (deg over horizontal, clavicle head to upper arm head); dclav = minus the body's own rest
  sh_l/r     shoulder top over the ground (mm): the highest posed vertex of the shoulder cap (rest vertices within 9 cm of
             the upper arm head, outside the neck); dsh = its change from the body's own rest (neck_01 is 126 mm lower on B's rig,
             so the neck joint is not a shared landmark)
  wr_l/r     wrist (hand joint) height over the ground (mm)
  sw_l/r     upper arm swing in her sagittal plane (deg from straight down, + forward)
  scr_l/r    the upper arm's on-screen angle from the screen vertical (deg, the play camera; + = toward screen right)
  fold_l/r   shoulder and armpit edges (rest vertices within 14 cm of the upper arm head) stretched over 2.5x rest; crush = under 0.4x
A and B are laid on each other by clip time. The A|B table: per clip and measure the worst |B-A| over the clip and its k.
--strips: per clip and camera, a 1:1 strip (crops around her, A over B, k = 0..N-1) in DIR/strips/.
Also B's and A's calf radii (knee, ankle: the farthest vertex from the calf's line within +-1 cm of the joint's height in rest)
and ankle height (foot joint over the sole), set beside lane A's SideCarry constants.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gl import Glb, edges  # noqa: E402
from posed_fit import m12, skin  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GLB = {"A": os.path.join(REPO, "godot/art/people/heroine.glb"), "B": os.path.join(REPO, "godot/art/people/body_p1/body.glb")}
BODY = "Heroine"


def rows(path):
    out = []
    for line in open(path):
        if '"clip"' not in line:
            continue
        r = json.loads(line)
        if "bones" in r and "skeleton" in r:
            out.append(r)
    return out


def ground(path):
    g = {}
    for line in open(path):
        if '"ground"' in line:
            r = json.loads(line)
            g[r["frame"]] = r["ground"]
    return g


def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))))))


class Body:
    def __init__(self, tag):
        self.tag = tag
        self.g = Glb(GLB[tag])
        self.sk = self.g.skeleton(0)
        m = self.g.mesh(BODY)
        self.T = m.T
        self.E = edges(m.T)
        P = m.P.astype(float)
        self.rest_len = np.linalg.norm(P[self.E[:, 0]] - P[self.E[:, 1]], axis=1)
        H = lambda n: self.sk.head(self.sk.index[n])
        neck = H("neck_01")
        self.rest = {n: H(n) for n in ("neck_01", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r")}
        self.cap, self.reg = {}, {}
        for s in "lr":
            u = H(f"upperarm_{s}")
            d = np.linalg.norm(P - u, axis=1)
            lat = np.abs(P[:, 0]) > abs(neck[0]) + 0.6 * abs(u[0] - neck[0])   # outside the neck (her x is left/right)
            self.cap[s] = np.where((d < 0.09) & lat)[0]
            inr = d < 0.14
            self.reg[s] = inr[self.E[:, 0]] & inr[self.E[:, 1]]
        self.P = P

    def rest_clav(self, s):
        v = self.rest[f"upperarm_{s}"] - self.rest[f"clavicle_{s}"]
        return math.degrees(math.asin(v[1] / np.linalg.norm(v)))

    def joints(self, r):
        X = m12(r["skeleton"])
        J = {}
        for n in ("neck_01", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r", "pelvis",
                  "thigh_l", "thigh_r"):
            J[n] = (X @ m12(r["bones"][n]))[:3, 3]
        return J

    def measure(self, r, gr, mesh=True):
        J = self.joints(r)
        out = {"t": r["t"], "frame": r["frame"]}
        # her forward: the hips' line (thigh_l - thigh_r) crossed with up
        hips = J["thigh_l"] - J["thigh_r"]
        fwd = np.cross(hips, [0, 1, 0]); fwd[1] = 0; fwd /= np.linalg.norm(fwd) + 1e-9
        # (sign: forward is where her neck leans over the pelvis on average; fixed per body below by the rest facing)
        cam = r.get("camera")
        V = None
        if mesh:
            V, _ = skin(self.g, BODY, r)
        for s in "lr":
            ua, la, ha, cl = J[f"upperarm_{s}"], J[f"lowerarm_{s}"], J[f"hand_{s}"], J[f"clavicle_{s}"]
            out[f"flex_{s}"] = ang(la - ua, ha - la)
            v = ua - cl
            out[f"clav_{s}"] = math.degrees(math.asin(v[1] / np.linalg.norm(v)))
            out[f"dclav_{s}"] = out[f"clav_{s}"] - self.rest_clav(s)
            out[f"wr_{s}"] = (ha[1] - gr) * 1000
            a = la - ua
            out[f"sw_{s}"] = math.degrees(math.atan2(float(np.dot(a, fwd)), float(-a[1])))
            if cam:
                C = m12(cam["x"]); Ci = np.linalg.inv(C)
                p0 = (Ci @ np.r_[ua, 1])[:3]; p1 = (Ci @ np.r_[la, 1])[:3]
                f = 0.5 * cam["size"][1] / math.tan(math.radians(cam["fov"]) / 2)
                s0 = np.array([p0[0] / -p0[2], p0[1] / -p0[2]]) * f; s1 = np.array([p1[0] / -p1[2], p1[1] / -p1[2]]) * f
                d = s1 - s0
                out[f"scr_{s}"] = math.degrees(math.atan2(d[0], -d[1]))
            if V is not None:
                # (neck_01 sits 126 mm lower on B's rig than on A's: the cap's top is measured over the ground instead, and as its
                # change from the body's own rest, scaled as the game scales her)
                sc = float(np.linalg.norm(m12(r["skeleton"])[:3, 0]))
                out[f"sh_{s}"] = (V[self.cap[s], 1].max() - gr) * 1000
                out[f"dsh_{s}"] = out[f"sh_{s}"] - self.P[self.cap[s], 1].max() * sc * 1000
                L = np.linalg.norm(V[self.E[:, 0]] - V[self.E[:, 1]], axis=1) / np.maximum(self.rest_len, 1e-6)
                m = self.reg[s]
                out[f"fold_{s}"] = int((L[m] > 2.5).sum())
                out[f"crush_{s}"] = int((L[m] < 0.4).sum())
        return out


def legs(b):
    """Calf radii at knee and ankle, ankle height over the sole (rest, m)."""
    sk, P = b.sk, b.P
    out = {}
    for s in "lr":
        k, a = sk.head(sk.index[f"calf_{s}"]), sk.head(sk.index[f"foot_{s}"])
        ax = (a - k) / np.linalg.norm(a - k)
        res = {}
        for nm, c in (("knee", k), ("ankle", a)):
            sel = np.abs(P[:, 1] - c[1]) < 0.01
            sel &= np.linalg.norm((P - c)[:, [0, 2]], axis=1) < 0.10
            sel &= np.sign(P[:, 0]) == np.sign(c[0])   # her own leg only
            d = P[sel] - k
            rad = np.linalg.norm(d - np.outer(d @ ax, ax), axis=1)
            res[nm] = (float(rad.max()), float(np.median(rad)))
        foot = np.linalg.norm(P - a, axis=1) < 0.25
        sole = P[foot, 1].min()
        out[s] = {"calf_knee_max": res["knee"][0], "calf_knee_med": res["knee"][1], "calf_ankle_max": res["ankle"][0],
                  "calf_ankle_med": res["ankle"][1], "ankle_h": float(a[1] - sole), "knee_h": float(k[1] - sole),
                  "ball_h": float(sk.head(sk.index[f"ball_{s}"])[1] - sole)}
    return out


def crop_strip(root, cam, clip, n, out):
    from PIL import Image
    tiles = []
    for tag in "AB":
        d = os.path.join(root, tag, cam)
        log = open(os.path.join(d, "run.log"), errors="ignore").read()
        row = []
        for k in range(n):
            nm = f"mb_{tag}_{cam}_{clip}_{k:02d}_1.png"
            p = os.path.join(d, nm)
            if not os.path.exists(p):
                row.append(None); continue
            i = log.find(nm); seg = log[i:i + 200]
            hx, hy = 960, 540
            if " her " in seg:
                w = seg.split(" her ")[1].split()
                hx, hy = int(float(w[0])), int(float(w[1]))
            im = Image.open(p)
            if cam == "close":
                box = (hx - 480, 0, hx + 480, 1080)
            else:
                box = (hx - 130, hy - 170, hx + 130, hy + 110)
            row.append(im.crop(box))
        tiles.append(row)
    w = max((t.width for r in tiles for t in r if t), default=0); h = max((t.height for r in tiles for t in r if t), default=0)
    if not w:
        return None
    S = Image.new("RGB", (w * n, h * 2), (40, 40, 40))
    for j, r in enumerate(tiles):
        for k, t in enumerate(r):
            if t:
                S.paste(t, (k * w, j * h))
    os.makedirs(out, exist_ok=True)
    f = os.path.join(out, f"{cam}_{clip}.png")
    S.save(f)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(REPO, "godot/.shots/motion_b"))
    ap.add_argument("--cam", default="play")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--strips", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    bodies = {t: Body(t) for t in "AB"}
    print("#### legs (rest, mm): calf radius at knee / ankle (max, median from the calf line), ankle and ball over the sole")
    print("lane A's SideCarry: CalfKnee 74, CalfAnkle 46, Clear 55, TipGround 30")
    L = {}
    for t, b in bodies.items():
        L[t] = legs(b)
        for s, v in L[t].items():
            print(f"{t} {s}: knee {v['calf_knee_max']*1000:.1f} / {v['calf_knee_med']*1000:.1f}  ankle {v['calf_ankle_max']*1000:.1f} / "
                  f"{v['calf_ankle_med']*1000:.1f}  ankle_h {v['ankle_h']*1000:.1f}  ball_h {v['ball_h']*1000:.1f}  knee_h {v['knee_h']*1000:.1f}")
    M = {}
    for t, b in bodies.items():
        d = os.path.join(a.root, t, a.cam)
        R = rows(os.path.join(d, "full.jsonl")); G = ground(os.path.join(d, "pose.jsonl"))
        by = {}
        for r in R:
            by.setdefault(r["clip"], []).append(b.measure(r, G.get(r["frame"], 0.0)))
        M[t] = by
    keys = ["flex_l", "flex_r", "dclav_l", "dclav_r", "clav_l", "clav_r", "dsh_l", "dsh_r", "sh_l", "sh_r", "wr_l", "wr_r", "sw_l", "sw_r", "scr_l", "scr_r",
            "fold_l", "fold_r", "crush_l", "crush_r"]
    thr = {k: (15 if k.split("_")[0] in ("sh", "dsh", "wr") else 5) for k in keys}
    table = {}
    for clip, ra in M["A"].items():
        rb = M["B"].get(clip)
        if not rb:
            print(f"\n## {clip}: not on B"); continue
        ln = max(x["t"] for x in ra) or 1
        print(f"\n## {clip} ({len(ra)} A rows, {len(rb)} B rows; len ~{ln:.2f} s)")
        print("k  " + " ".join(f"{k:>14s}" for k in keys[:16]) + "   fold/crush A | B (l,r)")
        for k in range(a.n):
            tk = k * ln / a.n
            x = min(ra, key=lambda q: abs(q["t"] - tk)); y = min(rb, key=lambda q: abs(q["t"] - tk))
            print(f"{k}  " + " ".join(f"{x[q]:6.0f}|{y[q]:<7.0f}" for q in keys[:16]) +
                  f"   {x['fold_l']},{x['fold_r']}/{x['crush_l']},{x['crush_r']} | {y['fold_l']},{y['fold_r']}/{y['crush_l']},{y['crush_r']}")
        worst = {}
        for q in keys:
            best = (0, None, None, None)
            for x in ra:
                if x["t"] < 0.02:
                    continue   # (the tour's first-pose frame: the clip's t=0 row can hold the clip before's last pose)
                y = min(rb, key=lambda z: abs(z["t"] - x["t"]))
                dlt = y[q] - x[q]
                if abs(dlt) > abs(best[0]):
                    best = (dlt, x["t"], x[q], y[q])
            rngA = (min(x[q] for x in ra), max(x[q] for x in ra)); rngB = (min(y[q] for y in rb), max(y[q] for y in rb))
            worst[q] = {"d": best[0], "t": best[1], "k": None if best[1] is None else round(best[1] / ln * a.n), "A": best[2], "B": best[3],
                        "rangeA": rngA, "rangeB": rngB, "flag": abs(best[0]) > thr[q]}
        table[clip] = worst
        print("worst B-A: " + "; ".join(f"{q} {w['d']:+.0f} @k{w['k']} (A {w['A']:.0f} B {w['B']:.0f}; range A {w['rangeA'][0]:.0f}..{w['rangeA'][1]:.0f} "
                                        f"B {w['rangeB'][0]:.0f}..{w['rangeB'][1]:.0f})" for q, w in worst.items() if w["flag"]))
    if a.strips:
        out = os.path.join(a.root, "strips")
        for cam in ("play", "side", "close"):
            for clip in M["A"]:
                f = crop_strip(a.root, cam, clip, a.n, out)
                if f:
                    print("strip", f)
    if a.json:
        json.dump({"legs": L, "table": table, "rows": M}, open(a.json, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
