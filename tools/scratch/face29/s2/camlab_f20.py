"""Label map of her mouth as the Look's camera sees it: python camlab.py GLB CAMLOG OUT.png [face] [pose] [sx]
CAMLOG: a Godot log with MOUTHCAM lines (HerFaceLife --mouth-cam); the last one is used. The crop is the sheets'
860,480..1060,650 (of 1920x1080) at sx samples per pixel. Colours: head tan, upper teeth white, lower teeth cyan (each
times its COLOR_0 r), tongue pink (times its COLOR_0), back faces of the head (her mouth's inside) red, nothing black.
Prints, per column band of the crop, what fills the opening."""
import re
import sys
import numpy as np
import trimesh
from PIL import Image
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import heroine_seam as hs

A = sys.argv + [None] * 6
GLB, LOG, OUT = A[1], A[2], A[3]
FACE = A[4] or "own"
POSE = A[5] or "open"
SX = int(A[6]) if (A[6] or "").isdigit() else 1
BOX = (860, 480, 1060, 650)
POSES = {"rest": {}, "open": {"mouth_open": 0.6}, "smo": {"mouth_open": 0.6, "smile": 0.8, "smile_open": 0.8},
         "smile": {"smile": 0.8}}


def cam(log):
    ls = [l for l in open(log, encoding="utf-8", errors="replace") if l.startswith("MOUTHCAM")]
    f = ls[-1].split()
    g = lambda k, n=3: np.array([float(v) for v in f[f.index(k) + 1:f.index(k) + 1 + n]])  # noqa: E731
    return g("o"), np.c_[g("bx"), g("by"), g("bz")], float(g("fov", 1)[0]), g("vp", 2)


def load(glb, face, pose):
    js, binc = hs._load(glb)
    W = dict(POSES[pose])
    if face != "own":
        W["face_" + face] = 1.0
    out = {}
    for m in js["meshes"]:
        if m.get("name") not in ("HeroineHead", "HeroineTeeth", "HeroineTongue"):
            continue
        p = m["primitives"][0]
        names = m.get("extras", {}).get("targetNames", [])
        V = hs._read(js, binc, p["attributes"]["POSITION"]).astype(float)
        F = hs._read(js, binc, p["indices"]).reshape(-1, 3).astype(np.int64)
        X = V.copy()
        for i, n in enumerate(names):
            if n in W:
                X += W[n] * hs._read(js, binc, p["targets"][i]["POSITION"])
        C = hs._read(js, binc, p["attributes"]["COLOR_0"]) if "COLOR_0" in p["attributes"] else np.ones((len(V), 4))
        D = hs._read(js, binc, p["targets"][names.index("mouth_open")]["POSITION"]) if "mouth_open" in names else None
        out[m["name"]] = (X, F, C, D, V)
    return js, out


def rays(o, B, fov, vp, box, sx):
    xs = (np.arange(box[0] * sx, box[2] * sx) + 0.5) / sx
    ys = (np.arange(box[1] * sx, box[3] * sx) + 0.5) / sx
    gx, gy = np.meshgrid(xs, ys)
    t = np.tan(np.radians(fov) / 2)
    dc = np.stack([(gx / vp[0] * 2 - 1) * t * vp[0] / vp[1], (1 - gy / vp[1] * 2) * t, -np.ones_like(gx)], -1).reshape(-1, 3)
    d = dc @ B.T
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return np.tile(o, (len(d), 1)), d, gx.shape


def cast(meshes, orig, dirs):
    best = np.full(len(orig), np.inf)
    lab = np.zeros(len(orig), int)
    val = np.zeros(len(orig))
    pos = np.full((len(orig), 3), np.nan)
    for li, name in ((1, "HeroineHead"), (2, "HeroineTeeth"), (4, "HeroineTongue")):
        X, F, C, D, V = meshes[name]
        if name == "HeroineHead":
            cen = X[F].mean(1)
            F = F[(np.abs(cen[:, 0] - 0.002) < 0.05) & (cen[:, 1] > 1.63) & (cen[:, 1] < 1.73) & (cen[:, 2] > 0.0)]
        tm = trimesh.Trimesh(X, F, process=False)
        loc, ri, ti = tm.ray.intersects_location(orig, dirs, multiple_hits=False)
        dist = ((loc - orig[ri]) * dirs[ri]).sum(1)
        nrm = tm.face_normals[ti]
        for k in range(len(ri)):
            r = ri[k]
            if dist[k] < best[r]:
                best[r] = dist[k]
                f = F[ti[k]]
                L = li
                if name == "HeroineTeeth":
                    L = 2 if np.linalg.norm(D[f], axis=1).mean() < 0.002 else 3
                if name == "HeroineHead" and (nrm[k] @ dirs[r]) > 0:
                    L = 5
                lab[r] = L
                val[r] = C[f, 0].mean() if name != "HeroineHead" else C[f, 3].mean()
                pos[r] = loc[k]
    return lab, val, pos


if __name__ == "__main__":
    o, B, fov, vp = cam(LOG)
    js, meshes = load(GLB, FACE, POSE)
    orig, dirs, shp = rays(o, B, fov, vp, BOX, SX)
    lab, val, pos = cast(meshes, orig, dirs)
    lab = lab.reshape(shp); val = val.reshape(shp); pos = pos.reshape(shp + (3,))
    img = np.zeros(shp + (3,))
    base = {0: (0, 0, 0), 1: (0.85, 0.65, 0.5), 2: (1, 1, 1), 3: (0.3, 1, 1), 4: (1, 0.45, 0.6), 5: (0.8, 0.1, 0.1)}
    for L, c in base.items():
        m = lab == L
        k = val[m][:, None] if L in (2, 3, 4) else (val[m][:, None] * 0.6 + 0.4 if L == 1 else 1.0)
        img[m] = np.array(c) * k
    Image.fromarray((img * 255).astype(np.uint8)).resize((shp[1] * 2 // SX * 1, shp[0] * 2 // SX * 1), Image.NEAREST).save(OUT)
    np.savez_compressed(OUT[:-4] + ".npz", lab=lab, val=val, pos=pos)
    print("cam o (mm)", np.round(o * 1000, 1), "fwd", np.round(-B[:, 2] / np.linalg.norm(B[:, 2]), 3), "fov", fov, "vp", vp,
          "scale", np.round(np.linalg.norm(B, axis=0), 4))
    # (bands of the crop's columns: what fills the opening (not head) in each)
    for c0 in range(0, shp[1], 10 * SX):
        col = lab[:, c0:c0 + 10 * SX]
        op = (col != 1).sum(0).mean()
        if op < 3 * SX:
            continue
        print("px %3d: open %5.1f px | U %4.1f L %4.1f T %4.1f in %4.1f none %4.1f" % (
            BOX[0] + c0 / SX, op / SX, *[(col == L).sum(0).mean() / SX for L in (2, 3, 4, 5, 0)]))
