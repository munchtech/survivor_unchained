"""Each shot's start and length as the game lays them out (the animatic's own
schedule), and each line's start, for writing the shooting scripts."""
import sys, os, json
T = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\tools\cinematics"
sys.path.insert(0, T)
import animatic as a
a.INDEX = a.load_json(os.path.join(a.GODOT, 'data', 'vo', 'index.json'))['lines']

facts = [x for x in sys.argv[2:]]
tl = a.load_json(os.path.join(a.GODOT, "data", "cinematics", f"{sys.argv[1]}.json"))
ctx = a.Ctx("warden", "hunter", "long", "female", facts)
shots, total = a.schedule(tl, ctx)
for shot, s, d, timed in shots:
    lines = [f"{c['id'].split('.')[1]}@{t - s:.1f}({a.line_seconds(c['id']):.1f})" for t, c in timed if c["do"] == "line"]
    print(f"{shot['id']:>4} {shot.get('type',''):6} start {s:6.2f} dur {d:5.2f} lens {shot.get('cam',{}).get('lens','-')} {' '.join(lines)}")
print(f"total {total:.1f}")
