"""Face 30 H1b (from h1/h1_shoot.py): python h1b_shoot.py <logs> [quick]. Install the pixie build (if given), import, then shoot the Look (3 faces x 3 styles x 4 turns,
own t180 by day) and the town close-up across run (pixie, day and night). One godot turn.
    python h1_shoot.py <scratch dir for logs> [built art dir with heroine_hair_pixie.*]"""
import os, subprocess, sys, time, glob, shutil
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot"); ART = os.path.join(G, "art", "people")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
OUT = sys.argv[1]; QUICK = len(sys.argv) > 2 and sys.argv[2] == "quick"; BUILT = sys.argv[3] if len(sys.argv) > 3 else None
LOGS = os.path.join(OUT, "logs"); os.makedirs(LOGS, exist_ok=True)
STY = ["braid", "ponytail", "pixie"]
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
def look(f, s, d):
    sk, ey = PZ[f]
    return ["--seconds", "10", "--turn", str(d), "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes", "--preset", f, "--skin", sk, "--eyes", ey]
CU = ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "across", "--close", "1", "--hair", "pixie",
      "--quick", "reaver", "--sex", "female", "--zone", "waystation", "--nohud", "--preset", "own", "--skin", "fair", "--eyes", "moss"]
def runs():
    r = []
    for f in ("own", "saffron", "sunborn"):
        for s in STY:
            for d in (0, 135, 180, 315):
                r.append((f"h1b_lk_{f}_{s}_t{d:03d}", look(f, s, d)))
    for s in STY:
        for d in (180, 315):
            r.append((f"h1b_lk_own_{s}_t{d:03d}_day", look("own", s, d) + ["--look-time", "day"]))
    r.append(("h1b_cu_own_pixie_across", CU + ["--time", "day"]))
    r.append(("h1b_cu_own_pixie_across_night", CU + ["--time", "night"]))
    if QUICK:
        want = {"h1b_lk_own_pixie_t180", "h1b_lk_own_braid_t315", "h1b_lk_sunborn_pixie_t180", "h1b_lk_own_ponytail_t315", "h1b_lk_own_pixie_t135"}
        r = [x for x in r if x[0] in want]
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
        n = len([f for f in glob.glob(os.path.join(G, ".shots", name + "*.png")) if ("_day" in f) == ("_day" in name) and ("_night" in f) == ("_night" in name)])
        print(f"[{name}] {n} png, {time.time()-t0:.0f} s", flush=True)
if subprocess.run([sys.executable, TP, "take", "godot", "face30: h1b shoot", "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    if BUILT:
        for ext in (".gltf", ".bin"):
            shutil.copy2(os.path.join(BUILT, f"heroine_hair_pixie{ext}"), os.path.join(ART, f"heroine_hair_pixie{ext}")); print("installed pixie" + ext)
    r = subprocess.run([GODOT, "--headless", "--path", G, "--import"], capture_output=True, text=True, timeout=1200)
    print("import exit", r.returncode, flush=True)
    shoot(runs())
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30: h1b shoot"])
print("SHOOT DONE", time.strftime("%H:%M"))
