"""Joint volume and ridge sharpness for helper variants, split in Python on the
before body (as the build would split it).

    python -u sweep2.py
Each variant: (name, profile, elbow bulge, elbow max, knee bulge, knee max, shoulder bulge, shoulder max).
Ridge: the sharpest folds of her skin round the joint (99.5th percentile and
max of the angle between neighbouring faces, degrees), against the same at rest.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from sweep import WT  # noqa: E402  (puts tools/anim on the path)
import helpers as hp  # noqa: E402
from sweep import body, pose, Regions, elbow, knee, arm_raise, arm_twist, wrist_turn  # noqa: E402
from rigtest import thigh_forward  # noqa: E402

VARIANTS = [
    ("before", None, 0, 1, 0, 1, 0, 1),
    ("smooth b0", "smooth", 0, 1, 0, 1, 0, 1),
    ("smooth r.7", "smooth", 0.7, 2, 0.7, 2, 0, 1),
    ("smooth r1", "smooth", 1, 2, 1, 2, 0, 1),
]


def both(fn, *a):
    return [fn("l", *a), fn("r", *a)]


POSES = [("elbow 90", both(elbow, 90), "elbow"), ("elbow 120", both(elbow, 120), "elbow"), ("elbow 145", both(elbow, 145), "elbow"),
         ("knee 90", both(knee, 90), "knee"), ("knee 120", both(knee, 120), "knee"), ("knee 145", both(knee, 145), "knee"),
         ("hip 110 knee 135", both(thigh_forward, 110) + both(knee, 135), "knee"),
         ("raise 100", both(arm_raise, 100), "shoulder"), ("raise 130", both(arm_raise, 130), "shoulder"),
         ("twist 70", both(arm_twist, 70), "shoulder"), ("elbow 90 wrist 80", both(elbow, 90) + [wrist_turn("l", 80, .5), wrist_turn("r", 80, .5)], "wrist")]


def edges_of(T):
    """Pairs of faces sharing an edge."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    f = np.tile(np.arange(len(T)), 3)
    e = np.sort(e, 1)
    key = e[:, 0].astype(np.int64) * 10_000_000 + e[:, 1]
    o = np.argsort(key)
    k, f = key[o], f[o]
    same = k[1:] == k[:-1]
    return np.stack([f[:-1][same], f[1:][same]], 1)


def ridge(P, T, pairs):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    c = np.clip((n[pairs[:, 0]] * n[pairs[:, 1]]).sum(1), -1, 1)
    a = np.degrees(np.arccos(c))
    return float(np.percentile(a, 99.5)), float(a.max())


def setspec(v):
    _, prof, eb, em, kb, km, sb, sm = v
    hp.SPEC["weights"]["profile"] = prof or "tent"
    for h in hp.SPEC["helpers"]:
        if h["name"].startswith("lowerarm_share"):
            h["bulge"], h["bulge_max"] = eb, em
        elif h["name"].startswith("calf_share"):
            h["bulge"], h["bulge_max"] = kb, km
        elif h["name"].startswith("upperarm_share"):
            h["bulge"], h["bulge_max"] = sb, sm


if __name__ == "__main__":
    out = {}
    for v in VARIANTS:
        setspec(v)
        b = body("before" if v[1] is None else "proto")
        R = Regions(b)
        rest = R.volumes(b.P, b.rest)
        regs = {**R.m.regions(), **R.extra}
        # The outer side of each hinge only (the elbow's back, the knee's
        # front: where a point would show), 2 cm out from the joint.
        _, rp = b.sk.rest_globals()
        for key in list(regs):
            T, j = regs[key]
            out_dir = {"elbow": -1.0, "knee": 1.0}.get(key[0])
            if out_dir is None:
                continue
            c = b.P[T].mean(1) - rp[0, j]
            regs[key] = (T[c[:, 2] * out_dir > 0.02], j)
        pairs = {k: edges_of(T) for k, (T, _) in regs.items()}
        rest_r = {k: ridge(b.P, regs[k][0], pairs[k]) for k in regs}
        rows = []
        for name, edits, joint in POSES:
            G = pose(b, edits)
            P = b.pose(G)
            vol = R.volumes(P, G)
            cells = []
            for s in "l":
                key = (joint, s)
                r = ridge(P, regs[key][0], pairs[key])
                cells.append(f"vol {100 * vol[key] / rest[key]:5.1f}% ridge {r[0]:4.0f}/{r[1]:4.0f} (rest {rest_r[key][0]:3.0f}/{rest_r[key][1]:3.0f})")
            rows.append((name, cells))
        out[v[0]] = rows
        print("done", v[0], flush=True)
    for i, (name, _, _) in enumerate(POSES):
        print(f"== {name}")
        for vn, rows in out.items():
            print(f"   {vn:16s} {' | '.join(rows[i][1])}")
