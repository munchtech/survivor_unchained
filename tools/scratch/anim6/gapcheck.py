"""Garments against her skin with the helpers: each garment point's split
against its nearest skin point's, and whether skin comes through a garment
in set poses, before the helpers and with them.

    python -u gapcheck.py [outfits...]
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
from sweep import S, WT, pose, elbow, knee, wrist_turn, arm_twist, arm_raise  # noqa: E402
from rigtest import arm_forward, thigh_forward  # noqa: E402
from rig import Skeleton  # noqa: E402
from skin import Body  # noqa: E402
import motion  # noqa: E402
import helpers as hp  # noqa: E402


def both(fn, *a):
    return [fn("l", *a), fn("r", *a)]


POSES = {
    "elbow 90": both(elbow, 90), "elbow 120": both(elbow, 120), "elbow 145": both(elbow, 145),
    "elbow 90 wrist +80": both(elbow, 90) + [wrist_turn("l", 80, 0.5), wrist_turn("r", 80, 0.5)],
    "elbow 90 wrist -80": both(elbow, 90) + [wrist_turn("l", -80, 0.5), wrist_turn("r", -80, 0.5)],
    "arm twist +70": both(arm_twist, 70), "arm twist -70": both(arm_twist, -70),
    "arm raised 100": both(arm_raise, 100), "arm raised 130": both(arm_raise, 130),
    "arm forward 90 elbow 45": both(arm_forward, 90) + both(elbow, 45),
    "knee 90": both(knee, 90), "knee 145": both(knee, 145),
    "hip 110 knee 135": both(thigh_forward, 110) + both(knee, 135),
}


def load(which, outfit):
    if which == "before":
        sk = Skeleton.load(S / "before" / "data" / "heroine_skeleton.json")
        d = S / "before" / "people"
    else:
        sk = Skeleton.load(WT / "tools" / "anim" / "data" / "heroine_skeleton.json")
        d = WT / "godot" / "art" / "people"
    files = [(d / "heroine.glb", lambda n: n == "Heroine", "skin"),
             (d / f"heroine_outfit_{outfit}.gltf", lambda n, o=outfit: n.startswith(o + "."), "garment")]
    return Body(sk, files, None, helpers=which != "before")


def dense(b, idx):
    D = np.zeros((len(idx), len(b.sk.names)))
    for k in range(4):
        np.add.at(D, (np.arange(len(idx)), b.J[idx, k]), b.W[idx, k])
    return D


def run(outfit):
    out = {}
    res = {}
    fixed = None   # the same garment points judged in both builds (the before's limb set)
    masks = {}
    for which in ("before", "after"):
        t0 = time.time()
        b = load(which, outfit)
        skin = np.nonzero(b.kind == "skin")[0]
        gar = np.nonzero(b.kind == "garment")[0]
        T = b.T[np.isin(b.T[:, 0], skin)]
        surf = motion.Surface(T, len(b.P))
        # Only garment points the helpers can move: near a limb (their
        # nearest skin point's weight mostly on an arm or a leg).
        tree = cKDTree(b.P[skin])
        dist0, ns = tree.query(b.P[gar], k=1)
        ns = skin[ns]
        limb = (b.part[ns] != 0) | (b.part[gar] != 0)
        if fixed is None:
            fixed = limb
        else:
            assert len(fixed) == len(limb), "garment point counts differ between builds"
            limb = fixed
        gar, ns, dist0 = gar[limb], ns[limb], dist0[limb]
        if which == "after":
            # The split's agreement: helper weight on a garment point against
            # its nearest skin point's.
            H = [b.sk.index[n] for n in hp.names() if n in b.sk.index]
            dg, ds = dense(b, gar), dense(b, ns)
            diff = np.abs(dg[:, H] - ds[:, H]).sum(1)
            near = dist0 < 0.02
            out["split"] = {"points": int(len(gar)), "within_2cm": int(near.sum()),
                            "helper_L1_median": float(np.median(diff[near])), "helper_L1_p95": float(np.percentile(diff[near], 95)),
                            "helper_L1_max": float(diff[near].max()),
                            "all_L1_p95": float(np.percentile(np.abs(dg - ds).sum(1)[near], 95))}
        surf.pose(b.P)
        d_rest, _ = surf.signed(b.P, b.P[gar])
        res[which] = {}
        for name, edits in POSES.items():
            G = pose(b, edits)
            P = b.pose(G)
            surf.pose(P)
            d, _ = surf.signed(P, P[gar])
            ok = np.isfinite(d) & np.isfinite(d_rest) & (d_rest > 0.0005)
            inside = ok & (d < 0)
            masks[(which, name)] = inside
            res[which][name] = (int(inside.sum()), float(-d[inside].min()) * 1000 if inside.any() else 0.0,
                                float(np.percentile((d - d_rest)[ok], 1)) * 1000)
        print(f"  {outfit} {which}: {time.time() - t0:.0f} s", flush=True)
    out["poses"] = res
    out["moved"] = {n: (int((masks[("after", n)] & ~masks[("before", n)]).sum()),
                        int((masks[("before", n)] & ~masks[("after", n)]).sum())) for n in POSES}
    return out


if __name__ == "__main__":
    outfits = sys.argv[1:] or ["warden", "arcanist", "ranger", "reaver"]
    for o in outfits:
        r = run(o)
        s = r["split"]
        print(f"{o}: split on {s['points']} limb points ({s['within_2cm']} within 2 cm of skin): helper weight off its skin point's "
              f"median {s['helper_L1_median']:.3f}, p95 {s['helper_L1_p95']:.3f}, max {s['helper_L1_max']:.3f} (all weights p95 {s['all_L1_p95']:.3f})")
        print(f"  {'pose':26s} | skin through garment: before (points, deepest mm, gap 1st pct change mm) | after | new, cured")
        for name in POSES:
            a, b_ = r["poses"]["before"][name], r["poses"]["after"][name]
            print(f"  {name:26s} | {a[0]:6d} {a[1]:5.1f} {a[2]:6.1f} | {b_[0]:6d} {b_[1]:5.1f} {b_[2]:6.1f} | {r['moved'][name][0]:6d} {r['moved'][name][1]:6d}")
