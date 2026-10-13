# Replica of HairSway.cs (round 3) driven by a HAIRDUMP=1 log; exact to 1e-4 a frame (see chainrep2 for variants, chainplot for views).
"""Offline replica of HairSway's chain driven by a HAIRDUMP log: rep.py LOG [model] -> validates (model 'cur') and plots."""
import json, sys, numpy as np

def load(log):
    fr = []
    for line in open(log, encoding="utf-8", errors="ignore"):
        if line.startswith("HAIRDUMP "):
            d = json.loads(line[9:])
            for k in ("target", "x", "xp", "at", "back", "across", "head"): d[k] = np.array(d[k], float)
            d["r"] = np.array(d["r"]); d["behind"] = np.array(d["behind"], bool)
            fr.append(d)
    # from the last fresh start (x == target)
    start = max(i for i, d in enumerate(fr) if np.abs(d["x"] - d["target"]).max() < 1e-6)
    return fr[start:]

def nz(v):
    n = np.linalg.norm(v); return v / n if n > 1e-12 else v

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

class Cur:
    """The C# solver as of round 3."""
    def __init__(s, fr):
        s.link = np.r_[0, np.linalg.norm(np.diff(fr[0]["target"], axis=0), axis=1)]
        s.keep = (1 - np.arange(8) / 7.0) ** 3
        s.hold = np.zeros(8); s.grip = np.zeros(8); s.touch = np.zeros((8, 3)); s.grounded = np.zeros(8, bool)
        s.offFloor = 1e3; s.hungFor = np.zeros(8); s.live = False; s.stiff = fr[0]["stiff"]
    def frame(s, d):
        tg, dt = d["target"], d["dt"]; stiff = s.stiff
        lying = s.grounded[1:].any(); s.grounded[:] = False
        s.offFloor = 0 if lying else s.offFloor + dt
        level = 1
        for i in range(1, 8):
            u = smooth(0.35, 0.85, nz(tg[i] - tg[0]) @ [0, -1, 0])
            level = min(level, smooth(-0.3, 0.1, nz(tg[i] - tg[i - 1]) @ [0, -1, 0]))
            k = s.keep[i] * (0.5 + 0.5 * level if i == 1 else level)
            want = stiff * (k + (1 - k) * u)
            s.hungFor[i] = s.hungFor[i] + dt if u > 0.98 else 0
            if not s.live or want <= s.hold[i]: s.hold[i] = want
            elif s.offFloor > 0.5 and s.hungFor[i] > 0.5: s.hold[i] = min(want, s.hold[i] + stiff * dt / 0.5)
        if not s.live:
            s.x = tg.copy(); s.xp = tg.copy(); s.rootThen = tg[0].copy(); s.offFloor = 1e3; s.live = True
        steps = max(1, int(np.ceil(dt * 120 - 1e-3))); h = dt / steps
        fall = np.array([0, -9.8, 0]) * h * h; floor = d["ground"] + 0.015
        rootStep = (tg[0] - s.rootThen) / steps; s.rootThen = tg[0].copy(); most = 2.5 * h
        x, xp = s.x, s.xp; vel = np.zeros((8, 3))
        for st in range(steps):
            for i in range(1, 8):
                was = x[i].copy(); vel[i] = (x[i] - xp[i]) * 0.985
                rel = vel[i] - rootStep
                if rel @ rel > most * most: vel[i] = rootStep + nz(rel) * most
                x[i] = x[i] + vel[i] + fall; xp[i] = was
            x[0] = tg[0]
            for k in range(3):
                for i in range(1, 8):
                    x[i] += (tg[i] - x[i]) * s.hold[i]
                    x[i] = x[i - 1] + nz(x[i] - x[i - 1]) * s.link[i]
                    s.collide(d, x, i)
                    if x[i][1] < floor: x[i][1] = floor; s.touch[i] = [0, 1, 0]; s.grip[i] = 0.5; s.grounded[i] = True
            for i in range(1, 8):
                if s.grip[i] == 0: continue
                v = vel[i] - s.touch[i] * min(0, vel[i] @ s.touch[i])
                xp[i] = x[i] - v * (1 - s.grip[i]); s.grip[i] = 0
        return x
    def collide(s, d, x, i):
        for b in range(len(d["r"])):
            w = d["across"][b]; ww = w @ w; at = d["at"][b]
            c = at + w * np.clip((x[i] - at) @ w / ww, -1, 1) if ww > 0 else at
            off = x[i] - c; r = d["r"][b]
            if off @ off >= r * r: continue
            bk = d["back"][b]
            if d["behind"][b] and off @ bk < 0: off = off - 2 * (off @ bk) * bk
            n = nz(off) if off @ off > 1e-10 else bk
            x[i] = c + n * r; s.touch[i] = n; s.grip[i] = max(s.grip[i], 0.1)

def simulate(fr, model):
    out = []
    for d in fr:
        out.append(model.frame(d).copy())
    return out

if __name__ == "__main__":
    fr = load(sys.argv[1])
    xs = simulate(fr, Cur(fr))
    err = [np.abs(xs[i] - fr[i + 1]["x"]).max() for i in range(len(fr) - 1)]
    print("frames", len(fr), "max err", max(err), "per frame", np.round(err, 4)[:50])

ART = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/"
def jlinks(style):
    P = np.array(json.load(open(ART + f"heroine_hair_{style}.chain.json"))["points"])
    return np.r_[0, np.linalg.norm(np.diff(P, axis=0), axis=1)]
