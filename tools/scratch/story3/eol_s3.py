"""Report CRLF and bare LF counts for files, and with --fix make a CRLF file all CRLF."""
import sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9"
fix = "--fix" in sys.argv
for rel in [a for a in sys.argv[1:] if a != "--fix"]:
    p = WT + "\\" + rel.replace("/", "\\")
    b = open(p, "rb").read()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    print(rel, "crlf", crlf, "bare lf", lf)
    if fix and crlf and lf:
        b = b.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        open(p, "wb").write(b)
        print("  fixed")
