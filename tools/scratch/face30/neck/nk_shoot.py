"""Face 30 neck: python nk_shoot.py <log dir> <tag> [base|tog|all]. One godot turn.
base: the Look, braid, 3 faces x turns 0/45 x day/night -> nk_<tag>_<face>_t<turn>_<day|night>.
tog: candidate toggles on own t045 night, own t000 day, sunborn t000 night -> nk_<tag>_<face>_t<turn>_<time>_<toggle>."""
import os, subprocess, sys, time, glob
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0"
G = os.path.join(W, "godot")
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TP = os.path.join(W, "tools", "turn.py")
LOGS = sys.argv[1]; TAG = sys.argv[2]; WHAT = sys.argv[3] if len(sys.argv) > 3 else "all"
os.makedirs(LOGS, exist_ok=True)
PZ = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe"), "highborn": ("fair", "frost")}
PZ = {k: v for k, v in PZ.items() if k in os.environ["FACES"].split(",")} if os.environ.get("FACES") else {k: v for k, v in PZ.items() if k != "highborn"}
LK = {"own": ("fair", "moss"), "saffron": ("warm", "peat"), "sunborn": ("brown", "sloe"), "highborn": ("fair", "frost")}
def look(f, d, tm, s="braid"):
    sk, ey = LK[f]
    a = ["--seconds", "10", "--turn", str(d), "--hair", s, "--new", "--sex", "female", "--step", "1", "--part", "0", "--open-eyes", "--preset", f, "--skin", sk, "--eyes", ey]
    return a + (["--look-time", "day"] if tm == "day" else [])
TOG = {  # name: (extra args, H1DBG)
    "base": ([], ""), "noamb": (["--look-ambient", "0"], ""), "norim": (["--rig", "1.3,0.22,0.8,0"], ""),
    "rimwhite": (["--rim-colour", "1,1,1"], ""), "noedge": (["--rig", "1.3,0.22,0,0.55"], ""), "nossao": (["--ssao", "off"], ""),
    "nohair": ([], "nohair"), "nosss": ([], "allsss"), "noshade": (["--shade-tint", "off"], ""), "nothin": (["--skin-set", "*:shade_thin=0"], ""),
    "noao": ([], "noao"), "flathead": ([], "flathead"), "flatbody": ([], "flatbody"), "flatall": ([], "flathead,flatbody"),
    "white": (["--rig-white"], ""), "nograde": (["--grade", "off"], ""),
}
RUNS = []
if WHAT in ("base", "all"):
    for f in PZ:
        for d in (0, 45):
            for tm in ("day", "night"):
                RUNS.append((f"nk_{TAG}_{f}_t{d:03d}_{tm}", look(f, d, tm), ""))
if WHAT in ("tog", "all"):
    for f, d, tm in (("own", 45, "night"), ("own", 0, "day"), ("sunborn", 0, "night")):
        for t, (ex, dbg) in TOG.items():
            RUNS.append((f"nk_{TAG}_{f}_t{d:03d}_{tm}_{t}", look(f, d, tm) + ex, dbg))
if WHAT == "uv":  # her head's UV emitted (and the graft's paint flat, to see the seam): nk_<tag>_<face>_t<turn>_night_uv
    for f in PZ:
        for d in (0, 45):
            RUNS.append((f"nk_{TAG}_{f}_t{d:03d}_night_uv", look(f, d, "night") + ["--tonemap", "linear", "--grade", "off"], "nohair,uv"))
if WHAT == "uv10":  # her head's UV, 0.25 * (u, v, 1): decoded against the blue
    for f in PZ:
        for d in (0, 45):
            RUNS.append((f"nk_{TAG}_{f}_t{d:03d}_night_uv10", look(f, d, "night") + ["--tonemap", "linear", "--grade", "off"], "nohair,uv10"))
if subprocess.run([sys.executable, TP, "take", "godot", "face30: neck shoot", "--wait", "3600", "--root", W]).returncode != 0:
    print("TURN REFUSED"); sys.exit(1)
try:
    if os.environ.get("NKIMPORT"):   # (env NKIMPORT=1: import first, for a changed texture)
        r = subprocess.run([GODOT, "--headless", "--path", G, "--import"], capture_output=True, text=True, timeout=1200); print("import exit", r.returncode, flush=True)
    for name, a, dbg in RUNS:
        t0 = time.time()
        for fp in glob.glob(os.path.join(G, ".shots", name + "*")): os.remove(fp)
        env = dict(os.environ)
        if dbg: env["H1DBG"] = dbg
        else: env.pop("H1DBG", None)
        with open(os.path.join(LOGS, name + ".log"), "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([GODOT, "--path", G, "--resolution", "1920x1080", "--", "--shot", name] + a, stdout=lf, stderr=subprocess.STDOUT, env=env)
            try: p.wait(timeout=300)
            except subprocess.TimeoutExpired:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True); print(name, "TIMEOUT")
        print(f"[{name}] {len(glob.glob(os.path.join(G, '.shots', name + '*.png')))} png, {time.time()-t0:.0f} s", flush=True)
finally:
    subprocess.run([sys.executable, TP, "give", "godot", "face30: neck shoot"])
print("SHOOT DONE", time.strftime("%H:%M"))
