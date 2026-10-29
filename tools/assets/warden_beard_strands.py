"""The Ford-Warden's beard r6: layered strand cards on her hair atlas and shader (godot/art/npc/ford_warden/beard.glb).

    python tools/assets/warden_beard_strands.py PKG_DIR [--work DIR] [--seed N] [--no-write]

r5 (warden_beard.py) was a sculpted mass of tubes with wide cards over it; the max judge scrapped it ("the wide,
hard-edged cards read as ropes, shards, slats or a bead strip"). This rebuild keeps warden_beard.py's guides (roots on
the Face Forge head, the drape held in front of him, the hood's collar cleared, the Head ramp) and its skinning and
writer, and draws every lock as a BUNDLE of narrow strand cards through the lock's volume instead of a tube:

  - each card a strip of her strand atlas (godot/art/people/head_tex/hair_strands.png, as many of its strands as the
    card is wide: her strands' fineness), three points across, its plane turned a little round the strand (no flat fan),
    its own wander, its own length (soft, staggered tips: its vertex alpha fades out over the last fifth);
  - lit as one mass (normals the beard's outward way, leaning toward the card's place in its lock), her shader's
    Kajiya-Kay highlight along it (BINORMAL root to tip), darker deep in (vertex r) and at the roots (her `roots`);
  - layers: inner (dense columns, dark, close), mid (dense and loose), outer (locks and wisps, thin, clumped to wet
    points, waved: the silhouette broken into strands); a dark solid core ribbon behind the middle of the inner layer
    (no tabard through the gaps; never at the beard's outline);
  - the moustache as bundles falling over the mouth; three braids (three-strand plaits, solid, their lobes shaded) with
    cord bands; river weed as thin olive cards.
Tips at the top of the tabard's lamp badge (concept A_hero).
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import warden_beard as wb  # noqa: E402

from warden_beard import (DENSE, LOOSE, LOCK, WISP, X0, HH, smoothstep, log)  # noqa: E402

ATLAS_URI = "../../people/head_tex/hair_strands.png"
ROOT_DARK, ROOT_RAMP = 0.35, 0.40     # each card's depth (vertex r) at its root, of its own, easing up over this share of it
COL_W = 1.0 / 16                       # one atlas column's width in u
STRAND_M = 0.016                       # metres of card width per column (her cards' 12-20 mm: her strands' fineness)

# lock layers (warden_beard.lock_lines' cfg) and each lock's bundle of cards
LAYERS = [
    dict(name="inner", spacing=0.020, off=0.0080, width=(0.034, 0.046), depth=(0.012, 0.016), clump=0.15, jit=0.030, wave=0.0015,
         cards=5, cw=(0.0075, 0.012), cols=DENSE, narrow=0.45, shade=(0.30, 0.48), turn=0.35, lf=(0.86, 1.02), tip_fade=0.80),
    dict(name="mid", spacing=0.022, off=0.0135, width=(0.028, 0.038), depth=(0.010, 0.013), clump=0.40, jit=0.055, wave=0.0025,
         cards=4, cw=(0.0060, 0.010), cols=DENSE + LOOSE, narrow=0.60, shade=(0.55, 0.78), turn=0.45, lf=(0.80, 1.03), tip_fade=0.75),
    dict(name="outer", spacing=0.024, off=0.0190, width=(0.018, 0.026), depth=(0.008, 0.011), clump=0.62, jit=0.085, wave=0.0035,
         cards=3, cw=(0.0035, 0.0065), cols=LOCK + LOOSE[:2] + WISP, narrow=0.80, shade=(0.80, 1.00), turn=0.55, lf=(0.75, 1.06), tip_fade=0.65),
]
MOUSTACHE = dict(spacing=0.0068, off=0.0048, width=(0.014, 0.020), depth=(0.006, 0.008), length=(0.060, 0.090),
                 cards=4, cw=(0.0040, 0.0070), cols=LOCK + DENSE[:3], narrow=0.75, shade=(0.62, 0.95), turn=0.4, lf=(0.80, 1.02), tip_fade=0.6)
CORE = dict(adx=0.040, w=0.55, back=0.40, r=0.10, lf=0.85)   # the dark core ribbons: inner locks within adx of the centre
TIP_Y = (1.235, 1.285)                 # the tips: the centre at the top of the badge, the sides a little higher
STRAYS = dict(n=22, cw=(0.0020, 0.0035), cols=WISP, shade=(0.85, 1.0))
K_BY_LENGTH = ((0.10, 7), (0.20, 9), (9.0, 11))   # a card's points by its length
# the braids (warden_beard.braid_lines: x top and bottom off the centre line, y from and to, half-width, twist, tuft):
# within the beard, their tufts ending with it (r5's ran 6 cm past it), the outer two thicker (A_b)
BRAIDS = [dict(x=(0.040, 0.032), y=(1.445, 1.290), R=0.0098, pitch=0.032, tuft=0.040, shade=(0.70, 0.92)),
          dict(x=(-0.044, -0.036), y=(1.440, 1.300), R=0.0098, pitch=0.032, tuft=0.038, shade=(0.66, 0.88)),
          dict(x=(-0.008, -0.012), y=(1.400, 1.290), R=0.0068, pitch=0.024, tuft=0.032, shade=(0.62, 0.86))]
WEED_LENGTH = (0.06, 0.15)


def _skin_mats(g):
    j = g.j
    sk = j["skins"][0]
    names = [j["nodes"][n]["name"] for n in sk["joints"]]
    M = np.asarray(g.acc(sk["inverseBindMatrices"]), float).reshape(-1, 4, 4).transpose(0, 2, 1)   # (glTF column-major)
    return names, M


_prims = wb.prims


def prims_rest(path):
    """warden_beard.prims, a garment glb carried into body.glb's rest (Warden 7 garment r3 binds the hood at the game's
    idle, its head 12 cm lower and 7 cm back: in the body's rest its collar and capelet stood where his chest is): each
    vertex by its own skin, sum w (body bind) (garment inverse bind) v."""
    g, out = _prims(path)
    if os.path.basename(path) == "body.glb" or "skins" not in g.j:
        return g, out
    body = os.path.join(os.path.dirname(os.path.dirname(path)), "body.glb")
    gn, gI = _skin_mats(g)
    bn, bI = _skin_mats(wb.Glb(body))
    bB = {n: np.linalg.inv(m) for n, m in zip(bn, bI)}
    X = np.stack([bB.get(n, np.linalg.inv(m)) @ m for n, m in zip(gn, gI)])     # per garment joint
    for k, v in out.items():
        if v["J"] is None:
            continue
        P4 = np.c_[v["P"], np.ones(len(v["P"]))]
        Q = np.zeros_like(P4)
        for c in range(4):
            Q += v["W"][:, c:c + 1] * np.einsum("nij,nj->ni", X[v["J"][:, c]], P4)
        v["P"] = Q[:, :3] / np.maximum(v["W"].sum(1, keepdims=True), 1e-9)
    log(f"{os.path.basename(path)} carried into body.glb's rest")
    return g, out


wb.prims = prims_rest


def frames_out(pk, C):
    t = np.gradient(C, axis=1)
    t /= np.linalg.norm(t, axis=2)[..., None] + 1e-12
    out = wb.outward(pk, C)
    side = np.cross(t, out)
    side /= np.linalg.norm(side, axis=2)[..., None] + 1e-12
    out = np.cross(side, t)
    return t, side, out


def resample_len(C, frac, K):
    """Each line (S x K0 x 3) cut to `frac` of its length and resampled to K points."""
    S = len(C)
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(C, axis=1), axis=2), 1)]
    out = np.zeros((S, K, 3))
    for s in range(S):
        t = np.linspace(0, arc[s, -1] * frac[s], K)
        for c in range(3):
            out[s, :, c] = np.interp(t, arc[s], C[s, :, c])
    return out


def ribbons(P, N, Sd, cw, cols, narrow, shade, alpha_fn, rng, root_w=0.6):
    """Cards (glTF): S guides P (S x K x 3), each with its normal N and across-way Sd (S x K x 3), its width cw (S),
    atlas columns, tapering by `narrow`; three points across (L, M, R), the middle bulged out a little. Returns a part
    dict as warden_beard.tubes' (pos, nrm, uv, col, tan, idx, at, arc, S)."""
    S, K, _ = P.shape
    f = np.linspace(0, 1, K)
    taper = (root_w + (1 - root_w) * smoothstep(0.0, 0.22, f)) * (1 - narrow * f ** 1.5)
    w = cw[:, None] * taper[None]
    L = P - Sd * (w / 2)[..., None]
    R = P + Sd * (w / 2)[..., None]
    M = P + N * (w * 0.10)[..., None]
    V = np.stack([L, M, R], 1)                                   # S x 3 x K x 3
    Nv = np.repeat(N[:, None], 3, 1)
    col = np.asarray(cols)[rng.integers(0, len(cols), S)]
    span = np.minimum(cw / STRAND_M, 1.0) * (COL_W - 0.004)
    u0 = col * COL_W + 0.002 + rng.random(S) * (COL_W - 0.004 - span)
    U = np.stack([u0, u0 + span / 2, u0 + span], 1)               # S x 3
    UV = np.stack([np.broadcast_to(U[:, :, None], (S, 3, K)), np.broadcast_to(f[None, None], (S, 3, K))], -1)
    r = np.asarray(shade, float)
    g_ = rng.random(S)
    a = alpha_fn(f)[None].repeat(S, 0) if callable(alpha_fn) else np.ones((S, K))
    Cc = np.zeros((S, 3, K, 4))
    Cc[..., 0] = r[:, None, None] * (ROOT_DARK + (1 - ROOT_DARK) * smoothstep(0.0, ROOT_RAMP, f))[None, None, :]   # (r6b: roots dark, near the jaw's value)
    Cc[..., 1] = g_[:, None, None]
    Cc[..., 3] = a[:, None, :]
    base = (np.arange(S) * 3 * K)[:, None]
    k = np.arange(K - 1)[None, :]
    q1 = np.stack([base + K + k, base + K + k + 1, base + k + 1, base + k], -1).reshape(-1, 4)
    q2 = np.stack([base + 2 * K + k, base + 2 * K + k + 1, base + K + k + 1, base + K + k], -1).reshape(-1, 4)
    F = wb.tris_of(np.vstack([q1, q2]))
    Vf = V.reshape(-1, 3)
    Nf = Nv.reshape(-1, 3)
    # (wound to face out, as her cards)
    fn = np.cross(Vf[F[:, 1]] - Vf[F[:, 0]], Vf[F[:, 2]] - Vf[F[:, 0]])
    flip = (fn * Nf[F[:, 0]]).sum(1) < 0
    F[flip] = F[flip][:, [0, 2, 1]]
    at = np.repeat(P[:, None], 3, 1).reshape(-1, 3)
    tan = wb.tangents(Vf, Nf, F, at, [(S, K)])
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=2), 1)]
    return dict(pos=Vf, nrm=Nf, uv=UV.reshape(-1, 2), col=Cc.reshape(-1, 4), tan=tan, idx=F, at=at,
                arc=np.repeat(arc[:, None], 3, 1).ravel(), S=S)


def tip_alpha(start):
    return lambda f: (1 - 0.9 * smoothstep(start, 1.0, f)) * (0.55 + 0.45 * smoothstep(0.0, 0.08, f))


def bundles(pk, C, w, d, cfg, rng, n=None, wide=1.0):
    """Each lock (glTF centre line, width, depth) as `cards` strand cards through its volume. Returns a part."""
    n = n or cfg["cards"]
    S0, K0, _ = C.shape
    t, side, out = frames_out(pk, C)
    f0 = np.linspace(0, 1, K0)
    prof = (1 - f0 ** 2.2) ** 0.7 * (0.65 + 0.35 * smoothstep(0.0, 0.15, f0))
    dprof = prof * (0.45 + 0.55 * smoothstep(0.0, 0.15, f0))
    Ps, Ns, Ss, cws, rs = [], [], [], [], []
    lo, hi = cfg["shade"]
    for s in range(S0):
        # (the cards spread evenly across the lock, jittered; front ones lighter, back ones darker)
        a = (np.arange(n) + rng.uniform(0.15, 0.85, n)) / n - 0.5
        b = rng.uniform(-0.5, 0.5, n)
        for j in range(n):
            arc_w = rng.normal(0, 1, 3)
            ph = rng.uniform(0, 6.28, 2)
            lam = rng.uniform(0.05, 0.11)
            arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C[s], axis=0), axis=1))]
            wander = (np.sin(2 * np.pi * arc / lam + ph[0])[:, None] * side[s] * 0.0012 * (1 + arc_w[0] * 0.3)
                      + np.sin(2 * np.pi * arc / (lam * 1.4) + ph[1])[:, None] * out[s] * 0.0008) * smoothstep(0.05, 0.35, f0)[:, None]
            spread = (a[j] * side[s] * 0.35 * w[s] + b[j] * out[s] * 0.2 * d[s]) * (f0 ** 2)[:, None]   # (tips fanned)
            P = C[s] + side[s] * (a[j] * w[s] * prof)[:, None] + out[s] * (b[j] * d[s] * dprof)[:, None] + wander + spread
            th = rng.uniform(-cfg["turn"], cfg["turn"])
            Sd = side[s] * np.cos(th) + out[s] * np.sin(th)
            Nn = out[s] * 0.85 + side[s] * (a[j] * 0.5) + out[s] * (b[j] * 0.3)
            Nn /= np.linalg.norm(Nn, axis=1)[:, None]
            Ps.append(P); Ns.append(Nn); Ss.append(Sd)
            cws.append(rng.uniform(*cfg["cw"]) * wide)
            rs.append(np.clip(rng.uniform(lo, hi) * (0.86 + 0.28 * (b[j] + 0.5)), 0.05, 1.0))
    P = np.array(Ps); N = np.array(Ns); Sd = np.array(Ss); cw = np.array(cws); r = np.array(rs)
    frac = rng.uniform(*cfg["lf"], len(P))
    L = np.linalg.norm(np.diff(P, axis=1), axis=2).sum(1) * frac
    parts = []
    lo_ = 0.0
    for hi_, K in K_BY_LENGTH:
        m = (L >= lo_) & (L < hi_)
        lo_ = hi_
        if not m.any():
            continue
        Pk = resample_len(P[m], frac[m], K)
        idx = np.linspace(0, K0 - 1, K)
        def rs_(A):
            Ar = np.zeros((m.sum(), K, 3))
            for c in range(3):
                Ar[:, :, c] = np.array([np.interp(idx * fr, np.arange(K0), A[i, :, c]) for i, fr in zip(np.nonzero(m)[0], frac[m])])
            n_ = np.linalg.norm(Ar, axis=2)[..., None] + 1e-12
            return Ar / n_
        parts.append(ribbons(Pk, rs_(N), rs_(Sd), cw[m], cfg["cols"], cfg["narrow"], r[m], tip_alpha(cfg["tip_fade"]), rng))
    return wb.cat_parts(parts)


def cores(pk, C, w, d, rng):
    """The dark solid core ribbons behind the inner layer's middle locks (material hair_mass)."""
    adx = np.abs(C[:, 0, 0] - X0)
    m = adx < CORE["adx"]
    if not m.any():
        return None
    C, w, d = C[m], w[m], d[m]
    t, side, out = frames_out(pk, C)
    K0 = C.shape[1]
    f0 = np.linspace(0, 1, K0)
    P = C - out * (CORE["back"] * d[:, None, None])
    Pk = resample_len(P, np.full(len(P), CORE["lf"]), 9)
    idx = np.linspace(0, (K0 - 1) * CORE["lf"], 9)
    def rs_(A):
        Ar = np.stack([np.array([np.interp(idx, np.arange(K0), A[i, :, c]) for i in range(len(A))]) for c in range(3)], -1)
        return Ar / (np.linalg.norm(Ar, axis=2)[..., None] + 1e-12)
    p = ribbons(Pk, rs_(out), rs_(side), w * CORE["w"], [0], 0.7, np.full(len(Pk), CORE["r"]), None, rng, root_w=0.8)
    p["uv"][:, 0] = p["uv"][:, 0] * 4.0          # (the mass texture tiles across)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg")
    ap.add_argument("--work", default=None)
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--no-preview", action="store_true")
    a = ap.parse_args()
    work = a.work or os.path.join(a.pkg, "..", "_beard_work")
    os.makedirs(work, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    lrng = np.random.default_rng(a.seed + 1)
    t0 = time.time()
    wb.TIP_Y = TIP_Y
    wb.BRAIDS = BRAIDS
    wb.WEED["length"] = WEED_LENGTH
    pk = wb.Package(a.pkg, rng)
    rep = {"locks": {}, "cards": {}}
    full, lod, shadow, solid = [], [], [], []

    # the soft edge on the skin at the line (warden_beard's short fine cards)
    ep, en, _ = wb.root_points(pk, rng, 0.0078, "edge")
    elen = rng.uniform(*wb.FINE["length"], len(ep))
    Pe, _ = wb.grow(pk, ep, en, "edge", wb.FINE, rng, elen.max())
    Pe = wb.trim(Pe, elen)
    wb.collider(pk, face_only=False)
    edge = wb.card_part(pk, [wb.card_set(Pe, wb.FINE, rng, wb.FINE["K"], alpha=wb.FINE["alpha"], edge=True)])
    rep["cards"]["edge"] = len(ep)

    # the moustache
    Cm, wm, dm = wb.lock_lines(pk, "moustache", MOUSTACHE, rng)
    Cm, _ = wb.hood_clear(pk, Cm, wm, dm, most=1.0)
    full.append(bundles(pk, Cm, wm, dm, MOUSTACHE, rng))
    lod.append(bundles(pk, Cm[::2], wm[::2], dm[::2], MOUSTACHE, lrng, n=1, wide=2.2))
    rep["locks"]["moustache"] = len(Cm)

    inner = None
    for L_ in LAYERS:
        C, w, d = wb.lock_lines(pk, "beard", L_, rng)
        C, kp = wb.hood_clear(pk, C, w, d)
        C, w, d = C[kp], w[kp], d[kp]
        full.append(bundles(pk, C, w, d, L_, rng))
        if L_["name"] != "mid":
            lod.append(bundles(pk, C, w, d, L_, lrng, n=1, wide=2.6 if L_["name"] == "inner" else 1.8))
        if L_["name"] == "inner":
            inner = (C, w, d)
            shadow.append(wb.tubes(pk, C, w, d, 4, 6, (0.5, 0.5), lrng))
        elif L_["name"] == "outer":
            shadow.append(wb.tubes(pk, C[::2], w[::2], d[::2], 4, 6, (0.5, 0.5), lrng))
        rep["locks"][L_["name"]] = len(C)
        rep["cards"][L_["name"]] = len(C) * L_["cards"]
    core = cores(pk, *inner, rng)
    if core is not None:
        solid.append(core)
        rep["cores"] = int(core["S"])

    # the braids (on the cards' front surface) and their bands; the weed
    fp = wb.cat_parts(full)
    grid = wb.surface_grid(fp["pos"], fp["idx"])
    br, ties, br_lod = wb.braids(pk, grid, rng, lrng)
    solid.append(br)
    lod.append(br_lod)
    shadow.append(br_lod)
    rep["braids"] = len(wb.BRAIDS)
    weed = wb.card_part(pk, [wb.card_set(wb.weed_lines(pk, grid, rng), wb.WEED, rng, wb.WEED["K"])])
    rep["weed"] = int(weed["pos"].shape[0] // (3 * wb.WEED["K"]))

    card_p = wb.skin_part(pk, wb.cat_parts(full))
    edge_p = edge
    solid_p = wb.skin_part(pk, wb.cat_parts(solid))
    tie_p = wb.skin_part(pk, ties)
    lod_p = wb.skin_part(pk, wb.cat_parts(lod))
    sh_p = wb.skin_part(pk, wb.cat_parts(shadow))
    tris = sum(len(p["idx"]) for p in (card_p, edge_p, solid_p, tie_p, weed))
    rep.update(tris=int(tris), cardTris=int(len(card_p["idx"])), edgeTris=int(len(edge_p["idx"])), solidTris=int(len(solid_p["idx"])),
               tieTris=int(len(tie_p["idx"])), weedTris=int(len(weed["idx"])), lodTris=int(len(lod_p["idx"])), shadowTris=int(len(sh_p["idx"])),
               rest=wb.measure(pk, card_p), seconds=round(time.time() - t0, 1))
    log(json.dumps(rep))
    json.dump(rep, open(os.path.join(work, "beard_report.json"), "w"), indent=1)
    if not a.no_preview:
        card_p["tint"], solid_p["tint"], weed["tint"] = (0.55, 0.75, 0.95), (0.75, 0.62, 0.45), (0.3, 0.6, 0.2)
        wb.preview(pk, [solid_p, card_p, weed], os.path.join(work, "beard_preview.png"))
        lod_p["tint"] = (0.62, 0.60, 0.55)
        wb.preview(pk, [lod_p], os.path.join(work, "beard_lod1_preview.png"), views=("front", "q"))
    if a.no_write:
        return
    wb.CARDS_TEX = ATLAS_URI                 # (material 0 "hair" and 4 "hair_weed" on her own strand atlas)
    wb.mass_texture(os.path.join(a.pkg, wb.MASS_TEX))
    sh = dict(pos=sh_p["pos"], nrm=sh_p["nrm"], J=sh_p["J"], W=sh_p["W"], idx=sh_p["idx"])
    wb.write(pk, os.path.join(a.pkg, "beard.glb"),
             [("beard", [(solid_p, 2), (card_p, 0), (edge_p, 0), (tie_p, 3), (weed, 4)]), ("beard.lod1", [(lod_p, 0)]), ("beard.shadow", [(sh, 1)])])
    man_path = os.path.join(a.pkg, "manifest.json")
    man = json.load(open(man_path, encoding="utf-8"))
    man["hair"] = {"file": "beard.glb", "colour": wb.COLOUR, "style": "beard", "uniforms": wb.HAIR_UNIFORMS,
                   "source": "tools/assets/warden_beard_strands.py (r6: layered strand cards on her atlas and shader, dark core ribbons, braids with cord bands, river weed)",
                   "tris": rep["tris"], "cardTris": rep["cardTris"], "solidTris": rep["solidTris"], "lodTris": rep["lodTris"],
                   "shadowTris": rep["shadowTris"], "locks": rep["locks"], "cards": rep["cards"], "braids": rep["braids"], "weed": rep["weed"]}
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    log("manifest hair set")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    main()
