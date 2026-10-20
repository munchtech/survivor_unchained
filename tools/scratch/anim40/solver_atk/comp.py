"""Play-true composites (PlayerView --hold's upperShot): each clip with root, pelvis and legs from IDLE's frame 0.
  python comp.py OUTDIR IDLE clip [clip ...]   (reads tools/anim/out/clips)"""
import sys, json
from pathlib import Path
ANIM = Path(__file__).resolve().parents[3] / 'anim'
out, idle, names = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
out.mkdir(parents=True, exist_ok=True)
legs = lambda b: b in ('root', 'pelvis') or b.startswith(('thigh', 'calf', 'foot', 'ball', 'glute'))
it = json.loads((ANIM / 'out/clips' / f'{idle}.json').read_text())
first = {(t['bone'], t['type']): t['keys'][0] for t in it['tracks'] if legs(t['bone'])}
for n in names:
    d = json.loads((ANIM / 'out/clips' / f'{n}.json').read_text())
    nf = len(d['tracks'][0]['keys'])
    d['tracks'] = [t for t in d['tracks'] if not legs(t['bone'])]
    d['tracks'] += [{'bone': b, 'type': ty, 'keys': [k] * nf} for (b, ty), k in first.items()]
    (out / f'{n}.json').write_text(json.dumps(d))
    print(out / f'{n}.json')
