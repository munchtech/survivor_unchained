"""Face 29, S1 round: before (darker faces, current art), install S1's build, after (all faces) at the Look and the
town close-up, for the shipped styles (braid, ponytail, pixie). One godot turn.
    python s1_shoot.py <built art dir> <scratch dir>"""
import os, subprocess, sys, time, glob, shutil
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot"); ART = os.path.join(G, "art", "people")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
BUILT, OUT = sys.argv[1], sys.argv[2]
LOGS = os.path.join(OUT, "logs"); os.makedirs(LOGS, exist_ok=True)
STY = ["braid", "ponytail", "pixie"]
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
def look(f, s, d):
    sk, ey = PZ[f]
    return ["--seconds", "10", "--turn", str(d), "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes", "--preset", f, "--skin", sk, "--eyes", ey]
def runs(phase):
    r = []
    for s in STY:
        for f in ("saffron", "sunborn"):
            for d in (0, 135, 180, 315):
                r.append((f"{phase}_lk_{f}_{s}_t{d:03d}", look(f, s, d)))
        if phase == "a":
            for d in range(0, 360, 45):
                r.append((f"a_lk_own_{s}_t{d:03d}", look("own", s, d)))
            r.append((f"a_lk_own_{s}_spin", ["--every", "0.5", "--count", "8", "--spin", "90"] + look("own", s, 0)[2:] + ["--seconds", "6"]))
            r.append((f"a_cu_own_{s}_across", ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "across", "--close", "1", "--time", "day", "--hair", s,
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
if subprocess.run([sys.executable, TP, "take", "godot", "face29: s1 shoot", "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    shoot(runs("b"))
    for s in STY:
        for ext in (".gltf", ".bin", ".chain.json"):
            src = os.path.join(BUILT, f"heroine_hair_{s}{ext}")
            if os.path.exists(src): shutil.copy2(src, os.path.join(ART, f"heroine_hair_{s}{ext}")); print("installed", os.path.basename(src))
    r = subprocess.run([GODOT.replace("_console", "_console"), "--headless", "--path", G, "--import"], capture_output=True, text=True, timeout=1200)
    print("import exit", r.returncode, flush=True)
    shoot(runs("a"))
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face29: s1 shoot"])
print("SHOOT DONE", time.strftime("%H:%M"))
