"""python shots.py ROUND [set ...]: E1's fixed-place frames (look bible 1c) in one godot turn.
Sets: night (Low Ford by night: camp, two road spots, ford, wood road, the close view at camp),
dawn (Low Ford at dawn, after the prologue), town_dawn, town_day. Frames: godot/.shots/ROUND_SET_NN.png. "old": the presets before E1 (--air-old); "unshadowed": the key casts no shadow; "tune=k=v,k=v": --air-tune; "args=--a 1 --b 2": raw switches."""
import os, subprocess, sys, time
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\env-3"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs")
TP = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
sys.path.insert(0, HERE)
from shots_cfg import HER, ROAD, SETS
rnd = sys.argv[1]; flags = {"old", "unshadowed"}; old = "old" in sys.argv[2:]; uns = "unshadowed" in sys.argv[2:]
tune = next((a[5:] for a in sys.argv[2:] if a.startswith("tune=")), None)
more = next((a[5:].split() for a in sys.argv[2:] if a.startswith("args=")), [])   # args="--close-key-night 0.5 ...": raw switches
sets = [a for a in sys.argv[2:] if a not in flags and not a.startswith(("tune=", "args="))] or list(SETS)
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0: print(b.stdout[-3000:]); sys.exit(1)
TURN = "env-3: E3 shots " + rnd
if subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600", "--stale-ok"]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for s in sets:
        extra, n = SETS[s]; name = f"{rnd}_{s}"; t0 = time.time()
        args = HER + (["--air-old"] if old else []) + (["--spots-unshadowed"] if uns else []) + (["--air-tune", tune] if tune else []) + more + extra + ["--spots-from", "10", "--spots-every", "6", "--shot", name, "--seconds", "15", "--every", "6", "--count", str(n)]
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + args, stdout=lf, stderr=subprocess.STDOUT)
            try: p.wait(timeout=600)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        print(f"[{name}] {time.time()-t0:.0f} s")
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
