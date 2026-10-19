"""armor 5 solver: her skin's signed depth (mm, + inside) sampled on a grid in a socket bone's REST frame, per frame
of the town clips, with an arm label per voxel (nearest skin vertex on an arm/hand bone). A trial socket row is then
scored by trilinear lookup, no Godot and no per-trial skin queries.
    python grids.py <bone> <out.npz> [--h 0.01]"""
import sys, time, argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools" / "anim"))
import numpy as np
from scipy.spatial import cKDTree
import armscheck as A

ARMY = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
CLIPS = [("idle_warden_town", 2), ("run_warden_town", 1), ("sprint_warden_town", 1), ("stop_warden_town_l", 1), ("stop_warden_town_r", 1)]
# Boxes in skeleton-rest space (+Y up, +Z front, +X her left).
BOX = {"pelvis": ((-0.36, 0.20, -0.36), (0.36, 1.45, 0.42)),
       "spine_03": ((-0.40, 0.30, -0.48), (0.40, 1.70, 0.25))}
REST = {"pelvis": (20.6, (0, 1.0723, 0)), "spine_03": (-18.4, (0, 1.3335, 0.0364))}


def rest(bone):
    a, o = REST[bone]
    a = np.radians(a)
    c, s = np.cos(a), np.sin(a)
    M = np.eye(4)
    M[:3, :3] = [[1, 0, 0], [0, c, -s], [0, s, c]]
    M[:3, 3] = o
    return M


def axes(bone, h):
    lo, hi = BOX[bone]
    return [np.arange(lo[i], hi[i] + 1e-9, h) for i in range(3)]


def job(args):
    bone, name, frames, h = args
    ck = A.SocketChecker("none")
    b = ck.b
    vb = np.array([any(a in str(n) for a in ARMY) for n in ck.vbone])
    ax = axes(bone, h)
    g = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
    Ri = np.linalg.inv(rest(bone))
    gl = g @ Ri[:3, :3].T + Ri[:3, 3]           # bone-local
    Gs = b.frames(b.clip(name, A.OUTDIR / "clips"))
    surf = ck.body
    out = []
    for f in frames:
        G = Gs[f]
        P = b.pose(G)
        surf.pose(P)
        M = G[ck.I[bone]]
        Q = gl @ M[:3, :3].T + M[:3, 3]
        tree = cKDTree(P[surf.used])
        dd, ix = tree.query(Q, k=1)
        vi = surf.used[ix]
        sgn = np.where(((Q - P[vi]) * surf.normals[vi]).sum(1) < 0, 1.0, -1.0)
        depth = sgn * dd * 1000.0
        lab = vb[vi]
        near = np.nonzero(dd < 0.03)[0]
        for lo in range(0, len(near), 20000):
            sl = near[lo:lo + 20000]
            d, nr = surf.signed(P, Q[sl], reach=0.035, k=8)
            ok = np.isfinite(d)
            depth[sl[ok]] = -d[ok] * 1000.0
            lab[sl[ok]] = vb[nr[ok]]
        out.append((name, f, depth.astype(np.float32), lab))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bone")
    ap.add_argument("out")
    ap.add_argument("--h", type=float, default=0.01)
    a = ap.parse_args()
    t0 = time.time()
    ax = axes(a.bone, a.h)
    shape = tuple(len(x) for x in ax)
    D, L, F = [], [], []
    with ProcessPoolExecutor(max_workers=7) as ex:
        jobs = [(a.bone, "idle_warden_town", list(range(i, 161, 6)), a.h) for i in (0, 2, 4)]
        jobs += [(a.bone, n, list(range(0, {"run_warden_town": 22, "sprint_warden_town": 22}.get(n, 25))), a.h) for n, _ in CLIPS[1:]]
        for res in ex.map(job, jobs):
            for name, f, d, l in res:
                D.append(d.reshape(shape)); L.append(l.reshape(shape)); F.append(f"{name}@{f}")
    np.savez_compressed(a.out, D=np.array(D), L=np.array(L), F=np.array(F), lo=np.array(BOX[a.bone][0]), h=a.h, shape=np.array(shape))
    print(f"{a.bone}: {len(F)} frames, grid {shape}, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
