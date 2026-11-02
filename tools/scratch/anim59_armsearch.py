"""Animation 59: for each blade key of flare_long_cut, search each fist's roll about the blade (psi) and its elbow's swing
about shoulder-wrist (phi) for the solve that holds the keyed blade with the least wrist bend; prints the best per frame.
    python ../scratch/anim59_armsearch.py r 6,11,24          (run from tools/anim)"""
import sys, math, time, json
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
import numpy as np
from keyed import Rig, grip_of
from rig import Skeleton, DATA, qrot, qmul, qinv, qaxis, qfrom_basis, qbetween
from clips import flare_long_cut as M

sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
rig.grip = grip_of("sunder", M.TILT)
L = M.LongCut(rig)
S_r, S_l, chest = L.body()
I = rig.I
side = sys.argv[1]
frames = [int(x) for x in sys.argv[2].split(",")]
prefer = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}   # {frame: [kx,ky,kz]} the knuckles' wanted way (soft)
lean = rig.grip.get("r", 0.0)
lq = qaxis([1.0, 0, 0], -lean)


def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, float(a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))))))


def perp(d):
    a = np.array([0, 1.0, 0]) if abs(d[1]) < 0.9 else np.array([0, 0, 1.0])
    u = a - d * float(a @ d); u /= np.linalg.norm(u)
    return u, np.cross(d, u)


def trial(fr, pose, P, d, psi, phi):
    u, v = perp(d)
    k = math.cos(math.radians(psi)) * u + math.sin(math.radians(psi)) * v
    if side == "r":
        want = qfrom_basis(np.cross(k, d), k, d)
        R = qmul(want, qinv(lq))
        W = P - qrot(R, M.AT)
        hz, hy = d, k
        S = S_r[fr]
    else:
        # the left fist: its line DIR_L on d, its roll psi (its knuckles k)
        e = k
        Mw = np.stack([d, e, np.cross(d, e)], axis=1)
        # the hand's own (DIR_L, Y') basis: Y' the hand's knuckle-ish axis orthogonalised to DIR_L
        yl = np.array([0, 1.0, 0]) - M.DIR_L * M.DIR_L[1]; yl /= np.linalg.norm(yl)
        Mh = np.stack([M.DIR_L, yl, np.cross(M.DIR_L, yl)], axis=1)
        Rw = Mw @ Mh.T
        W = P + d * M.LEFT_T - Rw @ M.AT_L
        hz, hy = Rw[:, 2], Rw[:, 1]
        S = S_l[fr]
    ax = (W - S) / np.linalg.norm(W - S)
    a, b = perp(ax)
    pole = math.cos(math.radians(phi)) * a + math.sin(math.radians(phi)) * b
    spec = {"pos": tuple(W), "blade": tuple(hz), "knuckles": tuple(hy), "frame": "char", "pole": tuple(pole),
            "pole_at": "shoulder", "twist": 0.5 if side == "r" else 0.4}
    p = dict(pose); p["hand_" + side] = spec
    rig.swivel = {}
    for a in ('elbow_seen', 'twist_last', 'swing_last'):
        if hasattr(rig, a):
            delattr(rig, a)
    local, pos = rig.solve(p, base=(L.base.rot[fr], L.base.pos[fr]))
    g, gp = sk.fk(local[None], pos[None])
    h = I["hand_" + side]
    if side == "r":
        dd = qrot(g[0, h], M.DIR); Pp = gp[0, h] + qrot(g[0, h], M.AT)
        err_p = np.linalg.norm(Pp - P)
    else:
        dd = qrot(g[0, h], M.DIR_L); Q = gp[0, h] + qrot(g[0, h], M.AT_L)
        Pq = P + d * M.LEFT_T
        off = Q - Pq; err_p = np.linalg.norm(off - d * float(off @ d))
    err_d = ang(dd, d)
    # the wrist's bend: the hand's local turn off its rest
    ql = qmul(qinv(sk.rest_rot[h]), local[h])
    ql = ql if ql[3] >= 0 else -ql
    an = 2 * math.acos(min(1.0, float(ql[3])))
    rv = ql[:3] / max(1e-9, math.sin(an / 2)) * math.degrees(an)     # (dev about X, twist about Y, flex about Z)
    bend = ((abs(rv[2]) / 70) ** 4 + (abs(rv[0]) / 30) ** 4) ** 0.25 * 50 + abs(rv[1]) * 0.5
    bend = (bend, rv)
    E = gp[0, I["lowerarm_" + side]]
    # Clearance of the arm off her trunk (a capsule on pelvis-spine_03-neck_01, radius TR m): the least, m (- inside).
    TR = float(__import__("os").environ.get("TRUNK_R", "0.17"))
    segs = [(gp[0, I["pelvis"]], gp[0, I["spine_03"]]), (gp[0, I["spine_03"]], gp[0, I["neck_01"]])]
    Sh = gp[0, I["upperarm_" + side]]
    pts = [Sh + (E - Sh) * t for t in (0.35, 0.6, 0.8, 1.0)] + [E + (gp[0, h] - E) * t for t in (0.33, 0.66, 1.0)]
    def dseg(x, a, b):
        u = min(1.0, max(0.0, float((x - a) @ (b - a)) / float((b - a) @ (b - a))))
        return float(np.linalg.norm(x - a - (b - a) * u))
    global CLR
    CLR = min(min(dseg(x, a, b) for a, b in segs) for x in pts) - TR
    global REACH
    REACH = (np.linalg.norm(W - S), np.linalg.norm(gp[0, h] - gp[0, I["upperarm_" + side]]), getattr(rig, 'twist_last', {}).get(side, float('nan')))
    return err_d, err_p * 1000, bend, k, E, pole, qrot(qinv(chest[fr]), pole)


for fr in frames:
    t0 = time.time()
    P, d = M._blade_at(fr)[:2]
    ov = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    if ov:
        d = np.array(ov["d"], float); d /= np.linalg.norm(d)
        P = np.array(ov["tip"], float) - d * M.BLADE_LEN if "tip" in ov else np.array(ov["P"], float)
        print("override P", np.round(P, 3), "d", np.round(d, 3))
    pose = L.pose(fr)
    res = []
    STEP = int(__import__('os').environ.get('STEP', '30'))
    for psi in range(0, 360, STEP):
        for phi in range(0, 360, STEP):
            ed, ep, bend, k, E, pole, pole_c = trial(fr, pose, P, d, psi, phi)
            pk = prefer.get(str(fr))
            pref = ang(k, np.array(pk)) if pk else 0.0
            res.append((REACH, ed * 3 + ep / 5 + bend[0] * 0.3 + pref * float(__import__("os").environ.get("PREFW", "0.15")) + max(0.0, -CLR) * 1000 * float(__import__("os").environ.get("CLRW", "0")), ed, ep, bend, psi, phi, k, E, pole_c, pref, CLR))
    res.sort(key=lambda r: r[1])
    print(f"f{fr} ({time.time()-t0:.0f}s) d={np.round(d,2)} S={np.round((S_r if side=='r' else S_l)[fr],2)}")
    if __import__('os').environ.get("PERPSI"):
        seen = set(); top = []
        for r in res:
            if r[5] not in seen:
                seen.add(r[5]); top.append(r)
    else:
        top = res[:6]
    for R_, *r in top:
        print(f"  clr {r[-1]*100:5.1f}cm tw {R_[2]:6.1f} reach {R_[0]:.3f}/{R_[1]:.3f} cost {r[0]:6.1f} blade {r[1]:5.1f} pos {r[2]:6.1f}mm bend {r[3][0]:5.1f} rv {np.round(r[3][1]).astype(int)} psi {r[4]:3d} phi {r[5]:3d} "
              f"knuck {np.round(r[6],2)} elbow {np.round(r[7],2)} pole_chest {np.round(r[8],2)} pref {r[9]:.0f}")
