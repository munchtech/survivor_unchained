import json, os
d0 = r"C:\Users\munch\AppData\Roaming\Godot\app_userdata\Survivor Unchained\saves"
for f in sorted(os.listdir(d0)):
    if not f.startswith("slot"): continue
    p = os.path.join(d0, f)
    d = json.load(open(p, encoding='utf-8'))
    ch = d['character']
    print(f, os.path.getsize(p), 'v', d.get('version'), 'day', d['world'].get('day'), 'lvl', ch.get('level'), 'arch', ch.get('archetype'))
    print('  pack', [(x['def'], x.get('qty', 1)) for x in ch['pack'] if x])
    print('  mats', ch.get('materials'))
    print('  equip', {k: v['def'] for k, v in ch['equipment'].items() if v})
