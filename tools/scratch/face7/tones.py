"""The skin tones the presets want: each portrait's skin against hers, as a tone on her fair paint."""
import json
import sys
import numpy as np

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'skin_d1.json'))
tag = sys.argv[2] if len(sys.argv) > 2 else 'd1'


def S(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)


def hx(l):
    return '#%02x%02x%02x' % tuple(int(round(v * 255)) for v in S(l))


def srgb2lin(c):
    c = np.array(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


refs, game = {}, {}
for k, v in d.items():
    if v is None:
        continue
    n = k.replace('/', '\\').split('\\')[-1].split('@')[0]
    if n.startswith(tag + '_u_'):
        continue
    if n.startswith(tag + '_'):
        game[n[len(tag) + 1:].split('.')[0].replace('p_', '')] = np.array(v['lin'])
    else:
        refs[n.split('_')[0]] = np.array(v['lin'])
refs['long'] = refs.pop('her')
pal = {'fair': None, 'rose': '#f0b8a0', 'warm': '#e0a47c', 'olive': '#c4945e', 'brown': '#946040', 'deep': '#5e3c2a'}


def tone(h):
    if h is None:
        return srgb2lin([1.0, 0.93, 0.87])
    c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return srgb2lin(c + (1 - c) * 0.35 * np.clip(lum * 1.1, 0.25, 1))


T = {k: tone(v) for k, v in pal.items()}
for k, v in T.items():
    print('tone %-6s %s' % (k, hx(v)))
use = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {'long': 'fair', 'highborn': 'fair', 'vixen': 'rose', 'doe': 'olive', 'sunborn': 'deep',
                                                          'moonlit': 'warm', 'saffron': 'brown', 'wildling': 'warm', 'hardwon': 'warm', 'fey': 'fair'}
for k in ['long', 'highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']:
    if k not in game:
        continue
    want = T['fair'] * refs[k] / refs['long']
    # (what the tone it has gives, against what the portrait asks: the game's skin over hers, per channel)
    print('%-9s portrait/her %s game/her %s | tone %s (%s) wants %s' % (
        k, np.round(refs[k] / refs['long'], 2), np.round(game[k] / game['long'], 2), hx(T[use[k]]), use[k], hx(want)))
