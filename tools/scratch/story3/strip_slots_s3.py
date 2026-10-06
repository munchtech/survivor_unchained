"""Remove the explicit-scene slots from dialogue.json (the legal lead's blocker): the variant
behind settings.intimacy == "full" in each intimate scene goes, the fade-to-black variants stay.
Round-trip format: indent 1, ensure_ascii False, CRLF, trailing CRLF; checked before writing."""
import json, sys
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\godot\data\content\dialogue.json"
raw = open(p, "rb").read()
d = json.loads(raw.decode("utf-8"))
def dump(x):
    return (json.dumps(x, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8")
if dump(d) != raw:
    sys.exit("round trip differs; not writing")
gone = []
for c, conv in d.items():
    for k, n in conv["nodes"].items():
        t = n["text"]
        if not isinstance(t, list):
            continue
        keep = [v for v in t if not v["text"].lstrip().startswith("[explicit scene")
                and "settings.intimacy" not in json.dumps(v.get("when"))]
        if len(keep) != len(t):
            gone.append(f"{c}.{k}: {len(t)} -> {len(keep)}")
            n["text"] = keep
open(p, "wb").write(dump(d))
print("\n".join(gone))
