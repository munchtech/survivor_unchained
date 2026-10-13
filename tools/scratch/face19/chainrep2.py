"""Variants of the chain solver for experiments (offline, on HAIRDUMP logs)."""
import numpy as np
from chainrep import load, nz, smooth, jlinks

def rot_between(a, b):
    """Rotation matrix taking unit a to unit b (minimal)."""
    v = np.cross(a, b); c = float(a @ b)
    if c < -0.999999:
        p = np.cross(a, [1, 0, 0]);
        if p @ p < 1e-6: p = np.cross(a, [0, 1, 0])
        p = nz(p); return 2 * np.outer(p, p) - np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)

class Solver:
    def __init__(s, fr, style, **o):
        s.o = dict(scale_links=True, bend=0.0, bend_max=None, root_cone=None, root_k=0.0, push_targets=False,
                   dftl=0.0, hold_mode="cur", damp=0.985, cap=2.5, iters=3, grip_ball=0.1, grip_floor=0.5)
        s.o.update(o)
        s.link0 = jlinks(style)
        s.keep = (1 - np.arange(8) / 7.0) ** 3
        s.hold = np.zeros(8); s.grip = np.zeros(8); s.touch = np.zeros((8, 3)); s.grounded = np.zeros(8, bool)
        s.offFloor = 1e3; s.hungFor = np.zeros(8); s.live = False; s.stiff = fr[0]["stiff"]
    def holds(s, tg, dt):
        stiff = s.stiff
        lying = s.grounded[1:].any(); s.grounded[:] = False
        s.offFloor = 0 if lying else s.offFloor + dt
        if s.o["hold_mode"] == "none": s.hold[:] = 0; return
        level = 1
        for i in range(1, 8):
            u = smooth(0.35, 0.85, nz(tg[i] - tg[0]) @ [0, -1, 0])
            level = min(level, smooth(-0.3, 0.1, nz(tg[i] - tg[i - 1]) @ [0, -1, 0]))
            k = s.keep[i] * (0.5 + 0.5 * level if i == 1 else level)
            if s.o["hold_mode"] == "upright": k = 0
            want = stiff * (k + (1 - k) * u)
            s.hungFor[i] = s.hungFor[i] + dt if u > 0.98 else 0
            if not s.live or want <= s.hold[i]: s.hold[i] = want
            elif s.offFloor > 0.5 and s.hungFor[i] > 0.5: s.hold[i] = min(want, s.hold[i] + stiff * dt / 0.5)
    def collide_pt(s, d, p, i=None):
        hit = False
        for b in range(len(d["r"])):
            r = d["r"][b] * (1.04 if s.o["scale_links"] else 1.0)
            if r <= 0: continue
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((p - at) @ w / ww, -1, 1) if ww > 0 else at
            off = p - c
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0: off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            p = c + n * r; hit = True
            if i is not None: s.touch[i] = n; s.grip[i] = max(s.grip[i], s.o["grip_ball"])
        return p, hit
    def frame(s, d):
        o = s.o; tg = d["target"].copy(); dt = d["dt"]
        if o["scale_links"]: link = np.r_[0, np.linalg.norm(np.diff(tg, axis=0), axis=1)]
        else: link = s.link0
        s.holds(tg, dt)
        if not s.live:
            s.x = tg.copy(); s.xp = tg.copy(); s.rootThen = tg[0].copy(); s.offFloor = 1e3; s.live = True
        floor = d["ground"] + 0.015
        tgo = tg.copy()
        if o["push_targets"]:
            for i in range(1, 8):
                tgo[i], _ = s.collide_pt(d, tgo[i]); tgo[i][1] = max(tgo[i][1], floor)
        steps = max(1, int(np.ceil(dt * 120 - 1e-3))); h = dt / steps
        fall = np.array([0, -9.8, 0]) * h * h
        rootStep = (tg[0] - s.rootThen) / steps; s.rootThen = tg[0].copy(); most = o["cap"] * h
        x, xp = s.x, s.xp; vel = np.zeros((8, 3))
        rest = [nz(tg[i] - tg[i - 1]) for i in range(1, 8)]; rest.insert(0, None)
        for st in range(steps):
            for i in range(1, 8):
                was = x[i].copy(); vel[i] = (x[i] - xp[i]) * o["damp"]
                rel = vel[i] - rootStep
                if o["cap"] and rel @ rel > most * most: vel[i] = rootStep + nz(rel) * most
                x[i] = x[i] + vel[i] + fall; xp[i] = was
            x[0] = tg[0]
            corr = np.zeros((8, 3))
            for k in range(o["iters"]):
                R = np.eye(3)
                for i in range(1, 8):
                    x[i] += (tgo[i] - x[i]) * s.hold[i]
                    # bending: link i toward the rest bend from link i-1 (R carries rest into now)
                    want = R @ rest[i]
                    cur = nz(x[i] - x[i - 1])
                    kb = o["root_k"] if i == 1 else o["bend"] * (1 - (i - 2) / 6 * o.get("bend_taper", 0.0))
                    if kb > 0:
                        cur = nz(cur + (want - cur) * kb)
                    lim = o["root_cone"] if i == 1 else o["bend_max"]
                    if lim is not None:
                        ang = np.arccos(np.clip(cur @ want, -1, 1))
                        if ang > lim:
                            ax_ = np.cross(want, cur)
                            if ax_ @ ax_ < 1e-12: ax_ = np.cross(want, [1, 0, 0])
                            ax_ = nz(ax_)
                            # rotate want toward cur by lim
                            cur = want * np.cos(lim) + np.cross(ax_, want) * np.sin(lim) + ax_ * (ax_ @ want) * (1 - np.cos(lim))
                    newp = x[i - 1] + cur * link[i]
                    corr[i] = newp - x[i]
                    x[i] = newp
                    x[i], _ = s.collide_pt(d, x[i], i)
                    if x[i][1] < floor: x[i][1] = floor; s.touch[i] = [0, 1, 0]; s.grip[i] = o["grip_floor"]; s.grounded[i] = True
                    R = rot_between(rest[i], nz(x[i] - x[i - 1])) if i < 7 else R
            if o["dftl"]:
                for i in range(1, 7): xp[i] = xp[i] + o["dftl"] * corr[i + 1]   # (Muller 2012: v -= s * d_next / h)
            for i in range(1, 8):
                if s.grip[i] == 0: continue
                v = vel[i] - s.touch[i] * min(0, vel[i] @ s.touch[i])
                xp[i] = x[i] - v * (1 - s.grip[i]); s.grip[i] = 0
        return x

def sim(fr, style, **o):
    m = Solver(fr, style, **o)
    return [m.frame(d).copy() for d in fr]
