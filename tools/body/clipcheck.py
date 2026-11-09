"""clipcheck: numbers for B's baked clips (the clip bridge, tools/body/README.md 'B native').

    python tools/body/clipcheck.py CLIP... [--out DIR] [--step N] [--no-a]

Reads the keys dump the bake writes for every clip with a tools/body/p1_clips.json entry
(tools/body/out/clips/NAME.json, git-ignored: A's posed globals and B's baked globals per key frame, both in
Godot skeleton space; tools_scenes/P1BakeRun.cs). Per clip, numbers only:
  pops    per keyed B bone the worst frame-to-frame local step against its median step (a spike: > 4x and > 3 deg),
          and for cycles the seam (last key vs first, deg, worst bone);
  feet    contact windows from A (ball height under A's clip floor + 2 cm; A and B measured in A's windows);
          the planted ball's horizontal drift in each window, the belt (A's median planted velocity) taken out, mm;
  body    B posed by the lbs poser (the glb's skin + rig_drive: helpers at rest local, then the laws, as P1Laws) at
          every Nth key: arm vertices (upper arm / forearm / hand dominant; those in the upper arm's first 40% along
          its axis, the armpit fold, counted apart as "axilla": a skin matter, not the clip's)
          against the torso, hips and thighs (signed distance to the nearest torso vertex along its normal, within
          3 cm): count inside, depth mm; each hand's nearest gap to the torso (min over frames; negative = inside);
  arms    each upper arm's elevation from down (deg, min/mean) and the elbow's (lowerarm head) signed distance to the
          torso skin (mm, min/mean), B beside A (A posed by plain lbs of heroine.glb, no laws).
Writes DIR/clipcheck.json (default tools/body/out/clipcheck.json).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from posers import make_poser  # noqa: E402

REPO = HERE.parent.parent
P1 = REPO / "godot/art/people/body_p1"
DUMP = HERE / "out/clips"
ARM = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")
TORSO = ("pelvis", "spine", "thigh", "glute", "breast", "pec", "lat", "belly", "butt")
GIRDLE = ("clavicle", "scap", "trap", "delt", "upperarm")
SPIKE_X, SPIKE_DEG = 4.0, 3.0
MOVING_DEG = 0.5   # a step under this (15 deg/s at 30 fps) is held, a breath at most: left out of the spike rule's median


def spike_median(st):
    """The spike rule's median: over the MOVING steps only (> MOVING_DEG), the two largest left out (a one-frame
    spike is two steps: out and back). A frozen hold's ~0 steps no longer pull the median to 0 (every fast beat after
    a hold was flagged), and a lone spike after a hold cannot set its own bar (its two steps alone: median 0, so it
    is flagged). fit.pop mirrors it."""
    mv = np.sort(st[st > MOVING_DEG])
    return float(np.median(mv[:-2])) if len(mv) > 2 else 0.0


LONE_X, BACK = 2.5, 0.5


def out_of_line(R, st, k, loop):
    """A pop is a step out of line with its neighbours: a lone jump (over LONE_X times the larger neighbour step) or
    an out-and-back (two steps whose net turn is under BACK of their sum). A burst that builds and settles over a few
    frames (a shove off a frozen hold: 8, 14.5, 4 deg) is neither, however fast. fit.pop mirrors it."""
    n = len(st)
    nb = lambda i: st[i % n] if loop or 0 <= i < n else 0.0  # noqa: E731
    if st[k] > LONE_X * max(nb(k - 1), nb(k + 1)):
        return True
    for a in (k - 1, k):
        if loop or (a >= 0 and a + 1 < n):
            if ang(R[a % n], R[(a + 2) % n] if loop else R[a + 2]) < BACK * (nb(a) + nb(a + 1)):
                return True
    return False


AXILLA = 0.4   # the upper arm's first 40% along its axis: the armpit fold (skin/weights, not the clip), reported apart


def mats(a):
    a = np.asarray(a, float).reshape(-1, 3, 4)
    m = np.zeros((len(a), 4, 4))
    m[:, :3] = a
    m[:, 3, 3] = 1
    return m


def ang(Ra, Rb):
    """Angle between rotations, deg (the dump's 5-decimal matrices orthonormalized first: their raw trace has a
    ~0.3 deg floor)."""
    from scipy.spatial.transform import Rotation
    sh = np.shape(Ra)[:-2]
    a = Rotation.from_matrix(np.reshape(Ra, (-1, 3, 3)))
    b = Rotation.from_matrix(np.reshape(Rb, (-1, 3, 3)))
    return np.degrees((a.inv() * b).magnitude()).reshape(sh)


def classes(p):
    """(arm vertex mask per side, hand vertex mask per side, torso vertex mask) by dominant bone."""
    dom = np.array([p.names[k] for k in np.argmax(p.D, 1)])
    body = p.piece == "body"
    arm = {s: body & np.array([d.startswith(ARM) and d.endswith("_" + s) for d in dom]) for s in "lr"}
    hand = {s: body & np.array([d.startswith(ARM[2:]) and d.endswith("_" + s) for d in dom]) for s in "lr"}
    # the torso: dominant torso bone AND under a third girdle/arm share. Weights v5 (CLAV front_below) left ~100 of
    # the shoulder part's front points dominant spine_04 while the girdle still moves them: as "torso" they put the
    # armpit fold's own skin inside it (axilla 50 -> 173-200 points at the 30 mm cap) and flipped the elbow's sign
    # (-91 against A's 219), a reading, not a penetration (P1 A shoulder, round 12)
    gi = [k for k, n in enumerate(p.names) if n.startswith(GIRDLE)]
    torso = body & np.array([d.startswith(TORSO) for d in dom]) & (p.D[:, gi].sum(1) < 1.0 / 3.0)
    return arm, hand, torso


def vnormals(V, T):
    n = np.zeros_like(V)
    f = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3):
        np.add.at(n, T[:, k], f)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def signed(V, N, tree, tidx, P):
    d, i = tree.query(P)
    q = tidx[i]
    return np.einsum("ij,ij->i", P - V[q], N[q]), d, q


class Body:
    """A poser posed from skeleton-space globals (Godot's) of its own bones."""

    def __init__(self, glb, rig, names, rest_dump, laws):
        self.p = make_poser("lbs", glb, rig)
        self.rig, self.laws = rig, laws
        if not laws:
            self.p.driver = type("NoLaws", (), {"drive": staticmethod(lambda p, G, r: (G, {}))})
        self.map = [self.p.index.get(n, -1) for n in names]
        j = names.index("pelvis")
        self.X = self.p.rest[self.p.index["pelvis"]] @ np.linalg.inv(rest_dump[j])   # Godot -> glb space
        self.arm, self.hand, self.torso = classes(self.p)
        self.tidx = np.nonzero(self.torso)[0]
        self.dom = np.array([self.p.names[k] for k in np.argmax(self.p.D, 1)])
        self.helpers = set()
        for h in rig.get("helpers", []):
            for s in ("l", "r") if "{s}" in h["name"] else ("",):
                self.helpers.add(h["name"].replace("{s}", s))
        par = self.p.parent
        self.order, seen = [], set()

        def visit(k):
            if k in seen:
                return
            if par[k] >= 0:
                visit(par[k])
            seen.add(k)
            self.order.append(k)
        for k in range(len(self.p.names)):
            visit(k)
        self.cache = {}

    def pose(self, Gd, keyed, f):
        if f in self.cache:
            return self.cache[f]
        p = self.p
        G = p.rest.copy()
        got = np.zeros(len(G), bool)
        for a, k in enumerate(self.map):
            if k >= 0:
                G[k] = self.X @ Gd[a]
                got[k] = True
        for k in self.order:   # bones the dump lacks, and (with the laws) unkeyed helpers: rest local, as P1Laws
            pk = p.parent[k]
            n = p.names[k]
            if pk >= 0 and (not got[k] or self.laws and n in self.helpers and n not in keyed):
                G[k] = G[pk] @ (np.linalg.inv(p.rest[pk]) @ p.rest[k])
        G, w = p.driver.drive(p, G, self.rig)
        V = p._skin(G, w)
        N = vnormals(V, p.T)
        tree = cKDTree(V[self.tidx])
        self.cache[f] = (V, G, N, tree)
        return self.cache[f]


def pops(names, parent, Gs, keyed, loop):
    out, worst, seam = {}, (0.0, "", 0), (0.0, "")
    for n in keyed:
        j = names.index(n)
        pj = parent[j]
        R = Gs[:, j, :3, :3] if pj < 0 else np.linalg.inv(Gs[:, pj, :3, :3]) @ Gs[:, j, :3, :3]
        st = ang(R[:-1], R[1:])
        med = spike_median(st)
        k = int(np.argmax(st))
        # (the largest step over 3 deg and SPIKE_X times the moving median that is also out of line with its neighbours)
        bad = [i for i in np.argsort(-st) if st[i] > SPIKE_DEG and st[i] > SPIKE_X * max(med, 1e-6)]
        bad = next((i for i in bad if out_of_line(R, st, int(i), loop)), None)
        if bad is not None:
            out[n] = {"frame": int(bad) + 1, "step": round(float(st[bad]), 2), "median": round(med, 3)}
        if st[k] > worst[0]:
            worst = (float(st[k]), n, k + 1)
        if loop:
            s = float(ang(R[-1], R[0]))
            if s > seam[0]:
                seam = (s, n)
    return out, worst, seam


def feet(d, Ga, Gb):
    """The foot lock's windows (P1Bake.FootLock, mirrored): A's ball within 2 cm of its clip floor, wrapping for cycles
    (the last key is the first), each window trimmed at its ends while A's ball or ankle (the one A holds longest)
    leaves its belt-riding anchor by > 10 mm; drift = that point's horizontal excursion, belt out, A and B."""
    an, bn = d["a_names"], d["b_names"]
    fps = d["fps"]
    n = len(Ga)
    m = n - 1 if d["loop"] and n > 2 else n
    res = {}
    pts = {s: [(an.index(f"ball_{s}"), bn.index(f"ball_{s}")), (an.index(f"foot_{s}"), bn.index(f"foot_{s}"))] for s in "lr"}
    floor = min(Ga[:m, pts[s][0][0], 1, 3].min() for s in "lr")
    planted = {s: Ga[:m, pts[s][0][0], 1, 3] < floor + 0.02 for s in "lr"}
    vel = []
    for s in "lr":
        P = Ga[:m, pts[s][0][0], :3, 3]
        for f in range(m if d["loop"] else m - 1):
            g = (f + 1) % m
            if planted[s][f] and planted[s][g]:
                vel.append((P[g] - P[f]) * fps)
    vel = np.array(vel) if vel else np.zeros((1, 3))
    belt = np.array([np.sort(vel[:, 0])[len(vel) // 2], 0, np.sort(vel[:, 2])[len(vel) // 2]])
    if np.linalg.norm(belt) < 0.05:
        belt = np.zeros(3)
    res["belt_mps"] = round(float(np.linalg.norm(belt)), 2)

    def hold(P, idx):
        t = np.arange(len(idx))[:, None] / fps
        r = P[idx] - P[idx[0]] - belt * t
        return float(np.linalg.norm(r[:, [0, 2]], axis=1).max())

    for s in "lr":
        c = planted[s]
        out = {"A": 0.0, "B": 0.0, "windows": 0, "B_lift_mm": 0.0}
        wins = []
        if c.all():
            wins = [list(range(m))]
        else:
            st = int(np.argmin(c)) if d["loop"] else 0
            k = 0
            while k < m:
                f = (st + k) % m
                if c[f] and (k == 0 and not d["loop"] or not c[(f - 1) % m] or k == 0 and False):
                    w = []
                    while len(w) < m and c[(f + len(w)) % m] and (d["loop"] or f + len(w) < m):
                        w.append((f + len(w)) % m)
                    wins.append(w)
                    k += len(w)
                else:
                    k += 1
        if c.all() and np.linalg.norm(belt) > 1e-6:
            wins = []
        for w in wins:
            best = None
            for pi, (ja, jb) in enumerate(pts[s]):
                PA = Ga[:, ja, :3, 3]
                s0, l0 = 0, len(w)
                while l0 >= 2 and hold(PA, w[s0:s0 + l0]) > 0.01:
                    if hold(PA, w[s0 + 1:s0 + l0]) <= hold(PA, w[s0:s0 + l0 - 1]):
                        s0 += 1
                    l0 -= 1
                if l0 >= 2 and (best is None or l0 > best[1]):
                    best = (s0, l0, ja, jb)
            if best is None:
                continue
            s0, l0, ja, jb = best
            idx = w[s0:s0 + l0]
            out["windows"] += 1
            out["A"] = max(out["A"], hold(Ga[:, ja, :3, 3], idx) * 1000)
            out["B"] = max(out["B"], hold(Gb[:, jb, :3, 3], idx) * 1000)
            hb = Gb[idx, jb, 1, 3]
            out["B_lift_mm"] = max(out["B_lift_mm"], float((hb.max() - hb.min()) * 1000))
        res[s] = {k: round(v, 1) if isinstance(v, float) else v for k, v in out.items()}
    return res


def arm_read(body, Gd, frames, keyed):
    p = body.p
    el = {s: [] for s in "lr"}
    eb = {s: [] for s in "lr"}
    for f in frames:
        V, G, N, tree = body.pose(Gd[f], keyed, f)
        for s in "lr":
            u, l = p.index[f"upperarm_{s}"], p.index[f"lowerarm_{s}"]
            dv = G[l][:3, 3] - G[u][:3, 3]
            el[s].append(float(np.degrees(np.arccos(np.clip(-dv[1] / np.linalg.norm(dv), -1, 1)))))
            eb[s].append(float(signed(V, N, tree, body.tidx, G[l][:3, 3][None])[0][0] * 1000))
    return {s: {"elev_min": round(min(el[s]), 1), "elev_mean": round(float(np.mean(el[s])), 1),
                "elbow_mm_min": round(min(eb[s]), 1), "elbow_mm_mean": round(float(np.mean(eb[s])), 1)} for s in "lr"}


def contact(body, Gd, frames, keyed):
    p = body.p
    out = {s: {"inside": 0, "depth_mm": 0.0, "frame": -1, "hand_gap_mm": 1e9, "axilla": 0, "axilla_mm": 0.0} for s in "lr"}
    for f in frames:
        V, G, N, tree = body.pose(Gd[f], keyed, f)
        for s in "lr":
            ai = np.nonzero(body.arm[s])[0]
            u = G[p.index[f"upperarm_{s}"]][:3, 3]
            lo = G[p.index[f"lowerarm_{s}"]][:3, 3]
            ax = (lo - u) / np.linalg.norm(lo - u)
            along = (V[ai] - u) @ ax
            axil = along < AXILLA * np.linalg.norm(lo - u)
            sd, dist, q = signed(V, N, tree, body.tidx, V[ai])
            ins_all = (sd < 0) & (dist < 0.03)
            ins = ins_all & ~axil
            o = out[s]
            ia = ins_all & axil
            o["axilla"] = max(o["axilla"], int(ia.sum()))
            if ia.any():
                o["axilla_mm"] = max(o["axilla_mm"], float(-sd[ia].min() * 1000))
            o["inside"] = max(o["inside"], int(ins.sum()))
            if ins.any() and -sd[ins].min() * 1000 > o["depth_mm"]:
                o["depth_mm"] = float(-sd[ins].min() * 1000)
                o["frame"] = f
                k = int(np.argmin(np.where(ins, sd, 1)))
                o["where"] = f"{body.dom[ai[k]]}>{body.dom[q[k]]}"
            hi = np.nonzero(body.hand[s])[0]
            o["hand_gap_mm"] = min(o["hand_gap_mm"], float(signed(V, N, tree, body.tidx, V[hi])[0].min() * 1000))
    return {s: {k: round(v, 1) if isinstance(v, float) else v for k, v in o.items()} for s, o in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--step", type=int, default=0, help="pose every Nth key (default: about 30 poses per clip)")
    ap.add_argument("--dump", default=str(DUMP), help="the keys dump folder (default tools/body/out/clips)")
    ap.add_argument("--p1", default=None, help="B's published folder (default godot/art/people/body_p1; a slider variant's body_p1_var/NAME)")
    ap.add_argument("--no-a", action="store_true", help="skip A's arm read")
    a = ap.parse_args()
    P1 = Path(a.p1) if a.p1 else globals()["P1"]
    rig = json.loads((P1 / "rig.json").read_text())
    B = A = None
    report = {}
    for name in a.clips:
        d = json.loads((Path(a.dump) / f"{name}.json").read_text())
        Ga = np.stack([mats(f) for f in d["A"]])
        Gb = np.stack([mats(f) for f in d["B"]])
        bn, bp = d["b_names"], d["b_parent"]
        keyed = set(d["keyed"])
        if B is None:
            B = Body(str(P1 / "body.glb"), rig, bn, mats(d["b_rest"]), True)
        if A is None and not a.no_a:
            A = Body(str(REPO / "godot/art/people/heroine.glb"), {}, d["a_names"], mats(d["a_rest"]), False)
        B.cache.clear()
        if A is not None:
            A.cache.clear()
        n = len(Gb)
        step = a.step or max(1, n // 30)
        frames = list(range(0, n, step))
        sp, worst, seam = pops(bn, bp, Gb, d["keyed"], d["loop"])
        r = {"frames": n, "posed": len(frames), "loop": d["loop"],
             "pops": sp, "worst_step": [round(worst[0], 2), worst[1], worst[2]],
             "seam_deg": [round(seam[0], 3), seam[1]] if d["loop"] else None,
             "feet": feet(d, Ga, Gb),
             "body": contact(B, Gb, frames, keyed),
             "arms_B": arm_read(B, Gb, frames, keyed)}
        if A is not None:
            r["arms_A"] = arm_read(A, Ga, frames, set(d["a_names"]))
            r["body_A"] = contact(A, Ga, frames, set(d["a_names"]))
        an = d["a_names"]
        ak = [k for k in d["keyed"] if k in an]
        spa, wa, _ = pops(an, d["a_parent"] if "a_parent" in d else None, Ga, ak, d["loop"]) if "a_parent" in d else ({}, (0, "", 0), 0)
        r["pops_A"] = spa
        report[name] = r
        f, b = r["feet"], r["body"]
        print(f"{name}: pops {len(sp)} (worst {worst[0]:.1f} deg {worst[1]} @{worst[2]}), seam {r['seam_deg']}, "
              f"feet drift A/B mm L {f['l']['A']}/{f['l']['B']} R {f['r']['A']}/{f['r']['B']} (belt {f['belt_mps']}), "
              f"inside L {b['l']['inside']}/{b['l']['depth_mm']}mm@{b['l']['frame']} R {b['r']['inside']}/{b['r']['depth_mm']}mm@{b['r']['frame']}, "
              f"[{b['l'].get('where')} {b['r'].get('where')}] axilla L {b['l']['axilla']}/{b['l']['axilla_mm']:.1f} R {b['r']['axilla']}/{b['r']['axilla_mm']:.1f}mm, hand gap L {b['l']['hand_gap_mm']} R {b['r']['hand_gap_mm']} mm")
        for who in ("arms_B", "arms_A"):
            if who in r:
                print(f"   {who}: " + "  ".join(f"{s}: elev {v['elev_min']}/{v['elev_mean']} elbow {v['elbow_mm_min']}/{v['elbow_mm_mean']}mm"
                                             for s, v in r[who].items()))
        if "body_A" in r:
            print("   body_A: " + "  ".join(f"{s}: inside {v['inside']}/{v['depth_mm']}mm {v.get('where')} hand gap {v['hand_gap_mm']}" for s, v in r["body_A"].items()))
        if sp:
            print("   spikes: " + ", ".join(f"{k} {v['step']}@{v['frame']} (med {v['median']}; A {r['pops_A'].get(k, {}).get('step', '-')})" for k, v in list(sp.items())[:8]))
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "clipcheck.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
