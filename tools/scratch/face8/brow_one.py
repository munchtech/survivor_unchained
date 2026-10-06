"""brow_one.py img[@x0,y0,x1,y1] ... : brow_fit's measure on any pictures (a sheet, an unshaded shot)."""
import sys
sys.argv = [sys.argv[0], 'none'] + sys.argv[1:]
src = open(__file__.replace('brow_one.py', 'brow_fit.py')).read().split('for p in P:')[0]
exec(src)
for a in sys.argv[2:]:
    c = None
    if '@' in a:
        a, b = a.split('@')
        c = [int(v) for v in b.split(',')]
    r = brows(a, c)
    print(a.split('\\')[-1].split('/')[-1], 'brow/skin r %.2f g %.2f b %.2f L %.2f hair %.2f' % (*r[0], r[1], r[2]) if r else 'no face')
