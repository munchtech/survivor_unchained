"""solver 5a: per-frame shape numbers for an upper clip over a play base (idle frame 0 or a run frame / every run frame).
python m5.py CLIP [--base idle_reaver] [--bf 0|all] [--folder DIR] [--frames a-b] [--key viking_axe@hand_r]
Columns (cm, world: x her left, y up, z forward; from the pelvis unless said):
 hl@hip = left hand from her left hip joint; elL/elR = elbow angles (deg, 180 straight); elRh = right elbow height
 above the shoulder; hr = right hand; bend = trunk (pelvis->neck) tilt from vertical deg, side = its azimuth (0 forward, 90 her left);
 haft = deg below horizontal (head lower +); head = axe head; thigh/knee/head clearances = closest axe point (cm) to
 the left thigh segment, the left knee joint, her head joint; face: closest axe/hand_r point to her head (cm)."""
import sys, json, argparse
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa

LEGS = ('thigh', 'calf', 'foot', 'ball', 'glute')
ap = argparse.ArgumentParser()
ap.add_argument('clip'); ap.add_argument('--base', default='idle_reaver'); ap.add_argument('--bf', default='0')
ap.add_argument('--folder'); ap.add_argument('--frames'); ap.add_argument('--key', default='viking_axe@hand_r')
a = ap.parse_args()
label, folder, skel = A.SETS[0]
folder = Path(a.folder) if a.folder else folder
sk = A.Skeleton.load(A.DATA / skel); I = sk.index
arms = json.load(open(ANIM / 'data/arms_local.json'))
d, rot0, pos0 = A.load(folder / f'{a.clip}.json', sk)
_, br, bp = A.load(ANIM / 'out/clips' / f'{a.base}.json', sk)
legj = [j for n, j in I.items() if n in ('root', 'pelvis') or n.startswith(LEGS)]
bfs = range(br.shape[0]) if a.bf == 'all' else [int(a.bf)]
key = a.key; hb = I[key.split('@')[1]]
v = np.array(arms[key]['v']); r = np.linalg.norm(v, axis=1); vs = v[::max(1, len(v) // 1500)]
head_l = v[r > r.max() - 0.12].mean(0)


def seg(pt, a0, a1):
    t = np.clip(((pt - a0) @ (a1 - a0)) / ((a1 - a0) @ (a1 - a0)), 0, 1)
    return np.linalg.norm(pt - (a0 + np.outer(t, a1 - a0)), axis=1)


def ang(a0, b, c):
    u, w = a0 - b, c - b
    return np.degrees(np.arccos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))


fr = range(rot0.shape[0])
if a.frames:
    s, e = a.frames.split('-'); fr = range(int(s), int(e) + 1)
print(f"{a.clip} over {a.base}@{a.bf}")
print(' f  hl@hip        elL elR elRh  hr             bend side haft head           thigh knee | worst bf')
for f in fr:
    worst = None
    for bf in bfs:
        rot, pos = rot0[f:f + 1].copy(), pos0[f:f + 1].copy()
        rot[:, legj] = br[bf, legj]; pos[:, legj] = bp[bf, legj]
        g, p = sk.fk(rot, pos); g, p = g[0], p[0]
        P = lambda n: p[I[n]]
        pts = p[hb] + np.array([A.qrot(g[hb], x) for x in vs])
        ds = seg(pts, P('thigh_l'), P('calf_l')); th = ds.min() * 100; at = np.linalg.norm(vs[ds.argmin()]) * 100
        kn = np.linalg.norm(pts - P('calf_l'), axis=1).min() * 100
        if worst is None or th < worst[0]:
            worst = (th, kn, bf, p, g, pts, at)
    th, kn, bf, p, g, pts, at = worst
    P = lambda n: p[I[n]]
    pv = P('pelvis')
    hl = (P('hand_l') - P('thigh_l')) * 100
    elL = ang(P('upperarm_l'), P('lowerarm_l'), P('hand_l')); elR = ang(P('upperarm_r'), P('lowerarm_r'), P('hand_r'))
    elRh = (P('lowerarm_r')[1] - P('upperarm_r')[1]) * 100
    t = P('neck_01') - pv; bend = np.degrees(np.arccos(t[1] / np.linalg.norm(t))); side = np.degrees(np.arctan2(t[0], t[2]))
    hd = p[hb] + A.qrot(g[hb], head_l); dv = hd - p[hb]; haft = -np.degrees(np.arcsin(dv[1] / np.linalg.norm(dv)))
    face = np.linalg.norm(pts - (P('Head') + [0, 0.09, 0]), axis=1).min() * 100
    print(f"{f:2d} {np.round(hl).astype(int)!s:13} {elL:3.0f} {elR:3.0f} {elRh:4.0f}  {np.round((P('hand_r') - pv) * 100).astype(int)!s:14}"
          f" {bend:4.0f} {side:4.0f} {haft:4.0f} {np.round((hd - pv) * 100).astype(int)!s:14} {th:5.1f} {kn:5.1f} | face {face:4.1f} bf{bf} at{at:3.0f}")
