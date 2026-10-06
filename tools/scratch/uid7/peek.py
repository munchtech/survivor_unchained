import json, glob, os
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qa_saves')
for f in sorted(glob.glob(os.path.join(D, '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    keys = list(d.keys())
    w = d.get('world') or d.get('World') or {}
    c = d.get('character') or d.get('Character') or {}
    q = w.get('quests') or w.get('Quests') or {}
    npcs = w.get('npcs') or w.get('Npcs') or {}
    met = [k for k, v in npcs.items() if (v.get('flags') or v.get('Flags') or {}).get('met')]
    hist = w.get('history') or w.get('History') or []
    print(os.path.basename(f), 'day', w.get('day') or w.get('Day'), 'lvl', c.get('level') or c.get('Level'), 'quests', len(q), 'met', len(met), 'history', len(hist), 'ver', d.get('version') or d.get('Version'), 'zone', (d.get('location') or d.get('Location') or {}).get('zone'))
