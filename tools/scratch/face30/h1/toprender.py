"""Software render of a hair style's cards + cap over her head (orthographic), for what shows at her crown.
    python toprender.py <gltf> <out.png> [elev_deg az_deg]   (az 0 = from her front, 90 = her left)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headlib import *  # noqa
from PIL import Image
path, out = sys.argv[1], sys.argv[2]
el, az = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (90.0, 0.0)
g = G(path); M = mats_for(g)
strands = np.asarray(Image.open(os.path.join(ART, "head_tex", "hair_strands.png")).convert("RGBA"), float) / 255
scalp = np.asarray(Image.open(os.path.join(ART, "head_tex", "hair_scalp.png")).convert("RGBA"), float) / 255
HV, HUV, HI, _ = head()
e, a = np.radians(el), np.radians(az)
fwd = -np.array([np.cos(e) * np.sin(a), np.sin(e), np.cos(e) * np.cos(a)])        # view direction (into the scene)
up0 = np.array([0, 0, -1.0]) if el > 80 else np.array([0, 1.0, 0])
right = np.cross(fwd, up0); right /= np.linalg.norm(right); up = np.cross(right, fwd)
C0 = np.array([0, EYE_Y + 0.05, 0.0]); S = 0.00025; N = 640
img = np.zeros((N, N, 3)); zb = np.full((N, N), -1e9); ids = np.zeros((N, N), int)
def draw(V, I, UV, col, kind, tex):
    p = V - C0; X = p @ right / S + N / 2; Y = -(p @ up) / S + N / 2; Z = -(p @ fwd)
    for k in range(len(I)):
        t = I[k]; xs, ys = X[t], Y[t]
        x0, x1 = int(max(np.floor(xs.min()), 0)), int(min(np.ceil(xs.max()), N - 1)); y0, y1 = int(max(np.floor(ys.min()), 0)), int(min(np.ceil(ys.max()), N - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        v0 = np.array([xs[1] - xs[0], ys[1] - ys[0]]); v1 = np.array([xs[2] - xs[0], ys[2] - ys[0]])
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-9: continue
        dx, dy = gx - xs[0], gy - ys[0]
        b1 = (dx * v1[1] - v1[0] * dy) / den; b2 = (v0[0] * dy - dx * v0[1]) / den; b0 = 1 - b1 - b2
        m = (b0 >= -1e-4) & (b1 >= -1e-4) & (b2 >= -1e-4)
        if not m.any(): continue
        bb = np.stack([b0[m], b1[m], b2[m]], 1)
        z = bb @ Z[t]; uv = bb @ UV[t]; c = bb @ col[t]
        iy, ix = (gy[m] - 0.5).astype(int), (gx[m] - 0.5).astype(int)
        if kind == "skin":
            sh = np.full(len(z), 0.0); al = np.ones(len(z)); rgb = np.tile([0.85, 0.7, 0.6], (len(z), 1))
        else:
            h, w = tex.shape[:2]
            tx = tex[np.clip((uv[:, 1] % 1) * h, 0, h - 1).astype(int), np.clip((uv[:, 0] % 1) * w, 0, w - 1).astype(int)]
            tr = 0.15 + 0.7 * tx[:, 0]
            if kind == "cap":
                fade = c[:, 3]; rope = c[:, 2]
                s = np.clip((fade - 0.85) / 0.15, 0, 1); s = s * s * (3 - 2 * s)
                br = tr * (1 - 0.5 * s * (1 - rope)) * (1 + (0.55 + 0.45 * c[:, 0] - 1) * rope)
                al = np.maximum(fade ** 2, tx[:, 3] * np.clip((fade + (tx[:, 1] - 0.5) * 0.35) / 0.8, 0, 1))
                rgb = np.outer(br, [0.55, 0.62, 1.0])           # (blue-ish: the cap)
            else:
                depth = c[:, 0]; along = uv[:, 1]
                sm = np.clip(along / 0.1, 0, 1); sm = sm * sm * (3 - 2 * sm)
                br = tr * ((1 - 0.4 * (1 - depth)) * (1 - sm) + sm) * (0.75 + 0.25 * depth)
                al = tx[:, 3] * np.clip(along / 0.012, 0, 1) * c[:, 3]
                keep = al >= 0.5; z = np.where(keep, z, -1e9); al = keep.astype(float)
                rgb = np.outer(br, [1.0, 0.6, 0.35])
        upd = z > zb[iy, ix]
        # cards opaque; cap blended over skin (drawn after skin): simple over
        for q in np.where(upd)[0]:
            yy, xx = iy[q], ix[q]
            if kind == "cap": img[yy, xx] = img[yy, xx] * (1 - al[q]) + rgb[q] * al[q]
            else: img[yy, xx] = rgb[q]
            zb[yy, xx] = z[q] if kind != "cap" else zb[yy, xx] + 0.0
        if kind == "cap":
            pass
draw(HV, HI, HUV, np.zeros((len(HV), 4)), "skin", None)
zb[:] = zb + 0.0012   # (the cap a millimetre out: drawn over her skin)
parts = []
for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
    at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
    V = skinned(P, J, Wt, M); col = g.acc(at["COLOR_0"]).astype(float)
    if col.max() > 1.5: col /= 65535.0
    parts.append((mat, V, I, g.acc(at["TEXCOORD_0"]).astype(float), col))
for mat, V, I, UV, col in parts:
    if mat == "hair_cap": draw(V, I, UV, col, "cap", scalp)
for mat, V, I, UV, col in parts:
    if mat == "hair": draw(V, I, UV, col, "card", strands)
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)
print("saved", out)
