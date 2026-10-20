"""anim41 solver 2: build one clip with patched module constants into a scratch folder.
  python drive.py MODULE CLIPFUNC OUTDIR [patch.py ...]   (each patch file is exec'd in the module's namespace)"""
import sys, time
from pathlib import Path
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import importlib  # noqa
from keyed import Rig  # noqa
from rig import DATA, Skeleton, write_clip  # noqa
mod, fn, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
sk = Skeleton.load(DATA / 'heroine_skeleton.json'); rig = Rig(sk, body='her')
M = importlib.import_module(f'clips.{mod}')
for pf in sys.argv[4:]:
    exec(Path(pf).read_text(), M.__dict__)
t0 = time.time()
clip = getattr(M, fn)(rig)
write_clip(clip, sk, out)
print(f'{clip.name} {clip.frames} frames -> {out} ({time.time() - t0:.1f} s)')
