"""solver 7a: play-true head per frame. python hr.py CLIP [--base idle_reaver] [--bf 0] [--folder DIR] [--frames a-b]
roll = her left ear above her right (+ = head tilted onto her RIGHT shoulder), deg, world; pitch = face below level (+ down);
both after play's HeadLevel 0.8 (ease -8). raw = before leveling. chest roll = spine_03 lateral axis roll (same sign)."""
import sys, json, argparse, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
from rig import qmatrix
ap = argparse.ArgumentParser(); ap.add_argument('clip'); ap.add_argument('--base', default='idle_reaver')
ap.add_argument('--bf', type=int, default=0); ap.add_argument('--folder'); ap.add_argument('--frames')
a = ap.parse_args()
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
folder = Path(a.folder) if a.folder else ANIM / 'out/clips'
d, rot0, pos0 = A.load(folder / f'{a.clip}.json', sk)
_, br, bp = A.load(ANIM / 'out/clips' / f'{a.base}.json', sk) if a.base != 'self' else (None, None, None)
LEGS = ('thigh', 'calf', 'foot', 'ball', 'glute')
legj = [j for n, j in I.items() if n in ('root', 'pelvis') or n.startswith(LEGS)]
gr, _ = sk.fk(sk.rest_rot[None].copy(), sk.rest_pos[None].copy())
def axes(q, qr):
    Rr = qmatrix(qr); R = qmatrix(q)
    return R @ (Rr.T @ np.array([0, 0, 1.])), R @ (Rr.T @ np.array([1., 0, 0]))
def rotv(axis, ang, v):
    axis = axis / np.linalg.norm(axis); c, s = math.cos(ang), math.sin(ang)
    return v * c + np.cross(axis, v) * s + axis * (axis @ v) * (1 - c)
fr = range(rot0.shape[0])
CA, CP = math.radians(45), math.radians(float(__import__('os').environ.get('CP', '35')))
CAM = np.array([math.sin(CA) * math.cos(CP), math.sin(CP), math.cos(CA) * math.cos(CP)]); D = -CAM
RT = np.cross(D, [0, 1, 0]); RT /= np.linalg.norm(RT); SU = np.cross(RT, D)
if a.frames: s, e = a.frames.split('-'); fr = range(int(s), int(e) + 1)
print(f"{a.clip} over {a.base}@{a.bf}:  f  roll pitch | raw roll pitch | chest roll | yaw(head vs pelvis) | screen tilt from 315 cam (+ top toward screen right = her left)")
for f in fr:
    rot, pos = rot0[f:f+1].copy(), pos0[f:f+1].copy()
    if br is not None: rot[:, legj] = br[a.bf, legj]; pos[:, legj] = bp[a.bf, legj]
    g, p = sk.fk(rot, pos); g = g[0]
    fw, lt = axes(g[I['Head']], gr[0, I['Head']])
    rr = math.degrees(math.asin(lt[1])); rp = math.degrees(-math.asin(fw[1]))
    droop = rp + 8
    if droop > 0:
        ax = np.cross(fw, [0, 1, 0]); lift = math.radians(min(droop, 35) * 0.8)
        fw2, lt2 = rotv(ax, lift, fw), rotv(ax, lift, lt)
    else: fw2, lt2 = fw, lt
    cf, cl = axes(g[I['spine_03']], gr[0, I['spine_03']])
    up2 = np.cross(fw2, lt2)  # head up (fwd x left = up)
    cu = np.cross(cf, cl)
    def scr(v):
        return math.degrees(math.atan2(v @ RT, v @ SU))
    nk = p[0, I['Head']] - p[0, I['spine_03']]
    pf, _ = axes(g[I['pelvis']], gr[0, I['pelvis']])
    yaw = math.degrees(math.atan2(fw2[0], fw2[2]) - math.atan2(pf[0], pf[2]))
    print(f"   {f:2d} {math.degrees(math.asin(lt2[1])):5.0f} {math.degrees(-math.asin(fw2[1])):5.0f} | {rr:5.0f} {rp:5.0f} | {math.degrees(math.asin(cl[1])):5.0f} | {yaw:5.0f} | scr head {scr(up2):4.0f} chest {scr(cu):4.0f} neckline {scr(nk):4.0f}")
