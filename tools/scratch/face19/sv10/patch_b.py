"""patch_b.py: add option 'sm' to hs10's loop: before each pass, a joint bent past sm degrees has its point drawn toward the
middle of its neighbours (a stiff braid rounds a corner by moving the corner, not by throwing what hangs below it out):
smk the share at full (ramped over smw degrees), smheld gate by the hold (1-free), smvn velocity-neutral."""
p = open("hs10.py").read()
old = """        for k in range(3):
            R = np.eye(3)
            for i in range(1, 8):
                x[i] += (tgo[i] - x[i]) * s.hold[i]"""
new = """        for k in range(3):
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
                x[i] += (tgo[i] - x[i]) * s.hold[i]"""
assert old in p; p = p.replace(old, new); open("hs10.py", "w").write(p); print("ok")
