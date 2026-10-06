import json, os, sys
d = json.load(open(os.path.join('godot', 'data', 'content', 'dialogue.json'), encoding='utf-8'))
key = sys.argv[1]
convs = sys.argv[2:]
for cid in convs:
    for nid, n in d[cid]['nodes'].items():
        s = json.dumps(n, ensure_ascii=False)
        if key in s:
            # print the paths
            def walk(x, path):
                if isinstance(x, dict):
                    for k, v in x.items():
                        yield from walk(v, path + [k])
                elif isinstance(x, list):
                    for i, v in enumerate(x):
                        yield from walk(v, path + [str(i)])
                elif isinstance(x, str) and key in x:
                    yield '/'.join(path)
            paths = sorted(set('/'.join(p.split('/')[:3]) for p in walk(n, [])))
            print(f'{cid}.{nid}: {paths}')
