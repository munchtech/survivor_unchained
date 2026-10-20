"""build a clip from clips.actions (or run) with a patch: python fb.py CLIPFN TAG PATCH.py [module]"""
import sys, importlib
from pathlib import Path
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
from keyed import Rig
from rig import DATA, Skeleton, write_clip
fn, tag, patch = sys.argv[1], sys.argv[2], sys.argv[3]
M = importlib.import_module(sys.argv[4] if len(sys.argv) > 4 else 'clips.actions')
exec(open(patch).read(), M.__dict__)
sk = Skeleton.load(DATA / 'heroine_skeleton.json'); rig = Rig(sk, body='her')
clip = getattr(M, fn)(rig)
out = Path(__file__).resolve().parent / 'x' / tag; write_clip(clip, sk, out); print('wrote', out)
