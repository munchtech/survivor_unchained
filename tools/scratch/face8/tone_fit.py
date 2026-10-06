"""tone_fit.py TAG: each face's skin under the white rig (TAG_w_<id>.png; hers TAG_white.png) against its portrait,
every portrait scaled by one number (hers lit as her portrait is, lightness for lightness): the factor each skin tone
needs, per channel in linear light, and the swatch colours (looks.json) and her own tone (People.SkinTone) that give it.
Run with the facefit venv's python."""
import json, sys
import numpy as np
from skin_sample import measure

tag = sys.argv[1]
w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
g = w + r'\godot\.shots'
s4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
crop = [660, 150, 1160, 740]
LW = np.array([0.2126, 0.7152, 0.0722])
P = json.load(open(w + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))
looks = json.load(open(w + r'\godot\data\content\looks.json', encoding='utf-8'))
sw = {s['id']: s['color'] for s in looks['skins']}


def lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(l):
    l = np.clip(np.asarray(l, float), 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def ease(c):
    """People.SkinTone: a chosen tone eased toward white, the less the darker it is."""
    a = 0.35 * np.clip((c @ LW) * 1.1, 0.25, 1)
    return c + (1 - c) * a


def unease(t):
    c = t.copy()
    for _ in range(50):
        a = 0.35 * np.clip((c @ LW) * 1.1, 0.25, 1)
        c = np.clip((t - a) / (1 - a), 0, 1)
    return c


OWN = np.array([1.0, 0.93, 0.87])
res = {}
for p in P:
    ref = s4 + (r'\from_face3\refs_her\her_23.png' if p['id'] == 'own' else '\\refs_front\\' + p['ref'].split('/')[-1] + '.png')
    shot = g + ('\\%s_white.png' % tag if p['id'] == 'own' else '\\%s_w_%s.png' % (tag, p['id']))
    a, b = measure(ref), measure(shot, crop)
    if a is None or b is None:
        print(p['id'], 'no face'); continue
    res[p['id']] = (np.array(a['lin']), np.array(b['lin']), p['skin'])
K = (res['own'][1] @ LW) / (res['own'][0] @ LW)
print('her white-rig lightness against her portrait: %.3f (every portrait scaled by it)' % K)
need = {}
for k, (a, b, skin) in res.items():
    f = a * K / b
    need.setdefault(skin, []).append(f)
    print('%-9s %-6s factor r %.3f g %.3f b %.3f   L %.3f' % (k, skin, *f, ((a * K) @ LW) / (b @ LW)))
print()
for skin, fs in need.items():
    f = np.exp(np.mean(np.log(fs), 0))
    cur = OWN if not sw.get(skin) else ease(hexrgb(sw[skin]))
    new_t = srgb(lin(cur) * f)
    if not sw.get(skin):
        print('%-6s (her own tone) %s -> %s   (factor %s)' % (skin, np.round(cur, 3), np.round(new_t, 3), np.round(f, 3)))
    else:
        c = unease(new_t)
        print('%-6s %s -> #%02x%02x%02x   (factor %s)' % (skin, sw[skin], *(np.round(c * 255).astype(int)), np.round(f, 3)))
