"""Print the __metadata__ block of safetensors files (licence, author, training notes)."""
import json, struct, sys, os
for p in sys.argv[1:]:
    with open(p, 'rb') as f:
        n = struct.unpack('<Q', f.read(8))[0]
        h = json.loads(f.read(n))
    m = h.get('__metadata__', {})
    print('=====', os.path.basename(p), len(m), 'keys')
    for k, v in m.items():
        s = str(v)
        if k in ('ss_tag_frequency', 'ss_dataset_dirs', 'ss_bucket_info'):
            s = s[:300]
        print(' ', k, ':', s[:600])
