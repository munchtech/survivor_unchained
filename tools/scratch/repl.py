"""Exact-text replacements in a file, line endings normalised, written back as found.

usage: python repl.py FILE EDITS.json   (EDITS: [[old, new], ...]); fails loudly when an old text is missing or not unique.
"""
import json, sys

path, edits = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))
raw = open(path, "rb").read()
bom = raw.startswith(b"\xef\xbb\xbf")
text = raw.decode("utf-8-sig")
crlf = "\r\n" in text
text = text.replace("\r\n", "\n")
for old, new in edits:
    old, new = old.replace("\r\n", "\n"), new.replace("\r\n", "\n")
    n = text.count(old)
    if n != 1:
        sys.exit(f"{n} matches for: {old[:80]!r}")
    text = text.replace(old, new)
if crlf:
    text = text.replace("\n", "\r\n")
open(path, "wb").write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
print(f"{len(edits)} edits")
