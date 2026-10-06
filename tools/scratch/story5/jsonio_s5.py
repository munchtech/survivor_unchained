"""Round-trip helpers for the content JSON (indent 1, ensure_ascii False, CRLF, trailing CRLF),
and a check of which content files round-trip exactly. Run directly to check."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
C = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a54dc034ed29f2e02\godot\data\content"

def dump(d):
    return (json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8")

def load(name):
    raw = open(os.path.join(C, name), "rb").read()
    data = json.loads(raw.decode("utf-8"))
    if dump(data) != raw:
        sys.exit(f"{name}: round trip differs; not safe to rewrite")
    return data

def save(name, data):
    open(os.path.join(C, name), "wb").write(dump(data))

if __name__ == "__main__":
    for f in sorted(os.listdir(C)):
        if not f.endswith(".json"): continue
        raw = open(os.path.join(C, f), "rb").read()
        ok = dump(json.loads(raw.decode("utf-8"))) == raw
        print(f, "round-trips" if ok else "DIFFERS")
