"""The presets' skins as their portraits ask (tones.py), in looks.json and presets.json, line by line (their layout kept)."""
import re
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
SKIN = {'vixen': 'fair', 'doe': 'rose', 'sunborn': 'brown', 'moonlit': 'fair', 'saffron': 'warm', 'wildling': 'rose', 'hardwon': 'rose'}
for p in (W + r'\godot\data\content\looks.json', W + r'\tools\assets\heroine_face\presets.json'):
    s = open(p, encoding='utf-8').read()
    out = []
    for line in s.split('\n'):
        m = re.search(r'\{"id": "(\w+)", "name"', line)
        if m and m.group(1) in SKIN and '"skin": "' in line:
            line = re.sub(r'"skin": "\w+"', '"skin": "%s"' % SKIN[m.group(1)], line)
        out.append(line)
    s = '\n'.join(out)
    if p.endswith('looks.json'):
        s = s.replace('"id": "brown",\n   "name": "Brown",\n   "color": "#946040"', '"id": "brown",\n   "name": "Brown",\n   "color": "#ba7f5e"')
    open(p, 'w', encoding='utf-8', newline='').write(s)
    print(p, 'done')
