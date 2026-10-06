import json
p = 'godot/data/content/looks.json'
d = json.load(open(p, encoding='utf-8'))
her = {'cuts': d.pop('herHairs'), 'eyes': d.pop('eyes'), 'paints': d.pop('paints'), 'faces': d.pop('faces'), 'sliders': d.pop('sliders')}
d['heroes'] = {'female': her}

def compact(o):
    return json.dumps(o, ensure_ascii=False, separators=(', ', ': '))

out = ['{']
keys = list(d.keys())
for i, k in enumerate(keys):
    end = ',' if i < len(keys) - 1 else ''
    if k == 'heroes':
        out.append(' "heroes": {')
        hk = list(d['heroes'].keys())
        for j, sex in enumerate(hk):
            out.append(f'  "{sex}": {{')
            parts = list(d['heroes'][sex].keys())
            for m, part in enumerate(parts):
                items = d['heroes'][sex][part]
                out.append(f'   "{part}": [')
                for n, it in enumerate(items):
                    out.append('    ' + compact(it) + (',' if n < len(items) - 1 else ''))
                out.append('   ]' + (',' if m < len(parts) - 1 else ''))
            out.append('  }' + (',' if j < len(hk) - 1 else ''))
        out.append(' }' + end)
    else:
        body = json.dumps(d[k], indent=1, ensure_ascii=False).replace('\n', '\n ')
        out.append(f' "{k}": {body}{end}')
out.append('}')
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
json.load(open(p, encoding='utf-8'))
print('ok')
