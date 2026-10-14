"""hs10.py: solver 10: the C# at HEAD (M8) with the step loop (hs5's M5.frame) rewritten here so held points that lodge on
a ball can be given options: dtouch (follow-the-leader pull from below), btouch (bend), gtouch (no grip), ctouch (cap),
lodge test 'lup' (touch normal's world-up share over it) and 'labove' (or the point above its predecessor)."""
import sys; sys.path[:0] = ["../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from g9 import *
import hs5
def core(s, d):
    o = s.o; tg = d["target"].copy(); dt = d["dt"]
    link = np.r_[0, np.linalg.norm(np.diff(tg, axis=0), axis=1)] * o.get("lscale", 1.0)
    s.holds(tg, dt)
    if not s.live or dt <= 0:
        s.x = tg.copy(); s.xp = tg.copy(); s.rootThen = tg[0].copy(); s.offFloor = 1e3; s.live = True; s.vrThen = None
    sc = o.get("sc", 1.04); floor = d["ground"] + 0.015
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
    if not hasattr(s, "lodge"): s.lodge = np.zeros(8); s.loglodge = []
    lod = s.lodge
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
            if o.get("sm"):
                c0 = math.radians(o["sm"]); wdt = math.radians(o.get("smw", 30))
                for i in range(1, 7):
                    a, b = x[i] - x[i - 1], x[i + 1] - x[i]
                    th = math.acos(float(np.clip(nz(a) @ nz(b), -1, 1)))
                    if th <= c0: continue
                    g = (1 - free[i]) if o.get("smheld") else 1.0
                    if o.get("smtouch") and not (s.grip[i] > 0): g = 0
                    mv = ((x[i - 1] + x[i + 1]) / 2 - x[i]) * o.get("smk", 0.5) * float(smooth(c0, c0 + wdt, th)) * g
                    x[i] = x[i] + mv
                    if o.get("smvn"): xp[i] = xp[i] + mv
            R = np.eye(3)
            for i in range(1, 8):
                x[i] += (tgo[i] - x[i]) * s.hold[i]
                want = R @ rest[i]; cur = nz(x[i] - x[i - 1])
                fb = max(free[i], lod[i]) if o.get("btouch") else free[i]
                kb = 0 if i == 1 else bend * fb
                bent = nz(cur + (want - cur) * kb) if kb > 0 else cur
                fc = max(free[i], lod[i]) if o.get("ctouch") else free[i]
                lim0 = math.radians(75) if i == 1 else math.radians(60)
                lim = lim0 + (math.pi - lim0) * (1 - fc)
                if fc > 0.02 and lim < math.pi - 1e-6: bent = cone(bent, want, lim)
                xp[i] += (bent - cur) * link[i]
                newp = x[i - 1] + bent * link[i]
                corr[i] = newp - x[i]; x[i] = newp
                x[i] = s.collide(d, x[i], i, sc)
                if x[i][1] < floor: x[i][1] = floor; s.touch[i] = [0, 1, 0]; s.grip[i] = 0.5; s.grounded[i] = True; s.surf[i] = 0
                if i < 7: R = rot_between(rest[i], nz(x[i] - x[i - 1]))
        # Which held points lodge on a ball this step (touched it with its normal mostly up, or sit above their predecessor).
        nl = np.zeros(8)
        for i in range(1, 8):
            on = s.grip[i] > 0 and not s.grounded[i] and s.touch[i][1] > o.get("lup", 2.0)
            if o.get("labove") and s.grip[i] > 0 and x[i][1] > x[i - 1][1]: on = True
            nl[i] = 1.0 if on else 0.0
        lod[:] = nl if not o.get("lfade") else np.maximum(nl, lod * o["lfade"])
        fd = np.maximum(free, lod) if o.get("dtouch") else free
        for i in range(1, 7): xp[i] = xp[i] + 0.9 * o.get("dtouch", 1.0) ** 0 * fd[i] * corr[i + 1]
        for i in range(1, 8):
            if s.grip[i] == 0: continue
            g = 0.0 if (o.get("gtouch") and lod[i] > 0) else s.grip[i]
            n = s.touch[i]; u = n * min(0, s.surf[i] @ n) * smooth(0.1, 0.5, free[i]); r = vel[i] - u; r = r - n * min(0, r @ n)
            xp[i] = x[i] - u - r * (1 - g)
            dp = o.get("dpost")
            if dp and i < 7 and (dp == "all" or lod[i] > 0):
                f = 1.0 if dp == "all" and o.get("dfree") else (max(free[i], lod[i]) if dp == "lod" else free[i])
                dv = -0.9 * f * corr[i + 1] * o.get("dgain", 1.0); vn = dv @ n
                if vn < 0: dv = dv - n * vn
                xp[i] = xp[i] - dv
            s.grip[i] = 0; s.surf[i] = 0
    s.loglodge.append(lod.copy())
    s.pd = d
    return x
ORIG = hs5.M5.frame
def pick(s, d): return ORIG(s, d) if s.o.get("orig") else core(s, d)
hs5.M5.frame = pick            # (M6 and M8 call M5.frame by name: the whole stack now runs this loop; orig=1 the old one)
def sim10(fr, style, **o):
    m = M8(fr, style, **per4(dict(H7, **o), style))
    return [m.frame(d).copy() for d in fr], m
STEP = dict(death=3, getup=4, getupback=4, throw=2, run=2, stop=2)
CLIPS = [(c, s) for c in ("run", "stop", "throw", "death", "getup", "getupback") for s in ("ponytail", "braid", "long")]
