"""Animation 59 (armpath): for each blade key of flare_long_cut, search each fist's roll about the blade (psi) and its elbow's swing
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



# ---- armpath: every key frame's (psi, phi) candidates, then the path through them that keeps the twist and the elbow
# moving gently (dynamic programming), with the arm clear of her trunk (CLRW per mm inside). --write: into BLADE.
import os, re
STEP = int(os.environ.get("STEP", "30"))
TWW, EW, CLRW = float(os.environ.get("TWW", "0.25")), float(os.environ.get("EW", "1.0")), float(os.environ.get("CLRW", "1.0"))
cands = []
for fr in frames:
    P, d = M._blade_at(fr)[:2]
    pose = L.pose(fr)
    row = []
    psis = list(range(0, 360, STEP))
    if os.environ.get("KEEP") and (not os.environ.get("KEEPF") or str(fr) in os.environ["KEEPF"].split(",")):
        # The fist's roll kept within +-KEEP deg of the key's own (the right fist's roll is the blade's edge).
        k0 = M._blade_at(fr)[3 if side == "r" else 5]
        u0, v0 = perp(d)
        p0 = math.degrees(math.atan2(float(k0 @ v0), float(k0 @ u0)))
        kw = int(os.environ["KEEP"])
        psis = [p0 + o for o in range(-kw, kw + 1, max(1, kw // 2 or 1))] if kw else [p0]
    if os.environ.get("ALPHA") and side == "l":
        # The left fist's roll locked to the right's (a firm two-handed grip): the right's knuckles turned ALPHA deg
        # about the blade (each value in the comma list is one candidate set).
        kr = M._blade_at(fr)[3]
        u0, v0 = perp(d)
        pr = math.degrees(math.atan2(float(kr @ v0), float(kr @ u0)))
        psis = [pr + float(a) for a in os.environ["ALPHA"].split(",")]
    for psi in psis:
        for phi in range(0, 360, int(os.environ.get("PSTEP", STEP))):
            ed, ep, bend, k, E, pole, pole_c = trial(fr, pose, P, d, psi, phi)
            c = ed * 3 + ep / 5 + bend[0] * 0.3 + max(0.0, -CLR) * 1000 * CLRW
            row.append(dict(c=c, tw=REACH[2], E=np.array(E), psi=psi, phi=phi, k=k, pole=pole_c, clr=CLR, ed=ed, ep=ep, bend=bend[0]))
    cands.append(row)
    if os.environ.get("DUMP"):
        for r in sorted(row, key=lambda r: r["c"])[:int(os.environ["DUMP"])]:
            print(f"   psi {r['psi']:5.0f} phi {r['phi']:3d} tw {r['tw']:6.1f} clr {r['clr']*100:5.1f} ed {r['ed']:4.1f} ep {r['ep']:5.1f} bend {r['bend']:5.1f} c {r['c']:6.1f} pole {tuple(round(float(x), 2) for x in r['pole'])}")
    print(f"f{fr}: {len(row)} candidates, best alone {min(r['c'] for r in row):.1f}", flush=True)
if os.environ.get("PKL"):
    import pickle
    pickle.dump({fr: [{k: v for k, v in r.items() if k != "E"} | {"E": r["E"].tolist()} for r in row] for fr, row in zip(frames, cands)},
                open(os.environ["PKL"], "wb"))
n = len(frames)
if os.environ.get("TWEND"):
    # The last key's twist pulled toward TWEND (deg; the clip's next pose, e.g. the idle's), 1 cost per TWENDW deg.
    for r in cands[-1]:
        r["c"] += abs(r["tw"] - float(os.environ["TWEND"])) / float(os.environ.get("TWENDW", "3"))
acc = [[r["c"] for r in cands[0]]]
back = []
for i in range(1, n):
    a, b = cands[i - 1], cands[i]
    cur, bk = [], []
    for r in b:
        best, bj = 1e18, -1
        for j, q in enumerate(a):
            dtw = abs(r["tw"] - q["tw"])
            t = acc[i - 1][j] + dtw * TWW + (1e4 if dtw > 120 else 0) + float(np.linalg.norm(r["E"] - q["E"])) * 100 * EW
            if t < best:
                best, bj = t, j
        cur.append(best + r["c"]); bk.append(bj)
    acc.append(cur); back.append(bk)
j = int(np.argmin(acc[-1]))
path = [j]
for i in range(n - 1, 0, -1):
    j = back[i - 1][j]; path.append(j)
path = path[::-1]
out = {}
for fr, row, j in zip(frames, cands, path):
    r = row[j]
    print(f"f{fr:2d} psi {r['psi']:5.0f} phi {r['phi']:3d} tw {r['tw']:6.1f} clr {r['clr']*100:5.1f}cm blade {r['ed']:4.1f} pos {r['ep']:5.1f}mm bend {r['bend']:5.1f}"
          f" pole {tuple(round(float(x), 2) for x in r['pole'])} knuck {tuple(round(float(x), 2) for x in r['k'])}")
    out[fr] = (tuple(round(float(x), 2) for x in r["pole"]), tuple(round(float(x), 2) for x in r["k"]))
if "--write" in sys.argv:
    p = M.__file__
    s = open(p).read()
    a0 = s.index("BLADE = ["); a1 = s.index("]\n", s.index("
]", a0) - 1)
    lines = s[a0:a1].split("\n")
    names = {"LAND": M.LAND}
    for li, ln in enumerate(lines):
        mm = re.match(r"\s+\((\w+), ", ln)
        if not mm:
            continue
        fr = int(mm.group(1)) if mm.group(1).isdigit() else names[mm.group(1)]
        if fr not in out:
            continue
        mm2 = re.match(r"^(\s+\(\w+, \([^)]*\), (?:_d\([^)]*\)|_n\([^)]*\)), )\(([^)]*)\), \(([^)]*)\), \(([^)]*)\), \(([^)]*)\)(\),.*)$", ln)
        assert mm2, ln
        g = list(mm2.groups())
        f3 = lambda v: ", ".join(f"{x:.2f}" for x in v)
        if side == "r":
            g[1], g[2] = f3(out[fr][0]), f3(out[fr][1])
        else:
            g[3], g[4] = f3(out[fr][0]), f3(out[fr][1])
        new = f"{g[0]}({g[1]}), ({g[2]}), ({g[3]}), ({g[4]}){g[5]}"
        lines[li] = new
    s = s[:a0] + "\n".join(lines) + s[a1:]
    open(p, "w").write(s)
    print("written", p)
