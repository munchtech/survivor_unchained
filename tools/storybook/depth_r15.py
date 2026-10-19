"""Round 15's layouts, as depth only (judge r2: edges carry the old picture's hand,
so no plate takes edges from a picture any more). Near is white, far and sky black,
as MoGe-2 renders it (tools/storybook/depth.py).

  p1  built here: our own block-out of the cut (MoGe reads the flat r13 block-in as
      a flat picture). The hillside rises to a crest; dug into it, a great raw cut
      whose far wall faces us as four big rock planes, one crease between each;
      an S of ledge down the wall with the column packed on it (heads, irregular);
      our rim at the lower left, the two legionaries on it, a small torch half
      hidden by the nearer.
  p4  MoGe of r14's P4 (the master), edited: the second shaft behind the shield
      gone, the spearhead's run over the chest gone (it is buried), the breath's
      wisps gone, the lower-left junk flattened to frost; then pulled back 15%
      (scaled 0.85 about the horizon's middle).
  p7  MoGe of the r13 block-in (r1's frame painted over), edited: the domed
      lanterns on bollards replaced by square cages on plain square posts; the
      ford's flat stones raised across the shallows; the twigs at lower left gone.
  p9  MoGe of the r13 block-in, edited: the cross-shaped tower replaced by a long
      low hall with a squat square tower beside it; the cloak's cone run down over
      the log to the ground.

    python tools/storybook/depth_r15.py [--src tools/storybook/out/style_r15/depth] [--out tools/storybook/out/style_r15/layouts]
"""
import argparse
import os

import cv2
import numpy as np

H, W = 1024, 1792


def load(f):
    return cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255


def save(f, d):
    u = (np.clip(d, 0, 1) * 255 + 0.5).astype(np.uint8)
    cv2.imwrite(f, cv2.merge([u, u, u]))


def poly_mask(pts, soft=0.0):
    m = np.zeros((H, W), np.float32)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), soft) if soft else m


def inpaint(d, m, r=12):
    u = (np.clip(d, 0, 1) * 65535).astype(np.uint16)
    u8 = (np.clip(d, 0, 1) * 255).astype(np.uint8)
    out = cv2.inpaint(u8, (m > 0.5).astype(np.uint8) * 255, r, cv2.INPAINT_TELEA).astype(np.float32) / 255
    return np.where(m > 0.5, out, u.astype(np.float32) / 65535)


def rowfill(d, m):
    """The masked runs of each row filled by a straight line between their two ends
    (a ground plane's depth changes down the frame, not across it)."""
    d = d.copy()
    mb = m > 0.5
    for y in np.where(mb.any(1))[0]:
        row, mr = d[y], mb[y]
        xs = np.where(~mr)[0]
        if len(xs) == 0:
            continue
        row[mr] = np.interp(np.where(mr)[0], xs, row[xs])
    return d


def plane(p0, p1, p2):
    """depth = a + b x + c y through three (x, y, depth) points."""
    A = np.array([[1, p[0], p[1]] for p in (p0, p1, p2)], np.float64)
    z = np.array([p[2] for p in (p0, p1, p2)], np.float64)
    a, b, c = np.linalg.solve(A, z)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return (a + b * xx + c * yy).astype(np.float32)


def curve(pts, n):
    p = np.array(pts, np.float32)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = np.linspace(0, seg[-1], n)
    return np.stack([np.interp(t, seg, p[:, 0]), np.interp(t, seg, p[:, 1])], 1)


def p1(src):
    d = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xs = np.arange(W, dtype=np.float32)
    crest = np.interp(xs, [0, 300, 650, 1000, 1350, W], [236, 222, 228, 204, 196, 176])
    rim = np.interp(xs, [0, 300, 700, 1000, 1200, W], [330, 322, 312, 305, 296, 300])
    # The hillside above the cut, rising away from us to the crest.
    t = np.clip((yy - crest[None]) / (rim - crest)[None], 0, 1)
    hill = (yy >= crest[None])
    d = np.where(hill, 0.07 + 0.10 * t, d)
    # The far wall: three big planes of rock facing us, a crease between each.
    A = [(300, 322), (700, 312), (1000, 305), (930, 560), (620, 640), (420, 520)]
    B = [(1000, 305), (1200, 296), (W, 300), (W, 790), (1320, 840), (930, 560)]
    C = [(420, 520), (620, 640), (930, 560), (1320, 840), (1240, H), (560, H), (470, 800)]
    D = [(1320, 840), (W, 790), (W, H), (1240, H)]
    for pts, pl in ((A, plane((300, 322, 0.19), (1000, 305, 0.185), (620, 640, 0.27))),
                    (B, plane((1000, 305, 0.185), (W, 300, 0.15), (1320, 840, 0.30))),
                    (C, plane((620, 640, 0.30), (930, 560, 0.285), (900, H, 0.44))),
                    (D, plane((1320, 840, 0.335), (W, 790, 0.31), (1500, H, 0.40)))):
        m = poly_mask(pts, 0.8)
        d = d * (1 - m) + pl * m
    # The ledge: an S cut into the wall, from just below the far rim to the bottom edge,
    # a little nearer than the rock under it; the column packed on it, heads uneven.
    path = curve([(640, 360), (760, 392), (900, 434), (1010, 486), (1000, 545), (880, 590), (740, 640), (690, 700),
                  (760, 760), (900, 815), (990, 870), (980, 940), (950, 1030)], 400)
    ledge = np.zeros((H, W), np.float32)
    for i in range(len(path) - 1):
        k = i / (len(path) - 1)
        cv2.line(ledge, tuple(int(v) for v in path[i]), tuple(int(v) for v in path[i + 1]), 1.0, int(14 + 26 * k), cv2.LINE_AA)
    ledge = cv2.GaussianBlur(ledge, (0, 0), 1.0)
    d = d + 0.025 * ledge
    rng = np.random.default_rng(15)
    crowd = np.zeros((H, W), np.float32)
    s = 0.0
    while s < len(path) - 1:
        k = s / (len(path) - 1)
        x, y = path[int(s)]
        hgt = 10 + 34 * k
        wid = hgt * rng.uniform(0.28, 0.4)
        x += rng.normal(0, 3 + 8 * k)
        cv2.ellipse(crowd, (int(x), int(y - hgt * 0.5)), (max(2, int(wid / 2)), max(3, int(hgt / 2))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        s += rng.uniform(0.35, 1.0) * (2.5 + 5 * k) * (1 if rng.random() > 0.12 else 3.0)
    d = d + 0.04 * cv2.GaussianBlur(crowd, (0, 0), 0.8)
    # Our rim, the lower left: near, dropping away at its edge into the cut.
    rimpts = [(0, 420), (260, 450), (430, 640), (560, H), (0, H)]
    m = poly_mask(rimpts, 1.0)
    d = d * (1 - m) + plane((0, 420, 0.72), (260, 450, 0.74), (300, H, 1.0)) * m
    # The two legionaries, from MoGe's reading of the r13 block-in (their outlines are ours).
    b = load(os.path.join(src, "b13p1_depth.png"))
    figs = ((b > 0.55) & (xx < 600)).astype(np.float32)
    figs = cv2.morphologyEx(figs, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    figs = cv2.GaussianBlur(figs, (0, 0), 0.8)
    d = d * (1 - figs) + np.maximum(b, 0.86) * figs
    # The near torch, half the r13 size, held low in front of the nearer, half hidden by him.
    tm = np.zeros((H, W), np.float32)
    cv2.line(tm, (446, 468), (440, 418), 1.0, 5, cv2.LINE_AA)
    cv2.ellipse(tm, (440, 406), (7, 13), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    d = np.maximum(d, 0.9 * tm)
    return np.clip(d, 0, 1)


def p4(src):
    d = load(os.path.join(src, "r14p4_depth.png"))
    m = np.zeros((H, W), np.float32)
    cv2.line(m, (1148, 620), (1308, 830), 1.0, 22)       # the second shaft (the X behind the shield)
    cv2.line(m, (716, 428), (808, 474), 1.0, 22)         # the spearhead's run over the chest: buried
    box = np.zeros((H, W), np.float32)
    box[320:420, 880:1215] = 1                            # the breath's wisps: thin bright shapes there
    th = d - cv2.morphologyEx(d, cv2.MORPH_OPEN, np.ones((17, 17), np.uint8))
    m = np.maximum(m, cv2.dilate(((th > 0.12) * box).astype(np.float32), np.ones((7, 7), np.uint8)))
    d = inpaint(d, m, 9)
    corner = np.zeros((H, W), np.float32)
    corner[600:, :] = (d[600:, :] < 0.05)                 # MoGe's empty corner at the lower right
    d = rowfill(d, corner)
    # The lower left flattened to frost: each row's ground depth there.
    ground = np.percentile(d[:, 1350:1792], 35, axis=1)
    ground = cv2.GaussianBlur(ground.reshape(-1, 1), (0, 0), 6).ravel()
    lm = poly_mask([(0, 790), (330, 790), (380, H), (0, H)], 12)
    d = d * (1 - lm) + ground[:, None] * lm
    # Pulled back 15%: scaled about the horizon's middle (borders run on).
    Mx = cv2.getRotationMatrix2D((896, 470), 0, 0.85)
    valid = cv2.warpAffine(np.ones((H, W), np.float32), Mx, (W, H), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    valid = cv2.erode(valid, np.ones((5, 5), np.uint8))
    d = cv2.warpAffine(d, Mx, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    d = np.where(valid > 0.5, d, np.nan)
    rows = np.nanpercentile(np.where(np.isnan(d), np.nan, d), 35, axis=1)
    ok = ~np.isnan(rows)
    yv = np.arange(H)
    fit = np.polyfit(yv[ok][-80:], rows[ok][-80:], 1)
    for y in yv:
        r = d[y]
        bad = np.isnan(r)
        if not bad.any():
            continue
        if bad.all():
            d[y] = np.polyval(fit, y)
            continue
        xs = np.where(~bad)[0]
        d[y, bad] = np.interp(np.where(bad)[0], xs, r[xs])
    return np.clip(d, 0, 1)


def p7(src):
    d = load(os.path.join(src, "b13p7_depth.png"))
    old = {"near": (d[650, 700], d[900, 691]), "mid": (d[540, 365], d[680, 365]), "far": (d[490, 240], d[560, 240])}
    m = np.zeros((H, W), np.float32)
    for x0, y0, x1, y1 in ((606, 530, 798, 980), (310, 466, 422, 730), (203, 438, 277, 596), (250, 925, 470, H)):
        cv2.rectangle(m, (x0, y0), (x1, y1), 1.0, -1)
    d = rowfill(d, m)
    # Square forged cages on plain square posts, a flat cap on each.
    for key, (cx0, cy0, cx1, cy1), (px0, px1, py1) in (("near", (640, 602, 742, 748), (680, 702, 968)),
                                                       ("mid", (338, 512, 392, 590), (359, 371, 722)),
                                                       ("far", (222, 474, 258, 526), (236, 244, 600))):
        head, post = old[key]
        cap = max(4, (cx1 - cx0) // 12)
        cv2.rectangle(d, (px0, cy1), (px1, py1), float(post), -1)
        cv2.rectangle(d, (cx0, cy0), (cx1, cy1), float(head), -1)
        cv2.rectangle(d, (cx0 - cap, cy0 - cap * 2), (cx1 + cap, cy0), float(head), -1)
    # The ford: flat stones raised a little across the shallows.
    for i, (x, y) in enumerate(curve([(800, 842), (870, 776), (940, 718), (1010, 662), (1080, 604), (1150, 548)], 9)):
        r = 44 - 3.0 * i
        st = np.zeros((H, W), np.float32)
        cv2.ellipse(st, (int(x), int(y + r * 0.15)), (int(r), int(r * 0.42)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        d = d + 0.03 * cv2.GaussianBlur(st, (0, 0), 1.5)
    return np.clip(d, 0, 1)


def p9(src):
    d = load(os.path.join(src, "b13p9_depth.png"))
    xs = np.arange(W, dtype=np.float32)
    # The old tower and its cross of roofs: rebuilt as sky over the rise.
    land = np.interp(xs, [360, 470, 520, 640, 700, 760], [426, 430, 418, 414, 424, 428])
    far = float(np.median(d[446:452, 470:700]))
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    box = np.zeros((H, W), bool)
    box[300:446, 440:720] = True
    d = np.where(box & (yy < land[None]), 0.0, d)
    d = np.where(box & (yy >= land[None]), far, d)
    v = far + 0.025
    # A long low hall of stone and timber, a steep roof, gable on; a squat square tower beside it.
    hall = [(470, 432), (470, 404), (466, 404), (484, 384), (590, 384), (608, 404), (604, 404), (604, 432)]
    cv2.fillPoly(d, [np.array(hall, np.int32)], float(v), lineType=cv2.LINE_AA)
    cv2.rectangle(d, (600, 352), (658, 434), float(v + 0.005), -1)
    cv2.rectangle(d, (596, 346), (662, 354), float(v + 0.005), -1)
    # The cloak's cone runs down over the log to the ground.
    c = float(d[760, 1070])
    cv2.fillPoly(d, [np.array([(930, 780), (1212, 780), (1228, 846), (916, 846)], np.int32)], c, lineType=cv2.LINE_AA)
    return np.clip(d, 0, 1)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(here, "out", "style_r15", "depth"))
    ap.add_argument("--out", default=os.path.join(here, "out", "style_r15", "layouts"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for k, f in (("p1", p1), ("p4", p4), ("p7", p7), ("p9", p9)):
        save(os.path.join(a.out, k + "_depth.png"), f(a.src))
        print(os.path.join(a.out, k + "_depth.png"))


if __name__ == "__main__":
    main()
