"""Our own block-ins (value and color thumbnails at full size) for the plates the
model can't compose from words (style judge r1: P1 a canyon in a mesa with movie
Romans and a runway of lights; P9 a camo jacket, headlights and a streetlight).
Each block-in places every shape where the script and the judge want it; the
painting pass (gen.py: init = unify.py prep of the block-in, control = its soft
edges, the shared hand prompt) paints over it. Coordinates are pixels of the
1792x1024 plate; the 2.39 window shows about y 130-880.

    python tools/storybook/blockin.py p1|p9 [--out tools/storybook/layouts]
"""
import argparse
import os

import cv2
import numpy as np

W, H = 1792, 1024


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


class Canvas:
    def __init__(self, color="#000000"):
        self.img = np.ones((H, W, 3), np.float32) * rgb(color)

    def mask_poly(self, pts, soft=1.5):
        m = np.zeros((H, W), np.float32)
        cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
        return cv2.GaussianBlur(m, (0, 0), soft) if soft else m

    def fill(self, m, color, a=1.0):
        c = rgb(color) if isinstance(color, str) else color
        self.img = self.img * (1 - m[..., None] * a) + c * (m[..., None] * a)

    def poly(self, pts, color, soft=1.5, a=1.0):
        self.fill(self.mask_poly(pts, soft), color, a)

    def vgrad(self, m, y0, c0, y1, c1):
        t = np.clip((np.arange(H, dtype=np.float32) - y0) / (y1 - y0), 0, 1)[:, None, None]
        g = rgb(c0) * (1 - t) + rgb(c1) * t
        self.img = self.img * (1 - m[..., None]) + g * m[..., None]

    def glow(self, x, y, r, color, a=1.0, ry=None):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = ((xx - x) / r) ** 2 + ((yy - y) / (ry or r)) ** 2
        g = np.exp(-d * 2.2) * a
        self.img = self.img + rgb(color) * g[..., None]

    def line(self, pts, color, w, a=1.0, soft=0.8):
        m = np.zeros((H, W), np.float32)
        cv2.polylines(m, [np.array(pts, np.int32)], False, 1.0, int(w), lineType=cv2.LINE_AA)
        self.fill(cv2.GaussianBlur(m, (0, 0), soft) if soft else m, color, a)

    def ellipse(self, cx, cy, rx, ry, color, ang=0, soft=1.2, a=1.0):
        m = np.zeros((H, W), np.float32)
        cv2.ellipse(m, (int(cx), int(cy)), (int(rx), int(ry)), ang, 0, 360, 1.0, -1, cv2.LINE_AA)
        self.fill(cv2.GaussianBlur(m, (0, 0), soft), color, a)

    def texture(self, amt=0.05, seed=3):
        """Loose paint: low-frequency value drift and long diagonal stroke marks,
        so the painting pass has marks to paint from, not flat fills."""
        rng = np.random.default_rng(seed)
        n = np.zeros((H, W), np.float32)
        for s, a in ((90, 0.5), (30, 0.3), (9, 0.2)):
            r = cv2.resize(rng.random((H // s + 2, W // s + 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
            n += a * (r - 0.5)
        k = np.zeros((25, 25), np.float32)
        cv2.line(k, (1, 17), (23, 7), 1.0, 1)
        st = cv2.filter2D(rng.random((H, W)).astype(np.float32) - 0.5, -1, k / k.sum())
        n = n + 2.5 * st
        self.img = np.clip(self.img * (1 + amt * n[..., None] * 2), 0, 1)


def curve(pts, n):
    """n points spaced evenly along a polyline."""
    p = np.array(pts, np.float32)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = np.linspace(0, seg[-1], n)
    return np.stack([np.interp(t, seg, p[:, 0]), np.interp(t, seg, p[:, 1])], 1)


def p9():
    c = Canvas("#16161a")
    sky = c.mask_poly([(0, 0), (W, 0), (W, 440), (0, 440)], 0)
    c.vgrad(sky, 0, "#0a0f26", 395, "#22305a")
    band = np.zeros((H, W), np.float32)
    band[390:414, :] = 1
    band = cv2.GaussianBlur(band, (0, 0), 5) * np.clip(1.3 - np.arange(W, dtype=np.float32) / W * 1.2, 0, 1)[None, :]
    c.fill(band, "#5c3c47", 0.85)
    hills = [(0, 432), (180, 418), (360, 426), (520, 412), (700, 424), (900, 415), (1150, 422), (1400, 410), (1600, 420), (W, 414),
             (W, 560), (0, 560)]
    c.poly(hills, "#10131c", 1.0)
    ground = [(0, 470), (W, 470), (W, H), (0, H)]
    c.vgrad(c.mask_poly(ground, 0), 470, "#14151a", 1024, "#121114")
    # The road: a narrow rutted dirt track from the near left to the Waystation on the horizon,
    # uneven edges, grass down the middle, ruts as broken grooves (r1 read as a paved road).
    rng = np.random.default_rng(4)
    ys = np.linspace(H, 432, 30)
    cx = np.interp(ys, [432, 560, 760, H], [566, 548, 470, 330])
    half = np.interp(ys, [432, H], [9, 165])
    jl = rng.normal(0, 1, len(ys)) * half * 0.06
    jr = rng.normal(0, 1, len(ys)) * half * 0.06
    left = [(cx[i] - half[i] + jl[i], ys[i]) for i in range(len(ys))]
    right = [(cx[i] + half[i] + jr[i], ys[i]) for i in range(len(ys))][::-1]
    c.poly(left + right, "#2b2724", 2.5)
    for off in (-0.48, 0.48):
        pts = [(cx[i] + off * half[i], ys[i]) for i in range(len(ys))]
        for i in range(len(pts) - 1):
            if rng.random() < 0.25:
                continue
            wdt = 1 + 9 * (pts[i][1] - 432) / (H - 432)
            c.line([pts[i], pts[i + 1]], "#191615", max(1, wdt * rng.uniform(0.6, 1.2)), 0.85, 1.0)
    for i in range(0, len(ys) - 1, 2):
        c.line([(cx[i] + rng.normal(0, 3), ys[i]), (cx[i + 1], ys[i + 1])], "#22231d", max(1, 6 * (ys[i] - 432) / (H - 432)), 0.6, 1.5)
    for _ in range(40):
        x = rng.uniform(0, 420); y = rng.uniform(560, 1000)
        c.line([(x, y), (x + rng.uniform(-10, 10), y - rng.uniform(10, 40))], "#0f1013", rng.uniform(2, 5), 0.8, 1.0)
    # The Waystation: a few roofs, warm lamps, one higher.
    for x, y, w, h in ((532, 410, 26, 22), (556, 404, 30, 28), (588, 409, 24, 23), (610, 413, 20, 19)):
        c.poly([(x, y + h), (x, y + 6), (x + w // 2, y), (x + w, y + 6), (x + w, y + h)], "#0d0f15", 0.6)
    c.line([(576, 432), (576, 393)], "#0d0f15", 3, 1.0, 0.5)
    for x, y, r in ((542, 422, 5), (564, 418, 5), (592, 423, 4), (614, 421, 4), (576, 390, 6)):
        c.glow(x, y, r * 3.0, "#ff9a40", 0.55)
        c.ellipse(x, y, max(1, r // 2), max(1, r // 2), "#ffe0a0", soft=0.6)
    # Trees and the river on the right; three blue points low by the water, uneven.
    c.poly([(1120, 476), (W, 470), (W, 506), (1120, 500)], "#2a3956", 2.0)
    rng = np.random.default_rng(9)
    for x in sorted(rng.uniform(1135, 1785, 26)):
        top = rng.uniform(300, 380)
        c.line([(x, 545), (x + rng.uniform(-8, 8), top)], "#0a0d14", rng.uniform(3, 9), 1.0, 0.8)
        for _ in range(5):
            y = rng.uniform(top, 470)
            c.line([(x, y), (x + rng.uniform(-60, 60), y - rng.uniform(15, 60))], "#0a0d14", rng.uniform(1, 3), 0.9, 0.7)
    c.poly([(1110, 515), (W, 505), (W, 600), (1110, 600)], "#101219", 3.0)
    for x, y in ((1262, 489), (1409, 496), (1567, 484)):
        c.glow(x, y, 26, "#5aa0e0", 0.55)
        c.ellipse(x, y, 3, 3, "#d8eeff", soft=0.7)
    # The fire, high, and its warm ring on the ground.
    c.glow(790, 668, 430, "#4a2a12", 0.9, ry=150)
    c.glow(790, 600, 180, "#ff8a3a", 0.25)
    for a, b in (((725, 670), (850, 640)), ((735, 640), (860, 672)), ((760, 676), (820, 630))):
        c.line([a, b], "#21160f", 12, 1.0, 1.0)
    c.poly([(735, 658), (752, 600), (772, 560), (790, 505), (803, 548), (826, 590), (846, 628), (842, 662)], "#ff8a3a", 4.0)
    c.poly([(758, 658), (772, 612), (790, 565), (808, 610), (824, 660)], "#ffc060", 3.0)
    c.poly([(772, 660), (790, 618), (806, 660)], "#fff0c0", 2.0)
    c.line(curve([(800, 505), (815, 420), (845, 330), (880, 240)], 30), "#2f3442", 26, 0.45, 9)
    # The bedroll with its blanket folded on it, between the road and the fire.
    c.poly([(612, 803), (612, 760), (760, 752), (772, 796)], "#3a3029", 2.0)
    c.ellipse(612, 781, 12, 22, "#2a221d")
    c.poly([(626, 762), (632, 738), (730, 733), (738, 757)], "#4a3e33", 2.0)
    c.line([(632, 748), (732, 744)], "#5c3a2c", 4, 0.6, 1.0)
    # The traveler: back to us, one plain dark wool cloak, hood to ground, a cone; firelit on the left.
    cone = [(1046, 448), (1070, 456), (1086, 476), (1090, 504), (1084, 528), (1112, 548), (1140, 586), (1160, 660), (1186, 740),
            (1214, 808), (930, 808), (946, 740), (962, 664), (978, 600), (996, 560), (1012, 534), (1006, 506), (1016, 474)]
    c.poly(cone, "#1a191e", 1.5)
    for x0, x1 in ((1060, 1060), (1110, 1150)):
        c.line([(x0, 620), (x1, 800)], "#121116", 6, 0.6, 3.0)
    c.line([(1016, 476), (1006, 506), (1012, 534), (996, 560), (978, 602), (962, 664), (946, 740), (933, 805)], "#8a5532", 7, 0.85, 2.0)
    c.line([(1046, 450), (1018, 474)], "#6a4128", 5, 0.8, 1.5)
    c.poly([(940, 598), (978, 592), (984, 628), (944, 634)], "#d6c39c", 1.0)
    c.line([(962, 630), (957, 650)], "#2a2420", 2, 1.0, 0.5)
    c.ellipse(955, 662, 8, 12, "#2e2620")
    c.line([(949, 655), (950, 670)], "#8a6240", 2, 0.8, 0.5)
    c.poly([(905, 830), (905, 800), (1262, 796), (1268, 826)], "#2a2018", 2.0)
    c.line([(905, 800), (1150, 797)], "#6a4428", 4, 0.7, 1.5)
    # The pack, by the traveler.
    c.poly([(1238, 805), (1236, 735), (1252, 716), (1300, 714), (1318, 734), (1322, 805)], "#26211d", 2.0)
    c.line([(1238, 800), (1237, 736), (1252, 718)], "#6a4428", 4, 0.6, 1.5)
    c.texture(0.05)
    figs = c.mask_poly(cone, 2.0)
    return c.img, figs


def p1():
    """We stand on the near rim; the column's S of torches zigzags down the far wall,
    which faces us; the hillside rises behind it to a crest under a strip of sky."""
    c = Canvas("#14100c")
    c.vgrad(c.mask_poly([(0, 0), (W, 0), (W, 300), (0, 300)], 0), 0, "#0a0d1a", 240, "#1d2238")
    crest = curve([(0, 236), (300, 222), (650, 228), (1000, 204), (1350, 196), (W, 176)], 40).astype(int).tolist()
    c.poly(crest + [(W, 300), (1200, 296), (700, 312), (300, 322), (0, 330)], "#191510", 2.5)
    # The far wall: three big planes and the depths, one contour each.
    c.poly([(300, 322), (700, 312), (1000, 305), (930, 560), (620, 640), (420, 520)], "#2e241c", 2.0)
    c.poly([(1000, 305), (1200, 296), (W, 300), (W, 760), (1320, 820), (930, 560)], "#1c1b20", 2.0)
    c.poly([(420, 520), (620, 640), (930, 560), (1320, 820), (1180, H), (560, H), (470, 800)], "#251e18", 2.0)
    c.vgrad(c.mask_poly([(440, 760), (1400, 760), (1400, H), (440, H)], 60), 760, "#251e18", 1000, "#090706")
    for line in ([(300, 322), (700, 312), (1000, 305), (1200, 296), (W, 300)], [(1000, 305), (930, 560), (1320, 820)],
                 [(420, 520), (620, 640), (930, 560)]):
        c.line(line, "#0c0a08", 5, 0.85, 1.5)
    # The column: an S of torches down the far wall to the bottom edge, the brightest shapes.
    path = curve([(470, 335), (700, 362), (930, 392), (1090, 440), (1060, 500), (860, 560), (680, 620), (640, 680), (760, 745),
                  (930, 800), (1010, 860), (980, 930), (960, 1015)], 26)
    c.line(path.astype(int).tolist(), "#3e2a1c", 18, 0.55, 7)
    for i, (x, y) in enumerate(path):
        r = 5.5 - 2.8 * i / (len(path) - 1)
        c.glow(x, y - r, r * 7, "#ff8a3a", 0.35)
        c.line([(x, y + r * 0.6), (x, y + r * 4.0)], "#0e0a08", max(2, r * 0.9), 1.0, 0.6)
        c.ellipse(x, y - r * 0.4, r * 0.8, r * 1.4, "#ffd07a", soft=0.8)
        c.ellipse(x, y - r * 0.2, r * 0.4, r * 0.7, "#fff0c8", soft=0.6)
    for i in range(0, len(path), 3):
        x, y = path[i]
        c.line(curve([(x, y - 10), (x + 30, y - 70), (x + 80, y - 140)], 12).astype(int).tolist(), "#3a332e", 10, 0.16, 6)
    # Our rim, bottom left, and two legionaries on it, backs to us: dark near shapes,
    # rust-red wool and dull bronze; one small torch held low in front of the nearer.
    c.poly([(0, 420), (260, 450), (430, 640), (560, H), (0, H)], "#100c09", 2.5)
    c.line([(0, 420), (260, 450), (430, 640), (560, H)], "#3a2618", 4, 0.6, 2.0)
    c.glow(470, 420, 120, "#ff8a3a", 0.3)
    for (cx, top, w, col) in ((170, 250, 200, "#2a140e"), (360, 285, 180, "#32180f")):
        h0 = top + 62
        c.poly([(cx - w * 0.30, h0 + 30), (cx - w * 0.5, h0 + 140), (cx - w * 0.55, H), (cx + w * 0.55, H), (cx + w * 0.5, h0 + 140),
                (cx + w * 0.30, h0 + 30), (cx + w * 0.12, h0)], col, 1.5)
        c.poly([(cx - w * 0.30, h0 + 30), (cx - w * 0.12, h0), (cx + w * 0.12, h0), (cx + w * 0.30, h0 + 30), (cx, h0 + 80)],
               "#1e100b", 1.5)
        c.ellipse(cx, top + 32, w * 0.16, w * 0.19, "#33291b")
        c.line([(cx - w * 0.15, top + 12), (cx, top - 6), (cx + w * 0.15, top + 12)], "#40241a", 9, 1.0, 1.2)
        c.line([(cx - w * 0.16, top + 30), (cx - w * 0.17, top + 62)], "#241c12", 6, 1.0, 1.0)
    c.line([(cx + w * 0.30, h0 + 32), (cx + w * 0.5, h0 + 140), (cx + w * 0.53, 760)], "#7a4024", 5, 0.7, 2.0)
    c.line([(452, 400), (462, 470)], "#21170f", 6, 1.0, 0.8)
    c.poly([(444, 402), (454, 372), (458, 352), (466, 374), (474, 400)], "#ff8a3a", 2.0)
    c.poly([(450, 400), (458, 376), (467, 400)], "#ffd890", 1.5)
    c.texture(0.05)
    figs = c.mask_poly([(40, 240), (470, 270), (500, H), (20, H)], 2.0)
    return c.img, figs


def p7():
    """A paint-over of r1's P7 (the closest frame; judge r1's fixes): the fourth
    light off its cord, low over the water in a wide glare above a ford of stones;
    black iron posts, no orange; a plain flame in the near cage; ice at both edges;
    the edges and the far bank two values down; blue pools round each post."""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "style_r10", "src", "p7.png")
    u8 = cv2.imread(src, cv2.IMREAD_COLOR)
    # The hanging lantern and its cord, and the copper ring under the near cage: filled from around.
    m = np.zeros((H, W), np.uint8)
    cv2.rectangle(m, (905, 560), (1000, 680), 255, -1)
    cv2.line(m, (952, 380), (952, 600), 255, 14)
    cv2.rectangle(m, (628, 728), (752, 768), 255, -1)
    cv2.rectangle(m, (655, 455), (725, 584), 255, -1)
    u8 = cv2.inpaint(u8, m, 9, cv2.INPAINT_TELEA)
    c = Canvas()
    c.img = cv2.cvtColor(u8, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    img = c.img
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    river = c.mask_poly([(470, 400), (640, 388), (1000, 468), (1400, 590), (W, 650), (W, H), (1180, H), (700, 770), (510, 600)], 0)
    snow = (lum > 0.42).astype(np.float32)
    water = river * (lum < 0.2)
    near_snow = cv2.dilate(snow, np.ones((15, 15), np.uint8))
    ice = cv2.GaussianBlur(water * near_snow, (0, 0), 3.0)
    c.fill(ice, "#56616f", 0.6)
    # The far bank and the frame's edges two values down.
    far = c.mask_poly([(560, 0), (W, 0), (W, 640), (1400, 585), (1000, 462), (640, 385)], 30)
    c.img = c.img * (1 - 0.42 * far[..., None] * (lum > 0.3)[..., None])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - 900) / 1000) ** 2 + ((yy - 640) / 620) ** 2)
    c.img = c.img * np.clip(1.25 - 0.55 * d, 0.45, 1)[..., None]
    # Black iron posts; blue pools on the snow round each foot.
    for x, y0, y1, w in ((240, 528, 600, 8), (365, 592, 722, 12), (690, 752, 968, 22)):
        c.poly([(x - w / 2, y0), (x + w / 2, y0), (x + w / 2 + 1, y1), (x - w / 2 - 1, y1)], "#0d0e12", 1.0)
        c.line([(x - w / 2 + 2, y0 + 4), (x - w / 2 + 2, y1 - 4)], "#4a6a8a", 2, 0.5, 0.8)
        c.glow(x, y1 - 4, w * 7, "#3a6a9a", 0.45, ry=w * 2.2)
    c.poly([(640, 752), (740, 752), (728, 738), (652, 738)], "#0d0e12", 1.0)
    # A plain flame in the near cage.
    c.poly([(672, 722), (678, 690), (688, 650), (693, 618), (700, 652), (708, 690), (712, 722)], "#8ac8ff", 3.0, 0.9)
    c.poly([(682, 720), (690, 680), (694, 650), (700, 682), (704, 720)], "#e6f4ff", 2.0, 0.9)
    # The ford: a trodden track down the near bank, flat stones across, the track up the far bank.
    c.line(curve([(560, H), (640, 960), (730, 900), (792, 850)], 20).astype(int).tolist(), "#5a6370", 60, 0.45, 12)
    for i, (x, y) in enumerate(curve([(800, 842), (870, 776), (940, 718), (1010, 662), (1080, 604), (1150, 548)], 9)):
        r = 32 - 2.2 * i
        c.ellipse(x, y + r * 0.15, r, r * 0.42, "#1b1e23", soft=1.5)
        c.ellipse(x - r * 0.1, y - r * 0.1, r * 0.6, r * 0.18, "#5d6774", soft=1.5)
    c.line(curve([(1160, 540), (1210, 488), (1260, 430)], 10).astype(int).tolist(), "#4a525e", 34, 0.4, 8)
    # The fourth light: just above the water, a wide cold glare; its streak in the water under it.
    c.glow(980, 640, 170, "#3a78b8", 0.55)
    c.glow(980, 640, 60, "#8ac8ff", 0.8)
    c.glow(980, 640, 16, "#e8f6ff", 1.0)
    c.line([(980, 690), (980, 860)], "#8ac8ff", 10, 0.35, 5)
    c.img = np.clip(c.img, 0, 1)
    return c.img, np.zeros((H, W), np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plate", choices=["p1", "p7", "p9"])
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "layouts"))
    a = ap.parse_args()
    img, figs = {"p1": p1, "p7": p7, "p9": p9}[a.plate]()
    os.makedirs(a.out, exist_ok=True)
    f = os.path.join(a.out, a.plate + "_block.png")
    cv2.imwrite(f, cv2.cvtColor((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))
    cv2.imwrite(os.path.join(a.out, a.plate + "_figs.png"), (np.clip(figs, 0, 1) * 255).astype(np.uint8))
    print(f)


if __name__ == "__main__":
    main()
