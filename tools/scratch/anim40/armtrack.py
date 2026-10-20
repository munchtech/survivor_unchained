"""Right (and left) arm track over a town idle, against idle_warden_town (animation 44, solver idle 2).
usage: python armtrack.py <clip> [<clip> ...]
Per clip and side: the wrist's travel (cm, the largest peak-to-peak axis, in her root's space and in the chest's), the
shoulder abduction (deg, the upper arm out from the chest's down axis in its frontal plane: min-max), its flexion
(forward, deg), the elbow bend (deg), and the wrist's height above the ground and out from her side (cm) at 0/25/50/75%."""
import sys, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parents[3] / "tools" / "anim"
sys.path.insert(0, str(HERE))
from skin import Body  # noqa

b = Body.heroine(jiggle=False, helpers=True)
I = b.sk.index


def ang(u, v):
    return math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))


for name in sys.argv[1:]:
    clip = b.clip(name)
    Gr = b.globals(type(clip)(clip.name, clip.fps, np.tile(b.sk.rest_rot, (1, 1, 1)).astype(float), np.tile(b.sk.rest_pos, (1, 1, 1)).astype(float), False, {}), 0)
    R3 = Gr[I["spine_03"]][:3, :3]
    Gs = [b.globals(clip, f) for f in range(clip.frames)]
    n = len(Gs)
    for sd, sg in (("r", -1), ("l", 1)):
        W, Wc, ab, fl, el = [], [], [], [], []
        for G in Gs:
            P = lambda k: G[I[k]][:3, 3]
            R = G[I["spine_03"]][:3, :3] @ R3.T
            down, left, fwd = R @ [0, -1, 0], R @ [1, 0, 0], R @ [0, 0, 1]
            arm = P(f"lowerarm_{sd}") - P(f"upperarm_{sd}")
            ab.append(math.degrees(math.atan2(sg * arm @ left, arm @ down)))
            fl.append(math.degrees(math.atan2(arm @ fwd, arm @ down)))
            el.append(ang(arm, P(f"hand_{sd}") - P(f"lowerarm_{sd}")))
            W.append(P(f"hand_{sd}"))
            Wc.append(np.linalg.inv(G[I["spine_03"]]) @ np.append(P(f"hand_{sd}"), 1))
        W, Wc = np.array(W), np.array(Wc)[:, :3]
        q = [int(n * k / 4) for k in range(4)]
        side = [sg * (W[i] - Gs[i][I["pelvis"]][:3, 3])[0] for i in q]
        print(f"{name:22} {sd}: wrist travel root {100 * np.ptp(W, axis=0).max():.1f} cm (x {100 * np.ptp(W[:, 0]):.1f} y {100 * np.ptp(W[:, 1]):.1f} z {100 * np.ptp(W[:, 2]):.1f}) "
              f"chest {100 * np.ptp(Wc, axis=0).max():.1f} | abd {min(ab):+.0f}..{max(ab):+.0f} flex {min(fl):+.0f}..{max(fl):+.0f} elbow {min(el):.0f}-{max(el):.0f} | "
              f"wrist h " + "/".join(f"{100 * W[i][1]:.0f}" for i in q) + " out " + "/".join(f"{100 * s:.0f}" for s in side))
