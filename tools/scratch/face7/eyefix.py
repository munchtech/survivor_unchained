"""eyefix.py SHOTS_JSON LIGHT_NOW LIGHT_NEW [write]: each eye colour's dye scaled, channel by channel, by what its irises
want (the portraits' iris over their cheek, on her game cheek) over what the game showed (iris_sample.py's JSON of
the presets' shots); moss by iris_light. One step of a fixed point: shoot again and repeat."""
import json
import re
import sys
import numpy as np

W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
F5 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
shots = json.load(open(sys.argv[1]))
light_now, light_new = float(sys.argv[2]), float(sys.argv[3])
write = 'write' in sys.argv[4:]


def lin(h):
    c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def hexc(l):
    l = np.clip(l, 0, 1)
    s = np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in s)


refs = json.load(open(F5 + r'\iris_refs.json'))
ref = {k.replace('\\', '/').split('/')[-1].split('_')[0]: v for k, v in refs.items()}
game = {}
for k, v in shots.items():
    n = k.replace('\\', '/').split('/')[-1].split('@')[0].split('.')[0]
    n = n.split('_p_')[-1] if '_p_' in n else 'her'
    if v and v['r'] and v['l']:
        game[n] = v
cheek_her_game = lin(game['her']['cheek'])
cheek_her_ref = lin(ref['her']['cheek'])
USE = {'moss': ['her'], 'frost': ['highborn', 'fey'], 'flint': ['vixen', 'hardwon'], 'sloe': ['sunborn', 'moonlit'],
       'peat': ['doe', 'saffron'], 'hazel': ['wildling']}
iris = lambda d: (lin(d['r']['iris']) + lin(d['l']['iris'])) / 2
p = W + r'\godot\data\content\looks.json'
s = open(p, encoding='utf-8').read()
for eye, who in USE.items():
    who = [w for w in who if w in game]
    if not who:
        continue
    want = np.mean([iris(ref[w]) / cheek_her_ref * cheek_her_game for w in who], 0)
    got = np.mean([iris(game[w]) for w in who], 0)
    k = want / got
    if 'lum' in sys.argv:
        # (by lightness alone, keeping the dye's own hue: channel by channel, a near-black iris's
        # channels are mostly the cornea's sheen, and their ratios swung its hue to green)
        k = np.full(3, (want @ [0.2126, 0.7152, 0.0722]) / (got @ [0.2126, 0.7152, 0.0722]))
    print("%-6s wants %s, shows %s: x %s" % (eye, hexc(want), hexc(got), np.round(k, 3)))
    if eye == 'moss':
        print("   iris_light for moss: %.3f" % (light_now * (want @ [0.2126, 0.7152, 0.0722]) / (got @ [0.2126, 0.7152, 0.0722])))
        continue
    m = re.search(r'\{"id": "%s", "name": "[^"]+", "color": "(#\w+)", "ring": "(#\w+)"\}' % eye, s)
    ni, nr = hexc(lin(m.group(1)) * k * light_now / light_new), hexc(lin(m.group(2)) * k * light_now / light_new)
    print("   %s/%s -> %s/%s" % (m.group(1), m.group(2), ni, nr))
    if write:
        s = s.replace(m.group(0), m.group(0).replace('"color": "%s"' % m.group(1), '"color": "%s"' % ni).replace('"ring": "%s"' % m.group(2), '"ring": "%s"' % nr))
if write:
    open(p, 'w', encoding='utf-8', newline='').write(s)
    print("written")
