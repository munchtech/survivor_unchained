"""A story run's gist: python gist.py NAME -> per-10 s health, ember, stage; its tagged frames by tag; its errors."""
import os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b\godot\.shots"
name = sys.argv[1]
text = open(os.path.join(HERE, "logs", name + ".log"), encoding="utf-8", errors="replace").read()
rows, low = [], None
for line in text.splitlines():
    m = re.match(r"\[\s*([\d.]+)s\] (\w+) hp (\d+)/(\d+) ember (\d+).*?(?:stage=(\w+))?(?: beat=(\d+))?(?: falls=(\d+))?", line)
    if not m: continue
    t, zone, hp, mx, em, st, bt, fl = m.groups()
    st = re.search(r"stage=(\w+)", line); bt = re.search(r"beat=(\d+)", line); fl = re.search(r"falls=(\d+)", line)
    rows.append(f"{float(t):.0f} {zone[:5]} {hp} e{em} {st.group(1) if st else ''}{bt.group(1) if bt else ''} f{fl.group(1) if fl else ''}")
    if zone == "arena": low = min(low or 9999, int(hp) / int(mx))
print("; ".join(rows))
print("lowest health in the fight:", f"{low:.0%}" if low else "-")
tags = collections.Counter()
for f in os.listdir(SHOTS):
    m = re.match(re.escape(name) + r"_(.+)_\d+\.png$", f)
    if m and not re.match(r"^\d+$", m.group(1)): tags[m.group(1)] += 1
print("tags:", ", ".join(f"{k} {v}" for k, v in sorted(tags.items())))
errs = [l for l in text.splitlines() if "Exception" in l]
print("exceptions:", len(errs), errs[:2])
