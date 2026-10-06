import json, sys
root = sys.argv[1]
p = root + '/data/content/items.json'
d = json.loads(open(p, encoding='utf-8').read())
it = d['items']
def M(stat, kind, value): return {"stat": stat, "kind": kind, "value": value, "source": "item"}
it['leather_cap']['mods'] = [M("armor", "flat", 2), M("maxHealth", "flat", 16)]
it['iron_helm']['mods'] = [M("armor", "flat", 3), M("maxHealth", "flat", 6), M("moveSpeed", "inc", -0.02)]
it['padded_jerkin']['mods'] = [M("armor", "flat", 3), M("maxHealth", "flat", 12)]
it['travelers_cloak']['mods'] = [M("moveSpeed", "inc", 0.03), M("armor", "flat", 3), M("maxHealth", "flat", 12)]
o = json.dumps(d, indent=1, ensure_ascii=False) + '\n'
o = o.replace('"tags": [\n    "mark"\n   ]', '"tags": ["mark"]')
open(p, 'w', encoding='utf-8', newline='\n').write(o)

def sub(path, old, new):
    s = open(root + '/' + path, encoding='utf-8').read()
    assert old in s, (path, old)
    open(root + '/' + path, 'w', encoding='utf-8').write(s.replace(old, new))
print("ok")
