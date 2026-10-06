"""Warmed is flavour only: drop the bonus from the love scenes' notices in dialogue.json, keeping
the words and the condition's record. Round-trip format checked before writing."""
import json, sys
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\godot\data\content\dialogue.json"
raw = open(p, "rb").read()
d = json.loads(raw.decode("utf-8"))
def dump(x):
    return (json.dumps(x, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8")
if dump(d) != raw:
    sys.exit("round trip differs; not writing")
new = {
    "You slept well, for once. (Warmed: +8% damage, +5% speed, one day)": "You slept well, for once.",
    "You feel good. Better than good. (Warmed: +8% damage, +5% speed, one day)": "You feel good. Better than good.",
}
done = 0
for c, conv in d.items():
    for k, n in conv["nodes"].items():
        for e in n.get("effects") or []:
            if isinstance(e, dict) and e.get("notice") in new:
                e["notice"] = new[e["notice"]]
                done += 1
                print(f"{c}.{k}: {e['notice']}")
if done != 2:
    sys.exit(f"changed {done}, wanted 2; not writing")
open(p, "wb").write(dump(d))
