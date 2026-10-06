"""Film a cinematic's hand-over into play: frames every 0.1 s from 1.5 s before its end to 2.5 s
into play (--handoff), then a contact sheet and an MP4 at 10 fps.
python ho.py CINE NAME UNTIL [--zone Z] [--wait MIN] [--wt WORKTREE_GODOT] [--before START_S]
--before START_S: an old build without --handoff: plain frames every 0.1 s from START_S (real seconds)."""
import glob, os, subprocess, sys, time

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7a4c20bcfd7ccfd3\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
FF = r"C:\Users\munch\AppData\Roaming\Python\Python314\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
cine, name, until = sys.argv[1], sys.argv[2], sys.argv[3]
extra = sys.argv[4:]


def opt(flag, default):
    if flag in extra:
        i = extra.index(flag); v = extra[i + 1]; del extra[i:i + 2]; return v
    return default


zone, wait, wt, before = opt("--zone", "lowford"), opt("--wait", "0"), opt("--wt", WT), opt("--before", None)
if wt == WT:
    b = subprocess.run(["dotnet", "build", os.path.join(WT, "SurvivorUnchained.csproj"), "-v", "q", "-nologo"], capture_output=True, text=True)
    if b.returncode != 0:
        print(b.stdout[-3000:]); sys.exit(2)
for f in glob.glob(os.path.join(wt, ".shots", f"{name}*")):
    os.remove(f)
args = [GODOT, "--path", wt, "--resolution", "1920x1080", "--", "--quick", "warden", "--sex", "female", "--zone", zone,
        "--cine", cine, "--shot", name, "--until", until]
args += ["--seconds", before, "--every", "0.1", "--count", "70"] if before else ["--handoff"]
args += extra
who = f"cinematics: hand-over {cine} {name}"
if subprocess.run([sys.executable, TURN, "take", "godot", who, "--wait", wait]).returncode != 0:
    sys.exit(1)
log = os.path.join(HERE, f"{name}.log")
try:
    with open(log, "w", encoding="utf-8", errors="replace") as lf:
        p = subprocess.Popen(args, stdout=lf, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=480)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
            print("TIMEOUT")
finally:
    subprocess.run([sys.executable, TURN, "give", "godot", who])
for ln in open(log, encoding="utf-8", errors="replace"):
    if ln.startswith("cinema"):
        print(ln.rstrip())
frames = sorted(glob.glob(os.path.join(wt, ".shots", f"{name}_[0-9][0-9].png" if before else f"{name}_ho_*.png")))
print(len(frames), "frames")
if not frames:
    sys.exit(0)
tmp = os.path.join(HERE, f"{name}_seq")
os.makedirs(tmp, exist_ok=True)
for f in glob.glob(os.path.join(tmp, "*.png")):
    os.remove(f)
from PIL import Image
for i, f in enumerate(frames):
    Image.open(f).convert("RGB").resize((960, 540)).save(os.path.join(tmp, f"{i:04d}.png"))
mp4 = os.path.join(HERE, f"{name}.mp4")
subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "10", "-i", os.path.join(tmp, "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4])
sheet = os.path.join(HERE, "..", "cine", "sheet.py")
pick = frames[::3]
subprocess.run([sys.executable, sheet, os.path.join(HERE, f"{name}.jpg")] + pick, env=dict(os.environ, SHEET_W="480", SHEET_COLS="5"))
print(mp4)
