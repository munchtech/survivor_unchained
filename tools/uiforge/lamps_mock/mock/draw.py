"""Supersampled drawing. Shapes are SDFs evaluated on a 3x sample grid over a local patch, then box-averaged to 1x.
Layers are premultiplied float32 RGBA (H, W, 4) at 1920x1080. Pixel i spans [i, i+1]."""
import numpy as np
import cv2

W, H, SS = 1920, 1080, 3


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def layer():
    return np.zeros((H, W, 4), np.float32)


class Patch:
    """a local 3x sample grid; paint into it with fill(), then stamp() it onto a 1x layer"""

    def __init__(self, x0, y0, x1, y1, ss=SS):
        self.x0, self.y0 = int(np.floor(x0)), int(np.floor(y0))
        self.x1, self.y1 = int(np.ceil(x1)), int(np.ceil(y1))
        self.ss = ss
        gy, gx = np.mgrid[0:(self.y1 - self.y0) * ss, 0:(self.x1 - self.x0) * ss].astype(np.float32)
        self.X = self.x0 + (gx + 0.5) / ss
        self.Y = self.y0 + (gy + 0.5) / ss
        self.a = np.zeros(self.X.shape + (4,), np.float32)

    def cov(self, d, soft=0.0):
        """coverage of sdf d (px; <0 inside); a 1-sample ramp, plus an optional extra softness in px"""
        w = 1.0 / self.ss + soft
        return np.clip(0.5 - d / w, 0, 1)

    def fill(self, d, color, alpha=1.0, soft=0.0, mode='over'):
        """color: rgb (3,) or an (h, w, 3) field"""
        c = self.cov(d, soft) * alpha
        col = np.broadcast_to(np.asarray(color, np.float32), self.a.shape[:2] + (3,))
        src = np.concatenate([col * c[..., None], c[..., None]], -1)
        if mode == 'over':
            self.a = src + self.a * (1 - c[..., None])
        elif mode == 'add':
            self.a[..., :3] += src[..., :3]
            self.a[..., 3] = np.maximum(self.a[..., 3], c)
        elif mode == 'mul':         # darken what's under by c (keep alpha)
            self.a[..., :3] *= 1 - c[..., None] * (1 - col)
        return c

    def erase(self, d, amount=1.0, soft=0.0):
        c = self.cov(d, soft) * amount
        self.a *= 1 - c[..., None]

    def down(self):
        s = self.ss
        h, w = self.a.shape[0] // s, self.a.shape[1] // s
        return self.a.reshape(h, s, w, s, 4).mean((1, 3))

    def stamp(self, L, opacity=1.0, mode='over'):
        stamp(L, self.x0, self.y0, self.down() * opacity, mode)


def stamp(L, x0, y0, p, mode='over'):
    h, w = p.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya:
        return
    s = p[ya - y0:yb - y0, xa - x0:xb - x0]
    d = L[ya:yb, xa:xb]
    if mode == 'over':
        L[ya:yb, xa:xb] = s + d * (1 - s[..., 3:4])
    else:
        L[ya:yb, xa:xb] = d + s


# ---------------------------------------------------------------- SDFs (screen px)
def circle(P, cx, cy, r):
    return np.hypot(P.X - cx, P.Y - cy) - r


def ring(d, w):
    return np.abs(d) - w / 2


def segment(P, ax, ay, bx, by):
    """distance to segment, and t along it (0..1) and the arc length along it (px)"""
    vx, vy = bx - ax, by - ay
    L2 = max(vx * vx + vy * vy, 1e-9)
    t = np.clip(((P.X - ax) * vx + (P.Y - ay) * vy) / L2, 0, 1)
    return np.hypot(P.X - ax - t * vx, P.Y - ay - t * vy), t, t * np.sqrt(L2)


def lozenge(P, cx, cy, rx, ry):
    """a diamond with half-diagonals rx, ry (exact for rx == ry)"""
    x, y = np.abs(P.X - cx), np.abs(P.Y - cy)
    k = np.hypot(rx, ry)
    return (x * ry + y * rx - rx * ry) / k


def rbox(P, cx, cy, hw, hh, r):
    qx, qy = np.abs(P.X - cx) - hw + r, np.abs(P.Y - cy) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def stadium(P, cx, cy, hw, hh):
    """a horizontal stadium of half-size hw x hh"""
    r = hh
    ax = max(hw - r, 0)
    x = np.clip(P.X - cx, -ax, ax)
    return np.hypot(P.X - cx - x, P.Y - cy) - r


def star(P, cx, cy, r_in, r_out, n=8, rot=0.0):
    """an n-ray sunburst (sharp rays): polygon star sdf, approximated by angular interpolation, good to ~0.3 px"""
    dx, dy = P.X - cx, P.Y - cy
    rr = np.hypot(dx, dy)
    th = np.arctan2(dy, dx) - rot
    seg = 2 * np.pi / n
    f = np.abs(((th / seg) % 1.0) - 0.5) * 2          # 1 at a ray tip, 0 between rays
    # the boundary radius along this angle for straight edges between tip and notch
    a = (1 - f) * seg / 2
    tip, notch = r_out, r_in
    # edge from tip (angle 0) to notch (angle seg/2): solve polar line
    x1, y1 = tip, 0.0
    x2, y2 = notch * np.cos(seg / 2), notch * np.sin(seg / 2)
    nx, ny = y2 - y1, x1 - x2
    nn = np.hypot(nx, ny); nx, ny = nx / nn, ny / nn
    c = nx * x1 + ny * y1
    rb = c / (nx * np.cos(a) + ny * np.sin(a))
    return (rr - rb) * (c / np.maximum(rb, 1e-6) * 0.9 + 0.1)


def teardrop(P, cx, cy, h, w):
    """a flame drop, point up: base circle radius w/2 at the bottom, tip at cy - h/2"""
    r = w / 2
    by = cy + h / 2 - r
    ty = cy - h / 2
    dx = np.abs(P.X - cx)
    dy = P.Y - by
    # cone from the tip tangent to the circle
    L = by - ty
    s = r / max(L, 1e-6)
    s = min(s, 0.999)
    ang = np.arcsin(s)
    # distance to the cone sides (2D: lines through tip at +-ang from vertical)
    px, py = dx, P.Y - ty
    ca, sa = np.cos(ang), np.sin(ang)
    side = px * ca - py * sa
    dc = np.hypot(dx, dy) - r
    tangent_y = by - r * s           # above it the cone sides rule
    return np.where(P.Y < tangent_y, np.maximum(side, ty - P.Y), dc)


def radial(P, cx, cy, r, stops):
    """a radial gradient: stops [(t, rgb)] over t = dist / r"""
    t = np.clip(np.hypot(P.X - cx, P.Y - cy) / max(r, 1e-6), 0, 1)
    ts = [s[0] for s in stops]
    out = np.zeros(t.shape + (3,), np.float32)
    for k in range(3):
        out[..., k] = np.interp(t, ts, [s[1][k] for s in stops])
    return out


# ---------------------------------------------------------------- 1x helpers
def gauss(img, sigma):
    if sigma <= 0:
        return img
    k = int(np.ceil(sigma * 3.5)) * 2 + 1
    return cv2.GaussianBlur(img, (k, k), sigma, borderType=cv2.BORDER_CONSTANT)


def glow_spot(L, cx, cy, sigma, color, peak, extent=3.2):
    """an additive gaussian spot into L (rgb added, premultiplied add layer)"""
    r = sigma * extent
    x0, y0 = int(np.floor(cx - r)), int(np.floor(cy - r))
    x1, y1 = int(np.ceil(cx + r)), int(np.ceil(cy + r))
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    g = np.exp(-((gx + 0.5 - cx) ** 2 + (gy + 0.5 - cy) ** 2) / (2 * sigma * sigma)) * peak
    p = np.zeros(g.shape + (4,), np.float32)
    p[..., :3] = g[..., None] * np.asarray(color, np.float32)
    p[..., 3] = g
    stamp(L, x0, y0, p, 'add')


def over(dst_rgb, L):
    """premultiplied layer over an rgb image"""
    return L[..., :3] + dst_rgb * (1 - L[..., 3:4])


def screen_add(dst_rgb, L, gain=1.0):
    """additive light, screen-blended so nothing clips hard"""
    a = np.clip(L[..., :3] * gain, 0, 1)
    return 1 - (1 - dst_rgb) * (1 - a)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def load_rgb(p):
    from PIL import Image
    return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255


def save(p, rgb):
    from PIL import Image
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p)
