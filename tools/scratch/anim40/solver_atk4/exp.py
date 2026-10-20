"""solver 4: build axe clips with the finish keys (clav_r forward >= 20) overridden, to solver_atk4/x/.
python exp.py CLIP TAG '{"clav":[4,12],"dspine":4,"dhips":0,"dhand":[0,0,0.05],"pole":[-0.9,-0.6,0.4],"dpitch":0,"dhinge":0}'"""
import sys, json
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
from keyed import Rig
from rig import DATA, Skeleton, write_clip
import clips.axe as X
clipname, tag, ov = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
orig = X.pose
def pose(hips_yaw, spine_yaw, hand, blade, pole=(-0.7, -0.5, -0.3), **kw):
    c = kw.get('clav_r', (4, 6))
    if tuple(c) == (6, 14):
        if 'clav' in ov: kw['clav_r'] = tuple(ov['clav'])
        spine_yaw += ov.get('dspine', 0); hips_yaw += ov.get('dhips', 0)
        hand = tuple(np.add(hand, ov.get('dhand', (0, 0, 0))))
        if 'pole' in ov: pole = tuple(ov['pole'])
        kw['pitch'] = kw.get('pitch', 12) + ov.get('dpitch', 0); kw['hinge'] = kw.get('hinge', 8) + ov.get('dhinge', 0)
        if 'blade' in ov: blade = X._n(*ov['blade'])
    p = orig(hips_yaw, spine_yaw, hand, blade, pole=pole, **kw)
    if tuple(c) == (6, 14) and ov.get('pole_at'):
        p['hand_r']['pole_at'] = 'shoulder'
    if tuple(c) == (6, 14) and ov.get('dcrouch'):
        x, y, z = p['hips']['pos']; p['hips']['pos'] = (x, y - ov['dcrouch'], z)
    return p
X.pose = pose
sk = Skeleton.load(DATA / 'heroine_skeleton.json'); rig = Rig(sk, body='her')
clip = getattr(X, clipname)(rig); clip.name = f'{clipname}'
out = Path(__file__).resolve().parent / 'x' / tag
write_clip(clip, sk, out); print('wrote', out / f'{clipname}.json')
