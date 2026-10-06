p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\cardcolour.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''    n = F.fbm(h, w, scale=14, octaves=4, seed=31)
    rime = np.clip((edge * 1.6 + up * 0.8) * (0.55 + n * 0.8), 0, 1) * (m > 0.2)
    white = F.hexc("#e8f6ff", lin=False)
    rgb = rgb * (1 - rime[..., None] * 0.9) + white * rime[..., None] * 0.9''', '''    n = F.fbm(h, w, scale=14, octaves=4, seed=31)
    # Crystalline, not a paste: fine flecks where the crust is, thickest at the edges.
    fleck = np.clip((F.fbm(h, w, scale=2.5, octaves=2, seed=33) + 0.15) * 3, 0, 1)
    rime = np.clip((edge * 1.6 + up * 0.8) * (0.55 + n * 0.8), 0, 1) * (m > 0.2) * (0.45 + 0.55 * fleck)
    white = F.hexc("#e8f6ff", lin=False)
    rgb = rgb * (1 - rime[..., None] * 0.9) + white * rime[..., None] * 0.9''')
rep('''    for y_bar, x0, x1 in ((98, 100, 636), (954, 100, 636)):''', '''    # Hoarfrost: needles grown out from the iron's outer edges into the air.
    outer = (cv2.dilate((m > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8)) - (m > 0.5)).astype(bool)
    ey, ex = np.nonzero(outer)
    gy_, gx_ = np.gradient(cv2.GaussianBlur(m, (0, 0), 3))
    for k in rng.choice(len(ex), 420, replace=False):
        x, y = ex[k], ey[k]
        nx_, ny_ = -gx_[y, x], -gy_[y, x]
        nn = math.hypot(nx_, ny_)
        if nn < 1e-3:
            continue
        nx_, ny_ = nx_ / nn, ny_ / nn
        L = rng.uniform(3, 9)
        a = math.atan2(ny_, nx_) + rng.uniform(-0.5, 0.5)
        d.line([(x * SS, y * SS), ((x + L * math.cos(a)) * SS, (y + L * math.sin(a)) * SS)], fill=(230, 244, 255, 220), width=SS)
    for y_bar, x0, x1 in ((98, 100, 636), (954, 100, 636)):''')
rep('''SEED = {"uncommon": 690, "rare": 691}
DENOISE = (0.46, 0.54)''', '''SEED = {"uncommon": 690, "rare": 693}
# The bramble paints well from words at a middling denoise; the rime does not (the paint takes
# it for the iron's own light), so the rare is painted lower and keeps its dressing.
DENOISE = {"uncommon": (0.46, 0.54), "rare": (0.3, 0.38)}''')
rep('''        for dn in DENOISE:''', '''        for dn in DENOISE[k]:''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
