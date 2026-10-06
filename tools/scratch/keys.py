import re, json, glob, os
G = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot'
glyphs = json.load(open(os.path.join(G, 'data', 'content', 'glyphs.json')))
src = {}
for f in glob.glob(os.path.join(G, 'logic', '**', '*.cs'), recursive=True) + glob.glob(os.path.join(G, 'src', '**', '*.cs'), recursive=True):
    src[f] = open(f, encoding='utf-8').read()
art = set()
for f, s in src.items():
    for m in re.finditer(r'\b(?:Art|Icon|Glyph)\s*=\s*"([a-z_0-9]+)"', s): art.add(m.group(1))
    for m in re.finditer(r'Glyphs\.(?:Icon|Texture)\("([a-z_0-9]+)"', s): art.add(m.group(1))
    for m in re.finditer(r'\("([a-z_]+)", (?:new Color|Hex|Style\.)', s): pass
# content json icons
for f in glob.glob(os.path.join(G, 'data', 'content', '*.json')):
    if f.endswith('glyphs.json'): continue
    s = open(f, encoding='utf-8').read()
    for m in re.finditer(r'"(?:icon|glyph|art)"\s*:\s*"([a-z_0-9]+)"', s): art.add(m.group(1))
items = set()
d = json.load(open(os.path.join(G, 'data', 'content', 'items.json')))
seq = d if isinstance(d, list) else list(d.values())
for it in seq:
    if isinstance(it, dict) and it.get('icon'): items.add(it['icon'])
print('glyph keys in glyphs.json:', len(glyphs))
used = sorted(art)
print('art/icon keys used in code and content:', len(used))
missing = [k for k in used if k not in glyphs]
print('used but not a glyph (fall back by family):', missing)
print('ITEM ICONS', len(items), sorted(items))
print('USED', used)
