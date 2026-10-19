"""python shots.py ROUND [set ...]: E1's fixed-place frames (look bible 1c) in one godot turn.
Sets: night (Low Ford by night: camp, two road spots, ford, wood road, the close view at camp),
dawn (Low Ford at dawn, after the prologue), town_dawn, town_day. Frames: godot/.shots/ROUND_SET_NN.png."""
import os, subprocess, sys, time
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\env-1"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs")
TP = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
HER = ["--quick", "warden", "--sex", "female", "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid", "--seed", "7", "--nohud"]
ROAD = "3,64;9,40;0,-38;-2,-72"
SETS = {
    # camp, road A (by the cart), road B (by the post), the ford, the wood road; then the close view at the fire
    "night": (["--zone", "lowford", "--facts", "prologue.woke=true", "--auto", "idle", "--spots", "-7.5,87.5;" + ROAD + ";-8.6,88.6,1,0"], 6),
    "dawn": (["--zone", "lowford", "--facts", "prologue.done=true", "--auto", "idle", "--spots", "-7.5,87.5;" + ROAD], 5),
    "town_dawn": (["--zone", "waystation", "--time", "dawn", "--auto", "idle", "--spots", "0,23;3,3;8,-18"], 3),
    "town_day": (["--zone", "waystation", "--time", "day", "--auto", "idle", "--spots", "0,23;3,3;8,-18"], 3),
}
rnd = sys.argv[1]; sets = sys.argv[2:] or list(SETS)
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0: print(b.stdout[-3000:]); sys.exit(1)
TURN = "env-1: E1 light " + rnd
if subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600", "--stale-ok"]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for s in sets:
        extra, n = SETS[s]; name = f"{rnd}_{s}"; t0 = time.time()
        args = HER + extra + ["--spots-from", "10", "--spots-every", "6", "--shot", name, "--seconds", "15", "--every", "6", "--count", str(n)]
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + args, stdout=lf, stderr=subprocess.STDOUT)
            try: p.wait(timeout=600)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        print(f"[{name}] {time.time()-t0:.0f} s")
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
