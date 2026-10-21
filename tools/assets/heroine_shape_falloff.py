"""A face shape's offsets made smooth over her temples and forehead, in her exported glb (heroine.glb), in place.

Sunborn's face key (face_sunborn, from heroine_face/targets/portrait-sunborn.target) carries a narrow relief round
the front of her face: her forehead pushed forward in the middle (+1.6 mm), a hollow at each of its upper corners
(-4.8 mm, about 25 mm across) and a rim just outside it (+2.2 mm, 6 mm from the hollow's floor), following the edge
of the face's front from the forehead's top corner down to brow level and on down the side of the face. At the Look
it drew a thin pale curved line at each temple, the outline of a mask (max judge, Face lead 32, 20 October 2026).
No paint, shader or tone held it: it was the shape.

This takes the key's fine relief (what a heat diffusion of the offsets over the head, ITER steps, takes out: a few
mm and under) away inside a soft mask: all her forehead from just above her brows (Y0, eased over Y_EASE) up to the
hairline (eased out by HAIR_Y), and a band along the edge of her face's front (LINE, full within R0, gone by R1)
down to her cheekbone; never her eyes or brows (an ellipse round each, eased), her ears, or the back of her head.
Her broad shape (the forehead's lean, the temples' width) is kept: only the relief smaller than the diffusion's
reach goes. The key's normals are moved by what the new shape turns them (area-weighted normals of the shaped head,
before and after), so the exporter's own normals stay everywhere the shape did not move.

    python tools/assets/heroine_shape_falloff.py [face ...]            (no faces: FIX; writes heroine.glb)
    python tools/assets/heroine_shape_falloff.py --measure [face ...]  (no faces: all nine; nothing written)
    python tools/assets/heroine_shape_falloff.py --glb IN.glb [--out OUT.glb] ...

--measure gives, per face and side, the relief the mask would take out (mm, max and 95th percentile inside it) and
how far each point would move: a face like Sunborn stands out against Doe (passed at the Look).

Idempotent: each face done is named in her head mesh's extras (shape_falloff), and is left on a second run.
The chain: after heroine_seam.py (heroine_head.py runs it on every heroine.glb it writes).
"""
import argparse
import os
import sys

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
HAIRS = os.path.join(ROOT, "godot", "art", "people", "heroine_hair_%s.gltf")
HAIR_STYLES = ["braid", "ponytail", "pixie", "bob", "long"]
HAIR_NEAR, HAIR_FAR = 0.025, 0.05  # (a hair point follows the scalp under it fully within NEAR of it, not past FAR)
FACES = ["doe", "fey", "hardwon", "highborn", "moonlit", "saffron", "sunborn", "vixen", "wildling"]
FIX = ["sunborn"]                  # (the faces this is run on: those whose --measure stands out like Sunborn's)

ITER, LAM = 80, 0.5                # (the diffusion that finds the broad shape: its steps and rate)
Y0, Y_EASE = 1.772, 0.014          # (her forehead from Y0 up, eased in over Y_EASE: her brows' tops are at ~1.772)
HAIR_Y, HAIR_EASE = 1.855, 0.015   # (and eased out by HAIR_Y, under her hair)
LINE = [(0.045, 1.838), (0.047, 1.815), (0.052, 1.795), (0.062, 1.775), (0.068, 1.752), (0.070, 1.73)]
R0, R1 = 0.010, 0.025              # (the band along the edge of her face's front: full within R0, gone by R1)
EYE = (0.035, 1.757, 0.026, 0.017, 0.35)   # (each eye and brow kept: centre |x|, y; radii x, y; ease, in radii)
EAR = (0.076, 1.735, -0.018, 0.026, 0.012)  # (each ear kept: centre |x|, y, z; radius, ease) (heroine_ears.EAR)
BACK = (-0.02, 0.03)               # (and the back of her head: z from BACK[0], eased in over BACK[1])


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _weld(V):
    """Each point's representative among the points at its place (her head is split along its UV seams)."""
    pairs = cKDTree(V).query_pairs(1e-6, output_type="ndarray")
    g = sp.coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(V), len(V)))
    _, lab = sp.csgraph.connected_components(g, directed=False)
    first = np.full(lab.max() + 1, len(V))
    np.minimum.at(first, lab, np.arange(len(V)))
    return first[lab]


class Head:
    def __init__(self, V, F):
        self.V, self.F = V, F
        self.rep = _weld(V)
        e = self.rep[np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])]
        e = np.unique(np.sort(e[e[:, 0] != e[:, 1]], 1), axis=0)
        n = len(V)
        self.A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
        self.deg = np.asarray(self.A.sum(1)).ravel()
        self.act = self.deg > 0

    def avg(self, x):
        o = x.copy()
        o[self.act] = (self.A @ x)[self.act] / self.deg[self.act, None]
        return o[self.rep]

    def broad(self, d):
        g = d.copy()
        for _ in range(ITER):
            g = g + LAM * (self.avg(g) - g)
        return g

    def normals(self, P):
        F = self.F
        fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
        acc = np.zeros_like(P)
        for k in range(3):
            np.add.at(acc, self.rep[F[:, k]], fn)
        n = acc[self.rep]
        return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)

    def mask(self):
        V = self.V
        ax = np.abs(V[:, 0])
        pts = []
        for x, y in LINE:  # (the edge's points on her face's front: the foremost point near each)
            for s in (1, -1):
                m = (np.abs(V[:, 0] - s * x) < 0.004) & (np.abs(V[:, 1] - y) < 0.004)
                pts.append(V[np.where(m)[0][np.argmax(V[m][:, 2])]])
        seg = []
        for s in (0, 1):
            P = np.array(pts[s::2])
            for i in range(len(P) - 1):
                seg += [P[i] * (1 - t) + P[i + 1] * t for t in np.linspace(0, 1, 12)]
        dist, _ = cKDTree(np.array(seg)).query(V)
        w = np.maximum(_ss((R1 - dist) / (R1 - R0)), _ss((V[:, 1] - Y0) / Y_EASE))
        e = np.sqrt(((ax - EYE[0]) / EYE[2]) ** 2 + ((V[:, 1] - EYE[1]) / EYE[3]) ** 2)
        keep_eye = _ss((e - 1) / EYE[4])
        keep_eye[V[:, 2] < 0.03] = 1
        ear = np.sqrt((ax - EAR[0]) ** 2 + (V[:, 1] - EAR[1]) ** 2 + (V[:, 2] - EAR[2]) ** 2)
        w = w * keep_eye * _ss((ear - EAR[3]) / EAR[4]) * _ss((V[:, 2] - BACK[0]) / BACK[1]) * _ss((HAIR_Y - V[:, 1]) / HAIR_EASE)
        return w


def _head(js, binc):
    mats = [m.get("name") for m in js.get("materials", [])]
    for m in js["meshes"]:
        for p in m["primitives"]:
            if "material" in p and mats[p["material"]] == "skin_head":
                return m, p
    raise SystemExit("no skin_head in the glb")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("faces", nargs="*")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--glb", default=GLB)
    ap.add_argument("--out")
    a = ap.parse_args()
    run(a.glb, a.out, a.faces or (FACES if a.measure else FIX), a.measure)


def run(path=GLB, out=None, faces=None, measure=False):
    faces = faces or FIX
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    hm, hp = _head(js, binc)
    names = hm.get("extras", {}).get("targetNames", [])
    V = hs._read(js, binc, hp["attributes"]["POSITION"])
    F = hs._read(js, binc, hp["indices"]).reshape(-1, 3)
    h = Head(V, F)
    w = h.mask()
    n0 = h.normals(V)
    done = hm.setdefault("extras", {}).setdefault("shape_falloff", {}) if not measure else hm.get("extras", {}).get("shape_falloff", {})
    wrote = False
    moved_hair = {}
    for f in faces:
        key = "face_" + f
        if key not in names:
            print("FALLOFF: no key", key)
            continue
        t = hp["targets"][names.index(key)]
        d = hs._read(js, binc, t["POSITION"])
        g = h.broad(d)
        hi = ((d - g) * n0).sum(1) * 1000  # (the fine relief along her normal, mm)
        d2 = d + w[:, None] * (g - d)
        mv = np.linalg.norm(d2 - d, axis=1) * 1000
        if measure:
            s = []
            for side, sm in (("R", V[:, 0] < 0), ("L", V[:, 0] > 0)):
                m = sm & (w > 0.5)
                s.append("%s relief max %.2f p95 %.2f" % (side, np.abs(hi[m]).max(), np.percentile(np.abs(hi[m]), 95)))
            print("FALLOFF %-9s %s | would move max %.2f mm (mask>0.5), %.2f mm where mask<0.05%s" % (
                f, "; ".join(s), mv[w > 0.5].max(), mv[w < 0.05].max(), "  [done]" if f in done else ""))
            continue
        if f in done:
            print("FALLOFF: %s already done in %s - left" % (f, path))
            continue
        _set_target(js, chunks, t, h, V, d, d2, hs._read(js, binc, t["NORMAL"]) if "NORMAL" in t else None)
        below = V[:, 1] < 1.765
        done[f] = {"iter": ITER, "y0": Y0, "r": [R0, R1], "max_mm": round(float(mv.max()), 2),
                   "below_brow_mm": round(float(mv[below].max()), 2)}
        wrote = True
        moved_hair[f] = (d2 - d)
        print("FALLOFF %s: relief taken out inside the mask; moved max %.2f mm (mask>0.5), %.2f mm where mask<0.05, "
              "%.2f mm below brow level (y<1.765), 0 where mask=0 (%.2g)" % (
                  f, mv[w > 0.5].max(), mv[w < 0.05].max(), mv[below].max(), mv[w == 0].max() if (w == 0).any() else 0))
    if wrote:
        hs._save(out or path, js, chunks)
        print("FALLOFF: written", out or path)
        if out is None or os.path.abspath(out) == os.path.abspath(GLB):
            for style in HAIR_STYLES:
                hair(HAIRS % style, V, moved_hair)


def hair(path, V, moved):
    """Each hair's face keys given the scalp's change under it, so her hair sits on her head as it did (a key's hair
    points follow the head's change at the 8 nearest of its points, weighted by inverse square distance, fully
    within HAIR_NEAR of the scalp, none past HAIR_FAR). Idempotent by the mesh's extras (shape_falloff)."""
    import json
    if not os.path.exists(path):
        return
    js = json.load(open(path))
    bin_path = os.path.join(os.path.dirname(path), js["buffers"][0]["uri"])
    binc = bytearray(open(bin_path, "rb").read())
    tree = cKDTree(V)
    changed = False
    for m in js["meshes"]:
        names = m.get("extras", {}).get("targetNames", [])
        done = m.setdefault("extras", {}).setdefault("shape_falloff", [])
        for f, dd in moved.items():
            key = "face_" + f
            if key not in names or f in done:
                continue
            most = 0.0
            for p in m["primitives"]:
                HV = hs._read(js, bytes(binc), p["attributes"]["POSITION"])
                dist, idx = tree.query(HV, k=8)
                wt = 1.0 / (dist ** 2 + 1e-8)
                ch = (dd[idx] * wt[..., None]).sum(1) / wt.sum(1)[:, None]
                ch *= (1 - _ss((dist[:, 0] - HAIR_NEAR) / (HAIR_FAR - HAIR_NEAR)))[:, None]
                t = p["targets"][names.index(key)]
                acc = js["accessors"][t["POSITION"]]
                vals = (hs._read(js, bytes(binc), t["POSITION"]) + ch).astype(np.float32)
                while len(binc) % 4:
                    binc.append(0)
                js["bufferViews"].append({"buffer": 0, "byteOffset": len(binc), "byteLength": vals.nbytes})
                binc += vals.tobytes()
                for k in ("byteOffset", "sparse"):
                    acc.pop(k, None)
                acc["bufferView"] = len(js["bufferViews"]) - 1
                acc["min"], acc["max"] = [float(v) for v in vals.min(0)], [float(v) for v in vals.max(0)]
                most = max(most, float(np.linalg.norm(ch, axis=1).max()))
            done.append(f)
            changed = True
            print("FALLOFF hair %s: %s's key given the scalp's change, most %.2f mm" % (os.path.basename(path), f, most * 1000))
    if changed:
        js["buffers"][0]["byteLength"] = len(binc)
        open(bin_path, "wb").write(bytes(binc))
        json.dump(js, open(path, "w"), indent=1)


def _set_target(js, chunks, t, h, V, d, d2, dn):
    """The key's offsets set to d2, and its normals turned by what the new shape turns them (area-weighted normals of
    the shaped head, before and after): untouched where nothing near moved."""
    hs._set(js, chunks, t["POSITION"], d2, minmax=True)
    if dn is None:
        return
    del_n = h.normals(V + d2) - h.normals(V + d)
    moved = np.linalg.norm(del_n, axis=1) > 1e-7
    dn = dn.copy()
    dn[moved] += del_n[moved]
    hs._set(js, chunks, t["NORMAL"], dn)


if __name__ == "__main__":
    main()
