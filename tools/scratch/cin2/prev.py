"""Render a cinematic's previs stills in the engine and make a contact sheet.
python prev.py CINE_ID NAME UNTIL [--cols 3] [--width 620] [--zone Z] [extra game args...]
Prints the cinema log lines and --cinebones output."""
import glob, os, subprocess, sys, time

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"
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
quiet = "--quiet" in extra
if quiet:
    extra.remove("--quiet")
t0 = time.time()
for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*")):
    os.remove(f)
args = [GODOT, "--path", WT, "--resolution", "1920x1080", "--", "--quick", "warden", "--sex", "female", "--zone", zone,
        "--cine", cine, "--shot", name, "--until", until, "--cinebones"] + extra
p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
for ln in (p.stdout + p.stderr).splitlines():
    if ln.startswith("cinema") or ("cinebones" in ln and not quiet) or ("cinema" in ln and ("WARN" in ln or "ERR" in ln)) or "no clip" in ln or "SCRIPT ERROR" in ln or "Unhandled" in ln:
        print(ln.replace("cinebones ", ""))
files = sorted((f for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*.png")) if os.path.getmtime(f) >= t0 - 1
                and (not only or any(f"_s{o.lower()}_" in os.path.basename(f) for o in only))), key=os.path.getmtime)
print(f"{len(files)} stills in {time.time() - t0:.0f} s")
if files:
    out = os.path.join(HERE, f"{name}_{cine}.jpg")
    env = dict(os.environ, SHEET_W=width, SHEET_COLS=cols)
    subprocess.run([sys.executable, SHEET, out] + files, env=env)
