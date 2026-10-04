"""The forge: the interface's metalwork, built from height and lit by one light.

Every frame, plate, slot, medallion, ring, keycap and cursor of Survivor
Unchained's interface is made here the same way: a height field (bevels,
grooves, bosses, filigree, hammer dents), a material per pixel (blackened
iron, gold, bronze, pewter, bone, leather, parchment; ember where there is
power), and one light baked into material spheres (matcaps/, rendered by
matcaps_blender.py: a warm key from the upper left, a dim sky, a cool rim
from the lower right). So every piece is lit identically, is exactly
symmetrical where it should be, and has its nine-slice margins exactly where
docs/UI_ART_BRIEF.md puts them.

Coordinates: x right, y down (image), heights in pixels of the working
canvas. Everything is float32 numpy; colours are linear until `finish`.
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_CAPS = None


def caps():
    global _CAPS
    if _CAPS is None:
        z = np.load(os.path.join(HERE, "matcaps", "matcaps.npz"))
        _CAPS = {k: z[k].astype(np.float32) for k in z.files}
    return _CAPS


# ----------------------------------------------------------------- colour --

def srgb_to_lin(c):
    c = np.asarray(c, dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def hexc(h, lin=True):
    """'#d9b56a' as an RGB triple (linear by default)."""
    h = h.lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)
    return srgb_to_lin(c) if lin else c


# ------------------------------------------------------------------ noise --

def fbm(h, w, scale=32.0, octaves=5, gain=0.55, seed=0, periodic=True):
    """Fractal noise in [-1, 1]-ish, periodic on the canvas (made in frequency space)."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    out = np.zeros((h, w), np.float32)
    amp, sc = 1.0, scale
    for _ in range(octaves):
        spec = (rng.standard_normal((h, w)) + 1j * rng.standard_normal((h, w)))
        band = np.exp(-((f * sc) ** 2) * 2.0) * (1 - np.exp(-((f * sc * 2.0) ** 2) * 2.0))
        n = np.real(np.fft.ifft2(spec * band)).astype(np.float32)
        n /= (n.std() + 1e-6)
        out += n * amp
        amp *= gain
        sc /= 2.0
    out /= (np.abs(out).max() + 1e-6)
    return out


def worley_dents(h, w, cell=24.0, depth=1.0, seed=0, jitter=1.0, shape=2.0):
    """Hammer dents: shallow round dimples at random points, periodic on the canvas."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    n = max(4, int(h * w / (cell * cell)))
    pts = rng.random((n, 2)) * [w, h]
    tree = cKDTree(pts, boxsize=[w, h])
    yy, xx = np.mgrid[0:h, 0:w]
    q = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1) % [w, h]
    d, i = tree.query(q, k=2)
    d1 = d[:, 0].reshape(h, w)
    d2 = d[:, 1].reshape(h, w)
    # Each dent a bowl reaching to the edge between neighbours (F2-F1 cells),
    # with random depth per dent.
    dep = (0.5 + rng.random(n) * jitter)[i[:, 0]].reshape(h, w)
    edge = (d2 - d1)
    r = np.clip(d1 / (d1 + edge * 0.5 + 1e-6), 0, 1)
    bowl = -(1 - r ** shape) * dep
    return (bowl * depth).astype(np.float32)


def facets(h, w, cell=24.0, tilt=0.35, seed=0, soften=1.0, elong=1.0):
    """Planished iron: flat hammer facets, each cell a little plane at its own tilt
    (periodic on the canvas). Returns height in px (tilt is the slope)."""
    from scipy.spatial import cKDTree
    rng = np.random.default_rng(seed)
    n = max(4, int(h * w / (cell * cell)))
    pts = rng.random((n, 2)) * [w, h]
    tree = cKDTree(pts * [1.0, elong], boxsize=[w, h * elong])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    q = np.stack([(xx.ravel() + 0.5) % w, ((yy.ravel() + 0.5) % h) * elong], 1)
    _, idx = tree.query(q, k=1)
    idx = idx.reshape(h, w)
    sx = rng.normal(0, tilt, n).astype(np.float32)
    sy = rng.normal(0, tilt, n).astype(np.float32)
    off = rng.normal(0, tilt * cell * 0.15, n).astype(np.float32)
    px, py = pts[idx, 0], pts[idx, 1]
    dx = (xx + 0.5 - px + w / 2) % w - w / 2
    dy = (yy + 0.5 - py + h / 2) % h - h / 2
    hgt = sx[idx] * dx + sy[idx] * dy + off[idx]
    if soften > 0:
        hgt = blur_wrap(hgt.astype(np.float32), soften)
    return hgt.astype(np.float32)


def kuwahara(img, r=2):
    """A painter's filter: each pixel takes the mean of its calmest quadrant (brush strokes)."""
    img = img.astype(np.float32)
    k = r + 1
    lum = img[..., :3].mean(axis=2) if img.ndim == 3 else img
    def box(a):
        return cv2.blur(a, (k, k), borderType=cv2.BORDER_REFLECT)
    m = box(img)
    lm = box(lum)
    lv = box(lum * lum) - lm * lm
    best = None
    bestv = None
    for ox, oy in ((-r // 2 - 0, -r // 2 - 0), (r // 2, -r // 2), (-r // 2, r // 2), (r // 2, r // 2)):
        M = np.roll(m, (oy, ox), axis=(0, 1))
        Vv = np.roll(lv, (oy, ox), axis=(0, 1))
        if best is None:
            best, bestv = M, Vv
        else:
            pick = Vv < bestv
            best = np.where(pick[..., None] if img.ndim == 3 else pick, M, best)
            bestv = np.where(pick, Vv, bestv)
    return best


def scratches(h, w, count=40, length=(10, 60), depth=0.6, width=1.0, seed=0, angle=None):
    rng = np.random.default_rng(seed)
    m = np.zeros((h, w), np.float32)
    for _ in range(count):
        x, y = rng.random() * w, rng.random() * h
        a = rng.random() * math.pi if angle is None else angle + rng.normal() * 0.25
        L = rng.uniform(*length)
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        # Wrap so the canvas stays periodic.
        for ox in (-w, 0, w):
            for oy in (-h, 0, h):
                cv2.line(m, (int(x - dx + ox), int(y - dy + oy)), (int(x + dx + ox), int(y + dy + oy)),
                         float(rng.uniform(0.4, 1.0)), max(1, int(width)), cv2.LINE_AA)
    return -m * depth


def blur(a, sigma):
    if sigma <= 0:
        return a
    k = int(sigma * 3) * 2 + 1
    return cv2.GaussianBlur(a, (k, k), sigma, borderType=cv2.BORDER_REFLECT)


def blur_wrap(a, sigma):
    """A blur on a periodic canvas (wraps at the edges)."""
    if sigma <= 0:
        return a
    p = int(sigma * 3) + 1
    big = np.pad(a, [(p, p), (p, p)] + [(0, 0)] * (a.ndim - 2), mode="wrap")
    return blur(big, sigma)[p:-p, p:-p]


# --------------------------------------------------------------- distance --

def sdf_from_mask(mask):
    """Signed distance (px) of a boolean mask: positive inside, negative outside."""
    m = mask.astype(np.uint8)
    inside = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    outside = cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
    return (inside - outside).astype(np.float32)


def grid(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return xx + 0.5, yy + 0.5


def sd_box(xx, yy, cx, cy, hw, hh, r=0.0):
    """Signed distance to a rounded box, positive INSIDE (px)."""
    qx = np.abs(xx - cx) - (hw - r)
    qy = np.abs(yy - cy) - (hh - r)
    out = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    return -out


def sd_circle(xx, yy, cx, cy, r):
    return r - np.hypot(xx - cx, yy - cy)


def sd_poly(xx, yy, pts):
    """Signed distance to a polygon (list of (x, y)), positive inside. Exact."""
    pts = np.asarray(pts, np.float32)
    d = np.full(xx.shape, 1e9, np.float32)
    s = np.ones(xx.shape, np.float32)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        wx, wy = xx - a[0], yy - a[1]
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey + 1e-9), 0, 1)
        bx, by = wx - ex * t, wy - ey * t
        d = np.minimum(d, bx * bx + by * by)
        c1 = yy >= a[1]
        c2 = yy < b[1]
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return -s * np.sqrt(d)


def sd_segment(xx, yy, a, b):
    ex, ey = b[0] - a[0], b[1] - a[1]
    wx, wy = xx - a[0], yy - a[1]
    t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey + 1e-9), 0, 1)
    return np.hypot(wx - ex * t, wy - ey * t)


def sd_polyline(xx, yy, pts):
    """Unsigned distance to an open polyline."""
    d = np.full(xx.shape, 1e9, np.float32)
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.minimum(d, sd_segment(xx, yy, a, b))
    return d


def bezier(p0, p1, p2, p3, n=48):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, np.float32) for p in (p0, p1, p2, p3))
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3).tolist()


def smin(a, b, k):
    """Smooth union of two signed distances (positive inside): a soft max."""
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0, 1)
    return a * h + b * (1 - h) + k * h * (1 - h)


# ---------------------------------------------------------------- profiles --

def bevel(sd, width, height, curve=1.0):
    """A bevelled rise: 0 outside, ramps up over `width` px inside the edge, flat `height` beyond."""
    t = np.clip(sd / max(width, 1e-6), 0, 1)
    if curve != 1.0:
        t = 1 - (1 - t) ** curve
    return (t * height).astype(np.float32)


def round_profile(sd, width, height):
    """A rounded (quarter-circle) edge."""
    t = np.clip(sd / max(width, 1e-6), 0, 1)
    return (np.sqrt(1 - (1 - t) ** 2) * height).astype(np.float32)


def ridge(d, halfwidth, height, flat=0.0):
    """A ridge along a line (d = distance to the line): round on top."""
    t = np.clip(1 - np.maximum(d - flat, 0) / max(halfwidth, 1e-6), 0, 1)
    return (np.sqrt(1 - (1 - t) ** 2) * height).astype(np.float32)


def coverage(sd, aa=1.0):
    """Anti-aliased coverage of a signed distance (positive inside)."""
    return np.clip(sd / aa + 0.5, 0, 1).astype(np.float32)


# --------------------------------------------------------------- surface --

@dataclass
class Mat:
    """A material: linear albedo, metalness, roughness."""
    albedo: tuple
    metal: float
    rough: float


MATS = {
    # Blackened iron: cool violet-black, a little metal showing through the black.
    "iron": Mat(tuple(hexc("#3a3542")), 0.6, 0.42),
    "iron_dark": Mat(tuple(hexc("#24202a")), 0.55, 0.5),
    "steel": Mat(tuple(hexc("#b8b4bc")), 1.0, 0.32),
    "gold": Mat(tuple(hexc("#e8be72")), 1.0, 0.30),
    "gold_dim": Mat(tuple(hexc("#a8844a")), 1.0, 0.45),
    "bronze": Mat(tuple(hexc("#b07a48")), 1.0, 0.38),
    "pewter": Mat(tuple(hexc("#8e8c94")), 1.0, 0.45),
    "bone": Mat(tuple(hexc("#d8cfbe")), 0.0, 0.55),
    "leather": Mat(tuple(hexc("#3a2418")), 0.0, 0.55),
    "wood": Mat(tuple(hexc("#3b2618")), 0.0, 0.62),
    "parchment": Mat(tuple(hexc("#efe2c2")), 0.0, 0.85),
    "black": Mat(tuple(hexc("#0e0c12")), 0.0, 0.3),
}


class Surface:
    """A canvas: height, material channels, emission, alpha."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.height = np.zeros((h, w), np.float32)
        self.albedo = np.zeros((h, w, 3), np.float32)
        self.metal = np.zeros((h, w), np.float32)
        self.rough = np.full((h, w), 0.5, np.float32)
        self.emit = np.zeros((h, w, 3), np.float32)
        self.alpha = np.zeros((h, w), np.float32)
        self.ao_extra = np.ones((h, w), np.float32)
        self.xx, self.yy = grid(h, w)

    # Painting a material where a coverage mask is.
    def paint(self, cov, mat: Mat | str, albedo_mul=None):
        if isinstance(mat, str):
            mat = MATS[mat]
        c = cov[..., None]
        alb = np.asarray(mat.albedo, np.float32)
        if albedo_mul is not None:
            alb = alb * (albedo_mul[..., None] if np.ndim(albedo_mul) == 2 else albedo_mul)
        self.albedo = self.albedo * (1 - c) + alb * c
        self.metal = self.metal * (1 - cov) + mat.metal * cov
        self.rough = self.rough * (1 - cov) + mat.rough * cov

    def shade(self, normal_strength=1.0, ao=0.6, shadow=0.5, light_elev=40.0, shadow_len=None, exposure=1.0):
        """Lit linear RGB from the matcaps."""
        hgt = self.height.astype(np.float32)
        gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3, borderType=cv2.BORDER_REPLICATE) / 8.0
        gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3, borderType=cv2.BORDER_REPLICATE) / 8.0
        nx, ny, nz = -gx * normal_strength, gy * normal_strength, np.ones_like(hgt)
        inv = 1 / np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny = nx * inv, ny * inv
        C = caps()
        S = C["diffuse"].shape[0]
        mapx = ((nx * 0.985) * 0.5 + 0.5) * (S - 1)
        mapy = (0.5 - (ny * 0.985) * 0.5) * (S - 1)

        def look(name):
            return cv2.remap(C[name], mapx.astype(np.float32), mapy.astype(np.float32), cv2.INTER_LINEAR)

        r = np.clip(self.rough, 0.15, 0.65)
        # Metal: lerp between roughness levels.
        lv = [(0.15, "metal_15"), (0.30, "metal_30"), (0.45, "metal_45"), (0.65, "metal_65")]
        metal = self._lerp_levels(r, lv, look)
        sv = [(0.15, "spec_08"), (0.30, "spec_30"), (0.65, "spec_60")]
        spec = self._lerp_levels(r, sv, look)
        diff = look("diffuse")
        alb = self.albedo
        m = self.metal[..., None]
        col = (alb * diff + spec) * (1 - m) + alb * metal * m
        # Ambient occlusion from the height: what sits lower than its surroundings.
        if ao > 0:
            occ = np.zeros_like(hgt)
            for s in (2.0, 6.0, 16.0):
                occ += np.clip(blur(hgt, s) - hgt, 0, None) / (s * 1.2)
            occ = np.clip(1 - occ * ao, 0.25, 1)
            col *= occ[..., None]
        # The key's cast shadow (upper left, low): a ray marched over the height.
        if shadow > 0:
            sh = self._shadow(hgt, light_elev, shadow_len)
            col *= (1 - shadow * sh)[..., None]
        col *= self.ao_extra[..., None]
        col = col * exposure + self.emit
        return col

    @staticmethod
    def _lerp_levels(r, levels, look):
        """The matcap for any roughness: hat-weighted between the rendered levels."""
        rs = [lv[0] for lv in levels]
        r = np.clip(r, rs[0], rs[-1])
        out = 0
        for i, (ri, name) in enumerate(levels):
            left = rs[i - 1] if i > 0 else ri - 1
            right = rs[i + 1] if i + 1 < len(rs) else ri + 1
            w = np.where(r <= ri, (r - left) / (ri - left), (right - r) / (right - ri))
            w = np.clip(w, 0, 1).astype(np.float32)
            if w.max() > 0:
                out = out + look(name) * w[..., None]
        return out

    def _shadow(self, hgt, elev, length):
        length = length or max(8, int(min(self.w, self.h) * 0.06))
        tanE = math.tan(math.radians(elev))
        d = np.array([-1.0, -1.0]) / math.sqrt(2)  # towards the light (upper left)
        best = np.zeros_like(hgt)
        pad = length + 2
        big = np.pad(hgt, pad, mode="edge")
        for t in range(1, length + 1):
            ox, oy = int(round(d[0] * t)), int(round(d[1] * t))
            shifted = big[pad + oy:pad + oy + self.h, pad + ox:pad + ox + self.w]
            best = np.maximum(best, shifted - hgt - t * tanE)
        return np.clip(best / 3.0, 0, 1)

    def finish(self, lin, size=None, glow=None, tone=1.0):
        """Tone-mapped sRGB RGBA (uint8), downsampled to `size` (area filter)."""
        x = lin * tone
        # A gentle shoulder: blacks and mid-tones as they are, highlights rolled off.
        k = 0.8
        y = np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))))
        rgb = lin_to_srgb(np.clip(y, 0, 1))
        a = self.alpha
        if glow is not None:
            # Glow outside the shape: light that needs no surface (additive, alpha from its light).
            g = lin_to_srgb(np.clip(glow, 0, 1))
            ga = np.clip(g.max(axis=2), 0, 1)
            out_a = a + ga * (1 - a)
            rgb = (rgb * a[..., None] + g * (1 - a[..., None])) / np.maximum(out_a[..., None], 1e-4)
            # Glow over the surface too (additive).
            rgb = np.clip(rgb + g * a[..., None] * 0.0, 0, 1)
            a = out_a
        img = np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])
        if size is not None and (size[0] != self.w or size[1] != self.h):
            img = downsample(img, size)
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def downsample(img, size):
    """Premultiplied area downsample (no dark fringes)."""
    W, H = size
    a = img[..., 3:4]
    pm = np.dstack([img[..., :3] * a, a])
    small = cv2.resize(pm, (W, H), interpolation=cv2.INTER_AREA)
    sa = small[..., 3:4]
    rgb = np.where(sa > 1e-4, small[..., :3] / np.maximum(sa, 1e-4), 0)
    return np.dstack([rgb, sa])


def to_pil(rgba):
    return Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def save(img: Image.Image, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)
