"""hs5.py: solver 5: hs4 (M4) plus a frame acceleration cap (facc, in g, as far as the hold has let go) and the braid's held joint cap (kink, deg, joints 2+)."""
import sys; sys.path[:0] = ["../sv5", "../sv4", "../sv3"]
from hs4 import *
class M5(M4):
    vrThen = None
    def frame(s, d):
        o = s.o; tg = d["target"].copy(); dt = d["dt"]
        link = np.r_[0, np.linalg.norm(np.diff(tg, axis=0), axis=1)]
        s.holds(tg, dt)
        if not s.live or dt <= 0:
            s.x = tg.copy(); s.xp = tg.copy(); s.rootThen = tg[0].copy(); s.offFloor = 1e3; s.live = True; s.vrThen = None
        sc = 1.04; floor = d["ground"] + 0.015
        tgo = tg.copy()
        free = np.array([1 - s.hold[i] / s.stiff if s.stiff > 0 else 1 for i in range(8)]); s.free = free
        ins = [False] * 8
        for i in range(1, 8):
            q = s.collide(d, tgo[i].copy(), None, sc); q[1] = max(q[1], floor)
            ins[i] = np.linalg.norm(q - tgo[i]) > 1e-6
            tgo[i] = tgo[i] + (q - tgo[i]) * (1.0 if o.get("pushheld") else free[i])
        steps = max(1, int(math.ceil(dt * 120 - 1e-3))); h = dt / steps; s.nsteps = steps
        fall = np.array([0, -9.8, 0]) * h * h
        rootStep = (tg[0] - s.rootThen) / steps; s.rootThen = tg[0].copy(); most = 2.5 * h
        vr = rootStep / h
        if o.get('facc') and s.vrThen is not None and dt > 0:
            a = (vr - s.vrThen) / dt; al = np.linalg.norm(a); lim = o['facc'] * 9.8
            if al > lim and np.linalg.norm(vr) > o.get('fvmin', 0):
                ex = a * (1 - lim / al)
                for i in range(1, 8): s.xp[i] = s.xp[i] - ex * dt * h * free[i]
        s.vrThen = vr
        x, xp = s.x, s.xp; vel = np.zeros((8, 3))
        rest = [None] + [nz(tg[i] - tg[i - 1]) for i in range(1, 8)]
        bend = o["bend"]
        for st in range(steps):
            for i in range(1, 8):
                was = x[i].copy(); s.prev[i] = was; vel[i] = (x[i] - xp[i]) * 0.985
                rel = (vel[i] - rootStep) * (1 - 0.03 * free[i])
                if rel @ rel > most * most: rel = nz(rel) * most
                vel[i] = rootStep + rel
                x[i] = x[i] + vel[i] + fall; xp[i] = was
            x[0] = tg[0]
            corr = np.zeros((8, 3))
            for k in range(3):
                R = np.eye(3)
                for i in range(1, 8):
                    x[i] += (tgo[i] - x[i]) * s.hold[i]
                    want = R @ rest[i]; cur = nz(x[i] - x[i - 1])
                    kb = 0 if i == 1 else bend * free[i]
                    bent = nz(cur + (want - cur) * kb) if kb > 0 else cur
                    lim0 = math.radians(75) if i == 1 else math.radians(60)
                    lim = lim0 + (math.pi - lim0) * (1 - free[i])
                    if o.get('kink') and i >= 2 and (ins[i] or not o.get('kin')): lim = lim0 + (math.radians(o['kink']) - lim0) * (1 - free[i])
                    if (free[i] > 0.02 or (o.get('kink') and i >= 2 and (ins[i] or not o.get('kin')))) and lim < math.pi - 1e-6: bent = cone(bent, want, lim)
                    xp[i] += (bent - cur) * link[i]
                    newp = x[i - 1] + bent * link[i]
                    corr[i] = newp - x[i]; x[i] = newp
                    x[i] = s.collide(d, x[i], i, sc)
                    if x[i][1] < floor: x[i][1] = floor; s.touch[i] = [0, 1, 0]; s.grip[i] = 0.5; s.grounded[i] = True; s.surf[i] = 0
                    if i < 7: R = rot_between(rest[i], nz(x[i] - x[i - 1]))
            for i in range(1, 7): xp[i] = xp[i] + 0.9 * free[i] * corr[i + 1]
            for i in range(1, 8):
                if s.grip[i] == 0: continue
                if o["recede"]:
                    n = s.touch[i]; u = n * min(0, s.surf[i] @ n) * ({None: 1, True: free[i], "step": float(free[i] > 0.5), "sq": free[i] ** 2, "ss": smooth(0.1, 0.5, free[i])}[o.get("recede_gate")]); r = vel[i] - u; r = r - n * min(0, r @ n)
                    xp[i] = x[i] - u - r * (1 - s.grip[i])
                else:
                    v = vel[i] - s.touch[i] * min(0, vel[i] @ s.touch[i])
                    xp[i] = x[i] - v * (1 - s.grip[i])
                s.grip[i] = 0; s.surf[i] = 0
        s.pd = d
        return x
def sim5(fr, style, **o):
    m = M5(fr, style, **o)
    return [m.frame(d).copy() for d in fr]
