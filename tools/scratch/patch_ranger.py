p = r'C:\Users\munch\Desktop\survivorsunchained\tools\assets\heroine_outfits.py'
s = open(p, encoding='utf-8').read()

s = s.replace('''    "stocking": ("rough_linen",''', '''    "greenleather": ("Leather026", (0.42, 0.85, 0.45), 52, 3, 0.0, None),
    "bronze": ("Metal048C", (0.85, 0.62, 0.4), 120, 3, 1.0, None),
    "stocking": ("rough_linen",''')

# Outfits' hide channels are fixed, whatever order they are built in.
s = s.replace('''    for k, name in enumerate(OUTFITS):
        objs =''', '''    for name in OUTFITS:
        k = CHANNELS.index(name)
        objs =''')
s = s.replace('''# Her skin under each outfit's fitted pieces is marked, one colour channel
# an outfit (in OUTFITS' order), for the game to leave undrawn''', '''# Her skin under each outfit's fitted pieces is marked, one colour channel
# an outfit (CHANNELS, as People.cs has them), for the game to leave undrawn''')

s = s.replace('''def front_line(x0, z0, x1, z1, width, n=80):''', '''def front_poly(pts, width, n=30):
    """A line through (x, z) points down her front, on her skin as seen
    from ahead (a lacing's zigzag, a boot's laces)."""
    on = []
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        on += [front_point(x0 + (x1 - x0) * t, z0 + (z1 - z0) * t) for t in np.linspace(0, 1, n)]
    d, _ = cKDTree(np.array(on)).query(P)
    return width / 2 - d


def side_point(sd, y, z):
    """Her skin on her side at (y, z), as a ray from beside her finds it."""
    s_ = 1 if sd == "l" else -1
    hit = BVH.ray_cast(Vector((0.6 * s_, y, z)), Vector((-s_, 0, 0)), 1.2)
    return np.array(hit[0][:]) if hit[0] is not None else np.array([0.18 * s_, y, z])


def pouch(name, sd, y, z, size, mkey):
    """A leather pouch on her hip: a rounded box (a superellipsoid), its
    back against her skin, moving as her skin there does."""
    s_ = 1 if sd == "l" else -1
    at = side_point(sd, y, z)
    a, b, c = size
    nu, nv = 18, 32
    th = np.linspace(0.02, np.pi - 0.02, nu)[:, None]
    ph = np.linspace(0, 2 * np.pi, nv, endpoint=False)[None, :]
    e = 0.3

    def sp(v):
        return np.sign(v) * np.abs(v) ** e

    lx = a * sp(np.sin(th) * np.cos(ph))
    ly = b * sp(np.sin(th) * np.sin(ph))
    lz = c * sp(np.cos(th) * np.ones_like(ph))
    pos = np.stack([at[0] + s_ * (a + 0.004) + s_ * lx, at[1] + ly, at[2] + lz], -1).reshape(-1, 3)
    idx = np.arange(nu * nv).reshape(nu, nv)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(nu, nv + 1)]
    n = vertex_normals(pos, tris)
    if ((pos - pos.mean(0)) * n).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    _, j = cKDTree(P).query(at)
    wt = np.repeat(W[j][None, :], len(pos), 0)
    return [finish(name, pos, wt, tris, mkey, 0.002, 0.0)]


def front_line(x0, z0, x1, z1, width, n=80):''', 1)

RANGER = '''def ranger():
    """The ranger: green leather, asymmetric. Her right arm and shoulder
    bare, the cup there held by a halter strap round her neck; her left in
    a full sleeve with a high collar and a layered bronze pauldron. A laced
    brown corset and belt, a pouch on her left hip; a leotard cut high over
    her right hip, that leg bare to the boot but for a buckled thigh strap,
    her left leg in green leather. Bracers, fingerless gloves, cuffed boots,
    the right one laced."""
    arms = ARMW["l"] + ARMW["r"]

    def gold(w=0.006, key="bronze"):
        return (key, w, 0.0004, 0.0013)

    cup, _ = cups(cover=0.6, plunge=0.012)
    # Above the cups on her left: chest, shoulder, back; and the sleeve.
    upper_l = AND(X + 0.005, Z - (UNDERBUST - 0.04), 0.5 - ARMW["r"], (WRIST_S - 0.03) - ARM_S["l"] + 9 * (ARMW["l"] < 0.5))
    nz = head("neck_01")[2]
    collar = AND(wsum("neck_01", "Head") - 0.3, X + 0.02, (nz + 0.075) - Z, 0.3 - arms)
    halter = strap([NIPPLE["r"] + np.array([0.01, 0.0, 0.03]), np.array([-0.06, -0.1, 1.5]), np.array([-0.035, -0.06, nz + 0.03]),
                    np.array([0.0, 0.0, nz + 0.05])], 0.022)
    # The suit below the corset: all round on her left, a high-cut leotard
    # on her right; her left leg in it down into the boot.
    hips = AND(1.06 - Z, Z - (CROTCH - 0.03), 0.3 - arms)
    lower = OR(AND(hips, OR(X + 0.01, bottom("full", top=0.11, side_rise=0.09))), limb("l", 0.0, KNEE_S + 0.05))
    ctop = UNDERBUST + 0.008 + 0.05 * (1 - FRONT)
    corset = AND(ctop - Z, Z - (1.03 - 0.03 * np.exp(-(X / 0.05) ** 2) * FRONT), 0.35 - arms)
    lz = np.linspace(UNDERBUST - 0.03, 1.05, 9)
    lacing = AND(front_poly([((0.018 if i % 2 else -0.018), z) for i, z in enumerate(lz)], 0.007), corset - 0.003)
    belt_z = 1.0 - 0.035 * X / 0.18
    belt = AND(0.018 - np.abs(Z - belt_z), 0.3 - arms)
    thigh = limb("r", 0.13, 0.165)
    fingers = wsum(*[n for n in BONES if n.split("_")[0] in ("index", "middle", "ring", "pinky", "thumb") and n.split("_")[1] in ("02", "03")])
    out = [
        *piece("ranger.cups", cup, "greenleather", lift=0.009, thick=0.0025, clear=0.0015, dome=True, trim=gold(0.006, "brownleather")),
        *piece("ranger.upper", upper_l, "greenleather", lift=0.003, smooth=4),
        *piece("ranger.collar", collar, "greenleather", lift=0.004, smooth=4, keep_off=("Head",), trim=gold(0.006, "brownleather")),
        *piece("ranger.halter", halter, "brownleather", lift=0.005, soften=0),
        *piece("ranger.suit", lower, "greenleather", lift=0.0025, smooth=3),
        *piece("ranger.corset", corset, "brownleather", lift=0.0055, smooth=6, trim=gold(0.006, "darkleather")),
        *piece("ranger.lacing", lacing, "darkleather", lift=0.0105, thick=0.0015, smooth=6, soften=1),
        *piece("ranger.belt", belt, "brownleather", lift=0.014, thick=0.004, smooth=3),
        *piece("ranger.buckle", AND(0.024 - np.linalg.norm(P - front_point(0.03, 1.0 - 0.035 * 0.03 / 0.18), axis=1), belt + 0.004), "bronze", lift=0.019, thick=0.003, smooth=4, soften=1),
        *piece("ranger.thighstrap", thigh, "brownleather", lift=0.004, thick=0.003, smooth=3),
        *piece("ranger.thighbuckle", AND(0.018 - np.linalg.norm(P - front_point(LEG["r"][0][0] - 0.01, LEG["r"][0][2] - 0.145), axis=1), thigh + 0.004), "bronze", lift=0.008, thick=0.003, smooth=3, soften=1),
        *pouch("ranger.pouch", "l", -0.01, 0.95, (0.022, 0.05, 0.06), "brownleather"),
    ]
    sh = shoulder("l")
    for k, (dz, r, lift) in enumerate(((0.0, 0.11, 0.022), (-0.045, 0.1, 0.017), (-0.09, 0.09, 0.012))):
        c = sh + np.array([0.02 * k, 0, dz])
        out += piece(f"ranger.pauldron{k}", AND(cap(c, r), Z - (c[2] - r * 0.55)), "bronze", lift=lift, thick=0.004, smooth=14, trim=gold(0.008, "brownleather"))
    for sd in "lr":
        out += [
            *piece(f"ranger.bracer_{sd}", limb(sd, ELBOW_S + 0.04, WRIST_S - 0.015, legs=False), "bronze", lift=0.007, smooth=8, trim=gold(0.006, "brownleather")),
            *piece(f"ranger.glove_{sd}", AND(limb(sd, WRIST_S - 0.03, 9.9, legs=False), 0.4 - fingers), "darkleather", lift=0.0015, thick=0.0012, bevel=0.0004),
            *piece(f"ranger.boot_{sd}", limb(sd, KNEE_S - 0.03, 9.9), "brownleather", lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03),
            *piece(f"ranger.cuff_{sd}", limb(sd, KNEE_S - 0.06, KNEE_S + 0.02), "brownleather", lift=0.013, thick=0.004, smooth=8),
        ]
    kx, kz = LEG["r"][1][0], LEG["r"][1][2]
    ax_, az = LEG["r"][2][0], LEG["r"][2][2]
    zs = np.linspace(kz - 0.08, az + 0.06, 11)
    laces = front_poly([(kx + (ax_ - kx) * (kz - 0.08 - z) / (kz - 0.08 - az) + (0.016 if i % 2 else -0.016), z) for i, z in enumerate(zs)], 0.006)
    out += piece("ranger.laces", AND(laces, limb("r", KNEE_S + 0.05, ANKLE_S)), "darkleather", lift=0.0085, thick=0.0015, smooth=4, soften=1)
    return out


CHANNELS = ["warden", "arcanist", "reaver", "ranger"]
OUTFITS = {"warden": warden, "arcanist": arcanist, "ranger": ranger}'''
s = s.replace('OUTFITS = {"warden": warden, "arcanist": arcanist}', RANGER, 1)
open(p, 'w', encoding='utf-8').write(s)
print("patched")
