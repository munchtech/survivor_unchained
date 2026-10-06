import json
p = r'C:\Users\munch\.claude\projects\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\subagents\agent-a09e0860794ed3e5c.jsonl'
o = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\my_coord_msgs.txt'
out = open(o, 'w', encoding='utf-8')
seen = set()
keys = ['coordinator', 'From the owner', 'do we have soul', 'vigilant-galileo', 'balance lab', 'story explorer']
for line in open(p, encoding='utf-8'):
    if 'coordinator' not in line and 'owner' not in line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get('type') == 'assistant':
        continue
    # walk all strings
    def walk(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from walk(v)
        elif isinstance(x, list):
            for v in x:
                yield from walk(v)
    for s in walk(d):
        if ('The coordinator sent' in s or 'From the owner' in s or 'standing note' in s) and len(s) < 20000:
            k = s[:300]
            if k in seen:
                continue
            seen.add(k)
            out.write(f'=== {d.get("timestamp")} {d.get("type")}\n{s}\n\n')
print(len(seen))
