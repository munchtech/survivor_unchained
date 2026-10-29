"""The Ford-Warden's material ID map (shaders/warden_wet.gdshader), in his body surface's own UVs.

His Meshy body is one 4096 atlas of tiny charts with one material, so the shader can't tell wool from leather from
iron. This map says, per texel, what each bit of him is made of. It is made from the bind pose and the atlas:
  * 3D place and skin weights, rasterised into UV space: which part of him a texel is on (head, arm, hand, torso,
    leg) and where (height, front/back, distance from the leg's bone line, along the arm);
  * the atlas colour at that texel (hue, saturation, value) and its local contrast (the quilting's grid);
  * the atlas's metal channel (buckles).
Rules (classify()), then a majority filter per chart so specks don't flip class, then dilated gutters.

Channels (2048, RGBA8; imported lossless, alpha untouched):
  R  class * 32 + puff (0..31): the class index (the shader texelFetches it and blends the 4 neighbours' params);
     the low bits vary the quilting's atlas normal per cell (x 0.4-1.6) so its grid isn't one perfect emboss
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
Writes PKG_DIR/id_generated.png (+ a class-colour picture in --debug OUT_DIR).
Re-run after any change to body.glb's geometry or UVs (it reads only body.glb's "generated" surface).
"""
import argparse, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

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
    vals = np.c_[P, N, grp, arm, legr, p["TANGENT"]].astype(np.float32)
    F, have = raster_fields(p["TEXCOORD_0"].astype(float), p["idx"], vals, size)
    pb = p["mat"]["pbrMetallicRoughness"]
    alb = np.asarray(g.image(pb["baseColorTexture"]["index"]).resize((size, size), Image.BOX), np.float32) / 255
    mr = np.asarray(g.image(pb["metallicRoughnessTexture"]["index"]).resize((size, size), Image.BOX), np.float32) / 255
    wet = os.path.join(pkg, "wet_generated.png")  # (warden_wet_maps.py's occlusion, same UVs: run that first)
    occ = np.asarray(Image.open(wet).convert("RGBA").resize((size, size), Image.BILINEAR), np.float32)[..., 1] / 255 if os.path.exists(wet) else np.zeros((size, size), np.float32)
    return dict(occ=occ, P=F[..., 0:3], N=F[..., 3:6], grp=F[..., 6:12], arm=F[..., 12], legr=F[..., 13], T=F[..., 14:18], have=have,
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
          QUILT: (0.005, False, 0.5, (0.0016, 0.2), (0.022, 1.6)),   # (the broad noise is the puffs' sag and creasing)
          LEATHER: (0.0, False, 0.0, (0.0022, 0.6), (0.015, 0.5)),
          IRON: (0.0, False, 0.0, (0.004, 0.25), (0.012, 0.6)),      # hammered dents
          BADGE: (0.005, False, 0.6, (0.0016, 0.2), (0.04, 0.3)),
          HEAD: (0.0, False, 0.0, (0.002, 0.0), (0.03, 0.0))}


def height(P, N, c):
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
    out = np.zeros(have.shape + (2,), np.float32)
    dx = (height(P + eps * t, N, c) - height(P - eps * t, N, c)) / (2 * eps)
    dy = (height(P + eps * b, N, c) - height(P - eps * b, N, c)) / (2 * eps)
    # (slopes of a unit-amplitude pattern over ~mm are ~1000/m: brought to ~0.5 at the weave; the shader's per-class
    #  strength sets how much shows)
    k = 0.0009
    out[have] = np.clip(np.c_[-dx * k, -dy * k], -1, 1)
    puff = np.zeros(have.shape, np.float32)  # the quilting's puffs, each cell its own height (the atlas normal x 0.4-1.6)
    puff[have] = np.clip(0.5 + 0.5 * vnoise3(P, 0.035, 21) + 0.25 * vnoise3(P, 0.012, 22), 0, 1)
    return out, puff


def majority(cls, have, k=7):
    """Each covered texel takes its k x k neighbourhood's most common class (covered texels only)."""
    votes = np.stack([ndimage.uniform_filter(((cls == c) & have).astype(np.float32), k) for c in range(len(NAMES))], -1)
    out = votes.argmax(-1).astype(np.uint8)
    return np.where(have, out, cls)


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
    cov = f["have"]
    print("id_generated.png:", ", ".join(f"{n} {((cls == i) & cov).sum() / cov.sum():.3f}" for i, n in enumerate(NAMES)))
    if a.debug:
        os.makedirs(a.debug, exist_ok=True)
        Image.fromarray(DEBUG_RGB[cls]).save(os.path.join(a.debug, "id_debug.png"))
        np.savez_compressed(os.path.join(a.debug, "feat.npz"), h=dbg["h"], s=dbg["s"], v=dbg["v"], c=dbg["contrast"], g=dbg["g"], have=cov,
                            y=f["P"][..., 1], arm=f["arm"], legr=f["legr"])


if __name__ == "__main__":
    main()
