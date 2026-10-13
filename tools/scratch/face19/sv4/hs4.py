"""Solver 4 harness: hs3's model plus (a) hold curve thresholds (hold_lo/hold_hi), (b) the behind-ball mirror only for a
point that came from behind ('came'), (c) recede contact as hs3; and the shader's per-segment turn (parallel transport)."""
import sys; sys.path.insert(0, "../sv3")
from cfg3 import *
import cfg3

class M4(Model):
    def __init__(s, fr, style, **o):
        Model.__init__(s, fr, style, **o)
        s.o.setdefault("hold_lo", 0.35); s.o.setdefault("hold_hi", 0.85); s.o.setdefault("mirror", "always")
        s.prev = np.zeros((8, 3))
    def holds(s, tg, dt):
        stiff = s.stiff
        lying = s.grounded[1:].any(); s.grounded[:] = False
        s.offFloor = 0 if lying else s.offFloor + dt
        for i in range(1, 8):
            dn = nz(tg[i] - tg[0]) @ [0, -1, 0]
            u = smooth(s.o["hold_lo"], s.o["hold_hi"], dn) * (smooth(*s.o["hold_mul"], dn) if "hold_mul" in s.o else 1)
            want = stiff * u
            s.hungFor[i] = s.hungFor[i] + dt if u > 0.98 else 0
            if not s.live or want <= s.hold[i]: s.hold[i] = want
            elif s.offFloor > 0.5 and s.hungFor[i] > 0.5: s.hold[i] = min(want, s.hold[i] + stiff * dt / 0.5)
    def collide(s, d, p, i=None, sc=1.0):
        for b in range(len(d["r"])):
            r = d["r"][b] * sc
            if r <= 0: continue
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            tt = np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else 0
            c = at + w * tt
            off = p - c
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0:
                came = s.o["mirror"] == "came" or (s.o["mirror"] == "came_free" and i is not None and s.free[i] > 0.5)
                if i is None or not came or (s.prev[i] - c) @ bk >= 0: off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            p = c + n * r
            if i is not None:
                s.touch[i] = n; s.grip[i] = max(s.grip[i], s.o["grip_ball"])
                if s.pd is not None:
                    pw = s.pd["across"][b]
                    s.surf[i] = (c - (s.pd["at"][b] + pw * tt)) / s.nsteps
                else: s.surf[i] = 0
        return p
    def frame(s, d):
        o = s.o; tg = d["target"].copy(); dt = d["dt"]
        link = np.r_[0, np.linalg.norm(np.diff(tg, axis=0), axis=1)]
        s.holds(tg, dt)
        if not s.live or dt <= 0:
            s.x = tg.copy(); s.xp = tg.copy(); s.rootThen = tg[0].copy(); s.offFloor = 1e3; s.live = True
        sc = 1.04; floor = d["ground"] + 0.015
        tgo = tg.copy()
        free = np.array([1 - s.hold[i] / s.stiff if s.stiff > 0 else 1 for i in range(8)]); s.free = free
        for i in range(1, 8):
            q = s.collide(d, tgo[i].copy(), None, sc); q[1] = max(q[1], floor)
            tgo[i] = tgo[i] + (q - tgo[i]) * free[i]
        steps = max(1, int(math.ceil(dt * 120 - 1e-3))); h = dt / steps; s.nsteps = steps
        fall = np.array([0, -9.8, 0]) * h * h
        rootStep = (tg[0] - s.rootThen) / steps; s.rootThen = tg[0].copy(); most = 2.5 * h
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
                    if free[i] > 0.02 and lim < math.pi - 1e-6: bent = cone(bent, want, lim)
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

def sim4(fr, style, **o):
    m = M4(fr, style, **o)
    return [m.frame(d).copy() for d in fr]

BEND = dict(braid=0.03, ponytail=0.03, long=0.02)
def per4(o, st): return dict(o, bend=BEND[st])
C2 = dict(recede=False)                                    # = solver 3's C# (G2)
C3 = dict(recede=True)                                     # = G3
def lg2(d, n): return cfg3.lg(d, n)
C3c = dict(recede=True, mirror="came")
H1 = dict(C3c, hold_lo=0.55, hold_hi=0.80)
H2 = dict(C3c, hold_lo=0.60, hold_hi=0.80)
C4 = dict(recede=True, recede_gate=True, mirror="came_free")
H2g = dict(C4, hold_lo=0.60, hold_hi=0.80)
C4a = dict(recede=True, recede_gate=True)
C4s = dict(recede=True, recede_gate="step")
C4q = dict(recede=True, recede_gate="sq")
C5 = dict(recede=True, recede_gate="ss", mirror="came_free")
H5 = dict(C5, hold_lo=0.60, hold_hi=0.80)
H6 = dict(C5, hold_lo=0.58, hold_hi=0.77)
H7 = dict(C5, hold_mul=(0.55, 0.77))
