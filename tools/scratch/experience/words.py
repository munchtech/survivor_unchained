"""How much there is to read in the story: words per conversation in dialogue.json, and a rough
reading time. A conversation's whole tree is an upper bound; one path through it is about the
share given by the deepest chain of nodes over all its nodes."""
import json, re, sys

D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b\godot\data\content\dialogue.json"
data = json.load(open(D, encoding="utf-8"))
convos = data if isinstance(data, list) else data.get("conversations") or list(data.values())
total_words = total_lines = 0
rows = []
for c in convos:
    if not isinstance(c, dict):
        continue
    nodes = c.get("nodes", {})
    vals = nodes.values() if isinstance(nodes, dict) else nodes
    words = lines = 0
    for n in vals:
        if not isinstance(n, dict):
            continue
        t = n.get("text") or ""
        if isinstance(t, list):
            t = " ".join(x if isinstance(x, str) else "" for x in t)
        words += len(re.findall(r"\w+", t))
        lines += 1
        for ch in n.get("choices") or []:
            ct = (ch.get("text") or "") if isinstance(ch, dict) else ""
            if isinstance(ct, list):
                ct = " ".join(x for x in ct if isinstance(x, str))
            words += len(re.findall(r"\w+", ct))
    rows.append((words, lines, c.get("id", "?")))
    total_words += words
    total_lines += lines
rows.sort(reverse=True)
print(f"{len(rows)} conversations, {total_lines} lines, {total_words} words in all")
print(f"reading all of it at 200 words a minute plus 1.5 s a line: {(total_words / 200 + total_lines * 1.5 / 60):.0f} minutes")
for w, l, i in rows[:12]:
    print(f"  {i}: {w} words, {l} lines")
