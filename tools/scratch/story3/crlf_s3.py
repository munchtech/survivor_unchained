"""Make the named worktree files CRLF throughout (the repo's docs are CRLF)."""
import sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9"
for rel in sys.argv[1:]:
    p = WT + "\\" + rel.replace("/", "\\")
    b = open(p, "rb").read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    open(p, "wb").write(b)
    print(rel, "crlf", b.count(b"\r\n"))
