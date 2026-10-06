"""Where a held blade goes through her body: python blade.py <clip names...> [--before]
For each frame: the blade's segment (grip to tip, along the diagonal grip's
line, keyed.GRIP) against capsules round her thighs, shins, hips and trunk.
Reports frames where the blade passes inside a capsule (cm of depth)."""
import math
import sys
from pathlib import Path

W = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(W))
import numpy as np  # noqa: E402
import audit  # noqa: E402
from keyed import GRIP  # noqa: E402
from rig import DATA, Skeleton, qaxis, qmul, qrot  # noqa: E402

# Length beyond the fist, by weapon (anim_review's: length * (1 - grip)).
REACH = {"sword": 0.80, "axe": 0.68, "daggers": 0.32, "wand": 0.33}
CAPS = [("thigh_l", "calf_l", 0.075), ("thigh_r", "calf_r", 0.075), ("calf_l", "foot_l", 0.055),
        ("calf_r", "foot_r", 0.055), ("pelvis", "spine_02", 0.13), ("spine_02", "neck_01", 0.12),
        ("thigh_l", "thigh_r", 0.10), ("neck_01", "Head", 0.07)]


def seg_seg(p1, q1, p2, q2):
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    c, b = d1 @ r, d1 @ d2
    den = a * e - b * b
    s = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 else 0.0
    t = (b * s + f) / e
    if t < 0:
        t, s = 0.0, np.clip(-c / a, 0, 1)
    elif t > 1:
        t, s = 1.0, np.clip((b - c) / a, 0, 1)
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t))), s


def main(argv):
    want = [a for a in argv if not a.startswith("--")]
    sets = audit.SETS[:2]
    if "--before" in argv:
        B = Path(__file__).parent / "out_before"
        sets = [(l, B / f.name, s) for l, f, s in sets]
    for label, folder, skel in sets:
        sk = Skeleton.load(DATA / skel)
        I = sk.index
        for fp in sorted(folder.glob("*.json")):
            if want and not any(w == fp.stem for w in want):
                continue
            d, rot, pos = audit.load(fp, sk)
            weapon = (d.get("meta") or {}).get("weapon", "")
            main_w = weapon.split("+")[0]
            if main_w not in REACH:
                print(f"{label} {fp.stem}: no blade ({weapon!r})")
                continue
            g, p = sk.fk(rot, pos)
            sides = "rl" if main_w in ("axes", "daggers") else "r"
            lean = GRIP.get("axe" if main_w == "axes" else main_w, 0.0) if "--square" not in argv else 0.0
            lq = qaxis([1.0, 0, 0], -lean)
            hits = []
            for s in sides:
                h = I[f"hand_{s}"]
                for f in range(rot.shape[0]):
                    q = qmul(g[f, h], lq)
                    a = p[f, h] + qrot(g[f, h], [-0.025, 0.075, 0.0])
                    b = a + qrot(q, [0, 0, 1.0]) * REACH[main_w]
                    worst = None
                    for j0, j1, r in CAPS:
                        dist, s_ = seg_seg(a, b, p[f, I[j0]], p[f, I[j1]])
                        depth = r + 0.01 - dist
                        if depth > 0 and s_ > 0.12 and (worst is None or depth > worst[0]):
                            worst = (depth, j0)
                    if worst:
                        hits.append(f"{s}f{f}:{worst[1]} {100 * worst[0]:.0f}")
            print(f"{label} {fp.stem}: {len(hits)} frames through her" + (": " + ", ".join(hits[:14]) if hits else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
