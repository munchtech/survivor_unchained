"""paint_fix.py <in.glb> <out.glb> <spec.json>: the app's atlas paint fixes for a generated (Meshy) model, by region.

A region is boxes [x0, y0, x1, y1] on a uvpass.py render (its <prefix>_uv.png), mapped onto the base-colour atlas
(glb_patch.screen_to_uv) and widened by `pad` texels. Ops (NPC 18 r2, Brannoc's straps, shirt edges, flecks, nostril):
  border  a dark garment edge on light cloth (a strap's pale fringe, ragged dark paint bleeding into a shirt): the dark
          class (L* under `dark`) is smoothed (median, `smooth` texels: ragged bits and jags go), then grown `grow`
          texels over the pale fringe; texels that change class take the colour of the nearest texel of their new
          class's core (dark: eroded 1; light: `grow` + 2 off the dark), and the new border is feathered 1 texel.
  tame    a jagged white rim (a shirt's open boundary): texels over the local median (`win`) by `dL` L* take that median.
  fleck   dark flecks on cloth: texels under `L` (or under the local median by `dL`) are inpainted from round them.
  lift    a dark mark (a nostril smudge reading as a ring or a scab): texels under the local median (`win`) by `dL`
          move `amount` of the way to it.
spec: {"ops": [{"op": "border", "uv": "<prefix>_uv.png", "boxes": [[...]], ...}, ...]}; a report of texels per op."""
import json, sys
import numpy as np, cv2
sys.path.insert(0, __import__('os').path.dirname(__file__))
from glb_patch import Glb, screen_to_uv

def region(op, size):
    uvr = cv2.imread(op['uv'], cv2.IMREAD_UNCHANGED); H, W = uvr.shape[:2]; m = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in op['boxes']: m[y0:y1, x0:x1] = True
    A = screen_to_uv(op['uv'], m, size, flip_v=op.get('flip_v', True)) > 0
    p = op.get('pad', 4)
    return cv2.dilate(A.astype(np.uint8), np.ones((2 * p + 1, 2 * p + 1), np.uint8)) > 0 if p else A

def nearest(src_mask):
    """For every texel, the (y, x) of the nearest texel in src_mask."""
    d, lab = cv2.distanceTransformWithLabels((~src_mask).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(src_mask); idx = np.zeros(lab.max() + 1, np.int64)
    # (labels count the zero texels of the input in scan order)
    order = np.flatnonzero(src_mask.ravel()); lz = lab.ravel()[order]; idx[lz] = order
    near = idx[lab]; return near // src_mask.shape[1], near % src_mask.shape[1]

def islands(G, size):
    """The atlas's UV islands: each texel's island id (0 off every island), from the mesh's triangles rasterized."""
    pr = G.J['meshes'][0]['primitives'][0]; UV = G.accessor(pr['attributes']['TEXCOORD_0']); I = G.accessor(pr['indices']).reshape(-1, 3)
    M = np.zeros((size, size), np.uint8); pts = np.round(UV[I] * size * 4).astype(np.int32)
    cv2.fillPoly(M, list(pts), 255, lineType=cv2.LINE_8, shift=2)
    return cv2.connectedComponents((M > 0).astype(np.uint8), connectivity=8)[1]

def fill_from(img, core, want, sigma):
    """Texels in want take the core's colour round them (a normalised Gaussian of the core texels): smooth, no streaks."""
    c = core.astype(np.float32); k = int(sigma * 3) | 1
    num = cv2.GaussianBlur(img.astype(np.float32) * c[:, :, None], (0, 0), sigma); den = cv2.GaussianBlur(c, (0, 0), sigma)[:, :, None]
    ok = want & (den[:, :, 0] > 1e-3); out = img.copy(); out[ok] = np.clip(num[ok] / den[ok], 0, 255).round().astype(np.uint8); return out, ok

def lab_L(img): return cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32) * (100 / 255)

def run(glb, out, spec):
    G = Glb(glb); J = G.J; tex = J['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']; ii = J['textures'][tex]['source']
    img = G.image(ii); size = img.shape[0]; rep = []
    global ISL; ISL = islands(G, size)
    for op in spec['ops']:
        R = region(op, size); L = lab_L(img); kind = op['op']; n = 0
        if kind == 'border':
            D = L < op.get('dark', 30); s = op.get('smooth', 2); g = op.get('grow', 3)
            Dm = cv2.medianBlur(D.astype(np.uint8) * 255, 2 * s + 1) > 127
            D2 = cv2.dilate(Dm.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * g + 1, 2 * g + 1))) > 0
            core_d = (cv2.erode(Dm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & D
            core_l = ~(cv2.dilate(D2.astype(np.uint8), np.ones((2 * g + 5, 2 * g + 5), np.uint8)) > 0) & ~D
            isl = ISL if 'ISL' in globals() else None
            for want, core in ((D2 & ~D, core_d), (D & ~D2, core_l)):
                ch = want & R
                if isl is not None:   # (a texel changes only from its own island's core: no paint across an atlas seam)
                    ny, nx = nearest(core); ch &= (isl == isl[ny, nx]) & (isl > 0)
                if ch.any(): img, ok = fill_from(img, core & (isl > 0 if isl is not None else True), ch, op.get('sigma', 2.5)); n += int(ok.sum())
            edge = (cv2.morphologyEx(D2.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0) & R
            bl = cv2.GaussianBlur(img, (3, 3), 0); img[edge] = bl[edge]
        elif kind == 'tame':
            w = op.get('win', 9); med = cv2.medianBlur(img, w); Lm = lab_L(med)
            ch = R & (L > Lm + op.get('dL', 6)); img[ch] = med[ch]; n = int(ch.sum())
        elif kind == 'fleck':
            w = op.get('win', 15); Lm = lab_L(cv2.medianBlur(img, w))
            ch = R & ((L < op['L']) if 'L' in op else (L < Lm - op.get('dL', 15)))
            ch = cv2.dilate(ch.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0; ch &= R
            img = cv2.inpaint(img, ch.astype(np.uint8) * 255, op.get('radius', 4), cv2.INPAINT_TELEA); n = int(ch.sum())
        elif kind == 'lift':
            w = op.get('win', 21); med = cv2.medianBlur(img, w); Lm = lab_L(med)
            ch = R & (L < Lm - op.get('dL', 6)); a = op.get('amount', 0.7)
            img[ch] = (img[ch].astype(np.float32) * (1 - a) + med[ch].astype(np.float32) * a).round().astype(np.uint8); n = int(ch.sum())
        rep.append({'op': kind, 'region': int(R.sum()), 'changed': n})
    G.set_image(ii, img); G.save(out); return rep

if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))), indent=1))
