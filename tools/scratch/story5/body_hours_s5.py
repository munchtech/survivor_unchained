"""List every line about the survivor's body heat, breath or heart, with its conditions, to check the body's hours
(cold and slow by night, warm and quick at dawn, breath smoking only at dawn)."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
C = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a54dc034ed29f2e02\godot\data\content"
d = json.load(open(C + r"\dialogue.json", encoding="utf-8"))
pat = re.compile(r"(your breath|breath (smok|show|doesn|does not|didn)|you're (so )?(cold|warm)|you were cold|your (skin|hands|heart|body|chest|feet|mouth) (is|are|was|were|'s)|cold as (the|a|stone|ice)|warm as|heart('s| is)? (slow|going|quick|beat)|your heart|no breath|not breathing)", re.I)
for c, conv in d.items():
    for k, n in conv.get("nodes", {}).items():
        t = n["text"]; vs = t if isinstance(t, list) else [{"text": t}]
        for i, x in enumerate(vs):
            for m in pat.finditer(x["text"]):
                s = max(0, m.start() - 60)
                print(f"{c}.{k}.{i} when={json.dumps(x.get('when'))[:70]} | ...{x['text'][s:m.end() + 50]}")
for f in ("npcs.json", "folk.json"):
    for m in pat.finditer(open(C + "\\" + f, encoding="utf-8").read()):
        print(f, "|", m.group(0))
