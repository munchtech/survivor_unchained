"""set_eyes.py TAG LIGHT: the presets' eye colours (looks.json) dyed as eyecal.py found they must be for their irises
to stand to her skin as the portraits' do, each colour's ring kept as it stood to its iris; LIGHT the iris_light they
are for (the calibration's albedo is after it)."""
import json
import re
import sys
import numpy as np

tag, light = sys.argv[1], float(sys.argv[2])
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
cal = json.load(open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face5\eyecal_%s.json' % tag))


def lin(h):
    c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def hexc(l):
    l = np.clip(l, 0, 1)
    s = np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in s)


p = W + r'\godot\data\content\looks.json'
s = open(p, encoding='utf-8').read()
for eye, a in cal.items():
    if eye == 'moss':
        continue
    m = re.search(r'\{"id": "%s", "name": "[^"]+", "color": "(#\w+)", "ring": "(#\w+)"\}' % eye, s)
    iris, ring = lin(m.group(1)), lin(m.group(2))
    # (the dye before iris_light; the mean of iris and ring made the albedo wanted, each channel)
    k = (np.array(a) / light) / ((iris + ring) / 2)
    ni, nr = hexc(iris * k), hexc(ring * k)
    print("%-6s %s/%s -> %s/%s" % (eye, m.group(1), m.group(2), ni, nr))
    s = s.replace(m.group(0), m.group(0).replace(m.group(1), ni, 1).replace('"ring": "%s"' % m.group(2), '"ring": "%s"' % nr))
open(p, 'w', encoding='utf-8', newline='').write(s)
