#!/usr/bin/env python3
"""The posed-fidelity ruler (P1 A shape): A's and B's skinned surfaces in the same game shot, from Godot's own numbers.

    python tools/body/posed_fit.py A.glb B_BUILD_DIR full_A.jsonl full_B.jsonl --out DIR --tag look [--shot-a a.png --shot-b b.png]
                                   [--crop x0,y0,x1,y1] [--px 1.0] [--pose-from REST_BUILD_DIR]

full_*.jsonl: --pose-probe-full (P1PoseProbe.cs): the skeleton's world, the camera, nonzero blend-shape weights, every bone's
skeleton-space pose at the shot's last frame. Each glb is skinned with its own weights and inverse binds (A's bone scales are in its
poses and binds; B's corrective keys are its active blend shapes). Both surfaces go to their OWN camera's space (the two cameras aim at
each body's eyes, so that is what the player compares).

Reports (twice: in the frame as the player sees it, then with B's torso registered rigidly onto A's over back and belly, which
separates shape and skinning from where the pose put the torso), per region on B's topology (stage/close.npz + out/topo/close.npz parts, each side): |d| p50, p95, max (mm) from B's vertices to A's
surface and the signed mean (+ = B outside A). Silhouette: neck to deltoid top line per side (mm, B - A, + = B higher), the armpit's apex
(mm), the far shoulder-to-breast notch depth. Writes DIR/clay_<tag>.png (A | B | B's distance to A: cool inside, warm outside, +-10 mm) and
with --shot-* DIR/check_<tag>.png (each shot with its surface's outline: the ruler checked against the game).

--pose-from: B's pose was probed on another build's rest: the probe's bones are carried to this build's rest by local rotation (parent's
frame), so a rest change can be read before the clips are re-baked (a preview; the re-baked clips are the truth).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ray  # noqa: E402
from gl import Glb  # noqa: E402
from surfdist import Surface  # noqa: E402

BODY = "Heroine"
HEAD = "HeroineHead"


def m12(a):
    """12 numbers (basis columns, origin) -> 4x4."""
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = a[0:3], a[3:6], a[6:9], a[9:12]
    return m


def read_probe(path, frame=None):
    rows = [json.loads(x) for x in open(path) if x.strip()]
    rows = [r for r in rows if "bones" in r and "camera" in r]
    r = rows[-1] if frame is None else min(rows, key=lambda q: abs(q["frame"] - frame))
    return r


def skin(glb, node, probe, bones=None):
    """(world positions, triangles) of a mesh in the probe's pose."""
    m = glb.mesh(node)
    P = m.P.astype(np.float64).copy()
    sh = probe["meshes"].get(node, {}).get("shapes", {})
    for k, v in sh.items():
        if k in m.targets:
            P += v * m.targets[k]["POSITION"]
    sk = glb.skeleton(0)
    G = np.stack([m12(probe["bones"][n]) if n in probe["bones"] else sk.rest[i] for i, n in enumerate(sk.names)]) if bones is None else bones
    M = G @ sk.ibm
    H = np.c_[P, np.ones(len(P))]
    out = np.zeros((len(P), 3))
    for k in range(m.J.shape[1]):
        out += m.W[:, k, None] * np.einsum("nij,nj->ni", M[m.J[:, k]], H)[:, :3]
    X = m12(probe["skeleton"])
    return (X[:3, :3] @ out.T).T + X[:3, 3], m.T


def _swing(u, v):
    """The shortest rotation (3x3) taking direction u onto v."""
    u, v = u / np.linalg.norm(u), v / np.linalg.norm(v)
    c, w = float(u @ v), np.cross(u, v)
    s = np.linalg.norm(w)
    if s < 1e-9:
        return np.eye(3)
    k = w / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K


def carry_pose(glb_from, glb_to, probe, lines=()):
    """The probe's pose (on glb_from's rest) on glb_to's rest: each bone's rotation relative to its parent kept, joints at the new rest's offsets.
    lines: bones (name -> its tail child) whose posed head->tail LINE is kept instead (swung onto the probe's): what a re-bake that lands the
    same lines does when the rest's bone angle changed (the clips are baked on the old rest)."""
    a, b = glb_from.skeleton(0), glb_to.skeleton(0)
    G0 = {n: m12(probe["bones"][n]) for n in a.names}
    out = np.zeros((len(b.names), 4, 4))
    for j, n in enumerate(b.names):
        p = b.parent[j]
        if n not in G0:
            out[j] = (out[p] if p >= 0 else np.eye(4)) @ (np.linalg.inv(b.rest[p]) @ b.rest[j] if p >= 0 else b.rest[j])
            continue
        ia = a.index[n]
        pa = a.parent[ia]
        la = (np.linalg.inv(G0[a.names[pa]]) @ G0[n]) if pa >= 0 else G0[n]
        ra = (np.linalg.inv(a.rest[pa]) @ a.rest[ia]) if pa >= 0 else a.rest[ia]
        rb = (np.linalg.inv(b.rest[p]) @ b.rest[j]) if p >= 0 else b.rest[j]
        lb = rb @ (np.linalg.inv(ra) @ la)      # the same rest-relative turn
        lb[:3, 3] = rb[:3, :3] @ (np.linalg.inv(ra[:3, :3]) @ la[:3, 3]) if pa >= 0 and np.linalg.norm(la[:3, 3] - ra[:3, 3]) > 1e-3 else rb[:3, 3]
        out[j] = (out[p] if p >= 0 else np.eye(4)) @ lb
        if n in dict(lines) and dict(lines)[n] in G0:
            c = dict(lines)[n]
            src = G0[c][:3, 3] - G0[n][:3, 3]
            tail = out[j] @ (np.linalg.inv(b.rest[j]) @ b.rest[b.index[c]])[:, 3]
            out[j][:3, :3] = _swing(tail[:3] - out[j][:3, 3], src) @ out[j][:3, :3]
    return out


class Cam:
    def __init__(self, c):
        self.X = m12(c["x"])
        self.inv = np.linalg.inv(self.X)
        self.w, self.h = c["size"]
        self.f = (self.h / 2) / math.tan(math.radians(c["fov"]) / 2)

    def space(self, P):
        return (self.inv[:3, :3] @ P.T).T + self.inv[:3, 3]

    def px(self, Pc):
        """Camera-space points to pixels."""
        return np.stack([self.w / 2 + self.f * Pc[:, 0] / -Pc[:, 2], self.h / 2 - self.f * Pc[:, 1] / -Pc[:, 2]], 1)


def vn(V, T):
    from gl import weld
    w = np.asarray(weld(V, 2e-5))
    Vw = np.zeros((w.max() + 1, 3))
    Vw[w] = V
    Tw = w[T]
    fn = np.cross(Vw[Tw[:, 1]] - Vw[Tw[:, 0]], Vw[Tw[:, 2]] - Vw[Tw[:, 0]])
    N = np.zeros_like(Vw)
    for k in range(3):
        np.add.at(N, Tw[:, k], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return N[w]


def raster(Vc, T, cam, crop, px=1.0, scal=None):
    """Clay through a camera-space mesh: (image [h,w] 0-1, mask, depth, sc): sc an optional per-vertex scalar's image."""
    x0, y0, x1, y1 = crop
    W, H = int((x1 - x0) * px), int((y1 - y0) * px)
    j, i = np.meshgrid((np.arange(W) + 0.5) / px + x0, (np.arange(H) + 0.5) / px + y0)
    d = np.stack([(j - cam.w / 2) / cam.f, -(i - cam.h / 2) / cam.f, -np.ones_like(j)], -1).reshape(-1, 3)
    n = np.linalg.norm(d, axis=1, keepdims=True)
    d = d / n
    s = ray.scene(Vc, T)
    pid, tf = ray.hits(s, np.zeros_like(d), d)
    m = pid >= 0
    N = vn(Vc, T)
    t = T[pid[m]]
    P = tf[m][:, None] * d[m]
    a, b, c = Vc[t[:, 0]], Vc[t[:, 1]], Vc[t[:, 2]]
    v0, v1, v2 = b - a, c - a, P - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-20)
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bu = 1 - bv - bw
    nn = N[t[:, 0]] * bu[:, None] + N[t[:, 1]] * bv[:, None] + N[t[:, 2]] * bw[:, None]
    nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
    vd = -d[m]
    nn = np.where(((nn * vd).sum(1))[:, None] < 0, -nn, nn)
    L = np.array([-0.45, 0.55, 0.62])
    L /= np.linalg.norm(L)
    img = np.ones(len(pid))
    img[m] = 0.16 + 0.66 * np.clip(nn @ L, 0, 1) + 0.10 * np.clip((nn * vd).sum(1), 0, 1)
    sc = None
    if scal is not None:
        sc = np.full(len(pid), np.nan)
        sc[m] = scal[t[:, 0]] * bu + scal[t[:, 1]] * bv + scal[t[:, 2]] * bw
    return img.reshape(H, W), m.reshape(H, W), sc.reshape(H, W) if sc is not None else None


def regions(build):
    """{name: boolean [n glb body vertices]} on B's topology."""
    s = np.load(os.path.join(build, "stage", "close.npz"), allow_pickle=True)
    z = np.load(os.path.join(HERE, "out", "topo", "close.npz"), allow_pickle=True)
    src = s["src"]
    V = s["V"]
    parts = list(map(str, z["parts"]))
    part = z["part"]
    ring = z["ring"]
    ip = {p: parts.index(p) for p in parts}
    x, y, zz = V[:, 0], V[:, 1], V[:, 2]
    br = part == ip["breast"]
    top = y[br].max()
    bot = y[br].min()
    cz = zz[(part == ip["trunk"]) & (np.abs(y - top) < 0.03)].mean()
    tr = part == ip["trunk"]
    # the breast's skirt: trunk within 35 mm of the breast part, above its bottom - 15 mm
    t2 = cKDTree(V[br])
    d, _ = t2.query(V, k=1)
    breasts = br | (tr & (d < 0.035) & (zz > cz))
    chest = (tr | br) & (zz > cz) & (y > top - 0.005) & ~breasts
    sh = part == ip["shoulder"]
    # the armpit's apex: the lowest shoulder vertices (each side), a 45 mm ball
    pit = np.zeros(len(V), bool)
    apex = {}
    for sgn, s_ in ((1, "l"), (-1, "r")):
        sel = sh & (x * sgn > 0)
        ids = np.where(sel)[0]
        ap = V[ids[np.argsort(y[ids])[:6]]].mean(0)
        apex[s_] = ap
        pit |= np.linalg.norm(V - ap, axis=1) < 0.045
    arm = part == ip["arm"]
    fa = (part == ip["elbow"]) | (part == ip["forearm"])
    back = tr & (zz < cz) & (y > 1.2)
    belly = tr & (y < bot) & (zz > cz)
    out = {"breasts": breasts, "chest": chest, "cap": sh & ~pit, "armpit": pit, "upper_arm": arm & ~pit, "forearm": fa, "back": back, "belly_ctl": belly, "neck": part == ip["neck"],
           "hand": part == ip["hand"]}       # (P1 R1 round 28: the hand and fingers, each side)
    # (P1 R1 round 30: the foot and the ankle (the shin's lowest 80 mm above the foot part), each side; the upper arm's
    # back half (each ring's points behind the ring's centre, -z at the rest), what a 3/4-back camera sees of it)
    ft = part == ip["foot"]
    out["foot"] = ft
    out["ankle"] = (part == ip["shin"]) & (y < y[ft].max() + 0.08)
    ab = np.zeros(len(V), bool)
    for sgn in (1, -1):
        for r_ in np.unique(ring[arm]):
            sel = arm & (ring == r_) & (x * sgn > 0)
            if sel.any():
                ab |= sel & (zz < zz[sel].mean())
    out["upper_arm_back"] = ab & ~pit
    res = {}
    for k, v in out.items():
        if k in ("neck", "belly_ctl", "back", "breasts", "chest"):
            res[k] = v[src]
            if k in ("breasts", "chest"):
                res[k + "_l"] = (v & (x > 0))[src]
                res[k + "_r"] = (v & (x < 0))[src]
        else:
            res[k + "_l"] = (v & (x > 0))[src]
            res[k + "_r"] = (v & (x < 0))[src]
    return res


def profile(mask, side, c_x, y_range):
    """The top of the mask per column on a side of c_x: {column: top row}."""
    out = {}
    h, w = mask.shape
    cols = range(c_x, w) if side > 0 else range(c_x, -1, -1)
    for j in cols:
        r = np.where(mask[y_range[0]:y_range[1], j])[0]
        if len(r) == 0:
            break
        out[j] = int(r[0]) + y_range[0]
    return out


def armpit_gap(mask, shoulder_px, cx, rows):
    """The arm/torso gap's apex near a shoulder: scanning rows downward from the shoulder, the first row where the column between the torso and
    the arm is empty: (row, col); None when no gap shows."""
    sgn = 1 if shoulder_px[0] > cx else -1
    for r in range(int(shoulder_px[1]), rows):
        row = mask[r]
        js = np.arange(cx, cx + sgn * 480, sgn)
        js = js[(js >= 0) & (js < mask.shape[1])]
        st = row[js]
        # torso run from the midline, then a hole, then the arm
        k = np.argmax(~st) if (~st).any() else -1
        if k <= 0:
            continue
        rest = st[k:]
        if rest.any():
            return r, int(js[k])
    return None


def notch(top_or_side, a, b):
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a_glb")
    ap.add_argument("b_build")
    ap.add_argument("a_probe")
    ap.add_argument("b_probe")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="pose")
    ap.add_argument("--shot-a")
    ap.add_argument("--shot-b")
    ap.add_argument("--crop", default="")
    ap.add_argument("--px", type=float, default=1.0)
    ap.add_argument("--pose-from")
    ap.add_argument("--no-image", action="store_true")
    ap.add_argument("--frame", type=int, default=None, help="the probes' row nearest this frame (default: the last; --pose-probe-every rows)")
    ap.add_argument("--carry-lines", action="store_true", help="with --pose-from: the arm chain's posed lines kept (a re-bake's preview)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    GA = Glb(a.a_glb)
    GB = Glb(os.path.join(a.b_build, "body.glb"))
    pa, pb = read_probe(a.a_probe, a.frame), read_probe(a.b_probe, a.frame)
    ca, cb = Cam(pa["camera"]), Cam(pb["camera"])
    bones = None
    if a.pose_from:
        lines = [(f"{x}_{s_}", f"{y}_{s_}") for s_ in "lr" for x, y in (("clavicle", "upperarm"), ("upperarm", "lowerarm"), ("lowerarm", "hand"))] if a.carry_lines else ()
        bones = carry_pose(Glb(os.path.join(a.pose_from, "body.glb")), GB, pb, lines)
    Va, Ta = skin(GA, BODY, pa)
    Vb, Tb = skin(GB, BODY, pb, bones)
    Ha, Tha = skin(GA, HEAD, pa)
    Hb, Thb = skin(GB, HEAD, pb, bones)
    Ca, Cb = ca.space(Va), cb.space(Vb)
    CHa, CHb = ca.space(Ha), cb.space(Hb)
    # the distance on A's body surface (+ = B outside A)
    S = Surface(Ca, Ta)
    q, n, tri, d = S.closest(Cb, k=16)
    sgn = np.sign(((Cb - q) * n).sum(1))
    # A's triangles wind outward: check on the mesh's volume
    vol = np.einsum("ij,ij->i", Ca[Ta[:, 0]], np.cross(Ca[Ta[:, 1]], Ca[Ta[:, 2]])).sum()
    sd = d * sgn * (1 if vol > 0 else -1)
    R = regions(a.b_build)
    print(f"#### {a.tag}: B to A (camera space, mm): region, n, p50, p95, max, signed mean")
    table = {}
    for k, v in R.items():
        dd = d[v] * 1e3
        table[k] = [int(v.sum()), float(np.percentile(dd, 50)), float(np.percentile(dd, 95)), float(dd.max()), float(sd[v].mean() * 1e3)]
        print(f"{k:14} {v.sum():6d} {table[k][1]:7.1f} {table[k][2]:7.1f} {table[k][3]:7.1f} {table[k][4]:+7.1f}")
    # the same after B's torso is registered to A's (rigid, closest points over back and belly, 6 rounds): what is shape and
    # skinning, not where the clip and the eye-aimed camera put her torso in the frame (that part is the pose's)
    reg = R["back"] | R["belly_ctl"]
    Cr = Cb.copy()
    for _ in range(6):
        qq, _, _, _ = S.closest(Cr[reg], k=16)
        pc, qc = Cr[reg].mean(0), qq.mean(0)
        U, _, Vt = np.linalg.svd((Cr[reg] - pc).T @ (qq - qc))
        Rm = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
        Cr = (Rm @ (Cr - pc).T).T + qc
    q2, n2, _, d2 = S.closest(Cr, k=16)
    sd2 = d2 * np.sign(((Cr - q2) * n2).sum(1)) * (1 if vol > 0 else -1)
    off = (Cr - Cb)[reg].mean(0) * 1e3
    print(f"#### {a.tag}: torso-registered (B moved {off.round(1).tolist()} mm, cam axes): region, p50, p95, max, signed mean")
    table_r = {}
    for k, v in R.items():
        dd = d2[v] * 1e3
        table_r[k] = [float(np.percentile(dd, 50)), float(np.percentile(dd, 95)), float(dd.max()), float(sd2[v].mean() * 1e3)]
        print(f"{k:14} {table_r[k][0]:7.1f} {table_r[k][1]:7.1f} {table_r[k][2]:7.1f} {table_r[k][3]:+7.1f}")
    # (P1 R1 round 30) the leg's end bones' posed directions, B against A, in the torso-registered frame (deg): the shin
    # (calf -> foot), the foot (foot -> ball), the toes (ball -> ball_leaf); and each foot's surface registered rigidly
    # onto A's foot (its own shape, not where the leg put it), p50/p95 mm
    def bdir(probe, cam, a_, b_, Rr=None):
        X = m12(probe["skeleton"])
        h = cam.space(((X @ m12(probe["bones"][a_]))[:3, 3])[None])[0]
        t = cam.space(((X @ m12(probe["bones"][b_]))[:3, 3])[None])[0]
        u = (t - h) / max(np.linalg.norm(t - h), 1e-12)
        return u if Rr is None else Rr @ u, np.linalg.norm(t - h)
    # the registration's whole rotation (the six rounds composed), from B's points
    Pb = Cb[reg] - Cb[reg].mean(0)
    Pr = Cr[reg] - Cr[reg].mean(0)
    U_, _, Vt_ = np.linalg.svd(Pb.T @ Pr)
    Rreg = Vt_.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt_.T @ U_.T))]) @ U_.T
    legs = {}
    for s_ in "lr":
        for lab, (b0, b1) in (("shin", ("calf", "foot")), ("foot", ("foot", "ball")), ("toes", ("ball", "ball_leaf"))):
            n0, n1 = f"{b0}_{s_}", f"{b1}_{s_}"
            if all(n in pa["bones"] and n in pb["bones"] for n in (n0, n1)):
                ua_, la_ = bdir(pa, ca, n0, n1)
                ub_, lb_ = bdir(pb, cb, n0, n1, Rreg)
                legs[f"{lab}_{s_}"] = {"deg": round(float(np.degrees(np.arccos(np.clip(ua_ @ ub_, -1, 1)))), 2),
                                       "pitch_A_B_deg": [round(float(np.degrees(np.arcsin(np.clip(u[1], -1, 1)))), 1) for u in (ua_, ub_)],
                                       "len_A_B_mm": [round(la_ * 1e3, 1), round(lb_ * 1e3, 1)]}
        fv = R["foot_" + s_]
        if fv.any():
            Cf = Cr.copy()
            for _ in range(8):
                qq, _, _, _ = S.closest(Cf[fv], k=16)
                pc, qc = Cf[fv].mean(0), qq.mean(0)
                U, _, Vt = np.linalg.svd((Cf[fv] - pc).T @ (qq - qc))
                Rm = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
                Cf = (Rm @ (Cf - pc).T).T + qc
            _, _, _, d3 = S.closest(Cf[fv], k=16)
            legs[f"foot_{s_}_registered_mm"] = [round(float(np.percentile(d3 * 1e3, 50)), 2), round(float(np.percentile(d3 * 1e3, 95)), 2)]
            P0, P1_ = Cr[fv] - Cr[fv].mean(0), Cf[fv] - Cf[fv].mean(0)
            U, _, Vt = np.linalg.svd(P0.T @ P1_)
            Rf = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
            legs[f"foot_{s_}_registration_deg_mm"] = [round(float(np.degrees(np.arccos(np.clip((np.trace(Rf) - 1) / 2, -1, 1)))), 2),
                                                     round(float(np.linalg.norm((Cf - Cr)[fv].mean(0)) * 1e3), 1)]
    print("legs", json.dumps(legs))
    # the silhouettes at the camera, each at its own (crop from the two bodies)
    both = np.r_[ca.px(Ca), cb.px(Cb), ca.px(CHa), cb.px(CHb)]
    lo, hi = np.floor(both.min(0)) - 30, np.ceil(both.max(0)) + 30
    if a.crop:
        crop = list(map(float, a.crop.split(",")))
    else:
        crop = [max(lo[0], 0), max(lo[1], 0), min(hi[0], ca.w), min(hi[1], ca.h)]
    VA, TA = np.r_[Ca, CHa], np.r_[Ta, Tha + len(Ca)]
    VB, TB = np.r_[Cb, CHb], np.r_[Tb, Thb + len(Cb)]
    ia, ma, _ = raster(VA, TA, ca, crop, a.px)
    sc = np.r_[sd, np.zeros(len(CHb))]
    ib, mb, sb = raster(VB, TB, cb, crop, a.px, sc)
    # scale: mm per px at the shoulders' depth (A)
    GAb = {n: m12(pa["bones"][n]) for n in pa["bones"]}
    Xa = m12(pa["skeleton"])
    def bone_px(cam, probe, name):
        G = m12(probe["bones"][name])
        X = m12(probe["skeleton"])
        p = (X @ G)[:3, 3]
        c = cam.space(p[None])
        return cam.px(c)[0], -c[0, 2]
    sil = {}
    for s_ in "lr":
        ua, za = bone_px(ca, pa, "upperarm_" + s_)
        ub, zb = bone_px(cb, pb, "upperarm_" + s_)
        na, _ = bone_px(ca, pa, "neck_01")
        ox, oy = crop[0], crop[1]
        mmpx = za / ca.f * 1e3 / a.px
        # columns: from the neck's side to the deltoid's outer edge, both masks' top line from the neck's midline
        cx = int((na[0] - ox) * a.px)
        sgn_ = 1 if ua[0] > na[0] else -1
        y_rng = (int(max(0, (min(ua[1], ub[1]) - 150 - oy) * a.px)), int((max(ua[1], ub[1]) + 90 - oy) * a.px))
        res = []
        pfa = profile(ma[:, :], sgn_, cx, y_rng)
        pfb = profile(mb[:, :], sgn_, cx, y_rng)
        cols = sorted(set(pfa) & set(pfb), key=lambda c: abs(c - cx))
        # only columns under the neck's edge: from the top line's drop (past the jaw/hair ...)
        start = int(40 * a.px)
        cols = [c for c in cols if abs(c - cx) >= start]
        diffs = [(abs(c - cx) * mmpx, (pfa[c] - pfb[c]) * mmpx) for c in cols]
        if diffs:
            dv = np.array(diffs)
            sil[s_] = {"from_mm": round(dv[0, 0]), "to_mm": round(dv[-1, 0]), "max_abs_mm": round(float(np.abs(dv[:, 1]).max()), 1), "mean_mm": round(float(dv[:, 1].mean()), 1),
                       "p": [round(float(x), 1) for x in dv[:: max(1, len(dv) // 12), 1]]}
            wa = abs(max(pfa, key=lambda c: abs(c - cx)) - cx) * mmpx
            wb = abs(max(pfb, key=lambda c: abs(c - cx)) - cx) * mmpx
            sil[s_]["half_span_A_B_mm"] = [round(wa), round(wb)]
        ga = armpit_gap(ma, ((ua[0] - ox) * a.px, (ua[1] - oy) * a.px), cx, ma.shape[0])
        gb = armpit_gap(mb, ((ub[0] - ox) * a.px, (ub[1] - oy) * a.px), cx, mb.shape[0])
        if ga and gb:
            sil[s_]["armpit_gap_rowcol_A_B"] = [ga, gb]
            sil[s_]["armpit_y_mm(+ B lower)"] = round((gb[0] - ga[0]) * mmpx, 1)
            sil[s_]["armpit_x_mm"] = round(abs(gb[1] - ga[1]) * mmpx, 1)
        else:
            sil[s_]["armpit_gap_rowcol_A_B"] = [ga, gb]
        print("silhouette", s_, json.dumps(sil[s_]))
    with open(os.path.join(a.out, f"fit_{a.tag}.json"), "w") as f:
        json.dump({"regions": table, "regions_torso_registered": table_r, "torso_shift_mm": off.tolist(), "silhouette": sil, "legs": legs, "crop": crop, "mm_per_px": float(mmpx)}, f, indent=1, default=float)
    if a.no_image:
        return
    heat = np.ones(sb.shape + (3,))
    t = np.clip(np.nan_to_num(sb) * 1e3 / 10.0, -1, 1)
    heat[..., 0] = np.where(t > 0, 1.0, 1.0 + t)
    heat[..., 1] = 1.0 - np.abs(t)
    heat[..., 2] = np.where(t < 0, 1.0, 1.0 - t)
    heat *= (0.35 + 0.65 * ib[..., None])
    heat[~mb] = 1.0
    row = np.concatenate([np.repeat(ia[..., None], 3, 2), np.repeat(ib[..., None], 3, 2), heat], 1)
    Image.fromarray((np.clip(row, 0, 1) * 255).astype(np.uint8)).save(os.path.join(a.out, f"clay_{a.tag}.png"))
    print("wrote", os.path.join(a.out, f"clay_{a.tag}.png"), "crop", crop, "mm/px", round(float(mmpx), 3))
    for shot, V, T, c, nm in ((a.shot_a, VA, TA, ca, "A"), (a.shot_b, VB, TB, cb, "B")):
        if not shot:
            continue
        im = np.asarray(Image.open(shot).convert("RGB")).astype(np.uint8).copy()
        _, m, _ = raster(V, T, c, [0, 0, c.w, c.h], 1.0)
        e = m ^ np.roll(m, 1, 0) | m ^ np.roll(m, 1, 1)
        im[e] = (0, 255, 0)
        x0, y0, x1, y1 = [int(v) for v in crop]
        Image.fromarray(im[y0:y1, x0:x1]).save(os.path.join(a.out, f"check_{a.tag}_{nm}.png"))


if __name__ == "__main__":
    main()
