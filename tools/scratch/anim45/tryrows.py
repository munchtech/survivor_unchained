"""Evaluate hand-built rows: python tryrows.py outfit "tx,ty,tz,fx,fz,roll" ..."""
import sys, numpy as np
from pathlib import Path
rows = sys.argv[2:]; sys.argv = sys.argv[:2]
src = open(Path(__file__).with_name('opt.py')).read().split('r = minimize')[0]
exec(src)
for r in rows:
    x = [float(v) for v in r.split(',')]
    print(r, end='  '); score(x, True)
    at, sh, thick, Fp = row(x); print("   ROW", ";".join(",".join(f"{v:.4f}" for v in a) for a in (at, sh, thick)))
