"""Face 30 H1b: one godot turn of debug shots (env H1DBG, People.H1Debug) at the patch's frames.
    python dbg_shoot.py <log dir>"""
import os, subprocess, sys, time, glob
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
LOGS = sys.argv[1]; os.makedirs(LOGS, exist_ok=True)
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
def look(f, s, d):
    sk, ey = PZ[f]
    return ["--seconds", "10", "--turn", str(d), "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes", "--preset", f, "--skin", sk, "--eyes", ey]
MODES = {"base": "", "nohair": "nohair", "uv": "nohair,uv", "dye": "capgreen,cardsblue", "nospec": "nospec",
         "nosss": "nosss", "mask": "mask", "nocap": "nocap", "uvhair": "uv"}
RUNS = []
for f, s, d in (("own", "pixie", 180), ("own", "braid", 315)):
    for m in MODES: RUNS.append((f"h1d_{f}_{s}_t{d:03d}_{m}", look(f, s, d), MODES[m]))
for m in ("base", "nospec", "nocap", "mask"):
    RUNS.append((f"h1d_sunborn_pixie_t180_{m}", look("sunborn", "pixie", 180), MODES[m]))
if len(sys.argv) > 2:   # (python dbg_shoot.py LOGS PROBE: the UV probes only)
    MODES.update({"uv10": "nohair,uv10", "uv11": "nohair,uv11"})
    RUNS = [(f"h1d_{f}_{s}_t{d:03d}_{m}", look(f, s, d), MODES[m]) for f, s, d in (("own", "pixie", 180), ("own", "braid", 315), ("sunborn", "pixie", 180)) for m in ("uv10", "uv11")]
if subprocess.run([sys.executable, TP, "take", "godot", "face30: h1b dbg", "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    for name, a, mode in RUNS:
        t0 = time.time()
        for fp in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(fp)
        env = dict(os.environ); env["H1DBG"] = mode
        if any(t.startswith("uv") for t in mode.split(",")): a = a + ["--tonemap", "linear", "--grade", "off"]
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--", "--shot", name] + a, stdout=lf, stderr=subprocess.STDOUT, env=env)
            try: p.wait(timeout=300)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        print(f"[{name}] {len(glob.glob(os.path.join(G, '.shots', name + '*.png')))} png, {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30: h1b dbg"])
print("DBG DONE", time.strftime("%H:%M"))
