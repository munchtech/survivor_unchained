"""Print each glTF/GLB's asset block (generator, copyright, extras) and node names."""
import json, struct, sys, os
for p in sys.argv[1:]:
    try:
        if p.endswith('.glb'):
            f = open(p, 'rb'); f.read(12)
            clen, ctype = struct.unpack('<II', f.read(8)); j = json.loads(f.read(clen))
        else:
            j = json.load(open(p, encoding='utf-8'))
    except Exception as e:
        print(p, 'ERR', e); continue
    a = j.get('asset', {})
    names = [n.get('name') for n in j.get('nodes', [])][:6]
    imgs = [i.get('name') or i.get('uri') for i in j.get('images', [])][:6]
    print(os.path.basename(p), '|', a.get('generator'), '|', a.get('copyright'), '|', a.get('extras'), '|', j.get('extras'), '| nodes', names, '| imgs', imgs)
