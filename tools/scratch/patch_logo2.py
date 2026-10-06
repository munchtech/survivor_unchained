p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\logo.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep('''SURVIVOR over UNCHAINED in the
game's own capitals (Cinzel), cut from forged iron, planished, the edges worn bright; between''',
    '''SURVIVOR over UNCHAINED in the
game's own capitals (Cinzel, at its heaviest), cut from forged steel with a deep chamfer that
takes the light, lightly planished, the edges worn bright; between''')
rep('''FONT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "fonts", "cinzel-600.ttf")''',
    '''# Cinzel's variable font (OFL, google/fonts) at weight 900: the game's display face, with a
# title's weight (at 600 and wide-set it read like a book's cover, not a game's name).
FONT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "fonts", "Cinzel-wght.ttf")
WEIGHT = 900''')
rep('''LINES = (
    ("SURVIVOR", 112, 4, 152, {0: 1.18}),
    ("UNCHAINED", 86, 8, 392, {0: 1.18}),
)
CHAIN_Y = 228             # the chain's middle''', '''LINES = (
    ("SURVIVOR", 124, -3, 156, {0: 1.16}),
    ("UNCHAINED", 98, 0, 388, {0: 1.16}),
)
CHAIN_Y = 230             # the chain's middle''')
rep('''        f0 = ImageFont.truetype(FONT, 100)
        hcap = f0.getbbox("H")[3] - f0.getbbox("H")[1]
        sizes = [cap * big.get(i, 1.0) / hcap * 100 for i in range(len(text))]
        fonts = [ImageFont.truetype(FONT, int(round(s * ss))) for s in sizes]''', '''        f0 = font(100)
        hcap = f0.getbbox("H")[3] - f0.getbbox("H")[1]
        sizes = [cap * big.get(i, 1.0) / hcap * 100 for i in range(len(text))]
        fonts = [font(int(round(s * ss))) for s in sizes]''')
rep('''def text_mask(ss):''', '''def font(size):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([WEIGHT])
    return f


def text_mask(ss):''')
rep('''    top, ch = 11.0, 4.2
    t = np.clip(sd / ch, 0, 1)
    letters = (t * top) * (sd > 0)
    shape = letters.copy()
    facet = F.facets(R.h, R.w, cell=16.0 * ss, tilt=0.03, seed=41, soften=1.5 * ss) / ss
    dents = RL.hammered(R, cell=5.0, depth=0.22, seed=42) / ss
    face = np.clip((sd - ch) / 1.5, 0, 1)
    letters = letters + (facet + dents) * face
    # A blade's fuller down the heavy strokes: a shallow groove where the letter is widest.
    fuller = np.exp(-((sd - sd.max() * 0.0 - 9.5) / 1.2) ** 2) * (sd > 8)
    letters = letters - fuller * 0.6
    h = letters
    mat = np.full(X.shape, RL.IDS["iron"], np.int32)''', '''    # A deep chamfer (45 degrees, 6 px) to a face crowned a little: the chamfer takes the
    # light as a bright edge, the face holds the planishing.
    top, ch = 9.0, 6.0
    t = np.clip(sd / ch, 0, 1)
    crown = np.clip((sd - ch) / 10.0, 0, 1) * 1.6
    letters = (t * top + crown) * (sd > 0)
    shape = letters.copy()
    facet = F.facets(R.h, R.w, cell=22.0 * ss, tilt=0.012, seed=41, soften=2.0 * ss) / ss
    dents = RL.hammered(R, cell=6.0, depth=0.12, seed=42) / ss
    face = np.clip((sd - ch) / 1.5, 0, 1)
    letters = letters + (facet + dents) * face
    h = letters
    mat = np.full(X.shape, RL.IDS["steel"], np.int32)''')
rep('''    core = np.clip(brk * 1.6, 0, 1)
    R.emit = (core[..., None] * (hot * 2.4 + deep) * (0.7 + 0.5 * n[..., None])).astype(np.float32)''', '''    core = np.clip(brk * 1.8, 0, 1)
    R.emit = (core[..., None] * (hot * 3.2 + deep * 1.4) * (0.75 + 0.5 * n[..., None])).astype(np.float32)
    R.alpha = np.maximum(R.alpha, core)''')
rep('''    R.tint = (1 + near[..., None] * (F.hexc("#ff9a50") / F.hexc("#ff9a50").max() - 0.5) * 0.9).astype(np.float32)''',
    '''    R.tint = (1 + near[..., None] * (F.hexc("#ffb070") / F.hexc("#ffb070").max() - 0.6) * 0.45).astype(np.float32)''')
rep('''            brk = np.exp(-((X - lx) ** 2 / (2 * 8.0 ** 2) + (Y - (CHAIN_Y - (LINK_W + 10) / 2)) ** 2 / (2 * 6.5 ** 2)))''',
    '''            brk = np.exp(-((X - lx) ** 2 / (2 * 11.0 ** 2) + (Y - (CHAIN_Y - (LINK_W + 10) / 2)) ** 2 / (2 * 8.0 ** 2)))''')
rep('''    return F.downsample(p, (W, H))


def main():''', '''    return glow(F.downsample(p, (W, H)))


def glow(img):
    """The break's light thrown on the air round it: a warm glow laid under and beside the
    iron, falling off softly (it needs no surface; its alpha is its light)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    by = CHAIN_Y - (LINK_W + 10) / 2
    g = (np.exp(-((xx - CX) ** 2 / (2 * 46.0 ** 2) + (yy - by) ** 2 / (2 * 34.0 ** 2))) * 0.85
         + np.exp(-((xx - CX) ** 2 / (2 * 150.0 ** 2) + (yy - by) ** 2 / (2 * 80.0 ** 2))) * 0.35)
    col = np.array([1.0, 0.52, 0.16], np.float32)
    a = img[..., 3]
    ga = np.clip(g, 0, 1) * (1 - a)
    out_a = a + ga
    rgb = (img[..., :3] * a[..., None] + col * ga[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([rgb, out_a]).astype(np.float32)


def main():''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
