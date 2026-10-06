"""Render a cinematic's previs stills in the engine and make a contact sheet.
python prev.py CINE_ID NAME UNTIL [--cols 3] [--width 620] [--zone Z] [extra game args...]
Prints the cinema log lines and --cinebones output."""
import glob, os, subprocess, sys, time

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aece7b87e89b13f19\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, "..", "cine", "sheet.py")

cine, name, until = sys.argv[1], sys.argv[2], sys.argv[3]
extra = sys.argv[4:]


def opt(flag, default):
    if flag in extra:
        i = extra.index(flag); v = extra[i + 1]; del extra[i:i + 2]; return v
    return default


cols, width, zone = opt("--cols", "3"), opt("--width", "620"), opt("--zone", "lowford")
only = [x for x in opt("--only", "").split(",") if x]
wait = opt("--wait", "0")
quiet = "--quiet" in extra
noturn = "--noturn" in extra
if noturn:
    extra.remove("--noturn")
if quiet:
    extra.remove("--quiet")
# The engine runs the last built assembly: build first (needs no turn).
b = subprocess.run(["dotnet", "build", os.path.join(WT, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
if b.returncode != 0:
    print("\n".join(l for l in b.stdout.splitlines() if " error " in l)[:3000]); sys.exit(2)
t0 = time.time()
for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*")):
    os.remove(f)
sex = ["--sex", "male", "--body", "hero"] if "--male" in extra else ["--sex", "female"]
if "--male" in extra:
    extra.remove("--male")
calling = opt("--calling", "warden")
args = [GODOT, "--path", WT, "--resolution", "1920x1080", "--", "--quick", calling] + sex + ["--zone", zone,
        "--cine", cine, "--shot", name, "--until", until, "--cinebones"] + extra
# The machine's heavy work takes turns (docs/team/README.md): a Godot run holds one.
TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
who = f"cinematics: previs {cine} {name}"
if not noturn and subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", wait]).returncode != 0:
    sys.exit(1)
# Streamed to a log (a flood of engine errors once ran the reader out of memory), with a time limit.
log = os.path.join(HERE, f"{name}.log")
with open(log, "w", encoding="utf-8", errors="replace") as lf:
    proc = subprocess.Popen(args, stdout=lf, stderr=subprocess.STDOUT)
    try:
        proc.wait(timeout=420)
    except subprocess.TimeoutExpired:
        # The console wrapper starts the engine as its child: stop the whole tree.
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        print("TIMEOUT: the engine was stopped")
if not noturn:
    subprocess.run([sys.executable, TURN, "give", "godot", who])
seen = {}
for ln in open(log, encoding="utf-8", errors="replace"):
    ln = ln.rstrip()
    if "ERROR" in ln or "WARNING" in ln:
        seen[ln[:160]] = seen.get(ln[:160], 0) + 1
    if ln.startswith("cinema") or ("cinebones" in ln and not quiet) or ("cinema" in ln and ("WARN" in ln or "ERR" in ln)) or "no clip" in ln or "SCRIPT ERROR" in ln or "Unhandled" in ln:
        print(ln.replace("cinebones ", ""))
files = sorted((f for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*.png")) if os.path.getmtime(f) >= t0 - 1
                and (not only or any(f"_s{o.lower()}_" in os.path.basename(f) for o in only))), key=os.path.getmtime)
for k, n in list(seen.items())[:12]:
    print(f"  [{n}x] {k}")
print(f"{len(files)} stills in {time.time() - t0:.0f} s")
if files:
    out = os.path.join(HERE, f"{name}_{cine}.jpg")
    env = dict(os.environ, SHEET_W=width, SHEET_COLS=cols)
    subprocess.run([sys.executable, SHEET, out] + files, env=env)
