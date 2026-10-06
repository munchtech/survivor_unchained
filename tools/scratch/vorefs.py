"""For each voice reference clip, say how casting.json and cast.json describe its origin (design, seed, or 'from' another part)."""
import json, os, sys
root = sys.argv[1]
refs = sorted(f[:-5] for f in os.listdir(os.path.join(root, 'refs')) if f.endswith('.flac'))
casting = json.load(open(os.path.join(root, 'refs', 'casting.json'), encoding='utf-8'))
cast = json.load(open(os.path.join(root, 'cast.json'), encoding='utf-8'))
cast = cast.get('voices', cast) if isinstance(cast, dict) else cast
for r in refs:
    base = r.split('.')[0]
    c = casting.get(base, {})
    v = cast.get(base, {}) if isinstance(cast, dict) else {}
    keys = sorted(v.keys()) if isinstance(v, dict) else []
    design = (v.get('design') or v.get('voice') or v.get('prompt') or '') if isinstance(v, dict) else ''
    print(f"{r:22s} seed={c.get('seed')} from={c.get('from')} cast_keys={keys} design={str(design)[:70]!r}")
