import json, os, sys
d = json.load(open(os.path.join('godot', 'data', 'content', 'dialogue.json'), encoding='utf-8'))
pats = sys.argv[1:]
for cid, c in d.items():
    for nid, n in c['nodes'].items():
        texts = []
        t = n.get('text')
        if isinstance(t, str):
            texts.append(('text', t))
        elif isinstance(t, list):
            for i, v in enumerate(t):
                texts.append((f'text#{i}', v.get('text', '')))
        for j, ch in enumerate(n.get('choices') or []):
            ct = ch.get('text')
            if isinstance(ct, str):
                texts.append((f'choice{j}', ct))
            elif isinstance(ct, list):
                for i, v in enumerate(ct):
                    texts.append((f'choice{j}#{i}', v.get('text', '')))
            if ch.get('locked'):
                texts.append((f'choice{j}.locked', ch['locked']))
        for where, tx in texts:
            for ptn in pats:
                if ptn.lower() in tx.lower():
                    print(f'{cid}.{nid} [{where}] ({ptn}): {tx}')
