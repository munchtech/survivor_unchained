"""Compare hand-set segments in the direction files with the automatic split; drop the ones the rules now cover."""
import json
import os
import sys

sys.path.insert(0, "tools/vo")
import lines as L

drop = "--drop" in sys.argv
built = {l["id"]: l for l in L.build()}
for f in sorted(os.listdir("tools/vo/direction")):
    if not f.endswith(".json"):
        continue
    p = os.path.join("tools/vo/direction", f)
    d = json.load(open(p, encoding="utf-8"))
    changed = False
    for k, v in d.items():
        if "segments" not in v:
            continue
        auto = built.get(k, {}).get("segments")
        hand = [(s["voice"], s["text"]) for s in v["segments"]]
        a = [(s["voice"], s["text"]) for s in auto] if auto else None
        same_words = auto is not None and " ".join(t for _, t in hand).split() == " ".join(t for _, t in a).split()
        same_voices = auto is not None and [x for x, _ in hand] == [x for x, _ in a]
        verdict = "same" if (same_words and same_voices) else "words differ" if not same_words else "voices differ"
        print(f"{f:16s} {k:30s} {verdict}")
        if not same_words:
            print("   hand:", hand)
            print("   auto:", a)
        if drop and (verdict == "same" or k in sys.argv):
            v.pop("segments")
            changed = True
    if changed:
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in d.items()) + "\n}\n")
