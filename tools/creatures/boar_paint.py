"""The boar's paint and its fine normals, made in its texture's own space.

    python tools/creatures/boar_paint.py --work DIR [--size 2048]

Reads the maps the build baked (WORK/maps: the sculpt's paint, the form's
normals, where each texel is on the body, which way it faces, which way its
UVs run, which part it is, the occlusion) and writes WORK/final:
boar_albedo.png, boar_normal.png and boar_bristles.png.

The look is ours, laid in layers over the sculpt's paint (which keeps the
face's own marks: the eyes, the nostrils, the lips):
  the coat     near-black umber, grizzled rust and ash along the back and the
               hump (what the camera sees from above), thinner and warmer
               under the belly; the pale whisker blaze down each cheek;
  the hair     every texel's bristle drawn along the way the coat lies on
               the body (back from the snout, down the flanks and the legs),
               as streaks in the paint and as fine grooves in the normals;
  the mud      dried dark loam caked up the legs, cracked at its edge;
  the scars    old pale raised seams across the snout and the shoulders;
  the ivory    yellowed at the root, worn pale at the point, cracked along.
"""
import argparse
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from boar_config import CONFIG  # noqa: E402

LO, HI = np.array([-1.0, -1.0, -0.1]), np.array([1.0, 1.0, 1.9])   # the bake's position box (boar_build)


def srgb(c):
    return (np.asarray(c, np.float32) / 255.0) ** 2.2


def to_srgb8(lin):
    return np.clip(np.power(np.clip(lin, 0, 1), 1 / 2.2) * 255 + 0.5, 0, 255).astype(np.uint8)


def read(path, unit=True):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit(f"missing {path}")
    if im.ndim == 3:
        im = im[..., :3][..., ::-1]                       # BGR to RGB
    if unit:
        im = im.astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)
    return im


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise3(p, scale, seed=0, octaves=4):
    """Value noise over the body's own space (so it is seamless across the
    UV islands), summed over octaves; 0..1."""
    rng = np.random.default_rng(seed)
    out = np.zeros(p.shape[:-1], np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        s = scale * (2 ** o)
        q = p * s
        i = np.floor(q).astype(np.int64)
        f = q - i
        f = f * f * (3 - 2 * f)
        perm = rng.integers(0, 2 ** 31 - 1, size=3)

        def h(dx, dy, dz):
            x = (i[..., 0] + dx) * 73856093 ^ (i[..., 1] + dy) * 19349663 ^ (i[..., 2] + dz) * 83492791 ^ perm[0]
            x = (x ^ (x >> 13)) * 1274126177
            return ((x ^ (x >> 16)) & 0xFFFF).astype(np.float32) / 65535.0
        c = [[[h(dx, dy, dz) for dz in (0, 1)] for dy in (0, 1)] for dx in (0, 1)]
        x0 = c[0][0][0] * (1 - f[..., 2]) + c[0][0][1] * f[..., 2]
        x1 = c[0][1][0] * (1 - f[..., 2]) + c[0][1][1] * f[..., 2]
        x2 = c[1][0][0] * (1 - f[..., 2]) + c[1][0][1] * f[..., 2]
        x3 = c[1][1][0] * (1 - f[..., 2]) + c[1][1][1] * f[..., 2]
        y0 = x0 * (1 - f[..., 1]) + x1 * f[..., 1]
        y1 = x2 * (1 - f[..., 1]) + x3 * f[..., 1]
        out += amp * (y0 * (1 - f[..., 0]) + y1 * f[..., 0])
        total += amp
        amp *= 0.5
    return out / total


def segment_distance(p, a, b):
    """Each point's distance to the segment a-b (object space)."""
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(1e-9, ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[..., None] * ab), axis=-1)


def flow(P, N):
    """Which way the coat lies at each point (object space, before it is
    laid flat on the skin): back from the snout along the body, down the
    flanks and the legs, back and up along the crest."""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    back = np.stack([np.zeros_like(x), np.ones_like(x), np.zeros_like(x)], -1)
    down = np.stack([np.zeros_like(x), 0.25 * np.ones_like(x), -np.ones_like(x)], -1)
    side = smoothstep(0.05, 0.25, np.abs(N[..., 0]))            # how much it faces sideways
    leg = 1 - smoothstep(0.22, 0.4, z)
    w = np.clip(0.55 * side + leg, 0, 1)[..., None]
    f = back * (1 - w) + down * w
    return f / np.linalg.norm(f, axis=-1, keepdims=True)


def strands(dir_uv, size, seed=3, length=9):
    """Bristles drawn along a field of directions in the picture: white
    noise of seeds smeared along each texel's own direction (a line
    integral), so the streaks follow the coat."""
    rng = np.random.default_rng(seed)
    seeds = (rng.random((size, size)) ** 6).astype(np.float32)     # sparse bright seeds: separate bristles
    seeds = cv2.GaussianBlur(seeds, (0, 0), 0.6)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    acc = np.zeros((size, size), np.float32)
    wsum = 0.0
    for k in range(-length, length + 1):
        w = 1.0 - abs(k) / (length + 1)
        mx = xs + dir_uv[..., 0] * k
        my = ys + dir_uv[..., 1] * k
        acc += w * cv2.remap(seeds, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        wsum += w
    s = acc / wsum
    return (s - s.mean()) / (s.std() + 1e-6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--size", type=int, default=0)
    a = ap.parse_args()
    maps = os.path.join(a.work, "maps")
    out = os.path.join(a.work, "final")
    os.makedirs(out, exist_ok=True)
    paint = read(os.path.join(maps, "paint.png"))
    size = paint.shape[0]
    P = read(os.path.join(maps, "position.png")) * (HI - LO) + LO
    N = read(os.path.join(maps, "onormal.png")) * 2 - 1
    N /= np.linalg.norm(N, axis=-1, keepdims=True) + 1e-6
    T = read(os.path.join(maps, "tangent.png")) * 2 - 1
    T -= N * np.sum(T * N, -1, keepdims=True)
    T /= np.linalg.norm(T, axis=-1, keepdims=True) + 1e-6
    B = np.cross(N, T)
    nform = read(os.path.join(maps, "normal_form.png")) * 2 - 1
    part = read(os.path.join(maps, "part.png"))[..., 0] > 0.5
    ao = read(os.path.join(maps, "ao.png"))[..., 0]
    covered = np.linalg.norm(read(os.path.join(maps, "onormal.png")) - 0.0, axis=-1) > 0.05
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    nz = N[..., 2]

    # ---------------------------------------------------------- the coat --
    lin = srgb(paint * 255)
    lum = (lin @ np.array([0.2126, 0.7152, 0.0722], np.float32))
    detail = np.clip(lum / (np.median(lum[covered]) + 1e-4), 0.45, 1.8)[..., None]   # the sculpt's light and dark, kept
    coat = srgb((30, 23, 19))
    rust, ash = srgb((104, 70, 46)), srgb((112, 104, 94))
    belly = srgb((62, 48, 40))
    n1 = noise3(P, 9.0, 1)
    n2 = noise3(P, 31.0, 2)
    top = smoothstep(0.15, 0.75, nz) * smoothstep(0.3, 0.55, z)                 # the back, seen from above
    hump = np.exp(-((y + 0.2) / 0.28) ** 2) * smoothstep(0.55, 0.8, z)         # over the shoulders
    grizzle = np.clip(top * 0.75 + hump * 0.55, 0, 1) * smoothstep(0.35, 0.7, n1 * 0.7 + n2 * 0.5)
    tipcol = rust[None, None] * (1 - n2[..., None]) + ash[None, None] * n2[..., None]
    col = coat * (1 - grizzle[..., None] * 0.85) + tipcol * grizzle[..., None] * 0.85
    under = smoothstep(-0.2, -0.75, nz) * smoothstep(0.3, 0.45, z)
    col = col * (1 - under[..., None] * 0.6) + belly * under[..., None] * 0.6
    # The pale blaze down each cheek, the snout's leather and the hooves.
    blaze = np.exp(-(((y + 0.62) / 0.09) ** 2 + ((z - 0.46) / 0.07) ** 2)) * smoothstep(0.03, 0.09, np.abs(x)) * smoothstep(0.35, 0.65, n2 + 0.3)
    col = col * (1 - blaze[..., None]) + srgb((150, 140, 124)) * blaze[..., None]
    disc = smoothstep(-0.74, -0.78, y)
    col = col * (1 - disc[..., None]) + srgb((84, 64, 62)) * disc[..., None]
    hoof = 1 - smoothstep(0.035, 0.07, z)
    col = col * (1 - hoof[..., None]) + srgb((24, 22, 21)) * hoof[..., None]
    # Mud: up the legs to about the knees, its edge broken.
    mud_line = 0.2 + 0.07 * (noise3(P, 14.0, 5) - 0.5)
    mud = (1 - smoothstep(mud_line - 0.02, mud_line + 0.02, z)) * (1 - hoof * 0.7)
    dry = smoothstep(mud_line - 0.08, mud_line, z)                              # paler where it has dried, higher up
    mudcol = srgb((58, 44, 32)) * (1 - dry[..., None]) + srgb((92, 76, 58)) * dry[..., None]
    col = col * (1 - mud[..., None] * 0.9) + mudcol * mud[..., None] * 0.9
    # Scars: pale raised seams (object-space strokes, mirrored where they are both sides').
    scar = np.zeros(z.shape, np.float32)
    for (a3, b3, width, both) in CONFIG.get("scars", []):
        a3, b3 = np.array(a3, np.float32), np.array(b3, np.float32)
        for s in ((1, -1) if both else (1,)):
            m = np.array([s, 1, 1], np.float32)
            d = segment_distance(P, a3 * m, b3 * m)
            scar = np.maximum(scar, 1 - smoothstep(width * 0.4, width, d))
    col = col * (1 - scar[..., None] * 0.75) + srgb((150, 118, 106)) * scar[..., None] * 0.75
    col *= detail ** 0.35

    # --------------------------------------------------------- the hair --
    F = flow(P, N)
    F -= N * np.sum(F * N, -1, keepdims=True)
    du = np.sum(F * T, -1)
    dv = np.sum(F * B, -1)
    norm = np.sqrt(du * du + dv * dv) + 1e-6
    # (The picture's rows run down, the UVs' v up.)
    dir_uv = np.stack([du / norm, -dv / norm], -1).astype(np.float32)
    s = strands(dir_uv, size, length=max(4, size // 230))
    hair = np.clip(1 + 0.18 * s, 0.6, 1.4)
    col *= hair[..., None] ** (1 - mud[..., None] * 0.7 - disc[..., None] - hoof[..., None])

    # -------------------------------------------------------- the ivory --
    if part.any():
        roots = [np.array(t["root"], np.float32) * np.array([sgn, 1, 1], np.float32) for t in CONFIG.get("tusks", []) for sgn in (1, -1)]
        lens = [t["length"] for t in CONFIG.get("tusks", []) for _ in (1, -1)]
        d = np.min([np.linalg.norm(P - r, axis=-1) / l for r, l in zip(roots, lens)], axis=0)
        along = np.clip(d / 0.8, 0, 1)
        ivory = srgb((150, 118, 74)) * (1 - along[..., None]) + srgb((228, 218, 192)) * along[..., None]
        cracks = smoothstep(0.82, 0.95, noise3(P * np.array([1, 1, 1], np.float32), 140.0, 9, 2))
        ivory *= (1 - 0.35 * cracks)[..., None]
        col = np.where(part[..., None], ivory, col)

    col *= (0.55 + 0.45 * ao)[..., None]
    albedo = to_srgb8(col)
    albedo[~covered] = 0
    cv2.imwrite(os.path.join(out, "boar_albedo.png"), albedo[..., ::-1])

    # ------------------------------------------------------- the normals --
    # The hair's grooves and the scars' ridges as heights, turned to slopes
    # in the picture's own directions, laid over the form's normals.
    h = (0.6 * s * (1 - mud - hoof - disc).clip(0, 1) + 3.0 * cv2.GaussianBlur(scar.astype(np.float32), (0, 0), 1.2)).astype(np.float32)
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3) / 8
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3) / 8
    k = CONFIG.get("hair_depth", 0.35)
    detail_n = np.stack([-gx * k, gy * k, np.ones_like(gx)], -1)                # (green up the texture)
    n = np.stack([nform[..., 0] + detail_n[..., 0], nform[..., 1] + detail_n[..., 1], nform[..., 2]], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
    n[~covered] = (0, 0, 1)
    nimg = np.clip((n * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(out, "boar_normal.png"), nimg[..., ::-1])

    # ------------------------------------------------------ the bristles --
    import bristles
    bristles.draw(os.path.join(out, "boar_bristles.png"), 1024, "boar")
    print("PAINTED", out)


if __name__ == "__main__":
    main()
