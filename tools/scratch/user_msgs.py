"""Extract the user-role messages (the coordinator's and the owner's relayed
words) from this session's transcript, in order."""
import json, sys
p = r'C:\Users\munch\.claude\projects\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3.jsonl'
out = sys.argv[1]
msgs = []
for line in open(p, encoding='utf-8'):
    try:
        o = json.loads(line)
    except Exception:
        continue
    if o.get('type') != 'user' or o.get('isSidechain'):
        continue
    m = o.get('message', {})
    c = m.get('content')
    texts = []
    if isinstance(c, str):
        texts.append(c)
    elif isinstance(c, list):
        for part in c:
            if isinstance(part, dict) and part.get('type') == 'text':
                texts.append(part.get('text', ''))
    for t in texts:
        if t.startswith('<task-notification>') or 'tool_result' in t[:40]:
            continue
        if len(t) < 40:
            continue
        msgs.append((o.get('timestamp', ''), t))
with open(out, 'w', encoding='utf-8') as f:
    for ts, t in msgs:
        f.write('=' * 30 + ' ' + ts + '\n' + t + '\n')
print(len(msgs))
