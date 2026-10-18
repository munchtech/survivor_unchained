"""face30 F1: python shoot.py VARIANTS.json  -- each [tag, kind, faces, [godot args]]; kind c04a (cinematic A5) or look.
Builds C#, takes one godot turn, gives it back."""
import os, subprocess, sys, time, glob, json
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs"); os.makedirs(LOGS, exist_ok=True)
TP = os.path.join(W, "tools", "turn.py")
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
VARS = json.loads(open(sys.argv[1]).read())
for k in range(4):
    b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
    if b.returncode == 0: break
    print("build failed, retry", flush=True); print(b.stdout[-1500:]); time.sleep(180)
else: sys.exit(2)
if subprocess.run([sys.executable, TP, "take", "godot", "face30 f1: mouth", "--wait", "3600", "--root", W, "--stale-ok"]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for tag, kind, faces, extra in VARS:
        for f in faces:
            sk, ey = PZ.get(f, ("fair", "moss"))
            name = f"f30{tag}_{f}"; t0 = time.time()
            for x in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(x)
            if kind == "c04a":
                a = ["--quick", "warden", "--sex", "female", "--zone", "lowford", "--nohud", "--cine", "c04a", "--shot", name, "--until", "46",
                     "--stills", "4", "--preset", f, "--skin", sk, "--eyes", ey, "--hair", "ponytail"]
            else:
                a = ["--shot", name, "--seconds", "10", "--hair", "ponytail", "--new", "--sex", "female", "--step", "1", "--part", "1",
                     "--open-eyes", "--preset", f] + (["--skin", sk, "--eyes", ey] if f in PZ else [])
            with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
                p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + a + extra, stdout=lf, stderr=subprocess.STDOUT)
                try: p.wait(timeout=420)
                except subprocess.TimeoutExpired:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
            print(f"[{name}] {len(glob.glob(os.path.join(G, '.shots', name + '*.png')))} png, {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30 f1: mouth"])
print("DONE")
