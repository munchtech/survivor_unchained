"""Face 30 round 3: the judge set in one godot turn (as h1b/h1b_shoot.py, art already installed and imported):
the Look (own, saffron, sunborn x braid, ponytail, pixie x turns 0, 135, 180, 315 by night), own braid/ponytail at
90 and 270, saffron ponytail 90/270, own t180/t315 by day, a ponytail spin strip, the town close-up across run (pixie
day and night, braid and ponytail by day), and the H1 probes still missing (sunborn t180 no-hair, sunborn t315).
    python shoot.py <logs dir> [only-prefix ...]"""
import os, subprocess, sys, time, glob
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
LOGS = sys.argv[1]; os.makedirs(LOGS, exist_ok=True); ONLY = sys.argv[2:]
STY = ["braid", "ponytail", "pixie"]
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe")}
def look(f, s, d):
    sk, ey = PZ[f]
    return ["--seconds", "10", "--turn", str(d), "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes", "--preset", f, "--skin", sk, "--eyes", ey]
def cu(s, tm):
    return ["--seconds", "8", "--every", "0.25", "--count", "12", "--auto", "across", "--close", "1", "--hair", s, "--quick", "reaver",
            "--sex", "female", "--zone", "waystation", "--nohud", "--preset", "own", "--skin", "fair", "--eyes", "moss", "--time", tm]
def runs():
    r = []
    for f in ("own", "saffron", "sunborn"):
        for s in STY:
            for d in (0, 135, 180, 315):
                r.append((f"r3_lk_{f}_{s}_t{d:03d}", look(f, s, d), ""))
    for f, ss in (("own", ("braid", "ponytail")), ("saffron", ("ponytail",))):
        for s in ss:
            for d in (90, 270):
                r.append((f"r3_lk_{f}_{s}_t{d:03d}", look(f, s, d), ""))
    for s in STY:
        for d in (180, 315):
            r.append((f"r3_lk_own_{s}_t{d:03d}_day", look("own", s, d) + ["--look-time", "day"], ""))
    r.append(("r3_spin_ponytail", ["--every", "0.1", "--count", "20", "--spin", "90"] + look("own", "ponytail", 0)[2:] + ["--seconds", "6"], ""))
    r.append(("r3_cu_own_pixie_across", cu("pixie", "day"), ""))
    r.append(("r3_cu_own_pixie_across_night", cu("pixie", "night"), ""))
    for s in ("braid", "ponytail"):
        r.append((f"r3_cu_own_{s}_across", cu(s, "day"), ""))
    lin = ["--tonemap", "linear", "--grade", "off"]
    r.append(("h1d_sunborn_pixie_t180_nohair", look("sunborn", "pixie", 180), "nohair"))
    for m, mode in (("nohair", "nohair"), ("uv10", "nohair,uv10"), ("uv11", "nohair,uv11")):
        r.append((f"h1d_sunborn_pixie_t315_{m}", look("sunborn", "pixie", 315) + (lin if "uv" in mode else []), mode))
    if ONLY:
        r = [x for x in r if any(x[0].startswith(o) for o in ONLY)]
    return r
def shoot(rs):
    for name, a, mode in rs:
        t0 = time.time()
        for f in glob.glob(os.path.join(G, ".shots", name + "*")):
            if ("_day" in f) == ("_day" in name) and ("_night" in f) == ("_night" in name): os.remove(f)
        env = dict(os.environ)
        if mode: env["H1DBG"] = mode
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--", "--shot", name] + a, stdout=lf, stderr=subprocess.STDOUT, env=env)
            try: p.wait(timeout=300)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        n = len([f for f in glob.glob(os.path.join(G, ".shots", name + "*.png")) if ("_day" in f) == ("_day" in name) and ("_night" in f) == ("_night" in name)])
        print(f"[{name}] {n} png, {time.time()-t0:.0f} s", flush=True)
if subprocess.run([sys.executable, TP, "take", "godot", "face30: r3 shoot", "--wait", "3600", "--root", W, "--stale-ok"]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    shoot(runs())
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30: r3 shoot"])
print("SHOOT DONE", time.strftime("%H:%M"))
