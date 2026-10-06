"""cut.py PATH FIRST LAST: delete lines FIRST..LAST (1-based, inclusive), keeping the file's line endings."""
import sys
from ed import ROOT
import os
p, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
p = p if os.path.isabs(p) else os.path.join(ROOT, p)
lines = open(p, encoding="utf-8", newline="").read().splitlines(keepends=True)
del lines[a - 1:b]
open(p, "w", encoding="utf-8", newline="").write("".join(lines))
print("cut", a, b, "from", p)
