"""What she holds, through her body: every clip, every weapon set.

The owner: "the shield just completely goes into her body all the time". For
each clip and each weapon set her loadouts give her (godot/logic/Play/Loadout.cs),
the pieces she holds (godot/src/Actors/Arms.cs: Make, MountTransform and
PieceTransform, dumped by godot/tools_scenes/ArmsDump.cs to data/arms_local.json,
each triangle in its holding bone's own space) are carried by her bones through
every frame and measured against her posed skin with the HOLDING ARM LEFT OUT
(motion.py's Measure.arm[side] surface: the rest of her, so the grip inside her
own fist does not count, but the other arm, trunk, breasts, hips, legs and head
do). The holding arm itself is measured too (13 October; it was left out, pauldron
and shoulder included, and a shield rim cut her own pauldron 40 mm unseen):
against her whole skin, counting points whose nearest vertex lies on the holding
side's shoulder or arm short of the mount (HOLD_REACH: above the elbow for the
shield on the forearm, short of the wrist for a piece in the fist). Each row's
depth and outfit are the worst of both; hold_mm / hold_outfit_mm are the arm's. Depth is mm inside her skin (skeleton units, as motion.py reports; the
game scales her and the weapon together by world_scale, so nothing changes in
relative terms). A point beyond the signed distance's reach (8 cm) is tested
by winding number: inside counts as 80 mm or more, so a shield buried deep is
never missed.

    python tools/anim/armscheck.py [clip ...] [--sets warden,oath,...] [--folder DIR]
                                   [--step N] [--save NAME] [--top N] [--outfit NAME] [--arms FILE]

Sets: warden_sword_shield, oath_shield, axe, axes, wand, staff, crossbow,
daggers (or a loadout key: worn_oathblade, judgement_disc_item, ...; 'warden'
and 'oath' alone are accepted for the first two). Default: every JSON in
out/clips, every set. Saved to out/armscheck_NAME.json.

--outfit warden|arcanist|reaver|ranger adds the depth into that outfit (cups,
belt, skirt: the garment's thickness over her skin, motion.py's cover, laid on
the nearest skin point; the holding arm's own garment is left out as its skin
is): outfit_mm per row, 0 when the piece clears the garment. Judge 46: a rim
on the cup reads as contact though the skin is clear.

--sockets [clip ...] [--step N] [--keep]: the weapons SHEATHED (by kind: Arms.cs Sockets). Fits
godot/art/anim/socket_clearance.json ({outfit: {socket: metres}}: the garment's thickness at each socket
plus 5 mm air, for warden, arcanist, reaver, ranger and none) and prints, per kind x outfit, the worst mm
into her skin / into the outfit with that clearance, over the clips (default: idle_<calling> and any
*_town clip). --keep measures with the file as it is. Needs the "sheathed" key of arms_local.json (ArmsDump).
"""
from __future__ import annotations

import argparse
import contextlib
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
from motion import Measure, Surface  # noqa: E402

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
# The kind of each right-hand piece (keyed.slide_dir: the line a clip's grip slide moves it along).
PIECE_KIND = {"mage_staff": "staff", "chevalier_sword": "sword", "viking_sword": "sword", "oathbrand": "sword",
              "viking_axe": "axe", "wand": "wand", "crossbow": "crossbow", "daggers": "daggers"}
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
HOLD_REACH = {"lowerarm": 0.85, "hand": 1.6}   # the holding arm counted up to here (0 shoulder, 1 elbow, 2 wrist)


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
    def __init__(self, outfit=None, arms=None):
        # Her helpers driven as the game's HerJoints drives them: the forearm
        # bone kept on its hinge (its roll handed to the hand), so a piece on
        # lowerarm_* turns only as the game turns it. (Without this the shield
        # rolled with the clip's forearm roll: 5-8 cm off at the rim.)
        self.b = Body.heroine(jiggle=True, helpers=True)
        self.m = Measure(self.b)
        self.cover = self.m._cover(outfit) if outfit else None
        self.I = self.b.sk.index
        raw = json.loads(Path(arms or DATA / "arms_local.json").read_text())
        self.local = {k: (np.array(d["v"], float), np.array(d["t"], int)) for k, d in raw.items() if "v" in d}
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
        # The holding arm (13 October): the surface above leaves the whole holding arm out, its
        # shoulder blend included, so a shield rim in her own pauldron or upper arm went unmeasured.
        # Measured here against her whole skin, counting only points whose nearest vertex is on the
        # holding side's shoulder or arm short of the mount (HOLD_REACH: above the elbow for a piece
        # strapped to the forearm, short of the wrist for one in the fist).
        self.whole = Surface(self.m.Tskin, len(b.P))
        self.whole.winding = lambda P, Q: np.ones(len(Q))
        rg, rp = b.sk.rest_globals()
        rp = rp[0]
        self.hold_along = {}
        for s in "lr":
            k = b.parts.index("arm_" + s)
            on = np.zeros(len(b.P), bool)
            on[self.m.skin] = b.share[self.m.skin, k] >= 0.05
            segs = [(rp[self.I[f"upperarm_{s}"]], rp[self.I[f"lowerarm_{s}"]]),
                    (rp[self.I[f"lowerarm_{s}"]], rp[self.I[f"hand_{s}"]]),
                    (rp[self.I[f"hand_{s}"]], rp[self.I[f"middle_01_{s}"]])]
            best = np.full(len(b.P), np.inf)
            along = np.full(len(b.P), np.inf)
            for i0, (a0, a1) in enumerate(segs):
                d = a1 - a0
                t = np.clip(((b.P - a0) @ d) / (d @ d), 0, 1)
                dist = np.linalg.norm(b.P - (a0 + t[:, None] * d), axis=1)
                m = dist < best
                best = np.where(m, dist, best)
                along = np.where(m, i0 + t, along)
            self.hold_along[s] = np.where(on, along, np.inf)

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

    def outfit_depth(self, P, key, G, depth, near):
        """mm into the outfit (cover over the skin): the worst point, and its nearest vertex."""
        bone = key.split("@")[1]
        surf = self.m.arm["r" if bone.endswith("_r") else "l"][2]
        M = self.bone_world(G, bone)
        Q = self.pts[key] @ M[:3, :3].T + M[:3, 3]
        d, nr = surf.signed(P, Q, reach=0.14, k=8)
        ok = np.isfinite(d) & (d > -0.002)
        od = np.zeros(len(Q))
        od[ok] = (self.cover[nr[ok]] - d[ok]) * 1000.0
        i = int(od.argmax())
        best, where = float(od[i]), int(nr[i])
        j = int(depth.argmax())
        if depth[j] > 0 and depth[j] + 1000.0 * self.cover[near[j]] > best:
            best, where = float(depth[j] + 1000.0 * self.cover[near[j]]), int(near[j])
        return max(0.0, best), where

    def hold_depth(self, P, key, G):
        """(mm into her skin, mm into her outfit, where) against the holding side's shoulder and arm
        short of the mount (see __init__). Coarse points first; the full set only within 40 mm."""
        bone = key.split("@")[1]
        side = "r" if bone.endswith("_r") else "l"
        zone = self.hold_along[side] < HOLD_REACH[bone.split("_")[0]]
        surf = self.whole
        M = self.bone_world(G, bone)
        cov = self.cover if self.cover is not None else np.zeros(len(P))
        for pts in (self.coarse[key], self.pts[key]):
            Q = pts @ M[:3, :3].T + M[:3, 3]
            d, nr = surf.signed(P, Q, reach=0.14, k=8)
            ok = np.isfinite(d) & (nr >= 0)
            ok[ok] = zone[nr[ok]]
            if not ok.any():
                return 0.0, 0.0, "-"
            qi = np.nonzero(ok)[0]
            # A point read inside by more than 4 mm is confirmed by winding number, deepest first.
            deep = qi[d[qi] < -0.004]
            if len(deep):
                deep = deep[np.argsort(d[deep])][:400]
                w = fast_winding(surf, P, Q[deep])
                d[deep[w < 0.5]] *= -1
            dq, nq = d[qi], nr[qi]
            clear = dq - cov[nq]
            if pts is self.coarse[key] and clear.min() > MARGIN:
                return 0.0, 0.0, "-"
            if pts is self.pts[key]:
                skin_mm = max(0.0, float(-dq.min()) * 1000.0)
                j = int(clear.argmin())
                out_mm = max(0.0, float(-clear[j]) * 1000.0)
                return skin_mm, out_mm, ("hold " + self.where(nq[j])) if out_mm > 0 or skin_mm > 0 else "-"

    def clip(self, name, folder, pieces, step=1):
        """{key: (worst mm per frame, where per frame[, outfit mm, outfit where])} over the sampled frames.
        A clip's "grip_slide" (metres, animation 47: keyed.build) moves the piece in her right fist that far along its
        shaft (keyed.slide_dir of its kind, PIECE_KIND), and its "grip_tilt" (degrees, animation 48) turns it in the
        fist about the palm's normal through the pocket first (keyed.grip_pose), as the game does (PersonView.Slide)."""
        c = self.b.clip(name, folder)
        with self.gripped(c, pieces):
            return self._clip(c, pieces, step)

    @contextlib.contextmanager
    def gripped(self, c, pieces):
        """The pieces of `pieces` moved in her fists as the clip `c` moves them (its "grip_slide" for the right fist and tilt;
        "grip_slide_l" for the left, animation 55: no pocket, so a slide along the plain mount's shaft, keyed.slide_dir_left),
        then put back."""
        s = float(c.meta.get("grip_slide", 0.0) or 0.0)
        tl = float(c.meta.get("grip_tilt", 0.0) or 0.0)
        sl = float(c.meta.get("grip_slide_l", 0.0) or 0.0)
        kept = {}
        if s or tl or sl:
            from keyed import slide_dir, slide_dir_left, grip_pose
            for k in pieces:
                kind = PIECE_KIND.get(k.split("@")[0])
                if k.endswith("@hand_r"):
                    d = slide_dir(kind) if (s or tl) else None
                    mv = (lambda kind=kind: grip_pose(kind, s, tl)) if d is not None else None
                else:
                    d = slide_dir_left("axes" if kind == "axe" else kind) if sl and k.endswith("@hand_l") else None
                    mv = (lambda d=d: (np.eye(3), sl * d)) if d is not None else None
                if mv is not None:
                    kept[k] = (self.local[k], self.pts[k], self.coarse[k])
                    v, t = self.local[k]
                    R, tr = mv()
                    self.local[k], self.pts[k], self.coarse[k] = ((v @ R.T + tr, t), self.pts[k] @ R.T + tr,
                                                                  self.coarse[k] @ R.T + tr)
        try:
            yield
        finally:
            for k, (lo, pt, co) in kept.items():
                self.local[k], self.pts[k], self.coarse[k] = lo, pt, co

    def _clip(self, c, pieces, step=1):
        b = self.b
        Gs = b.frames(c)
        # Per piece: body mm, where, outfit mm, where (each the worst of the rest of her and the
        # holding arm), then the holding arm alone: skin mm, outfit mm, where.
        res = {k: ([], [], [], [], [], [], []) for k in pieces}
        frames = list(range(0, len(Gs), step))
        for f in frames:
            G = Gs[f]
            P = b.pose(G)
            for s in "lr":
                self.m.arm[s][2].pose(P)
            self.whole.pose(P)
            for k in pieces:
                depth, near = self.depths(P, k, G)
                i = int(depth.argmax())
                hs, ho, hw = self.hold_depth(P, k, G)
                bd, bw = float(depth[i]), (self.where(near[i]) if depth[i] > 0 else "-")
                res[k][0].append(max(bd, hs))
                res[k][1].append(bw if bd >= hs else hw)
                res[k][4].append(hs)
                res[k][5].append(ho)
                res[k][6].append(hw)
                if self.cover is not None:
                    od, ow = self.outfit_depth(P, k, G, depth, near)
                    res[k][2].append(max(od, ho))
                    res[k][3].append((self.where(ow) if od > 0 else "-") if od >= ho else hw)
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


def _init(outfit=None, arms=None):
    global _CK
    _CK = Checker(outfit, arms)


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
            dep, wh, od, ow, hs, ho, hw = res[k]
            dep = np.array(dep)
            i = int(dep.argmax())
            bad = int((dep > BAD).sum())
            row = dict(clip=name, set=s, piece=piece, depth_mm=round(float(dep[i]), 1), frame=frames[i],
                       part=wh[i], frames_over=bad, frames=n, share=round(bad / n, 3))
            hh = np.maximum(np.array(hs), np.array(ho))
            h = int(hh.argmax())
            row.update(hold_mm=round(float(hs[h]), 1), hold_outfit_mm=round(float(ho[h]), 1), hold_frame=frames[h],
                       hold_part=hw[h], hold_frames_over=int((hh > BAD).sum()))
            if od:
                od = np.array(od)
                j = int(od.argmax())
                row.update(outfit_mm=round(float(od[j]), 1), outfit_frame=frames[j], outfit_part=ow[j],
                           outfit_frames_over=int((od > BAD).sum()))
            rows.append(row)
    return name, None, rows

# ------------------------------------------------------------------ sockets --
# Weapons sheathed (Arms.Sheathed: godot/src/Actors/Arms.cs, by KIND). ArmsDump writes, under "sheathed", every kind's
# piece at its bare socket in the socket bone's space, with its socket name and outward normal. --sockets
#   (a) fits godot/art/anim/socket_clearance.json = {outfit: {socket: metres}}: for each outfit (and 'none') and each
#       socket, the garment's thickness over her skin along the socket's normal (motion.py's cover, the 90th percentile
#       over her skin round the socket point, facing out) plus AIR; the game pushes the socket out by it, and
#   (b) measures every kind at its socket (pushed by that file) against every outfit, over the clips: worst mm into her
#       skin and into the outfit, per kind x outfit. A new asset needs only its Spec row (file, kind): run it.
CLEARANCE = HERE.parent.parent / "godot" / "art" / "anim" / "socket_clearance.json"
SOCKET_OUTFITS = ("warden", "arcanist", "reaver", "ranger", "none")
AIR = 0.005      # m, air between the socket and the garment
SOCKET_REACH = 0.06   # m, round the socket's normal line, the skin the garment is read on
CALLINGS = ("warden", "arcanist", "reaver", "stalker")


class SocketChecker(Checker):
    def __init__(self, outfit, arms=None):
        super().__init__(None if outfit == "none" else outfit, arms)
        self.outfit = outfit
        raw = json.loads(Path(arms or DATA / "arms_local.json").read_text()).get("sheathed", {})
        self.sheathed = {}
        for key, d in raw.items():
            self.sheathed[key] = dict(bone=d["bone"], kind=d["kind"], socket=d["socket"], normal=np.array(d["normal"], float),
                                      mount=np.array(d["mount"], float), v=np.array(d["v"], float), t=np.array(d["t"], int))
        self.pts_s = {k: sample(d["v"], d["t"]) for k, d in self.sheathed.items()}
        self.body = skin_surface(self)

    def fit(self, G, clearance_air=AIR):
        """{socket: metres} for this outfit, read on the pose G."""
        b, m = self.b, self.m
        P = b.pose(G)
        N = skin._normals(P, m.Tskin)
        cover = self.cover if self.cover is not None else np.zeros(len(P))
        used = m.skin
        out = {}
        for key, d in self.sheathed.items():
            if d["socket"] in out or key.endswith("@hand_l"):
                continue
            M = G[self.I[d["bone"]]]
            p = M[:3, :3] @ d["mount"][:, 3] + M[:3, 3]
            n = M[:3, :3] @ d["normal"]
            n /= np.linalg.norm(n)
            r = P[used] - p
            along = r @ n
            lateral = np.linalg.norm(r - along[:, None] * n, axis=1)
            sel = (lateral < SOCKET_REACH) & (np.abs(along) < 0.12) & (N[used] @ n > 0.3)
            thick = float(np.percentile(cover[used][sel], 90)) if sel.any() else 0.0
            out[d["socket"]] = round(thick + clearance_air, 4)
        return out

    def measure_clip(self, name, folder, clearance, step=1):
        """{key: (worst mm into skin, worst mm into outfit)} over the clip."""
        b = self.b
        Gs = b.frames(b.clip(name, folder))
        res = {k: [0.0, 0.0] for k in self.sheathed}
        for f in range(0, len(Gs), step):
            G = Gs[f]
            P = b.pose(G)
            self.body.pose(P)
            for k, d in self.sheathed.items():
                push = d["normal"] * clearance.get(d["socket"], 0.0)
                M = G[self.I[d["bone"]]]
                Q = (self.pts_s[k] + push) @ M[:3, :3].T + M[:3, 3]
                keep, near, _ = self.measure(P, self.body, Q)
                res[k][0] = max(res[k][0], float(keep.max()))
                if self.cover is not None:
                    dd, nr = self.body.signed(P, Q, reach=0.14, k=8)
                    ok = np.isfinite(dd) & (dd > -0.002)
                    od = np.zeros(len(Q))
                    od[ok] = (self.cover[nr[ok]] - dd[ok]) * 1000.0
                    j = int(keep.argmax())
                    deep = float(keep[j] + 1000.0 * self.cover[near[j]]) if keep[j] > 0 else 0.0
                    res[k][1] = max(res[k][1], float(od.max()), deep)
        return res


def skin_surface(ck):
    """The whole of her skin as one surface (the arms included, nothing left out, for a piece nobody holds)."""
    surf = Surface(ck.m.Tskin, len(ck.b.P))
    surf.winding = lambda P, Q: np.ones(len(Q))
    return surf


def _socket_job(job):
    outfit, folder, names, step, arms, keep = job
    ck = SocketChecker(outfit, arms)
    folder = Path(folder)
    first = ck.b.frames(ck.b.clip(names[0], folder))[0]
    fitted = ck.fit(first)
    clr = (json.loads(CLEARANCE.read_text()).get(outfit, {}) if keep and CLEARANCE.exists() else fitted)
    worst = {k: [0.0, 0.0] for k in ck.sheathed}
    for n in names:
        for k, (a, o) in ck.measure_clip(n, folder, clr, step).items():
            worst[k] = [max(worst[k][0], a), max(worst[k][1], o)]
    kinds = {}
    for k, w in worst.items():
        kd = ck.sheathed[k]["kind"]
        kinds[kd] = [max(kinds.get(kd, [0, 0])[0], w[0]), max(kinds.get(kd, [0, 0])[1], w[1])]
    return outfit, fitted, kinds, {k: (ck.sheathed[k]["kind"], ck.sheathed[k]["socket"]) for k in ck.sheathed}


def run_sockets(a):
    t0 = time.time()
    folder = Path(a.folder) if a.folder else OUTDIR / "clips"
    names = a.clips or ([f"idle_{c}" for c in CALLINGS if (folder / f"idle_{c}.json").exists()] + sorted(p.stem for p in folder.glob("*_town.json")))
    if not names:
        sys.exit(f"no clips in {folder}")
    jobs = [(o, str(folder), names, a.step, a.arms, a.keep) for o in SOCKET_OUTFITS]
    table, kinds, info = {}, {}, {}
    with ProcessPoolExecutor(max_workers=min(a.jobs, len(jobs))) as ex:
        for outfit, fitted, kd, inf in ex.map(_socket_job, jobs):
            table[outfit], kinds[outfit], info = fitted, kd, inf
            print(f"{outfit} {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    if not a.keep:
        CLEARANCE.parent.mkdir(parents=True, exist_ok=True)
        CLEARANCE.write_text(json.dumps(table, indent=1) + "\n")
        print(f"wrote {CLEARANCE}")
    socks = sorted({s for _, s in info.values()})
    print("clearance (mm) " + "".join(f"{o:>10}" for o in SOCKET_OUTFITS))
    for s in socks:
        print(f"  {s:14}" + "".join(f"{table[o].get(s, 0) * 1000:10.1f}" for o in SOCKET_OUTFITS))
    print(f"worst mm into skin / into outfit over {', '.join(names)} (step {a.step})")
    print(f"  {'kind':10} {'socket':10}" + "".join(f"{o:>14}" for o in SOCKET_OUTFITS))
    for kd in sorted({k for k, _ in info.values()}):
        s = next(s for k, s in info.values() if k == kd)
        print(f"  {kd:10} {s:10}" + "".join(f"{kinds[o][kd][0]:7.1f}/{kinds[o][kd][1]:<6.1f}" for o in SOCKET_OUTFITS))
    print(f"{len(names)} clips, {time.time() - t0:.0f} s")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="*")
    ap.add_argument("--sets")
    ap.add_argument("--folder")
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--save")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--jobs", type=int, default=10, help="clips measured at once (processes)")
    ap.add_argument("--outfit", choices=("warden", "arcanist", "reaver", "ranger"))
    ap.add_argument("--arms", help="another arms_local.json (an older mount, to compare)")
    ap.add_argument("--sockets", action="store_true", help="fit art/anim/socket_clearance.json and measure every weapon kind sheathed, per outfit")
    ap.add_argument("--keep", action="store_true", help="with --sockets: measure with the clearance file as it is (no refit, no write)")
    ap.add_argument("--raw", action="store_true", help="clips as written, not staged (clavhold + armroll) as the game plays them")
    a = ap.parse_args()
    import staged
    staged.set_from_argv(["--raw"] if a.raw else [])
    if a.sockets:
        return run_sockets(a)
    t0 = time.time()
    folder = Path(a.folder) if a.folder else OUTDIR / "clips"
    names = a.clips or sorted(p.stem for p in folder.glob("*.json"))
    sets = resolve_sets(a.sets)
    jobs = [(n, str(folder), sets, a.step) for n in names]
    rows = []
    with ProcessPoolExecutor(max_workers=max(1, min(a.jobs, len(jobs))), initializer=_init, initargs=(a.outfit, a.arms)) as ex:
        for i, (name, err, r) in enumerate(ex.map(_work, jobs)):
            if err:
                print(f"{name}: skipped ({err})", file=sys.stderr)
            rows += r
            print(f"[{i + 1}/{len(names)}] {name} {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    rows.sort(key=lambda r: (-r["depth_mm"], -r["share"]))
    if a.save:
        OUTDIR.mkdir(exist_ok=True)
        (OUTDIR / f"armscheck_{a.save}.json").write_text(json.dumps(dict(seconds=round(time.time() - t0, 1), step=a.step, outfit=a.outfit, rows=rows), indent=1))
    oh = f" {'outfit':>7} {'frame':>5}  {'part':20}" if a.outfit else ""
    print(f"{'clip':30} {'set':20} {'piece':8} {'depth':>7} {'frame':>5}  {'part':24} {'>10mm':>9} {'share':>6}" + oh
          + f" {'hold':>5} {'h_out':>5} {'frame':>5}  hold part")
    for r in rows[: a.top]:
        o = f" {r['outfit_mm']:7.1f} {r['outfit_frame']:5d}  {r['outfit_part']:20}" if "outfit_mm" in r else ""
        print(f"{r['clip']:30} {r['set']:20} {r['piece']:8} {r['depth_mm']:7.1f} {r['frame']:5d}  {r['part']:24} "
              f"{r['frames_over']:4d}/{r['frames']:<4d} {r['share'] * 100:5.0f}%" + o
              + f" {r['hold_mm']:5.1f} {r['hold_outfit_mm']:5.1f} {r['hold_frame']:5d}  {r['hold_part']}")
    print(f"{len(names)} clips, {len(sets)} sets, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
