"""python sweep.py JOBS.txt: several shots.py runs in one build and one godot turn. Each line of JOBS: NAME SET [raw switches...]
(# comments). Frames: godot/.shots/NAME_SET_NN.png; logs in logs/."""
import os, subprocess, sys, time, shlex
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\env-1"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
LOGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
TP = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
src = open(sys.argv[1]).read().splitlines()
from shots_cfg import HER, SETS
jobs = [shlex.split(l) for l in src if l.strip() and not l.lstrip().startswith("#")]
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0: print(b.stdout[-3000:]); sys.exit(1)
TURN = "env-1: E1 light sweep " + os.path.basename(sys.argv[1])
if subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600", "--stale-ok"]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for j in jobs:
        rnd, s, more = j[0], j[1], j[2:]
        extra, n = SETS[s]; name = f"{rnd}_{s}"; t0 = time.time()
        args = HER + more + extra + ["--spots-from", "10", "--spots-every", "6", "--shot", name, "--seconds", "15", "--every", "6", "--count", str(n)]
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + args, stdout=lf, stderr=subprocess.STDOUT)
            try: p.wait(timeout=600)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        print(f"[{name}] {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
