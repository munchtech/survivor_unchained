"""UI 18, The Drowned Girl (--hud drowned): the experience light's masks (the owner's pick (c), "no XP on screen until
it moves"), baked from the shipped art so the shader (shaders/hud_dg_xp.gdshaderinc) only reads them.

    python tools/uiforge/dg_xp_mask.py [--preview P.png]

Reads art/ui/lamp_life/drowned/lamp_cold.png (her figure, 2x) with lamp_geo.json, and art/ui/dg_river/river.png (2x)
with river_geo.json; never writes them. Writes art/ui/dg_river/xp_light.png: one 2x texture over the band the two
cover on the 1080 screen (at, size in xp_light.json), lossless:
  R  her hair: the mock's hair outline (UI 18 xp2 held.py, HAIR, cut above y 1030), softened 3 px. Only her figure's
     shader reads it: the light runs along her hair, never her face, shoulder or the hand that lifts the orb.
  G  the ridges: where the bronze stands proud (its lit relief over its own 3 px blur, plus its brightness), 0..1:
     the light catches the ridges, the hollows stay dark (dir_c.py ridges()).
  B  the light's cool cast, already softened (5 px) as held.py softens it: blur(M * (0.3 + G)), M = her hair and the
     river where her figure does not cover it.
xp_light.json also holds s0 and s1: the run's ends in the run coordinate s = x - 500 + 0.5 (clamp(y, 830, 980) - 830)
(1080 px), the 1st and 99th percentile of s over M > 0.3: her hair is 0, the eddy is full (Play/XpLight.cs).
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
UI = os.path.join(ROOT, 'godot', 'art', 'ui')
# her hair, in 1080 screen px (UI 18 xp2 dir_c.py HAIR: the judged mock's outline)
HAIR = [(505, 830), (560, 822), (640, 850), (700, 900), (760, 950), (760, 1080), (600, 1080), (570, 1030), (545, 990),
        (540, 960), (535, 900), (520, 860)]
AT = (295, 822)          # the band's top left (1080 px): her figure's quad's left, its top
SIZE = (1310, 258)       # to the river's right end (1604) and the screen's foot
K = 2                    # baked at 2x


def rgba(path):
    return np.asarray(Image.open(path).convert('RGBA')).astype(float) / 255


def place(img, x, y, W, H):
    """img (2x px) pasted at (x, y) in the band's 2x px (integer), clipped"""
    out = np.zeros((H, W, img.shape[2]))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + img.shape[1]), min(H, y + img.shape[0])
    out[y0:y1, x0:x1] = img[y0 - y:y1 - y, x0 - x:x1 - x]
    return out


def main():
    lg = json.load(open(os.path.join(UI, 'lamp_life', 'drowned', 'lamp_geo.json')))
    rg = json.load(open(os.path.join(UI, 'dg_river', 'river_geo.json')))
    W, H = SIZE[0] * K, SIZE[1] * K
    fig = rgba(os.path.join(UI, 'lamp_life', 'drowned', 'lamp_cold.png'))
    riv = rgba(os.path.join(UI, 'dg_river', 'river.png'))
    # (the river's art is drawn stretched to its geo size: its texture is that at 2x, to the pixel)
    rw, rh = int(round(rg['size'][0] * K)), int(round(rg['size'][1] * K))
    if riv.shape[1] != rw or riv.shape[0] != rh:
        riv = np.asarray(Image.fromarray((riv * 255).astype(np.uint8)).resize((rw, rh), Image.LANCZOS)).astype(float) / 255
    fw, fh = int(round(lg['canvas'][0] * K)), int(round(lg['canvas'][1] * K))
    if fig.shape[1] != fw or fig.shape[0] != fh:
        fig = np.asarray(Image.fromarray((fig * 255).astype(np.uint8)).resize((fw, fh), Image.LANCZOS)).astype(float) / 255
    F = place(fig, int(round((lg['at'][0] - AT[0]) * K)), int(round((lg['at'][1] - AT[1]) * K)), W, H)
    R = place(riv, int(round((rg['at'][0] - AT[0]) * K)), int(round((rg['at'][1] - AT[1]) * K)), W, H)
    # the bronze as the screen shows it (river under her figure) on a dark ground, for its ridges
    ground = np.array([0.06, 0.06, 0.08])
    C = ground * (1 - R[..., 3:]) + R[..., :3] * R[..., 3:]
    C = C * (1 - F[..., 3:]) + F[..., :3] * F[..., 3:]
    L = C[..., 0] * 0.3 + C[..., 1] * 0.55 + C[..., 2] * 0.15
    ridge = np.clip((L - gaussian_filter(L, 3.0 * K)) * 5.0 + (L - 0.22) * 1.4, 0, 1)
    # her hair's outline
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).polygon([((x - AT[0]) * K, (y - AT[1]) * K) for x, y in HAIR], fill=255)
    hp = np.asarray(im).astype(float) / 255
    Y, X = np.mgrid[0:H, 0:W]
    sy = AT[1] + (Y + 0.5) / K
    sx = AT[0] + (X + 0.5) / K
    hp = gaussian_filter(hp * (sy < 1030), 3.0 * K)
    Mh = F[..., 3] * hp
    Mr = R[..., 3] * (1 - F[..., 3])
    M = np.maximum(Mh, Mr)
    cast = np.clip(gaussian_filter(M * (0.3 + ridge), 5.0 * K), 0, 1)
    s = sx - 500 + 0.5 * (np.clip(sy, 830, 980) - 830)
    sm = s[M > 0.3]
    s0, s1 = float(np.percentile(sm, 1)), float(np.percentile(sm, 99))
    out = np.stack([hp, ridge, cast], -1)
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(UI, 'dg_river', 'xp_light.png'))
    meta = {'at': list(AT), 'size': list(SIZE), 's0': round(s0, 2), 's1': round(s1, 2),
            'note': 'tools/uiforge/dg_xp_mask.py: R her hair, G the ridges, B the cool cast (blurred); s0..s1 the run (s = x - 500 + 0.5 (clamp(y, 830, 980) - 830))'}
    json.dump(meta, open(os.path.join(UI, 'dg_river', 'xp_light.json'), 'w'), indent=1)
    print('xp_light', W, 'x', H, 's0', round(s0, 2), 's1', round(s1, 2))
    if '--preview' in sys.argv:
        Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGB').resize((W // 2, H // 2)).save(sys.argv[sys.argv.index('--preview') + 1])


if __name__ == '__main__':
    main()
