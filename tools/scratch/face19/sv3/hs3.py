"""Solver 2 harness: HairSway chain replica (today's and the new one), metrics, plots, on HAIRDUMP logs."""
import json, sys, math, numpy as np
S = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/"
ART = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/"

def load(log):
    fr = []
    for line in open(log, encoding="utf-8", errors="ignore"):
        if line.startswith("HAIRDUMP "):
            d = json.loads(line[9:])
            for k in ("target", "x", "xp", "at", "back", "across", "head"): d[k] = np.array(d[k], float)
            d["r"] = np.array(d["r"]); d["behind"] = np.array(d["behind"], bool)
            fr.append(d)
    start = max(i for i, d in enumerate(fr) if np.abs(d["x"] - d["target"]).max() < 1e-6)
    return fr[start:]

def nz(v):
    n = np.linalg.norm(v); return v / n if n > 1e-12 else v

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def jlinks(style):
    P = np.array(json.load(open(ART + f"heroine_hair_{style}.chain.json"))["points"])
    return np.r_[0, np.linalg.norm(np.diff(P, axis=0), axis=1)]

def rot_between(a, b):
    v = np.cross(a, b); c = float(a @ b)
    if c < -0.999999:
        p = np.cross(a, [1, 0, 0])
        if p @ p < 1e-6: p = np.cross(a, [0, 1, 0])
        p = nz(p); return 2 * np.outer(p, p) - np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)

def cone(cur, want, lim):
    """cur kept within lim radians of want (both unit)."""
    c = float(np.clip(cur @ want, -1, 1))
    if c >= math.cos(lim): return cur
    ax = np.cross(want, cur)
    if ax @ ax < 1e-12:
        ax = np.cross(want, [1, 0, 0])
        if ax @ ax < 1e-12: ax = np.cross(want, [0, 0, 1])
    ax = nz(ax)
    return want * math.cos(lim) + np.cross(ax, want) * math.sin(lim) + ax * (ax @ want) * (1 - math.cos(lim))

BASE = dict(scale=False, bend=0.0, bend_max=None, root_cone=None, root_k=0.0, push=False, dftl=0.0, dftl_sum=False,
            hold="cur", damp=0.985, cap=2.5, iters=3, grip_ball=0.1, grip_floor=0.5, rel_drag=0.0, bend_taper=0.0, bend_mode="pass", bend_gate=False, cap_gate=False, push_gate=False, dftl_gate=False, drag_gate=False, cone_soft=False, gate_pow=1.0, recede=False)
NEW = dict(BASE, scale=True, push=True, hold="hang", dftl=0.9, rel_drag=0.03, bend=0.01, bend_max=math.radians(60),
           root_cone=math.radians(60))

class Model:
    def __init__(s, fr, style, **o):
        s.o = dict(BASE); s.o.update(o)
        s.link0 = jlinks(style)
        s.keep = (1 - np.arange(8) / 7.0) ** 3
        s.hold = np.zeros(8); s.grip = np.zeros(8); s.touch = np.zeros((8, 3)); s.grounded = np.zeros(8, bool)
        s.offFloor = 1e3; s.hungFor = np.zeros(8); s.live = False; s.pd = None; s.surf = np.zeros((8, 3)); s.nsteps = 4; s.stiff = o.get("stiff", fr[0]["stiff"])
    def holds(s, tg, dt):
        stiff = s.stiff
        lying = s.grounded[1:].any(); s.grounded[:] = False
        s.offFloor = 0 if lying else s.offFloor + dt
        level = 1
        for i in range(1, 8):
            u = smooth(0.35, 0.85, nz(tg[i] - tg[0]) @ [0, -1, 0])
            level = min(level, smooth(-0.3, 0.1, nz(tg[i] - tg[i - 1]) @ [0, -1, 0]))
            k = s.keep[i] * (0.5 + 0.5 * level if i == 1 else level)
            if s.o["hold"] == "hang": k = 0
            want = stiff * (k + (1 - k) * u)
            s.hungFor[i] = s.hungFor[i] + dt if u > 0.98 else 0
            if not s.live or want <= s.hold[i]: s.hold[i] = want
            elif s.offFloor > 0.5 and s.hungFor[i] > 0.5: s.hold[i] = min(want, s.hold[i] + stiff * dt / 0.5)
    def collide(s, d, p, i=None, sc=1.0):
        for b in range(len(d["r"])):
            r = d["r"][b] * sc
            if r <= 0: continue
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
            off = p - c
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0: off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            p = c + n * r
            if i is not None:
                s.touch[i] = n; s.grip[i] = max(s.grip[i], s.o["grip_ball"])
                if s.pd is not None:
                    pw = s.pd["across"][b]; pww = pw @ pw
                    tt = np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else 0
                    s.surf[i] = (c - (s.pd["at"][b] + pw * tt)) / s.nsteps
                else: s.surf[i] = 0
        return p
    def frame(s, d):
        o = s.o; tg = d["target"].copy(); dt = d["dt"]
        sc = 1.04 if o["scale"] else 1.0
        link = np.r_[0, np.linalg.norm(np.diff(tg, axis=0), axis=1)] if o["scale"] else s.link0
        s.holds(tg, dt)
        if not s.live or dt <= 0:
            s.x = tg.copy(); s.xp = tg.copy(); s.rootThen = tg[0].copy(); s.offFloor = 1e3; s.live = True
        floor = d["ground"] + 0.015
        tgo = tg.copy()
        free = np.array([1 - s.hold[i] / s.stiff if s.stiff > 0 else 1 for i in range(8)])
        gfree = free ** o["gate_pow"]
        if o["push"]:
            for i in range(1, 8):
                q = s.collide(d, tgo[i].copy(), None, sc); q[1] = max(q[1], floor)
                tgo[i] = tgo[i] + (q - tgo[i]) * (gfree[i] if o["push_gate"] else 1)
        steps = max(1, int(math.ceil(dt * 120 - 1e-3))); h = dt / steps; s.nsteps = steps
        fall = np.array([0, -9.8, 0]) * h * h
        rootStep = (tg[0] - s.rootThen) / steps; s.rootThen = tg[0].copy(); most = o["cap"] * h
        x, xp = s.x, s.xp; vel = np.zeros((8, 3))
        rest = [None] + [nz(tg[i] - tg[i - 1]) for i in range(1, 8)]
        for st in range(steps):
            for i in range(1, 8):
                was = x[i].copy(); vel[i] = (x[i] - xp[i]) * o["damp"]
                rel = vel[i] - rootStep
                if o["rel_drag"]: vel[i] = rootStep + rel * (1 - o["rel_drag"] * (gfree[i] if o["drag_gate"] else 1)); rel = vel[i] - rootStep
                if o["cap"] and rel @ rel > most * most: vel[i] = rootStep + nz(rel) * most
                x[i] = x[i] + vel[i] + fall; xp[i] = was
            x[0] = tg[0]
            corr = np.zeros((8, 3))
            for k in range(o["iters"]):
                R = np.eye(3)
                for i in range(1, 8):
                    x[i] += (tgo[i] - x[i]) * s.hold[i]
                    want = R @ rest[i]
                    cur = nz(x[i] - x[i - 1])
                    kb = o["root_k"] if i == 1 else o["bend"] * (1 - (i - 2) / 6 * o["bend_taper"])
                    fi = free[i]
                    if o["bend_gate"]: kb *= fi
                    if o["bend_mode"] == "once" and k > 0: kb = 0
                    was = cur
                    if kb > 0: cur = nz(cur + (want - cur) * kb)
                    lim = o["root_cone"] if i == 1 else o["bend_max"]
                    if lim is not None and o["cone_soft"]: lim = lim + (math.pi - lim) * (1 - fi)
                    if lim is not None and (not o["cap_gate"] or fi > 0.02) and lim < math.pi - 1e-6: cur = cone(cur, want, lim)
                    if o["bend_mode"] == "vn": xp[i] += (cur - was) * link[i]
                    newp = x[i - 1] + cur * link[i]
                    if o["dftl_sum"]: corr[i] += newp - x[i]
                    else: corr[i] = newp - x[i]
                    x[i] = newp
                    x[i] = s.collide(d, x[i], i, sc)
                    if x[i][1] < floor: x[i][1] = floor; s.touch[i] = [0, 1, 0]; s.grip[i] = o["grip_floor"]; s.grounded[i] = True; s.surf[i] = 0
                    if i < 7: R = rot_between(rest[i], nz(x[i] - x[i - 1]))
            if o["dftl"]:
                for i in range(1, 7): xp[i] = xp[i] + o["dftl"] * (gfree[i] if o["dftl_gate"] else 1) * corr[i + 1]
            for i in range(1, 8):
                if s.grip[i] == 0: continue
                if o["recede"]:
                    n = s.touch[i]; u = n * min(0, s.surf[i] @ n); r = vel[i] - u; r = r - n * min(0, r @ n)
                    xp[i] = x[i] - u - r * (1 - s.grip[i]); s.grip[i] = 0; s.surf[i] = 0
                else:
                    v = vel[i] - s.touch[i] * min(0, vel[i] @ s.touch[i])
                    xp[i] = x[i] - v * (1 - s.grip[i]); s.grip[i] = 0
        s.pd = d
        return x

def sim(fr, style, **o):
    m = Model(fr, style, **o)
    return [m.frame(d).copy() for d in fr]

def today(fr):
    """The chain as C# ran it (after each frame)."""
    return [fr[i + 1]["x"] for i in range(len(fr) - 1)] + [fr[-1]["x"]]

def angles(x):
    l = [nz(x[i] - x[i - 1]) for i in range(1, 8)]
    return np.degrees([math.acos(float(np.clip(l[i] @ l[i + 1], -1, 1))) for i in range(6)])

def metrics(fr, xs, frames=None):
    """Per frame: max joint angle, points above the root (m), past the crown along head Y (m), on the head ball, floor."""
    out = []
    for i in (frames if frames is not None else range(len(xs))):
        d = fr[i]; x = xs[i]; hd = d["head"]
        a = angles(x)
        up = max(x[j][1] - x[0][1] for j in range(1, 8))
        past = max((x[j] - hd[0]) @ hd[2] for j in range(1, 8)) - (x[0] - hd[0]) @ hd[2]
        r0 = d["r"][0] * 1.04
        onhead = sum(np.linalg.norm(x[j] - d["at"][0]) < r0 + 0.006 for j in range(2, 8))
        fl = sum(x[j][1] < d["ground"] + 0.02 for j in range(1, 8))
        out.append((i, a.max(), up, past, onhead, fl))
    return out

def swing(fr, xs):
    """Each frame's tip offset from its rest target."""
    return np.array([xs[i][7] - fr[i]["target"][7] for i in range(len(xs))])

def runlog(name):
    return load(S + "f19/hair9/" + name + ".log")

FIX = dict(BASE, scale=True)
