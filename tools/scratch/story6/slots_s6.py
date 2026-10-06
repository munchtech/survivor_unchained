"""List every explicit-scene slot and every read of settings.intimacy across content and code."""
import glob, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7ba8903f4c8261b1"
d = json.load(open(WT + r"\godot\data\content\dialogue.json", encoding="utf-8"))
for c, conv in d.items():
    for k, n in conv["nodes"].items():
        t = n["text"]; vs = t if isinstance(t, list) else [{"text": t}]
        for i, x in enumerate(vs):
            if "explicit scene" in x["text"] or "intimacy" in json.dumps(x.get("when")):
                print(f"{c}.{k}.{i} when={json.dumps(x.get('when'))} | {x['text'][:200]}")
        if len(vs) > 1 and any("explicit scene" in x["text"] for x in vs):
            for i, x in enumerate(vs):
                if "explicit scene" not in x["text"]:
                    print(f"   cut-away {c}.{k}.{i} when={json.dumps(x.get('when'))[:80]} | {x['text'][:160]}")
pat = re.compile(r"intimacy|explicit scene", re.I)
for f in glob.glob(WT + r"\godot\**\*.*", recursive=True):
    if ".godot" in f or "\\art\\" in f or "\\assets" in f or not f.endswith((".cs", ".json", ".py", ".tscn")):
        continue
    if f.endswith("dialogue.json"):
        continue
    for i, l in enumerate(open(f, encoding="utf-8", errors="replace")):
        if pat.search(l):
            print(os.path.relpath(f, WT), i + 1, l.strip()[:160])
for f in glob.glob(WT + r"\tools\**\*.*", recursive=True) + glob.glob(WT + r"\docs\**\*.md", recursive=True):
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    k = len(re.findall(r"explicit scene", txt, re.I))
    if k:
        print("ref", os.path.relpath(f, WT), k)
