"""anim42 solver 3: stance and finish numbers per frame.  python stm.py CLIP [--folder DIR] [--play IDLE] [--frames a-b] [--key viking_axe@hand_r]
spread: ankle gap / shoulder gap; lfwd: left ankle ahead of the right (cm, along her hips' forward);
kneeL/R: knee bend (deg); knock: knee inside the ankle-ball line (cm, + = knock-kneed);
pelv: pelvis yaw (deg, + = turned toward her left, into the forehand); chest: chest yaw (same);
hinge: pelvis->neck lean forward from upright (deg); hr: right wrist from pelvis (cm, x left, y up, z fwd, in root space);
elL: left elbow (deg, 180 straight); lback: left upper arm swung behind the chest's plane (deg, + back);
head: axe head from pelvis (cm); hpitch: haft below level (deg); clr: axe head to left leg on screen (cm, cam 45/20)."""
import sys, json, math, argparse
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa

ap = argparse.ArgumentParser()
ap.add_argument('clip'); ap.add_argument('--folder'); ap.add_argument('--play'); ap.add_argument('--frames')
ap.add_argument('--key', default='viking_axe@hand_r'); ap.add_argument('--cam', type=float, default=45)
ap.add_argument('--pitch', type=float, default=20)
a = ap.parse_args()
label, folder, skel = A.SETS[0]
folder = Path(a.folder) if a.folder else folder
sk = A.Skeleton.load(A.DATA / skel); I = sk.index
d, rot, pos = A.load(folder / f'{a.clip}.json', sk)
if a.play:
    _, ir, ip = A.load(ANIM / 'out/clips' / f'{a.play}.json', sk)
    for name, j in I.items():
        if name in ('root', 'pelvis') or name.startswith(('thigh', 'calf', 'foot', 'ball', 'glute')):
            rot[:, j] = ir[0, j]; pos[:, j] = ip[0, j]
g, p = sk.fk(rot, pos)
gr, pr = sk.rest_globals(); pr = pr[0]
shw = np.linalg.norm(pr[I['upperarm_l']] - pr[I['upperarm_r']])
arms = json.load(open(ANIM / 'data/arms_local.json'))
key = a.key if a.key in arms else None
if key:
    hb = I[key.split('@')[1]]
    v = np.array(arms[key]['v']); r = np.linalg.norm(v, axis=1); head_l = v[r > r.max() - 0.12].mean(0)
ca, cp = math.radians(a.cam), math.radians(a.pitch)
cam = np.array([math.sin(ca) * math.cos(cp), math.sin(cp), math.cos(ca) * math.cos(cp)])
right = np.cross(-cam, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, -cam)
P = lambda f, n: p[f, I[n]]
def yaw(l, r):
    dv = l - r
    return math.degrees(math.atan2(r[2] - l[2], dv[0]))
def ang(a_, b, c):
    u, w = a_ - b, c - b
    return math.degrees(math.acos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))
def segd(x, s0, s1):
    t = np.clip((x - s0) @ (s1 - s0) / ((s1 - s0) @ (s1 - s0)), 0, 1); return np.linalg.norm(x - s0 - t * (s1 - s0))
fr = range(rot.shape[0])
if a.frames:
    s, e = a.frames.split('-'); fr = range(int(s), int(e) + 1)
print(f"{a.clip} {'over ' + a.play if a.play else 'own legs'}  shoulder gap {shw*100:.0f} cm")
print(' f spread lfwd kneeL kneeR knockL knockR pelv chest hinge  hr(cm)        elL lback  head(cm)        hpitch clr')
for f in fr:
    pv = P(f, 'pelvis')
    tl, tr = P(f, 'thigh_l'), P(f, 'thigh_r')
    al, ar = P(f, 'foot_l'), P(f, 'foot_r')
    fwd = np.array([-(tr[2] - tl[2]), 0, 0]); hx = (tl - tr); hx[1] = 0; hx /= np.linalg.norm(hx)
    hz = np.cross(hx, [0, 1, 0])
    gap = abs((al - ar)[0])
    lf = (al - ar)[2] * 100
    out = [f"{f:2d}", f"{gap / shw:5.2f}", f"{lf:4.0f}"]
    for s in 'lr':
        out.append(f"{180 - ang(P(f, 'thigh_' + s), P(f, 'calf_' + s), P(f, 'foot_' + s)):5.0f}")
    for s, sg in (('l', 1), ('r', -1)):
        k, an, bl = P(f, 'calf_' + s), P(f, 'foot_' + s), P(f, 'ball_' + s)
        mid = (an + bl) / 2; hp_ = P(f, 'thigh_' + s)
        t = (k[1] - hp_[1]) / (mid[1] - hp_[1]); ln = hp_ + t * (mid - hp_)
        out.append(f"{-sg * (k[0] - ln[0]) * 100:6.1f}")
    out.append(f"{yaw(tl, tr):5.0f}")
    out.append(f"{yaw(P(f, 'upperarm_l'), P(f, 'upperarm_r')):5.0f}")
    nk = P(f, 'neck_01') - pv
    hzc = np.cross([1, 0, 0], [0, 1, 0]); hzc = np.array([0, 0, 1.0])
    # lean in the hips' facing plane
    zf = hz; out.append(f"{math.degrees(math.atan2(nk @ zf, nk[1])):5.0f}")
    out.append(f"{np.round((P(f, 'hand_r') - pv) * 100).astype(int)!s:14}")
    out.append(f"{ang(P(f, 'upperarm_l'), P(f, 'lowerarm_l'), P(f, 'hand_l')):4.0f}/{ang(P(f, 'upperarm_r'), P(f, 'lowerarm_r'), P(f, 'hand_r')):3.0f}")
    ua_ = P(f, 'lowerarm_l') - P(f, 'upperarm_l'); cx_ = P(f, 'upperarm_l') - P(f, 'upperarm_r'); cx_ /= np.linalg.norm(cx_)
    out.append(f"abdL {math.degrees(math.asin(np.clip(ua_ @ cx_ / np.linalg.norm(ua_), -1, 1))):3.0f}")
    cx = P(f, 'upperarm_l') - P(f, 'upperarm_r'); cx[1] = 0; cx /= np.linalg.norm(cx); cz = np.cross(cx, [0, 1, 0])
    ua = P(f, 'lowerarm_l') - P(f, 'upperarm_l')
    out.append(f"{math.degrees(math.atan2(-(ua @ cz), -ua[1])):5.0f}")
    if key:
        hp = p[f, hb]; head = hp + A.qrot(g[f, hb], head_l); dv = (head - hp) / np.linalg.norm(head - hp)
        out.append(f"{np.round((head - pv) * 100).astype(int)!s:15}")
        out.append(f"{math.degrees(math.asin(-dv[1])):5.0f}")
        sp = lambda x: np.array([x @ right, x @ up])
        legpts = [sp(P(f, n)) for n in ('thigh_l', 'calf_l', 'foot_l')]
        hs = sp(head)
        dmin = min(segd(hs, legpts[0], legpts[1]), segd(hs, legpts[1], legpts[2]))
        out.append(f"{(dmin - 0.07) * 100:4.0f}")
    sp = lambda x: np.array([x @ right, x @ up])
    th = sp((P(f, 'thigh_l') + P(f, 'calf_l')) / 2); hrs = sp(P(f, 'hand_r'))
    out.append(f" hr-thL scr {np.round((hrs - th) * 100).astype(int)}")
    print(' '.join(out))
