"""Bring each union toward 0.9 of its two evolved halves together (the slot it
frees makes up the rest), from the `weapons` command's markdown:

    python tune_unions.py out/w.md [--apply] [--damp 0.8]"""
import math, re, sys

WEAPONS = '../logic/Content/Weapons.cs'
TARGET = 0.9

md = open(sys.argv[1], encoding='utf-8').read()
apply = '--apply' in sys.argv
damp = float(sys.argv[sys.argv.index('--damp') + 1]) if '--damp' in sys.argv else 0.8
rows = re.findall(r'^\| ([a-z_]+) \| [\d/]+ \| [\d/]+ \| ([\d.]+) \|$', md, re.M)
src = open(WEAPONS, encoding='utf-8').read()
for union, ratio in rows:
    f = max(0.4, min(3.0, (TARGET / max(0.05, float(ratio))) ** damp))
    pat = r'(Id = "%s", Name = "[^"]*", School = [^\n]*\n            Base = new\(\) \{ Cooldown = [\d.]+, Damage = )([\d.]+)' % union
    n = len(re.findall(pat, src))
    assert n == 1, (union, n)
    src = re.sub(pat, lambda m: m.group(1) + ('%.1f' % (float(m.group(2)) * f)).rstrip('0').rstrip('.'), src)
    print(f'{union:16} ratio {float(ratio):.2f} -> damage x{f:.2f}')
if apply:
    open(WEAPONS, 'w', encoding='utf-8').write(src)
    print('applied')
