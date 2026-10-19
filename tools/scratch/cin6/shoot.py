"""Cinematics shoot: python shoot.py RUNS.json [--noturn]
RUNS: list of {"name", "cine", "until", "args": [...], "env": {...}, "keep": ["_s10_", ...] (optional filter of stills kept)}.
Builds C#, takes ONE godot turn for the batch, gives it back. Shots land in godot/.shots/<name>_*."""
import os, subprocess, sys, time, glob, json
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs"); os.makedirs(LOGS, exist_ok=True)
TP = os.path.join(W, "tools", "turn.py")
RUNS = json.loads(open(sys.argv[1]).read())
b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0:
    print("\n".join(l for l in b.stdout.splitlines() if " error " in l)[:3000]); sys.exit(2)
TURN = "cinematics: shoot " + os.path.basename(sys.argv[1])
noturn = "--noturn" in sys.argv
if not noturn and subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for r in RUNS:
        name = r["name"]; t0 = time.time()
        for x in glob.glob(os.path.join(G, ".shots", name + "_*")): os.remove(x)
        env = dict(os.environ, **r.get("env", {}))
        base = ["--quick", r.get("calling", "warden"), "--sex", "female", "--zone", r.get("zone", "lowford"), "--nohud",
                "--cine", r["cine"], "--shot", name, "--until", str(r["until"]),
                "--preset", "own", "--skin", "fair", "--eyes", "moss", "--hair", "braid"]
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + base + r.get("args", []), stdout=lf, stderr=subprocess.STDOUT, env=env)
            try: p.wait(timeout=r.get("timeout", 600))
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        keep = r.get("keep")
        if keep:
            for x in glob.glob(os.path.join(G, ".shots", name + "_*.png")):
                if not any(k in os.path.basename(x) for k in keep): os.remove(x)
        print(f"[{name}] {len(glob.glob(os.path.join(G, '.shots', name + '_*.png')))} png, {time.time()-t0:.0f} s", flush=True)
finally:
    if not noturn: subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
