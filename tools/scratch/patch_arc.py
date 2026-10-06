p = r'C:\Users\munch\Desktop\survivorsunchained\tools\assets\heroine_outfits.py'
s = open(p, encoding='utf-8').read()

# ---- materials: more of them, and sheer ones (a seventh field: opacity).
s = s.replace('''    "fur": ("faux_fur_geometric", (0.6, 0.48, 0.36), None, 4, 0.0, None),
}''', '''    "fur": ("faux_fur_geometric", (0.6, 0.48, 0.36), None, 4, 0.0, None),
    "arcvelvet": ("velour_velvet", (0.42, 0.34, 1.0), 62, 5, 0.0, None),
    "plumleather": ("Leather026", (0.62, 0.42, 0.75), 48, 3, 0.0, None),
    "blackleather": ("Leather026", (1, 1, 1), 26, 3, 0.0, None),
    "brownleather": ("Leather021", (1, 0.9, 0.8), 60, 3, 0.0, None),
    "lace": ("velour_velvet", (0.3, 0.3, 0.32), 14, 8, 0.0, 0.5),
    "stocking": ("rough_linen", (0.4, 0.38, 0.42), 18, 14, 0.0, 0.45, 0.62),
}''')
s = s.replace('''    src, tint, mean, _, metal, rough = SPEC[key]''', '''    src, tint, mean, _, metal, rough = SPEC[key][:6]
    alpha = SPEC[key][6] if len(SPEC[key]) > 6 else 1.0''')
s = s.replace('''    MATS[key] = m
    return m''', '''    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    MATS[key] = m
    return m''')

# ---- piece: what it keeps off (her head and hair, or, for a choker, only them).
s = s.replace('''trim=None, clear=None, soften=3, dome=False):''', '''trim=None, clear=None, soften=3, dome=False, keep_off=("Head", "neck_01")):''')
s = s.replace('''    f = smooth_field(np.minimum(field, (0.3 - wsum("Head", "neck_01")) * 0.1), soften)''', '''    f = smooth_field(np.minimum(field, (0.3 - wsum(*keep_off)) * 0.1), soften)''')

# ---- hanging cloth and the hat, before the outfits.
NEW = '''def trimmed(name, pos, at, tris, mkey, thick, bevel, trim):
    """A sheet and, if asked, the gold along its edge (the field in `at`'s
    last column is the distance in from the edge)."""
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel)]
    if trim:
        tkey, w, h, tt = trim
        tp, ta, tr = clip(w - at[:, -1], pos, at, tris)
        if len(tr):
            tp, ta, tr = weld(tp, ta, tr)
            tp = relax(tp + vertex_normals(tp, tr) * (thick + h), tr)
            made.append(finish(name + "_trim", tp, ta[:, 3:3 + NB], tr, tkey, tt, bevel))
    return made


def grid(nu, nv):
    i = np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :]
    i = i.ravel()
    return np.vstack([np.c_[i, i + nv, i + 1], np.c_[i + 1, i + nv, i + nv + 1]])


def hanging(name, a0, a1, z_top, hem, mkey, flare=0.15, lift=0.01, gap=0.012, thick=0.0025, trim=None, nu=56):
    """Cloth hanging from her hips, all round her between the angles a0 and
    a1 (radians; 0 her front, rising toward her left): at each angle it
    falls from the hips, flaring out by `flare` a metre of fall, and never
    nearer her than `gap` (so it goes over her thighs, not into them). Its
    hem is `hem(u)`, u from -1 at a0 to 1 at a1. It is weighted to the
    pelvis at the top and more and more to the thigh on its side below the
    hip, so it swings with her stride."""
    ring = (np.abs(Z - z_top) < 0.008) & (ARMW["l"] + ARMW["r"] < 0.3)
    cy = (Y[ring].min() + Y[ring].max()) / 2
    zs = np.arange(z_top, min(hem(u) for u in np.linspace(-1, 1, 41)) - 0.03, -0.006)
    a = np.linspace(a0, a1, nu)
    body = (ARMW["l"] + ARMW["r"] < 0.3) & (wsum("Head") < 0.3)
    ang = np.arctan2(X, -(Y - cy))
    rad = np.hypot(X, Y - cy)
    R = np.full((len(zs), nu), np.nan)
    for k, z in enumerate(zs):
        m = body & (np.abs(Z - z) < 0.006)
        if not m.any():
            continue
        for j, aj in enumerate(a):
            d = np.abs((ang[m] - aj + np.pi) % (2 * np.pi) - np.pi)
            w = d < 0.12
            if w.any():
                R[k, j] = rad[m][w].max()
    R[0] = np.where(np.isnan(R[0]), np.nanmax(R[0]), R[0])
    for k in range(1, len(zs)):
        R[k] = np.where(np.isnan(R[k]), 0, R[k])
    hang = (R[0] + lift)[None, :] + flare * (z_top - zs)[:, None]
    r = np.maximum(hang, R + gap)
    r = np.maximum.accumulate(r, axis=0)
    for _ in range(6):
        r[1:-1] = (r[:-2] + 2 * r[1:-1] + r[2:]) / 4
        r[:, 1:-1] = (r[:, :-2] + 2 * r[:, 1:-1] + r[:, 2:]) / 4
        r = np.maximum(r, R + gap)
    zz = np.repeat(zs[:, None], nu, 1)
    aa = np.repeat(a[None, :], len(zs), 0)
    pos = np.stack([r * np.sin(aa), cy - r * np.cos(aa), zz], -1).reshape(-1, 3)
    tris = grid(len(zs), nu)
    nor = vertex_normals(pos, tris)
    out = np.c_[np.sin(aa).ravel(), -np.cos(aa).ravel()]
    if ((nor[:, :2] * out).sum(1)).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    u = (aa.ravel() - a0) / (a1 - a0) * 2 - 1
    zb = np.array([hem(x) for x in u])
    arc = np.minimum(aa.ravel() - a0, a1 - aa.ravel()) * r.ravel()
    f = np.minimum.reduce([pos[:, 2] - zb, z_top - pos[:, 2] + 0.002, arc])
    hip = head("thigh_l")[2]
    leg = 0.85 * ramp(hip - pos[:, 2], 0.0, 0.45)
    side = 1 / (1 + np.exp(-pos[:, 0] / 0.035))
    wt = np.zeros((len(pos), NB))
    wt[:, BI["pelvis"]] = 1 - leg
    wt[:, BI["thigh_l"]] = leg * side
    wt[:, BI["thigh_r"]] = leg * (1 - side)
    attr = np.hstack([nor, wt, f[:, None]])
    pos, at, tris = clip(f, pos, attr, tris)
    pos, at, tris = weld(pos, at, tris)
    pos = relax(pos, tris)
    return trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim)


def witch_hat(name, mkey, band_key, brim=0.16, height=0.34, droop=0.09):
    """A wide-brimmed hat with a tall crown that bends back and droops at
    the tip, set on her hair: its crown is as wide as her hair at the brim
    and never nearer it than a centimetre above. All of it is her head's."""
    hd = wsum("Head") > 0.5
    top = Z[hd].max()
    upper = hd & (Z > top - 0.1)
    cx, cy = X[upper].mean(), Y[upper].mean()
    zb = top - 0.07
    ang = np.arctan2(X[hd] - cx, -(Y[hd] - cy))
    rad = np.hypot(X[hd] - cx, Y[hd] - cy)
    nu = 64
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)

    def hair_r(z, dz=0.008):
        m = np.abs(Z[hd] - z) < dz
        out = np.zeros(nu)
        for j, aj in enumerate(a):
            d = np.abs((ang[m] - aj + np.pi) % (2 * np.pi) - np.pi) < 0.15
            if d.any():
                out[j] = rad[m][d].max()
        return out

    base = hair_r(zb) + 0.012
    base = np.maximum(base, np.percentile(base, 60) * 0.92)
    for _ in range(4):
        base = (np.roll(base, 1) + 2 * base + np.roll(base, -1)) / 4
    # The crown, ring by ring.
    K = 36
    rings = []
    for k in range(K + 1):
        t = k / K
        z = zb + height * t
        bend = max(0.0, t - 0.45) / 0.55
        ccy = cy + 0.13 * bend ** 2
        cz = z - droop * bend ** 3
        scale = (1 - t) ** 1.15
        rr = base * scale + 0.004 * (1 - t)
        need = hair_r(z) + 0.01
        rr = np.maximum(rr, need * (need > 0.01))
        rings.append(np.stack([cx + rr * np.sin(a), ccy - rr * np.cos(a), np.full(nu, cz)], -1))
    crown = np.array(rings).reshape(-1, 3)
    ct = grid(K + 1, nu + 1)
    # Close the seam: wrap the angle.
    idx = np.arange((K + 1) * nu).reshape(K + 1, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    ct = idx[ct]
    # The brim: from the crown's base out, sagging a little, its sides
    # turned up and front and back down (the witch's wave).
    M = 14
    br = []
    for k in range(M + 1):
        t = k / M
        rr = base + brim * t
        z = zb - 0.012 * t * t + 0.03 * t * t * (np.cos(2 * a) * -1 + 1) / 2 - 0.015 * t * t
        br.append(np.stack([cx + rr * np.sin(a), cy - rr * np.cos(a), z], -1))
    brimp = np.array(br).reshape(-1, 3)
    idx = np.arange((M + 1) * nu).reshape(M + 1, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    bt = idx[grid(M + 1, nu + 1)]
    # A band round the crown's foot.
    bandp = np.array(rings[:4]).reshape(-1, 3)
    bandp[:, :2] = (bandp[:, :2] - [cx, cy]) * 1.03 + [cx, cy]
    bandt = np.arange(4 * nu).reshape(4, nu)
    bandt = np.c_[bandt, bandt[:, :1]].ravel()[grid(4, nu + 1)]
    out = []
    for nm, pp, tt, key, th in ((name + "_crown", crown, ct, mkey, 0.003), (name + "_brim", brimp, bt, mkey, 0.004),
                                (name + "_band", bandp, bandt, band_key, 0.002)):
        n = vertex_normals(pp, tt)
        rad_out = pp[:, :2] - [cx, cy]
        if (n[:, :2] * rad_out).sum(1).mean() < 0 and nm.endswith(("crown", "band")):
            tt = tt[:, ::-1]
        if nm.endswith("brim") and n[:, 2].mean() < 0:
            tt = tt[:, ::-1]
        wt = np.zeros((len(pp), NB))
        wt[:, BI["Head"]] = 1
        out.append(finish(nm, pp, wt, tt, key, th, 0.001))
    print("HAT brim at %.3f, crown base %.3f-%.3f m" % (zb, base.min(), base.max()))
    return out


# ---------------------------------------------------------------- outfits --'''
s = s.replace('# ---------------------------------------------------------------- outfits --', NEW, 1)

ARC = '''def arcanist():
    """The arcanist: a velvet capelet and sleeves, a plum leather corset
    with gold boning under low velvet half-cups, an open coat that bares
    her thighs, sheer stockings, thigh boots and a witch's hat."""
    def gold(w=0.006):
        return ("gold", w, 0.0004, 0.0013)

    # Half-cups: high enough at the outside to cover the nipple, falling
    # steeply toward the middle, so the inner and upper breast show.
    parts = []
    for sd, s_ in (("l", 1), ("r", -1)):
        n, nip = NIP[sd], NIPPLE[sd]
        c = n + np.array([0, 0.035, -0.012])
        r = np.linalg.norm(P - c, axis=1)
        top = nip[2] + 0.03 - 0.55 * np.maximum(0, abs(nip[0]) - np.abs(X))
        parts.append(AND(0.098 - r, top - Z, X * s_ - 0.008, -(Y - 0.02)))
    cup = OR(*parts)
    arms = ARMW["l"] + ARMW["r"]
    ctop = UNDERBUST + 0.012 + 0.07 * (1 - FRONT)
    cbot = 1.012 - 0.04 * np.exp(-(X / 0.04) ** 2) * FRONT
    corset = AND(ctop - Z, Z - cbot, 0.35 - arms)
    belt_z = 1.0 + 0.035 * X / 0.18
    belt = AND(0.016 - np.abs(Z - belt_z), 0.3 - arms)
    bones = OR(*[strap([np.array([x, -0.25, UNDERBUST - 0.004]), np.array([x * 0.85, -0.25, 1.02 - 0.02 * (abs(x) < 0.05)])], 0.005)
                 for x in (-0.085, -0.04, 0.04, 0.085)])
    bones = AND(bones, corset - 0.004)
    nz = head("neck_01")[2]
    choker = AND(0.009 - np.abs(Z - (nz + 0.035)), wsum("neck_01", "Head") - 0.4, 0.3 - wsum("Head") + wsum("neck_01") * 0, 0.3 - arms)
    mantle = OR(cap(shoulder("l"), 0.14), cap(shoulder("r"), 0.14),
                AND(Z - 1.43, (Y - 0.0), 0.3 - arms))
    out = [
        *piece("arcanist.cups", cup, "arcvelvet", lift=0.007, thick=0.0025, clear=0.0015, dome=True, trim=gold()),
        *piece("arcanist.corset", corset, "plumleather", lift=0.0035, smooth=6, trim=gold(0.007)),
        *piece("arcanist.boning", bones, "gold", lift=0.0062, thick=0.0012, soften=0),
        *piece("arcanist.briefs", bottom("full"), "arcvelvet", lift=0.0025, smooth=2),
        *piece("arcanist.mantle", mantle, "arcvelvet", lift=0.016, thick=0.004, smooth=12, trim=gold(0.01)),
        *piece("arcanist.choker", choker, "blackleather", lift=0.002, soften=0, keep_off=("Head",)),
        *piece("arcanist.belt", belt, "brownleather", lift=0.017, thick=0.004, smooth=3),
        *piece("arcanist.buckle", AND(cap(np.array([0.0, -0.2, 1.0]), 0.02), belt), "gold", lift=0.021, thick=0.003, soften=0),
        *hanging("arcanist.apron", -0.3, 0.3, 1.0, lambda u: 0.56 + 0.07 * abs(u), "arcvelvet", flare=0.12, lift=0.012, trim=gold(0.012)),
        *hanging("arcanist.coat", 1.2, 2 * np.pi - 1.2, 1.0, lambda u: 0.3 + 0.16 * abs(u) ** 1.5, "arcvelvet", flare=0.3, lift=0.012, trim=gold(0.014)),
        *witch_hat("arcanist.hat", "arcvelvet", "gold"),
    ]
    for sd in "lr":
        out += [
            *piece(f"arcanist.sleeve_{sd}", limb(sd, 0.17, WRIST_S - 0.03, legs=False), "arcvelvet", lift=0.005, smooth=4, trim=gold(0.01)),
            *piece(f"arcanist.glove_{sd}", limb(sd, WRIST_S - 0.08, 9.9, legs=False), "blackleather", lift=0.0012, thick=0.001, bevel=0.0004),
            *piece(f"arcanist.stocking_{sd}", limb(sd, KNEE_S - 0.2, 9.9), "stocking", lift=0.001, thick=0.0006, bevel=0.0),
            *piece(f"arcanist.lace_{sd}", limb(sd, KNEE_S - 0.2, KNEE_S - 0.165), "lace", lift=0.0022, thick=0.001, soften=1),
            *piece(f"arcanist.boot_{sd}", limb(sd, KNEE_S - 0.05, 9.9, front_dip=-0.03), "brownleather", lift=0.004, smooth=4),
            *piece(f"arcanist.cuff_{sd}", limb(sd, KNEE_S - 0.065, KNEE_S - 0.015), "brownleather", lift=0.009, thick=0.003, smooth=6, trim=gold(0.005)),
        ]
    return out


OUTFITS = {"warden": warden, "arcanist": arcanist}'''
s = s.replace('OUTFITS = {"warden": warden}', ARC, 1)
open(p, 'w', encoding='utf-8').write(s)
print("patched")
