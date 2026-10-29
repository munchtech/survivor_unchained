# Body 2 A: the sanity sheet (numpy render, d_b render.py): rows rest grey / rest textured / idle grey / idle textured;
# columns front, back, 3/4 right arm, 3/4 left arm, each original | mine. 1600 x 900.
#   python sheet_a.py <mine glb> <out.png> [orig glb]
import os, sys, numpy as np
B = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\23290ad1-ed63-4a0d-8e12-ac0911d16c27\scratchpad\body2"
sys.path.insert(0, B + r"\d_b")
import cm, render
from raster import sample
from PIL import Image, ImageDraw
cm.FILES["mine"] = sys.argv[1]; OUT = sys.argv[2]
if len(sys.argv) > 3: cm.FILES["orig"] = sys.argv[3]
PW, PH = 200, 225
def rot(yaw):
    c, s = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    tow = np.array([s, 0, c]); up = np.array([0, 1., 0]); right = np.cross(up, tow); return np.array([right, up, tow])
VIEWS = [("front", rot(0), "both"), ("back", rot(180), "both"), ("3/4 R", rot(-40), "r"), ("3/4 L", rot(40), "l")]
L = np.array([-0.45, 0.6, 0.66]); L /= np.linalg.norm(L)
def panel(b, G, view, sel, tex):
    P = b.P if G is None else b.pose(G); V = P @ view.T; v = V[sel]
    cx, cy = (v[:, 0].min() + v[:, 0].max()) / 2, (v[:, 1].min() + v[:, 1].max()) / 2
    w = (v[:, 0].max() - v[:, 0].min()) * 1.08; h = (v[:, 1].max() - v[:, 1].min()) * 1.08; px = max(w / PW, h / PH)
    img = render.render(b, G, view, (cx, cy, PW * px, PH * px), px=px)
    img = img[:PH, :PW]; n = img[..., :3]; m = ~np.isnan(n[..., 0]); n = np.nan_to_num(n); n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    d = np.clip((n * L).sum(-1), 0, 1); fill = np.clip(n[..., 2], 0, 1); g = 0.12 + 0.68 * d + 0.2 * fill ** 2
    if not tex:
        out = np.repeat(g[..., None], 3, -1)
    else:
        out = np.zeros(img.shape[:2] + (3,), np.float32); uv = img[..., 3:5]; mi = np.round(np.nan_to_num(img[..., 5], nan=-1)).astype(int)
        for k, im in b.imgs.items():
            mk = m & (mi == k)
            if mk.any(): out[mk] = sample(im, uv[mk])
        out = out * (0.30 + 0.85 * d + 0.15 * fill ** 2)[..., None]
    out[~m] = 0.95
    full = np.full((PH, PW, 3), 0.95, np.float32); full[:out.shape[0], :out.shape[1]] = out
    return (np.clip(full, 0, 1) * 255).astype(np.uint8)
bodies = {t: cm.load(t) for t in ("orig", "mine")}
sheet = Image.new("RGB", (1600, 900), (242, 242, 242)); dr = ImageDraw.Draw(sheet)
for t, b in bodies.items():
    I = b.sk.index; Gi = b.globals(b.clip("idle_reaver_town"), 0)
    for ri, (pose, G, tex) in enumerate((("rest", None, False), ("rest", None, True), ("idle", Gi, False), ("idle", Gi, True))):
        P = b.P if G is None else b.pose(G)
        for vi, (vn, view, which) in enumerate(VIEWS):
            hu = b.piece == "Heroine"
            ys = P[:, 1]; top = ys[hu].max()
            if which == "both":
                armb = [I[f"{n}_{sd}"] for n in ("clavicle", "upperarm", "lowerarm", "hand") for sd in "lr"]
                sel = hu & (np.isin(b.J, armb) * b.W).sum(1).__gt__(0.3) & (ys < top - 0.02)
            else:
                Gx = b.rest if G is None else G; sh = Gx[I[f"upperarm_{which}"]][:3, 3]; hd = Gx[I[f"hand_{which}"]][:3, 3]
                sg = -1 if which == "r" else 1
                sel = hu & (P[:, 0] * sg > abs(sh[0]) - 0.10) & (ys > min(hd[1], sh[1]) - 0.05) & (ys < sh[1] + 0.12)
            im = panel(b, G, view, sel, tex)
            x = (vi * 2 + (0 if t == "orig" else 1)) * PW; y = ri * PH
            sheet.paste(Image.fromarray(im), (x, y))
            dr.text((x + 4, y + 3), f"{'ORIG' if t == 'orig' else 'A'} {vn} {pose}{' tex' if tex else ''}", fill=(20, 20, 20))
for vi in range(1, 4): dr.line([(vi * 2 * PW, 0), (vi * 2 * PW, 900)], fill=(90, 90, 90), width=2)
sheet.save(OUT); print("SHEET", OUT)
