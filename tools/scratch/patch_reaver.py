p = r'C:\Users\munch\Desktop\survivorsunchained\tools\assets\heroine_outfits.py'
s = open(p, encoding='utf-8').read()

# Cups without their trims.
s = s.replace('*smooth_cups("warden.cups", "steel", trim=gold()),', '*smooth_cups("warden.cups", "steel"),')
s = s.replace('*smooth_cups("arcanist.cups", "arcvelvet", thick=0.0025, trim=gold()),', '*smooth_cups("arcanist.cups", "arcvelvet", thick=0.0025),')
s = s.replace('*smooth_cups("ranger.cups", "greenleather", thick=0.0025, trim=gold(0.006, "brownleather")),', '*smooth_cups("ranger.cups", "greenleather", thick=0.0025),')

s = s.replace('''    "stocking": ("rough_linen",''', '''    "ink": ("rough_linen", (0.22, 0.26, 0.34), 22, 10, 0.0, 0.65),
    "stocking": ("rough_linen",''')

REAVER = '''def bandeau(name, mkey, zc, width, lift=0.004, thick=0.003, trim=None, rows=11, nu=120):
    """A strip of leather round her chest at height `zc`, `width` tall,
    pulled taut: each row of it lies on the convex hull of her body's
    section there (her arms left out), so it runs straight across the
    cleavage from breast to breast as a strap does, never into it. It
    moves with the skin nearest each point of it (her breasts' springs
    included)."""
    from scipy.spatial import ConvexHull
    body_pts = (ARMW["l"] + ARMW["r"] < 0.25) & (HAIR < 0.5)
    zs = np.linspace(zc - width / 2, zc + width / 2, rows)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    R = np.zeros((rows, nu))
    cxy = None
    for k, z in enumerate(zs):
        m = body_pts & (np.abs(Z - z) < 0.01)
        q = P[m][:, :2]
        if cxy is None:
            cxy = q.mean(0)
        h = ConvexHull(q)
        hv = q[h.vertices]
        d = np.stack([np.sin(a), -np.cos(a)], 1)
        best = np.zeros(nu)
        for i in range(len(hv)):
            p0, p1 = hv[i] - cxy, hv[(i + 1) % len(hv)] - cxy
            e = p1 - p0
            den = d[:, 0] * e[1] - d[:, 1] * e[0]
            ok = np.abs(den) > 1e-12
            t = np.where(ok, (p0[0] * e[1] - p0[1] * e[0]) / np.where(ok, den, 1), -1)
            u = np.where(ok, (p0[0] * d[:, 1] - p0[1] * d[:, 0]) / np.where(ok, den, 1), -1)
            hit = ok & (t > 0) & (u >= 0) & (u <= 1)
            best = np.where(hit, np.maximum(best, t), best)
        R[k] = best
    for _ in range(3):
        R[1:-1] = (R[:-2] + 2 * R[1:-1] + R[2:]) / 4
        R = (np.roll(R, 1, 1) + 2 * R + np.roll(R, -1, 1)) / 4
    R = R + lift
    zz = np.repeat(zs[:, None], nu, 1)
    aa = np.repeat(a[None, :], rows, 0)
    pos = np.stack([cxy[0] + R * np.sin(aa), cxy[1] - R * np.cos(aa), zz], -1).reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(rows, nu + 1)]
    nor = vertex_normals(pos, tris)
    if (nor[:, :2] * (pos[:, :2] - cxy)).sum(1).mean() < 0:
        tris = tris[:, ::-1]
        nor = -nor
    _, j = cKDTree(P).query(pos)
    edge = np.minimum(pos[:, 2] - zs[0], zs[-1] - pos[:, 2])
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.001, trim)
    for o in made:
        o["hides"] = True
    print("BANDEAU", name, "at %.3f, %.3f tall" % (zc, width))
    return made


def limb_angle(sd, legs=True):
    """Each point's angle round a limb's upper segment (radians)."""
    a, b = (LEG[sd][0], LEG[sd][1]) if legs else (ARM[sd][0], ARM[sd][1])
    ax = (b - a) / np.linalg.norm(b - a)
    ref = np.cross(ax, [1.0, 0, 0]) if abs(ax[0]) < 0.9 else np.cross(ax, [0, 1.0, 0])
    ref /= np.linalg.norm(ref)
    sec = np.cross(ax, ref)
    d = P - a
    return np.arctan2(d @ sec, d @ ref)


def zigzag_band(sd, s0, legs=True, width=0.005, amp=0.012, teeth=7):
    """A tattooed band round a limb at `s0` along it: a zigzag line,
    `teeth` points round, `amp` high."""
    S = LEG_S[sd] if legs else ARM_S[sd]
    Wm = LEGW[sd] if legs else ARMW[sd]
    th = limb_angle(sd, legs)
    tri = np.arcsin(np.sin(teeth * th)) / (np.pi / 2)
    return AND(width / 2 - np.abs(S - s0 - amp * tri), Wm - 0.5)


def reaver():
    """The reaver: a loincloth over a leather thong, a strip of leather
    across her breasts, a fur half cape over her left shoulder, fur-topped
    boots and fur cuffs at her wrists, leather bracers, and tattoos: zigzag
    bands round her right arm and left thigh."""
    arms = ARMW["l"] + ARMW["r"]

    def edge(w=0.005, key="darkleather"):
        return (key, w, 0.0004, 0.0013)

    nz = (NIPPLE["l"][2] + NIPPLE["r"][2]) / 2
    belt_z = 0.995 + 0.02 * X / 0.18
    belt = AND(0.02 - np.abs(Z - belt_z), 0.3 - arms)
    cape = OR(cap(shoulder("l"), 0.13),
              AND(X + 0.02, Y + 0.0, Z - 1.16, 0.4 - ARMW["r"], 0.5 - ARMW["l"] + 9 * (Z > head("upperarm_l")[2] - 0.02)))
    out = [
        *bandeau("reaver.strap", "oldleather", nz, 0.05, trim=edge()),
        *piece("reaver.thong", bottom("thong"), "darkleather", lift=0.0025, smooth=2),
        *piece("reaver.belt", belt, "oldleather", lift=0.012, thick=0.004, smooth=3, soften=10),
        *piece("reaver.buckle", AND(0.022 - np.linalg.norm(P - front_point(0.0, 0.995), axis=1), belt + 0.004), "rust", lift=0.017, thick=0.003, smooth=4, soften=1),
        *hanging("reaver.loin_front", -0.33, 0.33, 0.99, lambda u: 0.52 + 0.07 * u * u, "oldleather", flare=0.06, lift=0.016, trim=edge(0.01)),
        *hanging("reaver.loin_back", np.pi - 0.42, np.pi + 0.42, 0.99, lambda u: 0.55 + 0.07 * u * u, "oldleather", flare=0.1, lift=0.016, trim=edge(0.01)),
        *piece("reaver.cape", cape, "fur", lift=0.02, thick=0.014, smooth=12, soften=10, keep_off=("Head",)),
        *piece("reaver.tattoo_arm", OR(zigzag_band("r", ELBOW_S - 0.13, legs=False), zigzag_band("r", ELBOW_S - 0.085, legs=False, amp=0.008)), "ink", lift=0.0006, thick=0.0002, bevel=0.0, soften=0),
        *piece("reaver.tattoo_thigh", OR(zigzag_band("l", 0.16), zigzag_band("l", 0.21, amp=0.009)), "ink", lift=0.0006, thick=0.0002, bevel=0.0, soften=0),
    ]
    for sd in "lr":
        out += [
            *piece(f"reaver.bracer_{sd}", limb(sd, ELBOW_S + 0.05, WRIST_S - 0.04, legs=False), "oldleather", lift=0.004, smooth=6, trim=edge()),
            *piece(f"reaver.wristfur_{sd}", limb(sd, WRIST_S - 0.05, WRIST_S + 0.005, legs=False), "fur", lift=0.012, thick=0.012, smooth=8),
            *piece(f"reaver.boot_{sd}", limb(sd, KNEE_S - 0.01, 9.9), "oldleather", lift=0.005, smooth=8, iron=300, hull=LEG_S[sd] - ANKLE_S - 0.03),
            *piece(f"reaver.bootfur_{sd}", limb(sd, KNEE_S - 0.05, KNEE_S + 0.06), "fur", lift=0.016, thick=0.016, smooth=10),
        ]
    return out


OUTFITS = {"warden": warden, "arcanist": arcanist, "ranger": ranger, "reaver": reaver}'''
s = s.replace('OUTFITS = {"warden": warden, "arcanist": arcanist, "ranger": ranger}', REAVER, 1)
open(p, 'w', encoding='utf-8').write(s)
print("patched")
