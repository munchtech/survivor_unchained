p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\pages.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''BUILD = {
    "header": ("frames/header.png", header),''', '''def ember_light(R, hole_mask, cx, cy, size, seed):
    """The ember asleep in a coin's hole: a dull red-orange, hottest low in the hole."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    n = F.fbm(R.h, R.w, scale=max(8, R.w / 6), octaves=3, seed=seed) * 0.5 + 0.5
    d = np.hypot(X - cx, Y - (cy + size * 0.06)) / (size * 0.18)
    g = hole_mask * np.exp(-d ** 2 * 1.2) * (0.6 + 0.6 * n)
    return (g[..., None] * (F.hexc("#ff7a2a") * 1.1 + F.hexc("#9a2004") * 0.8)).astype(np.float32)


def column_divider(ss=4, samples=128):
    """The rule between a page's columns (frames/column_divider.png, 48x1120, 24x560 shown,
    slice 0 24 0 24, the middle tiled): a rod of the binders' twisted iron, two strands, with a
    forged collar every 128 px; its ends fade into the page. The slice repeats only the middle
    (512 shown), so the twist and the collars are periodic over exactly that, and the ends
    carry on the same pattern. The stone at its middle is a piece of its own."""
    TW, END, PER = 48, 48, 1024            # file px: width, each end, the repeating middle
    TH = PER + 2 * END
    PAD = 256                              # rendered past both ends, cropped (the light's edge)
    R = RL.Relief(TW, TH + 2 * PAD, ss)
    X, Y = R.xx / ss, R.yy / ss
    Yp = Y - PAD - END                     # 0 where the repeating middle starts
    cx = TW / 2
    across = X - cx
    th = 4.6 * K
    pitch = PER / 98.0
    s_ = Yp / pitch
    tw = np.zeros_like(X)
    for k0 in (0.0, 0.5):
        uu = ((across / th) - (((s_ + k0) % 1.0) - 0.5)) % 1.0 - 0.5
        tw = np.maximum(tw, np.sqrt(np.clip(1 - (uu / 0.5) ** 2, 0, 1)))
    rod_m = np.clip((th / 2 - np.abs(across)) * ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    h = (tw * 0.55 + edge * 0.45) * 2.6 * K * (rod_m > 0.02)
    shape = edge * 2.6 * K * (rod_m > 0.02)
    # A collar every 128 px: a short forged band round the rod, its edges chamfered.
    col = np.zeros_like(X)
    for k0 in range(-2, int((TH + 2 * PAD) / K / 128) + 2):
        yc = (k0 + 0.5) * 128 * K
        dy = np.abs(Yp - yc)
        band = (np.abs(across) < 4.6 * K) & (dy < 3.2 * K)
        prof = np.sqrt(np.clip(1 - (across / (4.6 * K)) ** 2, 0, 1)) * 3.4 * K * np.clip((3.2 * K - dy) / (1.0 * K), 0, 1) ** 0.5
        h = np.where(band, np.maximum(h, prof), h)
        shape = np.where(band, np.maximum(shape, prof), shape)
        col = np.maximum(col, band.astype(np.float32))
    dents = RL.hammered(R, cell=2.5 * K, depth=0.08 * K, seed=101) / ss
    h = h + dents * (col > 0.5)
    R.height = (h * ss).astype(np.float32)
    R.shape_height = (shape * ss).astype(np.float32)
    R.alpha = np.maximum(rod_m, col).astype(np.float32)
    R.mat[:] = RL.IDS["iron"]
    R.mat[col > 0.5] = RL.IDS["iron_dark"]
    R.tint = np.ones((R.h, R.w, 3), np.float32) * np.array([1.0, 0.95, 0.86], np.float32)
    img = R.render("page_divider", samples=samples, wear=1.4, grime=0.7, seed=102)
    small = R.file_size(img)
    mid = small[PAD:PAD + TH].copy()
    # A soft shadow either side, so it lies on the page and is not pasted on it.
    a = mid[..., 3]
    sh = cv2.GaussianBlur(a, (0, 0), 3.0 * K) * 0.45
    sh = np.roll(sh, int(1.5 * K), axis=1)
    out_a = a + sh * (1 - a)
    rgb = mid[..., :3] * a[..., None] / np.maximum(out_a[..., None], 1e-4)
    out = np.dstack([rgb, out_a]).astype(np.float32)
    # The ends fade (the slice's 24 px top and bottom are the ends, the middle repeats).
    yy = np.arange(TH, dtype=np.float32)[:, None] / K
    fade = np.clip(yy / 24.0, 0, 1) * np.clip((TH / K - yy) / 24.0, 0, 1)
    out[..., 3] *= fade ** 1.5
    return out


def coin_piece(size_shown, ss=8, samples=160, name="coin", rot=45.0, glow=1.0):
    """A binders' coin by itself, set on its point, its hole lit by the sleeping ember."""
    W = int(size_shown * K)
    R = RL.Relief(W, W, ss)
    c = W / 2
    hh, cm, hm = RL.coin(R, c, c, W * 0.86, 1.0, hole=0.34, rot=rot)
    R.height = (hh * cm * ss).astype(np.float32)
    R.shape_height = R.height.copy()
    R.alpha = cm.astype(np.float32)
    R.mat[:] = RL.IDS["gold_dim"]
    R.mat[hm > 0.5] = RL.IDS["ember"]
    R.emit = ember_light(R, hm, c, c, W * 0.86, seed=103) * glow
    img = R.render(f"page_{name}", samples=samples, wear=1.3, grime=0.8, seed=104)
    return R.file_size(img)


def column_divider_stone():
    """The stone at a divider's middle (frames/column_divider_stone.png, 64x64, 32x32 shown)."""
    return coin_piece(32, name="divider_stone")


def section_mark():
    """Before a section's title on its baseline (ornaments/section_mark.png, 24x24, 12x12
    shown): a small binders' coin, its ember barely awake."""
    return coin_piece(12, ss=16, name="section_mark", glow=0.8)


BUILD = {
    "header": ("frames/header.png", header),
    "column_divider": ("frames/column_divider.png", column_divider),
    "column_divider_stone": ("frames/column_divider_stone.png", column_divider_stone),
    "section_mark": ("ornaments/section_mark.png", section_mark),''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
