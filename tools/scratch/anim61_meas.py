"""Build flare_long_cut (no pack), write it, and print per-frame geometry."""
import sys, time, math, pickle
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-61\tools\anim")
import numpy as np
from keyed import Rig
from rig import Skeleton, DATA, qrot, write_clip
import build as B
from clips import flare_long_cut as M
from keyed import Rig as _R
rec = []
_st, _so = _R._strain, _R.solve
def _strain(self, d_la, want, ha, fa, side):
    r = _st(self, d_la, want, ha, fa, side)
    self._raw = getattr(self, "_raw", {}); self._raw[side] = r[0]
    return r
def _solve(self, pose, base=None):
    self._raw = {}
    out = _so(self, pose, base=base)
    rec.append(dict(self._raw))
    return out
_R._strain, _R.solve = _strain, _solve
_set = M._settle
def _settle(rig, clip):
    global REC
    REC = rec[-(M.END + 1):]
    return _set(rig, clip)
M._settle = _settle
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
t0 = time.time()
clip = M.flare_long_cut(rig)
print("built", round(time.time() - t0, 1), "s")
write_clip(clip, sk, B.OUT)
g, p = sk.fk(clip.rot, clip.pos)
I = rig.I
hr, hl = I["hand_r"], I["hand_l"]
fr_list = sys.argv[1:] and [int(x) for x in sys.argv[1].split(",")] or range(clip.frames)
print("fr  P(x y z)              dErr  tip(x y z)            Lline Lang  kneeR(y z)   ballL(y)  ballR(y)  pel_y  twL twR")
for f in fr_list:
    P = p[f, hr] + qrot(g[f, hr], M.AT); d = qrot(g[f, hr], M.DIR)
    Pk, dk = M._blade_at(f)[:2]
    tip = P + d * M.BLADE_LEN
    Q = p[f, hl] + qrot(g[f, hl], M.AT_L); dl = qrot(g[f, hl], M.DIR_L)
    v = Q - P; off = v - d * float(v @ d)
    ang = math.degrees(math.acos(max(-1, min(1, float(dl @ d)))))
    kn = p[f, I["calf_r"]]
    print(f"{f:2d} {P[0]:6.3f} {P[1]:5.3f} {P[2]:6.3f}  {math.degrees(math.acos(max(-1,min(1,float(d@dk))))):5.1f}  "
          f"{tip[0]:6.3f} {tip[1]:6.3f} {tip[2]:6.3f}  {np.linalg.norm(off)*1000:5.1f} {ang:5.1f}  "
          f"{kn[1]:5.3f} {kn[2]:6.3f}  {p[f, I['ball_l']][1]:6.3f} {p[f, I['ball_r']][1]:6.3f}  {p[f, I['pelvis']][1]:5.3f} {REC[f].get('l', float('nan')):5.0f} {REC[f].get('r', float('nan')):5.0f}")

# anim61: posture (sagittal, +z down the line): trunk lean (pelvis->neck, + forward), chest (spine_03 up axis tilt),
# head up-axis tilt (bow, + forward), the blade from vertical, crown margin over the shoulders on a 55-deg-down camera
# (front: the camera ahead looking back at her; back: behind her; side), knee bends, stance (ball z gap).
from rig import qmul, qinv
def tilt(v):
    return math.degrees(math.atan2(v[2], v[1]))
def upax(f, j):
    q = qmul(g[f, j], qinv(rig.grest[j])); return qrot(q, np.array([0, 1.0, 0]))
def bend(f, a, b, c):
    u = p[f, b] - p[f, a]; w = p[f, c] - p[f, b]
    return math.degrees(math.acos(max(-1, min(1, float(u @ w) / np.linalg.norm(u) / np.linalg.norm(w)))))
th = math.radians(55)
cams = {"front": np.array([0, math.cos(th), -math.sin(th)]), "back": np.array([0, math.cos(th), math.sin(th)]),
        "side": np.array([math.sin(th), math.cos(th), 0])}
print("fr trunk chest  head  bladeV  P(y z)        crown-shoulder mm (front back side)  neck_y  kneeL kneeR stance hips_y  tipZ")
for f in fr_list:
    pel, nk, hd = p[f, I["pelvis"]], p[f, I["neck_01"]], p[f, I["Head"]]
    hu = upax(f, I["Head"]); crown = hd + hu * 0.17
    sh = [p[f, I[n]] for n in ("clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "spine_03", "neck_01")]
    mg = [1000 * (float(crown @ u) - max(float(s @ u) for s in sh)) for u in cams.values()]
    P = p[f, hr] + qrot(g[f, hr], M.AT); d = qrot(g[f, hr], M.DIR)
    tip = P + d * M.BLADE_LEN
    bv = math.degrees(math.acos(max(-1, min(1, -float(d[1])))))
    print(f"{f:2d} {tilt(nk - pel):5.1f} {tilt(upax(f, I['spine_03'])):5.1f} {tilt(hu):5.1f}  {bv:5.1f}  {P[1]:5.3f} {P[2]:6.3f}   "
          f"{mg[0]:6.0f} {mg[1]:6.0f} {mg[2]:6.0f}   {nk[1]:5.3f}  {bend(f, I['thigh_l'], I['calf_l'], I['foot_l']):5.1f} "
          f"{bend(f, I['thigh_r'], I['calf_r'], I['foot_r']):5.1f} {p[f, I['ball_l']][2] - p[f, I['ball_r']][2]:6.3f} {pel[1]:5.3f} {tip[2]:6.3f}  elbX {p[f, I['lowerarm_l']][0]:6.3f} {p[f, I['lowerarm_r']][0]:6.3f} tip {tip[0]:6.3f} {tip[1]:6.3f} shY {p[f, I['upperarm_l']][1]:5.3f} {p[f, I['upperarm_r']][1]:5.3f}")
