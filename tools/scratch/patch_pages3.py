p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\pages.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''K = 2.0   # file px per shown px
PAINT = False''', '''K = 2.0   # file px per shown px
# The renders are crisp at twice their size already; a paint-over on a strip a band's height
# softens it (the painting is made at a megapixel), so the header keeps its render.
PAINT = False''')
rep('''  header         frames/header.png, 1024x200 (512x100 shown), slice 0 0 0 12, tiled along:
                 the band across every page's head. Worked oxblood leather, blind-tooled
                 with a double rule and a row of punched lozenges, darkening to the screen's
                 edge; along its foot a slim forged rail with the binders' twisted wire laid
                 in it and a nail every hand's width; a soft shadow cast on the page below.''',
    '''  header         frames/header.png, 1024x200 (512x100 shown), slice 0 0 0 12, tiled along:
                 the band across every page's head. Worked oxblood leather, darkening to the
                 screen's edge, blind-tooled along the top (a double rule, punched lozenges)
                 and with one fine rule over the rail, so it is calm where the page writes
                 (the tabs, the title, its line, down to y 80); at its foot a slim forged rail
                 with the binders' twisted wire laid in it and a nail every hand's width.
  backdrop_grain page/backdrop_grain.png, 512x512, tiled: grain and dust over the blurred world
                 (light and dark specks at low alpha; never a fill).
  backdrop_edges page/backdrop_edges.png, 1920x1080, stretched: smoke drifting in from the
                 edges and the ember's light low along the foot; clear in the middle.''')
rep('''    tint = np.where(leather, (0.55 + 0.4 * cloud) * fall * (1 - tool * 0.35), 1.0)
    R.tint = (tint[..., None] * np.ones(3, np.float32)).astype(np.float32)''', '''    tint = np.where(leather, (0.55 + 0.4 * cloud) * fall * (1 - tool * 0.35), 1.0)
    R.tint = (tint[..., None] * np.ones(3, np.float32)).astype(np.float32)
    # The rail's iron a little warmer than the house's (its cool rim went navy over the warm page).
    R.tint = np.where(on_rail[..., None], R.tint * np.array([1.0, 0.94, 0.84], np.float32), R.tint).astype(np.float32)''')
rep('''BUILD = {
    "header": ("frames/header.png", header),
}''', '''def backdrop_grain(N=512):
    """Grain and dust, tileable: light specks and dark ones at a low alpha, so the blurred
    world behind has a surface (a film's grain, ash in the air) and never a fill."""
    g = F.fbm(N, N, scale=1.6, octaves=2, seed=91)
    g = g / (np.abs(g).max() + 1e-6)
    coarse = F.fbm(N, N, scale=40, octaves=3, seed=92) * 0.5 + 0.5
    amp = 0.10 + 0.05 * coarse
    a = np.abs(g) * amp
    light = g > 0
    rgb = np.where(light[..., None], np.array([1.0, 0.92, 0.82], np.float32), np.array([0.02, 0.015, 0.01], np.float32))
    # Ash: a few soft specks, warm, a little bigger than the grain.
    rng = np.random.default_rng(93)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    for _ in range(70):
        cx, cy, r = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(0.6, 1.8)
        dx = (xx - cx + N / 2) % N - N / 2
        dy = (yy - cy + N / 2) % N - N / 2
        sp = np.exp(-(dx * dx + dy * dy) / (2 * r * r)) * rng.uniform(0.12, 0.3)
        a = np.maximum(a, sp)
        rgb = np.where((sp > a * 0.9)[..., None], np.array([0.85, 0.72, 0.6], np.float32), rgb)
    return np.dstack([rgb, np.clip(a, 0, 1)]).astype(np.float32)


def backdrop_edges(W=1920, H=1080):
    """Smoke drifting in from the edges, thickest in the corners, and the ember's light low
    along the foot; clear in the middle where the page is read. Made at half and enlarged:
    there is nothing sharp in it."""
    w, h = W // 2, H // 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    # Smoke: warped noise, so it curls instead of blotting.
    wx = F.fbm(h, w, scale=180, octaves=3, seed=94) * 40
    wy = F.fbm(h, w, scale=180, octaves=3, seed=95) * 40
    base = F.fbm(h, w, scale=120, octaves=5, seed=96)
    smoke = cv2.remap(base.astype(np.float32), (xx + wx).astype(np.float32), (yy + wy).astype(np.float32), cv2.INTER_LINEAR,
                      borderMode=cv2.BORDER_WRAP)
    smoke = np.clip(smoke * 0.5 + 0.5, 0, 1) ** 1.6
    edge = np.clip(1 - np.minimum(np.minimum(u, 1 - u) / 0.22, np.minimum(v, 1 - v) / 0.3), 0, 1) ** 1.3
    corner = np.clip(1 - np.hypot(np.minimum(u, 1 - u) / 0.35, np.minimum(v, 1 - v) / 0.45), 0, 1)
    dens = np.clip(smoke * (edge * 0.8 + corner * 0.6), 0, 1)
    a_smoke = dens * 0.55
    # Low: the ember's light along the foot, in pools, and lighting the smoke that lies there.
    pools = F.fbm(h, w, scale=260, octaves=2, seed=97) * 0.5 + 0.5
    low = np.clip((v - 0.62) / 0.38, 0, 1) ** 1.8 * (0.5 + 0.7 * pools)
    ember = np.array([1.0, 0.45, 0.12], np.float32)
    dark = np.array([0.07, 0.05, 0.045], np.float32)
    lit = np.array([0.42, 0.24, 0.14], np.float32)
    smoke_col = dark * (1 - low[..., None]) + lit * low[..., None]
    a_ember = low * 0.22
    a = a_smoke + a_ember * (1 - a_smoke)
    rgb = (smoke_col * a_smoke[..., None] + ember * (a_ember * (1 - a_smoke))[..., None]) / np.maximum(a[..., None], 1e-4)
    img = np.dstack([rgb, a]).astype(np.float32)
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC).clip(0, 1)


BUILD = {
    "header": ("frames/header.png", header),
    "backdrop_grain": ("page/backdrop_grain.png", backdrop_grain),
    "backdrop_edges": ("page/backdrop_edges.png", backdrop_edges),
}''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
