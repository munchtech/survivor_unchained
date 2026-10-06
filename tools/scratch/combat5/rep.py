"""Everything about one harness run: python rep.py NAME [hurt-part ...]
NAME is godot/balance/out/NAME.jsonl in the combat worktree."""
import sys, subprocess, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a5115633c7006e4d4\godot\balance\out"
f = os.path.join(OUT, sys.argv[1] + ".jsonl")
def run(*a): print(subprocess.run([sys.executable, *a], capture_output=True, text=True).stdout, end="")
run(os.path.join(HERE, "an.py"), f)
run(os.path.join(HERE, "rise.py"), f)
for part in sys.argv[2:]:
    run(os.path.join(HERE, "an.py"), f, "--by", "fight,tier", "--hurt", part)
rows = []
for l in open(f, encoding="utf-8"):
    try: rows.append(json.loads(l))
    except ValueError: pass
# Dips under half, by stage and calling; timeouts; falls by where.
g = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    s = r["Spec"]
    for st in r["Stages"]:
        if st["Name"] != "boss": g[(s["Fight"], s["Calling"])][st["Name"]].append(st["LowHp"])
for k in sorted(g):
    print("/".join(k), "  ".join(f"{n}: {sum(x < 0.5 for x in v) / len(v):.0%}" for n, v in sorted(g[k].items())))
cut = [r["Spec"]["Key"] + " " + r["Where"][:60] for r in rows if not r["Won"] and r["Minutes"] >= r["Spec"]["Cap"] - 0.01]
print(f"cut off at the cap: {len(cut)}"); [print("  ", c) for c in cut[:8]]
falls = collections.Counter()
for r in rows:
    for fa in r.get("FellAt", []): falls[(r["Spec"]["Fight"], " ".join(fa.split()[:2]))] += 1
print("falls:", dict(sorted(falls.items())))
hp = collections.defaultdict(list)
for r in rows:
    if r.get("MaxHpAtBoss"): hp[(r["Spec"]["Fight"], r["Spec"]["Calling"], r["Spec"]["Tier"])].append(r["MaxHpAtBoss"])
if hp:
    print("max hp at the boss (median):", " ".join(f"{k[0][0]}{k[1][0]}{k[2]}:{sorted(v)[len(v)//2]:.0f}" for k, v in sorted(hp.items())))
