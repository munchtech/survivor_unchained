"""The Ford-Warden's material ID map (shaders/warden_wet.gdshader), in his body surface's own UVs.

His Meshy body is one 4096 atlas of tiny charts with one material, so the shader can't tell wool from leather from
iron. This map says, per texel, what each bit of him is made of. It is made from the bind pose and the atlas:
  * 3D place and skin weights, rasterised into UV space: which part of him a texel is on (head, arm, hand, torso,
    leg) and where (height, front/back, distance from the leg's bone line, along the arm);
  * the atlas colour at that texel (hue, saturation, value) and its local contrast (the quilting's grid);
  * the atlas's metal channel (buckles).
Rules (classify()), then a majority filter per chart so specks don't flip class, wool holes in the quilting filled
by a 3D vote (fill3d()), then dilated gutters.

Channels (2048, RGBA8; imported lossless, alpha untouched):
  R  class * 32 + puff (0..31): the class index (the shader texelFetches it and blends the 4 neighbours' params);
     the low bits (0..1): on the quilting, the padding's loft (0 in a stitch line, 1 on a channel's top: the shader
     shades the grooves); on the tabard its fade (sun and river, 1 most faded); on the iron its convexity (0.5 flat,
     1 a convex edge: wear; 0 a recess); elsewhere a free smooth noise
  G  bind height (y / 2 m): the wet gradient (soaked from the hem to the thigh, drier toward the shoulders)
  B,A  a detail normal (tangent-space x, y; 0.5 = flat): each class's 3D height (wool twill, tabard plain weave,
     quilting weave + sag and creasing noise, leather grain, iron dents), baked from the bind pose triplanar on the
     world planes, so it is continuous across the atlas's charts
Classes:
  0 wool      hood, mantle, the dark robe under the tabard (the default)
  1 tabard    the blue surcoat
  2 quilting  the gambeson sleeves and skirts
  3 leather   belts, straps, pouch, boots
  4 iron      gauntlets, buckles, mail
  5 badge     the pale emblem on the tabard's chest
  6 head      face and rope beard (being replaced: a sane class only)

  python tools/assets/warden_wet_maps.py [PKG_DIR]     (first: its occlusion finds the face deep in the hood)
  python tools/assets/warden_id_map.py [PKG_DIR] [--size 2048] [--debug OUT_DIR]
Writes PKG_DIR/id_generated.png (+ a class-colour picture in --debug OUT_DIR), and fills wet_generated.png's B and A
(body_extras(): the beard's drip, wet streaks; so run it after warden_wet_maps.py).
Re-run after any change to body.glb's geometry or UVs (it reads only body.glb's "generated" surface).
"""
import argparse, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage, sparse
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warden_wet_maps import Glb  # noqa: E402

NAMES = ["wool", "tabard", "quilting", "leather", "iron", "badge", "head"]
WOOL, TABARD, QUILT, LEATHER, IRON, BADGE, HEAD = range(7)
DEBUG_RGB = np.array([(40, 40, 60), (40, 90, 230), (200, 170, 90), (150, 70, 30), (170, 180, 190), (255, 255, 255), (230, 120, 170)], np.uint8)
GROUPS = ["head", "arm", "hand", "torso", "thigh", "leg"]


def group_of(name):
    if name in ("Head", "neck_01"):
        return 0
    if "hand" in name or any(f in name for f in ("index", "middle", "pinky", "ring", "thumb")):
        return 2
    if any(f in name for f in ("upperarm", "lowerarm", "clavicle")):
        return 1
    if "thigh" in name:
        return 4
    if any(f in name for f in ("calf", "foot", "ball")):
        return 5
    return 3


def raster_fields(uv, idx, vals, size):
    """Per-vertex values into UV space (glTF UV, v down); returns (fields, covered). Gutters left for the caller."""
    c = vals.shape[1]
    out = np.zeros((size, size, c), np.float32)
    have = np.zeros((size, size), bool)
    px = uv * size - 0.5
    for t in idx:
        a, b, cc = px[t[0]], px[t[1]], px[t[2]]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), cc)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), cc)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
        if abs(den) < 1e-12:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w0 = ((b[1] - cc[1]) * (X - cc[0]) + (cc[0] - b[0]) * (Y - cc[1])) / den
        w1 = ((cc[1] - a[1]) * (X - cc[0]) + (a[0] - cc[0]) * (Y - cc[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.03) & (w1 >= -0.03) & (w2 >= -0.03)
        if not m.any():
            continue
        out[Y[m], X[m]] = w0[m, None] * vals[t[0]] + w1[m, None] * vals[t[1]] + w2[m, None] * vals[t[2]]
        have[Y[m], X[m]] = True
    return out, have


def curvature(P, N, idx, rings=3):
    """Per-vertex convexity (m): the vertex against its welded neighbours' smoothed mean, along the smoothed normal;
    + on convex edges (the iron's worn rims), - in recesses. The unwrap splits vertices at its seams: welded first."""
    _, wid = np.unique(np.round(P / 1e-5).astype(np.int64), axis=0, return_inverse=True)
    wid = wid.ravel(); nw = wid.max() + 1
    e = wid[np.r_[idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]]]
    A = sparse.coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), (nw, nw)).tocsr()
    A.data[:] = 1.0
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)[:, None]
    cnt = np.bincount(wid, minlength=nw)[:, None].astype(float)
    Pw = np.zeros((nw, 3)); np.add.at(Pw, wid, P); Pw /= cnt
    Nw = np.zeros((nw, 3)); np.add.at(Nw, wid, N); Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-9)
    S = Pw.copy()
    for _ in range(rings):
        S = 0.5 * S + 0.5 * (A @ S) / deg
    c = np.einsum("ij,ij->i", Pw - S, Nw)
    for _ in range(1):
        c = 0.5 * c + 0.5 * (A @ c[:, None]).ravel() / deg.ravel()
    return c[wid]


def seg_dist(P, a, b):
    """Distance from points to segment a-b and the parameter along it (0 at a, 1 at b)."""
    d = b - a
    t = np.clip(((P - a) @ d) / (d @ d), -0.5, 1.5)
    return np.linalg.norm(P - (a + np.clip(t, 0, 1)[:, None] * d), axis=1), t


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    v = mx
    s = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(mx - mn, 1e-4)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, s, v


def features(pkg, size):
    g = Glb(os.path.join(pkg, "body.glb"))
    p = g.prim("generated")
    j = g.j
    sk = j["skins"][0]
    names = [j["nodes"][i]["name"] for i in sk["joints"]]
    ibm = g.acc(sk["inverseBindMatrices"]).reshape(-1, 4, 4)
    jpos = {n: np.linalg.inv(ibm[k].T)[:3, 3] for k, n in enumerate(names)}
    P = p["POSITION"].astype(float)
    N = p["NORMAL"].astype(float)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    J, Wt = p["JOINTS_0"].astype(int), p["WEIGHTS_0"].astype(float)
    grp = np.zeros((len(P), len(GROUPS)))
    gid = np.array([group_of(n) for n in names])
    for k in range(J.shape[1]):
        np.add.at(grp, (np.arange(len(P)), gid[J[:, k]]), Wt[:, k])
    # along the arm: 0 at the shoulder, 1 at the elbow, 2 at the wrist (each side by x's sign)
    arm = np.zeros(len(P))
    legr = np.zeros(len(P))
    for side, sg in (("l", 1), ("r", -1)):
        s = np.sign(P[:, 0]) == sg
        du, tu = seg_dist(P[s], jpos[f"upperarm_{side}"], jpos[f"lowerarm_{side}"])
        dl, tl = seg_dist(P[s], jpos[f"lowerarm_{side}"], jpos[f"hand_{side}"])
        arm[s] = np.where(dl < du, 1 + tl, tu)
        legr[s] = seg_dist(P[s], jpos[f"calf_{side}"], jpos[f"foot_{side}"])[0]
    arm *= (grp[:, 1] + grp[:, 2]) > 0.3  # (only on the arms: the legs sit near the forearm's line too)
    curv = curvature(P, N, p["idx"])
    vals = np.c_[P, N, grp, arm, legr, p["TANGENT"], curv].astype(np.float32)
    F, have = raster_fields(p["TEXCOORD_0"].astype(float), p["idx"], vals, size)
    pb = p["mat"]["pbrMetallicRoughness"]
    alb = np.asarray(g.image(pb["baseColorTexture"]["index"]).resize((size, size), Image.BOX), np.float32) / 255
    mr = np.asarray(g.image(pb["metallicRoughnessTexture"]["index"]).resize((size, size), Image.BOX), np.float32) / 255
    wet = os.path.join(pkg, "wet_generated.png")  # (warden_wet_maps.py's occlusion, same UVs: run that first)
    occ = np.asarray(Image.open(wet).convert("RGBA").resize((size, size), Image.BILINEAR), np.float32)[..., 1] / 255 if os.path.exists(wet) else np.zeros((size, size), np.float32)
    return dict(occ=occ, P=F[..., 0:3], N=F[..., 3:6], grp=F[..., 6:12], arm=F[..., 12], legr=F[..., 13], T=F[..., 14:18], curv=F[..., 18], have=have,
                alb=alb, metal=mr[..., 2], jpos=jpos)


def classify(f):
    P, grp, alb, have = f["P"], f["grp"], f["alb"], f["have"]
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    sm = ndimage.uniform_filter(alb, (5, 5, 1))  # colour over ~10 atlas texels (quilting's grid lines average out)
    h, s, v = hsv(sm)
    v15 = ndimage.uniform_filter(v, 15)
    g = grp.argmax(-1)
    arm_part = (grp[..., 1] + grp[..., 2]) > 0.5
    lower = np.isin(g, (3, 4, 5))  # torso, thighs, shins
    cls = np.full(y.shape, WOOL, np.uint8)
    blue = (h > 198) & (h < 252) & (s > 0.12) & (v > 0.06)
    brown = ((h < 36) | (h > 340)) & (s > 0.24) & (v > 0.07)
    warm = ((h < 60) | (h > 330)) & (s > 0.07)
    # the tabard: its blue, closed over its darker wet streaks, and its pale trim where blue is all around
    tab = ndimage.binary_closing(blue & ~arm_part, np.ones((9, 9)), iterations=2) & have
    near_blue = ndimage.uniform_filter(blue.astype(np.float32), 25) > 0.35
    tab |= (s < 0.2) & (v > 0.18) & near_blue & ~arm_part & (y > 0.3) & (y < 1.5)
    # quilting: the sleeves (not the mantle's near-black on the shoulder) and the gambeson skirt above the mail
    cls[arm_part & warm & (v15 > 0.09)] = QUILT  # (the mantle's fur over the shoulder is cool grey: wool)
    under = lower & ~tab & (y < 0.98) & (y > 0.30)
    cls[under & (y >= 0.65)] = QUILT
    pale = (s < 0.2) & (v > 0.18)
    mail = under & (y < 0.65) & ~pale & ((z > -0.06) | ((s < 0.1) & (v < 0.18)))  # front and sides; neutral grey
    cls[mail] = IRON  # the mail hem
    tab |= under & (y < 0.65) & ~mail  # the tabard's pale hem trim and its dark wet hem
    cls[tab] = TABARD
    cls[brown | (under & (y > 0.8) & (h < 36) & (s > 0.16))] = LEATHER  # (+ the pouch's duller brown)
    # boots: on the shin, close to its bone line, and their soles
    cls[(g == 5) & (f["legr"] < 0.09) & (y < 0.47) & ~blue] = LEATHER
    cls[(g == 5) & (y < 0.06)] = LEATHER
    # gauntlets: the hand and the forearm's far part; buckles by the atlas's metal
    cls[((g == 2) | (f["arm"] > 1.55)) & ~brown] = IRON
    cls[f["metal"] > 0.3] = IRON
    # badge: pale on the tabard's left chest (not the armholes' pale trim)
    on_blue = ndimage.uniform_filter(blue.astype(np.float32), 41) > 0.3  # (the beard's charts aren't among the tabard's)
    cls[(v > 0.33) & (s < 0.3) & (y > 1.12) & (y < 1.45) & (z > 0.0) & (x > -0.01) & (x < 0.15) & on_blue] = BADGE
    # head: face and beard, the pale stuff in the hood's opening and down the chest
    # (the face sits deep in the hood: occluded; the hood's brim and crown are open. The beard hangs pale on the chest)
    head = (y > 1.50) & (y < 1.69) & (np.abs(x) < 0.11) & (z > 0.02) & (v > 0.12) & (f["occ"] > 0.45) & (g == 0)
    head |= (y > 1.1) & (y < 1.62) & (np.abs(x) < 0.12) & (z > 0.05) & (v > 0.2) & (s < 0.2) & ~on_blue & ~arm_part
    cls[head] = HEAD
    return cls, dict(h=h, s=s, v=v, contrast=v15, g=g)


def vnoise3(p, scale, seed):
    """Smooth value noise in 3D at a cell size (m), -1..1 (a 64^3 lattice, wrapped)."""
    g = np.random.default_rng(seed).uniform(-1, 1, (128, 128, 128)).astype(np.float32)
    q = p / scale
    i = np.floor(q).astype(np.int64)
    f = (q - i).astype(np.float32)
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * g[(i[:, 0] + dx) % 128, (i[:, 1] + dy) % 128, (i[:, 2] + dz) % 128]
    return out


def weave(a, b, period, twill):
    """A cloth weave's height on a plane (a across, b down, metres): threads over and under, 0..1."""
    s, t = a / period, b / period
    warp = np.abs(np.sin(np.pi * s))   # the vertical threads' round profile
    weft = np.abs(np.sin(np.pi * t))
    i, j = np.floor(s), np.floor(t)
    # plain: over-under alternates; 2/2 twill: two over, two under, shifted a thread per row (diagonal ribs)
    over = ((i + j) % 2) > 0.5 if not twill else ((i - j) % 4) < 2
    return np.where(over, warp, weft)


# per class: (weave period m or 0, twill, weave amp, fine noise (cell m, amp), broad noise (cell m, amp))
DETAIL = {WOOL: (0.0065, True, 1.0, (0.0016, 0.35), (0.03, 0.6)),
          TABARD: (0.005, False, 0.8, (0.0016, 0.25), (0.04, 0.5)),
          QUILT: (0.0085, False, 1.0, (0.003, 0.35), (0.05, 0.3)),   # coarse wet linen (+ quilt_cells(): the padding)
          LEATHER: (0.0, False, 0.0, (0.0022, 0.6), (0.015, 0.5)),
          IRON: (0.0, False, 0.0, (0.004, 0.25), (0.012, 0.6)),      # hammered dents
          BADGE: (0.005, False, 0.6, (0.0016, 0.2), (0.04, 0.3)),
          HEAD: (0.0, False, 0.0, (0.002, 0.0), (0.03, 0.0))}


# the gambeson's padding (Warden 6 r2: the sculpt's even square waffle read as a puffer sleeve): channels quilted down
# the body and along the arms, thread-thin stitch lines between, each channel's loft lumpy along it and its own, the
# padding flattened at the elbow's bend with creases across it
QUILT_W = 0.034                    # channel width (m), at the reference radius (a whole number of channels round)
# (Warden 7 judge: it still read as a puffer jacket: the loft halved, the channels' widths uneven, worn flat in
#  patches and pressed flat under the straps and the belt)
QUILT_PUFF, QUILT_STITCH, QUILT_BEND = 1.5, 0.45, 1.0


def quilt_cells(P, ax, ctr, rref, bend, press=None, shade=False):
    """The padding's height: P points; ax the channel's axis, ctr a point on it, rref the reference radius (per point);
    bend 0..1 (the elbow). Channels run along ax, spaced round it by angle (the seam where the angle wraps)."""
    up = np.where(np.abs(ax[:, 1:2]) < 0.9, [[0.0, 0.0, -1.0]], [[0.0, 0.0, -1.0]])
    up = up - ax * (up * ax).sum(1, keepdims=True)
    u = up / np.linalg.norm(up, axis=1, keepdims=True)    # (the seam behind: the back, the inner arm)
    v = np.cross(ax, u)
    d = P - ctr
    th = np.arctan2((d * v).sum(1), (d * u).sum(1))       # 0 at the back, +-pi in front
    n = np.round(2 * np.pi * rref / QUILT_W)
    c = (th + np.pi) / (2 * np.pi) * n                    # channel coordinate (whole channels round)
    along = (d * ax).sum(1)
    # uneven widths: the channel coordinate warped by a slow noise of itself (monotone: slope < 1), wandering along
    c = c + 0.38 * vnoise3(np.c_[c / 2.1, along / 0.35, rref * 7], 1.0, 52)
    ch = np.floor(c); fr = c - ch
    hsh = ((ch.astype(np.int64) * 2654435761 + (rref * 1000).astype(np.int64) * 97) % 1000) / 1000.0
    lump = 0.75 + 0.35 * vnoise3(np.c_[along / 0.045, ch * 1.7, hsh * 9], 1.0, 43)
    loft = np.sin(np.pi * np.clip(fr, 0, 1)) ** 0.7 * (0.8 + 0.4 * hsh) * lump
    # worn flat in patches (the padding compacted where it rubs), and pressed under the straps and belt
    worn = np.clip((vnoise3(P, 0.08, 53) + 0.45 * vnoise3(P, 0.03, 54) - 0.1) / 0.5, 0, 1)
    loft = loft * (1 - 0.75 * worn)
    if press is not None:
        loft = loft * (1 - 0.85 * press)
    stitch = 1 - np.clip(np.minimum(fr, 1 - fr) * QUILT_W / 0.0012, 0, 1)
    crease = np.sin(along / 0.011 + 3 * vnoise3(P, 0.03, 41)) * bend
    if shade:  # the padding's loft for the shader's groove shade: 0 down in the stitch line, 1 on the loft's top
        return np.clip(loft * (1 - 0.6 * bend) / 1.1, 0, 1) * (1 - stitch)
    return QUILT_PUFF * loft * (1 - 0.7 * bend) - QUILT_STITCH * stitch + QUILT_BEND * crease


def height(P, N, c, q=None):
    """Each point's detail height for its class (bind pose, metres in, unitless out); the weave is triplanar on the
    world planes (in the bind pose his cloth hangs along y, so the warp follows gravity)."""
    h = np.zeros(len(P), np.float32)
    w = np.abs(N) ** 4
    w /= w.sum(1, keepdims=True)
    for k, (per, tw, amp, fine, broad) in DETAIL.items():
        m = c == k
        if not m.any():
            continue
        p, ww = P[m], w[m]
        v = np.zeros(m.sum(), np.float32)
        if per:
            v += amp * (ww[:, 0] * weave(p[:, 2], p[:, 1], per, tw) + ww[:, 1] * weave(p[:, 0], p[:, 2], per, tw)
                        + ww[:, 2] * weave(p[:, 0], p[:, 1], per, tw))
        v += fine[1] * vnoise3(p, fine[0], 11)
        v += broad[1] * vnoise3(p, broad[0], 12) + 0.5 * broad[1] * vnoise3(p, broad[0] * 0.43, 13)
        if k == QUILT and q is not None:
            v += quilt_cells(p, q[0][m], q[1][m], q[2][m], q[3][m], q[4][m])
        h[m] = v
    return h


def detail(f, cls, eps=0.0004):
    """The detail normal (tangent-space x, y in -1..1) per covered texel: the class's 3D height's slope along the
    texel's tangent and bitangent (glTF: B = cross(N, T) * w), the same frame the shader's NORMAL_MAP uses."""
    have = f["have"]
    P, N, T = f["P"][have].astype(np.float64), f["N"][have], f["T"][have]
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    t = T[:, :3] - N * (T[:, :3] * N).sum(1, keepdims=True)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    b = np.cross(N, t) * np.where(T[:, 3:4] < 0, -1, 1)
    c = cls[have]
    # the quilting's channels: down the body round its centre line, or along the arm's bone round it
    arm = f["arm"][have]; jp = f["jpos"]
    pel = jp.get("pelvis", jp.get("Pelvis", np.zeros(3)))
    ax = np.tile([0.0, 1.0, 0.0], (len(P), 1)); ctr = np.tile([0.0, 0.0, pel[2]], (len(P), 1))
    rref = np.full(len(P), 0.2)
    for side, sg in (("l", 1), ("r", -1)):
        s = (np.sign(P[:, 0]) == sg) & (arm > 0)
        for a0, a1, sel in (("upperarm", "lowerarm", arm <= 1), ("lowerarm", "hand", arm > 1)):
            d = jp[f"{a1}_{side}"] - jp[f"{a0}_{side}"]
            ax[s & sel] = d / np.linalg.norm(d); ctr[s & sel] = jp[f"{a0}_{side}"]; rref[s & sel] = 0.06
    bend = np.clip(1 - np.abs(arm - 1.0) / 0.22, 0, 1) * (arm > 0)
    # the straps' and belt's press on the padding: near any leather in 3D
    lp = f["P"][have][c == LEATHER]
    press = np.zeros(len(P))
    if len(lp):
        dd, _ = cKDTree(lp[::3]).query(P[c == QUILT], distance_upper_bound=0.08)
        press[c == QUILT] = np.clip((0.05 - np.minimum(dd, 0.08)) / 0.035, 0, 1)
    q = (ax, ctr, rref, bend, press)
    out = np.zeros(have.shape + (2,), np.float32)
    dx = (height(P + eps * t, N, c, q) - height(P - eps * t, N, c, q)) / (2 * eps)
    dy = (height(P + eps * b, N, c, q) - height(P - eps * b, N, c, q)) / (2 * eps)
    # (slopes of a unit-amplitude pattern over ~mm are ~1000/m: brought to ~0.5 at the weave; the shader's per-class
    #  strength sets how much shows)
    k = 0.0009
    out[have] = np.clip(np.c_[-dx * k, -dy * k], -1, 1)
    puff = np.zeros(have.shape, np.float32)  # the low bits: 0..1, read on the quilting only (other classes: a free noise)
    pv = np.clip(0.5 + 0.5 * vnoise3(P, 0.035, 21) + 0.25 * vnoise3(P, 0.012, 22), 0, 1)
    m = c == QUILT  # (Warden 6 r3: on the quilting, the padding's loft: the shader shades its stitch grooves)
    if m.any():
        pv[m] = quilt_cells(P[m], ax[m], ctr[m], rref[m], bend[m], press[m], shade=True)
    # (Warden 7) the tabard: a broad fade (sun and river, uneven: 1 most faded); the iron: its convexity (0.5 flat,
    #  1 a worn convex edge, 0 a recess), from the mesh's curvature over the iron's own spread
    m = c == TABARD
    if m.any():
        fd = 0.5 + 0.45 * vnoise3(P[m], 0.16, 61) + 0.3 * vnoise3(P[m], 0.055, 62) + 0.12 * vnoise3(P[m], 0.018, 63)
        pv[m] = np.clip(fd, 0, 1)
    m = c == IRON
    if m.any():
        cv = f["curv"][have][m]
        sc = max(np.percentile(np.abs(cv), 90), 1e-6)
        pv[m] = np.clip(0.5 + 0.5 * cv / sc, 0, 1)
    puff[have] = pv
    return out, puff


def majority(cls, have, k=7):
    """Each covered texel takes its k x k neighbourhood's most common class (covered texels only)."""
    votes = np.stack([ndimage.uniform_filter(((cls == c) & have).astype(np.float32), k) for c in range(len(NAMES))], -1)
    out = votes.argmax(-1).astype(np.uint8)
    return np.where(have, out, cls)


def fill3d(cls, f, cell=0.05, frac=0.5):
    """Warden 6 r3: the quilting's pale cells (cooler, paler paint) fell to wool in UV-space rules and drew as pale blue
    blotches on the gambeson. Any wool texel whose 3D neighbourhood (cell m, trilinear-blurred voxels) is mostly
    quilting becomes quilting."""
    have = f["have"]; P = f["P"][have]; c = cls[have]
    lo = P.min(0) - cell; idx = (P - lo) / cell
    i0 = np.floor(idx).astype(int); fr = idx - i0
    shape = tuple(i0.max(0) + 3)
    q = np.zeros(shape); n = np.zeros(shape)
    corners = [(dx, dy, dz) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
    ws = []
    for dx, dy, dz in corners:
        w = (fr[:, 0] if dx else 1 - fr[:, 0]) * (fr[:, 1] if dy else 1 - fr[:, 1]) * (fr[:, 2] if dz else 1 - fr[:, 2])
        ws.append(w)
        np.add.at(q, (i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz), w * (c == QUILT))
        np.add.at(n, (i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz), w * ((c == QUILT) | (c == WOOL)))
    q = ndimage.uniform_filter(q, 3); n = ndimage.uniform_filter(n, 3)
    r = q / np.maximum(n, 1e-6)
    v = sum(w * r[i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz] for w, (dx, dy, dz) in zip(ws, corners))
    flip = (c == WOOL) & (v > frac)
    c[flip] = QUILT
    out = cls.copy(); out[have] = c
    print(f"fill3d: {flip.sum()} wool texels to quilting ({flip.sum() / max((c == QUILT).sum(), 1):.1%} of the quilting)")
    return out


def body_extras(pkg, f, cls, size):
    """Warden 7: the body's wet_generated.png B and A (zero from warden_wet_maps.py: they were the old TRELLIS head's
    beard and face), per texel at this map's size, R and G kept (resampled):
      B  the beard's drip: where his beard's tips (beard.glb, same bind) touch the tabard, and the run below them
      A  wet streaks: thin vertical runs (3D noise stretched along y, 0.5 = none), the iron's and the cloth's"""
    have = f["have"]; P = f["P"][have]
    B = np.zeros(len(P), np.float32)
    bg = os.path.join(pkg, "beard.glb")
    if os.path.exists(bg):
        g = Glb(bg)
        bp = g.acc(g.j["meshes"][0]["primitives"][0]["attributes"]["POSITION"]).astype(float)
        tips = bp[bp[:, 1] < bp[:, 1].min() + 0.1]
        dd, k = cKDTree(tips).query(P, distance_upper_bound=0.3)
        near = np.clip((0.06 - np.minimum(dd, 0.3)) / 0.04, 0, 1)
        # the run below: under the tips' footprint (x, z near), down 0.16 m, ragged
        lo = tips[:, 1].min()
        dxz, _ = cKDTree(tips[:, [0, 2]]).query(P[:, [0, 2]], distance_upper_bound=0.3)
        under = np.clip((0.05 - np.minimum(dxz, 0.3)) / 0.03, 0, 1) * np.clip(1 - (lo - P[:, 1]) / 0.16, 0, 1) * (P[:, 1] < lo + 0.02)
        under *= np.clip(0.6 + 0.8 * vnoise3(np.c_[P[:, 0] / 0.012, P[:, 1] / 0.2, P[:, 2] / 0.012], 1.0, 72), 0, 1)
        B = np.clip(np.maximum(near, under), 0, 1).astype(np.float32)
    A = np.clip(0.5 + 0.9 * vnoise3(np.c_[P[:, 0] / 0.007, P[:, 1] / 0.14, P[:, 2] / 0.007], 1.0, 71)
                + 0.3 * vnoise3(P, 0.05, 73), 0, 1).astype(np.float32)
    ext = np.zeros(have.shape + (2,), np.float32); ext[have] = np.c_[B, A]
    ext = dilate(ext, have)
    wp = os.path.join(pkg, "wet_generated.png")
    w = Image.open(wp).convert("RGBA")
    rg = np.asarray(w.resize((size, size), Image.BILINEAR) if w.size != (size, size) else w, np.uint8)[..., :2]
    out = np.zeros((size, size, 4), np.uint8); out[..., :2] = rg
    out[..., 2:4] = np.clip(np.round(ext * 255), 0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(wp)
    print(f"wet_generated.png: B beard drip {(B > 0.5).mean():.4f} of texels, A streaks mean {A.mean():.2f} ({size})")


def dilate(cls, have):
    _, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
    return cls[iy, ix]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg", nargs="?", default=os.path.join(os.path.dirname(__file__), "..", "..", "godot", "art", "npc", "ford_warden"))
    ap.add_argument("--size", type=int, default=2048)
    ap.add_argument("--debug", default="")
    a = ap.parse_args()
    f = features(a.pkg, a.size)
    cls, dbg = classify(f)
    cls = majority(cls, f["have"])
    cls = fill3d(cls, f)
    cls = dilate(cls, f["have"])
    out = np.zeros((a.size, a.size, 4), np.uint8)
    d, puff = detail(f, cls)
    d = dilate(d, f["have"])
    puff = dilate(puff, f["have"])
    hgt = dilate(f["P"][..., 1], f["have"])
    out[..., 0] = cls * 32 + np.round(puff * 31).astype(np.uint8)
    out[..., 1] = np.clip(np.round(hgt / 2.0 * 255), 0, 255).astype(np.uint8)
    out[..., 2:4] = np.clip(np.round((d * 0.5 + 0.5) * 255), 0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(os.path.join(a.pkg, "id_generated.png"))
    body_extras(a.pkg, f, cls, a.size)
    cov = f["have"]
    print("id_generated.png:", ", ".join(f"{n} {((cls == i) & cov).sum() / cov.sum():.3f}" for i, n in enumerate(NAMES)))
    if a.debug:
        os.makedirs(a.debug, exist_ok=True)
        Image.fromarray(DEBUG_RGB[cls]).save(os.path.join(a.debug, "id_debug.png"))
        np.savez_compressed(os.path.join(a.debug, "feat.npz"), h=dbg["h"], s=dbg["s"], v=dbg["v"], c=dbg["contrast"], g=dbg["g"], have=cov,
                            y=f["P"][..., 1], arm=f["arm"], legr=f["legr"])


if __name__ == "__main__":
    main()
