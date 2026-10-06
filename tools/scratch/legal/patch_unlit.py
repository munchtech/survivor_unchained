"""Patches make_motioncheck2.py: the marks become unlit emission (no albedo, specular, rim or
scatter), bright cyan for the areolas and dim cyan for the genital area, so a pixel's
brightness alone says which mark it is, in any light. The generator's text sits inside a
Python triple-quoted string, so GDScript's \\t and \\n need two backslashes there."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, 'make_motioncheck2.py')
t = open(p, encoding='utf-8').read()
start = t.index('\tcode = code.substr(0, end) + ')
stop = t.index('}\\n"', start) + len('}\\n"') if '}\\n"' in t[start:start + 2000] else t.index('\n', t.index('else if (UV2.y', start))
flat = 'ALBEDO = vec3(0.0); SPECULAR = 0.0; ROUGHNESS = 1.0; RIM = 0.0; SSS_STRENGTH = 0.0; BACKLIGHT = vec3(0.0);'
BS = '\\\\'  # two backslashes in the generator's text
line = ('\tcode = code.substr(0, end) + "' + BS + 'tif (UV2.x > 0.5) { ' + flat + ' EMISSION = vec3(0.0, 0.6, 0.6); }'
        + BS + 'n' + BS + 'telse if (UV2.y > 0.5) { ' + flat + ' EMISSION = vec3(0.0, 0.2, 0.2); }' + BS + 'n}' + BS + 'n"')
t = t[:start] + line + t[stop:]
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('patched')
