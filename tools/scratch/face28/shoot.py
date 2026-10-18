"""Face 28 verify shoot: cinematic close-ups of her face at their real cues + the Look at rest by night, one godot turn."""
import os, subprocess, sys, time, glob
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs"); os.makedirs(LOGS, exist_ok=True)
TP = os.path.join(W, "tools", "turn.py")
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
CINE = {"c01": 60, "c02": 42, "c03": 22, "c04a": 46}
runs = []
for f, (sk, ey) in PZ.items():
    pre = ["--preset", f, "--skin", sk, "--eyes", ey, "--hair", "ponytail"]
    for c, u in CINE.items():
        runs.append((f"v_{c}_{f}", ["--quick", "warden", "--sex", "female", "--zone", "lowford", "--nohud", "--cine", c, "--shot", f"v_{c}_{f}", "--until", str(u), "--stills", "4"] + pre))
    for t in ("day", "night"):
        runs.append((f"v_lk_{f}_{t}", ["--shot", f"v_lk_{f}_{t}", "--seconds", "10", "--new", "--sex", "female", "--step", "1", "--part", "1", "--open-eyes", "--time", t] + pre))
only = sys.argv[1:]
if only: runs = [r for r in runs if any(o in r[0] for o in only)]
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
print("dotnet build", b.returncode, flush=True)
if b.returncode: print(b.stdout[-2000:]); sys.exit(2)
if subprocess.run([sys.executable, TP, "take", "godot", "face28: verify", "--wait", "1800", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for name, a in runs:
        t0 = time.time()
        for f in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(f)
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + a, stdout=lf, stderr=subprocess.STDOUT)
            try: p.wait(timeout=420)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        errs = sum(1 for l in open(os.path.join(LOGS, name + ".log"), encoding="utf-8", errors="replace") if ("ERROR" in l or "Unhandled" in l) and "RID alloc" not in l)
        n = len(glob.glob(os.path.join(G, ".shots", name + "*.png")))
        print(f"[{name}] {n} png, {errs} error lines, {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face28: verify"])
print("SHOOT DONE", time.strftime("%H:%M"))
