"""Play the game from the story worktree: python play_s6.py NAME [godot args] -- [game args...]
Frames land in godot/.shots/, the console log in story6/logs/NAME.log. --timeout S caps the wall time.
(experience's play.py, pointed here.)"""
import subprocess, sys, os, time

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7ba8903f4c8261b1\godot"
GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

name = sys.argv[1]
rest = sys.argv[2:]
if "--" in rest:
    i = rest.index("--"); pre, game = rest[:i], rest[i + 1:]
else:
    pre, game = [], rest
timeout = 900
if "--timeout" in pre:
    j = pre.index("--timeout"); timeout = int(pre[j + 1]); pre = pre[:j] + pre[j + 2:]
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
talk = [l for l in text.splitlines() if l.startswith("talk:") or l.startswith("open ")]
print(f"{name}: {len(saved)} frames in {time.time() - t0:.0f}s wall; log {log}")
for l in talk[:10]:
    print("  ", l[:200])
for l in errs[:12]:
    print("ERR", l[:300])
