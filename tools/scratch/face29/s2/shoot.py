"""face29 s2: c04a close-ups, three faces. python shoot.py TAG [extra godot args...]"""
import os, subprocess, sys, time, glob
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs"); os.makedirs(LOGS, exist_ok=True)
TP = os.path.join(W, "tools", "turn.py")
PZ0 = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
PZ = {k: v for k, v in PZ0.items() if k in os.environ.get("FACES", "own,saffron,sunborn").split(",")}
import json
VARS = json.loads(open(sys.argv[1]).read()) if sys.argv[1].endswith(".json") else [[sys.argv[1]] + sys.argv[2:]]
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
print("dotnet build", b.returncode, flush=True)
if b.returncode: print(b.stdout[-2000:]); sys.exit(2)
if subprocess.run([sys.executable, TP, "take", "godot", "face29 s2: mouth c04a", "--wait", "3600", "--root", W, "--stale-ok"]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for TAG, *EXTRA in VARS:
     for f, (sk, ey) in PZ.items():
        name = f"s2{TAG}_{f}"; t0 = time.time()
        for x in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(x)
        a = ["--quick", "warden", "--sex", "female", "--zone", "lowford", "--nohud", "--cine", "c04a", "--shot", name, "--until", os.environ.get("UNTIL", "46"), "--stills", "4",
             "--preset", f, "--skin", sk, "--eyes", ey, "--hair", "ponytail"] + EXTRA
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + a, stdout=lf, stderr=subprocess.STDOUT)
            try: p.wait(timeout=420)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        print(f"[{name}] {len(glob.glob(os.path.join(G, '.shots', name + '*sa5*.png')))} sa5 png, {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face29 s2: mouth c04a"])
print("DONE")
