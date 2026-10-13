"""What she holds, through her body: every clip, every weapon set.

The owner: "the shield just completely goes into her body all the time". For
each clip and each weapon set her loadouts give her (godot/logic/Play/Loadout.cs),
the pieces she holds (godot/src/Actors/Arms.cs: Make, MountTransform and
PieceTransform, dumped by godot/tools_scenes/ArmsDump.cs to data/arms_local.json,
each triangle in its holding bone's own space) are carried by her bones through
every frame and measured against her posed skin with the HOLDING ARM LEFT OUT
(motion.py's Measure.arm[side] surface: the rest of her, so the grip inside her
own fist does not count, but the other arm, trunk, breasts, hips, legs and head
do). Depth is mm inside her skin (skeleton units, as motion.py reports; the
game scales her and the weapon together by world_scale, so nothing changes in
relative terms). A point beyond the signed distance's reach (8 cm) is tested
by winding number: inside counts as 80 mm or more, so a shield buried deep is
never missed.

    python tools/anim/armscheck.py [clip ...] [--sets warden,oath,...] [--folder DIR]
                                   [--step N] [--save NAME] [--top N]

Sets: warden_sword_shield, oath_shield, axe, axes, wand, staff, crossbow,
daggers (or a loadout key: worn_oathblade, judgement_disc_item, ...; 'warden'
and 'oath' alone are accepted for the first two). Default: every JSON in
out/clips, every set. Saved to out/armscheck_NAME.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import skin  # noqa: E402
from skin import Body  # noqa: E402
from motion import Measure  # noqa: E402

DATA = HERE / "data"
OUTDIR = HERE / "out"

# set -> [(piece name, "<arms id>@<bone>")]
SETS = {
    "warden_sword_shield": [("sword", "chevalier_sword@hand_r"), ("shield", "shield_round@lowerarm_l")],
    "oath_shield": [("sword", "viking_sword@hand_r"), ("shield", "shield_round@lowerarm_l")],
    "axe": [("axe", "viking_axe@hand_r")],
    "axes": [("axe_r", "viking_axe@hand_r"), ("axe_l", "viking_axe@hand_l")],
    "wand": [("wand", "wand@hand_r")],
    "staff": [("staff", "mage_staff@hand_r")],
    "crossbow": [("crossbow", "crossbow@hand_r")],
    "daggers": [("dagger_r", "daggers@hand_r"), ("dagger_l", "dagger_b@hand_l")],
}
ALIAS = {
    "warden": "warden_sword_shield", "worn_oathblade": "warden_sword_shield",
    "oath": "oath_shield", "judgement_disc_item": "oath_shield",
    "butchers_cleaver": "axe", "gyre_axes": "axes", "apprentice_wand": "wand",
    "ember_staff": "staff", "rime_rod": "staff", "hunting_bow": "crossbow", "knife_belt": "daggers",
}
DEEP = 80.0      # mm, a point beyond reach and inside
COARSE = 0.03   # m, the coarse points' voxel
MARGIN = 0.04   # m, the coarse points' distance from her skin beyond which the piece is clear
BAD = 10.0       # mm, a frame counts as through her beyond this


def sample(v, t, spacing=0.008, cap=6000, seed=1):
    """Points on a piece: its vertices and area-uniform samples of its faces."""
    A, B, C = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    area = np.linalg.norm(np.cross(B - A, C - A), axis=1) / 2
    n = int(min(cap, max(0, area.sum() / spacing ** 2)))
    pts = [v]
    if n > 0 and area.sum() > 0:
        rng = np.random.default_rng(seed)
        k = rng.choice(len(t), n, p=area / area.sum())
        r1, r2 = rng.random(n), rng.random(n)
        s = np.sqrt(r1)
        pts.append(A[k] * (1 - s)[:, None] + B[k] * (s * (1 - r2))[:, None] + C[k] * (s * r2)[:, None])
    return np.concatenate(pts)


_WCACHE = {}


def fast_winding(surf, P, Q, radius=0.25):
    """Surface.winding, vectorised: same maths, one pass over all pairs (the
    faces' tree kept while P is the same pose)."""
    hit = _WCACHE.get(id(surf))
    if hit is None or hit[0] is not P:
        A, B, C = P[surf.T[:, 0]], P[surf.T[:, 1]], P[surf.T[:, 2]]
        hit = _WCACHE[id(surf)] = (P, A, B, C, cKDTree((A + B + C) / 3))
    _, A, B, C, tree = hit
    out = np.zeros(len(Q))
    lists = tree.query_ball_point(Q, radius)
    cnt = np.array([len(x) for x in lists])
    if cnt.sum() == 0:
        return out
    ids = np.concatenate([np.asarray(x, int) for x in lists if len(x)])
    own = np.repeat(np.arange(len(Q)), cnt)
    q = Q[own]
    a, b, c = A[ids] - q, B[ids] - q, C[ids] - q
    la, lb, lc = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1), np.linalg.norm(c, axis=1)
    det = np.einsum("ij,ij->i", a, np.cross(b, c))
    den = la * lb * lc + (a * b).sum(1) * lc + (b * c).sum(1) * la + (c * a).sum(1) * lb
    np.add.at(out, own, np.arctan2(det, den))
    return out / (2 * np.pi)


class Checker:
    def __init__(self):
        self.b = Body.heroine(jiggle=True)
        self.m = Measure(self.b)
        self.I = self.b.sk.index
        raw = json.loads((DATA / "arms_local.json").read_text())
        self.local = {k: (np.array(d["v"], float), np.array(d["t"], int)) for k, d in raw.items()}
        self.pts = {k: sample(*vt) for k, vt in self.local.items()}
        self.coarse = {}
        for k, q in self.pts.items():
            vox = np.floor(q / COARSE).astype(np.int64)
            _, first = np.unique(vox, axis=0, return_index=True)
            self.coarse[k] = q[np.sort(first)]
        # Each bone's nearest-vertex normals for the deep fallback come from the surface itself.
        for s in "lr":
            # signed() would confirm each point it finds deep by winding number, one at a time: see depths().
            self.m.arm[s][2].winding = lambda P, Q: np.ones(len(Q))
        b = self.b
        # What part of her a skin vertex is: its heaviest bone's name (and breast flesh).
        self.vbone = np.array(b.sk.names)[b.J[np.arange(len(b.P)), b.W.argmax(1)]]

    def bone_world(self, G, bone):
        return G[self.I[bone]]

    def piece_points(self, key, G):
        bone = key.split("@")[1]
        M = G[self.I[bone]]
        return self.pts[key] @ M[:3, :3].T + M[:3, 3]

    def where(self, near):
        n = int(near)
        if n < 0:
            return "?"
        return ("breast " if self.m.breast[n] else "") + str(self.vbone[n])

    def depths(self, P, key, G):
        """Coarse points first (a point per 30 mm voxel); the full set only where the coarse
        ones are within 40 mm of her skin yet not already more than 20 mm through it."""
        bone = key.split("@")[1]
        surf = self.m.arm["r" if bone.endswith("_r") else "l"][2]
        M = self.bone_world(G, bone)
        for pts in (self.coarse[key], self.pts[key]):
            Q = pts @ M[:3, :3].T + M[:3, 3]
            keep, near, dmin = self.measure(P, surf, Q)
            if pts is self.pts[key] or keep.max() > 20 or (keep.max() <= 0 and dmin > MARGIN):
                return keep, near

    _vt = {}

    def vtree(self, P, surf):
        hit = self._vt.get(id(surf))
        if hit is None or hit[0] is not P:
            hit = self._vt[id(surf)] = (P, cKDTree(P[surf.used]))
        return hit[1]

    def measure(self, P, surf, Q):
        """Per point: depth in mm (<= 0: outside), and the nearest vertex, for one piece.

        Motion.py's signed distance confirms every point it finds deeper than
        4 mm by winding number, one by one: far too slow for a shield buried in
        her (thousands of points). Here the sign stands, and only the deepest
        points are confirmed (in batches, deepest first, until one is inside
        her): a frame is through her if its deepest confirmed point is."""
        d, near = surf.signed(P, Q, k=8)
        depth = np.where(np.isfinite(d), -d * 1000.0, 0.0)
        far = ~np.isfinite(d)
        if far.any():
            # Beyond reach (8 cm): inside her only if the nearest vertex's normal says it might be.
            qi = np.nonzero(far)[0]
            tree = self.vtree(P, surf)
            dd, ix = tree.query(Q[qi], k=1)
            vi = surf.used[ix]
            cand = qi[((Q[qi] - P[vi]) * surf.normals[vi]).sum(1) < 0]
            if len(cand):
                # (Its nearest vertex is farther than the reach; the depth is that distance, at least DEEP.)
                dc, ic = tree.query(Q[cand], k=1)
                depth[cand] = np.maximum(DEEP, dc * 1000.0)
                near[cand] = surf.used[ic]
        # Confirm, deepest first, in batches.
        order = np.argsort(-depth)
        order = order[depth[order] > 0]
        keep = np.zeros(len(depth))
        for lo, hi in ((0, 4), (4, 16), (16, 48)):
            batch = order[lo:hi]
            if len(batch) == 0:
                break
            w = fast_winding(surf, P, Q[batch])
            ok = batch[w > 0.5]
            keep[ok] = depth[ok]
            if len(ok):
                break
        fin = d[np.isfinite(d)]
        return keep, near, (float(fin.min()) if len(fin) else 1.0)

    def clip(self, name, folder, pieces, step=1):
        """{key: (worst mm per frame, where per frame)} over the sampled frames."""
        b = self.b
        c = b.clip(name, folder)
        Gs = b.frames(c)
        res = {k: ([], []) for k in pieces}
        frames = list(range(0, len(Gs), step))
        for f in frames:
            G = Gs[f]
            P = b.pose(G)
            for s in "lr":
                self.m.arm[s][2].pose(P)
            for k in pieces:
                depth, near = self.depths(P, k, G)
                i = int(depth.argmax())
                res[k][0].append(float(depth[i]))
                res[k][1].append(self.where(near[i]) if depth[i] > 0 else "-")
        return frames, res


def resolve_sets(arg):
    if not arg:
        return list(SETS)
    out = []
    for s in arg.split(","):
        s = s.strip()
        s = ALIAS.get(s, s)
        if s not in SETS:
            sys.exit(f"unknown set {s!r}; sets: {', '.join(SETS)}")
        if s not in out:
            out.append(s)
    return out


_CK = None


def _init():
    global _CK
    _CK = Checker()


def _work(job):
    name, folder, sets, step = job
    ck = _CK
    try:
        frames, res = ck.clip(name, Path(folder), sorted({k for s in sets for _, k in SETS[s]}), step)
    except Exception as e:  # a clip without her bones, or not a clip
        return name, f"{type(e).__name__}: {e}", []
    n = len(frames)
    rows = []
    for s in sets:
        for piece, k in SETS[s]:
            dep, wh = res[k]
            dep = np.array(dep)
            i = int(dep.argmax())
            bad = int((dep > BAD).sum())
            rows.append(dict(clip=name, set=s, piece=piece, depth_mm=round(float(dep[i]), 1), frame=frames[i],
                             part=wh[i], frames_over=bad, frames=n, share=round(bad / n, 3)))
    return name, None, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="*")
    ap.add_argument("--sets")
    ap.add_argument("--folder")
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--save")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--jobs", type=int, default=10, help="clips measured at once (processes)")
    a = ap.parse_args()
    t0 = time.time()
    folder = Path(a.folder) if a.folder else OUTDIR / "clips"
    names = a.clips or sorted(p.stem for p in folder.glob("*.json"))
    sets = resolve_sets(a.sets)
    jobs = [(n, str(folder), sets, a.step) for n in names]
    rows = []
    with ProcessPoolExecutor(max_workers=max(1, min(a.jobs, len(jobs))), initializer=_init) as ex:
        for i, (name, err, r) in enumerate(ex.map(_work, jobs)):
            if err:
                print(f"{name}: skipped ({err})", file=sys.stderr)
            rows += r
            print(f"[{i + 1}/{len(names)}] {name} {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    rows.sort(key=lambda r: (-r["depth_mm"], -r["share"]))
    if a.save:
        OUTDIR.mkdir(exist_ok=True)
        (OUTDIR / f"armscheck_{a.save}.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), step=a.step, rows=rows), indent=1))
    print(f"{'clip':30} {'set':20} {'piece':8} {'depth':>7} {'frame':>5}  {'part':24} {'>10mm':>9} {'share':>6}")
    for r in rows[: a.top]:
        print(f"{r['clip']:30} {r['set']:20} {r['piece']:8} {r['depth_mm']:7.1f} {r['frame']:5d}  {r['part']:24} "
              f"{r['frames_over']:4d}/{r['frames']:<4d} {r['share'] * 100:5.0f}%")
    print(f"{len(names)} clips, {len(sets)} sets, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
