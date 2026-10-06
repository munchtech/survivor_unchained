def heart_shape(cx, cy, s):
    t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    y = y - (y.max() + y.min()) / 2
    return poly([(cx + a * s / 16, cy + b * s / 16) for a, b in zip(x, y)])


def flame_tongue(x, y, w, h, lean=0.0):
    """A flame standing on (x, y): w wide at its foot, h tall, its tip leaning by `lean`."""
    return poly([(x - w / 2, y), (x - w * 0.55, y - h * 0.35), (x - w * 0.2 + lean * 0.4, y - h * 0.7), (x + lean, y - h),
                 (x + w * 0.15 + lean * 0.5, y - h * 0.6), (x + w * 0.55, y - h * 0.3), (x + w / 2, y)])


def d_aegis():
    """Shielded: a kite shield of the Order, a ward of dawn-gold round it."""
    e = Emblem("holy")
    e.lay(stroke(arc(50, 50, 42, 0, 360, 96), 3.0), "glow", 1, 1.2, light=1.0)
    kite = poly([(50, 90), (24, 52), (26, 18), (50, 10), (74, 18), (76, 52)])
    e.lay(kite, "steel", 5, 3)
    e.lay(cut(kite, poly([(50, 82), (30, 51), (32, 22), (50, 16), (68, 22), (70, 51)])), "gold", 6.5, 2)
    e.lay(stroke([(50, 20), (50, 76)], 4), "gold", 6.5, 2)
    e.lay(stroke([(34, 40), (66, 40)], 4), "gold", 6.5, 2)
    e.lay(circle(50, 40, 5), "glow", 2, 2, light=1.8, z=6.5)
    return e


def d_howl():
    """War cry: a carter's war horn, iron-banded, its call going out in red."""
    e = Emblem("blood")
    horn = stroke(bez((22, 78), (26, 40), (52, 22), (70, 30), 40), 6, 24)
    e.lay(horn, "bone", 5, 5)
    for (a, b) in (((24, 64), (34, 70)), ((32, 44), (42, 52)), ((48, 30), (54, 42))):
        e.lay(stroke([a, b], 3.2), "iron", 7, 1.5)
    e.lay(ellipse(70, 30, 6, 12, -28), F.Mat((0.02, 0.0, 0.0), 0.0, 0.8), 6, 1)
    for i, r in enumerate((14, 22, 30)):
        e.lay(stroke(arc(70, 30, r, 25, 125), 3.4 - i * 0.6), "glow", 1, 1.2, light=1.6 - i * 0.35)
    e.lay(stroke([(18, 82), (14, 90)], 5, 4), "gold_dim", 5, 2)
    return e


def d_expand():
    """Wider reach: a bright orb, four arrowheads driven outward from it."""
    e = Emblem("arcane")
    e.lay(circle(50, 50, 13), "glow", 2, 6, light=1.8)
    e.lay(stroke(arc(50, 50, 22, 0, 360, 96), 2.4), "glow", 1, 1, light=0.8)
    for ang in (45, 135, 225, 315):
        pts = rot([(50, 10), (64, 26), (56, 26), (56, 33), (44, 33), (44, 26), (36, 26)], ang)
        e.lay(poly(pts), "gold", 5, 2.5)
    return e


def d_retaura():
    """A ring of the Order's fire round you: flames standing all round an empty ring."""
    e = Emblem("holy")
    e.lay(cut(circle(50, 50, 30), circle(50, 50, 23)), "gold", 4, 2)
    for k in range(12):
        a = k * 30
        sd = flame_tongue(50, 22, 9, 16 + 7 * (k % 2), lean=1.5)
        e.lay(rotated(sd, a), "glow", 1, 2, light=1.5)
    e.lay(cut(circle(50, 50, 21), circle(50, 50, 17)), "glow", 1, 1, light=0.7)
    return e


def _at(sd, xr, yr):
    """A field sampled at other coordinates (to rotate or move a shape made at its place)."""
    mx = (xr * K).astype(np.float32)
    my = (yr * K).astype(np.float32)
    return cv2.remap(sd.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-50)


def rotated(sd, ang, cx=50, cy=50):
    c_, s_ = math.cos(math.radians(-ang)), math.sin(math.radians(-ang))
    xr = cx + (X - cx) * c_ - (Y - cy) * s_
    yr = cy + (X - cx) * s_ + (Y - cy) * c_
    return _at(sd, xr, yr)


def d_frostaura():
    """A ring of the Low Ford's rime: ice needles standing out all round."""
    e = Emblem("frost")
    e.lay(cut(circle(50, 50, 24), circle(50, 50, 19)), F.Mat(tuple(F.hexc("#c8e8ff")), 0.0, 0.08), 3, 2)
    needle = poly([(50, 4), (54, 24), (50, 28), (46, 24)])
    small = poly([(50, 12), (52.5, 25), (50, 27), (47.5, 25)])
    for k in range(16):
        e.lay(rotated(needle if k % 2 == 0 else small, k * 22.5), F.Mat(tuple(F.hexc("#d8f0ff")), 0.0, 0.05), 3, 2,
              round_=False, light=0.25)
    e.lay(cut(circle(50, 50, 18), circle(50, 50, 15)), "glow", 1, 1, light=0.9)
    return e


def d_pyre():
    """A pyre: logs crossed and stacked, a tall fire on them."""
    e = Emblem("fire")
    for (a, b, w) in (((14, 86), (86, 72), 9), ((16, 72), (84, 86), 9), ((22, 66), (78, 66), 8)):
        e.lay(stroke([a, b], w), "wood", 5, 4)
        e.lay(circle(b[0], b[1], w / 2 - 0.5), F.Mat(tuple(F.hexc("#8a5a34")), 0.0, 0.7), 5.5, 2)
    e.lay(flame_tongue(50, 66, 46, 58, lean=-2), "glow", 2, 6, light=1.6)
    e.lay(flame_tongue(36, 64, 18, 30, lean=-4), "glow", 2, 3, light=1.8)
    e.lay(flame_tongue(64, 64, 20, 34, lean=3), "glow", 2, 3, light=1.8)
    return e


def d_risen():
    """The risen: a grave's stone split, the barrow's violet light pouring out of the crack."""
    e = Emblem("shadow")
    mound = ellipse(50, 88, 40, 9)
    e.lay(mound, F.Mat(tuple(F.hexc("#2a2420")), 0.0, 0.9), 3, 4)
    stone = union(poly([(28, 88), (28, 34), (72, 34), (72, 88)]), circle(50, 34, 22))
    left = inter(stone, poly([(0, 0), (52, 0), (46, 30), (54, 46), (44, 64), (50, 100), (0, 100)]))
    right = inter(stone, poly([(100, 0), (54, 0), (48, 30), (56, 46), (46, 64), (52, 100), (100, 100)]))
    e.lay(rotated(left, -6, 30, 88), F.Mat(tuple(F.hexc("#5a5664")), 0.0, 0.7), 6, 3)
    e.lay(rotated(right, 5, 70, 88), F.Mat(tuple(F.hexc("#5a5664")), 0.0, 0.7), 6, 3)
    e.lay(stroke([(52, 10), (47, 30), (55, 46), (45, 64), (51, 90)], 4.5, 2.5), "glow", 1, 1.5, light=2.2)
    return e


def d_herd():
    """The spirit herd: a stag's skull and its great antlers in the Verge's green fire."""
    e = Emblem("nature")
    for sx in (-1, 1):
        beam = bez((50 + sx * 9, 40), (50 + sx * 22, 30), (50 + sx * 36, 22), (50 + sx * 40, 6), 30)
        e.lay(stroke(beam, 5.5, 2.5), "bone", 4, 2.5)
        for (t, dx, dy) in ((0.35, -2, -16), (0.6, 8, -10), (0.8, 10, -4)):
            p = beam[int(t * 29)]
            e.lay(stroke([p, (p[0] + sx * dx, p[1] + dy)], 3.6, 1.2), "bone", 4, 2)
    skull = poly([(50, 82), (40, 64), (36, 44), (42, 34), (50, 32), (58, 34), (64, 44), (60, 64)])
    e.lay(skull, "bone", 6, 5)
    for x in (43.5, 56.5):
        e.lay(ellipse(x, 47, 3.6, 4.6), "glow", 1, 1.5, light=2.2, z=3)
    e.lay(stroke([(47, 74), (53, 74)], 2.2), F.Mat((0.05, 0.04, 0.03), 0.0, 0.8), 6.2, 0.6)
    e.glow = 1.3
    return e


def d_tether():
    """A tether: a dark coil wound round a heart, drawing it."""
    e = Emblem("shadow")
    e.lay(heart_shape(50, 52, 30), F.Mat(tuple(F.hexc("#6a0c14")), 0.0, 0.25), 6, 8, light=0.4)
    for y0, y1 in ((24, 44), (40, 62), (58, 78)):
        e.lay(stroke(bez((12, y0), (40, y0 - 10), (60, y1 + 10), (90, y1), 30), 4.6), "glow", 1, 1.5, light=1.4, z=6)
    e.lay(stroke(bez((86, 76), (94, 64), (94, 40), (80, 26), 30), 3.2, 1.2), "glow", 1, 1.2, light=1.0)
    return e


def d_umbral():
    """An umbral bolt: a spearhead of shadow tearing forward, the dark streaming behind it."""
    e = Emblem("shadow")
    # The dark streaming behind it, down and to the left.
    for (a, b, w) in (((10, 92), (40, 62), 5), ((8, 76), (34, 58), 3), ((24, 96), (44, 70), 3)):
        e.lay(stroke([a, b], 1, w), "glow", 1, 1, light=0.9)
    head = poly(rot([(50, 6), (64, 40), (56, 36), (54, 70), (46, 70), (44, 36), (36, 40)], 55))
    e.lay(head, F.Mat(tuple(F.hexc("#141020")), 0.6, 0.3), 6, 4, light=0.2)
    edge = poly(rot([(50, 10), (60, 38), (50, 32), (40, 38)], 55))
    e.lay(edge, "glow", 1, 2, light=1.6, z=6)
    return e


def d_consecrate():
    """Consecrated ground: the Legion's seal burned gold into the stone, seven notches round it."""
    e = Emblem("holy")
    ring = cut(ellipse(50, 56, 42, 26), ellipse(50, 56, 33, 19))
    e.lay(ring, "glow", 1, 2, light=1.5)
    for k in range(7):
        a = math.radians(k * 360 / 7)
        x, y = 50 + 37.5 * math.sin(a), 56 - 22.5 * math.cos(a)
        e.lay(ellipse(x, y, 3.2, 2.4), F.Mat((0.03, 0.02, 0.01), 0.0, 0.8), 1.2, 0.5, z=0.5)
    e.lay(ellipse(50, 56, 12, 7), "glow", 1, 2, light=1.2)
    for x, h in ((50, 46), (38, 30), (62, 32), (26, 18), (74, 20)):
        e.lay(stroke([(x, 54), (x, 54 - h)], 3.2, 0.5), "glow", 1, 1, light=1.1)
    return e


def d_drain():
    """Drain: a thread of red life poured into an iron goblet."""
    e = Emblem("blood")
    cup = union(poly([(30, 30), (70, 30), (64, 50), (54, 58), (46, 58), (36, 50)]), stroke([(50, 58), (50, 80)], 6),
                ellipse(50, 84, 16, 5))
    e.lay(cup, "iron", 5, 4)
    e.lay(cut(ellipse(50, 31, 20, 4.5), ellipse(50, 31, 18, 3.2)), "gold", 6, 1.5)
    e.lay(ellipse(50, 31.5, 17.5, 3), "glow", 1, 1, light=1.4, z=4)
    stream = bez((90, 8), (74, 6), (58, 12), (52, 30), 30)
    e.lay(stroke(stream, 2.4, 5.4), "glow", 1, 2, light=1.8)
    for x, y, r in ((84, 22, 1.8), (72, 26, 1.4), (63, 22, 1.1)):
        e.lay(circle(x, y, r), "glow", 1, 1, light=1.5)
    return e


def d_static():
    """Static: two iron studs, a spark leaping between them."""
    e = Emblem("storm")
    for x, y in ((22, 72), (78, 30)):
        e.lay(circle(x, y, 10), "iron", 5, 4)
        e.lay(circle(x, y, 4), "gold", 7, 2)
    bolt = [(26, 66), (36, 58), (32, 52), (48, 46), (44, 40), (60, 38), (56, 32), (74, 34)]
    e.lay(stroke(bolt, 5, 3), "glow", 1, 1.5, light=2.0)
    e.lay(stroke([(48, 46), (56, 56), (62, 54)], 2.4, 0.8), "glow", 1, 1, light=1.4)
    e.lay(stroke([(36, 58), (32, 40)], 2.0, 0.6), "glow", 1, 1, light=1.2)
    return e


def d_book():
    """A tome of the Order: worn leather, iron corners, an ember set in its cover."""
    e = Emblem("arcane")
    cover = poly([(24, 14), (76, 14), (80, 18), (80, 86), (76, 90), (24, 90), (20, 86), (20, 18)])
    e.lay(cover, "leather", 6, 3)
    e.lay(stroke([(22, 18), (22, 86)], 6), F.Mat(tuple(F.hexc("#2a160e")), 0.0, 0.6), 7, 2)
    for x, y, sx, sy in ((22, 16, 1, 1), (78, 16, -1, 1), (22, 88, 1, -1), (78, 88, -1, -1)):
        e.lay(poly([(x, y), (x + sx * 13, y), (x, y + sy * 13)]), "iron", 7, 1.5)
    e.lay(cut(poly([(50, 30), (66, 52), (50, 74), (34, 52)]), poly([(50, 36), (61, 52), (50, 68), (39, 52)])), "gold", 7.5, 1.5)
    e.lay(circle(50, 52, 6.5), "glow", 2, 2.5, light=2.0, z=6)
    e.lay(stroke([(80, 46), (90, 46), (90, 58), (80, 58)], 3), "iron", 6, 1.5)
    return e


DESIGNS = {k[2:]: f for k, f in globals().items() if k.startswith("d_")}

SUBJECT.update({
    "aegis": "a steel kite shield with a gold cross and rim, a ring of golden ward light round it",
    "howl": "a curved bone war horn bound with iron bands, its call going out in red rings of sound",
    "expand": "a glowing violet orb with four gold arrowheads driven outward from it",
    "retaura": "a ring of golden holy flames standing all round an empty circle",
    "frostaura": "a ring of sharp ice needles standing outward all round an empty circle, frost",
    "pyre": "a pyre of crossed logs with a tall fire burning on it",
    "risen": "a gravestone split in two, violet light pouring out of the crack",
    "herd": "a stag's skull with great branching antlers, green spirit fire in its eyes",
    "tether": "a dark red heart bound by coils of glowing violet shadow",
    "umbral": "a black spearhead of shadow tearing forward, violet light along its edge, dark streaks behind it",
    "consecrate": "a glowing golden seal burned into dark stone ground, seven notches round it, rays rising from it",
    "drain": "a thread of glowing red blood pouring into an iron goblet",
    "static": "two iron studs with a crackling blue spark of lightning leaping between them",
    "book": "an old leather tome with iron corners and a glowing violet ember set in a gold diamond on its cover",
})
