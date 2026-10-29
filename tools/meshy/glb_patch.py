"""glb_patch.py: edit a generated (Meshy) GLB in place of its data, nothing else re-encoded.

The app's hand-patch tool for a generated model's faults that live in the source (a sculpt ridge, a paint stroke):
  G = Glb(path); X = G.accessor(i) (numpy); G.set_accessor(i, X); img = G.image(i) (BGR/BGRA uint8, cv2);
  G.set_image(i, img) (re-encoded in the image's own mime type); G.save(out).
  screen_to_uv(uv_png, mask, size) maps a screen-space mask (from tools/meshy/uvpass.py's UV render) onto the atlas;
  smooth_region(P, I, w, iters, k) relaxes the vertices weighted by w (0..1), welded by position so seams stay shut;
  vertex_normals(P, I) recomputes smooth normals (welded).
Only POSITION/NORMAL/TEXCOORD float accessors and embedded images are supported (Meshy's export)."""
import json, struct
import numpy as np, cv2

CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

class Glb:
    def __init__(self, path):
        b = open(path, 'rb').read(); L = struct.unpack('<I', b[12:16])[0]
        self.J = json.loads(b[20:20 + L]); o = 20 + L; bl = struct.unpack('<I', b[o:o + 4])[0]
        self.bin = b[o + 8:o + 8 + bl]
        self.views = [bytes(self.bin[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]) for v in self.J['bufferViews']]
    def accessor(self, i):
        a = self.J['accessors'][i]; v = self.J['bufferViews'][a['bufferView']]
        assert 'byteStride' not in v or v['byteStride'] == np.dtype(CT[a['componentType']]).itemsize * NC[a['type']]
        d = np.frombuffer(self.views[a['bufferView']], CT[a['componentType']], a['count'] * NC[a['type']], a.get('byteOffset', 0))
        return d.reshape(a['count'], NC[a['type']]).copy() if NC[a['type']] > 1 else d.copy()
    def set_accessor(self, i, X):
        a = self.J['accessors'][i]; bv = a['bufferView']; off = a.get('byteOffset', 0)
        raw = np.ascontiguousarray(X, CT[a['componentType']]).tobytes(); v = bytearray(self.views[bv]); v[off:off + len(raw)] = raw; self.views[bv] = bytes(v)
        if a['type'] == 'VEC3' and 'min' in a: a['min'] = np.asarray(X).min(0).tolist(); a['max'] = np.asarray(X).max(0).tolist()
    def image(self, i):
        return cv2.imdecode(np.frombuffer(self.views[self.J['images'][i]['bufferView']], np.uint8), cv2.IMREAD_UNCHANGED)
    def set_image(self, i, img, quality=95):
        im = self.J['images'][i]; ext = '.png' if im.get('mimeType') == 'image/png' else '.jpg'
        ok, enc = cv2.imencode(ext, img, [cv2.IMWRITE_JPEG_QUALITY, quality] if ext == '.jpg' else [])
        assert ok; self.views[im['bufferView']] = enc.tobytes()
    def save(self, out):
        buf = bytearray()
        for k, v in enumerate(self.views):
            while len(buf) % 4: buf.append(0)
            self.J['bufferViews'][k]['byteOffset'] = len(buf); self.J['bufferViews'][k]['byteLength'] = len(v); buf += v
        while len(buf) % 4: buf.append(0)
        self.J['buffers'] = [{'byteLength': len(buf)}]
        js = json.dumps(self.J, separators=(',', ':')).encode()
        while len(js) % 4: js += b' '
        tot = 12 + 8 + len(js) + 8 + len(buf)
        with open(out, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, tot)); f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack('<II', len(buf), 0x004E4942)); f.write(buf)

def screen_to_uv(uv_png, mask, size, flip_v=True):
    """A screen mask (H x W bool) -> an atlas mask (size x size uint8 255) through a 16-bit UV render (R,G = u,v; B = covered)."""
    uv = cv2.imread(uv_png, cv2.IMREAD_UNCHANGED)[:, :, :3][:, :, ::-1].astype(np.float64) / 65535.0
    m = mask & (uv[:, :, 2] > 0.5); u = uv[:, :, 0][m]; v = uv[:, :, 1][m]
    x = np.clip((u * size).astype(int), 0, size - 1); y = np.clip(((1 - v) if flip_v else v) * size, 0, size - 1).astype(int)
    A = np.zeros((size, size), np.uint8); A[y, x] = 255; return A

def _weld(P, eps=1e-5):
    _, inv = np.unique(np.round(P / eps).astype(np.int64), axis=0, return_inverse=True); return inv.ravel()

def smooth_region(P, I, w, iters=8, k=0.5, mu=-0.53):
    """Taubin relax (k, then mu: no shrink) of the vertices weighted by w (0..1), on the position-welded mesh (UV seams stay shut)."""
    W = _weld(P); n = W.max() + 1; Q = np.zeros((n, 3)); np.add.at(Q, W, P); c = np.bincount(W, minlength=n)[:, None]; Q /= c
    ww = np.zeros(n); np.maximum.at(ww, W, w)
    T = W[I.reshape(-1, 3)]; E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); E = np.concatenate([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=n)[:, None].astype(float); deg[deg == 0] = 1
    for it in range(iters * 2):
        f = k if it % 2 == 0 else mu
        S = np.zeros_like(Q); np.add.at(S, E[:, 0], Q[E[:, 1]]); Q = Q + (f * ww)[:, None] * (S / deg - Q)
    return Q[W].astype(np.float32)

def vertex_normals(P, I):
    W = _weld(P); n = W.max() + 1; T = I.reshape(-1, 3)
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros((n, 3))
    for j in range(3): np.add.at(N, W[T[:, j]], fn)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12; return N[W].astype(np.float32)
