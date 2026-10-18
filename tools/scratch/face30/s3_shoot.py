"""Face 30, S3: the Look (own, saffron, sunborn; turns 0-270, own 315), a spin strip and the town close-up for braid and
ponytail, on the installed art. One godot turn.   python s3_shoot.py <unused> <scratch dir>"""
import os, subprocess, sys, time, glob, shutil
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot"); ART = os.path.join(G, "art", "people")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
BUILT, OUT = sys.argv[1], sys.argv[2]
LOGS = os.path.join(OUT, "logs"); os.makedirs(LOGS, exist_ok=True)
STY = ["braid", "ponytail"]
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
def look(f, s, d):
    sk, ey = PZ[f]
    return ["--seconds", "10", "--turn", str(d), "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes", "--preset", f, "--skin", sk, "--eyes", ey]
def runs():
    r = []
    for s in STY:
        for f in ("own", "saffron", "sunborn"):
            for d in (0, 90, 180, 270) + ((315,) if f == "own" else ()):
                r.append((f"s3_lk_{f}_{s}_t{d:03d}", look(f, s, d)))
        r.append((f"s3_spin_{s}", ["--every", "0.1", "--count", "20", "--spin", "90"] + look("own", s, 0)[2:] + ["--seconds", "6"]))
        r.append((f"s3_cu_own_{s}_across", ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "across", "--close", "1", "--time", "day", "--hair", s,
                                           "--quick", "reaver", "--sex", "female", "--zone", "waystation", "--nohud", "--preset", "own", "--skin", "fair", "--eyes", "moss"]))
    return r
def shoot(rs):
    for name, a in rs:
        t0 = time.time()
        for f in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(f)
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--", "--shot", name] + a, stdout=lf, stderr=subprocess.STDOUT)
            try: p.wait(timeout=300)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        n = len(glob.glob(os.path.join(G, ".shots", name + "*.png")))
        print(f"[{name}] {n} png, {time.time()-t0:.0f} s", flush=True)
if subprocess.run([sys.executable, TP, "take", "godot", "face30: s3 shoot", "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    shoot(runs())
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30: s3 shoot"])
print("SHOOT DONE", time.strftime("%H:%M"))
