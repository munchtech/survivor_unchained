"""Inclusive and self time per method from a dotnet-trace speedscope file (evented profiles).
    python prof.py FILE [--thread SUBSTR] [--under METHOD_SUBSTR] [--top N] [--self]"""
import json
import sys
from collections import defaultdict

argv = sys.argv[1:]


def opt(flag, default):
    if flag in argv:
        i = argv.index(flag)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


thread = opt("--thread", None)
under = opt("--under", None)
top = int(opt("--top", "40"))
selfonly = "--self" in argv
if selfonly:
    argv.remove("--self")
d = json.load(open(argv[0], encoding="utf-8"))
frames = [f["name"] for f in d["shared"]["frames"]]


def short(n):
    # Strip the module prefix and argument lists.
    if "!" in n:
        n = n.split("!", 1)[1]
    p = n.find("(")
    return n[:p] if p > 0 else n


profiles = d["profiles"]
summary = []
for p in profiles:
    total = p["endValue"] - p["startValue"]
    summary.append((total, p["name"], p))
summary.sort(key=lambda x: -x[0])
if not thread:
    for t, n, p in summary[:15]:
        names = set()
        for e in p["events"][:20000]:
            names.add(short(frames[e["frame"]]))
        hint = [x for x in names if "_Process" in x or "Step" in x][:3]
        print(f"{t:10.0f} {n} {hint}")
    sys.exit()
p = next(p for t, n, p in summary if thread in n)
incl = defaultdict(float)
selft = defaultdict(float)
stack = []
last = None
busy = 0.0
for e in p["events"]:
    at = e["at"]
    if last is not None and stack:
        dt = at - last
        names = [short(frames[f]) for f in stack]
        if under is None or any(under in x for x in names):
            busy += dt
            seen = set()
            start = 0
            if under is not None:
                start = max(i for i, x in enumerate(names) if under in x)
            for x in names[start:]:
                if x not in seen:
                    incl[x] += dt
                    seen.add(x)
            selft[names[-1]] += dt
    last = at
    if e["type"] == "O":
        stack.append(e["frame"])
    else:
        # Close: pop to the matching frame.
        while stack:
            f = stack.pop()
            if f == e["frame"]:
                break
print(f"busy {busy:.0f} ms (unit as in file) in {p['name']}")
rows = (selft if selfonly else incl).items()
for name, t in sorted(rows, key=lambda x: -x[1])[:top]:
    print(f"{t:9.0f} {100 * t / max(busy, 1):5.1f}%  {name}")
