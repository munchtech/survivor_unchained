"""Our own stone-slate roof material for the crypt (Pieces.cs RoofSlates()).

A tileable 1024 px set for a 3 m tile (the material keeps Uv1Scale 1/3):
albedo.jpg, normal.jpg (OpenGL / Godot, green = up) and arm.jpg
(R = AO, G = roughness, B = metal) into godot/art/materials/roof_slate/.

Image x runs along the ridge (the roof's U), image y runs down the slope
(the roof's V, toward the eaves), so the courses are rows of the image.
Each course sits under the butt of the course above it: the height rises
down a course to its butt, then steps down onto the next course.

The CC0 Poly Haven photo roof_slates_02 is raw material only: its
luminance, high-passed (sigma 8 px), its own gap lines masked out, sampled
at a random offset and flip per slate, adds surface grain recoloured by our
per-slate tones. No photo structure larger than the grain survives.

    python tools/assets/env_roof_slate.py [--photo PATH] [--seed N]
"""
import argparse
import os

import numpy as np
from PIL import Image

N = 1024                     # px per tile
TILE_M = 3.0                 # metres per tile
PPM = N / TILE_M             # px per metre
COURSES = 13                 # 1024 / 13 = 78.8 px = 0.231 m exposed course
BUMP = 8.0  # height units to px
GRAIN_BUMP = 0.25
TARGET_LUMA = 0.50         # mean Rec.709 luma (sRGB values); the old albedo was 0.5286, but our cool slate under the blue moon reads ~15% brighter in game

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "godot", "art", "materials", "roof_slate")
PHOTO = r"C:\Users\munch\Desktop\survivorsunchained_inputs\raw_materials\roof_slates_02\albedo.jpg"

KY = np.fft.fftfreq(N)[:, None]
KX = np.fft.fftfreq(N)[None, :]


def blur(a, sx, sy=None):
    """Gaussian blur with wrap (FFT), sigma in px per axis."""
    sy = sx if sy is None else sy
    g = np.exp(-2 * np.pi ** 2 * ((KX * sx) ** 2 + (KY * sy) ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g))


def noise(rng, sx, sy=None):
    n = blur(rng.standard_normal((N, N)), sx, sy)
    return n / (n.std() + 1e-9)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def layout(rng):
    """Course bands (rows) and per-course slate edges (columns), all wrapping."""
    h = rng.uniform(0.20, 0.26, COURSES) * PPM
    h = h * N / h.sum()
    tops = np.concatenate([[0], np.cumsum(h)])
    courses = []
    prev = None
    first = None
    for c in range(COURSES):
        best = None
        for _ in range(200):
            w = []
            while sum(w) < N:
                w.append(rng.uniform(0.18, 0.36) * PPM)
            w = np.array(w) * N / sum(w)          # exact wrap
            if w.min() < 0.17 * PPM or w.max() > 0.37 * PPM:
                continue
            off = rng.uniform(0, N)
            edges = (off + np.concatenate([[0], np.cumsum(w)[:-1]])) % N
            # Staggered: every joint well away from the joints of the course above
            # (and, for the last course, of the first one, across the wrap).
            score = 1e9
            for other in (prev, first if c == COURSES - 1 else None):
                if other is None:
                    continue
                d = np.abs(edges[:, None] - other[None, :])
                d = np.minimum(d, N - d)
                score = min(score, d.min())
            if best is None or score > best[0]:
                best = (score, off, w, edges)
            if score > 0.3 * w.mean():
                break
        _, off, w, edges = best
        courses.append((off, w))
        prev = edges
        if c == 0:
            first = edges
    return tops, courses


def photo_grain(rng, path):
    """High-passed photo luminance, gap lines masked out, normalised to std 1."""
    p = np.asarray(Image.open(path).convert("L").resize((N, N), Image.LANCZOS)).astype(np.float64) / 255
    hp = p - blur(p, 8)
    s = hp.std()
    gap = blur((hp < -1.6 * s).astype(float), 2) > 0.08   # the photo's own dark joints, dilated
    alt = np.roll(hp, (391, 613), (0, 1))
    altgap = np.roll(gap, (391, 613), (0, 1))
    hp = np.where(gap, np.where(altgap, 0.0, alt), hp)
    hp = np.tanh(hp / (1.5 * s)) * 1.5                  # no strong photo line survives
    return hp / hp.std()


def build(seed, photo):
    rng = np.random.default_rng(seed)
    tops, courses = layout(rng)
    grain_src = photo_grain(rng, photo)

    yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)
    course = np.clip(np.searchsorted(tops, yy[:, 0], side="right") - 1, 0, COURSES - 1)
    C = np.repeat(course[:, None], N, 1)
    top = tops[C]
    hc = (tops[1:] - tops[:-1])[C]
    t = yy - top                      # px down from the course's top (under the butt above)
    slate_id = np.zeros((N, N), int)
    dl = np.zeros((N, N))             # px from the slate's left edge
    wd = np.zeros((N, N))             # slate width
    base_id = 0
    ids_per_course = []
    for c, (off, w) in enumerate(courses):
        rows = course == c
        xs = (xx[rows] - off) % N
        cum = np.concatenate([[0], np.cumsum(w)])
        k = np.clip(np.searchsorted(cum, xs, side="right") - 1, 0, len(w) - 1)
        slate_id[rows] = base_id + k
        dl[rows] = xs - cum[k]
        wd[rows] = w[k]
        ids_per_course.append((base_id, len(w)))
        base_id += len(w)
    ns = base_id
    dr = wd - dl
    s = dl / wd

    # Per-slate draws.
    r = lambda lo, hi: rng.uniform(lo, hi, ns)
    butt_lift = r(0.0, 3.5)[slate_id]                 # px the butt sits short of the band's end
    butt_skew = r(-2.5, 2.5)[slate_id]                # px across the width
    corner_r = r(4, 13)[slate_id]
    tilt = r(0.85, 1.25)[slate_id]                    # height rise down the slate
    twist = r(-0.25, 0.25)[slate_id]                  # height across the slate
    lift = r(-0.12, 0.12)[slate_id]
    joint = r(1.2, 2.4)                               # half gap per left edge
    jl = joint[slate_id]
    # the right edge's gap is the next slate's left half-gap
    nxt = slate_id.copy()
    for c, (b, n) in enumerate(ids_per_course):
        m = (slate_id >= b) & (slate_id < b + n)
        nxt[m] = b + (slate_id[m] - b + 1) % n
    jr = joint[nxt]

    dy = hc - butt_lift - butt_skew * (s - 0.5) - t   # px above this slate's butt
    under = (dy < 0) | (dl < jl) | (dr < jr)
    # Rounded lower corners.
    for d in (dl, dr):
        cx = corner_r - d
        cy = corner_r - dy
        under |= (cx > 0) & (cy > 0) & (cx ** 2 + cy ** 2 > corner_r ** 2)
    # Chips bitten out of the butts.
    nchips = rng.integers(0, 3, ns)
    chip = np.zeros((N, N), bool)
    for c, (b, n) in enumerate(ids_per_course):
        rows = np.where(course == c)[0]
        for k in range(n):
            sid = b + k
            for _ in range(nchips[sid]):
                cs = rng.uniform(0.15, 0.85)
                rad = rng.uniform(2.5, 7)
                m = slate_id[rows] == sid
                ddx = (s[rows] - cs) * wd[rows]
                ddy = dy[rows]
                hit = m & (ddx ** 2 + (ddy * 1.4) ** 2 < rad ** 2)
                chip[rows] |= hit
    under |= chip

    # ---- height (arbitrary units; scaled to the old map's slope later)
    tn = np.clip(t / hc, 0, 1)
    surf = tilt * tn + twist * (s - 0.5) + lift
    surf += 0.05 * noise(rng, 14) + 0.02 * noise(rng, 3)
    # soft bevel on the butt and the side edges
    bev = smooth(0, 3.5, dy) * smooth(0, 2.5, np.minimum(dl - jl, dr - jr))
    surf = surf * (0.75 + 0.25 * bev) - 0.15 * (1 - bev)
    gap_h = -0.35 + 0.15 * tn
    height = np.where(under, gap_h, surf)

    # ---- albedo
    ttone = r(0, 1)                                   # 0 blue-grey .. 1 grey-green
    blue = np.array([0.525, 0.512, 0.492])
    green = np.array([0.515, 0.515, 0.480])
    col = blue[None] * (1 - ttone[:, None]) + green[None] * ttone[:, None]
    neutral = rng.random(ns) < 0.25
    col[neutral] = np.array([0.525, 0.515, 0.505])
    rust = rng.random(ns) < 0.05
    col[rust] = np.array([0.565, 0.50, 0.435])
    col *= rng.uniform(0.90, 1.10, ns)[:, None]
    col += rng.uniform(-0.008, 0.008, (ns, 3))
    alb = col[slate_id]

    # grain: the photo, sampled at a random offset and flip per slate
    oy = rng.integers(0, N, ns)
    ox = rng.integers(0, N, ns)
    fl = rng.random(ns) < 0.5
    gx = np.where(fl[slate_id], -xx, xx) + ox[slate_id]
    gy = yy + oy[slate_id]
    grain = grain_src[gy.astype(int) % N, gx.astype(int) % N]
    own = 0.6 * noise(rng, 22) + 0.4 * noise(rng, 6, 9)
    streak = noise(rng, 2.5, 34)                      # rain runs down the slope
    shade = 1 + 0.045 * grain + 0.05 * own - 0.03 * np.clip(streak, 0, None)
    shade *= 1 - 0.14 * np.exp(-t / 9.0) * ~under    # grime and shade under the butt above
    shade *= 1 + 0.05 * (1 - smooth(0, 4, dy))       # a paler worn butt edge
    alb = alb * shade[..., None]
    alb = np.where(under[..., None], alb * 0.32, alb)
    lum0 = (alb @ [0.2126, 0.7152, 0.0722])[..., None]
    alb = lum0 + 0.87 * (alb - lum0)                 # pull toward neutral: chroma <= 0.033
    # match the old mean luma
    for _ in range(6):
        l = (np.clip(alb, 0, 1) @ [0.2126, 0.7152, 0.0722]).mean()
        alb *= TARGET_LUMA / l
    alb = np.clip(alb, 0, 1)

    # ---- normal (OpenGL: green = up = toward the ridge, i.e. image row decreasing)
    # Height in px: the slates' shape plus the grain as a fine relief.
    hpx = BUMP * height + GRAIN_BUMP * (0.7 * grain + 0.3 * noise(rng, 1.2)) * ~under
    def d(a, ax):
        return (np.roll(a, -1, ax) - np.roll(a, 1, ax)) / 2
    sob = lambda a, ax, other: (2 * d(a, ax) + d(np.roll(a, 1, other), ax) + d(np.roll(a, -1, other), ax)) / 4
    hpx = blur(hpx, 0.8)
    dhx, dhy = sob(hpx, 1, 0), sob(hpx, 0, 1)
    nrm = np.stack([-dhx, dhy, np.ones_like(dhx)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)

    # ---- AO and roughness
    cav = np.clip(blur(height, 6) - height, 0, None)
    ao = r(0.66, 0.90)[slate_id] - 0.9 * cav - 0.3 * np.exp(-t / 12.0)
    ao = np.where(under, ao * 0.55, ao)
    ao = np.clip(ao, 0.2, 1)
    rough_s = rng.uniform(0.33, 0.50, ns)
    rough_s[rng.random(ns) < 0.1] = rng.uniform(0.5, 0.6)
    rough = rough_s[slate_id] + 0.02 * own - 0.07 * smooth(0.3, 1.5, streak)
    rough = np.where(under, 0.3, rough)
    rough = np.clip(rough, 0.25, 0.62)
    arm = np.stack([ao, rough, np.zeros_like(ao)], -1)
    return alb, nrm, arm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", default=PHOTO)
    ap.add_argument("--seed", type=int, default=2026_10_19)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    alb, nrm, arm = build(a.seed, a.photo)
    os.makedirs(a.out, exist_ok=True)
    to8 = lambda x: Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))
    to8(alb).save(os.path.join(a.out, "albedo.jpg"), quality=93)
    to8(nrm * 0.5 + 0.5).save(os.path.join(a.out, "normal.jpg"), quality=95)
    to8(arm).save(os.path.join(a.out, "arm.jpg"), quality=93)
    l = (alb @ [0.2126, 0.7152, 0.0722]).mean()
    print(f"albedo luma {l:.4f} (target {TARGET_LUMA}), rough mean {arm[..., 1].mean():.3f}, ao mean {arm[..., 0].mean():.3f}")
    print(f"normal xy std {(nrm[..., 0] * .5).std():.3f} {(nrm[..., 1] * .5).std():.3f} (old 0.069 0.109); median |xy| {np.median(np.abs(nrm[..., 0])):.3f} {np.median(np.abs(nrm[..., 1])):.3f}")


if __name__ == "__main__":
    main()
