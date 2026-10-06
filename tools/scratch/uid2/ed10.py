p = 'tools/assets/heroine_paint.py'
s = open(p, encoding='utf-8').read()
old_w = s[s.index('    # The brush\'s strokes, down her face'):s.index('def ochre(')]
s = s.replace(old_w, '''    # The brush's strokes, down her face: streaks of thicker and thinner paint;
    # at the edge, the bristles' lines broken where the brush ran dry.
    streak = noise((h, w), 14, seed + 1)
    streak = cv2.resize(cv2.resize(streak, (w, h // 10)), (w, h))
    bristle = cv2.resize(cv2.resize(noise((h, w), 3, seed + 3), (w, h // 24)), (w, h))
    near_edge = np.clip(1 - (xx - edge) / 46, 0, 1)
    broken = np.clip((bristle - 0.62 * near_edge) / 0.12 + 0.5, 0, 1) ** 0.6
    fill = inside * (0.86 + 0.14 * streak) * (1 - near_edge * (1 - broken))
    lay(L, fill.astype(np.float32), blue, 0.95, grain, through=0.35)
    return L


''')
old_o = s[s.index('    ey = (f[\'holes\'][0].nonzero()[0].mean() + f[\'holes\'][1].nonzero()[0].mean()) / 2\n    for k, dy in enumerate((-36, 32)):'):s.index('def ash(')]
s = s.replace(old_o, '''    ey = (f['holes'][0].nonzero()[0].mean() + f['holes'][1].nonzero()[0].mean()) / 2
    # (the two fingers' tracks one band: where they overlap it is no thicker)
    cov = np.zeros(shape, np.float32)
    for k, dy in enumerate((-26, 24)):
        pts = [(TEMPLE_R[0] + 30, ey + dy + 26), (650, ey + dy - 2), (MID, ey + dy - 12), (1450, ey + dy - 2), (TEMPLE_L[0] - 30, ey + dy + 24)]
        c = stroke(shape, pts, [92, 98, 96, 92, 70], dry=0.55, streaks=0.5, soft=0.3, seed=seed + k, taper=(0.04, 0.12), streak_px=8, edge=0.45)
        cov = np.maximum(cov, c)
    lay(L, cov, red, 0.92, grain, through=0.45)
    return L


''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
