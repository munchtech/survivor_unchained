"""The free space round her hips in the pelvis's rest frame (animation 44, solver idle 2): over every frame of a set of
clips, on a 1.5 cm grid, the least signed distance to her skin (arms left out; - inside), and per phase (idle / run /
sprint, the clip's first word) the least distance to either hand (hand, fingers, thumb, forearm within 8 cm of the
wrist). A piece fixed to the pelvis is then scored by reading the grid at its points (socksearch.py --field).
usage: python sockfield.py axe|wand   (writes sockfield_<kind>.npz here)"""
import sys, math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[3] / "tools" / "anim"
sys.path.insert(0, str(HERE))
import armscheck as ac  # noqa
import skin  # noqa

kind = sys.argv[1]
outfit = "reaver" if kind == "axe" else "arcanist"
CL = {"axe": ["idle_reaver_town", "run_reaver_town", "sprint_reaver_town"],
      "wand": ["idle_arcanist_town", "run_arcanist_wand_town", "sprint_arcanist_wand_town"]}[kind]
c, s = math.cos(math.radians(20.6)), math.sin(math.radians(20.6))
REST = np.eye(4); REST[:3, :3] = [[1, 0, 0], [0, c, -s], [0, s, c]]; REST[:3, 3] = [0, 1.0723, 0]
ck = ac.Checker(outfit)
b, I, vb = ck.b, ck.I, ck.vbone
cover = ck.cover if ck.cover is not None else np.zeros(len(b.P))
FING = ("index", "middle", "ring", "pinky", "thumb")
armish = np.array([n.split("_")[0] in ("upperarm", "lowerarm", "hand") + FING for n in vb])
HAND = {sd: np.array([n.endswith("_" + sd) and (n.startswith("hand") or n.split("_")[0] in FING) for n in vb]) for sd in "lr"}
FORE = {sd: vb == f"lowerarm_{sd}" for sd in "lr"}
ax = [np.arange(-0.42, 0.42 + 1e-6, 0.015), np.arange(0.10, 1.30 + 1e-6, 0.015), np.arange(-0.45, 0.30 + 1e-6, 0.015)]
grid = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
skin_d = np.full(len(grid), 9.0)
out_d = np.full(len(grid), 9.0)
hand = {ph: np.full(len(grid), 9.0) for ph in ("idle", "run", "sprint")}
for name in CL:
    Gs = b.frames(b.clip(name))
    ph = name.split("_")[0]
    st = 3 if ph == "idle" else 1
    for f in range(0, len(Gs), st):
        G = Gs[f]
        P = b.pose(G)
        N = skin._normals(P, ck.m.Tskin)
        T = REST @ np.linalg.inv(G[I["pelvis"]])
        X = P @ T[:3, :3].T + T[:3, 3]
        NX = N @ T[:3, :3].T
        body = ~armish
        BX, BN, BC = X[body], NX[body], cover[body]
        d, i = cKDTree(BX).query(grid, k=4)
        # sign by the 4 nearest vertices' normals (a vote), so a point between two legs is not called inside
        sg = np.sign((((grid[:, None, :] - BX[i]) * BN[i]).sum(2)).mean(1))
        sd_ = d[:, 0] * sg
        skin_d = np.minimum(skin_d, sd_)
        out_d = np.minimum(out_d, sd_ - BC[i[:, 0]])
        for sd in "lr":
            hj = T[:3, :3] @ G[I[f"hand_{sd}"]][:3, 3] + T[:3, 3]
            m = HAND[sd] | (FORE[sd] & (np.linalg.norm(X - hj, axis=1) < 0.08))
            hand[ph] = np.minimum(hand[ph], cKDTree(X[m]).query(grid)[0])
        print(name, f, file=sys.stderr, flush=True)
sh = [len(a) for a in ax]
np.savez_compressed(Path(__file__).with_name(f"sockfield_{kind}.npz"), x=ax[0], y=ax[1], z=ax[2], skin=skin_d.reshape(sh),
                    outfit=out_d.reshape(sh), **{f"hand_{k}": v.reshape(sh) for k, v in hand.items()})
print("ok")
