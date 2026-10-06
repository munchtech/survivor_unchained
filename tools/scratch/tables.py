import re, os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot\logic\Content')
w = open('Weapons.cs', encoding='utf-8').read()
b = open('Boons.cs', encoding='utf-8').read()
boon_names = dict(re.findall(r'Id = "([a-z_]+)", Name = "([^"]+)", Icon', b))
kinds = dict(re.findall(r'Id = "([a-z_]+)", Name = "[^"]+", Icon = "[^"]*", Rarity = Rarity\.\w+, Max = \d+, Kind = BoonKind\.(\w+)', b))
# split weapon blocks
blocks = re.split(r'\n        new\(\)\n        \{', w)
rows = []
for blk in blocks[1:]:
    m = re.search(r'Id = "([a-z_]+)", Name = "([^"]+)", School = School\.(\w+), Behavior = WeaponBehavior\.(\w+)', blk)
    if not m: continue
    wid, name, school, beh = m.groups()
    findable = 'Findable = true' in blk.split('Evolutions')[0]
    evos = re.findall(r'new\(\) \{ Id = "([a-z_]+)", Name = "([^"]+)", Description = "[^"]*",\s*Catalysts = \[([^\]]*)\]', blk)
    rows.append((wid, name, school, beh, findable, evos))
print(len([r for r in rows if r[4]]), 'findable weapons;', len(rows) - len([r for r in rows if r[4]]), 'union weapons')
print(sum(len(r[5]) for r in rows), 'evolutions')
print()
print('| Skill | School | Shape | Evolves into (with) |')
print('|---|---|---|---|')
for wid, name, school, beh, f, evos in rows:
    if not f: continue
    parts = []
    for eid, ename, cats in evos:
        cs = [c.strip().strip('"') for c in cats.split(',') if c.strip()]
        parts.append(f"{ename} ({' or '.join(boon_names.get(c, c) for c in cs)})")
    print(f'| {name} | {school} | {beh} | {"; ".join(parts)} |')
print()
from collections import Counter
print(Counter(kinds.values()))
