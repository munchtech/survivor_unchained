"""Check the bible's Act 1 seeds against the data: every `conv.node` named exists, and every
quoted phrase in a seed line is found somewhere in the game's text."""
import glob, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a54dc034ed29f2e02"
C = os.path.join(WT, "godot", "data", "content")
d = json.load(open(os.path.join(C, "dialogue.json"), encoding="utf-8"))
allText = []
for f in glob.glob(os.path.join(C, "*.json")):
    allText.append(open(f, encoding="utf-8").read())
for f in glob.glob(os.path.join(WT, "godot", "logic", "**", "*.cs"), recursive=True) + glob.glob(os.path.join(WT, "godot", "src", "**", "*.cs"), recursive=True):
    allText.append(open(f, encoding="utf-8").read().replace('\\"', '"'))
for f in glob.glob(os.path.join(WT, "godot", "data", "**", "*.json"), recursive=True):
    allText.append(open(f, encoding="utf-8").read())
def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()
blob = norm(" ".join(allText))
bible = open(os.path.join(WT, "docs", "STORY_BIBLE.md"), encoding="utf-8").read()
start = bible.index("### Seeds planted in Act 1")
end = bible.index("## 7. Act 2")
sec = bible[start:end]
missing_nodes, missing_q = [], []
for m in re.finditer(r"`([a-z_]+)\.([a-z_0-9]+)`", sec):
    conv, node = m.groups()
    if conv in d and node not in d[conv].get("nodes", {}):
        missing_nodes.append(f"{conv}.{node}")
for m in re.finditer(r'"([^"`*]{12,240}?)"', sec):
    q = m.group(1).replace("\n", " ")
    if q.startswith((".", ",", ")", ";", ":")) or "(" in q[:2]: continue
    for part in re.split(r"\.\.\.|…", q):
        p = norm(part)
        if len(p) >= 12 and p not in blob:
            missing_q.append(q[:120]); break
print("nodes named that do not exist:", sorted(set(missing_nodes)))
print("quotes not found in the game's text:")
for q in missing_q: print("  -", q)
