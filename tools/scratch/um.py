import json, sys
p = r'C:\Users\munch\.claude\projects\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\subagents\agent-a09e0860794ed3e5c.jsonl'
o = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\my_user_msgs.txt'
out = open(o, 'w', encoding='utf-8')
n = 0
for line in open(p, encoding='utf-8'):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get('type') != 'user':
        continue
    m = d.get('message', {})
    c = m.get('content')
    texts = []
    if isinstance(c, str):
        texts = [c]
    elif isinstance(c, list):
        for x in c:
            if isinstance(x, dict) and x.get('type') == 'text':
                texts.append(x['text'])
    for t in texts:
        if len(t) < 40:
            continue
        n += 1
        out.write(f'=== {n} {d.get("timestamp")}\n{t}\n\n')
print(n)
