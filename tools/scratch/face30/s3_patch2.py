"""Face 30 S3 + H3: braid and ponytail side hairs (fine hairs end at the top of her ear at the sides; one lock a side)."""
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets\heroine_hair.py"
s = open(p, encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a))
    s = s.replace(a, b)


rep('''def hairline_hairs(comb, spacing=0.0026, points=8, sides=None):''',
    '''def hairline_hairs(comb, spacing=0.0026, points=8, sides=None, low=None):''')
rep('''    are; cut by hashed alpha they were a scatter of dots)."""
    out = []
    pts, nrm = roots(spacing, above=-0.001, below=0.022, soft=0.014)
    theta = np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))
    near = np.abs(np.degrees(theta)) < 125''', '''    are; cut by hashed alpha they were a scatter of dots). With `low`, none
    at her sides (past 40 degrees from her front) rooted below that height.
    (18 October, face 30: drawn back, the fine hairs before her ears ran
    down over her cheek, and in profile read as claw scratches at the Look
    and scars at the close-up, however far off her skin: braid and ponytail
    now end them at the top of her ear.)"""
    out = []

    def high(pts):
        if low is None:
            return np.ones(len(pts), bool)
        th = np.degrees(np.abs(np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))))
        return (th < 40) | (pts[:, 2] > low)
    pts, nrm = roots(spacing, above=-0.001, below=0.022, soft=0.014)
    theta = np.arctan2(pts[:, 0] - CENTRE[0], -(pts[:, 1] - CENTRE[1]))
    near = (np.abs(np.degrees(theta)) < 125) & high(pts)''')
rep('''    keep = RNG.random(len(pts)) < np.interp(th, [0, 35, 60], [0.6, 0.85, 1.0])''',
    '''    keep = (RNG.random(len(pts)) < np.interp(th, [0, 35, 60], [0.6, 0.85, 1.0])) & high(pts)''')
rep('''    out += hairline_hairs(comb, sides=no_part)
    out += tendrils()''', '''    out += hairline_hairs(comb, sides=no_part, low=float(HP[EAR, 2].max()) if EAR.any() else EYE_Z + 0.01)
    out += tendrils(per_side=1, lock=True)''')
rep('''def tendrils(per_side=9):''', '''def tendrils(per_side=9, lock=False):''')
rep('''    pick = []
    for sd in (1, -1):
        cand = np.where(ok & (np.sign(pts[:, 0]) == sd))[0]
        if len(cand):
            pick += list(RNG.choice(cand, min(per_side, len(cand)), replace=False))''', '''    pick = []
    for sd in (1, -1):
        cand = np.where(ok & (np.sign(pts[:, 0]) == sd))[0]
        if len(cand) and lock:
            # (18 October, face 30: nine fine ones a side still read as claw
            # scratches across her cheek in profile. Now one, a lock: thicker,
            # tapered to its tip, from her temple to her jaw, wide of her face)
            pick += list(cand[np.argsort(np.abs(th[cand] - 60) + np.abs(pts[cand, 2] - EYE_Z - 0.03) * 300)[:per_side]])
        elif len(cand):
            pick += list(RNG.choice(cand, min(per_side, len(cand)), replace=False))''')
rep('''    L = RNG.uniform(0.11, 0.17, len(pts))
    # (18 October, face 29's judge''', '''    L = RNG.uniform(0.11, 0.17, len(pts)) if not lock else np.full(len(pts), 0.125)
    # (18 October, face 29's judge''')
rep('''    P = wave(P, 0.005, 0.07, pts)
    c = cards(P, RNG.uniform(0.007, 0.013, len(pts)), list(range(8, 15)), 0.010, narrow=0.65, face=(0.0, -1.0, 0.0), floor=0.004)
    c["alpha"] = np.repeat(RNG.uniform(0.75, 1.0, len(pts)) * 0.75, 3 * 16)
    c["mat"] = 3
    c["blue"] = 0.35''', '''    P = wave(P, 0.005, 0.07, pts)
    if lock:
        c = cards(P, np.full(len(pts), 0.016), [11, 12, 13], 0.010, narrow=0.85, face=(0.0, -1.0, 0.0), floor=0.004)
        print("  tendrils: %d locks" % len(pts))
        return [c]
    c = cards(P, RNG.uniform(0.007, 0.013, len(pts)), list(range(8, 15)), 0.010, narrow=0.65, face=(0.0, -1.0, 0.0), floor=0.004)
    c["alpha"] = np.repeat(RNG.uniform(0.75, 1.0, len(pts)) * 0.75, 3 * 16)
    c["mat"] = 3
    c["blue"] = 0.35''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
