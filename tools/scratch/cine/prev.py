"""Render a cinematic's previs stills in the engine and make a contact sheet.
python prev.py CINE_ID NAME UNTIL [--cols 3] [--width 620] [extra game args...]
Prints the cinema log lines and --cinebones output."""
import glob, os, subprocess, sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af7a79bc783cca7bc\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

cine, name, until = sys.argv[1], sys.argv[2], sys.argv[3]
extra = sys.argv[4:]
cols, width = "3", "620"
if "--cols" in extra:
    i = extra.index("--cols"); cols = extra[i + 1]; del extra[i:i + 2]
if "--width" in extra:
    i = extra.index("--width"); width = extra[i + 1]; del extra[i:i + 2]
zone = "lowford"
if "--zone" in extra:
    i = extra.index("--zone"); zone = extra[i + 1]; del extra[i:i + 2]
import time; t0 = time.time()
for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*")):
    os.remove(f)
args = [GODOT, "--path", WT, "--resolution", "1920x1080", "--", "--quick", "warden", "--sex", "female", "--zone", zone,
        "--cine", cine, "--shot", name, "--until", until, "--cinebones"] + extra
p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
for ln in (p.stdout + p.stderr).splitlines():
    if ln.startswith("cinema") or "cinebones" in ln or ("cinema" in ln and ("WARN" in ln or "ERR" in ln)) or "no clip" in ln:
        print(ln.replace("cinebones ", ""))
files = sorted((f for f in glob.glob(os.path.join(WT, ".shots", f"{name}_*.png")) if os.path.getmtime(f) >= t0 - 1), key=os.path.getmtime)
if files:
    out = os.path.join(HERE, f"{name}_{cine}.jpg")
    env = dict(os.environ, SHEET_W=width, SHEET_COLS=cols)
    subprocess.run([sys.executable, os.path.join(HERE, "sheet.py"), out] + files, env=env)
