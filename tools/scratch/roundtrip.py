import json, sys
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content"
for name in sys.argv[1:]:
    raw = open(f"{ROOT}\\{name}", "rb").read()
    d = json.loads(raw.decode("utf-8"))
    ok = []
    for ind in (1, 2):
        out = json.dumps(d, indent=ind, ensure_ascii=False)
        for nl in ("\r\n", "\n"):
            for tail in ("", nl):
                if (out.replace("\n", nl) + tail).encode("utf-8") == raw:
                    ok.append((ind, repr(nl), repr(tail)))
    print(name, ok or "NO MATCH")
