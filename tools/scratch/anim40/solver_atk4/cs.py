"""solver 4: build chain_strike with arts' module values patched (a python file exec'd in clips.arts), to x/TAG.
python cs.py TAG PATCH.py"""
import sys
from pathlib import Path
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
from keyed import Rig
from rig import DATA, Skeleton, write_clip
import clips.arts as M
tag, patch = sys.argv[1], sys.argv[2]
exec(open(patch).read(), M.__dict__)
sk = Skeleton.load(DATA / 'heroine_skeleton.json'); rig = Rig(sk, body='her')
clip = M.chain_strike(rig)
out = Path(__file__).resolve().parent / 'x' / tag; write_clip(clip, sk, out); print('wrote', out)
