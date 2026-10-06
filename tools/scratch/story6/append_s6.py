"""Append a markdown section (LF in the scratchpad) to a CRLF doc in the worktree."""
import sys
src, dst = sys.argv[1], sys.argv[2]
add = open(src, encoding="utf-8").read().replace("\r\n", "\n").replace("\n", "\r\n")
raw = open(dst, "rb").read().decode("utf-8")
if not raw.endswith("\r\n"):
    raw += "\r\n"
open(dst, "wb").write((raw + add).encode("utf-8"))
print("appended", len(add), "chars")
