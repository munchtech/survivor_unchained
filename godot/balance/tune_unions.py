"""Bring each union toward 0.9 of its two evolved halves together (the slot it
frees makes up the rest), from the `weapons` command's markdown:

    python tune_unions.py out/w.md [--apply] [--damp 0.8]"""
import math, re, sys
import skills_json

TARGET = 0.9

md = open(sys.argv[1], encoding='utf-8').read()
apply = '--apply' in sys.argv
damp = float(sys.argv[sys.argv.index('--damp') + 1]) if '--damp' in sys.argv else 0.8
rows = re.findall(r'^\| ([a-z_]+) \| [\d/]+ \| [\d/]+ \| ([\d.]+) \|$', md, re.M)
src = skills_json.read()
for union, ratio in rows:
    f = max(0.4, min(3.0, (TARGET / max(0.05, float(ratio))) ** damp))
    moved = skills_json.scale_base(src, union, f, digits=1)
    assert moved != src or f == 1, (union, 'no base damage')
    src = moved
    print(f'{union:16} ratio {float(ratio):.2f} -> damage x{f:.2f}')
if apply:
    skills_json.write(src)
    print('applied')
