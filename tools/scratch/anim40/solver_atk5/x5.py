"""solver 5a: build CLIP with the finish keys (clav_r (6,14)) overridden; JSON keys: any pose kwarg (absolute),
plus hand, blade, dspine, dhips. Writes x/TAG/CLIP.json.  python x5.py CLIP TAG JSON"""
import sys, json
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
from keyed import Rig
from rig import DATA, Skeleton, write_clip
import clips.axe as X
clipname, tag, ov = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
if 'sub' in ov:
    src = (ANIM / 'clips/axe.py').read_text()
    for a, b in ov.pop('sub'):
        assert a in src, a
        src = src.replace(a, b)
    exec(compile(src, str(ANIM / 'clips/axe.py'), 'exec'), X.__dict__)
orig = X.pose
def pose(hips_yaw, spine_yaw, hand, blade, pole=(-0.7, -0.5, -0.3), **kw):
    if tuple(kw.get('clav_r', (4, 6))) == (6, 14):
        o = dict(ov)
        spine_yaw += o.pop('dspine', 0); hips_yaw += o.pop('dhips', 0)
        if 'hand' in o: hand = tuple(o.pop('hand'))
        if 'blade' in o: blade = X._n(*o.pop('blade'))
        if 'pole' in o: pole = tuple(o.pop('pole'))
        for k, v in o.items(): kw[k] = tuple(v) if isinstance(v, list) else v
    return orig(hips_yaw, spine_yaw, hand, blade, pole=pole, **kw)
X.pose = pose
sk = Skeleton.load(DATA / 'heroine_skeleton.json'); rig = Rig(sk, body='her')
clip = getattr(X, clipname)(rig); clip.name = clipname
out = Path(__file__).resolve().parent / 'x' / tag
write_clip(clip, sk, out)
