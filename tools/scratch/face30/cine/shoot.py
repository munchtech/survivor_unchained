"""face30 cine (H10/F2/F3): python shoot.py VARIANTS.json -- each [tag, kinds, faces, [godot args], {env}].
kinds: c01 c02 c04a day night. Shot names f30c{tag}_{face}_{kind}. Builds C#, one godot turn, gives it back."""
import os, subprocess, sys, time, glob, json
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(HERE, "logs"); os.makedirs(LOGS, exist_ok=True)
TP = os.path.join(W, "tools", "turn.py")
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
UNTIL = {"c01": "60", "c02": "42", "c04a": "46"}
VARS = json.loads(open(sys.argv[1]).read())
for k in range(4):
    b = subprocess.run(["dotnet", "build", os.path.join(G, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
    if b.returncode == 0: break
    print("build failed, retry", flush=True); print(b.stdout[-1500:]); time.sleep(180)
else: sys.exit(2)
TURN = "face30 cine: close-ups"
if subprocess.run([sys.executable, TP, "take", "godot", TURN, "--wait", "3600", "--root", W, "--stale-ok"]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for v in VARS:
        tag, kinds, faces, extra = v[:4]; env = dict(os.environ, **(v[4] if len(v) > 4 else {}))
        for f in faces:
            sk, ey = PZ[f]
            pre = ["--preset", f, "--skin", sk, "--eyes", ey, "--hair", "braid"]
            for kind in kinds:
                name = f"f30c{tag}_{f}_{kind}"; t0 = time.time()
                for x in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(x)
                if kind in UNTIL:
                    a = ["--quick", "warden", "--sex", "female", "--zone", "lowford", "--nohud", "--cine", kind, "--shot", name, "--until", UNTIL[kind], "--stills", "4"]
                elif kind in ("town", "townn"):
                    a = ["--shot", name, "--seconds", "8", "--close", "1", "--quick", "reaver", "--zone", "waystation", "--nohud", "--sex", "female", "--time", "day" if kind == "town" else "night"]
                else:
                    a = ["--shot", name, "--seconds", "10", "--new", "--sex", "female", "--step", "1", "--part", "1", "--open-eyes"] + (["--look-time", "day"] if kind == "day" else [])
                with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
                    p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--"] + a + pre + extra, stdout=lf, stderr=subprocess.STDOUT, env=env)
                    try: p.wait(timeout=420)
                    except subprocess.TimeoutExpired:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
                # keep only the stills we need
                for x in glob.glob(os.path.join(G, ".shots", name + "_c0*.png")):
                    if not any(s in x for s in ("_s7_", "_s8_", "_s8b_", "_sa5_", "_sa7_")): os.remove(x)
                print(f"[{name}] {len(glob.glob(os.path.join(G, '.shots', name + '*.png')))} png, {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", TURN])
print("DONE")
