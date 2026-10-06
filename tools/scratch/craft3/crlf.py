"""Give files back the CRLF the checkout has (sed -i on Windows writes LF): python crlf.py PATH..."""
import sys, os
from ed import ROOT
for p in sys.argv[1:]:
    p = p if os.path.isabs(p) else os.path.join(ROOT, p)
    s = open(p, encoding="utf-8", newline="").read()
    t = s.replace("\r\n", "\n").replace("\n", "\r\n")
    if t != s:
        open(p, "w", encoding="utf-8", newline="").write(t)
        print("crlf", p)
