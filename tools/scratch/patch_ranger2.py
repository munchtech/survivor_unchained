p = r'C:\Users\munch\Desktop\survivorsunchained\tools\assets\heroine_outfits.py'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, n)


# ---- binding: fairer curves, and nothing left outside them.
rep('''def bind_edges(name, pos, at, tris, key, width, height, overhang, thick, sigma=0.007):''',
    '''def bind_edges(name, pos, at, tris, key, width, height, overhang, thick, sigma=0.012):''')
rep('''        # The sheet's edge points onto the fair line.
        lt = cKDTree(cur)
        _, jj = lt.query(pos[loop])
        pos[loop] = cur[jj]
        moved[loop] = True''', '''        # The sheet's edge points onto the fair line, and anything of the
        # sheet still standing out past it (scraps, pinched corners) pulled
        # back inside it.
        lt = cKDTree(cur)
        _, jj = lt.query(pos[loop])
        pos[loop] = cur[jj]
        moved[loop] = True
        dn, jn = lt.query(pos)
        near_ = dn < 0.025
        out_ = ((pos - cur[jn]) * outward[jn]).sum(1)
        fix = near_ & (out_ > 0)
        pos[fix] -= outward[jn[fix]] * out_[fix][:, None]
        moved |= fix''')

# ---- the strip under her crotch: a gusset laid along the roof of the slot.
a = s.index('def crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift, rows=18, cols=13):')
b = s.index('def on_surface(pts, step=0.004):')
s = s[:a] + '''def crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift):
    """What carries a garment under her crotch, where it was cut away
    either side of the slot between her thighs: a gusset of even width laid
    straight along the roof of the slot, overlapping the garment's bound
    edges in front and behind."""
    path = roof_path(GAP_F - 0.014, GAP_B + 0.014, 18, lift=0.002)
    return ribbon(name + "_gusset", path, 0.013, mkey, lift=0.0, thick=thick, snap=False)


''' + s[b:]

# ---- the reaver's string under her too.
rep('''*ribbon("reaver.gstring_back", back_string(bz0 + 0.07, CROTCH + 0.005), 0.022, "oldleather", lift=0.003, thick=0.004,
                trim=edge(0.004, "blackleather"), snap=False),''',
    '''*ribbon("reaver.gstring_back", thong_path(bz0 + 0.07), 0.022, "oldleather", lift=0.003, thick=0.004,
                trim=edge(0.004, "blackleather"), snap=False),''')

# ---- the ranger, after the reference.
a = s.index('def ranger():')
b = s.index('CHANNELS = ["warden", "arcanist", "reaver", "ranger"]')
RANGER = '''def leg_z(sd, s0):
    """Height of the point `s0` along a leg (metres from the hip)."""
    pts = LEG[sd]
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.array(pts), axis=0), axis=1))]
    return float(np.interp(s0, d, np.array(pts)[:, 2]))


def ranger():
    """The ranger, after the reference: a green leather suit (her left arm
    sleeved, a stand collar round the left and back of her neck, her left
    breast and leg covered, her right hip bare to a high-cut leotard line),
    smooth green cups, the right one on a halter; an underbust brown corset,
    cinched and pointed in front, laced across a gap; a belt slung round her
    hips with a buckle and a pouch on her left hip; a buckled strap high on
    her bare right thigh; bronze pauldron lames on her left shoulder, bronze
    bracers, fingerless gloves; knee boots with folded cuffs, the right one
    laced up the front."""
    arms = ARMW["l"] + ARMW["r"]

    def edge(w=0.006, key="darkleather"):
        return (key, w, 0.0006, 0.0013)

    nz = head("neck_01")[2]
    ang = np.arctan2(X, -(Y - CROTCH_Y))

    def belt_z(a):
        return CROTCH + 0.085 - 0.022 * np.sin(a)

    # The suit: her left upper body and sleeve, its inner edge a plunge from
    # the base of her neck down beside the cleavage; round her middle under
    # the corset; a leotard over her right hip; her left leg to the boot.
    plunge = X - (0.006 + 0.028 * np.clip((Z - UNDERBUST) / (nz - UNDERBUST), 0, 1))
    upper = AND(plunge, Z - (UNDERBUST - 0.05), 0.5 - ARMW["r"],
                (WRIST_S - 0.035) - ARM_S["l"] + 9 * (ARMW["l"] < 0.5))
    middle = AND(Z - (CROTCH + 0.04), (UNDERBUST - 0.01) - Z, 0.35 - arms)
    hips = AND((CROTCH + 0.12) - Z, Z - (CROTCH - 0.03), 0.3 - arms)
    lower = OR(AND(hips, OR(X + 0.01, bottom("full", top=0.11, side_rise=0.09))), limb("l", 0.0, KNEE_S + 0.08))
    suit = OR(upper, middle, lower)
    # The corset: under her breasts to the belt, a point in front, open
    # down the front for its lacing.
    ctop = UNDERBUST + 0.006 + 0.035 * (1 - FRONT)
    cbot = belt_z(ang) + 0.004 - 0.042 * np.clip(1 - np.abs(X) / 0.075, 0, 1) * FRONT
    opening = np.where(FRONT > 0.5, np.abs(X) - 0.012, 1.0)
    corset = AND(ctop - Z, Z - cbot, 0.35 - arms, OFF_BREAST, opening)
    # Eyelets down each side of the opening, laced across.
    zt = UNDERBUST - 0.01
    zb = belt_z(0.0) + 0.006
    rows = np.linspace(zt, zb, 7)
    sides = {}
    for sgn in (1, -1):
        e = []
        for z in rows:
            q = front_point(0.019 * sgn, z)
            n = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            e.append((q + n * 0.0105, n))
        sides[sgn] = e
    eyelets = [p for sg in (1, -1) for p, _ in sides[sg]]
    enorm = [n for sg in (1, -1) for _, n in sides[sg]]
    laces = []
    for i in range(len(rows) - 1):
        for sg in (1, -1):
            a0 = sides[sg][i][0]
            a1 = sides[-sg][i + 1][0]
            laces += ribbon(f"ranger.lace{i}{'ab'[sg > 0]}", [a0, a1], 0.0035, "darkleather", lift=0.0006, thick=0.0012, snap=False)
    # The halter: from the top of her right cup up to the collar.
    halter_curve = [NIPPLE["r"] + np.array([0.012, 0.0, 0.04]), np.array([-0.05, -0.1, 1.5]),
                    np.array([-0.03, -0.065, nz + 0.02]), np.array([-0.01, -0.03, nz + 0.035])]
    neck = (wsum("neck_01") > 0.35) & (HAIR < 0.5) & (Z > nz - 0.03) & (Z < nz + 0.09)
    # The belt and its gear.
    bfront = front_point(0.035, float(belt_z(0.2)))
    bn_ = np.array(SKIN_BVH.find_nearest(Vector(bfront))[1][:])
    tz = leg_z("r", 0.16)
    tpt = front_point(LEG["r"][0][0] - 0.03, tz)
    tn_ = np.array(SKIN_BVH.find_nearest(Vector(tpt))[1][:])
    fingers = wsum(*[n for n in BONES if n.split("_")[0] in ("index", "middle", "ring", "pinky", "thumb") and n.split("_")[1] in ("02", "03")])
    out = [
        *smooth_cups("ranger.cups", "greenleather", lift=0.008, thick=0.0022),
        *piece("ranger.suit", suit, "greenleather", lift=0.0028, smooth=3, soften=12, slot="right", trim=edge(0.005)),
        *girdle("ranger.collar", lambda a: np.full_like(a, nz + 0.035), 0.05, "greenleather", lift=0.004, thick=0.003,
                trim=edge(0.005), mask=neck, arc=(0.35, 4.55), flare=0.008, nu=90),
        *ribbon("ranger.halter", halter_curve, 0.016, "brownleather", lift=0.009, trim=edge(0.003)),
        *piece("ranger.corset", corset, "brownleather", lift=0.0058, thick=0.003, smooth=6, soften=20, trim=edge(0.006)),
        *domes("ranger.eyelets", eyelets, enorm, "bronze", r=0.0026),
        *laces,
        *girdle("ranger.belt", belt_z, 0.042, "brownleather", lift=0.011, thick=0.004, trim=edge(0.005)),
        *frame("ranger.buckle", bfront + bn_ * 0.02, bn_, np.array([0, 0, 1.0]), 0.042, 0.052, "bronze", r=0.0028),
        *pouch("ranger.pouch", "l", -0.005, float(belt_z(np.pi / 2)) - 0.055, (0.024, 0.055, 0.06), "brownleather"),
        *girdle("ranger.thighstrap", lambda a: np.full_like(a, tz), 0.028, "brownleather", lift=0.003, thick=0.003,
                trim=edge(0.004), mask=(LEGW["r"] > 0.6) & (np.abs(Z - tz) < 0.05)),
        *frame("ranger.thighbuckle", tpt + tn_ * 0.008, tn_, np.array([0, 0, 1.0]), 0.03, 0.036, "bronze", r=0.0022),
    ]
    sh = shoulder("l")
    for k, (dz, r, lift) in enumerate(((0.0, 0.11, 0.024), (-0.045, 0.1, 0.019), (-0.09, 0.09, 0.014), (-0.13, 0.08, 0.009))):
        c = sh + np.array([0.02 * k, 0, dz])
        out += piece(f"ranger.pauldron{k}", AND(cap(c, r), Z - (c[2] - r * 0.55)), "bronze", lift=lift, thick=0.004, smooth=14,
                     soften=10, studs="darksteel")
    tops = {"r": KNEE_S - 0.03, "l": KNEE_S + 0.1}
    for sd in "lr":
        cz = leg_z(sd, tops[sd] + 0.02)
        out += [
            *piece(f"ranger.bracer_{sd}", limb(sd, ELBOW_S + 0.04, WRIST_S - 0.015, legs=False), "bronze", lift=0.007, smooth=8,
                   soften=10, trim=edge(0.006, "brownleather"), studs="darksteel"),
            *piece(f"ranger.glove_{sd}", AND(limb(sd, WRIST_S - 0.03, 9.9, legs=False), 0.4 - fingers), "darkleather", lift=0.0015,
                   thick=0.0012, bevel=0.0004, soften=8),
            *piece(f"ranger.boot_{sd}", limb(sd, tops[sd], 9.9), "brownleather", lift=0.005, smooth=8, iron=300,
                   hull=LEG_S[sd] - ANKLE_S - 0.03, soften=10),
            *girdle(f"ranger.cuff_{sd}", lambda a, cz=cz: np.full_like(a, cz), 0.06, "brownleather", lift=0.01, thick=0.003,
                    trim=edge(0.005), mask=(LEGW[sd] > 0.6) & (np.abs(Z - cz) < 0.07), flare=0.012),
        ]
    # The right boot laced up the front of her shin, below its cuff.
    kx = LEG["r"][1][0]
    ax_ = LEG["r"][2][0]
    z0, z1 = LEG["r"][2][2] + 0.07, leg_z("r", tops["r"] + 0.02) - 0.04
    lz = np.linspace(z1, z0, 9)
    bl = {}
    for sgn in (1, -1):
        e = []
        for z in lz:
            t = (LEG["r"][1][2] - z) / (LEG["r"][1][2] - LEG["r"][2][2])
            x = kx + (ax_ - kx) * t + 0.013 * sgn
            q = front_point(x, z)
            n = np.array(SKIN_BVH.find_nearest(Vector(q))[1][:])
            e.append(q + n * 0.0095)
        bl[sgn] = e
    for i in range(len(lz) - 1):
        for sg in (1, -1):
            out += ribbon(f"ranger.bootlace{i}{'ab'[sg > 0]}", [bl[sg][i], bl[-sg][i + 1]], 0.003, "darkleather", lift=0.0005,
                          thick=0.0012, snap=False)
    return out


'''
s = s[:a] + RANGER + s[b:]
open(p, 'w', encoding='utf-8').write(s)
print("patched")
