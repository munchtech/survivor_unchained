"""Give a file CRLF line endings (the repo's docs use them). Usage: crlf_s5.py PATH"""
import sys
p = sys.argv[1]
t = open(p, "rb").read().decode("utf-8").replace("\r\n", "\n")
open(p, "wb").write(t.replace("\n", "\r\n").encode("utf-8"))
print("crlf", p)
