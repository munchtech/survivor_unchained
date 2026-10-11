"""Offline replica of HairSway's chain (old and new solver), to tune the stiffness profile.
Scenarios: face down with the head pitched back 35 deg (death's rest), standing still, a run start."""
import json, sys, numpy as np
ART = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/godot/art/people/"

def rotx(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def load(style):
    d = json.load(open(ART + f"heroine_hair_{style}.chain.json"))
    P = np.array(d["points"]); B = [(s["bone"], np.array(s["at"]), s["r"]) for s in d["spheres"]]
    return d["bone"], d["stiff"], P, B

def run(style, solver, scene, fps=30, secs=3.0, K=None, q=None, floor=True):
    bone, stiff, P, B = load(style)
    link = np.r_[0, np.linalg.norm(np.diff(P, axis=0), axis=1)]
    neck = np.array([0, 1.60, -0.03])
    def pose(tm):
        # body rotation about the ankles, head extra pitch about the neck; returns (point xf for bone, ball xf)
        if scene == "facedown":
            Rb = rotx(np.pi / 2); Tb = np.array([0, 0.15, 0.0])   # face down, front 15 cm above floor
            Rh = Rb @ rotx(np.radians(35))                        # chin up 35 deg (head tipped back)
        elif scene == "stand":
            Rb = np.eye(3); Tb = np.zeros(3); Rh = Rb
        else:  # run: lean 15 deg, moving +z at 4 m/s from t=0.5
            Rb = rotx(np.radians(15) if tm > 0.5 else 0); Tb = np.array([0, 0, 4.0 * max(0, tm - 0.5)]); Rh = Rb
        bx = lambda R, p: Tb + Rb @ neck + R @ (p - neck)
        return bx, Rh, Rb
    h0 = 1 / 120
    dt = 1 / fps; steps = 4 if solver == 'old' else max(1, int(np.ceil(dt * 120 - 1e-6))); h = dt / steps
    x = xp = None; out = []
    for f in range(int(secs * fps)):
        tm = f * dt
        bx, Rh, Rb = pose(tm)
        tgt = np.array([bx(Rh if bone == "Head" else Rb, p) for p in P])
        balls = [(bx(Rh if n == "Head" else Rb, a), r, n != "Head", Rb @ np.array([0, 0, -1.0])) for n, a, r in B]
        if x is None: x = tgt.copy(); xp = tgt.copy()
        for s in range(steps):
            if solver == "old":
                v = (x - xp) * 0.985; fall = np.array([0, -9.8, 0]) * h * h
            else:
                v = (x - xp) * 0.985 ** (h / h0); fall = np.array([0, -9.8, 0]) * h * h
            xp = x.copy(); x = x + v + fall; x[0] = tgt[0]
            if solver != "old":
                t = np.arange(8) / 7.0
                d = tgt - tgt[0]; d[0] = [0, -1, 0]
                u = np.clip(-(d[:, 1]) / np.maximum(np.linalg.norm(d, axis=1), 1e-9), 0, 1)
                ks = stiff * ((1 - t) ** q + (1 - (1 - t) ** q) * u ** K)
            for k in range(3):
                for i in range(1, 8):
                    x[i] += (tgt[i] - x[i]) * (stiff if solver == "old" else ks[i])
                    x[i] = x[i - 1] + (x[i] - x[i - 1]) / np.linalg.norm(x[i] - x[i - 1]) * link[i]
                    for c, r, behind, back in balls:
                        off = x[i] - c
                        if off @ off >= r * r: continue
                        side = Rb @ np.array([1.0, 0, 0])
                        if behind and off @ back < 0 and (solver == "old" or abs(off @ side) < 0.6 * r): off = off - 2 * (off @ back) * back
                        x[i] = c + off / max(np.linalg.norm(off), 1e-9) * r
                    if floor and solver != "old": x[i][1] = max(x[i][1], 0.01)
        out.append(x.copy())
    return np.array(out), tgt

if __name__ == "__main__":
    cfgs = [("old", {})] + [(f"p{K}q{q}", dict(K=K, q=q)) for K, q in [(2, 2), (2, 3), (4, 3), (8, 3)]]
    for style in ("braid", "ponytail", "long"):
        for name, kw in cfgs:
            sol = "old" if name == "old" else "new"
            res = []
            for fps in (30, 60):
                X, tgt = run(style, sol, "facedown", fps=fps, secs=4, **kw)
                last = X[-fps:]                      # the last second
                hi = last[:, 1:, 1].max(1).mean()    # the chain's highest point (back surface ~0.28)
                res.append(f"fd{fps} tip {last[:,7,1].mean():.2f} hi {hi:.2f} wob {last[:,7,1].std():.3f}")
            Xs, tg = run(style, sol, "stand", **kw)
            dev = np.linalg.norm(Xs[-1] - tg, axis=1).max()
            Xr, _ = run(style, sol, "run", secs=2.5, **kw)
            sw = np.abs(Xr[:, 7, 2] - Xr[:, 0, 2])
            print(f"{style:8s} {name:9s} {' | '.join(res)} | stand {dev:.3f} | run tipz-rootz max {sw.max():.2f} end {sw[-1]:.2f}")
