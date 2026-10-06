p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\cardcolour.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep('''def leaf(d, cx, cy, ang, L, W, col, rib):
    """A bramble leaf: pointed at both ends, toothed a little, a darker midrib."""
    c, s = math.cos(ang), math.sin(ang)
    pts = []
    for t in np.linspace(0, math.pi, 14):
        r = W / 2 * math.sin(t) * (1 + 0.12 * math.sin(t * 9))
        u = -L / 2 * math.cos(t)
        pts.append((u, r))
    for t in np.linspace(math.pi, 0, 14):
        r = -W / 2 * math.sin(t) * (1 + 0.12 * math.sin(t * 9))
        u = -L / 2 * math.cos(t)
        pts.append((u, r))
    P = [((cx + u * c - v * s) * SS, (cy + u * s + v * c) * SS) for u, v in pts]
    d.polygon(P, fill=col)
    d.line([((cx - L / 2 * c) * SS, (cy - L / 2 * s) * SS), ((cx + L / 2 * c) * SS, (cy + L / 2 * s) * SS)], fill=rib, width=SS)''',
    '''def leaf(d, cx, cy, ang, L, W, col, rib):
    """A bramble leaf: pointed at both ends, toothed a little, folded along its midrib so
    one half takes the light (upper left) and the other is in shade."""
    c, s = math.cos(ang), math.sin(ang)

    def half(sign):
        pts = [(-L / 2, 0)]
        for t in np.linspace(0, math.pi, 16)[1:-1]:
            r = W / 2 * math.sin(t) ** 0.8 * (1 + 0.14 * math.sin(t * 11))
            pts.append((-L / 2 * math.cos(t), sign * r))
        pts.append((L / 2, 0))
        return [((cx + u * c - v * s) * SS, (cy + u * s + v * c) * SS) for u, v in pts]

    # Which half faces the light: the one whose outward normal points up and left.
    lit = 1 if s - c > 0 else -1
    light = tuple(min(255, int(v * 1.35)) for v in col[:3]) + (255,)
    dark = tuple(int(v * 0.62) for v in col[:3]) + (255,)
    d.polygon(half(lit), fill=light)
    d.polygon(half(-lit), fill=dark)
    d.line([((cx - L / 2 * c) * SS, (cy - L / 2 * s) * SS), ((cx + L / 2 * c) * SS, (cy + L / 2 * s) * SS)], fill=rib, width=SS)''')
rep('''    low = np.clip((yy - 0.55) / 0.4, 0, 1)
    xx = np.mgrid[0:h, 0:w][1] / w
    corner = np.clip(1 - np.minimum(xx, 1 - xx) / 0.18, 0, 1) * low
    moss = np.clip((n + 0.35 - (1 - low) * 0.9) * 2.5, 0, 1) * m * np.maximum(low * 0.6, corner)
    tone = F.hexc("#3c6a22", lin=False) * (0.6 + 0.6 * np.clip(n[..., None] + 0.5, 0, 1))
    rgb = rgb * (1 - moss[..., None] * 0.85) + tone * moss[..., None] * 0.85''', '''    low = np.clip((yy - 0.4) / 0.5, 0, 1)
    xx = np.mgrid[0:h, 0:w][1] / w
    corner = np.clip(1 - np.minimum(xx, 1 - xx) / 0.2, 0, 1) * np.maximum(low, np.clip((0.2 - yy) / 0.12, 0, 1) * 0.6)
    moss = np.clip((n + 0.4 - (1 - low) * 0.8) * 2.5, 0, 1) * m * np.maximum(low * 0.7, corner)
    nf = F.fbm(h, w, scale=6, octaves=2, seed=22)
    tone = F.hexc("#3c6a22", lin=False) * (0.55 + 0.6 * np.clip(n[..., None] + 0.5, 0, 1)) * (0.85 + 0.3 * nf[..., None])
    # The iron itself has taken the wood's green where it is wet: a verdigris in its lights.
    rgb = rgb * (1 - m[..., None] * 0.5) + np.clip(rgb * np.array([0.86, 1.08, 0.84], np.float32), 0, 1) * m[..., None] * 0.5
    rgb = rgb * (1 - moss[..., None] * 0.9) + tone * moss[..., None] * 0.9''')
rep('''            L, W = rng.uniform(20, 32), rng.uniform(10, 15)''', '''            L, W = rng.uniform(18, 34), rng.uniform(9, 16)''')
rep('''        for i in range(3, len(S) - 3, 6):''', '''        for i in range(3, len(S) - 3, 5):''')

# The paint: the house's paint-over (paintover.paint), not a free img2img: the painting gives
# the hand, the dressed guide keeps its colours and its light, and nothing moves.
rep('''SEED = {"uncommon": 670, "rare": 671}
DENOISE = (0.5, 0.58)''', '''SEED = {"uncommon": 680, "rare": 681}
DENOISE = (0.34, 0.42)''')
rep('''def paint(kinds=None, n=3):
    import krea
    jobs = []
    for k in kinds or list(GUIDES):
        g = GUIDES[k](os.path.join(RAW, "guides", f"card_{k}_dressed.png"))
        for dn in DENOISE:
            jobs.append((f"card3_{k}_{int(dn * 100)}", g, prompt(k), dn, SEED[k]))
    return krea.i2i_many(jobs, n=n, out=os.path.join(RAW, "card3"))''', '''def paint(kinds=None, n=2):
    """Every take of the dressed cards, painted over and saved on black as card3/NAME.png
    (what cards.fit cuts): the painting's detail on the guide's own colour and light."""
    import krea
    jobs, guides = [], {}
    for k in kinds or list(GUIDES):
        g = GUIDES[k](os.path.join(RAW, "guides", f"card_{k}_dressed.png"))
        guides[k] = g
        for dn in DENOISE:
            jobs.append((f"card3po_{k}_{int(dn * 100)}", g, prompt(k), dn, SEED[k]))
    res = krea.i2i_many(jobs, n=n, out=os.path.join(RAW, "card3"))
    made = []
    for tag, paths in res.items():
        k = tag.split("_")[1]
        base = np.asarray(Image.open(guides[k]).convert("RGB"), np.float32) / 255
        for p in paths:
            out = p.replace("card3po_", "card3m_")
            Image.fromarray((np.clip(merge(base, p), 0, 1) * 255 + 0.5).astype(np.uint8)).save(out)
            made.append(out)
    return made


def merge(base, painted_path, keep=0.7):
    """The painting's detail and hue over the guide's large light and colour (paintover.py's
    rule): what the dressing put there stays there, with the painting's hand."""
    painted = np.asarray(Image.open(painted_path).convert("RGB"), np.float32) / 255
    painted = cv2.resize(painted, (base.shape[1], base.shape[0]), interpolation=cv2.INTER_AREA)
    sgm = 6.0
    lb = cv2.GaussianBlur(F.srgb_to_lin(base), (0, 0), sgm)
    lp = cv2.GaussianBlur(F.srgb_to_lin(painted), (0, 0), sgm)
    lin_p = F.srgb_to_lin(painted)
    mixed = lin_p * (1 - keep) + (lin_p / np.maximum(lp, 1e-4) * lb) * keep
    return F.lin_to_srgb(np.clip(mixed, 0, 1))''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
