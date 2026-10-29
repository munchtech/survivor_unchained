"""dye_mask.py: a Marionette package NPC's dye mask (per-copy cloth and hair colours in a crowd).

  python tools/meshy/dye_mask.py <name> [--report] [--out DIR]     (name: a godot/art/npc/<name> package)

Reads the package's body.glb (one baked "generated" material: albedo, normal, metallicRoughness), rasterizes its
triangles into the atlas (each texel's bind-pose 3D point), classifies each texel by its nearest anchor colour
(Lab) from the package's config below, with 3D keep-outs (head: no cloth channels and only there hair; hands: nothing),
cleans the labels (5x5 mode, then small UV islands to their majority), and writes:
  art/npc/<name>/dye.png   1024 RGB: R = main cloth "a", G = second cloth "b", B = hair+beard; soft 1-texel edges on
                           the dyed side only (skin, face, eyes, lips, metal, leather stay exactly 0); gutters dilated.
  art/npc/<name>/dye.json  mask, base (each channel's mean albedo, measured, linear mean -> sRGB hex), range (Oklab L
                           clamps for any target), palette (period dyes), scale (per-copy height jitter in random mode).
--report: k-means (k=8, Lab) of the covered atlas: each cluster's hex, share and mean height, for picking anchors;
          and an overlay sheet (albedo | mask tint) in --out (default: the scratch dir) for checking by eye.
Shader side: shaders/npc_dye.gdshader; game side: src/Actors/NpcDye.cs.
"""
import json, os, re, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_patch import Glb

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
N = 1024

# Per package: anchors (Lab-nearest colour -> channel; "0" keeps the paint), the head keep-out (cloth channels are
# zeroed above neck_y + head_drop; hair only above neck_y + hair_drop, so a beard counts), hands (radius about the
# hand bones, zeroed), the channel ranges (Oklab L) and the palettes.
CFG = {
    'npc_folk_m': {'anchors': [['#62533b', 'a'], ['#564732', 'a'], ['#322014', 'b'], ['#4a3c34', 'hair'], ['#463524', 'hair'],
                               ['#c0927c', '0', 'skin'], ['#85604c', '0', 'skin'], ['#a17865', '0', 'skin']],
                   'ylim': {'a': [0.6, 9], 'b': [0.45, 0.9]}, 'hair_max': 0.17,
                   'range': {'a': [-0.12, 0.1], 'b': [-0.08, 0.12], 'hair': [-0.2, 0.2]},
                   'palette': {'a': ['#5f513a', '#6b3a2a', '#3e4f63', '#6a6236', '#4e3b2a', '#77736a', '#7a4a32', '#4b5a3e', '#8a7d62'],
                               'b': ['#312012', '#3a2a1e', '#2e2c2a', '#2f3540', '#3b3a26', '#4a2e1e', '#4a4741'],
                               'hair': ['#1e1a18', '#2b211b', '#3a2a20', '#5a4030', '#6e3a24', '#7a6048', '#5a5550', '#7d7872']}},
    'npc_folk_w': {'anchors': [['#560b09', 'a'], ['#d6cfbc', '0'], ['#b4a78e', 'b'], ['#190d0c', 'hair'], ['#544c44', '0'], ['#4f351b', '0'],
                               ['#dfa681', '0', 'skin'], ['#ba8169', '0', 'skin']],
                   'ylim': {'b': [1.1, 9]},
                   'range': {'a': [0.0, 0.25], 'b': [-0.1, 0.12], 'hair': [0.0, 0.25]},
                   'palette': {'a': ['#570b08', '#6e1a14', '#2f4466', '#8a6a26', '#5a3a24', '#33452e', '#7a3a20', '#6e6a62', '#4e2a3a'],
                               'b': ['#b9ab8f', '#c9bfa8', '#ddd6c6', '#cdb779', '#9fb0be', '#c79a88', '#b0aca2', '#a8ad8e'],
                               'hair': ['#0e0d0c', '#1e1a18', '#2b211b', '#3a2a20', '#4a3426', '#5a2e1c']}},
    'npc_watch_m': {'anchors': [['#1c3650', 'a'], ['#3b4e63', 'a'], ['#665b3e', 'b'], ['#817f7f', 'hair'], ['#6a6866', 'hair'], ['#5f5a58', 'hair'],
                                ['#3e291f', '0'], ['#2c2926', '0'], ['#c28f7d', '0', 'skin']], 'head_cloth': ['a'],
                    'ylim': {'b': [1.0, 9]},
                    'range': {'a': [-0.06, 0.1], 'b': [-0.12, 0.08], 'hair': [-0.2, 0.2]},
                    'palette': {'a': ['#30455c', '#2a3a52', '#3b5068', '#46576a', '#283447', '#3d4a58'],
                                'b': ['#685c3f', '#5a4a34', '#55554c', '#4b5a3e', '#6b4a32', '#706650', '#4a4036'],
                                'hair': ['#65605d', '#7d7872', '#9a9690', '#4a4440', '#3a302a', '#b0aca6']}},
    'npc_risen_s': {'anchors': [['#65665d', '0', 'skin'], ['#565654', '0', 'skin'], ['#7d715e', 'a'], ['#3e3323', 'a'], ['#4f4434', 'a'],
                                ['#655846', 'a'], ['#2f271c', 'hair'], ['#a49580', '0']],
                    'xlim': {'a': [-0.3, 0.3]}, 'ylim': {'a': [0.45, 1.42]}, 'hair_drop': 0.1,
                    'zero_boxes': [[-0.1, 1.40, 0.0, 0.1, 1.64, 0.5]], 'scale': 0.05,
                    'range': {'a': [-0.08, 0.08], 'hair': [-0.1, 0.1]},
                    'palette': {'a': ['#564b3a', '#5f5c55', '#4e4230', '#4f5446', '#66625a', '#3e3528', '#6e6656'],
                                'hair': ['#352c23', '#2a241e', '#3a3028', '#4a4a46', '#1e1c1a', '#50463a']}},
}


def hex2rgb(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def rgb2hex(c):
    c = np.clip(np.round(np.asarray(c) * 255), 0, 255).astype(int); return '#%02x%02x%02x' % tuple(c)


def s2l(c):
    c = np.asarray(c, np.float64); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def l2s(c):
    c = np.clip(np.asarray(c, np.float64), 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def oklab_L(lin):
    r, g, b = lin
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    return float(0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s)


def lab(rgb01):
    """rgb (..., 3) in 0..1, RGB order -> cv2 Lab float (L 0..100)."""
    return cv2.cvtColor(np.asarray(rgb01, np.float32).reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(np.shape(rgb01))


def load(name):
    G = Glb(os.path.join(ROOT, 'godot', 'art', 'npc', name, 'body.glb')); J = G.J
    mat = J['materials'][0]; tex = J['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
    alb = cv2.cvtColor(G.image(tex['source'])[..., :3], cv2.COLOR_BGR2RGB)
    P, UV, I = [], [], []
    for mesh in J['meshes']:
        for pr in mesh['primitives']:
            o = sum(len(p) for p in P)
            P.append(G.accessor(pr['attributes']['POSITION'])); UV.append(G.accessor(pr['attributes']['TEXCOORD_0']))
            I.append(G.accessor(pr['indices']).reshape(-1, 3).astype(np.int64) + o)
    P, UV, I = np.concatenate(P), np.concatenate(UV), np.concatenate(I)
    sk = J['skins'][0]; ibm = G.accessor(sk['inverseBindMatrices']).reshape(-1, 4, 4)
    bones = {J['nodes'][j]['name']: np.linalg.inv(ibm[i].T)[:3, 3] for i, j in enumerate(sk['joints'])}
    return alb, P, UV, I, bones


def raster(P, UV, I):
    """Each atlas texel's triangle (-1: gutter) and bind-pose point."""
    tri = np.full((N, N), -1, np.int32)
    px = UV * N - 0.5
    for t, (a, b, c) in enumerate(I):
        pts = np.round(px[[a, b, c]] * 16).astype(np.int32)
        cv2.fillConvexPoly(tri, pts, int(t), lineType=cv2.LINE_8, shift=4)
    ys, xs = np.nonzero(tri >= 0); t = tri[ys, xs]
    A, B, C = px[I[t, 0]], px[I[t, 1]], px[I[t, 2]]
    q = np.stack([xs, ys], 1).astype(np.float64)
    v0, v1, v2 = B - A, C - A, q - A
    d = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]; d = np.where(np.abs(d) < 1e-12, 1e-12, d)
    w1 = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / d; w2 = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / d
    w1, w2 = np.clip(w1, 0, 1), np.clip(w2, 0, 1); w0 = np.clip(1 - w1 - w2, 0, 1)
    X = np.zeros((N, N, 3), np.float32)
    X[ys, xs] = w0[:, None] * P[I[t, 0]] + w1[:, None] * P[I[t, 1]] + w2[:, None] * P[I[t, 2]]
    return tri, X


def splat(X, cov, img, H=640):
    """Front | back orthographic views of the atlas's texels (a z-buffered point splat): a cheap 3D look at a mask."""
    P = X[cov]; C = img[cov]; lo = np.percentile(P, 0.3, 0); hi = np.percentile(P, 99.7, 0)
    k = np.all((P >= lo) & (P <= hi), 1); P, C = P[k], C[k]; s = (H - 8) / (hi[1] - lo[1]); W = int((hi[0] - lo[0]) * s) + 8
    outs = []
    for sgn in (1, -1):
        o = np.full((H, W, 3), 0.15, np.float32); zb = np.full((H, W), -1e9)
        u = ((P[:, 0] - lo[0]) * s + 4).astype(int); u = u if sgn > 0 else W - 1 - u
        v = (H - 5 - (P[:, 1] - lo[1]) * s).astype(int); z = P[:, 2] * sgn
        order = np.argsort(z); u, v, z, c = u[order], v[order], z[order], C[order]
        for dy in (0, 1):
            for dx in (0, 1):
                o[np.clip(v + dy, 0, H - 1), np.clip(u + dx, 0, W - 1)] = c
        outs.append(o)
    return np.hstack(outs)


def mode5(lbl, cov, k):
    oh = np.stack([((lbl == i) & cov).astype(np.float32) for i in range(k)], -1)
    oh = np.stack([cv2.boxFilter(oh[..., i], -1, (5, 5), normalize=False) for i in range(k)], -1)
    out = np.argmax(oh, -1).astype(np.int32)
    return np.where(cov, out, lbl)


def build(name, report=False, out=None):
    cfg = CFG[name]
    alb, P, UV, I, bones = load(name)
    tri, X = raster(P, UV, I); cov = tri >= 0
    a1 = cv2.resize(alb, (N, N), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    L = lab(cv2.GaussianBlur(a1, (0, 0), 0.8))
    if report:
        sel = L[cov]; cv2.setRNGSeed(7)
        _, lab_k, cent = cv2.kmeans(sel.astype(np.float32), 8, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2), 4, cv2.KMEANS_PP_CENTERS)
        lab_k = lab_k.ravel(); ycov = X[cov][:, 1]
        for i, c in enumerate(cent):
            rgb = cv2.cvtColor(c.reshape(1, 1, 3).astype(np.float32), cv2.COLOR_LAB2RGB).ravel()
            m = lab_k == i
            print(f'  k{i} {rgb2hex(rgb)} share {m.mean():.3f} y {ycov[m].mean():.2f} [{np.percentile(ycov[m], 5):.2f}..{np.percentile(ycov[m], 95):.2f}]')
    if not cfg.get('anchors'):
        return
    names = ['0', 'a', 'b', 'hair']
    anc = cfg['anchors']; ac = lab(np.stack([hex2rgb(x[0]) for x in anc])); ach = np.array([names.index(x[1]) for x in anc])
    prot = np.array([bool(p) for p in [len(x) > 2 and x[2] == 'skin' for x in anc]])
    w = np.array([1.0, 1.6, 1.6], np.float32) * cfg.get('ab_weight', 1.0) ** np.array([0, 1, 1])
    d = (((L[:, :, None, :] - ac[None, None]) * w) ** 2).sum(-1)
    near = np.argmin(d, -1)
    lbl = ach[near].astype(np.int32); skin = prot[near]
    neck = bones['neck_01'][1]; y = X[..., 1]
    head = y > neck + cfg.get('head_drop', 0.0)
    hairzone = (y > neck + cfg.get('hair_drop', -0.05)) & (y < neck + cfg.get('hair_max', 9.0)) & (np.abs(X[..., 0]) < cfg.get('hair_x', 0.16))
    hc = cfg.get('head_cloth', [])
    def limits():
        lbl[(lbl == 3) & ~hairzone] = 0
        for c in (1, 2):
            if names[c] not in hc: lbl[(lbl == c) & head] = 0
        for c, (x0, x1) in cfg.get('xlim', {}).items():
            ci = names.index(c); lbl[(lbl == ci) & ((X[..., 0] < x0) | (X[..., 0] > x1))] = 0
        for c, (y0, y1) in cfg.get('ylim', {}).items():
            ci = names.index(c); lbl[(lbl == ci) & ((y < y0) | (y > y1))] = 0
        if not cfg.get('hands_keep'):
            lbl[hands] = 0
    lbl[(lbl == 3) & ~hairzone] = 0
    hands = np.zeros_like(cov)
    for sd in ('l', 'r'):   # past the wrist (along the forearm) and near the hand: the hand, never its cuff
        h, e = bones['hand_' + sd], bones['lowerarm_' + sd]; ax = (h - e) / np.linalg.norm(h - e)
        hands |= (((X - h) @ ax) > cfg.get('wrist', 0.0)) & (np.linalg.norm(X - h, axis=-1) < 0.25)
    limits()
    lbl[~cov] = 0
    lbl = mode5(lbl, cov, 4); lbl[~cov] = 0
    # small UV islands to their majority (a speck of dyed texels in a strap's island, or the reverse)
    nI, isl = cv2.connectedComponents(cov.astype(np.uint8), connectivity=8)
    area = np.bincount(isl.ravel(), minlength=nI)
    for i in np.nonzero((area > 0) & (area < cfg.get('island', 300)))[0]:
        if i == 0: continue
        m = isl == i; cnt = np.bincount(lbl[m], minlength=4)
        if cnt.max() > 0.7 * m.sum(): lbl[m] = cnt.argmax()
    # keep-outs after cleanup too: they are absolute
    limits()
    for b in cfg.get('zero_boxes', []):   # [x0,y0,z0,x1,y1,z1] bind-pose boxes forced 0
        lo, hi = np.array(b[:3]), np.array(b[3:])
        lbl[np.all((X >= lo) & (X <= hi), -1) & cov] = 0
    hard0 = cov & (lbl == 0)
    M = np.zeros((N, N, 3), np.float32)
    for c in range(3):
        m = (lbl == c + 1).astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), 0.7)
        m[hard0] = 0; m[lbl == c + 1] = np.maximum(m[lbl == c + 1], 0.0)
        M[..., c] = m
    # the soft edge may only spread onto cloth-of-another-channel and the dyed side: protected texels exactly 0
    face = cv2.dilate((skin & head & cov).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & (lbl != 3)
    lbl[face] = 0; hard0 = cov & (lbl == 0)
    for c in range(3): M[..., c][face] = 0
    zero = hard0 & (skin | hands | face | head & (lbl == 0))
    M[zero] = 0
    # gutters: the nearest covered value (so mips and bilinear never pull a gutter's 0 into cloth)
    g = M.copy(); have = cov.copy()
    for _ in range(12):
        dil = cv2.dilate(g, np.ones((3, 3), np.uint8)); hv = cv2.dilate(have.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        new = hv & ~have; g[new] = dil[new]; have = hv
    M = np.where(cov[..., None], M, g)
    # measured base: each channel's linear mean over its solid texels (full-res albedo)
    lin = s2l(a1)
    base, rng = {}, {}
    for c, key in enumerate(['a', 'b', 'hair']):
        m = (M[..., c] > 0.9) & cov
        if m.sum() < 50: continue
        mean = lin[m].mean(0); base[key] = rgb2hex(l2s(mean))
        Lb = oklab_L(mean); lo, hi = cfg['range'].get(key, [-0.2, 0.2])
        rng[key] = [round(max(0.0, Lb + lo), 3), round(min(1.0, Lb + hi), 3)]
    pkg = os.path.join(ROOT, 'godot', 'art', 'npc', name)
    png = np.clip(np.round(M * 255), 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(pkg, 'dye.png'), cv2.cvtColor(png, cv2.COLOR_RGB2BGR))
    js = {'mask': 'dye.png', 'base': base, 'range': rng,
          'palette': {k: v for k, v in cfg['palette'].items() if k in base}, 'scale': cfg.get('scale', 0.04)}
    txt = re.sub(r'\[\s+([^\[\]{}]*?)\s+\]', lambda m: '[' + re.sub(r'\s*\n\s*', ' ', m.group(1)) + ']', json.dumps(js, indent=1))
    open(os.path.join(pkg, 'dye.json'), 'w').write(txt + '\n')
    tot = cov.sum()
    share = {k: round(float((M[..., c][cov] > 0.5).sum() / tot), 3) for c, k in enumerate(['a', 'b', 'hair'])}
    skin_hit = float(M[face & cov].max()) if (face & cov).any() else 0.0
    hand_hit = float(M[hands & cov].max()) if (hands & cov).any() and not cfg.get('hands_keep') else 0.0
    face = head & cov & ~((lbl == 3)); face_hit = float(M[face][:, :2].max()) if face.any() else 0.0
    print(f'{name}: share of covered atlas {share}; base {base}; range {rng}; max on face skin {skin_hit:.3f} ({int((face & cov).sum())} texels), hands {hand_hit:.3f} ({int((hands & cov).sum())} texels)')
    if out:
        tint = a1.copy(); col = np.array([[1, 0.1, 0.1], [0.1, 1, 0.1], [0.2, 0.4, 1]], np.float32)
        for c in range(3): tint = tint * (1 - 0.65 * M[..., c:c + 1]) + 0.65 * M[..., c:c + 1] * col[c]
        sheet = np.hstack([a1, tint]); sheet = cv2.resize(sheet, (N, N // 2), interpolation=cv2.INTER_AREA)
        v3 = np.hstack([splat(X, cov, a1), splat(X, cov, tint)])
        cv2.imwrite(os.path.join(out, f'{name}_view.jpg'), cv2.cvtColor((v3 * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
        cv2.imwrite(os.path.join(out, f'{name}_mask.jpg'), cv2.cvtColor((sheet * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[a.index('--out') + 1] if '--out' in a else None
    for n in [x for x in a if not x.startswith('--') and (out is None or x != out)]:
        build(n, report='--report' in a, out=out)
