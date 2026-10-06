"""Write a safetensors file's embedded 'license' metadata to a text file."""
import json, struct, sys
p, out = sys.argv[1], sys.argv[2]
with open(p, 'rb') as f:
    n = struct.unpack('<Q', f.read(8))[0]
    h = json.loads(f.read(n))
open(out, 'w', encoding='utf-8').write(h.get('__metadata__', {}).get('license', ''))
print(len(h.get('__metadata__', {}).get('license', '')), 'chars')
