"""Summarise a GLB: counts of meshes, materials, images (with sizes) and distinct mesh/material names."""
import json, struct, sys, collections
for p in sys.argv[1:]:
    f = open(p, 'rb'); f.read(12)
    clen, _ = struct.unpack('<II', f.read(8)); j = json.loads(f.read(clen))
    mats = collections.Counter(m.get('name') for m in j.get('materials', []))
    meshes = collections.Counter((m.get('name') or '').split('_')[0] for m in j.get('meshes', []))
    print('=====', p, 'meshes', len(j.get('meshes', [])), 'materials', len(j.get('materials', [])), 'images', len(j.get('images', [])), 'textures', len(j.get('textures', [])))
    print('  materials:', mats.most_common(30))
    print('  mesh names:', meshes.most_common(30))
    print('  images:', [(i.get('name'), i.get('mimeType'), i.get('uri')) for i in j.get('images', [])][:20])
    print('  node names:', collections.Counter((n.get('name') or '') for n in j.get('nodes', [])).most_common(20))
