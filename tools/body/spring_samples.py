"""spring_samples: the breast surface samples and arm radii B's springs collide with (P1 R1 jiggle).

    python tools/body/spring_samples.py [--glb godot/art/people/body_p1/body.glb] [--n 0]

Reads B's close body (the Heroine mesh of body.glb, bind space = skeleton space) and writes
godot/data/body/p1_spring_samples.json: per breast side, every surface vertex of the part breast_{s} + breast_tip_{s} move (their
weight >= 0.25) in farthest-point order (the game collides a prefix, colliders.samples; the harness measures all), each with its rest position and its skin (bone names,
weights), so the game and the harness skin them exactly as the GPU does (LBS on the posed globals); per arm side the
upper arm's radius (median distance of the upper arm's vertices to its axis, upperarm head -> lowerarm head).
Rerun after a republish that changes the bust or the arms (godot/data/body/springs.json reads it; P1Springs).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def load(glb: Path):
    f = glb.read_bytes()
    n = struct.unpack('<I', f[12:16])[0]
    js = json.loads(f[20:20 + n])
    b0 = 20 + n + 8

    def acc(i):
        a = js['accessors'][i]
        bv = js['bufferViews'][a['bufferView']]
        k = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        ct = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[a['componentType']]
        return np.frombuffer(f, dtype=ct, count=a['count'] * k, offset=b0 + bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, k)

    skin = js['skins'][0]
    names = [js['nodes'][j]['name'] for j in skin['joints']]
    ibm = acc(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    rest = np.linalg.inv(ibm)
    mesh = next(m for m in js['meshes'] if m['name'] == 'Heroine')
    at = mesh['primitives'][0]['attributes']
    V = acc(at['POSITION']).astype(float)
    J = acc(at['JOINTS_0']).astype(int)
    W = acc(at['WEIGHTS_0']).astype(float)
    if W.max() > 1.5:
        W /= 255 if W.max() <= 255 else 65535
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
    return f, names, rest, V, J, W


def fps(P, n):
    idx = [int(np.argmax(P[:, 2]))]          # start at the front-most (the apex)
    d = np.linalg.norm(P - P[idx[0]], axis=1)
    while len(idx) < min(n, len(P)):
        i = int(np.argmax(d))
        idx.append(i)
        d = np.minimum(d, np.linalg.norm(P - P[i], axis=1))
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--glb', default=str(ROOT / 'godot/art/people/body_p1/body.glb'))
    ap.add_argument('--n', type=int, default=0, help='samples per side (0: every moving vertex, in farthest-point order so a prefix is a spread subset)')
    ap.add_argument('--out', default=str(ROOT / 'godot/data/body/p1_spring_samples.json'))
    a = ap.parse_args()
    raw, names, rest, V, J, W = load(Path(a.glb))
    out = {'about': 'B breast surface samples (rest position + skin) and upper-arm radii for P1Springs; written by tools/body/spring_samples.py, do not edit',
           'glb_sha1': hashlib.sha1(raw).hexdigest()[:12], 'breasts': {}, 'arm_radius': {}}
    for s in ('l', 'r'):
        ids = [names.index(f'breast_{s}'), names.index(f'breast_tip_{s}')]
        w = sum((W * (J == i)).sum(1) for i in ids)
        vid = np.nonzero(w >= 0.25)[0]
        pick = vid[fps(V[vid], a.n or len(vid))]
        rows = []
        for v in pick:
            js_ = [(names[J[v, k]], round(float(W[v, k]), 5)) for k in range(4) if W[v, k] > 1e-4]
            rows.append({'p': [round(float(x), 5) for x in V[v]], 'j': [n for n, _ in js_], 'w': [x for _, x in js_]})
        out['breasts'][s] = rows
        arm = [i for i, n in enumerate(names) if n == f'upperarm_{s}' or (n.startswith('upperarm_twist') and n.endswith('_' + s))]
        wa = sum((W * (J == i)).sum(1) for i in arm)
        P = V[wa >= 0.5]
        a0 = rest[names.index(f'upperarm_{s}')][:3, 3]
        a1 = rest[names.index(f'lowerarm_{s}')][:3, 3]
        ax = (a1 - a0) / np.linalg.norm(a1 - a0)
        t = np.clip((P - a0) @ ax, 0, np.linalg.norm(a1 - a0))
        r = np.linalg.norm(P - (a0 + t[:, None] * ax), axis=1)
        out['arm_radius'][s] = round(float(np.median(r)), 4)
        print(f'{s}: {len(vid)} moving breast verts, {len(rows)} samples; upper arm {len(P)} verts, radius median {np.median(r)*1000:.1f} mm p90 {np.percentile(r, 90)*1000:.1f}')
    Path(a.out).write_text(json.dumps(out, separators=(',', ':')) + '\n')
    print('wrote', a.out)


if __name__ == '__main__':
    main()
