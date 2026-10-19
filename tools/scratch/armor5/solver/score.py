"""armor 5 solver: score a trial socket row against the grids (grids.py). Rows as in Arms.cs Sockets (skeleton space
at rest). A key's dumped points move by new_mount * inverse(old mount)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools" / "anim"))
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
import armscheck as A
from grids import rest

OUTFITS = A.SOCKET_OUTFITS
ROWS = {  # name: (bone, At, Shaft, Thick, Normal, Mirrors)
    "back": ("spine_03", (0, 1.22, -0.20), (0, 1, 0), (0, 0, -1), (0, 0, -1), False),
    "hip_blade": ("pelvis", (0.21, 1.20, 0.10), (0.08, -0.87, -0.50), (1, 0, 0), (1, 0, 0), True),
    "hip_loop": ("pelvis", (-0.19, 0.50, 0.0), (0.06, 1, 0), (-1, 0, 0), (-1, 0, 0), True),
    "hip_belt": ("pelvis", (-0.18, 1.14, 0.05), (0.15, 0.95, 0.25), (-1, 0, 0), (-1, 0, 0), True),
    "belt_back": ("pelvis", (-0.17, 1.12, -0.13), (1, 0, 0), (0, 0, -1), (0, 0, -1), True),
    "sling": ("spine_03", (0.10, 1.16, -0.17), (-0.6, 0.8, 0), (0, 0, 1), (0, 0, -1), False),
    "back_diag": ("spine_03", (-0.07, 1.30, -0.20), (0.25, -0.97, 0), (0, 0, -1), (0, 0, -1), False),
}
PISTOL = {"Crossbow"}


def nz(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def mount(row, pistol, left):
    bone, at, shaft, thick, normal, mirrors = row
    at, shaft, thick, normal = (np.array(x, float) for x in (at, shaft, thick, normal))
    if left and mirrors:
        for v in (at, shaft, thick, normal):
            v[0] = -v[0]
    shaft = nz(shaft)
    thick = nz(thick - shaft * thick.dot(shaft))
    third = np.cross(shaft, thick)
    B = np.stack([shaft, thick, np.cross(shaft, thick)] if pistol else [third, shaft, thick], 1)
    T = np.eye(4); T[:3, :3] = B; T[:3, 3] = at
    Ri = np.linalg.inv(rest(bone))
    n = Ri[:3, :3] @ normal
    return Ri @ T, n


class Scorer:
    def __init__(self, grids, socket_keys=None, fitclip="idle_warden"):
        self.ck = A.SocketChecker("none")
        ck = self.ck
        self.keys = {k: d for k, d in ck.sheathed.items() if socket_keys is None or d["socket"] in socket_keys}
        self.pts = {}
        for k, d in self.keys.items():
            q = ck.pts_s[k]
            self.pts[k] = q
        self.g = {}
        for bone, path in grids.items():
            z = np.load(path)
            D = z["D"]; L = z["L"]
            # No part of her arm is thicker than 50 mm from its skin: an arm voxel deeper than that was signed off a
            # far vertex's normal (fingers, a hand's concave side): outside.
            # (and anything beyond the 30 mm shell signed exactly: a piece that deep crosses the shell too, so it still
            # reads 25-30 mm there; the far signs are off a far vertex's normal and unreliable)
            bad = D > 32
            D[bad] = -D[bad]
            self.g[bone] = dict(D=D, L=z["L"], F=list(z["F"]), lo=z["lo"], h=float(z["h"]), shape=tuple(z["shape"]))
        # fit: idle_warden_town frame 0, each outfit's cover
        G0 = ck.b.frames(ck.b.clip(fitclip, A.OUTDIR / "clips"))[0]
        self.G0 = G0
        self.P0 = ck.b.pose(G0)
        self.N0 = A.skin._normals(self.P0, ck.m.Tskin)
        self.cover = {o: (ck.m._cover(o) if o != "none" else np.zeros(len(self.P0))) for o in OUTFITS}

    def check_mounts(self):
        for k, d in self.keys.items():
            row = ROWS[d["socket"]]
            M, n = mount(row, d["kind"] in PISTOL, k.endswith("@hand_l"))
            err = np.abs(M[:3] - d["mount"]).max()
            print(f"{k:26} mount err {err:.4f} normal err {np.abs(n - d['normal']).max():.4f}")

    def clearance(self, socket, row, pistol=False):
        """{outfit: metres} as armscheck fit() reads it at the row's (right-hand) mount."""
        ck = self.ck
        M, n = mount(row, pistol, False)
        G = self.G0[ck.I[row[0]]]
        p = G[:3, :3] @ M[:3, 3] + G[:3, 3]
        n = G[:3, :3] @ n; n /= np.linalg.norm(n)
        used = ck.m.skin
        r = self.P0[used] - p
        along = r @ n
        lateral = np.linalg.norm(r - along[:, None] * n, axis=1)
        sel = (lateral < A.SOCKET_REACH) & (np.abs(along) < 0.12) & (self.N0[used] @ n > 0.3)
        out = {}
        for o in OUTFITS:
            thick = float(np.percentile(self.cover[o][used][sel], 90)) if sel.any() else 0.0
            out[o] = round(thick + A.AIR, 4)
        return out

    def lookup(self, bone, q_rest):
        g = self.g[bone]
        x = (q_rest - g["lo"]) / g["h"]
        sh = np.array(g["shape"])
        inside = np.all((x >= 0) & (x <= sh - 1.001), 1)
        x = np.clip(x, 0, sh - 1.001)
        i = np.floor(x).astype(int); t = x - i
        D = g["D"]
        acc = 0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                    acc = acc + D[:, i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz] * w
        r = np.rint(x).astype(int)
        lab = g["L"][:, r[:, 0], r[:, 1], r[:, 2]]
        acc = np.where(inside[None], acc, -999.0)
        return acc, lab  # (frames, points)

    def key_points(self, k, row):
        d = self.keys[k]
        M1, n1 = mount(row, d["kind"] in PISTOL, k.endswith("@hand_l"))
        M0 = np.eye(4); M0[:3] = d["mount"]
        X = M1 @ np.linalg.inv(M0)
        p = self.pts[k] @ X[:3, :3].T + X[:3, 3]
        return p, n1

    def score(self, socket, row, outfits=OUTFITS, clr=None, detail=False):
        """{key: {outfit: (body mm, arm mm, frame of worst arm, frame of worst body, skin gap mm at idle@0)}}"""
        bone = row[0]
        R = rest(bone)
        pistol = any(d["kind"] in PISTOL for d in self.keys.values() if d["socket"] == socket)
        clr = clr or self.clearance(socket, row, pistol)
        res = {}
        F = self.g[bone]["F"]
        i0 = F.index("idle_warden_town@0")
        for k, d in self.keys.items():
            if d["socket"] != socket:
                continue
            p, n = self.key_points(k, row)
            res[k] = {}
            for o in outfits:
                q = p + n * clr[o]
                qr = q @ R[:3, :3].T + R[:3, 3]
                D, L = self.lookup(bone, qr)
                body = np.where(L, -999, D); arm = np.where(L, D, -999)
                bf = body.max(1); af = arm.max(1)
                gap = -np.where(L[i0], -999, D[i0]).max()
                res[k][o] = (max(0.0, float(bf.max())), max(0.0, float(af.max())),
                             F[int(af.argmax())], F[int(bf.argmax())], float(gap))
        return res, clr
