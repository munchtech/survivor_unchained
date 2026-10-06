"""Play the game for the experience audit: python play.py NAME [godot args] -- [game args...]
Runs the game in a 1920x1080 window from the experience worktree; frames land in godot/.shots/,
the whole console log in scratchpad/experience/logs/NAME.log. --timeout S caps the wall time."""
import subprocess, sys, os, time

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

name = sys.argv[1]
rest = sys.argv[2:]
if "--" in rest:
    i = rest.index("--"); pre, game = rest[:i], rest[i + 1:]
else:
    pre, game = [], rest
timeout = 3600
if "--timeout" in pre:
    j = pre.index("--timeout"); timeout = int(pre[j + 1]); pre = pre[:j] + pre[j + 2:]
# Game time steps evenly however busy the GPU is (other sessions share it); --real runs in wall time.
if "--real" in pre: pre.remove("--real")
elif "--fixed-fps" not in pre: pre = ["--fixed-fps", "60"] + pre
args = [GODOT, "--path", WT, "--resolution", "1920x1080"] + pre + ["--"] + game + ["--shot", name]
shots = os.path.join(WT, ".shots")
for f in os.listdir(shots) if os.path.isdir(shots) else []:
    if f.startswith(name + "_") or f == name + ".png":
        os.remove(os.path.join(shots, f))
os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
log = os.path.join(HERE, "logs", name + ".log")
t0 = time.time()
with open(log, "w", encoding="utf-8", errors="replace") as fh:
    try:
        subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
text = open(log, encoding="utf-8", errors="replace").read()
saved = [l for l in text.splitlines() if l.startswith("saved")]
errs = [l for l in text.splitlines() if ("ERROR" in l or "Exception" in l) and "saved" not in l]
print(f"{name}: {len(saved)} frames in {time.time() - t0:.0f}s wall; log {log}")
for l in errs[:15]:
    print("ERR", l[:300])
