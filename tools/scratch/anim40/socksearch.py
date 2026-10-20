"""Grid-search a hip socket in the pelvis's rest frame (animation 44, solver idle 2). Fast and approximate: her skin
(each frame carried into the pelvis's rest frame, so the piece stands still) against the piece's points; the winners
go to socktry.py (armscheck's exact measure).
usage: python socksearch.py axe|wand [--outfit=reaver] [--top=15]
axe: the haft top (u y 0.56) at clock angle th (12 forward, 3 her right) and radius r at height hy; the haft leans
foot-out by tb (radially) and foot-back by tt (tangentially, + toward her back centre); the blade points ph deg off
straight back (+ outward). Both sides (the left mirrored with the edge mirrored, Arms.cs HipLoop MirrorEdge).
wand: the grip (u origin) at th, r, hy; tip down (shaft = grip->crystal) leaning tb back from straight down."""
import json, sys, math, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[3] / "tools" / "anim"
sys.path.insert(0, str(HERE))
import armscheck as ac  # noqa
import skin  # noqa

kind = sys.argv[1]
opt = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--") and "=" in a)
outfit = opt.get("outfit", "reaver" if kind == "axe" else "arcanist")
CL = {"axe": ["idle_reaver_town", "run_reaver_town", "sprint_reaver_town"],
      "wand": ["idle_arcanist_town", "run_arcanist_wand_town", "sprint_arcanist_wand_town"]}[kind]
KEY = {"axe": "viking_axe@hand_r", "wand": "wand@hand_r"}[kind]
c, s = math.cos(math.radians(20.6)), math.sin(math.radians(20.6))
REST = np.eye(4); REST[:3, :3] = [[1, 0, 0], [0, c, -s], [0, s, c]]; REST[:3, 3] = [0, 1.0723, 0]

ck = ac.Checker(outfit)
b, I, vb = ck.b, ck.I, ck.vbone
cover = ck.cover if ck.cover is not None else np.zeros(len(b.P))
FING = ("index", "middle", "ring", "pinky", "thumb")
armish = np.array([n.split("_")[0] in ("upperarm", "lowerarm", "hand") + FING for n in vb])
HAND = {sd: np.array([n.endswith("_" + sd) and (n.startswith("hand") or n.split("_")[0] in FING) for n in vb]) for sd in "lr"}
FORE = {sd: vb == f"lowerarm_{sd}" for sd in "lr"}
frames = []   # (clip, f, body tree, body normals, body cover, {side: hand tree})
for name in CL:
    Gs = b.frames(b.clip(name))
    st = 6 if name.startswith("idle") else 1
    for f in range(0, len(Gs), st):
        G = Gs[f]
        P = b.pose(G)
        N = skin._normals(P, ck.m.Tskin)
        T = REST @ np.linalg.inv(G[I["pelvis"]])
        X = P @ T[:3, :3].T + T[:3, 3]
        NX = N @ T[:3, :3].T
        body = ~armish
        hands = {}
        for sd in "lr":
            hj = T[:3, :3] @ G[I[f"hand_{sd}"]][:3, 3] + T[:3, 3]
            m = HAND[sd] | (FORE[sd] & (np.linalg.norm(X - hj, axis=1) < 0.08))
            hands[sd] = cKDTree(X[m])
        frames.append((name, f, cKDTree(X[body]), X[body], NX[body], cover[body], hands))
print(f"{len(frames)} frames", file=sys.stderr)

raw = json.loads((ac.DATA / "arms_local.json").read_text())["sheathed"][KEY]
M0 = np.vstack([np.array(raw["mount"], float), [0, 0, 0, 1]])
v = ac.sample(np.array(raw["v"], float), np.array(raw["t"], int), spacing=0.015, cap=1500)
u = (np.linalg.inv(M0) @ np.c_[v, np.ones(len(v))].T).T[:, :3]
head = u[:, 1] > (0.42 if kind == "axe" else 0.20)


def unit(a):
    return a / np.linalg.norm(a)


def rowfor(th, r, hy, tb, tt, ph, left=False):
    """Socket row (At, Shaft, Thick) in skeleton rest space for the right side."""
    t = math.radians(th)
    rad = np.array([-math.sin(t), 0, math.cos(t)])          # out from her axis toward the clock angle (right = -X)
    tan = np.array([-math.cos(t), 0, -math.sin(t)]) * -1     # toward her back centre from the right side
    tan = unit(np.cross([0, 1, 0], rad))                       # (recomputed: up x radial)
    if np.dot(tan, [0, 0, -1]) < 0:
        tan = -tan
    H = np.array([0, hy, 0]) + r * rad
    if kind == "axe":
        foot = -np.array([0, 1, 0]) * math.cos(math.radians(tb)) + rad * math.sin(math.radians(tb))
        foot = unit(foot + tan * math.tan(math.radians(tt)))
        shaft = -foot
        p = math.radians(ph)
        want = unit(np.array([0, 0, -1]) * math.cos(p) + np.array([-1, 0, 0]) * math.sin(p))
        third = unit(want - shaft * want.dot(shaft))
        thick = np.cross(third, shaft)
        at = H - 0.56 * shaft
    else:
        # tip down, leaning back by tb (crystal behind the grip), out by tt
        shaft = unit(np.array([0, -math.cos(math.radians(tb)), -math.sin(math.radians(tb))]) + rad * math.tan(math.radians(tt)))
        thick = unit(np.cross(shaft, [0, 0, 1])) if abs(shaft[2]) < 0.9 else np.array([-1, 0, 0])
        thick = -rad - shaft * (-rad).dot(shaft); thick = unit(thick)
        third = np.cross(shaft, thick)
        at = H
    return at, shaft, thick, third


def place(at, shaft, thick, third, left):
    M = np.diag([-1, 1, 1]) if left else np.eye(3)
    B = np.column_stack([M @ third, M @ shaft, M @ thick])   # MirrorEdge: the edge mirrored, the flat flipped
    return u @ B.T + M @ at


def score(row):
    out = {}
    for left in (False, True):
        if kind == "wand" and left:
            continue
        Q = place(*row, left)
        hd = {k: 9.0 for k in ("idle", "run", "sprint")}
        hp = {k: 9.0 for k in ("idle", "run", "sprint")}
        pen = -9.0
        po = -9.0
        for name, f, bt, BX, BN, BC, hands in frames:
            ph = name.split("_")[0]
            for sd, ht in hands.items():
                hd[ph] = min(hd[ph], ht.query(Q[head])[0].min())
                hp[ph] = min(hp[ph], ht.query(Q)[0].min())
            d, i = bt.query(Q)
            sgn = np.sign(((Q - BX[i]) * BN[i]).sum(1))
            pen = max(pen, float(-(d * sgn).min()))        # into her skin (+), or the air left (-)
            po = max(po, float(-(d * sgn - BC[i]).min()))   # into the outfit
        out["L" if left else "R"] = (hd, hp, pen, po)
    return out


if __name__ == "__main__":
    grid = json.loads(opt["grid"]) if "grid" in opt else (
        dict(th=[145, 155, 165], r=[0.19, 0.21, 0.23], hy=[0.98, 1.03], tb=[5, 15], tt=[0, 10], ph=[0, 20]) if kind == "axe" else
        dict(th=[140, 150, 160], r=[0.17, 0.19, 0.21], hy=[1.00, 1.04], tb=[20, 25, 30], tt=[0, 10], ph=[0]))
    res = []
    for vals in itertools.product(*grid.values()):
        p = dict(zip(grid.keys(), vals))
        row = rowfor(**p)
        sc = score(row)
        worst_idle = min(v[0]["idle"] for v in sc.values())
        worst_run = min(min(v[0]["run"], v[0]["sprint"]) for v in sc.values())
        pen = max(v[2] for v in sc.values())
        ok = int(worst_idle >= 0.10) + int(worst_run >= 0.04) + int(pen <= -0.008)
        res.append((ok, min(worst_idle / 0.10, worst_run / 0.04, -pen / 0.008), p, sc, row))
        print(p, f"idle {1000 * worst_idle:.0f} run {1000 * worst_run:.0f} pen {1000 * pen:+.0f}", file=sys.stderr, flush=True)
    res.sort(key=lambda r: (-r[0], -r[1]))
    for ok, m, p, sc, row in res[: int(opt.get("top", 15))]:
        at, sh, tk, _ = row
        print(ok, f"{m:.2f}", p, " | ".join(f"{k}: head i/r/s {1000 * v[0]['idle']:.0f}/{1000 * v[0]['run']:.0f}/{1000 * v[0]['sprint']:.0f} piece {1000 * v[1]['idle']:.0f}/{1000 * v[1]['run']:.0f}/{1000 * v[1]['sprint']:.0f} pen {1000 * v[2]:+.0f} outfit {1000 * v[3]:+.0f}" for k, v in sc.items()))
        print("   row", ";".join(",".join(f"{x:.3f}" for x in a) for a in (at, sh, tk)))
