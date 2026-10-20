# WIP (style frames r1, solver): expects the solver scratch layout next to it (src/<frame>_<B|C>.png graded sources, masks/keep_town_o55.png, MoGe depth from paint.py save_control in b1/ b2/). The brush pass (structure tensor + flow LIC + LIC-noise stroke texture) is the piece an engine post-process could copy.
"""prepass.py FRAME DIR OUT [light=S] [brush=L] [ms=SP,SR] [tex=AMP] [ang=DEG]
A hand-made light block-in (what an engine light and fog pass could do) and a flow-aligned brush pass, before img2img.
FRAME town|ford|close, DIR B|C (which graded source). light S scales the light block-in (0 = none)."""
import sys, numpy as np, cv2
from PIL import Image
S = __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0] + "/"
fr, dr, out = sys.argv[1:4]; kw = dict(a.split("=", 1) for a in sys.argv[4:])
img = np.asarray(Image.open(S + f"src/{fr}_{dr}.png").convert("RGB"), np.float32) / 255
H, W = img.shape[:2]; YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
DEP = {"town": "b1/tB_d70_35_ctrl.png", "ford": "b2/fB1_s1_50_ctrl.png", "close": "b2/cB1_s1_50_ctrl.png"}
dep = np.asarray(Image.open(S + DEP[fr]).convert("L").resize((W, H), Image.BILINEAR), np.float32) / 255
LW = np.array([0.2126, 0.7152, 0.0722], np.float32)
def ss(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def pool(cx, cy, sig): return np.exp(-((XX - cx) ** 2 + (YY - cy) ** 2) / (2 * sig * sig))[..., None]
def fbm(seed, sigs, H=H, W=W):
    r = np.random.default_rng(seed); n = 0
    for i, s in enumerate(sigs): n = n + cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), s) * s
    n = (n - n.mean()) / (n.std() + 1e-6); return n
def light(x, s):
    lum = x @ LW
    if fr == "town":
        lb = cv2.GaussianBlur(lum, (0, 0), 3); lit = ss(0.17, 0.25, lb)[..., None]
        warm = np.array([1.0 + 0.10 * s, 1.0 + 0.035 * s, 1.0 - 0.10 * s], np.float32)
        x = x * (lit * warm + (1 - lit))
        sh = (1 - lit)
        x = x * (1 - sh) + sh * (x * np.array([1 - 0.05 * s, 1 - 0.025 * s, 1 + 0.08 * s], np.float32) + np.array([0.007, 0.007, 0.016], np.float32) * s)
        bounce = cv2.GaussianBlur(lit[..., 0], (0, 0), 35)[..., None] * sh
        x = x + bounce * np.array([0.030, 0.016, 0.004], np.float32) * s
        far = (1 - ss(0.05, 0.45, dep))[..., None]                       # aerial haze toward the top (far)
        x = x * (1 - 0.10 * s * far) + 0.10 * s * far * np.array([0.62, 0.58, 0.60], np.float32)
        sun = pool(W * 1.05, -H * 0.15, 900)                               # sunward glow, upper right
        x = x + sun * np.array([0.060, 0.038, 0.008], np.float32) * s
        x = x + pool(1855, 1015, 70) * np.array([0.20, 0.09, 0.02], np.float32) * s   # the brazier's own glow
    elif fr == "ford":
        x = x + pool(961, 525, 120) * np.array([0.20, 0.075, 0.015], np.float32) * s     # her ember light on water and stones
        x = x + pool(958, 751, 85) * np.array([0.17, 0.10, 0.03], np.float32) * s       # the lantern, amber
        x = x + pool(958, 830, 40) * np.array([0.06, 0.035, 0.01], np.float32) * s      # its reflection under it
        top = (1 - ss(0.0, 0.55, YY / H))[..., None]
        x = x + top * np.array([0.0, 0.020, 0.035], np.float32) * s                     # moon side of the river
        hp = np.maximum(lum - cv2.GaussianBlur(lum, (0, 0), 3), 0)[..., None]
        water = ((YY < 800) & (dep < 0.75))[..., None].astype(np.float32)
        x = x + hp * water * np.array([0.6, 0.9, 1.2], np.float32) * 0.8 * s           # moonlit ripple glints
        mist = ss(0.6, 2.0, fbm(3, (90, 45)))[..., None] * water * (1 - ss(0.5, 0.75, YY / H))[..., None]
        x = x * (1 - 0.10 * s * mist) + 0.10 * s * mist * np.array([0.30, 0.42, 0.58], np.float32)
        bank = ss(0.78, 0.86, YY / H)[..., None]
        x = x + bank * np.maximum(lum - 0.12, 0)[..., None] * np.array([0.05, 0.12, 0.2], np.float32) * s
    elif fr == "close":
        fire = pool(420, 960, 380)
        x = x * (1 + fire * np.array([0.50, 0.18, -0.06], np.float32) * s) + fire * np.array([0.060, 0.024, 0.0], np.float32) * s
        x = x + pool(400, 780, 140) * np.array([0.10, 0.04, 0.0], np.float32) * s       # glow round the flames
        far = (1 - ss(0.08, 0.40, dep))[..., None] * (1 - fire)
        x = x * (1 - 0.18 * s * far) + 0.18 * s * far * np.array([0.10, 0.17, 0.27], np.float32)   # moonlit haze between far trunks
        x = x + far * np.maximum(lum - cv2.GaussianBlur(lum, (0, 0), 6), 0)[..., None] * np.array([0.5, 0.8, 1.1], np.float32) * s  # cold rims far off
    return np.clip(x, 0, 1)

def setts(x, zoom=1.7):
    obj = np.asarray(Image.open(S + "masks/keep_town_o55.png").convert("L"), np.float32) / 255
    ground = (1 - np.clip(cv2.dilate(obj, np.ones((9, 9), np.uint8)) * 3, 0, 1))
    base = cv2.GaussianBlur(x, (0, 0), 4.0); det = x - base
    M = cv2.getRotationMatrix2D((W * 0.5, H * 0.5), 9.0, zoom)
    det2 = cv2.warpAffine(det * ground[..., None], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    g2 = cv2.warpAffine(ground, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    m = ss(-0.15, 0.35, fbm(11, (110, 55))) * ground * ss(0.9, 1.0, g2)
    return np.clip(base + det * (1 - m[..., None]) + det2 * m[..., None] * 1.1, 0, 1)
def brush(x, L, ang=35.0, tex=0.0):
    g = cv2.GaussianBlur(x, (0, 0), 1.0)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    E, F, G = [cv2.GaussianBlur(v, (0, 0), 3.0) for v in ((gx * gx).sum(-1), (gx * gy).sum(-1), (gy * gy).sum(-1))]
    D = np.sqrt((E - G) ** 2 + 4 * F * F); l1 = (E + G + D) / 2; l2 = (E + G - D) / 2
    tx, ty = l1 - E, -F; n = np.sqrt(tx * tx + ty * ty) + 1e-9; tx, ty = tx / n, ty / n
    A = np.clip((l1 - l2) / (l1 + l2 + 1e-9) * 1.5, 0, 1) * ss(1e-4, 1e-3, l1)
    a = np.radians(ang); tx = A * tx + (1 - A) * np.cos(a); ty = A * ty + (1 - A) * np.sin(a)
    n = np.sqrt(tx * tx + ty * ty) + 1e-9; tx, ty = (tx / n).astype(np.float32), (ty / n).astype(np.float32)
    def lic(src):
        acc = src.copy(); ws = np.ones(src.shape[:2], np.float32)
        for sg in (1, -1):
            px, py = XX.copy(), YY.copy(); vx, vy = tx * sg, ty * sg
            for k in range(1, int(L) + 1):
                px = px + vx; py = py + vy; wk = np.float32(np.exp(-k * k / (2 * (L / 2.0) ** 2)))
                acc = acc + cv2.remap(src, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) * (wk if src.ndim == 2 else wk)
                ws = ws + wk
                nx = cv2.remap(tx, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT); ny = cv2.remap(ty, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
                sgn = np.where(nx * vx + ny * vy < 0, -1, 1).astype(np.float32); vx, vy = nx * sgn, ny * sgn
        return acc / (ws[..., None] if src.ndim == 3 else ws)
    y = lic(x)
    if tex > 0:
        r = np.random.default_rng(5); nz = cv2.GaussianBlur(r.standard_normal((H, W)).astype(np.float32), (0, 0), max(L / 5.0, 0.8))
        st = lic(nz); st = st / (st.std() + 1e-6)
        y = y * (1 + tex * st[..., None])
    return np.clip(y, 0, 1)
x = img
if float(kw.get("light", 0)) > 0: x = light(x, float(kw["light"]))
if "setts" in kw: x = setts(x, float(kw["setts"]))
if "ms" in kw:
    sp, sr = (float(v) for v in kw["ms"].split(","))
    x = cv2.pyrMeanShiftFiltering((x[..., ::-1] * 255).astype(np.uint8), sp, sr)[..., ::-1].astype(np.float32) / 255
if float(kw.get("brush", 0)) > 0: x = brush(x, float(kw["brush"]), float(kw.get("ang", 35)), float(kw.get("tex", 0)))
Image.fromarray(np.clip(np.rint(x * 255), 0, 255).astype(np.uint8)).save(out); print(out)
