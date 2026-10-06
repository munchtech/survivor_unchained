"""Replace exact line texts in the content JSON in place (keeps the file's layout).
Usage: python edit_lines_s2.py <edits.json>; edits: [[file, old, new], ...]"""
import json, sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a035208561a66c171"
edits = json.load(open(sys.argv[1], encoding="utf-8"))
for f, old, new in edits:
    p = WT + "\\" + f.replace("/", "\\")
    s = open(p, encoding="utf-8", newline="").read()
    o, n = json.dumps(old, ensure_ascii=False), json.dumps(new, ensure_ascii=False)
    c = s.count(o)
    if c != 1:
        print("SKIP", f, c, old[:60]); continue
    open(p, "w", encoding="utf-8", newline="").write(s.replace(o, n))
    print("ok", f, old[:50], "->", new[:50])
