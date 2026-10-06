import json, sys
p = r'C:\Users\munch\.claude\projects\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3.jsonl'
key = sys.argv[1]
out = sys.argv[2]
seen = set()
res = []
for line in open(p, encoding='utf-8'):
    if key not in line:
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue

    def walk(x):
        if isinstance(x, str):
            if key in x and len(x) > 1500 and x[:300] not in seen:
                seen.add(x[:300])
                yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from walk(v)
        elif isinstance(x, list):
            for v in x:
                yield from walk(v)
    for s in walk(o):
        res.append(s)
with open(out, 'w', encoding='utf-8') as f:
    for s in res:
        f.write('=' * 40 + ' %d\n' % len(s))
        f.write(s)
        f.write('\n')
print(len(res), [len(s) for s in res])
