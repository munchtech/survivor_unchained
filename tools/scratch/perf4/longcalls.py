"""Long calls on one thread of a dotnet-trace speedscope (evented) profile: every
call that lasted over MS milliseconds whose children each lasted less (the
deepest long call), with its chain of callers and its biggest children.
    python longcalls.py FILE --thread SUBSTR [--ms 15] [--from T0] [--to T1]"""
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
limit = float(opt("--ms", "15"))
t_from = float(opt("--from", "-1e18"))
t_to = float(opt("--to", "1e18"))
d = json.load(open(argv[0], encoding="utf-8"))
frames = [f["name"] for f in d["shared"]["frames"]]


def short(n):
    if "!" in n:
        n = n.split("!", 1)[1]
    p = n.find("(")
    return n[:p] if p > 0 else n


p = next(pr for pr in d["profiles"] if thread in pr["name"])
start = p["startValue"]
# Each call: [frame, open, close, children]
stack = []
long_calls = []
for e in p["events"]:
    if e["type"] == "O":
        stack.append([e["frame"], e["at"], None, []])
    else:
        while stack:
            c = stack.pop()
            c[2] = e["at"]
            if stack:
                stack[-1][3].append(c)
            dur = c[2] - c[1]
            if dur > limit and t_from <= c[1] - start <= t_to:
                # Deepest: no child as long.
                if not any(ch[2] - ch[1] > limit for ch in c[3]):
                    chain = [short(frames[s[0]]) for s in stack[-8:]]
                    kids = defaultdict(float)
                    for ch in c[3]:
                        kids[short(frames[ch[0]])] += ch[2] - ch[1]
                    long_calls.append((c[1] - start, dur, short(frames[c[0]]), chain, sorted(kids.items(), key=lambda x: -x[1])[:4]))
            if c[0] == e["frame"]:
                break
print(f"{len(long_calls)} deepest calls over {limit} ms on {p['name']}")
for at, dur, name, chain, kids in long_calls[:80]:
    print(f"{at:9.0f} {dur:6.1f}  {name}")
    print("            via " + " < ".join(reversed(chain[-5:])))
    if kids:
        print("            kids " + ", ".join(f"{k} {v:.1f}" for k, v in kids))
