"""Face 28 hair shoot (the owner, 17 Oct): every style at creation's Look (8 turns at rest + spinning), in town at the close-up
and play cameras in motion (across, away), day and night, a fight at the close-up, and the cinematic walk-ups with physics styles."""
import os, subprocess, sys, time, glob
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs"); os.makedirs(LOGS, exist_ok=True)
TP = os.path.join(W, "tools", "turn.py")
STY = ["long", "ponytail", "braid", "bob", "pixie"]
OWN = ["--preset", "own", "--skin", "fair", "--eyes", "moss"]
LOOK = ["--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes"] + OWN
TOWN = ["--quick", "arcanist", "--sex", "female", "--zone", "waystation", "--nohud"] + OWN
runs = []
RV = ["--quick", "reaver", "--sex", "female", "--zone", "waystation", "--nohud"] + OWN
for s in STY:
    runs.append((f"r_cu_day_{s}_across", ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "across", "--close", "1", "--time", "day", "--hair", s] + RV))
for s in ("long", "ponytail", "braid"):
    runs.append((f"r_cu_day_{s}_away", ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "away", "--close", "1", "--time", "day", "--hair", s] + RV))
    runs.append((f"r_cu_night_{s}_across", ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "across", "--close", "1", "--time", "night", "--hair", s] + RV))
for s in STY:
    for d in range(0, 360, 45):
        runs.append((f"h_lk_{s}_t{d:03d}", ["--seconds", "10", "--turn", str(d), "--hair", s] + LOOK))
    runs.append((f"h_lk_{s}_spin", ["--seconds", "6", "--every", "0.5", "--count", "8", "--spin", "90", "--hair", s] + LOOK))
for s in STY:
    for m in ("across", "away"):
        runs.append((f"h_cu_day_{s}_{m}", ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", m, "--close", "1", "--time", "day", "--hair", s] + TOWN))
    runs.append((f"h_cm_day_{s}_away", ["--seconds", "8", "--every", "0.25", "--count", "8", "--auto", "away", "--close", "0.5", "--time", "day", "--hair", s] + TOWN))
    runs.append((f"h_pl_day_{s}_across", ["--seconds", "8", "--every", "0.5", "--count", "6", "--auto", "across", "--time", "day", "--hair", s] + TOWN))
for s in ("long", "ponytail"):
    runs.append((f"h_cu_night_{s}_across", ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "across", "--close", "1", "--time", "night", "--hair", s] + TOWN))
    runs.append((f"h_cu_night_{s}_away", ["--seconds", "8", "--every", "0.25", "--count", "8", "--auto", "away", "--close", "1", "--time", "night", "--hair", s] + TOWN))
runs.append(("h_pl_night_ponytail_away", ["--seconds", "8", "--every", "0.5", "--count", "6", "--auto", "away", "--time", "night", "--hair", "ponytail"] + TOWN))
for s in ("long",):
    runs.append((f"h_fight_{s}", ["--quick", "arcanist", "--sex", "female", "--zone", "lowford", "--nohud", "--auto", "--seconds", "25", "--every", "1", "--count", "15", "--hair", s] + OWN))
for s in ("long", "braid"):
    for c, u in (("c02", 42), ("c03", 22)):
        runs.append((f"h_{c}_{s}", ["--quick", "warden", "--sex", "female", "--zone", "lowford", "--nohud", "--cine", c, "--until", str(u), "--stills", "4", "--hair", s] + OWN))
only = sys.argv[1:]
if only: runs = [r for r in runs if any(o in r[0] for o in only)]
print(len(runs), "runs", flush=True)
if subprocess.run([sys.executable, TP, "take", "godot", "face28: hair", "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for name, a in runs:
        t0 = time.time()
        for f in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(f)
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--", "--shot", name] + a, stdout=lf, stderr=subprocess.STDOUT)
            try: p.wait(timeout=300)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        errs = sum(1 for l in open(os.path.join(LOGS, name + ".log"), encoding="utf-8", errors="replace") if ("ERROR" in l or "Unhandled" in l) and "RID alloc" not in l and "get_singleton" not in l)
        n = len(glob.glob(os.path.join(G, ".shots", name + "*.png")))
        print(f"[{name}] {n} png, {errs} error lines, {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face28: hair"])
print("SHOOT DONE", time.strftime("%H:%M"))
