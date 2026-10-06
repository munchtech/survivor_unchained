"""Drop takes whose words the rewrite changed from the voice index, as produce.py's write_index
does (a take plays only while its hash matches): the line goes quiet until it is recorded again."""
import json, os, sys
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1"
P = os.path.join(WT, "godot", "data", "vo", "index.json")
raw = open(P, "rb").read()
crlf = b"\r\n" in raw
d = json.loads(raw.decode("utf-8"))

def dump(x):
    s = json.dumps(x, indent=1, ensure_ascii=False)
    s = s.replace("\n", "\r\n") if crlf else s
    return (s + ("\r\n" if crlf else "\n")).encode("utf-8")

if dump(d) != raw:
    sys.exit("index.json does not round-trip; not rewriting")
for lid in sys.argv[1:]:
    t = d["lines"].pop(lid)
    f = os.path.join(WT, "godot", "art", "vo", t["file"])
    print("dropped", lid, t["file"], os.path.exists(f))
open(P, "wb").write(dump(d))
