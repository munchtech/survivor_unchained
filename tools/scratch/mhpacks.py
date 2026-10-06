"""MakeHuman asset licence metadata from MPFB's pack index, for the named assets."""
import json, glob, sys
D = r"C:\Users\munch\AppData\Roaming\Blender Foundation\Blender\4.5\extensions\.user\user_default\mpfb\data\packs"
want = set(sys.argv[1:])
for f in glob.glob(D + r'\*.json'):
    j = json.load(open(f, encoding='utf-8'))
    for k, v in j.items():
        if not want or k in want:
            print(f.split('\\')[-1], k, {x: v.get(x) for x in ('author', 'license', 'source', 'original_author', 'original_source', 'created')})
