"""calf_radii.py GLB [GLB...]: a body's calf, for SideCarry's blade-calf capsule (CalfKnee, CalfAnkle) and the ankle
height. Bind-space skin: vertices whose largest weights are the calf's (calf_* and calf_twist_*), radial distance from the
knee-ankle line; the radius at the knee band (10-25% down) and the ankle band (75-90%), 90th percentile, both legs
averaged; the ankle (foot bone head) height over the lowest foot vertex. Prints the ratio of each to the first file's, so
a body's capsule is the first body's tuned numbers times its own ratio (carry_targets.json 'runtime_body_constants')."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "body"))
from gl import Glb

def read(path):
    g = Glb(path); sk = g.skeleton()
    bind = {n: np.linalg.inv(sk.ibm[i])[:3, 3] for i, n in enumerate(sk.names)}
    out = {}
    for side in "lr":
        calf = [i for i, n in enumerate(sk.names) if n.startswith("calf") and n.endswith("_" + side)]
        foot = [i for i, n in enumerate(sk.names) if (n.startswith("foot") or n.startswith("ball")) and n.endswith("_" + side)]
        knee, ankle = bind["calf_" + side], bind["foot_" + side]
        P, w = [], []
        F = []
        for m in g.meshes:
            if m.skin is None or m.J is None: continue
            wc = np.where(np.isin(m.J, calf), m.W, 0).sum(1)
            wf = np.where(np.isin(m.J, foot), m.W, 0).sum(1)
            P.append(m.P[wc > 0.5]); F.append(m.P[wf > 0.5])
        P = np.concatenate(P).astype(float); F = np.concatenate(F).astype(float)
        ax = ankle - knee; L = np.linalg.norm(ax); u = ax / L
        t = (P - knee) @ u / L; r = np.linalg.norm((P - knee) - np.outer((P - knee) @ u, u), axis=1)
        k = np.percentile(r[(t > 0.10) & (t < 0.25)], 90); a = np.percentile(r[(t > 0.75) & (t < 0.90)], 90)
        out[side] = (k, a, ankle[1] - F[:, 1].min(), L)
    return {k: float(np.mean([out[s][i] for s in "lr"])) for i, k in enumerate(("knee", "ankle", "ankle_h", "calf_len"))}

ref = None
for p in sys.argv[1:]:
    r = read(p); ref = ref or r
    print(Path(p).parent.name + "/" + Path(p).name, "  ".join(f"{k} {v:.4f} (x{v / ref[k]:.3f})" for k, v in r.items()))
